"""跨平台共享逻辑：frontmatter→Plan、图片扫描、CDN URL 提取、登录态/编辑器交互的通用辅助。

各平台脚本（publish_juejin.py / publish_feifan.py / 以后的 csdn / zhihu 等）只需要：
- 提供自己的 SELECTORS dict
- 实现 upload_one_image()、fill_metadata()、do_save_or_publish()
- 调 run_pipeline() 串起来

把共享代码抽这里有两个动机：
1. 一处修 = 处处修。比如 CodeMirror 写入靶点变了，所有平台同时受益。
2. 加平台只用写"差异点"，主流程不重复。
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class ImageRef:
    """正文里发现的一张图片引用。"""

    raw: str                       # 原始 markdown 片段 ![alt](path "title")
    alt: str
    src: str                       # 原始 src
    is_remote: bool
    local_path: Path | None = None
    cdn_url: str | None = None     # 上传后得到的平台 CDN URL


@dataclass
class Plan:
    md_path: Path
    title: str
    category: str | None
    column: str | None
    tags: list[str]
    cover: str | None
    summary: str | None
    body: str
    images: list[ImageRef] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Markdown 解析（图片 + frontmatter→Plan）
# ---------------------------------------------------------------------------


IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def is_remote(src: str) -> bool:
    return src.startswith(("http://", "https://", "//"))


def scan_images(body: str, md_dir: Path) -> list[ImageRef]:
    refs: list[ImageRef] = []
    for m in IMG_RE.finditer(body):
        alt, src = m.group(1), m.group(2)
        remote = is_remote(src)
        local_path: Path | None = None
        if not remote:
            local_path = (md_dir / src).resolve() if not Path(src).is_absolute() else Path(src)
        refs.append(ImageRef(raw=m.group(0), alt=alt, src=src, is_remote=remote, local_path=local_path))
    return refs


def build_plan(md_path: Path, cli_title: str | None, default_category: str | None) -> Plan:
    # 延后 import 避免 frontmatter 在 _common 顶部就被加载（让 _common 自身保持零依赖）
    sys.path.insert(0, str(Path(__file__).parent))
    import frontmatter as fm  # type: ignore[import-not-found]

    data, body = fm.load(md_path)
    title = cli_title or data.get("title") or md_path.stem
    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return Plan(
        md_path=md_path,
        title=str(title),
        category=data.get("category") or default_category,
        column=data.get("column"),
        tags=[str(t) for t in tags],
        cover=data.get("cover"),
        summary=data.get("summary"),
        body=body,
        images=scan_images(body, md_path.parent),
    )


# ---------------------------------------------------------------------------
# CDN URL 提取：上传响应 JSON 字段名各平台不同，列穷举法
# ---------------------------------------------------------------------------


def extract_cdn_url(data: Any) -> str | None:
    """从上传接口的 JSON 响应里挖出 CDN URL。

    常见字段：url / image_url / src / fileUrl / file_url / path / data 嵌套。
    递归探查，命中第一个 http 开头的字符串即返回。
    """
    if isinstance(data, str):
        return data if data.startswith("http") else None
    if isinstance(data, list):
        for item in data:
            u = extract_cdn_url(item)
            if u:
                return u
        return None
    if not isinstance(data, dict):
        return None
    # 优先查常见名
    for key in ("url", "image_url", "imageUrl", "src", "fileUrl", "file_url", "path", "ossUrl"):
        v = data.get(key)
        if isinstance(v, str) and v.startswith("http"):
            return v
    # 再下钻
    for key in ("data", "result", "body", "payload"):
        v = data.get(key)
        if v is not None:
            u = extract_cdn_url(v)
            if u:
                return u
    return None


# ---------------------------------------------------------------------------
# 编辑器写入：清空 + 写入正文。CodeMirror / Bytemd / contenteditable / textarea 都适用
# ---------------------------------------------------------------------------


def write_into_editor(page: "Page", editor_selector: str, body: str) -> None:
    """点击编辑器 → Cmd/Ctrl+A → Delete → 写入。

    优先走 CodeMirror 6 的 dispatch API（直接 setValue 整段），这比 keyboard.insert_text
    快得多——大文本（>5KB）时 insert_text 会逐字符触发 InputEvent + markdown 重解析，
    在飞帆 md-editor-v3 上能把 CM6 锁死好几分钟。dispatch 一次性替换是 O(1)。

    退路：如果 CM6 实例找不到（CM5 / 普通 textarea / contenteditable），回落到
    原来的 keyboard 流程。
    """
    page.locator(editor_selector).first.click()

    # 优先：CM6 dispatch 整段替换
    cm6_ok = page.evaluate("""(body) => {
        // CodeMirror 6 实例通常挂在 .cm-editor 的 CodeMirror 元素上，但暴露方式因包装而异。
        // 通用兜底：找一个 .cm-editor，再从它的 cmView/EditorView 拿 view。
        const root = document.querySelector('.cm-editor');
        if (!root) return false;
        // @codemirror/view 把 EditorView 实例挂在 .cm-editor 的 _view 字段（实测 md-editor-v3）。
        // 不同版本字段名不同，依次试：_view / view / __view
        const view = root._view || root.view || root.__view ||
                     (root.firstChild && (root.firstChild._view || root.firstChild.view));
        if (!view || typeof view.dispatch !== 'function') return false;
        const len = view.state.doc.length;
        view.dispatch({changes: {from: 0, to: len, insert: body}});
        return true;
    }""", body)
    if cm6_ok:
        return

    # 兜底：传统键盘流程（适用于 CM5 / textarea / contenteditable）
    is_mac = sys.platform == "darwin"
    mod = "Meta" if is_mac else "Control"
    page.keyboard.press(f"{mod}+A")
    page.keyboard.press("Delete")
    page.keyboard.insert_text(body)


def press_save_shortcut(page: "Page") -> None:
    mod = "Meta" if sys.platform == "darwin" else "Control"
    page.keyboard.press(f"{mod}+S")


# ---------------------------------------------------------------------------
# 替换正文里的本地路径
# ---------------------------------------------------------------------------


def rewrite_local_image_urls(body: str, mapping: dict[str, str]) -> str:
    """把 `]({old})` 形式整体替换；不动 src 后跟 title 的部分。"""
    out = body
    for old, new in mapping.items():
        out = out.replace(f"]({old})", f"]({new})")
    return out


# ---------------------------------------------------------------------------
# 图片上传：真实系统剪贴板 + 真实 ⌘V/Ctrl+V
# ---------------------------------------------------------------------------
# 实测教训：现代 markdown 编辑器（bytemd、Lexical、Slate 等）的图片接收口大多在
# paste/drop handler 上，而不是 file input。但 JS 合成 ClipboardEvent 的 clipboardData
# 是 readonly，带不动真实 File 对象——编辑器收不到。唯一稳定的等价路径是：
#   1. 把图片写进真实操作系统剪贴板
#      - macOS: osascript + sips（PNG 格式）
#      - Windows: PowerShell + System.Windows.Forms.Clipboard
#   2. focus 目标编辑器
#   3. 发**真实的** ⌘/Ctrl+V 键事件，Chromium 会读真实系统剪贴板
# 这样编辑器的 paste handler 收到的是真实 DataTransfer，能正常走自家上传管道。


_MD_IMG_URL_RE = re.compile(r'!\[[^\]]*\]\(((?:https?:)?/[^\s)]+)')
# ↑ 接受三种 URL 形态：http://, https://, 以及 / 开头的站内相对路径（飞帆返回 /oss/...）。
#   注意：本地路径如 ./img/x.png 不会匹配——这是有意的，避免把待替换的本地引用算作"已有 URL"。


def diff_new_image_urls(before: str, after: str) -> list[str]:
    """返回 after 中新增、before 中没有的图片 URL（按出现顺序）。"""
    before_set = set(_MD_IMG_URL_RE.findall(before))
    seen: set[str] = set()
    new: list[str] = []
    for url in _MD_IMG_URL_RE.findall(after):
        if url in before_set or url in seen:
            continue
        if "Uploading" in url or url.endswith("/0"):
            continue
        seen.add(url)
        new.append(url)
    return new


def get_editor_markdown(page: "Page") -> str:
    """从 CodeMirror / bytemd 编辑器读出当前 markdown。

    覆盖三种形态：CodeMirror 5 实例对象、CodeMirror 6 的 .cm-content、
    底层镜像 textarea。其他编辑器（Monaco、Lexical 等）可能需要扩展。
    """
    return page.evaluate("""() => {
        const cm5 = document.querySelector('.CodeMirror');
        if (cm5 && cm5.CodeMirror) return cm5.CodeMirror.getValue();
        const cm6 = document.querySelector('.bytemd-editor .cm-content, .cm-content');
        if (cm6) return cm6.innerText;
        const ta = document.querySelector('.bytemd textarea, textarea.bytemd-editor');
        if (ta) return ta.value;
        // 兜底：找 contenteditable
        const ce = document.querySelector('[contenteditable="true"]');
        if (ce) return ce.innerText;
        return '';
    }""")


def load_image_to_clipboard(path: Path) -> bool:
    """把图片放进操作系统剪贴板，跨平台。

    - **macOS**：osascript `set the clipboard to (read ... as «class PNGf»)`。
      该命令只认 PNG，所以非 PNG 先用 sips 转 PNG。
    - **Windows**：PowerShell + .NET 的 `[System.Windows.Forms.Clipboard]::SetImage()`。
      `System.Drawing.Image.FromFile` 原生支持 PNG/JPG/GIF/BMP/TIFF，**不需要先转 PNG**。
      必须用 STA 线程（PowerShell 5.x 的 `powershell.exe -Sta`；pwsh 7+ 默认 MTA 所以也加 -Sta）。
    - **Linux**：未实现。占位返回 False 并提示用户。可选实现方向：xclip / wl-copy。
    """
    import subprocess

    if sys.platform == "darwin":
        return _load_image_to_clipboard_macos(path)
    if sys.platform == "win32":
        return _load_image_to_clipboard_windows(path)
    print(
        "   ⚠️ 剪贴板上传暂不支持当前平台（仅 macOS + Windows）。\n"
        "   Linux 用户可以参考 _common.py 实现 xclip / wl-copy 版本。",
        file=sys.stderr,
    )
    return False


def _load_image_to_clipboard_macos(path: Path) -> bool:
    import subprocess
    import tempfile

    png_path = path
    if path.suffix.lower() != ".png":
        tmp = Path(tempfile.gettempdir()) / f"_clip_{path.stem}.png"
        try:
            subprocess.run(
                ["sips", "-s", "format", "png", str(path), "--out", str(tmp)],
                check=True, capture_output=True,
            )
            png_path = tmp
        except Exception as e:  # noqa: BLE001
            print(f"   ⚠️ sips 转 PNG 失败：{e}", file=sys.stderr)
            return False

    script = f'set the clipboard to (read (POSIX file "{png_path}") as «class PNGf»)'
    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ osascript 写剪贴板失败：{e}", file=sys.stderr)
        return False


def _load_image_to_clipboard_windows(path: Path) -> bool:
    """Windows: PowerShell + .NET Forms 写图片到剪贴板。

    用 -EncodedCommand 传脚本：把 PowerShell 脚本 UTF-16-LE 编码再 base64，
    一并通过命令行喂给 powershell.exe——这是 PowerShell 官方的脚本传递方式，
    完全绕开 shell 转义（路径里的空格、引号、$ 都不会出问题）。

    路径用 PowerShell single-quoted 字符串，规则只需把 `'` 转义成 `''`。

    需要 powershell.exe（Windows 10/11 默认）；不强依赖 pwsh。
    """
    import base64
    import subprocess

    abs_path = str(path.resolve())
    quoted = abs_path.replace("'", "''")  # PowerShell single-quote 转义
    ps_script = (
        "Add-Type -AssemblyName System.Windows.Forms\n"
        "Add-Type -AssemblyName System.Drawing\n"
        f"$img = [System.Drawing.Image]::FromFile('{quoted}')\n"
        "[System.Windows.Forms.Clipboard]::SetImage($img)\n"
        "$img.Dispose()\n"
    )
    encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")

    try:
        # -Sta：STA 线程才能用 Clipboard.SetImage
        # -NoProfile：跳过 $PROFILE，启动更快且避免用户配置干扰
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Sta", "-EncodedCommand", encoded],
            check=True, capture_output=True, timeout=15,
        )
        return True
    except FileNotFoundError:
        print(
            "   ⚠️ 没找到 powershell.exe——你的系统不像是标准 Windows？",
            file=sys.stderr,
        )
        return False
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace").strip() \
              or (e.stdout or b"").decode("utf-8", errors="replace").strip()
        print(f"   ⚠️ PowerShell 写剪贴板失败：{err}", file=sys.stderr)
        return False
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ 调用 PowerShell 失败：{e}", file=sys.stderr)
        return False


def upload_image_via_clipboard(
    page: "Page",
    local_path: Path,
    editor_selector: str,
    timeout_s: int = 30,
) -> str | None:
    """通用剪贴板上传：写剪贴板 → focus 编辑器 → 真实 ⌘V → diff 出新 URL。

    适用于任何接受 paste 事件且会自动插入 markdown 图片引用的编辑器
    （bytemd / CodeMirror / 类似实现）。返回 CDN URL 或 None。

    调用方负责再用 `rewrite_local_image_urls` 把原本地路径替换成 CDN URL。
    """
    before = get_editor_markdown(page)

    if not load_image_to_clipboard(local_path):
        return None

    try:
        editor = page.locator(editor_selector).first
        editor.click()
        mod = "Meta" if sys.platform == "darwin" else "Control"
        page.keyboard.press(f"{mod}+End")
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ focus 编辑器失败：{e}", file=sys.stderr)
        return None

    mod = "Meta" if sys.platform == "darwin" else "Control"
    page.keyboard.press(f"{mod}+v")

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(0.5)
        now = get_editor_markdown(page)
        new_urls = diff_new_image_urls(before, now)
        if new_urls:
            return new_urls[0]

    print(f"   ⚠️ {timeout_s}s 内编辑器没出现新图片 URL", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------


def wait_for(predicate, timeout_ms: int = 10000, interval_ms: int = 200) -> bool:
    deadline = time.time() + timeout_ms / 1000.0
    while time.time() < deadline:
        try:
            if predicate():
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(interval_ms / 1000.0)
    return False


def lazy_import_playwright():
    """统一的「找不到 playwright 就给友好提示」入口。"""
    try:
        import browser_cdp as _bcdp  # type: ignore[import-not-found]
        from playwright.sync_api import TimeoutError as PWT
    except ModuleNotFoundError as e:
        print(
            f"❌ 缺少依赖：{e.name}\n"
            "   先 `pip install -r scripts/requirements.txt` 并 `playwright install chromium`",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return _bcdp, PWT


def echo_plan(plan: Plan, mode: str, platform: str) -> None:
    """运行前回显计划，方便用户拦截错误的发布。"""
    print(
        f"📝 准备发布到 [{platform}]: {plan.title}\n"
        f"   分类: {plan.category or '(未指定)'}\n"
        f"   标签: {plan.tags or '(无)'}\n"
        f"   图片: {len(plan.images)} 张 (本地 {sum(1 for i in plan.images if not i.is_remote)})\n"
        f"   模式: {mode}",
        file=sys.stderr,
    )
