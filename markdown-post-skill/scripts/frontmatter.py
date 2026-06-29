"""轻量 YAML frontmatter 解析。

只支持 markdown-post-skill 实际用到的几种字段类型：
- 字符串：`title: foo`、`title: "带:冒号"`、`title: '带"引号"'`
- 数字/布尔会被当字符串保留（掘金字段都是字符串/枚举，不需要 typed parsing）
- 数组：行内 `tags: [a, b, c]` 或多行 `tags:\n  - a\n  - b`

故意不引 PyYAML，省一个依赖；这个文件只解析自己定义的 frontmatter，不是通用 YAML 解析器。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _parse_inline_list(s: str) -> list[str]:
    # `[a, b, "c, d"]` -> ["a", "b", "c, d"]
    inner = s.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    # 简单按逗号切分，再去引号——掘金 tag 名里没逗号，足够用
    out: list[str] = []
    cur = ""
    in_q: str | None = None
    for ch in inner:
        if in_q:
            cur += ch
            if ch == in_q:
                in_q = None
            continue
        if ch in ("'", '"'):
            in_q = ch
            cur += ch
            continue
        if ch == ",":
            v = _strip_quotes(cur)
            if v:
                out.append(v)
            cur = ""
            continue
        cur += ch
    v = _strip_quotes(cur)
    if v:
        out.append(v)
    return out


def parse(md_text: str) -> tuple[dict[str, Any], str]:
    """返回 (frontmatter dict, body 字符串)。没有 frontmatter 时返回 ({}, md_text)。"""
    m = FRONTMATTER_RE.match(md_text)
    if not m:
        return {}, md_text
    raw = m.group(1)
    body = md_text[m.end():]

    data: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in raw.split("\n"):
        if not line.strip():
            continue
        # 续接 list 项
        if current_list is not None and re.match(r"^\s+-\s", line):
            item = line.split("-", 1)[1].strip()
            current_list.append(_strip_quotes(item))
            continue
        # 否则结束之前的 list
        if current_list is not None:
            data[current_key] = current_list  # type: ignore[index]
            current_list = None
            current_key = None

        m2 = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if not m2:
            continue
        key, val = m2.group(1), m2.group(2).strip()
        if val == "":
            # 开启一个 list 累积块
            current_key = key
            current_list = []
            continue
        if val.startswith("[") and val.endswith("]"):
            data[key] = _parse_inline_list(val)
            continue
        data[key] = _strip_quotes(val)

    if current_list is not None and current_key:
        data[current_key] = current_list

    return data, body


def load(path: str | Path) -> tuple[dict[str, Any], str]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return parse(text)
