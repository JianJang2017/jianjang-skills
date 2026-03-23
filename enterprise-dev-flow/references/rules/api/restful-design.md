# RESTful 设计规范

> 适用范围：所有 HTTP API 接口设计，适用于产品经理定义接口需求、研发人员设计接口

---

## 1. 规则说明

RESTful 是一种基于 HTTP 协议的 API 设计风格，通过统一的接口规范提高系统的可维护性和可扩展性。本规范定义了企业级应用中 RESTful API 的设计原则和最佳实践。

## 2. 规则内容

### 2.1 核心原则

- **资源导向**：URL 表示资源，不包含动词
- **HTTP 方法语义化**：使用标准 HTTP 方法表达操作意图
- **无状态**：每个请求包含完整的处理信息，服务端不保存客户端状态
- **统一接口**：所有资源使用统一的操作方式

### 2.2 HTTP 方法语义

| HTTP 方法 | 语义 | 幂等性 | 使用场景 |
|----------|------|-------|---------|
| GET | 查询资源 | 是 | 查询列表、查询详情 |
| POST | 创建资源 | 否 | 创建新资源、非标准操作 |
| PUT | 全量更新资源 | 是 | 替换整个资源 |
| PATCH | 部分更新资源 | 否 | 更新资源的部分字段 |
| DELETE | 删除资源 | 是 | 删除资源 |

### 2.3 资源命名规范

- 使用**复数名词**表示资源集合
- 使用**小写字母**
- 多个单词使用**连字符（-）**分隔，不使用下划线（_）
- 避免使用动词，用 HTTP Method 表达操作

### 2.4 URL 层级关系

- 使用 URL 层级表示资源之间的关系
- 层级不宜过深，建议不超过 3 层
- 使用路径参数表示资源 ID

## 3. 示例

### 正确示例

```
# 查询用户列表
GET /api/v1/users

# 查询指定用户
GET /api/v1/users/{id}

# 创建用户
POST /api/v1/users

# 全量更新用户
PUT /api/v1/users/{id}

# 部分更新用户
PATCH /api/v1/users/{id}

# 删除用户
DELETE /api/v1/users/{id}

# 查询用户的订单列表
GET /api/v1/users/{userId}/orders

# 非标准操作（登录）
POST /api/v1/users/login
```

### 错误示例

```
# ❌ 使用动词
GET /api/v1/getUser
POST /api/v1/createUser

# ❌ 使用单数形式
GET /api/v1/user

# ❌ 使用下划线
GET /api/v1/user_profiles

# ❌ 不使用 HTTP 方法语义
POST /api/v1/users/delete

# ❌ URL 层级过深
GET /api/v1/users/{userId}/orders/{orderId}/items/{itemId}/details
```

## 4. 检查清单

- [ ] URL 使用名词表示资源，不包含动词
- [ ] 资源名称使用复数形式
- [ ] 使用小写字母和连字符分隔
- [ ] HTTP 方法语义正确（GET查询、POST创建、PUT更新、DELETE删除）
- [ ] GET 请求无副作用（幂等）
- [ ] PUT 和 DELETE 请求幂等
- [ ] URL 层级不超过 3 层
- [ ] 路径参数使用大括号表示

---

**版本：** 1.0
**最后更新：** 2026-03-23
