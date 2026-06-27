# JianJang Skills

Claude Code 技能集合，覆盖企业开发全流程、数据库运维、API 文档、文章排版与配图、邮件管理、飞书协同等场景。

**[English](./README_EN.md)**

---

## 📦 技能一览

| 技能 | 用途 | 关键能力 |
|---|---|---|
| [enterprise-dev-flow](./enterprise-dev-flow) | 企业级开发全流程 | PRD → 设计 → 任务拆分 → 测试用例 → 测试报告，Spring Cloud Alibaba 技术栈适配 |
| [database-tools-skills](./database-tools-skills) | 数据库运维 | PostgreSQL/MySQL 结构查询、DDL 导出、数据字典、性能分析、结构对比 |
| [api-generator-skill](./api-generator-skill) | API 文档生成 | 扫描代码生成 Markdown / HTML / Postman Collection，支持 6 种框架 |
| [markdown-to-html](./markdown-to-html) | Markdown 排版为 HTML | 40 套主题，全内联样式，可直接贴公众号编辑器/邮件客户端 |
| [markdown-to-feishu-skill](./markdown-to-feishu-skill) | Markdown 写入飞书知识库 | 自动建 Wiki 节点、写正文、按原文位置插入本地图片，保证图片完整性 |
| [article-illustration-tools](./article-illustration-tools) | 文章自动配图 | 分析文章结构、推荐图片位置、调用 Codex / Antigravity 生图并插入 |
| [image-factory-skill](./image-factory-skill) | AI 生图 + 飞书推送 | 一句描述生成图片，并发推送给指定飞书用户/群组 |
| [enterprise-email-manager](./enterprise-email-manager) | 企业邮件管理 | IMAP/SMTP 协议的邮件备份、删除、整理、批量发送 |

---

## 🔹 技能详情

### 1. enterprise-dev-flow — 企业级开发全流程

为 Claude Code 设计的智能开发助手工具集，覆盖**需求分析 → 技术设计 → 任务拆分 → 测试设计 → 测试报告**全生命周期。

- 5 个核心技能 + 25+ 规则文件（安全/数据库/API/代码质量/Git/测试/架构）+ 6 个参考模板
- 每个环节内置质量检查清单，自动验证企业级规范
- 任务拆分双格式输出：项目管理清单（Markdown）+ Claude Code Plan
- 技术栈：Spring Cloud Alibaba + PostgreSQL + Redis + RocketMQ + MinIO

### 2. database-tools-skills — 数据库工具集

PostgreSQL / MySQL 数据库元数据与性能管理工具。

- 查看结构（schema、表、字段、索引、约束）
- 生成 DDL 初始化脚本（含 EXTENSION/TYPE/SEQUENCE/FUNCTION/TRIGGER）
- 导出数据字典（Markdown / HTML，HTML 带左侧固定导航）
- 性能分析（未使用索引、冗余索引、缺失外键索引、表膨胀等）
- 生成优化脚本、导出 Seed INSERT、结构对比与迁移、结构快照（JSON）

```bash
/db pg tables -s public
/db pg ddl -s public -o init.sql
/db-dict pg dict -s public -f html -o dict.html
/db-report pg report -s public -o report.md
/db diff --source dev --target prod
```

依赖：`psycopg2-binary`（PostgreSQL）或 `pymysql`（MySQL），Python ≥ 3.9。

### 3. api-generator-skill — API 文档生成器

从项目代码自动生成标准 API 文档，输出 Markdown、HTML、Postman/Apifox Collection 三种格式。

- 自动识别 controller/router/handler 目录，跳过测试文件
- 智能推断不完整参数，标注「（推断）」
- HTML 带左侧分级导航、HTTP 方法色块、请求/响应 Tab 切换
- 嵌套参数点号展开（如 `data.userInfo.userId`）
- 支持框架：Spring Boot、Express.js、FastAPI、Flask、Gin、Koa

```bash
/api-doc ./src/main/java/com/example/controller
/api-doc-html ./src/routes/order.ts
/api-doc-postman ./src --base-url http://api.example.com
```

### 4. markdown-to-html — Markdown 排版为 HTML

把 Markdown 转换成**排版精美、可直接粘贴到微信公众号编辑器或邮件客户端**的 HTML。所有样式全部内联在 `style="..."` 里，不依赖 `<style>` 块、外部样式表或 `class` 选择器。

- 内置 **40 套主题**：原创精品主题 + markdown2wechat 移植主题
- 题材型主题（如「原生蓝图」「青格笔记」）按文体匹配；风格型主题按气质匹配
- 代码块用 `&nbsp;`/`<br>` 渲染（避免公众号折叠空白）
- 自带校验脚本，交付前检查会"掉样式"的写法

```
把 ~/notes/读书笔记.md 排版成公众号文章
这段 markdown 帮我转成好看的 HTML，用「青格笔记」主题
换个主题风格重新排一下这篇 md
```

### 5. markdown-to-feishu-skill — Markdown 写入飞书知识库

把本地 Markdown（含本地图片）完整写入飞书/Lark 知识库。核心解决**图片完整性**问题——飞书原生 Markdown 导入只会下载网络 URL 图片，本地路径图片会被丢弃。

- 自动新建 Wiki 节点 / 写入已有 docx 文档
- marker 占位 + `media-insert --before` 定位，保证每张本地图片都落在原文位置
- 飞书配置从 skill 根目录 `.env` 读取（`space_id` / `parent_node_token` / 身份等）
- 依赖：`lark-cli`，Python ≥ 3.9

```
把这篇 markdown 上传到飞书 wiki 并保留图片
把带图片的文章整理进知识库
```

### 6. article-illustration-tools — 文章自动配图

为 Markdown 文章自动配图的 AI 工具。

- 智能分析文章结构、推荐图片位置、生成详细提示词
- 三维风格系统：Type × Style × Palette（21 个预设，552 种组合）
- 双后端：Codex CLI 和 Antigravity CLI（agy），自动检测
- 批量并发生成，带超时/重试/验证，自动插入 Markdown

触发：「为文章配图」「给文章生成图片」「illustrate article」

### 7. image-factory-skill — AI 生图 + 飞书推送

输入一句图片描述 → 自动生成图片 → 推送到飞书的人或群。图片、配文与生成 prompt 合成**一条**富文本消息；多目标时图片只上传一次、并发发送。

- 后端：codex-cli 或 agy（Antigravity CLI）
- 接收人通过 `.env` 配置 `FEISHU_USER_IDS` / `FEISHU_CHAT_IDS`
- 依赖：`lark-cli`

```
生成一张科技感的系统架构图，发给张三
给研发群发一张手绘风格的产品路线图，配文：Q2 规划草图
```

### 8. enterprise-email-manager — 企业邮件管理器

IMAP/SMTP 协议的邮件自动化管理工具。

- 邮件备份、删除、整理、批量发送
- 通用 HTML 模板，自动读取签名/公司信息
- 仅使用 Python 标准库，无第三方依赖（Python ≥ 3.6）
- 凭证通过 `.env` 配置，已在 `.gitignore` 中

---

## 🚀 安装

```bash
git clone https://github.com/JianJang2017/jianjang-skills.git
cd jianjang-skills

# 复制需要的技能到 Claude Code 技能目录
cp -r enterprise-dev-flow ~/.claude/skills/
cp -r database-tools-skills ~/.claude/skills/
cp -r api-generator-skill ~/.claude/skills/
cp -r markdown-to-html ~/.claude/skills/
cp -r markdown-to-feishu-skill ~/.claude/skills/
cp -r article-illustration-tools ~/.claude/skills/
cp -r image-factory-skill ~/.claude/skills/
cp -r enterprise-email-manager ~/.claude/skills/
```

### 可选依赖

```bash
# 数据库
pip install psycopg2-binary    # PostgreSQL
pip install pymysql            # MySQL

# 飞书相关（markdown-to-feishu-skill、image-factory-skill）
npx @larksuite/cli@latest install
lark-cli auth login

# AI 生图后端（article-illustration-tools、image-factory-skill，二选一）
npm install -g codex-cli
# 或安装 agy（Antigravity CLI）
```

各技能的 `.env.example` 已提供，复制为 `.env` 后填写即可；`.env` 默认在 `.gitignore` 中。

---

## 🗂️ 按场景选技能

| 场景 | 推荐技能 |
|---|---|
| 写需求 / 出设计 / 拆任务 / 出测试 | enterprise-dev-flow |
| 看库结构、出数据字典、排查慢 SQL | database-tools-skills |
| 项目交付时一键出 API 文档 | api-generator-skill |
| Markdown 文章发公众号 / 邮件 | markdown-to-html |
| Markdown 归档到飞书知识库 | markdown-to-feishu-skill |
| 给长文自动配插图 | article-illustration-tools |
| 临时一张图发飞书 | image-factory-skill |
| 邮件批量备份 / 群发 | enterprise-email-manager |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

## 📄 许可证

MIT License
