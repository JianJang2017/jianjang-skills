# api-generator-skill

A Claude Code skill that automatically generates standard API documentation from project source code. Supports scanning project directories or single files, with output in Markdown, HTML, and Postman/Apifox Collection formats.

**[中文文档](./README.md)**

---

## Features

- **Multi-framework support**: Spring Boot, Express.js, FastAPI, Flask, Gin (Go), Koa
- **Three output formats**:
  - Markdown (standard format with full request/response parameter tables)
  - HTML (with sidebar navigation, HTTP method badges, request/response tab switching)
  - Postman / Apifox Collection JSON (v2.1 spec, ready to import)
- **Smart inference**: Fills in missing parameter details from context, marked as "(inferred)"
- **Directory scanning**: Auto-detects controller/router/handler directories, skips test files

## Installation

Copy the `api-generator-skill` directory to `~/.claude/skills/`.

## Usage

### Natural Language

Just describe what you need — the skill triggers automatically:

```
Scan ./src/controller and generate API docs
Analyze UserController.java and generate interface documentation
Scan project APIs and export a Postman collection
Generate HTML format API documentation
```

### Slash Commands

| Command | Description |
|---------|-------------|
| `/api-doc <path>` | Generate Markdown documentation |
| `/api-doc-html <path>` | Generate HTML documentation (auto-opens in browser) |
| `/api-doc-postman <path>` | Generate Postman/Apifox Collection JSON |

**Examples:**

```bash
/api-doc ./src/main/java/com/example/controller
/api-doc-html ./src/routes/order.ts
/api-doc-postman ./src --base-url http://api.example.com
/api-doc UserController.java --output ./docs/user-api.md
```

## Output Format Details

### Markdown Format

Standard Markdown format, including:

- Interface info (URL, method, content type, description)
- Request parameter table (name, description, type, required, range, example)
- Request body example (JSON or URL format for GET)
- Response parameter table (nested fields expanded with dot notation)
- Success and failure response examples

### HTML Format

Single self-contained file with no external dependencies:

- Fixed left sidebar with collapsible module groups
- Right-side API cards that expand on click
- HTTP method badges (GET blue, POST green, PUT orange, DELETE red)
- Tab switching between request example / success response / failure response

### Postman / Apifox Collection

- Follows Postman Collection v2.1 spec
- Grouped by module with full request bodies and query params
- Supports variables (`{{base_url}}`, `{{token}}`)
- Apifox import: Project Settings → Import Data → select "Postman" format

## Supported Frameworks

| Framework | Language | Detection |
|-----------|----------|-----------|
| Spring Boot | Java | `@RestController`, `@GetMapping`, `@PostMapping` |
| Express.js | TypeScript/JavaScript | `router.get()`, `router.post()`, `app.get()` |
| FastAPI | Python | `@app.get()`, `@app.post()`, `@router.get()` |
| Flask | Python | `@app.route()`, `@blueprint.route()` |
| Gin | Go | `r.GET()`, `r.POST()`, `group.GET()` |
| Koa | TypeScript/JavaScript | `router.get()`, `router.post()` |
