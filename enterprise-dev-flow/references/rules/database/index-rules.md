# 数据库索引规范

> 定义数据库索引的设计和使用规则

## 适用范围

本规范适用于：
- 研发人员设计数据库表结构
- DBA进行数据库优化
- 产品经理理解性能优化需求

## 1. 索引设计原则

### 1.1 索引数量控制

**强制要求：**
- 单表索引数量控制在 **5 个以内**（不含主键）
- 过多索引会影响写入性能和存储空间

### 1.2 必须建立索引的场景

**关键业务属性必须建立索引：**
- 高频查询条件字段（如 user_id、order_no）
- 常用组合查询字段（如 status + create_time）
- 外键字段
- 唯一约束字段

### 1.3 禁止建立索引的场景

- 区分度低的字段单独建索引（如性别、状态）
- 更新频繁的字段
- 大字段（TEXT、BLOB）
- 查询频率极低的字段

## 2. 索引类型

### 2.1 主键索引（PRIMARY KEY）

**说明：** 每张表必须有主键，主键自动创建聚簇索引

**示例：**
```sql
CREATE TABLE t_order_core_info (
    id BIGINT NOT NULL COMMENT '订单ID（雪花算法）',
    -- 其他字段...
    PRIMARY KEY (id)
) COMMENT = '订单核心信息表';
```

### 2.2 唯一索引（UNIQUE KEY）

**说明：** 用于保证字段值的唯一性，如订单编号、用户名

**命名规则：** `uk_{表名缩写}_{字段名}`

**示例：**
```sql
-- 订单编号唯一索引
CREATE UNIQUE INDEX uk_order_no ON t_order_core_info (order_no);

-- 用户名唯一索引
CREATE UNIQUE INDEX uk_username ON t_user_info_profile (username);

-- 组合唯一索引
CREATE UNIQUE INDEX uk_user_product ON t_user_relation_favorite (user_id, product_id);
```

### 2.3 普通索引（INDEX）

**说明：** 用于加速查询，最常用的索引类型

**命名规则：** `idx_{表名缩写}_{字段名}`

**示例：**
```sql
-- 单字段索引
CREATE INDEX idx_order_user_id ON t_order_core_info (user_id);

-- 组合索引
CREATE INDEX idx_order_status_time ON t_order_core_info (status, create_time);
```

## 3. 索引命名规范

### 3.1 命名规则

| 索引类型 | 命名规则 | 示例 |
|---------|---------|------|
| 主键索引 | PRIMARY KEY | PRIMARY KEY (id) |
| 唯一索引 | uk_{表名缩写}_{字段名} | uk_order_no |
| 普通索引 | idx_{表名缩写}_{字段名} | idx_order_user_id |
| 组合索引 | idx_{表名缩写}_{字段1}_{字段2} | idx_order_status_time |

### 3.2 表名缩写规则

| 表名 | 缩写 |
|------|------|
| t_order_core_info | order |
| t_user_info_profile | user |
| t_payment_biz_record | payment |
| t_product_info_detail | product |

## 4. 组合索引设计

### 4.1 最左前缀原则

**说明：** 组合索引遵循最左前缀原则，查询条件必须包含索引的最左字段

**示例：**
```sql
-- 创建组合索引
CREATE INDEX idx_order_status_time ON t_order_core_info (status, create_time);

-- 可以使用索引的查询
SELECT * FROM t_order_core_info WHERE status = 'PAID';  -- ✅ 使用索引
SELECT * FROM t_order_core_info WHERE status = 'PAID' AND create_time > '2026-03-01';  -- ✅ 使用索引

-- 不能使用索引的查询
SELECT * FROM t_order_core_info WHERE create_time > '2026-03-01';  -- ❌ 不使用索引（缺少最左字段status）
```

### 4.2 字段顺序选择

**原则：**
1. 区分度高的字段放在前面
2. 等值查询字段放在前面，范围查询字段放在后面
3. 查询频率高的字段放在前面

**示例：**
```sql
-- 正确：status（等值）在前，create_time（范围）在后
CREATE INDEX idx_order_status_time ON t_order_core_info (status, create_time);

-- 错误：create_time（范围）在前，status（等值）在后
CREATE INDEX idx_order_time_status ON t_order_core_info (create_time, status);  -- ❌ 不推荐
```

### 4.3 组合索引示例

| 查询场景 | 组合索引 | 说明 |
|---------|---------|------|
| 按用户ID和状态查询订单 | idx_order_user_status (user_id, status) | user_id区分度高，放在前面 |
| 按状态和时间范围查询订单 | idx_order_status_time (status, create_time) | status等值查询，create_time范围查询 |
| 按商品ID和创建时间查询 | idx_product_time (product_id, create_time) | product_id等值查询在前 |

## 5. 索引使用规范

### 5.1 查询优化建议

**使用索引的查询：**
```sql
-- ✅ 使用索引：等值查询
SELECT * FROM t_order_core_info WHERE user_id = 10001;

-- ✅ 使用索引：范围查询
SELECT * FROM t_order_core_info WHERE create_time > '2026-03-01';

-- ✅ 使用索引：IN查询（数量不超过1000）
SELECT * FROM t_order_core_info WHERE status IN ('PAID', 'SHIPPED');

-- ✅ 使用索引：LIKE前缀匹配
SELECT * FROM t_order_core_info WHERE order_no LIKE 'ORD2026%';
```

**不使用索引的查询：**
```sql
-- ❌ 不使用索引：函数操作
SELECT * FROM t_order_core_info WHERE DATE(create_time) = '2026-03-23';

-- ❌ 不使用索引：LIKE后缀匹配
SELECT * FROM t_order_core_info WHERE order_no LIKE '%2026';

-- ❌ 不使用索引：NOT、!=、<>
SELECT * FROM t_order_core_info WHERE status != 'CANCELLED';

-- ❌ 不使用索引：OR条件（除非所有字段都有索引）
SELECT * FROM t_order_core_info WHERE user_id = 10001 OR phone = '13812345678';
```

### 5.2 避免索引失效

| 场景 | 错误示例 | 正确示例 |
|------|---------|---------|
| 函数操作 | `WHERE DATE(create_time) = '2026-03-23'` | `WHERE create_time >= '2026-03-23 00:00:00' AND create_time < '2026-03-24 00:00:00'` |
| 类型转换 | `WHERE user_id = '10001'`（user_id是BIGINT） | `WHERE user_id = 10001` |
| LIKE后缀 | `WHERE order_no LIKE '%2026'` | `WHERE order_no LIKE 'ORD2026%'` |
| OR条件 | `WHERE user_id = 10001 OR phone = '138'` | 拆分为两个查询或使用UNION |

## 6. 索引监控与优化

### 6.1 索引使用情况分析

**查看索引使用情况：**
```sql
-- MySQL
SHOW INDEX FROM t_order_core_info;

-- 查看索引统计信息
SELECT * FROM information_schema.STATISTICS
WHERE table_schema = 'your_database'
  AND table_name = 't_order_core_info';
```

### 6.2 慢查询分析

**开启慢查询日志：**
```sql
-- 设置慢查询阈值（2秒）
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
```

**分析慢查询：**
```sql
-- 使用EXPLAIN分析查询计划
EXPLAIN SELECT * FROM t_order_core_info WHERE user_id = 10001;
```

### 6.3 索引优化建议

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 查询慢 | 缺少索引 | 为高频查询字段建立索引 |
| 写入慢 | 索引过多 | 删除不必要的索引 |
| 索引未使用 | 查询条件不匹配 | 调整查询条件或索引字段 |
| 索引区分度低 | 字段值重复率高 | 使用组合索引提高区分度 |

## 7. 索引设计示例

### 7.1 订单表索引设计

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
    enabled         TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否有效',
    create_by       VARCHAR(64)     NOT NULL COMMENT '创建人',
    create_time     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_by       VARCHAR(64)     NOT NULL COMMENT '更新人',
    update_time     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    remark          VARCHAR(500)    NULL COMMENT '备注',

    -- 主键索引
    PRIMARY KEY (id),

    -- 唯一索引：订单编号
    UNIQUE KEY uk_order_no (order_no),

    -- 普通索引：用户ID（高频查询）
    KEY idx_order_user_id (user_id),

    -- 组合索引：状态+创建时间（按状态和时间范围查询）
    KEY idx_order_status_time (status, create_time),

    -- 组合索引：用户ID+状态（按用户查询特定状态订单）
    KEY idx_order_user_status (user_id, status)
) COMMENT = '订单核心信息表';
```

### 7.2 用户表索引设计

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
    enabled         TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否有效',
    create_by       VARCHAR(64)     NOT NULL COMMENT '创建人',
    create_time     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_by       VARCHAR(64)     NOT NULL COMMENT '更新人',
    update_time     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    remark          VARCHAR(500)    NULL COMMENT '备注',

    -- 主键索引
    PRIMARY KEY (id),

    -- 唯一索引：用户名
    UNIQUE KEY uk_username (username),

    -- 唯一索引：手机号
    UNIQUE KEY uk_phone (phone),

    -- 普通索引：创建时间（按注册时间查询）
    KEY idx_user_create_time (create_time)
) COMMENT = '用户信息档案表';
```

## 8. 索引检查清单

在创建索引之前，必须逐项检查：

- [ ] 索引数量不超过5个（不含主键）
- [ ] 高频查询字段已建立索引
- [ ] 唯一约束字段已建立唯一索引
- [ ] 组合索引字段顺序正确（区分度高的在前）
- [ ] 索引命名符合规范（uk_/idx_前缀）
- [ ] 避免为区分度低的字段单独建索引
- [ ] 索引字段类型合适（避免大字段）
- [ ] 使用EXPLAIN验证索引生效

---

**文档版本**: 1.0
**创建日期**: 2026-03-23
**适用项目**: 所有企业级项目
