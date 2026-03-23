# 缓存策略

> 适用范围：所有使用 Redis 缓存的场景，适用于架构师、研发人员

---

## 1. 规则说明

合理的缓存策略能够显著提高系统性能，减少数据库压力。本规范定义了 Redis 缓存的命名规范、异常处理、一致性策略和数据结构选择。

## 2. 规则内容

### 2.1 Key 命名格式

**格式：** `项目名:模块名:业务含义:唯一标识`

**示例：**
```
mall:order:info:123456
mall:user:session:10001
mall:product:stock:20001
```

**命名规则：**
- 使用冒号（:）分隔
- 使用小写字母
- 使用有意义的名称
- 包含唯一标识（ID）

### 2.2 过期时间设置

| 数据类型 | 过期时间 | 说明 |
|---------|---------|------|
| 热点数据 | 30 分钟 - 2 小时 | 如商品详情、用户信息 |
| Session 数据 | 2 小时 - 24 小时 | 如用户登录态 |
| 验证码 | 5 分钟 | 短信验证码、图形验证码 |
| 分布式锁 | 10 秒 - 30 秒 | 根据业务操作时间设置 |
| 临时数据 | 1 分钟 - 5 分钟 | 如防重复提交的 Token |

**过期时间设置原则：**
- 根据数据更新频率设置
- 避免设置过长的过期时间
- 添加随机因子，避免缓存雪崩

### 2.3 缓存异常处理

#### 缓存穿透

**定义：** 查询不存在的数据，导致每次请求都打到数据库

**解决方案：**
1. **布隆过滤器**：在缓存前加一层布隆过滤器，过滤不存在的数据
2. **缓存空值**：将不存在的数据也缓存起来，设置较短的过期时间

```java
public User getUser(Long userId) {
    // 1. 查询缓存
    String key = "mall:user:info:" + userId;
    String value = redisTemplate.opsForValue().get(key);

    if (value != null) {
        if ("NULL".equals(value)) {
            // 缓存的空值
            return null;
        }
        return JSON.parseObject(value, User.class);
    }

    // 2. 查询数据库
    User user = userMapper.selectById(userId);

    if (user == null) {
        // 缓存空值，过期时间 5 分钟
        redisTemplate.opsForValue().set(key, "NULL", 5, TimeUnit.MINUTES);
        return null;
    }

    // 3. 写入缓存
    redisTemplate.opsForValue().set(key, JSON.toJSONString(user), 30, TimeUnit.MINUTES);
    return user;
}
```

#### 缓存击穿

**定义：** 热点数据过期，大量请求同时打到数据库

**解决方案：**
1. **互斥锁**：只允许一个线程查询数据库，其他线程等待
2. **逻辑过期**：不设置过期时间，在数据中记录过期时间，异步更新

```java
public User getUser(Long userId) {
    String key = "mall:user:info:" + userId;
    String lockKey = "lock:user:" + userId;

    // 1. 查询缓存
    String value = redisTemplate.opsForValue().get(key);
    if (value != null) {
        return JSON.parseObject(value, User.class);
    }

    // 2. 获取锁
    Boolean locked = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS);

    if (!locked) {
        // 获取锁失败，等待 100ms 后重试
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return getUser(userId);
    }

    try {
        // 3. 双重检查
        value = redisTemplate.opsForValue().get(key);
        if (value != null) {
            return JSON.parseObject(value, User.class);
        }

        // 4. 查询数据库
        User user = userMapper.selectById(userId);

        // 5. 写入缓存
        if (user != null) {
            redisTemplate.opsForValue().set(key, JSON.toJSONString(user), 30, TimeUnit.MINUTES);
        }

        return user;
    } finally {
        // 6. 释放锁
        redisTemplate.delete(lockKey);
    }
}
```

#### 缓存雪崩

**定义：** 大量缓存同时过期，导致大量请求打到数据库

**解决方案：**
1. **过期时间随机因子**：在过期时间基础上加上随机值
2. **缓存预热**：系统启动时预先加载热点数据
3. **多级缓存**：本地缓存 + Redis 缓存

```java
public void setCache(String key, Object value, long timeout) {
    // 添加随机因子（0-300 秒）
    long randomTimeout = timeout + ThreadLocalRandom.current().nextInt(300);
    redisTemplate.opsForValue().set(key, JSON.toJSONString(value), randomTimeout, TimeUnit.SECONDS);
}
```

### 2.4 双写一致性策略

**策略一：先更新数据库，再删除缓存（推荐）**

```java
@Transactional
public void updateUser(User user) {
    // 1. 更新数据库
    userMapper.updateById(user);

    // 2. 删除缓存
    String key = "mall:user:info:" + user.getId();
    redisTemplate.delete(key);
}
```

**策略二：先删除缓存，再更新数据库**

```java
@Transactional
public void updateUser(User user) {
    String key = "mall:user:info:" + user.getId();

    // 1. 删除缓存
    redisTemplate.delete(key);

    // 2. 更新数据库
    userMapper.updateById(user);

    // 3. 延迟双删（可选）
    CompletableFuture.runAsync(() -> {
        try {
            Thread.sleep(500);
            redisTemplate.delete(key);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    });
}
```

**策略三：使用 Canal 监听 binlog（最终一致性）**

```java
// Canal 监听 MySQL binlog，异步更新缓存
@CanalEventListener
public class UserCanalListener {

    @ListenPoint(schema = "mall", table = "t_user")
    public void onUserChange(CanalEntry.EventType eventType, CanalEntry.RowData rowData) {
        if (eventType == CanalEntry.EventType.UPDATE || eventType == CanalEntry.EventType.DELETE) {
            String userId = rowData.getAfterColumnsList().stream()
                .filter(column -> "id".equals(column.getName()))
                .findFirst()
                .map(CanalEntry.Column::getValue)
                .orElse(null);

            if (userId != null) {
                String key = "mall:user:info:" + userId;
                redisTemplate.delete(key);
            }
        }
    }
}
```

### 2.5 数据结构选择

| 数据结构 | 使用场景 | 示例 |
|---------|---------|------|
| String | 简单的 key-value | 用户信息、商品详情 |
| Hash | 对象存储，部分字段更新 | 用户 Session、购物车 |
| List | 列表、队列 | 消息队列、最新动态 |
| Set | 去重、交集、并集 | 标签、关注列表 |
| ZSet | 排行榜、延迟队列 | 热门商品、定时任务 |

**示例：**

```java
// String：用户信息
redisTemplate.opsForValue().set("mall:user:info:10001", JSON.toJSONString(user));

// Hash：用户 Session
redisTemplate.opsForHash().put("mall:user:session:10001", "userId", "10001");
redisTemplate.opsForHash().put("mall:user:session:10001", "nickname", "张三");

// List：最新动态
redisTemplate.opsForList().leftPush("mall:user:feeds:10001", JSON.toJSONString(feed));

// Set：关注列表
redisTemplate.opsForSet().add("mall:user:following:10001", "20001", "20002");

// ZSet：热门商品
redisTemplate.opsForZSet().add("mall:product:hot", "30001", 100.0);
```

## 3. 示例

### 正确示例

**缓存设计文档：**

```markdown
### 缓存设计

| Key | 数据结构 | 内容 | 过期时间 | 缓存策略 |
|-----|---------|------|---------|---------|
| mall:order:info:{orderId} | String(JSON) | 订单详情 | 30分钟 | 查询时回填，更新时先删缓存 |
| mall:user:session:{userId} | Hash | 用户Session信息 | 2小时 | 滑动过期 |
| mall:product:stock:{productId} | String | 商品库存 | 10分钟 | 更新时先删缓存 |
| mall:product:hot | ZSet | 热门商品排行 | 1小时 | 定时任务更新 |

**缓存异常处理：**
- 缓存穿透：缓存空值，过期时间 5 分钟
- 缓存击穿：互斥锁，锁超时时间 10 秒
- 缓存雪崩：过期时间随机因子 0-300 秒
```

### 错误示例

```java
// ❌ Key 命名不规范
redisTemplate.opsForValue().set("user_10001", JSON.toJSONString(user));

// ❌ 没有设置过期时间
redisTemplate.opsForValue().set("mall:user:info:10001", JSON.toJSONString(user));

// ❌ 没有处理缓存穿透
public User getUser(Long userId) {
    String key = "mall:user:info:" + userId;
    String value = redisTemplate.opsForValue().get(key);
    if (value != null) {
        return JSON.parseObject(value, User.class);
    }

    // 直接查询数据库，没有缓存空值
    User user = userMapper.selectById(userId);
    if (user != null) {
        redisTemplate.opsForValue().set(key, JSON.toJSONString(user), 30, TimeUnit.MINUTES);
    }
    return user;
}

// ❌ 先更新缓存，再更新数据库（错误的顺序）
public void updateUser(User user) {
    String key = "mall:user:info:" + user.getId();
    redisTemplate.opsForValue().set(key, JSON.toJSONString(user), 30, TimeUnit.MINUTES);
    userMapper.updateById(user);
}
```

## 4. 检查清单

- [ ] Key 命名符合规范（项目名:模块名:业务含义:唯一标识）
- [ ] 设置了合理的过期时间
- [ ] 添加了过期时间随机因子
- [ ] 处理了缓存穿透（布隆过滤器或缓存空值）
- [ ] 处理了缓存击穿（互斥锁或逻辑过期）
- [ ] 处理了缓存雪崩（随机因子或多级缓存）
- [ ] 选择了合适的数据结构
- [ ] 双写一致性策略明确（先更新数据库，再删除缓存）
- [ ] 缓存设计在文档中明确说明

---

**版本：** 1.0
**最后更新：** 2026-03-23
