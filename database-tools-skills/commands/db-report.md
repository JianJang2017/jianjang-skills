---
description: "数据库索引性能分析与优化脚本生成"
argument-hint: "[pg|mysql] [report|optimize] -s <schema> [-o 输出文件] [连接参数]"
allowed-tools: Bash(python3 *)
---

## 已配置的数据库 profile

!`python3 "${CLAUDE_PLUGIN_ROOT}/db.py" config list 2>/dev/null || echo "（无已配置 profile）"`

## 执行性能分析

用户参数：$ARGUMENTS

运行命令：
!`python3 "${CLAUDE_PLUGIN_ROOT}/db.py" $ARGUMENTS`

将报告中的关键发现呈现给用户：未使用索引数量、冗余索引、慢查询 Top 3、表膨胀情况。

如果生成了优化脚本，提醒用户：删除索引前务必确认无用，建议先在测试环境执行。
