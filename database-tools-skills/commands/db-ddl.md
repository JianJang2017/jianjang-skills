---
description: "生成数据库 DDL 初始化脚本"
argument-hint: "[pg|mysql] ddl -s <schema> [-o 输出文件] [连接参数]"
allowed-tools: Bash(python3 *)
---

## 已配置的数据库 profile

!`python3 "${CLAUDE_PLUGIN_ROOT}/db.py" config list 2>/dev/null || echo "（无已配置 profile）"`

## 执行 DDL 导出

用户参数：$ARGUMENTS

运行命令：
!`python3 "${CLAUDE_PLUGIN_ROOT}/db.py" $ARGUMENTS`

告知用户文件路径，说明脚本包含的对象类型。PG DDL 包含 EXTENSION/TYPE/SEQUENCE/FUNCTION/TRIGGER；MySQL 默认用 SHOW CREATE TABLE 快速模式。
