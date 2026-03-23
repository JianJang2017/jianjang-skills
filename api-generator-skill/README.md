# api-generator-skill

从项目代码自动生成标准 API 文档的 Claude Code 技能包。支持扫描项目目录或单个文件，输出 Markdown、HTML、Postman/Apifox Collection 三种格式。

**[English](./README_EN.md)**

---

## 功能特性

- **多框架支持**：Spring Boot、Express.js、FastAPI、Flask、Gin（Go）、Koa
- **三种输出格式**：
  - Markdown（标准格式，含完整请求/响应参数表格）
  - HTML（带左侧分级导航菜单、HTTP 方法色块、请求/响应 Tab 切换）
  - Postman / Apifox Collection JSON（v2.1 规范，可直接导入）
- **智能推断**：参数信息不完整时根据上下文合理推断，并标注「（推断）」
- **目录扫描**：自动识别 controller、router、handler 等目录，跳过测试文件

## 安装

将 `api-generator-skill` 目录复制到 `~/.claude/skills/` 下即可。

## 使用方式

### 自然语言触发

直接在对话中描述需求，技能会自动触发：

```
帮我扫描 ./src/controller 目录，生成 API 文档
分析 UserController.java，生成接口文档
扫描项目接口，导出 Postman collection
生成 HTML 格式的 API 文档
```

### Slash Command

| 命令 | 说明 |
|------|------|
| `/api-doc <路径>` | 生成 Markdown 格式文档 |
| `/api-doc-html <路径>` | 生成 HTML 格式文档（自动在浏览器打开） |
| `/api-doc-postman <路径>` | 生成 Postman/Apifox Collection JSON |

**示例：**

```bash
/api-doc ./src/main/java/com/example/controller
/api-doc-html ./src/routes/order.ts
/api-doc-postman ./src --base-url http://api.example.com
/api-doc UserController.java --output ./docs/user-api.md
```

## 输出格式说明

### Markdown 格式

标准 Markdown 格式，包含：

- 接口说明（地址、方法、参数格式、描述）
- 请求参数表格（参数名、说明、类型、是否必填、取值范围、示例值）
- 请求参数样例（JSON 或 URL 格式）
- 响应参数表格（含嵌套字段点号展开）
- 成功/失败响应样例

### HTML 格式

单文件，无外部依赖，包含：

- 左侧固定导航，按模块分级折叠
- 右侧接口卡片，点击展开详情
- HTTP 方法色块（GET 蓝、POST 绿、PUT 橙、DELETE 红）
- 请求示例 / 成功响应 / 失败响应 Tab 切换

### Postman / Apifox Collection

- 遵循 Postman Collection v2.1 规范
- 按模块分组，包含完整请求体和 query 参数
- 支持变量（`{{base_url}}`、`{{token}}`）
- Apifox 导入：项目设置 → 导入数据 → 选择「Postman」格式

## 支持的框架

| 框架 | 语言 | 识别特征 |
|------|------|---------|
| Spring Boot | Java | `@RestController`, `@GetMapping`, `@PostMapping` |
| Express.js | TypeScript/JavaScript | `router.get()`, `router.post()`, `app.get()` |
| FastAPI | Python | `@app.get()`, `@app.post()`, `@router.get()` |
| Flask | Python | `@app.route()`, `@blueprint.route()` |
| Gin | Go | `r.GET()`, `r.POST()`, `group.GET()` |
| Koa | TypeScript/JavaScript | `router.get()`, `router.post()` |
