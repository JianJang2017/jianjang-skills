---
description: "数据库工具 — pg/mysql 结构查看、DDL、数据字典（Markdown/HTML）、Seed 数据导出、性能分析、结构对比"
argument-hint: "[pg|mysql] [子命令] [选项]"
allowed-tools: Bash(python3 *), Bash(open *), Read, Write
---

## 可用 profile

!`python3 "${CLAUDE_PLUGIN_ROOT}/db.py" config list 2>/dev/null || echo "（无已配置 profile）"`

## 用户请求

用户输入的参数：$ARGUMENTS

## 执行规则

根据参数直接运行对应命令：

```
python3 "${CLAUDE_PLUGIN_ROOT}/db.py" $ARGUMENTS
```

**常用命令示例：**

| 用途 | 命令 |
|------|------|
| 列出 PG schema | `pg schemas` |
| 列出表 | `pg tables -s public` |
| 查看表结构 | `pg inspect -s public` |
| 生成 DDL | `pg ddl -s public -o init.sql` |
| 导出数据字典（Markdown） | `pg dict -s public -o dict.md` |
| 导出数据字典（HTML） | `pg dict -s public -f html -o dict.html` |
| 导出指定表数据字典 | `pg dict -s public -t users orders -o dict.md` |
| 性能分析报告 | `pg report -s public -o report.md` |
| 优化脚本 | `pg optimize -s public -o optimize.sql` |
| 导出 Seed 数据 | `pg seed -s public -o seed.sql` |
| 导出指定表 Seed | `pg seed -s public -t users roles -o seed.sql` |
| MySQL 数据字典（Markdown） | `mysql dict -s mydb -o dict.md` |
| MySQL 数据字典（HTML） | `mysql dict -s mydb -f html -o dict.html` |
| MySQL Seed 数据 | `mysql seed -s mydb -l 100 -o seed.sql` |
| 结构对比 | `diff --source dev --target prod` |
| 导出快照 | `snapshot --profile dev -o snap.json` |
| 查看 profile | `config list` |

如果参数为空或不完整，先展示上方 profile 列表，再用 AskUserQuestion 询问用户：
1. 数据库类型（PostgreSQL / MySQL）
2. 要执行的操作
3. 连接信息（如无 profile）

执行完毕后简洁呈现结果。若输出为文件，告知路径和包含的表数量。若输出为 `.html` 文件，自动执行 `open <文件路径>` 在浏览器中打开。
