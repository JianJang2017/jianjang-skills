# 事务边界规范

> 适用范围：所有涉及数据库事务的业务逻辑，适用于研发人员设计和实现事务边界

---

## 1. 规则说明

事务边界是指事务的开始和结束范围。合理的事务边界能够保证数据一致性，同时避免事务过大导致的性能问题和死锁风险。本规范定义了事务边界的设计原则和最佳实践。

## 2. 规则内容

### 2.1 事务粒度控制

**原则：事务应该尽可能小，只包含必须保证原子性的操作。**

- **事务内操作**：数据库写操作（INSERT、UPDATE、DELETE）
- **事务外操作**：RPC 调用、文件 IO、复杂计算、发送消息

### 2.2 事务内禁止的操作

| 操作类型 | 原因 | 替代方案 |
|---------|------|---------|
| RPC 调用 | 网络延迟长，占用数据库连接 | 事务提交后调用，或使用事务消息 |
| 文件 IO | IO 操作慢，占用数据库连接 | 事务提交后操作 |
| 复杂计算 | 耗时长，占用数据库连接 | 事务前计算好 |
| 发送 MQ 消息 | 可能失败，影响事务 | 使用事务消息或事务提交后发送 |
| 调用第三方接口 | 不可控，可能超时 | 事务提交后调用，或使用异步补偿 |

### 2.3 本地事务 vs 分布式事务

| 场景 | 事务类型 | 实现方式 |
|------|---------|---------|
| 单数据库操作 | 本地事务 | @Transactional |
| 多数据库操作（强一致） | 分布式事务 | Seata AT 模式 |
| 多服务操作（最终一致） | 分布式事务 | RocketMQ 事务消息 |

### 2.4 事务传播行为

| 传播行为 | 说明 | 使用场景 |
|---------|------|---------|
| REQUIRED（默认） | 如果当前存在事务，则加入；否则新建 | 大部分场景 |
| REQUIRES_NEW | 总是新建事务，挂起当前事务 | 日志记录、审计 |
| NESTED | 嵌套事务，子事务回滚不影响父事务 | 部分失败可接受的场景 |
| SUPPORTS | 如果当前存在事务，则加入；否则非事务执行 | 查询操作 |
| NOT_SUPPORTED | 总是非事务执行，挂起当前事务 | 不需要事务的操作 |
| NEVER | 总是非事务执行，如果存在事务则抛异常 | 明确不允许事务的操作 |

### 2.5 事务超时设置

```java
@Transactional(timeout = 30)  // 30 秒超时
public void createOrder(CreateOrderReq req) {
    // ...
}
```

**建议超时时间：**
- 简单操作：5-10 秒
- 复杂操作：30-60 秒
- 批量操作：根据数据量设置

### 2.6 事务回滚规则

```java
// 默认只回滚 RuntimeException 和 Error
@Transactional

// 回滚所有异常
@Transactional(rollbackFor = Exception.class)

// 不回滚指定异常
@Transactional(noRollbackFor = BizException.class)
```

## 3. 示例

### 正确示例

**示例 1：本地事务（单数据库操作）**

```java
@Service
public class OrderServiceImpl implements OrderService {

    @Override
    @Transactional(rollbackFor = Exception.class, timeout = 30)
    public OrderResp createOrder(CreateOrderReq req) {
        // 1. 参数校验（事务外）
        User user = userService.getById(req.getUserId());
        if (user == null) {
            throw new BizException("用户不存在");
        }

        // 2. 计算金额（事务外）
        BigDecimal totalAmount = calculateAmount(req.getItems());

        // 3. 数据库操作（事务内）
        Order order = new Order();
        order.setUserId(req.getUserId());
        order.setAmount(totalAmount);
        order.setStatus(OrderStatus.PENDING);
        orderMapper.insert(order);

        // 4. 插入订单明细（事务内）
        for (OrderItemReq item : req.getItems()) {
            OrderItem orderItem = new OrderItem();
            orderItem.setOrderId(order.getId());
            orderItem.setProductId(item.getProductId());
            orderItem.setQuantity(item.getQuantity());
            orderItemMapper.insert(orderItem);
        }

        // 5. 扣减库存（事务内）
        for (OrderItemReq item : req.getItems()) {
            inventoryMapper.deductStock(item.getProductId(), item.getQuantity());
        }

        return OrderConverter.toResp(order);
    }

    // 事务提交后发送消息
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleOrderCreated(OrderCreatedEvent event) {
        // 发送 MQ 消息
        rocketMQTemplate.syncSend("order_created", event);

        // 发送短信通知
        smsService.sendOrderCreatedNotification(event.getUserId());
    }
}
```

**示例 2：分布式事务（RocketMQ 事务消息）**

```java
@Service
public class OrderServiceImpl implements OrderService {

    @Override
    public OrderResp createOrder(CreateOrderReq req) {
        // 1. 发送事务消息
        Message<CreateOrderReq> message = MessageBuilder
            .withPayload(req)
            .setHeader("orderId", generateOrderId())
            .build();

        TransactionSendResult result = rocketMQTemplate.sendMessageInTransaction(
            "order_created", message, req);

        if (result.getLocalTransactionState() != LocalTransactionState.COMMIT_MESSAGE) {
            throw new BizException("创建订单失败");
        }

        // 2. 返回结果
        return OrderConverter.toResp(result);
    }

    // 执行本地事务
    @RocketMQTransactionListener
    public class OrderTransactionListener implements RocketMQLocalTransactionListener {

        @Override
        @Transactional(rollbackFor = Exception.class)
        public RocketMQLocalTransactionState executeLocalTransaction(Message msg, Object arg) {
            try {
                CreateOrderReq req = (CreateOrderReq) arg;

                // 执行本地事务
                Order order = new Order();
                order.setUserId(req.getUserId());
                order.setAmount(req.getAmount());
                orderMapper.insert(order);

                return RocketMQLocalTransactionState.COMMIT;
            } catch (Exception e) {
                log.error("本地事务执行失败", e);
                return RocketMQLocalTransactionState.ROLLBACK;
            }
        }

        @Override
        public RocketMQLocalTransactionState checkLocalTransaction(Message msg) {
            // 检查本地事务状态
            String orderId = msg.getHeaders().get("orderId", String.class);
            Order order = orderMapper.selectByOrderId(orderId);

            if (order != null) {
                return RocketMQLocalTransactionState.COMMIT;
            } else {
                return RocketMQLocalTransactionState.ROLLBACK;
            }
        }
    }
}
```

**示例 3：嵌套事务（日志记录）**

```java
@Service
public class OrderServiceImpl implements OrderService {

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void cancelOrder(Long orderId) {
        // 1. 更新订单状态
        Order order = orderMapper.selectById(orderId);
        order.setStatus(OrderStatus.CANCELLED);
        orderMapper.updateById(order);

        // 2. 恢复库存
        List<OrderItem> items = orderItemMapper.selectByOrderId(orderId);
        for (OrderItem item : items) {
            inventoryMapper.restoreStock(item.getProductId(), item.getQuantity());
        }

        // 3. 记录操作日志（独立事务，即使主事务回滚也要记录）
        operationLogService.log(orderId, "取消订单");
    }
}

@Service
public class OperationLogServiceImpl implements OperationLogService {

    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void log(Long orderId, String operation) {
        OperationLog log = new OperationLog();
        log.setOrderId(orderId);
        log.setOperation(operation);
        log.setOperateTime(LocalDateTime.now());
        operationLogMapper.insert(log);
    }
}
```

### 错误示例

```java
// ❌ 事务内调用 RPC
@Transactional
public void createOrder(CreateOrderReq req) {
    // 插入订单
    orderMapper.insert(order);

    // ❌ 事务内调用 RPC，占用数据库连接
    UserResp user = userServiceClient.getUser(req.getUserId());

    // ❌ 事务内调用第三方接口，可能超时
    PaymentResp payment = paymentClient.pay(order.getId());
}

// ❌ 事务内发送 MQ 消息
@Transactional
public void createOrder(CreateOrderReq req) {
    // 插入订单
    orderMapper.insert(order);

    // ❌ 事务内发送消息，如果消息发送失败会导致事务回滚
    rocketMQTemplate.syncSend("order_created", order);
}

// ❌ 事务内进行复杂计算
@Transactional
public void createOrder(CreateOrderReq req) {
    // ❌ 事务内进行复杂计算，占用数据库连接
    BigDecimal totalAmount = BigDecimal.ZERO;
    for (OrderItemReq item : req.getItems()) {
        Product product = productMapper.selectById(item.getProductId());
        BigDecimal itemAmount = product.getPrice().multiply(new BigDecimal(item.getQuantity()));
        totalAmount = totalAmount.add(itemAmount);
    }

    // 插入订单
    Order order = new Order();
    order.setAmount(totalAmount);
    orderMapper.insert(order);
}

// ❌ 事务过大
@Transactional
public void batchCreateOrders(List<CreateOrderReq> reqList) {
    // ❌ 批量操作在一个事务内，事务过大
    for (CreateOrderReq req : reqList) {
        Order order = new Order();
        order.setUserId(req.getUserId());
        orderMapper.insert(order);

        // 调用其他服务
        inventoryService.deductStock(req.getProductId(), req.getQuantity());
    }
}

// ❌ 没有设置回滚规则
@Transactional  // 默认只回滚 RuntimeException
public void createOrder(CreateOrderReq req) throws Exception {
    orderMapper.insert(order);

    // 抛出 Exception，但不会回滚
    throw new Exception("创建订单失败");
}
```

## 4. 检查清单

- [ ] 事务只包含必须保证原子性的数据库操作
- [ ] 事务内没有 RPC 调用
- [ ] 事务内没有文件 IO 操作
- [ ] 事务内没有复杂计算
- [ ] 事务内没有发送 MQ 消息（除非使用事务消息）
- [ ] 事务内没有调用第三方接口
- [ ] 设置了合理的事务超时时间
- [ ] 设置了正确的回滚规则（rollbackFor = Exception.class）
- [ ] 选择了合适的事务传播行为
- [ ] 批量操作考虑了事务大小，避免事务过大
- [ ] 跨服务操作使用了分布式事务方案

---

**版本：** 1.0
**最后更新：** 2026-03-23
