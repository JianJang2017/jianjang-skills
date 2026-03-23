---
description: "生成 API 接口文档（Markdown 格式）"
argument-hint: "<目录或文件路径> [--output <输出文件>]"
allowed-tools: Read, Write, Glob, Grep, Bash(open *)
---

## 技能说明

!`cat "${CLAUDE_PLUGIN_ROOT}/SKILL.md"`

## 用户参数

$ARGUMENTS

## 执行规则

根据参数中的路径扫描代码，生成 Markdown 格式的 API 文档。

- 如果参数包含 `--output <文件>`，保存到指定路径
- 否则：接口 ≤ 5 个直接输出，> 5 个保存为同目录下的 `api_doc.md`
- 如果参数为空，用 AskUserQuestion 询问用户要分析的目录或文件路径

格式规范参考：`${CLAUDE_PLUGIN_ROOT}/references/format-template.md`
