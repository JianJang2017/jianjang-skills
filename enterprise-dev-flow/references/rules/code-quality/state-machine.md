# 状态机规范

> 适用范围：所有包含状态流转的业务实体（订单、审批、任务等），适用于产品经理设计状态流转、研发人员实现状态机、测试工程师编写测试用例

---

## 1. 规则说明

状态机是管理业务实体状态流转的标准方式，能够清晰定义状态之间的转换规则，防止非法状态流转。本规范定义了状态机设计的四要素和最佳实践。

## 2. 规则内容

### 2.1 状态机四要素

文档中必须明确以下四要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| **状态列表** | 所有合法状态的完整枚举 | 待支付、已支付、配货中、已发货、已完成、已取消 |
| **触发事件** | 导致状态变更的动作 | 用户支付、超时未付、管理员取消 |
| **动作** | 状态变更时需要执行的操作 | 扣减库存、发送短信、写入流水 |
| **约束条件** | 状态流转的前提条件 | 只有"已支付"才能触发"发货" |

### 2.2 状态定义规范

**状态命名规则：**
- 使用过去分词或形容词（已支付、待审核、进行中）
- 避免使用动词（支付、审核、进行）
- 状态名称清晰明确，不产生歧义

**状态枚举定义：**
```java
@Getter
@AllArgsConstructor
public enum OrderStatus {

    PENDING(0, "待支付"),
    PAID(1, "已支付"),
    PREPARING(2, "配货中"),
    SHIPPED(3, "已发货"),
    COMPLETED(4, "已完成"),
    CANCELLED(5, "已取消");

    private final int code;
    private final String desc;
}
```

### 2.3 状态流转规则

**状态流转矩阵：**

| 当前状态 | 可流转到的状态 | 触发事件 | 约束条件 |
|---------|--------------|---------|---------|
| 待支付 | 已支付 | 用户支付 | 支付成功 |
| 待支付 | 已取消 | 超时未付 | 超过30分钟 |
| 待支付 | 已取消 | 用户取消 | 无 |
| 已支付 | 配货中 | 系统自动 | 库存充足 |
| 已支付 | 已取消 | 管理员取消 | 有权限 |
| 配货中 | 已发货 | 仓库发货 | 配货完成 |
| 已发货 | 已完成 | 用户确认收货 | 无 |
| 已发货 | 已完成 | 系统自动 | 超过7天 |

**状态流转图：**
```
待支付 ──支付成功──> 已支付 ──自动──> 配货中 ──发货──> 已发货 ──确认收货──> 已完成
  │                    │
  │                    │
  └──超时/取消──> 已取消 <──┘
```

### 2.4 状态流转实现

**方式一：枚举 + 状态流转表**

```java
@Getter
@AllArgsConstructor
public enum OrderStatus {

    PENDING(0, "待支付"),
    PAID(1, "已支付"),
    PREPARING(2, "配货中"),
    SHIPPED(3, "已发货"),
    COMPLETED(4, "已完成"),
    CANCELLED(5, "已取消");

    private final int code;
    private final String desc;

    /**
     * 检查是否可以流转到目标状态
     */
    public boolean canTransitionTo(OrderStatus target) {
        switch (this) {
            case PENDING:
                return target == PAID || target == CANCELLED;
            case PAID:
                return target == PREPARING || target == CANCELLED;
            case PREPARING:
                return target == SHIPPED;
            case SHIPPED:
                return target == COMPLETED;
            default:
                return false;
        }
    }
}
```

**方式二：状态机框架（Spring State Machine）**

```java
@Configuration
@EnableStateMachine
public class OrderStateMachineConfig extends StateMachineConfigurerAdapter<OrderStatus, OrderEvent> {

    @Override
    public void configure(StateMachineStateConfigurer<OrderStatus, OrderEvent> states) throws Exception {
        states
            .withStates()
            .initial(OrderStatus.PENDING)
            .states(EnumSet.allOf(OrderStatus.class));
    }

    @Override
    public void configure(StateMachineTransitionConfigurer<OrderStatus, OrderEvent> transitions) throws Exception {
        transitions
            // 待支付 -> 已支付
            .withExternal()
                .source(OrderStatus.PENDING)
                .target(OrderStatus.PAID)
                .event(OrderEvent.PAY)
                .action(payAction())
            .and()
            // 待支付 -> 已取消
            .withExternal()
                .source(OrderStatus.PENDING)
                .target(OrderStatus.CANCELLED)
                .event(OrderEvent.CANCEL)
                .action(cancelAction())
            .and()
            // 已支付 -> 配货中
            .withExternal()
                .source(OrderStatus.PAID)
                .target(OrderStatus.PREPARING)
                .event(OrderEvent.PREPARE)
                .action(prepareAction());
    }

    @Bean
    public Action<OrderStatus, OrderEvent> payAction() {
        return context -> {
            // 执行支付后的操作
            Long orderId = context.getMessage().getHeaders().get("orderId", Long.class);
            // 扣减库存、发送通知等
        };
    }
}
```

### 2.5 状态流转操作

```java
@Service
public class OrderServiceImpl implements OrderService {

    @Override
    @Transactional
    public void payOrder(Long orderId) {
        Order order = orderMapper.selectById(orderId);

        // 检查当前状态
        if (order.getStatus() != OrderStatus.PENDING) {
            throw new BizException("订单状态不允许支付");
        }

        // 检查是否可以流转
        if (!order.getStatus().canTransitionTo(OrderStatus.PAID)) {
            throw new BizException("订单状态流转失败");
        }

        // 更新状态（使用乐观锁）
        int rows = orderMapper.updateStatus(
            orderId, OrderStatus.PENDING, OrderStatus.PAID, order.getVersion());

        if (rows == 0) {
            throw new BizException("订单状态已变更，请刷新后重试");
        }

        // 执行状态流转后的操作
        // 1. 扣减库存
        inventoryService.deductStock(order.getProductId(), order.getQuantity());

        // 2. 发送通知
        notificationService.sendPaySuccessNotification(order.getUserId());

        // 3. 写入流水
        paymentService.createPaymentRecord(orderId);
    }
}
```

## 3. 示例

### 正确示例

**订单状态机设计：**

**1. 状态列表：**
- 待支付（PENDING）
- 已支付（PAID）
- 配货中（PREPARING）
- 已发货（SHIPPED）
- 已完成（COMPLETED）
- 已取消（CANCELLED）

**2. 触发事件：**
- 用户支付（PAY）
- 超时未付（TIMEOUT）
- 用户取消（CANCEL）
- 管理员取消（ADMIN_CANCEL）
- 仓库发货（SHIP）
- 用户确认收货（CONFIRM）
- 系统自动确认（AUTO_CONFIRM）

**3. 状态流转规则：**

| 当前状态 | 触发事件 | 目标状态 | 约束条件 | 执行动作 |
|---------|---------|---------|---------|---------|
| 待支付 | 用户支付 | 已支付 | 支付成功 | 扣减库存、发送通知 |
| 待支付 | 超时未付 | 已取消 | 超过30分钟 | 释放库存 |
| 待支付 | 用户取消 | 已取消 | 无 | 释放库存 |
| 已支付 | 系统自动 | 配货中 | 库存充足 | 通知仓库 |
| 已支付 | 管理员取消 | 已取消 | 有权限 | 退款、释放库存 |
| 配货中 | 仓库发货 | 已发货 | 配货完成 | 发送物流通知 |
| 已发货 | 用户确认收货 | 已完成 | 无 | 结算佣金 |
| 已发货 | 系统自动确认 | 已完成 | 超过7天 | 结算佣金 |

**4. 状态流转图：**
```
     ┌─────────┐
     │  待支付  │
     └────┬────┘
          │
    ┌─────┼─────┐
    │     │     │
  支付  超时  取消
    │     │     │
    ▼     ▼     ▼
┌────────┐  ┌────────┐
│ 已支付  │  │ 已取消  │
└───┬────┘  └────────┘
    │           ▲
  自动          │
    │         取消
    ▼           │
┌────────┐     │
│ 配货中  │─────┘
└───┬────┘
    │
  发货
    │
    ▼
┌────────┐
│ 已发货  │
└───┬────┘
    │
 确认收货
    │
    ▼
┌────────┐
│ 已完成  │
└────────┘
```

### 错误示例

```java
// ❌ 没有检查当前状态
public void payOrder(Long orderId) {
    Order order = orderMapper.selectById(orderId);

    // 直接更新状态，没有检查当前状态
    order.setStatus(OrderStatus.PAID);
    orderMapper.updateById(order);
}

// ❌ 没有使用乐观锁，存在并发问题
public void cancelOrder(Long orderId) {
    Order order = orderMapper.selectById(orderId);

    if (order.getStatus() == OrderStatus.PENDING) {
        // 没有使用版本号，可能被并发修改
        order.setStatus(OrderStatus.CANCELLED);
        orderMapper.updateById(order);
    }
}

// ❌ 状态流转规则不清晰
public void updateOrderStatus(Long orderId, OrderStatus newStatus) {
    Order order = orderMapper.selectById(orderId);

    // 允许任意状态流转，没有约束
    order.setStatus(newStatus);
    orderMapper.updateById(order);
}
```

## 4. 检查清单

- [ ] 明确定义了所有合法状态
- [ ] 明确定义了所有触发事件
- [ ] 明确定义了状态流转规则
- [ ] 明确定义了状态流转的约束条件
- [ ] 明确定义了状态流转后的执行动作
- [ ] 提供了状态流转图
- [ ] 状态流转使用乐观锁防止并发问题
- [ ] 状态流转前检查当前状态
- [ ] 状态流转失败时抛出明确的异常
- [ ] 测试用例覆盖所有状态流转路径

---

**版本：** 1.0
**最后更新：** 2026-03-23
