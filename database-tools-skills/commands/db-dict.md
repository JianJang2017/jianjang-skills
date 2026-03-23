---
description: "导出数据库数据字典，支持 Markdown 和 HTML 格式（HTML 含左侧菜单导航）"
argument-hint: "[pg|mysql] dict -s <schema> [-f markdown|html] [-t 表名...] [-o 输出文件] [连接参数]"
allowed-tools: Bash(python3 *), Bash(open *)
---

## 已配置的数据库 profile

!`python3 "${CLAUDE_PLUGIN_ROOT}/db.py" config list 2>/dev/null || echo "（无已配置 profile）"`

## 执行数据字典导出

用户参数：$ARGUMENTS

运行命令：
!`python3 "${CLAUDE_PLUGIN_ROOT}/db.py" $ARGUMENTS`

将命令输出结果呈现给用户。如果写入了文件，告知文件路径和包含的表数量。

**HTML 格式**：如果输出了 `.html` 文件，自动在浏览器中打开：
```
open <输出文件路径>
```

如果参数不完整（缺少数据库类型或 schema），用 AskUserQuestion 询问用户：
1. 数据库类型（PostgreSQL / MySQL）
2. Schema / 数据库名
3. 输出格式（Markdown 文档 / HTML 交互文档）
4. 连接信息（如无 profile）

**格式说明**：
- `--format markdown`（默认）：纯文本 Markdown，适合纳入 git 或粘贴到文档
- `--format html`：带左侧菜单导航的 HTML，支持表名搜索和滚动高亮，适合浏览器查阅
