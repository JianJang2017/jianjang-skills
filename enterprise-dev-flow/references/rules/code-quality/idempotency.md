# 幂等性设计

> 适用范围：所有写操作场景（创建、更新、删除），适用于产品经理设计功能、研发人员实现逻辑、测试工程师编写用例

---

## 1. 规则说明

幂等性是指同一操作重复执行多次，产生的结果与执行一次相同。在分布式系统中，由于网络超时、重试机制、消息队列重复消费等原因，同一请求可能被执行多次，因此必须设计幂等性保障机制。

## 2. 规则内容

### 2.1 什么是幂等

**幂等性定义**：同一操作重复发起多次，产生的结果与执行一次相同。

**幂等 vs 非幂等：**

| 操作类型 | 是否幂等 | 说明 |
|---------|---------|------|
| 查询操作（GET） | 是 | 多次查询结果相同 |
| 删除操作（DELETE） | 是 | 删除已删除的资源，结果相同 |
| 创建操作（POST） | 否 | 多次创建会产生多条记录 |
| 更新操作（PUT） | 是 | 多次更新为相同值，结果相同 |
| 部分更新（PATCH） | 否 | 累加操作等非幂等 |

### 2.2 必须设计幂等的场景

1. **用户连续点击提交按钮**：前端防抖失效或用户快速点击
2. **网络超时后客户端重试**：请求已处理但响应超时，客户端重试
3. **消息队列消费端重复消费**：消息队列至少一次投递保证
4. **分布式事务补偿**：事务回滚后重新执行
5. **定时任务重复执行**：任务调度系统故障导致重复触发

### 2.3 常见实现方式

#### 方式一：数据库唯一索引

**适用场景**：创建操作，防止重复创建

**实现方式**：
```sql
-- 订单表添加唯一索引
CREATE UNIQUE INDEX uk_order_no ON t_order_core_info (order_no);

-- 支付流水表添加唯一索引
CREATE UNIQUE INDEX uk_payment_trade_no ON t_payment_biz_record (trade_no);
```

**优点**：
- 实现简单，数据库层面保证
- 性能好，利用数据库索引

**缺点**：
- 只能防止完全相同的数据重复
- 违反唯一约束会抛出异常，需要捕获处理

#### 方式二：Redis 分布式锁

**适用场景**：防止并发操作，如库存扣减、余额扣减

**实现方式**：
```java
public void deductStock(Long productId, Integer quantity) {
    String lockKey = "lock:stock:" + productId;
    String lockValue = UUID.randomUUID().toString();

    try {
        // 获取锁，超时时间 10 秒
        Boolean locked = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, lockValue, 10, TimeUnit.SECONDS);

        if (!locked) {
            throw new BizException("操作频繁，请稍后重试");
        }

        // 执行业务逻辑
        Product product = productMapper.selectById(productId);
        if (product.getStock() < quantity) {
            throw new BizException("库存不足");
        }

        product.setStock(product.getStock() - quantity);
        productMapper.updateById(product);

    } finally {
        // 释放锁（Lua 脚本保证原子性）
        String script = "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                       "return redis.call('del', KEYS[1]) else return 0 end";
        redisTemplate.execute(new DefaultRedisScript<>(script, Long.class),
            Collections.singletonList(lockKey), lockValue);
    }
}
```

**优点**：
- 防止并发操作
- 适用于分布式环境

**缺点**：
- 需要引入 Redis
- 锁超时时间难以设置

#### 方式三：前端令牌（Token）机制

**适用场景**：表单提交，防止重复提交

**实现方式**：

1. 前端请求获取令牌：
```java
@GetMapping("/token")
public Result<String> getToken() {
    String token = UUID.randomUUID().toString();
    redisTemplate.opsForValue().set("token:" + token, "1", 5, TimeUnit.MINUTES);
    return Result.success(token);
}
```

2. 提交时验证并删除令牌：
```java
@PostMapping("/submit")
public Result<Void> submit(@RequestHeader("X-Token") String token,
                          @RequestBody SubmitReq req) {
    // 验证并删除令牌（Lua 脚本保证原子性）
    String script = "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                   "return redis.call('del', KEYS[1]) else return 0 end";
    Long result = redisTemplate.execute(
        new DefaultRedisScript<>(script, Long.class),
        Collections.singletonList("token:" + token), "1");

    if (result == 0) {
        throw new BizException("请勿重复提交");
    }

    // 执行业务逻辑
    // ...

    return Result.success();
}
```

**优点**：
- 防止前端重复提交
- 用户体验好

**缺点**：
- 需要前端配合
- 令牌过期时间难以设置

#### 方式四：状态机 + 版本号

**适用场景**：状态流转操作，如订单状态变更

**实现方式**：
```java
@Transactional
public void cancelOrder(Long orderId, Integer version) {
    // 使用乐观锁更新
    int rows = orderMapper.updateStatus(orderId,
        OrderStatus.PENDING, OrderStatus.CANCELLED, version);

    if (rows == 0) {
        throw new BizException("订单状态已变更，请刷新后重试");
    }

    // 执行后续操作（退款、恢复库存等）
    // ...
}
```

```xml
<!-- MyBatis Mapper -->
<update id="updateStatus">
    UPDATE t_order_core_info
    SET status = #{newStatus},
        version = version + 1,
        update_time = NOW()
    WHERE id = #{orderId}
      AND status = #{oldStatus}
      AND version = #{version}
</update>
```

**优点**：
- 防止并发修改
- 状态流转清晰

**缺点**：
- 需要前端传递版本号
- 并发冲突时需要重试

#### 方式五：请求 ID 去重

**适用场景**：消息队列消费端，防止重复消费

**实现方式**：
```java
@RocketMQMessageListener(topic = "order_created", consumerGroup = "inventory_service")
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

        // 执行业务逻辑
        inventoryService.deductStock(event.getOrderId());
    }
}
```

**优点**：
- 防止消息重复消费
- 实现简单

**缺点**：
- 需要生成全局唯一的请求 ID
- 需要存储已消费的请求 ID

## 3. 示例

### 正确示例

**创建订单（数据库唯一索引）：**
```java
@Transactional
public OrderResp createOrder(CreateOrderReq req) {
    // 生成订单号（全局唯一）
    String orderNo = generateOrderNo();

    Order order = new Order();
    order.setOrderNo(orderNo);
    order.setUserId(req.getUserId());
    order.setAmount(req.getAmount());

    try {
        orderMapper.insert(order);
    } catch (DuplicateKeyException e) {
        // 订单号重复，返回已存在的订单
        Order existOrder = orderMapper.selectByOrderNo(orderNo);
        return OrderConverter.toResp(existOrder);
    }

    return OrderConverter.toResp(order);
}
```

**扣减库存（Redis 分布式锁）：**
```java
public void deductStock(Long productId, Integer quantity) {
    String lockKey = "lock:stock:" + productId;
    RLock lock = redissonClient.getLock(lockKey);

    try {
        // 尝试获取锁，等待 3 秒，锁超时 10 秒
        boolean locked = lock.tryLock(3, 10, TimeUnit.SECONDS);
        if (!locked) {
            throw new BizException("操作频繁，请稍后重试");
        }

        // 执行业务逻辑
        Product product = productMapper.selectById(productId);
        if (product.getStock() < quantity) {
            throw new BizException("库存不足");
        }

        product.setStock(product.getStock() - quantity);
        productMapper.updateById(product);

    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        throw new BizException("操作被中断");
    } finally {
        if (lock.isHeldByCurrentThread()) {
            lock.unlock();
        }
    }
}
```

### 错误示例

```java
// ❌ 没有幂等性保障
@Transactional
public OrderResp createOrder(CreateOrderReq req) {
    Order order = new Order();
    order.setUserId(req.getUserId());
    order.setAmount(req.getAmount());

    // 直接插入，没有防重机制
    orderMapper.insert(order);

    return OrderConverter.toResp(order);
}

// ❌ 使用 synchronized 在分布式环境下无效
public synchronized void deductStock(Long productId, Integer quantity) {
    // synchronized 只能保证单机并发安全
    Product product = productMapper.selectById(productId);
    product.setStock(product.getStock() - quantity);
    productMapper.updateById(product);
}

// ❌ 没有检查消息是否已消费
@RocketMQMessageListener(topic = "order_created", consumerGroup = "inventory_service")
public class OrderCreatedListener implements RocketMQListener<OrderCreatedEvent> {

    @Override
    public void onMessage(OrderCreatedEvent event) {
        // 直接处理，没有去重
        inventoryService.deductStock(event.getOrderId());
    }
}
```

## 4. 检查清单

- [ ] 所有写操作（创建、更新、删除）都考虑了幂等性
- [ ] 创建操作使用数据库唯一索引或请求 ID 去重
- [ ] 并发操作使用分布式锁或乐观锁
- [ ] 表单提交使用令牌机制防止重复提交
- [ ] 状态流转使用状态机 + 版本号
- [ ] 消息队列消费端使用请求 ID 去重
- [ ] 幂等实现方式在接口文档中明确说明
- [ ] 测试用例覆盖重复提交场景

---

**版本：** 1.0
**最后更新：** 2026-03-23
