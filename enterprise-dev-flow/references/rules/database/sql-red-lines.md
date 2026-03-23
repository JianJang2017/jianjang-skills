# SQL 红线规范

> 定义SQL编写的强制性规则，违反将导致代码审查不通过

## 适用范围

本规范适用于：
- 研发人员编写SQL语句
- DBA进行SQL审查
- 测试工程师进行SQL注入测试

## 1. 禁止 SELECT *

### 1.1 规则说明

**强制要求：** 严禁使用 `SELECT *`，必须明确列出需要查询的字段

### 1.2 原因

- 避免查询不必要的字段，浪费网络带宽和内存
- 防止表结构变更导致的问题（新增字段、字段顺序变化）
- 提高查询性能，减少数据传输量
- 便于代码维护，明确知道使用了哪些字段

### 1.3 示例

**错误示例：**
```sql
-- ❌ 禁止使用 SELECT *
SELECT * FROM t_order_core_info WHERE id = 123;

-- ❌ 禁止使用 SELECT *
SELECT * FROM t_user_info_profile WHERE user_id = 10001;
```

**正确示例：**
```sql
-- ✅ 明确列出需要的字段
SELECT id, order_no, user_id, amount, status, create_time
FROM t_order_core_info
WHERE id = 123;

-- ✅ 只查询需要的字段
SELECT id, username, nickname, phone
FROM t_user_info_profile
WHERE user_id = 10001;
```

### 1.4 MyBatis 示例

**错误示例：**
```xml
<!-- ❌ 禁止使用 SELECT * -->
<select id="getOrderById" resultType="Order">
    SELECT * FROM t_order_core_info WHERE id = #{orderId}
</select>
```

**正确示例：**
```xml
<!-- ✅ 明确列出字段 -->
<select id="getOrderById" resultType="Order">
    SELECT id, order_no, user_id, amount, status, create_time
    FROM t_order_core_info
    WHERE id = #{orderId}
</select>
```

## 2. SQL 注入防护

### 2.1 规则说明

**强制要求：**
- 严禁 SQL 注入风险
- 必须使用预编译语句或 MyBatis `#{}` 占位符
- 禁止使用字符串拼接构建 SQL

### 2.2 MyBatis 占位符

| 占位符 | 说明 | 是否安全 | 使用场景 |
|-------|------|---------|---------|
| `#{}` | 预编译占位符，参数会被转义 | ✅ 安全 | 所有参数值 |
| `${}` | 字符串替换，参数不会被转义 | ❌ 不安全 | 表名、列名（需严格校验） |

### 2.3 示例

**错误示例（存在SQL注入风险）：**
```xml
<!-- ❌ 危险！使用 ${} 存在SQL注入风险 -->
<select id="getUserById" resultType="User">
    SELECT id, username, nickname
    FROM t_user_info_profile
    WHERE id = ${userId}
</select>

<!-- ❌ 危险！字符串拼接存在SQL注入风险 -->
<select id="searchUser" resultType="User">
    SELECT id, username, nickname
    FROM t_user_info_profile
    WHERE username LIKE '%${keyword}%'
</select>
```

**正确示例：**
```xml
<!-- ✅ 安全：使用 #{} 预编译 -->
<select id="getUserById" resultType="User">
    SELECT id, username, nickname
    FROM t_user_info_profile
    WHERE id = #{userId}
</select>

<!-- ✅ 安全：使用 #{} 和 CONCAT -->
<select id="searchUser" resultType="User">
    SELECT id, username, nickname
    FROM t_user_info_profile
    WHERE username LIKE CONCAT('%', #{keyword}, '%')
</select>
```

### 2.4 Java 代码示例

**错误示例：**
```java
// ❌ 危险！字符串拼接存在SQL注入风险
String sql = "SELECT * FROM t_user_info_profile WHERE username = '" + username + "'";
jdbcTemplate.query(sql, new UserRowMapper());
```

**正确示例：**
```java
// ✅ 安全：使用预编译
String sql = "SELECT id, username, nickname FROM t_user_info_profile WHERE username = ?";
jdbcTemplate.query(sql, new UserRowMapper(), username);
```

### 2.5 动态表名/列名处理

**场景：** 当需要动态指定表名或列名时，必须使用白名单校验

**错误示例：**
```xml
<!-- ❌ 危险！动态表名未校验 -->
<select id="queryByTable" resultType="Map">
    SELECT * FROM ${tableName} WHERE id = #{id}
</select>
```

**正确示例：**
```java
// ✅ 安全：白名单校验
public List<Map<String, Object>> queryByTable(String tableName, Long id) {
    // 白名单校验
    List<String> allowedTables = Arrays.asList(
        "t_order_core_info",
        "t_user_info_profile",
        "t_product_info_detail"
    );

    if (!allowedTables.contains(tableName)) {
        throw new IllegalArgumentException("非法的表名: " + tableName);
    }

    String sql = "SELECT id, name, status FROM " + tableName + " WHERE id = ?";
    return jdbcTemplate.queryForList(sql, id);
}
```

## 3. 禁止在 WHERE 子句中使用函数

### 3.1 规则说明

**强制要求：** 禁止在 WHERE 子句中对索引字段使用函数，会导致索引失效

### 3.2 示例

**错误示例：**
```sql
-- ❌ 索引失效：对索引字段使用函数
SELECT id, order_no, amount
FROM t_order_core_info
WHERE DATE(create_time) = '2026-03-23';

-- ❌ 索引失效：对索引字段使用函数
SELECT id, username
FROM t_user_info_profile
WHERE UPPER(username) = 'ADMIN';
```

**正确示例：**
```sql
-- ✅ 索引生效：使用范围查询
SELECT id, order_no, amount
FROM t_order_core_info
WHERE create_time >= '2026-03-23 00:00:00'
  AND create_time < '2026-03-24 00:00:00';

-- ✅ 索引生效：直接比较
SELECT id, username
FROM t_user_info_profile
WHERE username = 'admin';
```

## 4. 禁止使用 NOT、!=、<>

### 4.1 规则说明

**强制要求：** 避免使用 NOT、!=、<>，会导致索引失效

### 4.2 示例

**错误示例：**
```sql
-- ❌ 索引失效：使用 !=
SELECT id, order_no, status
FROM t_order_core_info
WHERE status != 'CANCELLED';

-- ❌ 索引失效：使用 NOT IN
SELECT id, username
FROM t_user_info_profile
WHERE user_id NOT IN (1, 2, 3);
```

**正确示例：**
```sql
-- ✅ 索引生效：使用 IN 列举正常状态
SELECT id, order_no, status
FROM t_order_core_info
WHERE status IN ('PENDING', 'PAID', 'SHIPPED', 'COMPLETED');

-- ✅ 索引生效：使用 NOT EXISTS
SELECT id, username
FROM t_user_info_profile u
WHERE NOT EXISTS (
    SELECT 1 FROM t_user_blacklist b WHERE b.user_id = u.id
);
```

## 5. 禁止使用 OR 条件

### 5.1 规则说明

**建议：** 避免使用 OR 条件，除非所有字段都有索引，否则会导致索引失效

### 5.2 示例

**错误示例：**
```sql
-- ❌ 索引失效：OR 条件中的字段没有都建立索引
SELECT id, order_no, user_id
FROM t_order_core_info
WHERE user_id = 10001 OR phone = '13812345678';
```

**正确示例：**
```sql
-- ✅ 使用 UNION 替代 OR
SELECT id, order_no, user_id
FROM t_order_core_info
WHERE user_id = 10001

UNION

SELECT id, order_no, user_id
FROM t_order_core_info
WHERE phone = '13812345678';
```

## 6. 禁止深分页

### 6.1 规则说明

**强制要求：** 禁止深分页（pageNum > 1000），改用游标分页

### 6.2 原因

- 深分页会导致性能问题（需要扫描大量数据）
- 数据库需要跳过大量行，消耗大量资源

### 6.3 示例

**错误示例：**
```sql
-- ❌ 深分页：性能差
SELECT id, order_no, amount
FROM t_order_core_info
WHERE enabled = 1
ORDER BY create_time DESC
LIMIT 10000, 10;  -- 跳过10000行
```

**正确示例（游标分页）：**
```sql
-- ✅ 游标分页：性能好
SELECT id, order_no, amount
FROM t_order_core_info
WHERE enabled = 1
  AND id < #{lastId}  -- 使用上一页的最后一条记录ID
ORDER BY id DESC
LIMIT 10;
```

## 7. 禁止大批量操作

### 7.1 规则说明

**强制要求：**
- 批量插入/更新/删除必须分批执行，每批不超过 1000 条
- 避免长事务，事务执行时间不超过 3 秒

### 7.2 示例

**错误示例：**
```java
// ❌ 一次性插入10000条数据，可能导致锁表
List<Order> orders = getOrders();  // 10000条
orderMapper.batchInsert(orders);
```

**正确示例：**
```java
// ✅ 分批插入，每批1000条
List<Order> orders = getOrders();  // 10000条
int batchSize = 1000;

for (int i = 0; i < orders.size(); i += batchSize) {
    int end = Math.min(i + batchSize, orders.size());
    List<Order> batch = orders.subList(i, end);
    orderMapper.batchInsert(batch);
}
```

## 8. 禁止在事务中执行耗时操作

### 8.1 规则说明

**强制要求：** 事务内禁止执行以下操作：
- RPC 调用（远程服务调用）
- 文件 IO 操作
- 复杂计算
- 发送消息队列（应在事务提交后执行）

### 8.2 原因

- 事务时间过长会导致锁等待
- 影响数据库并发性能
- 增加死锁风险

### 8.3 示例

**错误示例：**
```java
// ❌ 事务中执行RPC调用
@Transactional
public void createOrder(CreateOrderRequest request) {
    // 1. 创建订单
    Order order = buildOrder(request);
    orderRepository.save(order);

    // 2. RPC调用库存服务（耗时操作）
    inventoryService.deductStock(request.getProductId(), request.getQuantity());

    // 3. RPC调用支付服务（耗时操作）
    paymentService.createPayment(order.getId(), order.getAmount());
}
```

**正确示例：**
```java
// ✅ 事务外执行RPC调用
public void createOrder(CreateOrderRequest request) {
    // 1. 事务内：创建订单
    Order order = createOrderInTransaction(request);

    // 2. 事务外：RPC调用库存服务
    try {
        inventoryService.deductStock(request.getProductId(), request.getQuantity());
    } catch (Exception e) {
        // 补偿：取消订单
        cancelOrder(order.getId());
        throw e;
    }

    // 3. 事务外：RPC调用支付服务
    paymentService.createPayment(order.getId(), order.getAmount());
}

@Transactional
private Order createOrderInTransaction(CreateOrderRequest request) {
    Order order = buildOrder(request);
    return orderRepository.save(order);
}
```

## 9. SQL 红线检查清单

在代码提交前，必须逐项检查：

- [ ] 禁止使用 `SELECT *`，明确列出字段
- [ ] 使用 `#{}` 预编译，避免 SQL 注入
- [ ] 动态表名/列名使用白名单校验
- [ ] WHERE 子句中避免对索引字段使用函数
- [ ] 避免使用 NOT、!=、<>
- [ ] 避免使用 OR 条件（改用 UNION）
- [ ] 禁止深分页（pageNum > 1000）
- [ ] 批量操作分批执行（每批≤1000条）
- [ ] 事务内禁止 RPC 调用和耗时操作
- [ ] 事务执行时间不超过 3 秒

## 10. 违规处理

违反 SQL 红线的代码：
- **P0级缺陷**：必须立即修复，阻断上线
- **代码审查不通过**：必须修改后重新提交
- **性能问题**：可能导致生产环境故障

---

**文档版本**: 1.0
**创建日期**: 2026-03-23
**适用项目**: 所有企业级项目
