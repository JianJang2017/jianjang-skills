# JianJang Skills

A collection of Claude Code skills covering enterprise development lifecycle, database operations, API documentation, Markdown formatting and illustration, email management, and Lark/Feishu collaboration.

**[中文文档](./README.md)**

---

## 📦 Skills Overview

| Skill | Purpose | Key Capabilities |
|---|---|---|
| [enterprise-dev-flow](./enterprise-dev-flow) | Enterprise dev lifecycle | PRD → design → task breakdown → test cases → test report, tuned for the Spring Cloud Alibaba stack |
| [database-tools-skills](./database-tools-skills) | Database operations | PostgreSQL/MySQL inspection, DDL export, data dictionary, performance analysis, structure diff |
| [api-generator-skill](./api-generator-skill) | API doc generation | Scan code and emit Markdown / HTML / Postman Collection, 6 frameworks supported |
| [markdown-to-html](./markdown-to-html) | Markdown → HTML formatter | 40 themes, fully inline styles, pasteable into WeChat editor or email clients |
| [markdown-to-feishu-skill](./markdown-to-feishu-skill) | Markdown → Feishu/Lark Wiki | Create wiki node, write body, place local images at their original positions — no missing images |
| [article-illustration-tools](./article-illustration-tools) | Auto-illustrate articles | Analyze structure, recommend image slots, call Codex / Antigravity to generate and insert images |
| [image-factory-skill](./image-factory-skill) | AI image → Feishu push | One-line prompt → generate image → push to selected Feishu users/chats in parallel |
| [enterprise-email-manager](./enterprise-email-manager) | Corporate email automation | IMAP/SMTP backup, deletion, organization, bulk send |

---

## 🔹 Skill Details

### 1. enterprise-dev-flow — Enterprise Development Lifecycle

An intelligent dev-assistant toolset for Claude Code covering the full lifecycle: **requirements → technical design → task breakdown → test design → test reporting**.

- 5 core skills + 25+ rule files (security, database, API, code quality, Git, testing, architecture) + 6 reference templates
- Each stage has a built-in quality checklist that validates enterprise conventions before output
- Task breakdown emits two formats simultaneously: project-management checklist (Markdown) and Claude Code Plan
- Target stack: Spring Cloud Alibaba + PostgreSQL + Redis + RocketMQ + MinIO

### 2. database-tools-skills — Database Toolkit

PostgreSQL / MySQL metadata and performance management.

- Inspect structure (schemas, tables, columns, indexes, constraints)
- Generate DDL init scripts (including EXTENSION/TYPE/SEQUENCE/FUNCTION/TRIGGER)
- Export data dictionary (Markdown / HTML, HTML ships a fixed sidebar nav)
- Performance reports (unused indexes, redundant indexes, missing FK indexes, table bloat, etc.)
- Optimization scripts, seed INSERT export, structure diff & migration, JSON snapshots

```bash
/db pg tables -s public
/db pg ddl -s public -o init.sql
/db-dict pg dict -s public -f html -o dict.html
/db-report pg report -s public -o report.md
/db diff --source dev --target prod
```

Dependencies: `psycopg2-binary` (PostgreSQL) or `pymysql` (MySQL), Python ≥ 3.9.

### 3. api-generator-skill — API Documentation Generator

Scans project code and emits standard API docs in Markdown, HTML, and Postman/Apifox Collection.

- Auto-detects controller/router/handler directories, skips test files
- Smart inference for incomplete parameter info, flagged as "(inferred)"
- HTML output ships sidebar navigation, HTTP method badges, request/response tabs
- Nested parameters expanded with dot notation (e.g. `data.userInfo.userId`)
- Frameworks: Spring Boot, Express.js, FastAPI, Flask, Gin, Koa

```bash
/api-doc ./src/main/java/com/example/controller
/api-doc-html ./src/routes/order.ts
/api-doc-postman ./src --base-url http://api.example.com
```

### 4. markdown-to-html — Markdown Formatter

Turns Markdown into **beautifully formatted HTML pasteable directly into the WeChat editor or email clients**. All styles are inline on `style="..."` — no `<style>` blocks, external stylesheets, or `class` selectors (WeChat and most email clients strip those).

- 40 built-in themes: original premium themes + ported markdown2wechat themes
- Subject themes (e.g. "Native Blueprint", "Cyan Grid Notes") match by genre; style themes match by vibe
- Code blocks rendered with `&nbsp;`/`<br>` (avoids WeChat's whitespace collapse)
- Built-in validator checks for patterns that would lose styling

```
Format ~/notes/reading-notes.md for a WeChat article
Convert this Markdown to HTML using the "Cyan Grid Notes" theme
Re-format this md with a different theme
```

### 5. markdown-to-feishu-skill — Markdown to Feishu/Lark Wiki

Imports local Markdown (with images) into a Feishu/Lark wiki. Solves the **image integrity** problem — Feishu's native Markdown import only fetches network URLs, so local-path images get dropped.

- Creates a new wiki node, or writes into an existing docx document
- Marker placeholder + `media-insert --before` strategy keeps every local image at its original position
- Feishu config read from the skill's `.env` (`space_id` / `parent_node_token` / identity, etc.)
- Dependencies: `lark-cli`, Python ≥ 3.9

```
Upload this Markdown to the Feishu wiki and keep the images
Archive this article (with images) into the knowledge base
```

### 6. article-illustration-tools — Auto-Illustrate Articles

An AI tool that auto-illustrates Markdown articles.

- Analyzes structure, recommends image positions, generates detailed prompts
- Three-axis style system: Type × Style × Palette (21 presets, 552 combinations)
- Dual backends: Codex CLI and Antigravity CLI (agy), auto-detected
- Concurrent generation with timeout/retry/validation, auto-inserts into Markdown

Triggers: "illustrate article", "add images to article", "generate article images"

### 7. image-factory-skill — AI Image → Feishu Push

One-line description → generate image → push to a Feishu user or chat. Image, caption, and the generating prompt are combined into a **single** rich-text message; with multiple targets the image is uploaded once and sent concurrently.

- Backends: codex-cli or agy (Antigravity CLI)
- Recipients configured in `.env` via `FEISHU_USER_IDS` / `FEISHU_CHAT_IDS`
- Dependency: `lark-cli`

```
Generate a tech-style system architecture diagram and send it to Zhang San
Send the R&D group a hand-drawn product roadmap with caption "Q2 sketch"
```

### 8. enterprise-email-manager — Corporate Email Manager

IMAP/SMTP-based email automation toolkit.

- Backup, delete, organize, and bulk-send email
- Generic HTML template auto-fills signature and company info
- Python stdlib only — no third-party dependencies (Python ≥ 3.6)
- Credentials configured via `.env`, which is git-ignored

---

## 🚀 Installation

```bash
git clone https://github.com/JianJang2017/jianjang-skills.git
cd jianjang-skills

# Copy the skills you need to the Claude Code skills directory
cp -r enterprise-dev-flow ~/.claude/skills/
cp -r database-tools-skills ~/.claude/skills/
cp -r api-generator-skill ~/.claude/skills/
cp -r markdown-to-html ~/.claude/skills/
cp -r markdown-to-feishu-skill ~/.claude/skills/
cp -r article-illustration-tools ~/.claude/skills/
cp -r image-factory-skill ~/.claude/skills/
cp -r enterprise-email-manager ~/.claude/skills/
```

### Optional Dependencies

```bash
# Database
pip install psycopg2-binary    # PostgreSQL
pip install pymysql            # MySQL

# Feishu/Lark (for markdown-to-feishu-skill, image-factory-skill)
npx @larksuite/cli@latest install
lark-cli auth login

# AI image backends (for article-illustration-tools, image-factory-skill — pick one)
npm install -g codex-cli
# Or install agy (Antigravity CLI)
```

Each skill ships a `.env.example` — copy it to `.env` and fill in the values. `.env` is already in `.gitignore`.

---

## 🗂️ Pick a Skill by Scenario

| Scenario | Recommended Skill |
|---|---|
| Write a PRD / design / break down tasks / produce tests | enterprise-dev-flow |
| Inspect a database, generate a data dictionary, debug slow SQL | database-tools-skills |
| Generate API docs at delivery time | api-generator-skill |
| Format a Markdown article for WeChat or email | markdown-to-html |
| Archive a Markdown article into Feishu wiki | markdown-to-feishu-skill |
| Auto-illustrate a long-form article | article-illustration-tools |
| Generate a quick image and ship it to Feishu | image-factory-skill |
| Bulk email backup / send | enterprise-email-manager |

---

## 🤝 Contributing

Issues and Pull Requests are welcome.

## 📄 License

MIT License
