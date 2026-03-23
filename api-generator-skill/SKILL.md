---
name: api-generator-skill
description: 从项目代码自动生成标准 API 文档。支持 Spring Boot、Express.js、FastAPI、Flask、Gin 等主流框架。可输出 Markdown、HTML（带分级菜单）、Postman/Apifox Collection JSON 三种格式。触发关键词：生成 API 文档、扫描接口、生成接口文档、api doc、接口文档生成、generate api docs、导出 Postman、导出 Apifox、导出 HTML。即使用户只说"帮我生成文档"或"扫描一下接口"，只要涉及代码文件或目录，也应触发此技能。也可通过 slash command 调用：/api-doc、/api-doc-html、/api-doc-postman。
---

# API 文档生成器

从项目代码提取 API 接口，支持三种输出格式：Markdown、HTML、Postman/Apifox Collection。

## 工作流程

### 第一步：理解输入

用户会提供以下之一：
- **项目目录路径**：扫描整个目录下的所有代码文件
- **单个文件路径**：只分析该文件中的接口

如果用户没有明确提供路径，用 AskUserQuestion 询问。

### 第二步：识别框架和扫描接口

读取代码文件，识别框架，提取所有 API 接口信息。

**支持的框架：**

| 框架 | 识别特征 |
|------|---------|
| Spring Boot | `@RestController`, `@GetMapping`, `@PostMapping`, `@RequestMapping` |
| Express.js | `router.get()`, `router.post()`, `app.get()` |
| FastAPI | `@app.get()`, `@app.post()`, `@router.get()` |
| Flask | `@app.route()`, `@blueprint.route()` |
| Gin (Go) | `r.GET()`, `r.POST()`, `group.GET()` |
| Koa | `router.get()`, `router.post()` |

**目录扫描规则：**
- 优先扫描 controller、router、routes、api、handler 等目录
- 文件类型：`.java`, `.ts`, `.js`, `.py`, `.go`, `.kt`
- 跳过测试文件（`*Test.java`, `*.test.ts`, `*_test.go` 等）

### 第三步：提取接口信息

对每个接口提取：接口路径（含前缀）、请求方式、参数格式、接口描述（从注释/Swagger注解/函数名推断）、请求参数、响应结构。

信息不完整时合理推断，并标注"（推断）"。

### 第四步：按格式生成文档

根据用户指定格式（或默认 Markdown）生成，详见下方"输出格式"。

## 输出格式

**Markdown（默认）：**
- ≤ 5 个接口：直接输出到对话
- > 5 个接口：保存为 `api_doc.md`
- 格式规范见 `references/format-template.md`

**HTML（用户说"导出 HTML"或 `--html`）：**
- 保存为 `api_doc.html`，带左侧分级菜单、HTTP 方法色块、请求/响应 tab
- 模板见 `references/html-template.md`
- 生成后根据操作系统打开：macOS 用 `open`，Linux 用 `xdg-open`，Windows 用 `start`

**Postman / Apifox（用户说"导出 Postman"、"导出 Apifox"、"生成 collection"）：**
- 保存为 `api_collection.json`，遵循 Postman Collection v2.1 规范
- 格式规范见 `references/postman-format.md`

生成完成后告知接口数量和文件路径。

## 关键原则

**完整性优先**：宁可多写推断内容，也不要留空。无法确定的字段用合理默认值填充并标注"（推断）"。

**嵌套参数展开**：响应参数嵌套对象用点号展开，如 `data.token`、`data.userInfo.userId`；数组用 `data.list[].orderId`。

**示例值要真实**：不用 `xxx` 或 `string`，用真实可能的值如 `10001`、`jack123`、`eyJhbGci...`。

**GET 接口**：无请求体，请求参数样例改为 URL 格式，如 `/api/user/info?userId=10001`。

**标题层级（Markdown）**：

文档直接从模块标题或接口标题开始，不要在开头加 `# 文档标题`、`> 扫描目录`、`> 生成时间`、目录列表等任何额外内容。

```
### X.X 模块名称          ← 多文件/目录时，模块用三级标题 ###
#### X.X.X 接口名称       ← 接口用四级标题 ####
##### X.X.X.1 接口说明
##### X.X.X.2 请求参数
##### X.X.X.3 请求参数样例
##### X.X.X.4 响应参数
##### X.X.X.5 响应样例
###### X.X.X.5.1 成功响应
###### X.X.X.5.2 失败响应
```

单文件时没有模块层，直接从 `#### X.X 接口名称` 开始。

常见错误（不要这样做）：
- ❌ `## 用户模块` → 应为 `### 1.1 用户模块`
- ❌ `### 用户登录` → 应为 `#### 1.1.1 用户登录`
- ❌ 文档开头加 `# API 接口文档` 或 `> 扫描目录：xxx`
