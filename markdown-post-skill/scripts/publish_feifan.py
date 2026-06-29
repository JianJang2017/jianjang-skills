#!/usr/bin/env python3
"""把一篇 Markdown 文章发布到讯飞内部的「飞帆」平台。

URL: https://feifan.iflytek.com/writeAnArticle

用法：
    python3 publish_feifan.py <file>.md [--title T] [--publish] [--cdp-url URL] \\
        [--keep-broken-images]

实测验证过的发布路径（2026-06-29）：
1. 飞帆默认是 TinyMCE 富文本编辑器。脚本启动后**第一步切换到 MD 编辑器**
   （CodeMirror 6 / md-editor-v3），后续就和掘金完全一样的栈。
2. 图片上传走系统剪贴板 + 真实 ⌘V（_common.upload_image_via_clipboard）。
3. 默认仅写入正文 + 标题 + 等自动保存，**不点发布**——飞帆点发布会弹模板选择
   弹窗，需要人工选模板后才能正式发布；脚本不替你做这个决定。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).parent))
import _common as C  # noqa: E402

if TYPE_CHECKING:
    from playwright.sync_api import Page

PWTimeout: type = Exception
browser_cdp = None


# ---------------------------------------------------------------------------
# 配置 & 选择器（已对 feifan.iflytek.com 实地验证）
# ---------------------------------------------------------------------------

PLATFORM = "feifan"
FEIFAN_HOME = "https://feifan.iflytek.com/"
EDITOR_URL = "https://feifan.iflytek.com/writeAnArticle"

DEFAULT_TIMEOUT_MS = int(os.getenv("FEIFAN_TIMEOUT_MS", "30000"))

SELECTORS = {
    # MD 模式下的编辑器：md-editor-v3 包装的 CodeMirror 6
    "editor": ".cm-editor",
    # 标题输入
    "title_input": "input[placeholder='请输入标题']",
    # 切换 MD 编辑器（默认是富文本）。按文本找最稳——class 名带 hash 后缀，会变。
    "toggle_md": "text=切换MD编辑器",
    "toggle_richtext": "text=切换富文本编辑器",
    # 顶部「发布」按钮（cursor:pointer 的那个）。点击会弹模板选择，**默认不点**。
    "publish_button": ".publishAnArticle___NKhGM, [class*='publishAnArticle']",
    # 发布流程的模板选择弹窗（仅 --publish 时会触及）
    "publish_modal": "[class*='templateModalArea'], [class*='templateModalList']",
    # 模板选择弹窗里的取消（兜底关闭）
    "modal_close": "[class*='templateModalArea'] [class*='close'], .ant-modal-close",
}


# ---------------------------------------------------------------------------
# 浏览器交互
# ---------------------------------------------------------------------------


def _ensure_logged_in(page: "Page") -> None:
    """飞帆走讯飞 SSO；未登录会被重定向到 sso.iflytek.com。"""
    u = page.url.lower()
    if "sso.iflytek" in u or "/login" in u or "passport" in u:
        raise SystemExit(
            "❌ 飞帆未登录（被重定向到 SSO 登录页）。\n"
            f"   当前 URL: {page.url}\n"
            "   请在弹出的浏览器里完成讯飞 SSO 登录后重跑本脚本。"
        )


def open_editor(page: "Page") -> None:
    """打开编辑器并切到 MD 模式。"""
    page.goto(EDITOR_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    # 等 SPA 渲染 + 可能的 SSO 重定向
    page.wait_for_timeout(5000)
    _ensure_logged_in(page)

    # 切换 MD 模式（默认是富文本，得切了才能 paste markdown）
    # 等待「切换MD编辑器」文本出现
    try:
        page.get_by_text("切换MD编辑器").first.click(timeout=10000)
        print("✓ 已切到 MD 编辑器", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        # 可能已经在 MD 模式（按钮变成「切换富文本编辑器」）；看 .cm-editor 是否已存在
        try:
            page.wait_for_selector(SELECTORS["editor"], timeout=3000)
            print("ℹ️  编辑器已在 MD 模式，跳过切换", file=sys.stderr)
        except Exception:  # noqa: BLE001
            raise SystemExit(
                f"❌ 既找不到「切换MD编辑器」按钮，也找不到 .cm-editor。\n"
                f"   错误：{e}\n"
                f"   请用 _diagnose_feifan.py（如果还存在）或手动核对页面状态。"
            )

    # 等 CodeMirror 6 挂上
    page.wait_for_selector(SELECTORS["editor"], timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_timeout(1500)  # 给 CM 完整渲染


def fill_title(page: "Page", title: str) -> None:
    el = page.locator(SELECTORS["title_input"]).first
    el.click()
    el.fill(title)


def upload_one_image(page: "Page", local_path: Path) -> str | None:
    """飞帆 MD 编辑器（md-editor-v3）接受 paste 事件；走通用剪贴板上传。"""
    return C.upload_image_via_clipboard(page, local_path, SELECTORS["editor"])


def wait_autosave(page: "Page", timeout_ms: int = 8000) -> None:
    """飞帆顶部有「内容将自动保存」提示——给它一点时间让 autosave 触发。

    没有显式的「已保存」状态指示器（实测，至少 dump 时没看到），所以用固定 sleep
    + Ctrl+S 兜底。
    """
    time.sleep(timeout_ms / 1000.0 / 2)
    C.press_save_shortcut(page)
    time.sleep(timeout_ms / 1000.0 / 2)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def run(plan: C.Plan, *, publish: bool, cdp_url: str | None,
        keep_broken_images: bool) -> dict[str, Any]:
    global PWTimeout, browser_cdp  # noqa: PLW0603
    browser_cdp, PWTimeout = C.lazy_import_playwright()

    images_total = sum(1 for img in plan.images if not img.is_remote and img.local_path)
    missing = [img.src for img in plan.images
               if not img.is_remote and (not img.local_path or not img.local_path.exists())]
    if missing and not keep_broken_images:
        print("⚠️  以下本地图片不存在，将保留原 markdown 引用：\n  - " + "\n  - ".join(missing),
              file=sys.stderr)

    with browser_cdp.get_context(cdp_url=cdp_url) as (_pw, _br, ctx):
        page = browser_cdp.find_or_open(ctx, FEIFAN_HOME, FEIFAN_HOME)
        open_editor(page)  # 内含登录态检查 + 切 MD 模式

        # 1. 上传图片（剪贴板路径——MD 编辑器在主页面 .cm-editor）
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

        # 2. 替换 + 写入正文。
        # 上传时编辑器里已经插了 N 张 ![](cdn)，所以要全清空再写完整正文。
        body = C.rewrite_local_image_urls(plan.body, url_mapping)
        C.write_into_editor(page, SELECTORS["editor"], body)
        fill_title(page, plan.title)

        # 3. 等自动保存
        wait_autosave(page)

        result: dict[str, Any] = {
            "platform": PLATFORM,
            "page_url": page.url,
            "article_url": None,
            "title": plan.title,
            "images_uploaded": uploaded,
            "images_total": images_total,
            "status": "draft",  # 飞帆没有显式草稿概念，「写入并自动保存」就当 draft
            "notes": [],
        }

        # 4. --publish：点发布按钮（会弹模板选择弹窗），由人工完成模板选择。
        # 我们不替用户选模板，因为不同模板可能跨频道/审核流程。
        if publish:
            try:
                page.locator(SELECTORS["publish_button"]).first.click(timeout=5000)
                # 等弹窗
                try:
                    page.wait_for_selector(SELECTORS["publish_modal"], timeout=5000)
                    result["status"] = "awaiting_template_selection"
                    result["notes"].append(
                        "已点「发布」并弹出模板选择弹窗——请在浏览器里选模板后人工完成发布。"
                    )
                except Exception:  # noqa: BLE001
                    result["notes"].append("点了发布但没看到模板弹窗，请在浏览器里核对。")
            except Exception as e:  # noqa: BLE001
                result["notes"].append(f"点击发布按钮失败：{e.__class__.__name__}")
        else:
            # 草稿模式：把元数据回显给用户照填
            if any([plan.category, plan.tags, plan.cover, plan.summary]):
                result["notes"].append(
                    "草稿已写入。发布时（人工点「发布」并选模板后）请记得填："
                    f"分类={plan.category or '—'}, 标签={plan.tags or '—'}, "
                    f"封面={plan.cover or '—'}, 摘要={'有' if plan.summary else '—'}"
                )

        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="把 Markdown 发布到讯飞飞帆（默认草稿）")
    parser.add_argument("md", help="markdown 文件路径")
    parser.add_argument("--title", default=None)
    parser.add_argument("--publish", action="store_true",
                        help="点「发布」按钮（仅触发模板选择弹窗，需人工完成最终发布）")
    parser.add_argument("--cdp-url", default=None)
    parser.add_argument("--keep-broken-images", action="store_true")
    parser.add_argument("--default-category", default=os.getenv("FEIFAN_DEFAULT_CATEGORY"))
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
                 keep_broken_images=args.keep_broken_images)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
