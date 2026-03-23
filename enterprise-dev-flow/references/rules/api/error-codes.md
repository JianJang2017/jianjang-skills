# 错误码规范

> 适用范围：所有 HTTP API 接口错误处理，适用于产品经理定义错误场景、研发人员实现错误处理

---

## 1. 规则说明

统一的错误码规范能够帮助快速定位问题，提高系统的可维护性。本规范定义了 HTTP 状态码和业务状态码的使用规则，确保错误信息的一致性和可读性。

## 2. 规则内容

### 2.1 HTTP 状态码

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

### 2.2 业务状态码（code 字段）

| 状态码范围 | 说明 | 示例场景 |
|----------|------|---------|
| 200 | 成功 | 操作成功 |
| 400-499 | 客户端错误 | 参数错误、业务规则校验失败 |
| 500-599 | 服务端错误 | 系统异常、第三方服务异常 |

### 2.3 业务状态码命名规范

格式：`{业务前缀}_{错误码}`

| 业务域 | 前缀 | 示例 |
|-------|------|------|
| 用户 | USER | USER_001、USER_002 |
| 订单 | ORDER | ORDER_001、ORDER_002 |
| 支付 | PAYMENT | PAYMENT_001、PAYMENT_002 |
| 库存 | INVENTORY | INVENTORY_001、INVENTORY_002 |

**示例：**
- `USER_001`：用户不存在
- `USER_002`：用户名或密码错误
- `ORDER_001`：库存不足
- `ORDER_002`：余额不足
- `PAYMENT_001`：支付失败
- `PAYMENT_002`：支付超时

### 2.4 错误信息规范

| 错误类型 | msg 内容 | 是否暴露详情 |
|---------|---------|------------|
| 参数校验错误 | 明确提示哪个参数错误 | 是 |
| 业务规则错误 | 明确提示业务原因 | 是 |
| 系统内部错误 | 通用提示"系统繁忙，请稍后重试" | 否（不暴露堆栈） |
| 第三方服务错误 | 通用提示"服务暂时不可用" | 否 |

### 2.5 错误信息原则

1. **对用户友好**：使用用户能理解的语言，避免技术术语
2. **明确具体**：清楚说明错误原因，帮助用户解决问题
3. **不暴露敏感信息**：不暴露系统内部实现细节、堆栈信息
4. **提供解决方案**：在可能的情况下，提示用户如何解决

## 3. 示例

### 正确示例

**参数校验错误：**
```json
{
  "code": 400,
  "msg": "用户名不能为空",
  "data": null,
  "traceId": "a1b2c3d4e5f6"
}
```

**业务规则错误：**
```json
{
  "code": 400,
  "msg": "库存不足，当前库存：5，需要：10",
  "data": null,
  "traceId": "a1b2c3d4e5f6"
}
```

**认证错误：**
```json
{
  "code": 401,
  "msg": "登录已过期，请重新登录",
  "data": null,
  "traceId": "a1b2c3d4e5f6"
}
```

**权限错误：**
```json
{
  "code": 403,
  "msg": "无权限访问该资源",
  "data": null,
  "traceId": "a1b2c3d4e5f6"
}
```

**资源不存在：**
```json
{
  "code": 404,
  "msg": "用户不存在",
  "data": null,
  "traceId": "a1b2c3d4e5f6"
}
```

**系统异常：**
```json
{
  "code": 500,
  "msg": "系统繁忙，请稍后重试",
  "data": null,
  "traceId": "a1b2c3d4e5f6"
}
```

**错误码枚举类：**
```java
@Getter
@AllArgsConstructor
public enum ErrorCode {

    // 通用错误
    SUCCESS(200, "操作成功"),
    PARAM_ERROR(400, "参数错误"),
    UNAUTHORIZED(401, "未认证"),
    FORBIDDEN(403, "无权限"),
    NOT_FOUND(404, "资源不存在"),
    INTERNAL_ERROR(500, "系统繁忙，请稍后重试"),

    // 用户相关
    USER_NOT_FOUND(404, "用户不存在"),
    USER_PASSWORD_ERROR(400, "用户名或密码错误"),
    USER_DISABLED(403, "用户已被禁用"),

    // 订单相关
    ORDER_NOT_FOUND(404, "订单不存在"),
    ORDER_INSUFFICIENT_STOCK(400, "库存不足"),
    ORDER_INSUFFICIENT_BALANCE(400, "余额不足"),
    ORDER_CANNOT_CANCEL(400, "订单状态不允许取消"),

    // 支付相关
    PAYMENT_FAILED(500, "支付失败"),
    PAYMENT_TIMEOUT(500, "支付超时");

    private final int code;
    private final String msg;
}
```

### 错误示例

```json
// ❌ 暴露技术细节
{
  "code": 500,
  "msg": "NullPointerException at com.example.service.UserService.getUser(UserService.java:123)",
  "data": null
}

// ❌ 错误信息不明确
{
  "code": 400,
  "msg": "参数错误",
  "data": null
}

// ❌ 使用技术术语
{
  "code": 500,
  "msg": "数据库连接超时",
  "data": null
}

// ❌ 暴露敏感信息
{
  "code": 404,
  "msg": "用户 zhangsan 不存在，数据库查询：SELECT * FROM t_user WHERE username = 'zhangsan'",
  "data": null
}
```

## 4. 检查清单

- [ ] HTTP 状态码使用正确
- [ ] 业务状态码使用统一的命名规范
- [ ] 错误信息对用户友好，易于理解
- [ ] 参数校验错误明确提示哪个参数错误
- [ ] 业务规则错误明确提示业务原因
- [ ] 系统异常不暴露堆栈信息
- [ ] 不暴露系统内部实现细节
- [ ] 不暴露敏感信息（用户名、SQL 语句等）
- [ ] 在可能的情况下提供解决方案
- [ ] 所有错误响应包含 traceId 字段

---

**版本：** 1.0
**最后更新：** 2026-03-23
