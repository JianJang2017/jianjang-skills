#!/usr/bin/env python3
"""校验生成的 HTML 是否符合"公众号/邮件可直接粘贴"的约束。

公众号编辑器和多数邮件客户端会丢弃 <style> 块、外部样式表和 class/id 选择器，
只保留内联 style="..."。所以排版必须全内联。这个脚本做一次快速体检，
把常见会"在编辑器里掉样式"的写法挑出来，避免人工逐行检查。

用法：
    python validate_html.py output.html
    python validate_html.py output.html --strict   # 有任何告警就以非 0 退出

检查项：
  - <style> / <link rel=stylesheet> 等外部或全局样式（公众号会丢弃）
  - class= / id=  选择器（无对应内联样式时无效）
  - <script>（公众号会清除，且非排版所需）
  - 缺少 <meta charset>（中文易乱码）
  - 容器宽度是否设了 max-width（移动端阅读体验）
退出码：0 = 通过；1 = 有问题（strict 模式或硬错误）。
"""
import argparse
import re
import sys


def check(html_text: str):
    errors = []
    warnings = []

    if re.search(r"<style[\s>]", html_text, re.I):
        errors.append("发现 <style> 块：公众号编辑器会丢弃，样式需全部内联到 style 属性")
    if re.search(r"<link[^>]+stylesheet", html_text, re.I):
        errors.append("发现外部样式表 <link rel=stylesheet>：粘贴后样式会全部丢失")
    if re.search(r"<script[\s>]", html_text, re.I):
        errors.append("发现 <script>：公众号会清除，排版不应依赖脚本")

    for m in re.finditer(r"\sclass\s*=", html_text, re.I):
        warnings.append("发现 class= 属性：没有内联样式时不会生效，请改为 style=")
        break
    for m in re.finditer(r"\sid\s*=", html_text, re.I):
        warnings.append("发现 id= 属性：通常无用，且不应作为样式钩子")
        break

    if not re.search(r"<meta[^>]+charset", html_text, re.I):
        warnings.append("缺少 <meta charset>：中文可能乱码，建议加 <meta charset=\"utf-8\">")
    if not re.search(r"max-width\s*:", html_text, re.I):
        warnings.append("未发现 max-width：移动端建议外层容器设 max-width(约 680px)")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="校验内联样式 HTML 是否可直接粘贴")
    parser.add_argument("file", help="待校验的 HTML 文件")
    parser.add_argument("--strict", action="store_true", help="有告警也判失败")
    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        html_text = f.read()

    errors, warnings = check(html_text)

    for e in errors:
        print(f"[错误] {e}")
    for w in warnings:
        print(f"[告警] {w}")

    if not errors and not warnings:
        print("[通过] 未发现明显问题，HTML 可直接粘贴到公众号/邮件")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
