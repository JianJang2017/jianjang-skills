#!/usr/bin/env python3
"""把一篇 Markdown 文章发布到稀土掘金。

用法：
    python3 publish_juejin.py <file>.md [--title T] [--publish] [--cdp-url URL] \\
        [--draft-id ID] [--keep-broken-images]

通用逻辑（frontmatter→Plan、扫图、编辑器写入、CDN URL 提取）见 _common.py；
这里只保留掘金特定的选择器、登录态判定、上传响应过滤、发布弹窗交互。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, TYPE_CHECKING
from urllib.parse import urlparse

# 让脚本既能 `python publish_juejin.py` 跑，也能被当模块导入
sys.path.insert(0, str(Path(__file__).parent))
import _common as C  # noqa: E402

if TYPE_CHECKING:
    from playwright.sync_api import Page

# run() 启动时会把 PWTimeout 替换成真实 class；占位让上面 except 语法能 parse。
PWTimeout: type = Exception
browser_cdp = None


# ---------------------------------------------------------------------------
# 配置 & 选择器（DOM 变了改这里）
# ---------------------------------------------------------------------------

PLATFORM = "juejin"
EDITOR_NEW_URL = "https://juejin.cn/editor/drafts/new?v=2"
JUEJIN_HOME = "https://juejin.cn/"

UPLOAD_API_HOSTS = ("juejin.cn", "bytedance.com", "byteimg.com")

DEFAULT_TIMEOUT_MS = int(os.getenv("JUEJIN_TIMEOUT_MS", "30000"))

SELECTORS = {
    # 登录态判定：右上角头像
    "logged_in_avatar": ".avatar, .user-dropdown-list, img.avatar-img",

    # 编辑器
    "title_input": "input.title-input, textarea.title-input",
    # bytemd codemirror 区域；contenteditable 的 cm-content 是写入靶点
    "editor_cm": ".bytemd .CodeMirror, .bytemd-editor .cm-editor, .CodeMirror, .cm-editor",
    # 图片上传隐藏 input——掘金正文图片不走工具栏 file input，但封面图的 file input
    # 在同一页面 (.coverselector_container input)，走相同的上传通道。我们用它做正文图片
    # 上传，拿到 CDN URL 后手动塞进 markdown。
    "editor_image_input": ".coverselector_container input[type='file'], input[type='file'][accept*='image']",
    # 工具栏图片按钮（点击后真正的 input 才挂上）
    "toolbar_image_button": "[bytemd-tippy-path*='image'], .bytemd-toolbar [data-icon='image'], button[aria-label*='图片']",
    # 自动保存状态
    "save_status": ".save-status, .draft-status, :text('已保存')",

    # 发布按钮 & 弹窗
    "publish_button_top": "button:has-text('发布'), .publish-popup-btn, .btn-publish",
    "publish_dialog": ".publish-popup, .byte-modal:has-text('发布'), .ant-modal:has-text('发布')",
    "category_radio": ".category-list label, .category-select .item",
    "tag_input": "input[placeholder*='标签'], .tag-select input",
    "tag_option": ".byte-select-dropdown .byte-select-option, .ant-select-item-option",
    "cover_input": "input[type='file'][accept*='image']:not(:disabled)",
    "summary_textarea": "textarea[placeholder*='摘要'], textarea[placeholder*='简介']",
    "confirm_publish": ".publish-popup button:has-text('确认'), .ant-modal button:has-text('确认发布'), button:has-text('确认并发布')",
}


# ---------------------------------------------------------------------------
# 掘金特定的浏览器交互
# ---------------------------------------------------------------------------


def _ensure_logged_in(page: "Page") -> None:
    """判定掘金登录态。

    旧判据：右上角 `.avatar` 出现。但掘金新版 DOM 变了，未登录主页也有头像类元素，
    导致误判。改用更可靠的判据：直接打开编辑器，看是否被重定向到 passport 登录页。
    """
    # 我们调用 open_editor 时会先 goto；这里只检查最终 URL 是否被踢到登录页
    if "passport" in page.url.lower() or "login" in page.url.lower():
        raise SystemExit(
            "❌ 掘金未登录（被重定向到登录页）。\n"
            f"   当前 URL: {page.url}\n"
            "   请在浏览器里打开 https://juejin.cn 登录后重跑本脚本。"
        )


def open_editor(page: "Page", draft_id: str | None) -> None:
    target = EDITOR_NEW_URL if not draft_id else f"https://juejin.cn/editor/drafts/{draft_id}"
    page.goto(target, wait_until="domcontentloaded")
    page.wait_for_selector(SELECTORS["editor_cm"], timeout=DEFAULT_TIMEOUT_MS)


def _get_editor_markdown(page: "Page") -> str:
    """掘金编辑器的 markdown 读取（向后兼容旧调用）。"""
    return C.get_editor_markdown(page)


def _diff_new_image_urls(before: str, after: str) -> list[str]:
    return C.diff_new_image_urls(before, after)


def upload_one_image(page: "Page", local_path: Path) -> str | None:
    """掘金图片上传——委托给 _common 的通用剪贴板实现。

    走过的弯路（网络响应过滤 / file input / 合成 ClipboardEvent / 封面通道）
    见 references/juejin.md。
    """
    return C.upload_image_via_clipboard(page, local_path, SELECTORS["editor_cm"])


def fill_title(page: "Page", title: str) -> None:
    el = page.locator(SELECTORS["title_input"]).first
    el.click()
    el.fill(title)


def wait_autosave(page: "Page", timeout_ms: int = 6000) -> None:
    deadline = time.time() + timeout_ms / 1000.0
    while time.time() < deadline:
        try:
            text = page.locator(SELECTORS["save_status"]).first.inner_text(timeout=500)
            if "已保存" in text:
                return
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.3)
    C.press_save_shortcut(page)
    time.sleep(1.0)


def fill_publish_dialog(page: "Page", plan: C.Plan) -> tuple[bool, str]:
    """打开发布弹窗并预填字段。返回 (成功, 提示信息)。"""
    page.locator(SELECTORS["publish_button_top"]).first.click()
    try:
        page.wait_for_selector(SELECTORS["publish_dialog"], timeout=10000)
    except PWTimeout:
        return False, "发布弹窗没出现"

    notes: list[str] = []

    if plan.category:
        cats = page.locator(SELECTORS["category_radio"])
        found = False
        for i in range(cats.count()):
            if plan.category in cats.nth(i).inner_text().strip():
                cats.nth(i).click()
                found = True
                break
        if not found:
            notes.append(f"分类 '{plan.category}' 没匹配到，请手选")

    for tag in plan.tags:
        try:
            tag_box = page.locator(SELECTORS["tag_input"]).first
            tag_box.click()
            tag_box.fill(tag)
            page.wait_for_selector(SELECTORS["tag_option"], timeout=3000)
            options = page.locator(SELECTORS["tag_option"])
            matched = False
            for i in range(options.count()):
                if tag in options.nth(i).inner_text():
                    options.nth(i).click()
                    matched = True
                    break
            if not matched:
                notes.append(f"标签 '{tag}' 不在掘金预设里，已跳过")
                page.keyboard.press("Escape")
        except Exception as e:  # noqa: BLE001
            notes.append(f"标签 '{tag}' 处理失败：{e}")

    if plan.summary:
        try:
            page.locator(SELECTORS["summary_textarea"]).first.fill(plan.summary)
        except Exception:  # noqa: BLE001
            notes.append("摘要输入框没找到")

    if plan.cover:
        cover_path: Path | None = None
        if C.is_remote(plan.cover):
            notes.append("封面是 URL，请手动设置")
        else:
            cp = (plan.md_path.parent / plan.cover).resolve()
            if cp.exists():
                cover_path = cp
            else:
                notes.append(f"封面文件不存在：{cp}")
        if cover_path:
            try:
                page.locator(SELECTORS["cover_input"]).last.set_input_files(str(cover_path))
                time.sleep(2.0)
            except Exception as e:  # noqa: BLE001
                notes.append(f"封面上传失败：{e}")

    return True, "; ".join(notes) if notes else "OK"


def confirm_publish(page: "Page") -> None:
    page.locator(SELECTORS["confirm_publish"]).first.click()
    try:
        page.wait_for_url(re.compile(r"juejin\.cn/(post|editor/drafts)/"), timeout=15000)
    except PWTimeout:
        pass


def extract_draft_id(url: str) -> str | None:
    m = re.search(r"/editor/drafts/([^/?#]+)", url)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def run(plan: C.Plan, *, publish: bool, cdp_url: str | None, draft_id: str | None,
        keep_broken_images: bool) -> dict[str, Any]:
    global PWTimeout, browser_cdp  # noqa: PLW0603
    browser_cdp, PWTimeout = C.lazy_import_playwright()

    images_total = sum(1 for img in plan.images if not img.is_remote and img.local_path)
    missing = [img.src for img in plan.images
               if not img.is_remote and (not img.local_path or not img.local_path.exists())]
    if missing and not keep_broken_images:
        print("⚠️  以下本地图片不存在，将保留原 markdown 引用：\n  - " + "\n  - ".join(missing),
              file=sys.stderr)

    with browser_cdp.get_context(
        cdp_url=cdp_url,
        # 不在这里做登录检测——掘金未登录会被重定向到 passport，我们在 _ensure_logged_in
        # 里用 URL 判断更可靠；这里只负责开 profile 和打开主页。
        login_check_url=JUEJIN_HOME,
        login_indicator_selector=None,
    ) as (_pw, _br, ctx):
        page = browser_cdp.find_or_open(ctx, JUEJIN_HOME, JUEJIN_HOME)
        # 先开编辑器，再检查登录态——掘金新版未登录会重定向到 passport.juejin.cn
        open_editor(page, draft_id)
        _ensure_logged_in(page)

        # 已有草稿：先清空编辑器，避免旧正文干扰图片 diff
        if draft_id:
            C.write_into_editor(page, SELECTORS["editor_cm"], "")
            time.sleep(0.5)

        # 1. 上传图片，建立 mapping
        url_mapping: dict[str, str] = {}
        uploaded = 0
        for img in plan.images:
            if img.is_remote or not img.local_path or not img.local_path.exists():
                continue
            print(f"↑ 上传 {img.local_path.name} ...", file=sys.stderr)
            cdn = upload_one_image(page, img.local_path)
            if cdn:
                img.cdn_url = cdn
                url_mapping[img.src] = cdn
                uploaded += 1
            else:
                print(f"   失败，保留原引用：{img.src}", file=sys.stderr)

        # 2. 替换 + 写入
        body = C.rewrite_local_image_urls(plan.body, url_mapping)
        C.write_into_editor(page, SELECTORS["editor_cm"], body)
        fill_title(page, plan.title)

        # 3. 自动保存
        wait_autosave(page)

        result: dict[str, Any] = {
            "platform": PLATFORM,
            "draft_url": page.url,
            "draft_id": extract_draft_id(page.url),
            "article_url": None,
            "title": plan.title,
            "images_uploaded": uploaded,
            "images_total": images_total,
            "status": "draft",
            "notes": [],
        }

        # 4. 草稿模式不开发布弹窗（参见 SKILL.md 的设计取舍）；--publish 才进
        if publish:
            ok, notes = fill_publish_dialog(page, plan)
            if notes and notes != "OK":
                result["notes"].append(notes)
            if ok:
                confirm_publish(page)
                if "/post/" in page.url:
                    result["article_url"] = page.url
                    result["status"] = "published"
                else:
                    result["notes"].append("点了确认发布但 URL 没跳到文章页，请在浏览器里核对必填项")
            else:
                result["notes"].append("发布弹窗打开失败，已保留草稿，请人工发布")
        else:
            if any([plan.category, plan.tags, plan.cover, plan.summary]):
                result["notes"].append(
                    "草稿已存。发布时请在弹窗里填："
                    f"分类={plan.category or '—'}, 标签={plan.tags or '—'}, "
                    f"封面={plan.cover or '—'}, 摘要={'有' if plan.summary else '—'}"
                )

        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="把 Markdown 文章发布到稀土掘金（默认草稿）")
    parser.add_argument("md", help="markdown 文件路径")
    parser.add_argument("--title", default=None)
    parser.add_argument("--publish", action="store_true",
                        help="直接发布；不带则只存草稿")
    parser.add_argument("--cdp-url", default=None)
    parser.add_argument("--draft-id", default=None,
                        help="覆盖某个已有草稿，不带则新建")
    parser.add_argument("--keep-broken-images", action="store_true")
    parser.add_argument("--default-category", default=os.getenv("JUEJIN_DEFAULT_CATEGORY"))
    args = parser.parse_args()

    md_path = Path(args.md).expanduser().resolve()
    if not md_path.exists():
        print(f"❌ 找不到文件：{md_path}", file=sys.stderr)
        return 1

    plan = C.build_plan(md_path, args.title, args.default_category)
    if not plan.title:
        print("❌ 没有标题：frontmatter 里没 title，命令行也没传 --title", file=sys.stderr)
        return 1

    C.echo_plan(plan, "发布" if args.publish else "草稿", PLATFORM)
    result = run(plan, publish=args.publish, cdp_url=args.cdp_url,
                 draft_id=args.draft_id, keep_broken_images=args.keep_broken_images)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
