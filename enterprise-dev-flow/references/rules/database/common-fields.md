# 数据库通用字段规范

> 定义所有数据库表必须包含的通用字段

## 适用范围

本规范适用于：
- 所有业务表（除系统表、临时表外）
- 产品经理定义数据实体时需要考虑
- 研发人员设计表结构时必须遵守

## 1. 通用字段清单

每张业务表必须包含以下6个通用字段，顺序固定，放在业务字段之后：

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|------|-------|------|
| `enabled` | TINYINT(1) | NOT NULL | 1 | 是否有效：0-无效，1-有效 |
| `create_by` | VARCHAR(64) | NOT NULL | - | 创建人 |
| `create_time` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| `update_by` | VARCHAR(64) | NOT NULL | - | 更新人 |
| `update_time` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 更新时间（自动更新） |
| `remark` | VARCHAR(500) | NULL | NULL | 备注 |

## 2. 字段详细说明

### 2.1 enabled（是否有效）

**用途：** 逻辑删除标记，避免物理删除数据

**取值：**
- `0` - 无效（已删除）
- `1` - 有效（正常）

**使用场景：**
- 用户删除数据时，不物理删除，而是将 `enabled` 设置为 0
- 查询时默认只查询 `enabled = 1` 的数据
- 需要查询已删除数据时，可以查询 `enabled = 0` 的数据

**示例：**
```sql
-- 逻辑删除
UPDATE t_order_core_info SET enabled = 0, update_by = 'admin', update_time = NOW() WHERE id = 123;

-- 查询有效数据
SELECT * FROM t_order_core_info WHERE enabled = 1;

-- 查询已删除数据
SELECT * FROM t_order_core_info WHERE enabled = 0;
```

### 2.2 create_by（创建人）

**用途：** 记录数据的创建者

**取值：**
- 用户ID（推荐）
- 用户名
- 系统标识（如 "system"、"job"）

**使用场景：**
- 审计追踪：谁创建了这条数据
- 数据权限：只能查看自己创建的数据
- 问题排查：定位数据来源

**示例：**
```sql
-- 用户创建订单
INSERT INTO t_order_core_info (id, user_id, amount, enabled, create_by, create_time, update_by, update_time)
VALUES (123, 10001, 99.99, 1, '10001', NOW(), '10001', NOW());

-- 系统定时任务创建数据
INSERT INTO t_order_stat_summary (id, date, total_amount, enabled, create_by, create_time, update_by, update_time)
VALUES (456, '2026-03-23', 10000.00, 1, 'system', NOW(), 'system', NOW());
```

### 2.3 create_time（创建时间）

**用途：** 记录数据的创建时间

**类型：** TIMESTAMP

**默认值：** CURRENT_TIMESTAMP（数据库自动填充）

**使用场景：**
- 数据排序：按创建时间排序
- 数据统计：按时间范围统计
- 审计追踪：数据创建时间点

**示例：**
```sql
-- 查询最近7天创建的订单
SELECT * FROM t_order_core_info
WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND enabled = 1;

-- 按创建时间倒序排列
SELECT * FROM t_order_core_info
WHERE enabled = 1
ORDER BY create_time DESC;
```

### 2.4 update_by（更新人）

**用途：** 记录数据的最后更新者

**取值：**
- 用户ID（推荐）
- 用户名
- 系统标识（如 "system"、"job"）

**使用场景：**
- 审计追踪：谁最后修改了这条数据
- 问题排查：定位数据变更来源
- 并发控制：结合版本号实现乐观锁

**示例：**
```sql
-- 用户更新订单
UPDATE t_order_core_info
SET status = 'PAID', update_by = '10001', update_time = NOW()
WHERE id = 123;

-- 系统定时任务更新数据
UPDATE t_order_stat_summary
SET total_amount = 10000.00, update_by = 'system', update_time = NOW()
WHERE date = '2026-03-23';
```

### 2.5 update_time（更新时间）

**用途：** 记录数据的最后更新时间

**类型：** TIMESTAMP

**默认值：** CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP（数据库自动更新）

**使用场景：**
- 数据同步：增量同步时根据更新时间判断
- 缓存失效：根据更新时间判断缓存是否过期
- 审计追踪：数据最后修改时间点

**示例：**
```sql
-- 查询最近1小时更新的订单
SELECT * FROM t_order_core_info
WHERE update_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
  AND enabled = 1;

-- 增量同步：同步最近更新的数据
SELECT * FROM t_order_core_info
WHERE update_time > '2026-03-23 10:00:00'
  AND enabled = 1;
```

### 2.6 remark（备注）

**用途：** 记录额外的备注信息

**类型：** VARCHAR(500)

**约束：** NULL（可选字段）

**使用场景：**
- 记录特殊说明
- 记录操作原因
- 记录异常情况

**示例：**
```sql
-- 订单取消时记录原因
UPDATE t_order_core_info
SET status = 'CANCELLED', remark = '用户申请取消，库存不足', update_by = '10001', update_time = NOW()
WHERE id = 123;

-- 手动调整数据时记录原因
UPDATE t_inventory_core_stock
SET stock = 100, remark = '盘点调整，实际库存100件', update_by = 'admin', update_time = NOW()
WHERE product_id = 456;
```

## 3. 建表DDL模板

```sql
CREATE TABLE t_{biz}_{scope}_{model_name} (
    -- 主键
    id          BIGINT          NOT NULL COMMENT '主键（雪花算法）',

    -- 业务字段
    [字段名]    [类型]          [NOT NULL/NULL] COMMENT '[说明]',

    -- 通用字段（必须包含，顺序固定）
    enabled     TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否有效：0-无效，1-有效',
    create_by   VARCHAR(64)     NOT NULL COMMENT '创建人',
    create_time TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_by   VARCHAR(64)     NOT NULL COMMENT '更新人',
    update_time TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    remark      VARCHAR(500)    NULL COMMENT '备注',

    -- 主键约束
    PRIMARY KEY (id)
) COMMENT = '[表说明]';
```

## 4. 完整示例

### 4.1 订单表示例

```sql
CREATE TABLE t_order_core_info (
    -- 主键
    id              BIGINT          NOT NULL COMMENT '订单ID（雪花算法）',

    -- 业务字段
    order_no        VARCHAR(32)     NOT NULL COMMENT '订单编号',
    user_id         BIGINT          NOT NULL COMMENT '用户ID',
    amount          DECIMAL(18,2)   NOT NULL COMMENT '订单金额',
    status          VARCHAR(20)     NOT NULL COMMENT '订单状态',

    -- 通用字段
    enabled         TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否有效：0-无效，1-有效',
    create_by       VARCHAR(64)     NOT NULL COMMENT '创建人',
    create_time     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_by       VARCHAR(64)     NOT NULL COMMENT '更新人',
    update_time     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    remark          VARCHAR(500)    NULL COMMENT '备注',

    -- 主键约束
    PRIMARY KEY (id),

    -- 索引
    UNIQUE KEY uk_order_no (order_no),
    KEY idx_user_id (user_id),
    KEY idx_status_time (status, create_time)
) COMMENT = '订单核心信息表';
```

### 4.2 用户表示例

```sql
CREATE TABLE t_user_info_profile (
    -- 主键
    id              BIGINT          NOT NULL COMMENT '用户ID（雪花算法）',

    -- 业务字段
    username        VARCHAR(32)     NOT NULL COMMENT '用户名',
    nickname        VARCHAR(64)     NOT NULL COMMENT '昵称',
    phone           VARCHAR(11)     NOT NULL COMMENT '手机号',
    email           VARCHAR(64)     NULL COMMENT '邮箱',

    -- 通用字段
    enabled         TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否有效：0-无效，1-有效',
    create_by       VARCHAR(64)     NOT NULL COMMENT '创建人',
    create_time     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_by       VARCHAR(64)     NOT NULL COMMENT '更新人',
    update_time     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    remark          VARCHAR(500)    NULL COMMENT '备注',

    -- 主键约束
    PRIMARY KEY (id),

    -- 索引
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_phone (phone),
    KEY idx_create_time (create_time)
) COMMENT = '用户信息档案表';
```

## 5. 通用字段使用规范

### 5.1 插入数据时

```java
// 正确示例：填充通用字段
Order order = new Order();
order.setId(snowflakeId);
order.setOrderNo(orderNo);
order.setUserId(userId);
order.setAmount(amount);
order.setStatus("PENDING");
order.setEnabled(1);
order.setCreateBy(String.valueOf(userId));
order.setCreateTime(new Date());
order.setUpdateBy(String.valueOf(userId));
order.setUpdateTime(new Date());
orderRepository.save(order);
```

### 5.2 更新数据时

```java
// 正确示例：更新通用字段
Order order = orderRepository.findById(orderId);
order.setStatus("PAID");
order.setUpdateBy(String.valueOf(userId));
order.setUpdateTime(new Date());
orderRepository.update(order);
```

### 5.3 逻辑删除时

```java
// 正确示例：逻辑删除
Order order = orderRepository.findById(orderId);
order.setEnabled(0);
order.setUpdateBy(String.valueOf(userId));
order.setUpdateTime(new Date());
order.setRemark("用户申请删除");
orderRepository.update(order);
```

### 5.4 查询数据时

```java
// 正确示例：只查询有效数据
List<Order> orders = orderRepository.findByUserIdAndEnabled(userId, 1);

// MyBatis示例
<select id="findByUserId" resultType="Order">
    SELECT * FROM t_order_core_info
    WHERE user_id = #{userId}
      AND enabled = 1
    ORDER BY create_time DESC
</select>
```

## 6. 通用字段检查清单

在创建表之前，必须逐项检查：

- [ ] 包含 `enabled` 字段（TINYINT(1)，默认1）
- [ ] 包含 `create_by` 字段（VARCHAR(64)，NOT NULL）
- [ ] 包含 `create_time` 字段（TIMESTAMP，默认CURRENT_TIMESTAMP）
- [ ] 包含 `update_by` 字段（VARCHAR(64)，NOT NULL）
- [ ] 包含 `update_time` 字段（TIMESTAMP，自动更新）
- [ ] 包含 `remark` 字段（VARCHAR(500)，NULL）
- [ ] 通用字段顺序正确（放在业务字段之后）
- [ ] 所有字段都有COMMENT注释

---

**文档版本**: 1.0
**创建日期**: 2026-03-23
**适用项目**: 所有企业级项目
