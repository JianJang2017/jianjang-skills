# 异常处理规范

## 业务异常定义

### BizException 自定义异常

所有业务异常统一使用 `BizException` 类：

```java
public class BizException extends RuntimeException {
    private String code;
    private String message;

    public BizException(String code, String message) {
        super(message);
        this.code = code;
        this.message = message;
    }

    // getters
}
```

**使用示例：**
```java
// 抛出业务异常
throw new BizException("100001", "用户不存在");

// 使用 i18n 消息
throw new BizException("100001", messageSource.getMessage("user.not.found", null, locale));
```

## 异常编码规则

### 编码格式

**格式：** `模块编码(2位) + 业务错误码(4位)`

- **模块编码：** 从 10 开始，两位数字
- **业务错误码：** 从 0001 开始，四位数字

### 模块编码分配示例

| 模块编码 | 模块名称 | 说明 |
|---------|---------|------|
| 10 | 用户模块 | user |
| 11 | 订单模块 | order |
| 12 | 商品模块 | product |
| 13 | 支付模块 | payment |
| 14 | 库存模块 | inventory |
| 15 | 物流模块 | logistics |

### 错误码示例

| 错误码 | 模块 | 说明 | i18n Key |
|-------|------|------|----------|
| 100001 | 用户模块 | 用户不存在 | user.not.found |
| 100002 | 用户模块 | 用户已存在 | user.already.exists |
| 100003 | 用户模块 | 密码错误 | user.password.incorrect |
| 110001 | 订单模块 | 订单不存在 | order.not.found |
| 110002 | 订单模块 | 订单状态异常 | order.status.invalid |
| 120001 | 商品模块 | 商品不存在 | product.not.found |
| 120002 | 商品模块 | 商品库存不足 | product.stock.insufficient |

## i18n 国际化配置

### 配置文件结构

```
resources/
├── i18n/
│   ├── messages.properties          # 默认（中文）
│   ├── messages_en_US.properties    # 英文
│   └── messages_zh_CN.properties    # 简体中文
```

### 消息配置示例

**messages_zh_CN.properties:**
```properties
# 用户模块
user.not.found=用户不存在
user.already.exists=用户已存在
user.password.incorrect=密码错误

# 订单模块
order.not.found=订单不存在
order.status.invalid=订单状态异常

# 商品模块
product.not.found=商品不存在
product.stock.insufficient=商品库存不足
```

**messages_en_US.properties:**
```properties
# User Module
user.not.found=User not found
user.already.exists=User already exists
user.password.incorrect=Incorrect password

# Order Module
order.not.found=Order not found
order.status.invalid=Invalid order status

# Product Module
product.not.found=Product not found
product.stock.insufficient=Insufficient product stock
```

## 异常处理最佳实践

### 1. 统一异常处理器

使用 `@RestControllerAdvice` 统一处理异常：

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @Autowired
    private MessageSource messageSource;

    @ExceptionHandler(BizException.class)
    public Result<Void> handleBizException(BizException e, Locale locale) {
        String message = messageSource.getMessage(
            e.getCode(),
            null,
            e.getMessage(),
            locale
        );
        return Result.fail(e.getCode(), message);
    }

    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e) {
        log.error("系统异常", e);
        return Result.fail("999999", "系统异常，请稍后重试");
    }
}
```

### 2. 业务层抛出异常

```java
@Service
public class UserService {

    public UserDTO getUserById(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BizException("100001", "user.not.found");
        }
        return UserConverter.toDTO(user);
    }

    public void createUser(UserCreateDTO dto) {
        User existUser = userMapper.selectByUsername(dto.getUsername());
        if (existUser != null) {
            throw new BizException("100002", "user.already.exists");
        }
        // 创建用户逻辑
    }
}
```

### 3. 参数校验异常

```java
@ExceptionHandler(MethodArgumentNotValidException.class)
public Result<Void> handleValidationException(
    MethodArgumentNotValidException e) {

    String message = e.getBindingResult()
        .getFieldErrors()
        .stream()
        .map(FieldError::getDefaultMessage)
        .collect(Collectors.joining(", "));

    return Result.fail("400000", message);
}
```

## 异常编码规范总结

### 编码分配原则

1. **模块编码从 10 开始**，避免与系统保留编码冲突
2. **业务错误码从 0001 开始**，按功能顺序递增
3. **预留编码空间**，每个模块预留足够的编码空间（建议至少 100 个）
4. **统一管理**，在常量类或枚举中集中定义错误码

### 特殊错误码

| 错误码 | 说明 |
|-------|------|
| 400000 | 参数校验失败 |
| 401000 | 未认证 |
| 403000 | 无权限 |
| 404000 | 资源不存在 |
| 500000 | 系统内部错误 |
| 999999 | 未知异常 |

### 错误码常量定义

```java
public interface ErrorCode {
    // 用户模块 10xxxx
    String USER_NOT_FOUND = "100001";
    String USER_ALREADY_EXISTS = "100002";
    String USER_PASSWORD_INCORRECT = "100003";

    // 订单模块 11xxxx
    String ORDER_NOT_FOUND = "110001";
    String ORDER_STATUS_INVALID = "110002";

    // 商品模块 12xxxx
    String PRODUCT_NOT_FOUND = "120001";
    String PRODUCT_STOCK_INSUFFICIENT = "120002";
}
```
