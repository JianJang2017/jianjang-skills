#!/usr/bin/env python3
"""把代码块/流程图文本转换成内联 HTML 可直接嵌入的片段。

公众号和邮件 HTML 不能依赖 <pre>/<code> 的空白折叠和外部样式，所以代码块
统一渲染成一个 <p>，内部用 &nbsp; 保留缩进、用 <br> 换行。这个脚本把这步做成
确定性的，避免每次手工转义出错（漏转义 < > & 会破坏排版甚至注入标签）。

用法：
    # 从标准输入读取，打印转义后的片段（只含正文，不含外层 <p>）
    python escape_code.py < snippet.txt

    # 从文件读取
    python escape_code.py --in snippet.txt

输出的字符串可直接替换主题代码块组件里的 {{escaped_code_with_br_and_nbsp}}。
"""
import argparse
import html
import sys


def escape_code(text: str) -> str:
    """HTML 转义后，前导空格转 &nbsp;，换行转 <br>。"""
    # 先去掉结尾多余换行，避免末尾冒出空行
    text = text.rstrip("\n")
    lines = text.split("\n")
    out_lines = []
    for line in lines:
        # 转义 & < > " 等，防止破坏 HTML 结构
        escaped = html.escape(line, quote=False)
        # 行内所有空格都转 &nbsp;，保留缩进和对齐（制表符按 4 空格展开）
        escaped = escaped.replace("\t", "    ").replace(" ", "&nbsp;")
        out_lines.append(escaped)
    return "<br>".join(out_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="转义代码块文本为内联 HTML 片段")
    parser.add_argument("--in", dest="infile", help="输入文件，默认读 stdin")
    args = parser.parse_args()

    if args.infile:
        with open(args.infile, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    sys.stdout.write(escape_code(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
