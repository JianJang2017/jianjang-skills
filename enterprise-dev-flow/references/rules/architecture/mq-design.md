# 消息队列设计

> 适用范围：所有使用 RocketMQ 的场景，适用于架构师、研发人员

---

## 1. 规则说明

消息队列是实现系统解耦、异步处理和削峰填谷的重要手段。本规范定义了 RocketMQ 的 Topic/Tag 命名规范、消息可靠性保障、幂等消费实现和死信队列处理。

## 2. 规则内容

### 2.1 Topic/Tag 命名规范

**Topic 命名格式：** `项目名_业务域_动作`

**示例：**
```
mall_order_created      # 订单创建
mall_payment_success    # 支付成功
mall_notification       # 通知
```

**Tag 命名规范：**
- 使用小写字母
- 多个单词使用下划线（_）分隔
- 表示消息的具体类型

**示例：**
```
pay_success             # 支付成功
pay_fail                # 支付失败
sms_send                # 短信发送
email_send              # 邮件发送
```

### 2.2 消息可靠性保障

#### 生产者可靠性

**方式一：同步发送（推荐）**

```java
@Service
public class OrderServiceImpl implements OrderService {

    @Override
    @Transactional
    public void createOrder(CreateOrderReq req) {
        // 1. 创建订单
        Order order = new Order();
        order.setUserId(req.getUserId());
        order.setAmount(req.getAmount());
        orderMapper.insert(order);

        // 2. 同步发送消息
        OrderCreatedEvent event = new OrderCreatedEvent();
        event.setOrderId(order.getId());
        event.setUserId(order.getUserId());

        SendResult result = rocketMQTemplate.syncSend(
            "mall_order_created:pay_success", event);

        if (result.getSendStatus() != SendStatus.SEND_OK) {
            throw new BizException("消息发送失败");
        }
    }
}
```

**方式二：事务消息（强一致性）**

```java
@Service
public class OrderServiceImpl implements OrderService {

    @Override
    public void createOrder(CreateOrderReq req) {
        // 1. 发送事务消息
        Message<CreateOrderReq> message = MessageBuilder
            .withPayload(req)
            .setHeader("orderId", generateOrderId())
            .build();

        TransactionSendResult result = rocketMQTemplate.sendMessageInTransaction(
            "mall_order_created", message, req);

        if (result.getLocalTransactionState() != LocalTransactionState.COMMIT_MESSAGE) {
            throw new BizException("创建订单失败");
        }
    }
}

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
```

#### 消费者可靠性

**消费确认机制：**
- 消费成功：返回 `ConsumeConcurrentlyStatus.CONSUME_SUCCESS`
- 消费失败：返回 `ConsumeConcurrentlyStatus.RECONSUME_LATER`

```java
@RocketMQMessageListener(
    topic = "mall_order_created",
    consumerGroup = "inventory_service",
    selectorExpression = "pay_success"
)
public class OrderCreatedListener implements RocketMQListener<OrderCreatedEvent> {

    @Override
    public void onMessage(OrderCreatedEvent event) {
        try {
            // 处理消息
            inventoryService.deductStock(event.getOrderId());

            // 消费成功，自动返回 CONSUME_SUCCESS
        } catch (BizException e) {
            // 业务异常，抛出异常触发重试
            log.error("扣减库存失败，订单ID：{}", event.getOrderId(), e);
            throw e;
        } catch (Exception e) {
            // 系统异常，抛出异常触发重试
            log.error("处理消息失败", e);
            throw e;
        }
    }
}
```

### 2.3 幂等消费实现

**方式一：请求 ID 去重（推荐）**

```java
@RocketMQMessageListener(topic = "mall_order_created", consumerGroup = "inventory_service")
public class OrderCreatedListener implements RocketMQListener<OrderCreatedEvent> {

    @Override
    public void onMessage(OrderCreatedEvent event) {
        String requestId = event.getRequestId();
        String key = "consumed:" + requestId;

        // 检查是否已消费
        Boolean consumed = redisTemplate.opsForValue()
            .setIfAbsent(key, "1", 7, TimeUnit.DAYS);

        if (!consumed) {
            log.warn("消息已消费，跳过处理：{}", requestId);
            return;
        }

        try {
            // 执行业务逻辑
            inventoryService.deductStock(event.getOrderId());
        } catch (Exception e) {
            // 消费失败，删除去重标记，允许重试
            redisTemplate.delete(key);
            throw e;
        }
    }
}
```

**方式二：数据库唯一索引**

```java
@RocketMQMessageListener(topic = "mall_order_created", consumerGroup = "inventory_service")
public class OrderCreatedListener implements RocketMQListener<OrderCreatedEvent> {

    @Override
    public void onMessage(OrderCreatedEvent event) {
        try {
            // 插入消费记录（唯一索引：message_id）
            ConsumeRecord record = new ConsumeRecord();
            record.setMessageId(event.getMessageId());
            record.setTopic("mall_order_created");
            record.setConsumeTime(LocalDateTime.now());
            consumeRecordMapper.insert(record);

            // 执行业务逻辑
            inventoryService.deductStock(event.getOrderId());

        } catch (DuplicateKeyException e) {
            // 消息已消费，跳过处理
            log.warn("消息已消费，跳过处理：{}", event.getMessageId());
        }
    }
}
```

### 2.4 死信队列处理

**死信队列定义：**
- 消息消费失败，重试次数超过最大重试次数（默认 16 次）
- 消息会被投递到死信队列（DLQ）

**死信队列命名：** `%DLQ%{ConsumerGroup}`

**死信队列处理：**

```java
@RocketMQMessageListener(
    topic = "%DLQ%inventory_service",
    consumerGroup = "inventory_service_dlq"
)
public class OrderCreatedDLQListener implements RocketMQListener<OrderCreatedEvent> {

    @Override
    public void onMessage(OrderCreatedEvent event) {
        // 记录死信消息
        log.error("死信消息：{}", JSON.toJSONString(event));

        // 发送告警
        alertService.sendAlert("死信消息", JSON.toJSONString(event));

        // 人工处理或补偿
        // ...
    }
}
```

### 2.5 消息设计规范

| 项目 | 规范 | 说明 |
|------|------|------|
| 消息体大小 | < 4MB | 超过限制会发送失败 |
| 消息 Key | 必须 | 用于消息去重和查询 |
| 消息 Tag | 推荐 | 用于消息过滤 |
| 消息属性 | 可选 | 用于扩展信息 |
| 消息内容 | JSON | 统一使用 JSON 格式 |

**消息体设计：**

```java
@Data
public class OrderCreatedEvent {

    /**
     * 消息 ID（全局唯一）
     */
    private String messageId;

    /**
     * 请求 ID（用于幂等）
     */
    private String requestId;

    /**
     * 订单 ID
     */
    private Long orderId;

    /**
     * 用户 ID
     */
    private Long userId;

    /**
     * 订单金额
     */
    private BigDecimal amount;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;
}
```

## 3. 示例

### 正确示例

**消息队列设计文档：**

```markdown
### 消息队列设计

| Topic | Tag | 生产者 | 消费者 | 消息体结构 | 可靠性要求 |
|-------|-----|-------|-------|----------|---------|
| mall_order_created | pay_success | OrderService | InventoryService | {orderId, userId, amount} | 事务消息 |
| mall_notification | sms_send | NotifyService | SmsService | {phone, template, params} | 普通消息+重试 |

**消费端幂等保障方式：**
- InventoryService：Redis 去重，key = "consumed:" + requestId，过期时间 7 天
- SmsService：数据库唯一索引，message_id 唯一

**死信队列处理：**
- 死信消息记录日志
- 发送告警通知
- 人工处理或补偿
```

**生产者代码：**

```java
@Service
public class OrderServiceImpl implements OrderService {

    @Override
    @Transactional
    public void createOrder(CreateOrderReq req) {
        // 1. 创建订单
        Order order = new Order();
        order.setUserId(req.getUserId());
        order.setAmount(req.getAmount());
        orderMapper.insert(order);

        // 2. 发送消息
        OrderCreatedEvent event = new OrderCreatedEvent();
        event.setMessageId(UUID.randomUUID().toString());
        event.setRequestId(UUID.randomUUID().toString());
        event.setOrderId(order.getId());
        event.setUserId(order.getUserId());
        event.setAmount(order.getAmount());
        event.setCreateTime(LocalDateTime.now());

        Message<OrderCreatedEvent> message = MessageBuilder
            .withPayload(event)
            .setHeader(RocketMQHeaders.KEYS, event.getOrderId().toString())
            .setHeader(RocketMQHeaders.TAGS, "pay_success")
            .build();

        SendResult result = rocketMQTemplate.syncSend("mall_order_created", message);

        if (result.getSendStatus() != SendStatus.SEND_OK) {
            throw new BizException("消息发送失败");
        }
    }
}
```

**消费者代码：**

```java
@RocketMQMessageListener(
    topic = "mall_order_created",
    consumerGroup = "inventory_service",
    selectorExpression = "pay_success"
)
public class OrderCreatedListener implements RocketMQListener<OrderCreatedEvent> {

    @Override
    public void onMessage(OrderCreatedEvent event) {
        String requestId = event.getRequestId();
        String key = "consumed:" + requestId;

        // 幂等检查
        Boolean consumed = redisTemplate.opsForValue()
            .setIfAbsent(key, "1", 7, TimeUnit.DAYS);

        if (!consumed) {
            log.warn("消息已消费，跳过处理：{}", requestId);
            return;
        }

        try {
            // 执行业务逻辑
            inventoryService.deductStock(event.getOrderId());
        } catch (Exception e) {
            // 消费失败，删除去重标记，允许重试
            redisTemplate.delete(key);
            throw e;
        }
    }
}
```

### 错误示例

```java
// ❌ Topic 命名不规范
rocketMQTemplate.syncSend("order", event);

// ❌ 没有设置消息 Key
Message<OrderCreatedEvent> message = MessageBuilder
    .withPayload(event)
    .build();

// ❌ 没有检查发送结果
rocketMQTemplate.syncSend("mall_order_created", event);

// ❌ 没有幂等检查
@RocketMQMessageListener(topic = "mall_order_created", consumerGroup = "inventory_service")
public class OrderCreatedListener implements RocketMQListener<OrderCreatedEvent> {

    @Override
    public void onMessage(OrderCreatedEvent event) {
        // 直接处理，没有幂等检查
        inventoryService.deductStock(event.getOrderId());
    }
}

// ❌ 消费失败不抛出异常
@RocketMQMessageListener(topic = "mall_order_created", consumerGroup = "inventory_service")
public class OrderCreatedListener implements RocketMQListener<OrderCreatedEvent> {

    @Override
    public void onMessage(OrderCreatedEvent event) {
        try {
            inventoryService.deductStock(event.getOrderId());
        } catch (Exception e) {
            // 捕获异常但不抛出，消息会被确认消费
            log.error("处理消息失败", e);
        }
    }
}
```

## 4. 检查清单

- [ ] Topic 命名符合规范（项目名_业务域_动作）
- [ ] Tag 命名符合规范（小写字母，下划线分隔）
- [ ] 消息体大小 < 4MB
- [ ] 设置了消息 Key
- [ ] 消息内容使用 JSON 格式
- [ ] 生产者检查了发送结果
- [ ] 消费者实现了幂等消费
- [ ] 消费失败时抛出异常触发重试
- [ ] 配置了死信队列处理
- [ ] 消息队列设计在文档中明确说明

---

**版本：** 1.0
**最后更新：** 2026-03-23
