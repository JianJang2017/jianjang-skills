---
description: "生成 API 接口文档（HTML 格式，带分级菜单）"
argument-hint: "<目录或文件路径> [--output <输出文件>]"
allowed-tools: Read, Write, Glob, Grep, Bash(open *)
---

## 技能说明

!`cat "${CLAUDE_PLUGIN_ROOT}/SKILL.md"`

## HTML 模板

!`cat "${CLAUDE_PLUGIN_ROOT}/references/html-template.md"`

## 用户参数

$ARGUMENTS

## 执行规则

根据参数中的路径扫描代码，生成 HTML 格式的 API 文档：

- 如果参数包含 `--output <文件>`，保存到指定路径
- 否则保存为同目录下的 `api_doc.html`
- 如果参数为空，用 AskUserQuestion 询问用户要分析的目录或文件路径
- 生成完成后根据操作系统打开文件：macOS 用 `open <路径>`，Linux 用 `xdg-open <路径>`，Windows 用 `start <路径>`；无法判断时告知用户文件路径，让其手动打开

HTML 要求：左侧固定导航按模块分级，右侧接口卡片可展开，HTTP 方法色块，请求/响应 tab 切换，纯单文件无外部依赖。
