# 安全红线规范

> 任何角色书写的文档和代码均不得违反以下规则

## 适用范围

本规范适用于：
- 产品经理编写PRD文档
- 研发人员编写代码和设计文档
- 测试工程师编写测试用例

## 1. 敏感信息保护

### 1.1 禁止明文展示

严禁在以下场景明文展示敏感信息：
- 文档中的示例数据
- 日志输出
- API响应
- 前端页面展示
- 错误提示信息

### 1.2 敏感信息清单

| 敏感信息类型 | 保护要求 | 示例 |
|------------|---------|------|
| 用户密码 | 严禁明文存储和传输，必须加密 | - |
| 短信验证码 | 严禁在日志和响应中展示 | - |
| 银行卡号 | 必须脱敏展示 | `6222 **** **** 1234` |
| CVV安全码 | 严禁存储和展示 | - |
| 完整身份证号 | 必须脱敏展示 | `110101********1234` |
| 完整手机号 | 必须脱敏展示 | `138****1234` |
| AccessKey/SecretKey | 严禁硬编码，必须通过配置中心管理 | - |

### 1.3 脱敏规则

**手机号脱敏：**
```
原始：13812345678
脱敏：138****5678
```

**身份证号脱敏：**
```
原始：110101199001011234
脱敏：110101********1234
```

**银行卡号脱敏：**
```
原始：6222021234567890123
脱敏：6222 **** **** 0123
```

### 1.4 密钥管理

- AccessKey / SecretKey 严禁硬编码在代码中
- 必须通过配置中心（Nacos）或环境变量管理
- 私有文件（合同、证件）严禁前端直接访问
- 必须通过后端签发临时 Presigned URL（有效期≤1小时）

## 2. SQL 安全

### 2.1 SQL 注入防护

**强制要求：**
- 严禁 SQL 注入风险
- 必须使用预编译语句或 MyBatis `#{}` 占位符
- 禁止使用字符串拼接构建 SQL

**正确示例（MyBatis）：**
```xml
<select id="getUserById" resultType="User">
    SELECT * FROM t_user WHERE id = #{userId}
</select>
```

**错误示例：**
```xml
<!-- 危险！存在SQL注入风险 -->
<select id="getUserById" resultType="User">
    SELECT * FROM t_user WHERE id = ${userId}
</select>
```

### 2.2 禁止 SELECT *

**强制要求：**
- 严禁使用 `SELECT *`
- 必须明确列出需要查询的字段

**原因：**
- 避免查询不必要的字段，浪费网络带宽和内存
- 防止表结构变更导致的问题
- 提高查询性能

**正确示例：**
```sql
SELECT id, username, nickname, email FROM t_user WHERE id = ?
```

**错误示例：**
```sql
SELECT * FROM t_user WHERE id = ?
```

## 3. 越权访问防护

### 3.1 权限校验要求

**强制要求：**
- 接口必须校验当前登录用户是否有权操作该数据
- 不能仅依赖前端传参，必须在后端验证
- 权限控制粒度到按钮级（RBAC/ABAC）

### 3.2 常见越权场景

| 场景 | 风险 | 防护措施 |
|------|------|---------|
| 查询他人订单 | 用户A通过修改订单ID查看用户B的订单 | 校验订单归属：`order.userId == currentUserId` |
| 修改他人信息 | 用户A通过修改用户ID修改用户B的信息 | 校验操作权限：`targetUserId == currentUserId` |
| 删除他人数据 | 普通用户删除管理员数据 | 校验角色权限：`hasRole('ADMIN')` |

### 3.3 实现示例

```java
// 正确示例：校验数据归属
@GetMapping("/orders/{orderId}")
public Result<OrderDTO> getOrder(@PathVariable Long orderId) {
    Order order = orderService.getById(orderId);

    // 防越权：校验订单是否属于当前用户
    Long currentUserId = SecurityUtils.getCurrentUserId();
    if (!order.getUserId().equals(currentUserId)) {
        throw new BizException(ErrorCode.FORBIDDEN, "无权访问该订单");
    }

    return Result.success(OrderConverter.toDTO(order));
}
```

## 4. 错误信息安全

### 4.1 错误信息处理原则

**强制要求：**
- 系统错误严禁将原始堆栈信息暴露给前端用户
- 对外统一返回友好提示
- 内部记录详细的 Error Log（包含堆栈信息）

### 4.2 错误响应规范

| 错误类型 | 对外提示 | 内部日志 |
|---------|---------|---------|
| 系统异常 | "系统繁忙，请稍后重试" | 完整堆栈信息 + TraceID |
| 数据库异常 | "系统繁忙，请稍后重试" | SQL语句 + 异常信息 |
| 第三方服务异常 | "服务暂时不可用，请稍后重试" | 请求参数 + 响应内容 |
| 业务规则异常 | 明确的业务提示（如"库存不足"） | 业务上下文 + 参数 |

### 4.3 实现示例

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e, HttpServletRequest request) {
        String traceId = MDC.get("traceId");

        // 内部记录详细日志
        log.error("系统异常, traceId={}, uri={}", traceId, request.getRequestURI(), e);

        // 对外返回友好提示，不暴露堆栈
        return Result.error(500, "系统繁忙，请稍后重试", traceId);
    }
}
```

## 5. 安全检查清单

在提交代码前，必须逐项检查：

- [ ] 敏感信息已脱敏（手机号、身份证号、银行卡号）
- [ ] 密码、密钥未硬编码
- [ ] SQL 使用预编译，无注入风险
- [ ] 禁止使用 `SELECT *`
- [ ] 接口已实现越权校验
- [ ] 错误信息不暴露堆栈
- [ ] 日志中无敏感信息
- [ ] 私有文件通过临时URL访问

## 6. 违规处理

违反安全红线的代码：
- **P0级缺陷**：必须立即修复，阻断上线
- **代码审查不通过**：必须修改后重新提交
- **安全审计记录**：纳入个人绩效考核

---

**文档版本**: 1.0
**创建日期**: 2026-03-23
**适用项目**: 所有企业级项目
