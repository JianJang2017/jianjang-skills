---
description: "生成 Postman / Apifox Collection JSON"
argument-hint: "<目录或文件路径> [--output <输出文件>] [--base-url <基础URL>]"
allowed-tools: Read, Write, Glob, Grep
---

## 技能说明

!`cat "${CLAUDE_PLUGIN_ROOT}/SKILL.md"`

## Postman 格式规范

!`cat "${CLAUDE_PLUGIN_ROOT}/references/postman-format.md"`

## 用户参数

$ARGUMENTS

## 执行规则

根据参数中的路径扫描代码，生成 Postman Collection v2.1 JSON：

- 如果参数包含 `--output <文件>`，保存到指定路径
- 否则保存为同目录下的 `api_collection.json`
- 如果参数包含 `--base-url <url>`，用该值作为 `base_url` 变量默认值，否则用 `http://localhost:8080`
- 如果参数为空，用 AskUserQuestion 询问用户要分析的目录或文件路径

生成的 JSON 可直接导入 Postman 或 Apifox（选择 Postman 格式导入）。
生成完成后告知接口数量和文件路径。
