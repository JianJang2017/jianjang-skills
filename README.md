# JianJang Skills

Claude Code 技能集合，提供数据库管理和 API 文档生成等实用工具。

**[English](./README_EN.md)**

---

## 📦 技能列表

### 1. Database Tools Skills（数据库工具集）

PostgreSQL / MySQL 数据库工具集。查结构、导 DDL、性能分析、索引优化、导出数据字典、跨库对比。

**主要功能**
- 📊 查看数据库结构（schema、表、字段、索引、约束）
- 📝 生成 DDL 初始化脚本（含 EXTENSION/TYPE/SEQUENCE/FUNCTION/TRIGGER）
- 📖 导出数据字典（Markdown 和 HTML 两种格式，HTML 带左侧固定导航菜单）
- 🔍 性能分析报告（未使用索引、冗余索引、缺失外键索引、慢查询、表膨胀等）
- ⚡ 生成优化脚本（创建缺失索引、删除未使用/冗余索引、表维护）
- 💾 导出初始化数据（Seed INSERT 语句）
- 🔄 结构对比与迁移（同引擎自动生成 ALTER TABLE 迁移 DDL）
- 📸 结构快照（JSON 格式，支持版本控制和离线对比）

**支持的数据库**
- PostgreSQL（9.6+）
- MySQL（5.7+）

**使用方式**
```bash
# 查看结构
/db pg tables -s public
/db pg inspect -s public -t users

# 导出 DDL
/db pg ddl -s public -o init.sql

# 导出数据字典
/db-dict pg dict -s public -o dict.md
/db pg dict -s public -f html -o dict.html

# 性能分析
/db-report pg report -s public -o report.md
/db pg optimize -s public -o optimize.sql

# 导出初始化数据
/db pg seed -s public -o seed.sql

# 结构对比
/db diff --source dev --target prod
```

**安装方法**
```bash
# Python 版本要求：>= 3.9

# PostgreSQL 支持
pip install psycopg2-binary

# MySQL 支持
pip install pymysql

# 将 database-tools-skills 目录复制到 ~/.claude/skills/ 下
```

**详细文档**：[database-tools-skills/README.md](./database-tools-skills/README.md)

---

### 2. API Generator Skill（API 文档生成器）

从项目代码自动生成标准 API 文档。支持多种框架，可输出 Markdown、HTML、Postman/Apifox Collection 三种格式。

**主要功能**
- 🔍 自动扫描项目代码，识别 API 接口
- 🧠 智能推断参数信息（不完整时根据上下文推断，标注「（推断）」）
- 📄 支持三种输出格式：
  - Markdown（标准格式，含完整请求/响应参数表格）
  - HTML（带左侧分级导航菜单、HTTP 方法色块、请求/响应 Tab 切换）
  - Postman / Apifox Collection JSON（v2.1 规范，可直接导入）
- 📁 自动识别 controller、router、handler 等目录，跳过测试文件
- 🌳 嵌套参数展开（用点号表示，如 `data.userInfo.userId`）

**支持的框架**
- Spring Boot（Java）
- Express.js（TypeScript/JavaScript）
- FastAPI（Python）
- Flask（Python）
- Gin（Go）
- Koa（TypeScript/JavaScript）

**使用方式**
```bash
# 生成 Markdown 格式文档
/api-doc ./src/main/java/com/example/controller
/api-doc UserController.java --output ./docs/user-api.md

# 生成 HTML 格式文档（自动在浏览器打开）
/api-doc-html ./src/routes/order.ts

# 生成 Postman/Apifox Collection
/api-doc-postman ./src --base-url http://api.example.com
```

**安装方法**
```bash
# 将 api-generator-skill 目录复制到 ~/.claude/skills/ 下即可
```

**详细文档**：[api-generator-skill/README.md](./api-generator-skill/README.md)

---

## 🚀 快速开始

### 安装

1. 克隆本仓库：
```bash
git clone https://github.com/yourusername/jianjang-skills.git
cd jianjang-skills
```

2. 复制技能到 Claude Code 技能目录：
```bash
# 复制所有技能
cp -r api-generator-skill ~/.claude/skills/
cp -r database-tools-skills ~/.claude/skills/

# 或者只复制需要的技能
cp -r api-generator-skill ~/.claude/skills/
```

3. 安装依赖（如果使用 database-tools-skills）：
```bash
# PostgreSQL 支持
pip install psycopg2-binary

# MySQL 支持
pip install pymysql
```

### 使用

在 Claude Code 中，技能会自动触发，或者使用 slash commands：

```bash
# API 文档生成
/api-doc ./src/controller
/api-doc-html ./src/routes

# 数据库工具
/db pg tables -s public
/db-dict pg dict -s public -o dict.html
/db-report pg report -s public
```

---

## 📝 技能对比

| 方面 | Database Tools | API Generator |
|------|---|---|
| 主要用途 | 数据库元数据管理、性能优化 | API 文档自动生成 |
| 输入 | 数据库连接信息 | 项目代码目录或文件 |
| 输出格式 | Markdown、HTML、JSON、SQL 脚本 | Markdown、HTML、JSON（Postman） |
| 依赖 | psycopg2-binary、pymysql | 无外部依赖 |
| 适用场景 | 数据库运维、结构管理、性能优化 | API 文档生成、接口管理 |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

