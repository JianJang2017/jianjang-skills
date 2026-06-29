"""浏览器接入：CDP 复用已登录 Chrome / 持久化独立 profile 两条路径。

两种模式：

1. **CDP 接入**（`attach`）：用户已用 `--remote-debugging-port` 启动 Chrome 时走这条。
   复用用户主 profile 的全部 cookie/storage，零额外登录。**但 Chrome 136+ 禁止对默认
   用户数据目录开启远程调试端口**，所以这条路对很多人不再可用。

2. **持久化独立 profile**（`launch_persistent`）：Playwright 自己启动 chromium，把
   cookies 存到 skill 目录下的独立 user-data-dir。首次运行需要在新窗口里登录一次，
   之后这个 profile 长期复用——和 CDP 接入的体验几乎无差。

`get_context` 自动选择：CDP 端口能连上就走 CDP，否则回落到持久化 profile。
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse
from urllib.request import urlopen

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)


DEFAULT_CDP_URL = os.getenv("CDP_URL", "http://localhost:9222")

# 持久化 profile 存放位置。和 skill 目录同级是为了：
#   - 不污染用户主 Chrome
#   - 一次登录长期复用
#   - 想清除就 rm -rf 一下
PERSISTENT_PROFILE_DIR = Path(
    os.getenv("MARKDOWN_POST_PROFILE_DIR", str(Path.home() / ".markdown-post-skill" / "chrome-profile"))
)


def _check_cdp_reachable(cdp_url: str, timeout: float = 2.0) -> tuple[bool, str]:
    """快速 ping CDP 端口；失败时回友好提示。"""
    parsed = urlparse(cdp_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError as e:
        return False, f"TCP {host}:{port} 连不上 ({e})"
    # 拉一下 /json/version 确认是 CDP
    try:
        with urlopen(f"{cdp_url.rstrip('/')}/json/version", timeout=timeout) as r:
            data = json.load(r)
            return True, data.get("Browser", "unknown")
    except Exception as e:  # noqa: BLE001
        return False, f"{cdp_url}/json/version 不是合法 CDP 响应 ({e})"


def _print_startup_hint(cdp_url: str, why: str) -> None:
    """打印按平台定制的 Chrome 启动提示。

    自动回落到持久化 profile 时这条函数其实不会被触发（`get_context` 不调用 attach
    的失败路径），但保留它给"显式 --cdp-url 但连不上"的兜底。
    """
    if sys.platform == "darwin":
        launch = (
            "  # macOS\n"
            "  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\\n"
            "    --remote-debugging-port=9222 \\\n"
            "    --user-data-dir=\"$HOME/Library/Application Support/Google/Chrome\"\n\n"
            "  # 验证\n"
            "  curl http://localhost:9222/json/version\n"
        )
    elif sys.platform == "win32":
        launch = (
            "  # Windows PowerShell\n"
            "  & 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' `\n"
            "    --remote-debugging-port=9222 `\n"
            "    --user-data-dir=\"$env:LOCALAPPDATA\\Google\\Chrome\\User Data\"\n\n"
            "  # 验证\n"
            "  curl http://localhost:9222/json/version\n\n"
            "  # 提示：Chrome 136+ 安全限制不允许对默认 profile 启用远程调试。\n"
            "  #       这时直接重跑脚本，会自动回落到独立持久化 profile（首次需要登录一次）。\n"
        )
    else:
        launch = (
            "  # Linux\n"
            "  google-chrome --remote-debugging-port=9222 \\\n"
            "    --user-data-dir=\"$HOME/.config/google-chrome\"\n\n"
            "  # 验证\n"
            "  curl http://localhost:9222/json/version\n"
        )
    print(
        f"❌ 无法连接到 Chrome 的远程调试端口：{cdp_url}\n"
        f"   {why}\n\n"
        "请用 --remote-debugging-port 启动 Chrome（保留登录态），或直接重跑脚本让它\n"
        "走自动回落的持久化 profile 模式。\n\n"
        f"{launch}\n"
        "Chrome 起来后，在浏览器里登录目标平台再重跑本脚本。",
        file=sys.stderr,
    )


@contextmanager
def attach(cdp_url: str | None = None) -> Iterator[tuple[Playwright, Browser, BrowserContext]]:
    """以 context manager 形式接入 CDP，退出时只 disconnect，不关用户的 Chrome。"""
    url = cdp_url or DEFAULT_CDP_URL
    ok, info = _check_cdp_reachable(url)
    if not ok:
        _print_startup_hint(url, info)
        raise SystemExit(2)

    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(url)
        # CDP 接入后只有一个默认 context（用户主 profile），不要新建
        contexts = browser.contexts
        if not contexts:
            # 兜底：极少数情况下没有 context，新建一个
            ctx = browser.new_context()
        else:
            ctx = contexts[0]
        try:
            yield pw, browser, ctx
        finally:
            # 不调用 browser.close()——会把用户的整个 Chrome 关掉
            try:
                browser.close()  # CDP 模式下 close() 实际只 disconnect
            except Exception:  # noqa: BLE001
                pass
    finally:
        pw.stop()


@contextmanager
def launch_persistent(
    profile_dir: Path | None = None,
    headless: bool = False,
    login_check_url: str | None = None,
    login_indicator_selector: str | None = None,
) -> Iterator[tuple[Playwright, None, BrowserContext]]:
    """启动 Playwright 自己的 chromium，使用持久化 user-data-dir。

    第一次跑时这个目录是空的，目标网站会显示未登录——脚本会打开登录页让用户扫码/输入
    凭据，登录完毕后 cookies 写回目录，下次直接复用。

    返回 (Playwright, None, BrowserContext)；签名故意和 attach() 对齐，方便上层
    无差别使用。Browser 位返回 None 是因为 launch_persistent_context 只暴露 context。
    """
    pdir = profile_dir or PERSISTENT_PROFILE_DIR
    pdir.mkdir(parents=True, exist_ok=True)
    first_run = not any(pdir.iterdir())

    pw = sync_playwright().start()
    try:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(pdir),
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",  # 降低被反爬识别概率
            ],
            viewport={"width": 1440, "height": 900},
        )

        if first_run and login_check_url:
            print(
                f"🆕 首次运行：用 Playwright 启动独立 Chrome（profile: {pdir}）。\n"
                f"   请在弹出的窗口里登录目标网站后回到这里——脚本会自动检测。",
                file=sys.stderr,
            )

        if login_check_url:
            page = ctx.new_page()
            page.goto(login_check_url, wait_until="domcontentloaded")
            if login_indicator_selector:
                _wait_for_user_login(page, login_indicator_selector)

        try:
            yield pw, None, ctx
        finally:
            try:
                ctx.close()
            except Exception:  # noqa: BLE001
                pass
    finally:
        pw.stop()


def _wait_for_user_login(page: Page, indicator_selector: str, timeout_s: int = 600) -> None:
    """轮询登录态指示器；最多等 10 分钟（够用户扫码 + 手动登录）。"""
    print(
        f"⏳ 等待登录态出现（最多 10 分钟）...\n"
        f"   selector: {indicator_selector}",
        file=sys.stderr,
    )
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            page.wait_for_selector(indicator_selector, timeout=3000)
            print("✓ 检测到登录态，继续执行", file=sys.stderr)
            return
        except Exception:  # noqa: BLE001
            time.sleep(2)
    raise SystemExit(
        "❌ 10 分钟内没检测到登录态。请确认在弹出的 Chrome 窗口里完成了登录后重跑。"
    )


@contextmanager
def get_context(
    cdp_url: str | None = None,
    persistent_profile_dir: Path | None = None,
    login_check_url: str | None = None,
    login_indicator_selector: str | None = None,
    force_persistent: bool = False,
) -> Iterator[tuple[Playwright, Browser | None, BrowserContext]]:
    """统一入口：CDP 可达就走 CDP，否则回落到持久化 profile。

    `force_persistent=True` 强制走持久化模式（用于绕过现有 Chrome 不带 --remote-debugging-port
    的场景，避免一次失败的 CDP 探测）。
    """
    url = cdp_url or DEFAULT_CDP_URL
    if not force_persistent:
        ok, info = _check_cdp_reachable(url, timeout=1.0)
        if ok:
            print(f"✓ CDP 接入：{url} ({info})", file=sys.stderr)
            with attach(url) as bundle:
                yield bundle
            return
        print(
            f"ℹ️  CDP 不可用（{info}），改用持久化 profile 模式。\n"
            f"   profile: {persistent_profile_dir or PERSISTENT_PROFILE_DIR}",
            file=sys.stderr,
        )

    with launch_persistent(
        profile_dir=persistent_profile_dir,
        login_check_url=login_check_url,
        login_indicator_selector=login_indicator_selector,
    ) as bundle:
        yield bundle


def find_or_open(ctx: BrowserContext, url_prefix: str, fallback_url: str | None = None) -> Page:
    """在已有 tab 里找一个 URL 以 prefix 开头的；找不到就新开 fallback_url（或 prefix）。"""
    for page in ctx.pages:
        try:
            if page.url.startswith(url_prefix):
                return page
        except Exception:  # noqa: BLE001
            continue
    page = ctx.new_page()
    page.goto(fallback_url or url_prefix, wait_until="domcontentloaded")
    return page


def wait_for(predicate, timeout_ms: int = 10000, interval_ms: int = 200) -> bool:
    """轮询 predicate，True 则返回；超时返回 False。"""
    deadline = time.time() + timeout_ms / 1000.0
    while time.time() < deadline:
        try:
            if predicate():
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(interval_ms / 1000.0)
    return False
