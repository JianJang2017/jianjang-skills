# Postman Collection v2.1 格式说明

生成的 JSON 文件遵循 Postman Collection v2.1 规范，可直接导入 Postman 和 Apifox。

## 完整结构模板

```json
{
  "info": {
    "name": "{{项目名称}} API",
    "_postman_id": "{{随机UUID}}",
    "description": "由 api-doc-generator 自动生成",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "用户模块",
      "item": [
        {
          "name": "用户登录",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"account\": \"jack123\",\n  \"password\": \"Jack@123456\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/api/user/login",
              "host": ["{{base_url}}"],
              "path": ["api", "user", "login"]
            },
            "description": "用户通过账号密码登录，返回 token"
          },
          "response": []
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8080",
      "type": "string"
    }
  ]
}
```

## 关键规则

### 整体结构
- `info.name`：取项目名或目录名
- `info._postman_id`：生成一个随机 UUID（格式：`xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`）
- `item`：顶层为模块分组（folder），每个模块下是接口列表

### 模块分组（folder）
```json
{
  "name": "模块名称",
  "item": [ ...接口列表... ]
}
```
单文件时不需要分组，`item` 直接放接口。

### 接口（request item）
```json
{
  "name": "接口名称",
  "request": {
    "method": "POST",
    "header": [...],
    "body": {...},
    "url": {...},
    "description": "接口描述"
  },
  "response": []
}
```

### URL 构造
将路径按 `/` 分割填入 `path` 数组，去掉空字符串：
- `/api/user/login` → `["api", "user", "login"]`
- `/api/order/{orderId}` → `["api", "order", ":orderId"]`（path variable 用 `:` 前缀）

`raw` 字段拼接完整 URL：`{{base_url}}/api/user/login`

### Header 处理
- JSON 请求体：添加 `Content-Type: application/json`
- 需要认证的接口：添加 `Authorization: Bearer {{token}}`（value 用变量）
- form-data：`Content-Type: multipart/form-data`（Postman 会自动处理，可省略）

### Body 处理

**JSON 请求体（POST/PUT/PATCH）：**
```json
{
  "mode": "raw",
  "raw": "{\n  \"key\": \"value\"\n}",
  "options": { "raw": { "language": "json" } }
}
```
`raw` 字段用真实示例值填充，格式化缩进。

**Query 参数（GET）：**
```json
{
  "url": {
    "raw": "{{base_url}}/api/user/info?userId=10001",
    "host": ["{{base_url}}"],
    "path": ["api", "user", "info"],
    "query": [
      { "key": "userId", "value": "10001", "description": "用户ID" }
    ]
  }
}
```
可选参数加 `"disabled": true`。

**Header 参数（如 Authorization）：**
```json
{
  "header": [
    { "key": "Authorization", "value": "Bearer {{token}}", "description": "登录令牌" }
  ]
}
```

**无请求体（GET/DELETE）：** `body` 字段省略或设为 `null`。

### 变量
在顶层 `variable` 数组中声明所有用到的变量：
```json
"variable": [
  { "key": "base_url", "value": "http://localhost:8080", "type": "string" },
  { "key": "token", "value": "", "type": "string" }
]
```

## Apifox 导入说明

Apifox 完全兼容 Postman Collection v2.1 格式。导入步骤：
1. 打开 Apifox → 项目设置 → 导入数据
2. 选择「Postman」格式
3. 上传生成的 `api_collection.json`
4. 确认导入即可
