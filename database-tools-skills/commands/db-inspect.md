---
description: "查看数据库表结构（schema/tables/inspect）"
argument-hint: "[pg|mysql] [schemas|tables|inspect] -s <schema> [连接参数]"
allowed-tools: Bash(python3 *)
---

## 已配置的数据库 profile

!`python3 "${CLAUDE_PLUGIN_ROOT}/db.py" config list 2>/dev/null || echo "（无已配置 profile）"`

## 执行结构查看

用户参数：$ARGUMENTS

运行命令：
!`python3 "${CLAUDE_PLUGIN_ROOT}/db.py" $ARGUMENTS`

将结果以简洁方式呈现给用户，重点说明表数量、核心表的字段和索引情况。

如果参数不完整，用 AskUserQuestion 询问：数据库类型、要查看的内容（schema 列表 / 表列表 / 表结构详情）、连接信息。
