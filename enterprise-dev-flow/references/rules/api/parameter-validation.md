# 参数校验规范

> 适用范围：所有 HTTP API 接口参数校验，适用于产品经理定义参数规则、研发人员实现校验逻辑

---

## 1. 规则说明

参数校验是保证系统安全性和数据完整性的第一道防线。所有接口必须对请求参数进行严格校验，防止非法数据进入系统。本规范定义了参数校验的标准和最佳实践。

## 2. 规则内容

### 2.1 校验层级

| 层级 | 校验内容 | 实现方式 |
|------|---------|---------|
| Controller 层 | 基础校验（非空、格式、长度、范围） | @Valid / @Validated + 校验注解 |
| Service 层 | 业务规则校验（库存、余额、权限） | 业务逻辑代码 + 抛出业务异常 |

### 2.2 Controller 层校验

所有请求参数必须使用 `@Valid` 或 `@Validated` 进行校验：

```java
@PostMapping("/login")
public Result<LoginResp> login(@Valid @RequestBody LoginReq req) {
    // ...
}
```

### 2.3 常用校验注解

| 注解 | 适用类型 | 说明 | 示例 |
|------|---------|------|------|
| @NotNull | 所有类型 | 不能为 null | @NotNull(message = "用户ID不能为空") |
| @NotBlank | String | 不能为空字符串（null、""、" "） | @NotBlank(message = "用户名不能为空") |
| @NotEmpty | Collection/Array | 不能为空集合/数组 | @NotEmpty(message = "订单项不能为空") |
| @Size | String/Collection | 长度/大小限制 | @Size(min = 6, max = 16, message = "密码长度6-16位") |
| @Min / @Max | Number | 数值范围 | @Min(value = 1, message = "数量至少为1") |
| @DecimalMin / @DecimalMax | BigDecimal | 精确数值范围 | @DecimalMin(value = "0.01", message = "金额至少0.01元") |
| @Pattern | String | 正则表达式 | @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式错误") |
| @Email | String | 邮箱格式 | @Email(message = "邮箱格式错误") |
| @Past / @Future | Date/LocalDate | 过去/未来时间 | @Past(message = "出生日期必须是过去时间") |
| @Valid | Object | 嵌套对象校验 | @Valid private Address address; |

### 2.4 自定义校验注解

对于复杂的校验规则，可以自定义校验注解：

```java
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = PhoneValidator.class)
public @interface Phone {
    String message() default "手机号格式错误";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

### 2.5 Service 层校验

对于复杂的业务规则校验，在 Service 层进行：

```java
// 检查库存
if (product.getStock() < order.getQuantity()) {
    throw new BizException(ErrorCode.INSUFFICIENT_STOCK, "库存不足");
}

// 检查余额
if (user.getBalance().compareTo(order.getAmount()) < 0) {
    throw new BizException(ErrorCode.INSUFFICIENT_BALANCE, "余额不足");
}

// 检查权限
if (!user.hasPermission(Permission.ORDER_CANCEL)) {
    throw new BizException(ErrorCode.PERMISSION_DENIED, "无权限取消订单");
}
```

### 2.6 校验失败处理

- Controller 层校验失败：返回 400 错误，提示具体参数错误
- Service 层校验失败：抛出业务异常，返回业务错误码和提示信息

## 3. 示例

### 正确示例

**请求 DTO：**
```java
@Data
public class CreateOrderReq {

    @NotNull(message = "用户ID不能为空")
    private Long userId;

    @NotBlank(message = "收货地址不能为空")
    @Size(max = 200, message = "收货地址不能超过200字符")
    private String address;

    @NotEmpty(message = "订单项不能为空")
    @Size(max = 20, message = "订单项不能超过20个")
    @Valid
    private List<OrderItemReq> items;

    @NotNull(message = "订单金额不能为空")
    @DecimalMin(value = "0.01", message = "订单金额至少0.01元")
    @DecimalMax(value = "999999.99", message = "订单金额不能超过999999.99元")
    private BigDecimal amount;

    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式错误")
    private String phone;

    @Email(message = "邮箱格式错误")
    private String email;
}

@Data
public class OrderItemReq {

    @NotNull(message = "商品ID不能为空")
    private Long productId;

    @NotNull(message = "商品数量不能为空")
    @Min(value = 1, message = "商品数量至少为1")
    @Max(value = 999, message = "商品数量不能超过999")
    private Integer quantity;
}
```

**Controller 层：**
```java
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    @PostMapping
    public Result<OrderResp> createOrder(@Valid @RequestBody CreateOrderReq req) {
        OrderResp resp = orderService.createOrder(req);
        return Result.success(resp);
    }
}
```

**Service 层：**
```java
@Service
public class OrderServiceImpl implements OrderService {

    @Override
    @Transactional
    public OrderResp createOrder(CreateOrderReq req) {
        // 业务规则校验
        User user = userService.getById(req.getUserId());
        if (user == null) {
            throw new BizException(ErrorCode.USER_NOT_FOUND, "用户不存在");
        }

        // 检查库存
        for (OrderItemReq item : req.getItems()) {
            Product product = productService.getById(item.getProductId());
            if (product.getStock() < item.getQuantity()) {
                throw new BizException(ErrorCode.INSUFFICIENT_STOCK,
                    "商品【" + product.getName() + "】库存不足");
            }
        }

        // 检查余额
        if (user.getBalance().compareTo(req.getAmount()) < 0) {
            throw new BizException(ErrorCode.INSUFFICIENT_BALANCE, "余额不足");
        }

        // 创建订单
        // ...
    }
}
```

### 错误示例

```java
// ❌ 没有使用 @Valid 注解
@PostMapping
public Result<OrderResp> createOrder(@RequestBody CreateOrderReq req) {
    // ...
}

// ❌ 没有定义校验规则
@Data
public class CreateOrderReq {
    private Long userId;  // 缺少 @NotNull
    private String address;  // 缺少 @NotBlank 和 @Size
    private BigDecimal amount;  // 缺少 @NotNull 和范围校验
}

// ❌ 在 Controller 层进行业务规则校验
@PostMapping
public Result<OrderResp> createOrder(@Valid @RequestBody CreateOrderReq req) {
    // ❌ 不应该在 Controller 层检查库存
    if (product.getStock() < req.getQuantity()) {
        return Result.fail("库存不足");
    }
    // ...
}

// ❌ 校验失败不提供明确的错误信息
@NotBlank
private String username;  // 缺少 message 属性
```

## 4. 检查清单

- [ ] 所有请求参数使用 @Valid 或 @Validated 注解
- [ ] 必填参数使用 @NotNull 或 @NotBlank 注解
- [ ] 字符串参数定义长度限制（@Size）
- [ ] 数值参数定义范围限制（@Min、@Max）
- [ ] 格式参数使用正则表达式校验（@Pattern）
- [ ] 嵌套对象使用 @Valid 注解
- [ ] 所有校验注解提供明确的错误提示（message）
- [ ] 业务规则校验在 Service 层进行
- [ ] 校验失败抛出明确的业务异常
- [ ] 错误信息对用户友好，不暴露技术细节

---

**版本：** 1.0
**最后更新：** 2026-03-23
