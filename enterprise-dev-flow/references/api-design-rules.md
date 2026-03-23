# API 接口设计规范

> 基于 RESTful 风格的企业级接口设计规范
> 适用于 Spring Cloud Alibaba 技术栈

---

## 1. 接口设计原则

### 1.1 RESTful 风格

- 使用 HTTP 方法表达操作语义：GET（查询）、POST（创建）、PUT（全量更新）、PATCH（部分更新）、DELETE（删除）
- URL 表示资源，不包含动词
- 使用复数名词表示资源集合

### 1.2 统一响应格式

所有接口必须使用统一的响应封装格式 `Result<T>`：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": { ... },
  "traceId": "a1b2c3d4e5f6"
}
```

---

## 2. 接口文档结构

每个接口文档必须包含以下完整章节：

### 2.1 接口说明

| 项目 | 说明 | 示例 |
|------|------|------|
| **接口地址** | URL 路径（含版本号） | `/api/v1/user/login` |
| **请求方式** | HTTP Method | POST |
| **参数格式** | Content-Type | JSON（application/json） |
| **接口描述** | 功能说明（1-2句话） | 用户通过用户名/手机号+密码登录，返回登录态token及用户信息 |
| **是否需要认证** | 是否需要 Token | 是/否 |
| **幂等性** | 是否幂等及实现方式 | 是（通过请求ID去重） |

### 2.2 请求参数

使用表格格式定义所有请求参数：

| 参数名称 | 参数说明 | 参数类型 | 是否必填 | 取值范围 | 示例值 |
|---------|---------|---------|---------|---------|--------|
| account | 登录账号（用户名/手机号） | string | 是 | - | jack123/13800138000 |
| password | 登录密码 | string | 是 | 6-16位 | Jack@123456 |
| remember | 是否记住登录（7天有效） | boolean | 否 | true/false | true |

**参数约束说明：**
- 必填参数不能为空
- 字符串类型需说明长度限制
- 数值类型需说明取值范围
- 枚举类型需列出所有可选值
- 复杂对象需展开说明子字段

### 2.3 请求参数样例

提供完整的 JSON 请求示例：

```json
{
  "account": "jack123",
  "password": "Jack@123456",
  "remember": true
}
```

### 2.4 响应参数

使用表格格式定义所有响应字段（包括嵌套字段）：

| 参数名称 | 参数说明 | 参数类型 | 是否必返 | 示例值 |
|---------|---------|---------|---------|--------|
| code | 响应码 | int | 是 | 200 |
| msg | 响应信息 | string | 是 | 登录成功 |
| data | 响应数据 | object | 是 | - |
| data.token | 登录令牌 | string | 是 | eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... |
| data.userInfo | 用户信息 | object | 是 | - |
| data.userInfo.userId | 用户ID | long | 是 | 10001 |
| data.userInfo.nickname | 昵称 | string | 是 | 杰克 |

**嵌套对象说明：**
- 使用 `.` 表示层级关系（如 `data.userInfo.userId`）
- 数组类型需说明元素类型（如 `list<UserInfo>`）
- 可选字段需明确标注"否"

### 2.5 响应样例

#### 成功响应

```json
{
  "code": 200,
  "msg": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEwMDAxLCJ1c2VybmFtZSI6ImphY2sxMjMiLCJleHAiOjE3MTI1Nzc2MDAsImlhdCI6MTcxMjAwOTYwMH0.8Z9Z8f8k7s7d6s5a4s3d2f1g7h8j9k0l",
    "userInfo": {
      "userId": 10001,
      "nickname": "杰克"
    }
  },
  "traceId": "a1b2c3d4e5f6"
}
```

#### 失败响应（业务异常）

```json
{
  "code": 401,
  "msg": "密码错误",
  "data": null,
  "traceId": "a1b2c3d4e5f6"
}
```

#### 失败响应（系统异常）

```json
{
  "code": 500,
  "msg": "系统繁忙，请稍后重试",
  "data": null,
  "traceId": "a1b2c3d4e5f6"
}
```

---

## 3. URL 设计规范

### 3.1 URL 结构

```
/{api-prefix}/{version}/{resource}/{action}
```

| 段 | 说明 | 示例 |
|----|------|------|
| api-prefix | API 前缀（固定） | api |
| version | 版本号 | v1、v2 |
| resource | 资源名称（复数） | users、orders、products |
| action | 操作（可选，仅非标准 CRUD） | login、logout、export |

### 3.2 URL 示例

| 操作 | HTTP Method | URL | 说明 |
|------|------------|-----|------|
| 查询列表 | GET | `/api/v1/users` | 查询用户列表 |
| 查询详情 | GET | `/api/v1/users/{id}` | 查询指定用户 |
| 创建 | POST | `/api/v1/users` | 创建用户 |
| 更新 | PUT | `/api/v1/users/{id}` | 全量更新用户 |
| 部分更新 | PATCH | `/api/v1/users/{id}` | 部分更新用户 |
| 删除 | DELETE | `/api/v1/users/{id}` | 删除用户 |
| 非标准操作 | POST | `/api/v1/users/login` | 用户登录 |

### 3.3 URL 命名规范

- 使用小写字母
- 多个单词使用连字符（-）分隔，不使用下划线（_）
- 资源名称使用复数形式
- 避免使用动词，用 HTTP Method 表达操作

**正确示例：**
- `/api/v1/user-profiles`
- `/api/v1/order-items`

**错误示例：**
- `/api/v1/getUserProfile`（包含动词）
- `/api/v1/user_profiles`（使用下划线）
- `/api/v1/user`（单数形式）

---

## 4. 响应码规范

### 4.1 HTTP 状态码

| 状态码 | 说明 | 使用场景 |
|-------|------|---------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 204 | No Content | 删除成功（无返回内容） |
| 400 | Bad Request | 参数校验失败 |
| 401 | Unauthorized | 未认证（未登录） |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 系统内部错误 |
| 503 | Service Unavailable | 服务不可用（降级/熔断） |

### 4.2 业务状态码（code 字段）

| 状态码 | 说明 | 示例场景 |
|-------|------|---------|
| 200 | 成功 | 操作成功 |
| 400-499 | 客户端错误 | 参数错误、业务规则校验失败 |
| 500-599 | 服务端错误 | 系统异常、第三方服务异常 |

**业务状态码命名规范：**
- 使用业务前缀 + 具体错误码
- 示例：`ORDER_001`（库存不足）、`USER_002`（用户不存在）

### 4.3 错误信息规范

| 错误类型 | msg 内容 | 是否暴露详情 |
|---------|---------|------------|
| 参数校验错误 | 明确提示哪个参数错误 | 是 |
| 业务规则错误 | 明确提示业务原因 | 是 |
| 系统内部错误 | 通用提示"系统繁忙，请稍后重试" | 否（不暴露堆栈） |
| 第三方服务错误 | 通用提示"服务暂时不可用" | 否 |

---

## 5. 参数校验规范

### 5.1 请求参数校验

所有请求参数必须在 Controller 层使用 `@Valid` 或 `@Validated` 进行校验：

```java
@PostMapping("/login")
public Result<LoginResp> login(@Valid @RequestBody LoginReq req) {
    // ...
}
```

### 5.2 常用校验注解

| 注解 | 说明 | 示例 |
|------|------|------|
| `@NotNull` | 不能为 null | `@NotNull(message = "用户ID不能为空")` |
| `@NotBlank` | 不能为空字符串 | `@NotBlank(message = "用户名不能为空")` |
| `@Size` | 字符串长度限制 | `@Size(min = 6, max = 16, message = "密码长度6-16位")` |
| `@Min` / `@Max` | 数值范围 | `@Min(value = 1, message = "数量至少为1")` |
| `@Pattern` | 正则表达式 | `@Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式错误")` |
| `@Email` | 邮箱格式 | `@Email(message = "邮箱格式错误")` |

### 5.3 自定义校验

对于复杂的业务规则校验，在 Service 层进行：

```java
if (user.getBalance() < order.getAmount()) {
    throw new BizException(ErrorCode.INSUFFICIENT_BALANCE, "余额不足");
}
```

---

## 6. 分页查询规范

### 6.1 分页请求参数

| 参数名称 | 参数说明 | 参数类型 | 是否必填 | 默认值 | 取值范围 |
|---------|---------|---------|---------|-------|---------|
| pageNum | 页码 | int | 否 | 1 | >= 1 |
| pageSize | 每页数量 | int | 否 | 10 | 1-100 |

### 6.2 分页响应格式

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "total": 100,
    "pageNum": 1,
    "pageSize": 10,
    "pages": 10,
    "list": [
      { "userId": 1, "nickname": "用户1" },
      { "userId": 2, "nickname": "用户2" }
    ]
  }
}
```

### 6.3 分页性能约束

- 单页最大数量不超过 100 条
- 禁止深分页（pageNum > 1000），改用游标分页
- 大数据量查询必须建立索引

---

## 7. 接口安全规范

### 7.1 认证与授权

- 需要认证的接口必须在请求头携带 Token：`Authorization: Bearer {token}`
- Token 过期时返回 401，前端跳转登录页
- 权限不足时返回 403，提示"无权限访问"

### 7.2 敏感信息保护

- 密码、密钥等敏感信息禁止明文传输（使用 HTTPS）
- 响应中禁止返回完整手机号、身份证号（需脱敏）
- 日志中禁止打印敏感信息

### 7.3 防重放攻击

- 关键操作接口（支付、转账）需要实现防重放机制
- 使用请求签名 + 时间戳 + nonce 防止重放

---

## 8. 接口文档示例模板

```markdown
#### X.X.X 接口名称

##### X.X.X.1 接口说明

- 接口地址：/api/v1/xxx
- 请求方式：POST
- 参数格式：JSON（application/json）
- 接口描述：[功能说明]
- 是否需要认证：是
- 幂等性：是（通过请求ID去重）

##### X.X.X.2 请求参数

| 参数名称 | 参数说明 | 参数类型 | 是否必填 | 取值范围 | 示例值 |
|---------|---------|---------|---------|---------|--------|
| [字段名] | [说明] | [类型] | [是/否] | [范围] | [示例] |

##### X.X.X.3 请求参数样例

```json
{
  "field1": "value1",
  "field2": "value2"
}
```

##### X.X.X.4 响应参数

| 参数名称 | 参数说明 | 参数类型 | 是否必返 | 示例值 |
|---------|---------|---------|---------|--------|
| code | 响应码 | int | 是 | 200 |
| msg | 响应信息 | string | 是 | 操作成功 |
| data | 响应数据 | object | 是 | - |

##### X.X.X.5 响应样例

###### X.X.X.5.1 成功响应

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": { ... }
}
```

###### X.X.X.5.2 失败响应

```json
{
  "code": 400,
  "msg": "参数错误",
  "data": null
}
```
```

---

## 9. 接口设计检查清单

设计完成后，必须逐项检查：

- [ ] URL 符合 RESTful 规范（资源名称、HTTP Method）
- [ ] 请求参数表格完整（参数名称、说明、类型、必填、范围、示例）
- [ ] 响应参数表格完整（包括嵌套字段）
- [ ] 提供了请求和响应的 JSON 样例
- [ ] 定义了成功和失败的响应样例
- [ ] 参数校验规则明确（长度、范围、格式）
- [ ] 敏感信息已脱敏处理
- [ ] 错误码和错误信息已定义
- [ ] 幂等性设计已说明（写操作必须）
- [ ] 分页接口符合分页规范
- [ ] 接口文档包含 traceId 字段
