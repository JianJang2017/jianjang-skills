# JianJang Skills

Claude Code skill collection providing practical tools for database management and API documentation generation.

**[中文文档](./README.md)**

---

## 📦 Skill List

### 1. Database Tools Skills

PostgreSQL / MySQL database toolkit. View structure, export DDL, performance analysis, index optimization, export data dictionary, cross-database comparison.

**Key Features**
- 📊 View database structure (schema, tables, fields, indexes, constraints)
- 📝 Generate DDL initialization scripts (including EXTENSION/TYPE/SEQUENCE/FUNCTION/TRIGGER)
- 📖 Export data dictionary (Markdown and HTML formats, HTML with fixed sidebar navigation)
- 🔍 Performance analysis reports (unused indexes, redundant indexes, missing foreign key indexes, slow queries, table bloat)
- ⚡ Generate optimization scripts (create missing indexes, remove unused/redundant indexes, table maintenance)
- 💾 Export initialization data (Seed INSERT statements)
- 🔄 Structure comparison and migration (auto-generate ALTER TABLE migration DDL for same engine)
- 📸 Structure snapshots (JSON format, supports version control and offline comparison)

**Supported Databases**
- PostgreSQL (9.6+)
- MySQL (5.7+)

**Usage**
```bash
# View structure
/db pg tables -s public
/db pg inspect -s public -t users

# Export DDL
/db pg ddl -s public -o init.sql

# Export data dictionary
/db-dict pg dict -s public -o dict.md
/db pg dict -s public -f html -o dict.html

# Performance analysis
/db-report pg report -s public -o report.md
/db pg optimize -s public -o optimize.sql

# Export initialization data
/db pg seed -s public -o seed.sql

# Structure comparison
/db diff --source dev --target prod
```

**Installation**
```bash
# Python version requirement: >= 3.9

# PostgreSQL support
pip install psycopg2-binary

# MySQL support
pip install pymysql

# Copy database-tools-skills directory to ~/.claude/skills/
```

**Documentation**: [database-tools-skills/README.md](./database-tools-skills/README.md)

---

### 2. API Generator Skill

Automatically generates standard API documentation from project source code. Supports multiple frameworks with output in Markdown, HTML, and Postman/Apifox Collection formats.

**Key Features**
- 🔍 Automatically scan project code and identify API endpoints
- 🧠 Smart inference of parameter information (fills in missing details from context, marked as "(inferred)")
- 📄 Three output formats:
  - Markdown (standard format with full request/response parameter tables)
  - HTML (with sidebar navigation, HTTP method badges, request/response tab switching)
  - Postman / Apifox Collection JSON (v2.1 spec, ready to import)
- 📁 Auto-detect controller/router/handler directories, skip test files
- 🌳 Nested parameter expansion (dot notation, e.g., `data.userInfo.userId`)

**Supported Frameworks**
- Spring Boot (Java)
- Express.js (TypeScript/JavaScript)
- FastAPI (Python)
- Flask (Python)
- Gin (Go)
- Koa (TypeScript/JavaScript)

**Usage**
```bash
# Generate Markdown documentation
/api-doc ./src/main/java/com/example/controller
/api-doc UserController.java --output ./docs/user-api.md

# Generate HTML documentation (auto-opens in browser)
/api-doc-html ./src/routes/order.ts

# Generate Postman/Apifox Collection
/api-doc-postman ./src --base-url http://api.example.com
```

**Installation**
```bash
# Copy api-generator-skill directory to ~/.claude/skills/
```

**Documentation**: [api-generator-skill/README.md](./api-generator-skill/README.md)

---

## 🚀 Quick Start

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/jianjang-skills.git
cd jianjang-skills
```

2. Copy skills to Claude Code skills directory:
```bash
# Copy all skills
cp -r api-generator-skill ~/.claude/skills/
cp -r database-tools-skills ~/.claude/skills/

# Or copy only the skills you need
cp -r api-generator-skill ~/.claude/skills/
```

3. Install dependencies (if using database-tools-skills):
```bash
# PostgreSQL support
pip install psycopg2-binary

# MySQL support
pip install pymysql
```

### Usage

In Claude Code, skills will trigger automatically, or use slash commands:

```bash
# API documentation generation
/api-doc ./src/controller
/api-doc-html ./src/routes

# Database tools
/db pg tables -s public
/db-dict pg dict -s public -o dict.html
/db-report pg report -s public
```

---

## 📝 Skill Comparison

| Aspect | Database Tools | API Generator |
|--------|---|---|
| Primary Use | Database metadata management, performance optimization | API documentation generation |
| Input | Database connection info | Project code directory or files |
| Output Formats | Markdown, HTML, JSON, SQL scripts | Markdown, HTML, JSON (Postman) |
| Dependencies | psycopg2-binary, pymysql | No external dependencies |
| Use Cases | Database operations, structure management, performance tuning | API documentation, interface management |

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

MIT License

