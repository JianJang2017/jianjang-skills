# 研发详细设计文档模板

> 引用自《研发详细设计文档规范（Spring Cloud Alibaba 技术栈）》
> 使用时请结合 `common-rules.md` 中的通用规则

---

# [功能/模块名称] 详细设计文档

| 文档元数据 | 内容 |
| :--- | :--- |
| **关联PRD** | [PRD文档链接/版本] |
| **服务名称** | [微服务名，如 order-service] |
| **技术栈** | Spring Cloud Alibaba + PostgreSQL + Redis + RocketMQ + MinIO |
| **负责研发** | [姓名] |
| **文档版本** | V1.0 |
| **最后更新** | [日期] |
| **评审状态** | 草稿 → 评审中 → 已确认 |

---

## 1. 需求分析

### 1.1 核心流程梳理
> 简述PRD的核心业务流程，识别关键技术难点。

- **主流程**：[用自己的语言描述核心链路]
- **关键难点**：
  - [难点1]：[分析及应对思路]
  - [难点2]：[分析及应对思路]

### 1.2 技术风险评估

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|---------|
| [风险1] | 高/中/低 | 高/中/低 | [方案] |
| [风险2] | 高/中/低 | 高/中/低 | [方案] |

---

## 2. 架构图

### 2.1 系统时序图（Sequence Diagram）

```
[用PlantUML或Mermaid描述时序]
示例：
participant 前端
participant OrderService
participant PayService
participant RocketMQ
participant PostgreSQL

前端 -> OrderService: POST /api/v1/orders (创建订单)
OrderService -> PostgreSQL: 写入订单（状态=待支付）
OrderService -> 前端: 返回订单ID + 支付URL
前端 -> PayService: 发起支付
PayService -> RocketMQ: 发送事务消息（支付成功）
RocketMQ -> OrderService: 消费消息，更新订单状态=已支付
```

### 2.2 服务交互图

> 标注同步调用（OpenFeign）和异步调用（RocketMQ）的边界。

```
[插入服务交互图，注明 Sync/Async]
```

---

## 3. 分层架构设计

> 严格遵循 DDD 分层，禁止跨层调用。

### 3.1 层级职责说明

| 层级 | 类名命名 | 职责 | 禁止事项 |
|------|---------|------|---------|
| Controller | `XxxController` | 参数校验、路由转发、响应封装 | 不含任何业务逻辑 |
| Service | `XxxService/Impl` | 核心业务逻辑、事务控制 | 不直接操作数据库 |
| Manager（可选） | `XxxManager` | 通用业务、第三方封装、复杂组装 | - |
| Repository/DAO | `XxxMapper/Repo` | 数据持久化 | 不含业务逻辑 |
| Infrastructure | `XxxAdapter` | 中间件适配（Redis/MQ/MinIO） | - |

---

## 4. 模型设计

### 4.1 数据库设计（PostgreSQL）

#### 数据库设计规范说明

数据库设计必须遵循以下规范：

**核心规范要点：**
- 表命名：`t_{biz}_{scope}_{model_name}`（业务域_模块_模型名称）
- 通用字段：每张表必须包含 enabled、create_by、create_time、update_by、update_time、remark
- 索引规范：单表索引数量控制在 5 个以内，关键业务属性必须建立索引
- SQL 安全：禁止 SQL 注入，禁止 `SELECT *`

**详细规范参考：**
- 表命名规范：`rules/database/table-naming.md`
- 通用字段规范：`rules/database/common-fields.md`
- 索引设计规范：`rules/database/index-rules.md`
- SQL 安全红线：`rules/database/sql-red-lines.md`

#### DDL 示例模板

```sql
-- 表命名规范：t_{biz}_{scope}_{model_name}
CREATE TABLE t_{biz}_{scope}_{model_name} (
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
    PRIMARY KEY (id)
) COMMENT = '[表说明]';

-- 关键业务属性索引（高频查询字段必须建立）
CREATE INDEX idx_{表名}_{字段名} ON t_{biz}_{scope}_{model_name} ([关键业务字段]);
```

### 4.2 缓存设计（Redis）

#### 缓存设计规范说明

缓存设计必须遵循以下规范：

**核心规范要点：**
- Key 格式：`项目名:模块名:业务含义:唯一标识`
- 过期时间：必须设置合理的过期时间，避免内存泄漏
- 缓存策略：查询时回填、更新时先删缓存、滑动过期等
- 异常处理：缓存穿透、缓存击穿、缓存雪崩的应对方案

**详细规范参考：** `rules/architecture/cache-strategy.md`

#### 缓存设计示例模板

| Key | 数据结构 | 内容 | 过期时间 | 缓存策略 |
|-----|---------|------|---------|---------|
| `mall:order:info:{orderId}` | String(JSON) | 订单详情 | 30分钟 | 查询时回填，更新时先删缓存 |
| `mall:user:session:{userId}` | Hash | 用户Session信息 | 2小时 | 滑动过期 |

### 4.3 消息队列设计（RocketMQ）

#### 消息队列设计规范说明

消息队列设计必须遵循以下规范：

**核心规范要点：**
- Topic 格式：`项目名_业务域_动作`
- 消息体结构：必须明确定义消息体字段
- 可靠性要求：事务消息、普通消息+重试、顺序消息等
- 消费端幂等：数据库唯一键、Redis去重等方式保障

**详细规范参考：** `rules/architecture/mq-design.md`

#### 消息队列设计示例模板

| Topic | Tag | 生产者 | 消费者 | 消息体结构 | 可靠性要求 |
|-------|-----|-------|-------|----------|---------|
| `mall_order_created` | `pay_success` | OrderService | InventoryService | `{orderId, userId, amount}` | 事务消息 |
| `mall_notification` | `sms_send` | NotifyService | SmsService | `{phone, template, params}` | 普通消息+重试 |

---

## 5. API 接口设计

### 5.1 接口设计规范说明

每个接口文档必须包含以下完整章节：

1. **接口说明**：接口地址、请求方式、参数格式、功能描述、是否需要认证、幂等性说明
2. **请求参数**：使用表格定义所有参数（参数名称、说明、类型、是否必填、取值范围、示例值）
3. **请求参数样例**：提供完整的 JSON 请求示例
4. **响应参数**：使用表格定义所有响应字段（包括嵌套字段，使用 `.` 表示层级）
5. **响应样例**：提供成功响应和失败响应（业务异常、系统异常）的完整 JSON 示例

**关键规范要点：**
- URL 设计：`/{api-prefix}/{version}/{resource}/{action}`，资源名称用复数
- 统一响应格式：`Result<T>`（包含 code、msg、data、traceId）
- 参数校验：所有请求参数必须定义校验规则（长度、范围、格式、必填）
- 响应码规范：HTTP 状态码 + 业务状态码（如 `ORDER_001`）
- 幂等性设计：写操作必须说明幂等实现方式
- 分页查询：使用标准分页参数（pageNum、pageSize）
- 接口安全：敏感信息脱敏、认证授权、防重放攻击

**详细规范参考：**
- 统一响应格式：`rules/api/response-format.md`
- URL 命名规范：`rules/api/url-naming.md`
- RESTful 设计：`rules/api/restful-design.md`
- 响应码规范：`rules/api/error-codes.md`
- 参数校验规范：`rules/api/parameter-validation.md`
- 分页查询规范：`rules/api/pagination.md`
- 完整接口设计规范：`api-design-rules.md`

### 5.X [接口名称]

#### 5.X.1 接口说明

| 项目 | 说明 |
|------|------|
| **接口地址** | `/api/v1/[resource]/{id}` |
| **请求方式** | POST / GET / PUT / DELETE |
| **参数格式** | JSON（application/json） |
| **接口描述** | [功能说明，1-2句话] |
| **是否需要认证** | 是/否 |
| **幂等性** | 是（通过[方式]保证）/ 否 |

#### 5.X.2 请求参数

| 参数名称 | 参数说明 | 参数类型 | 是否必填 | 取值范围 | 示例值 |
|---------|---------|---------|---------|---------|--------|
| fieldName | 字段含义 | string | 是 | 长度<=128 | example |
| amount | 金额 | number | 是 | >0，精度Decimal(18,2) | 99.99 |

#### 5.X.3 请求参数样例

```json
{
  "fieldName": "example",
  "amount": 99.99
}
```

#### 5.X.4 响应参数

| 参数名称 | 参数说明 | 参数类型 | 是否必返 | 示例值 |
|---------|---------|---------|---------|--------|
| code | 响应码 | int | 是 | 200 |
| msg | 响应信息 | string | 是 | 操作成功 |
| data | 响应数据 | object | 是 | - |
| data.orderId | 订单ID | long | 是 | 123456789 |
| data.status | 订单状态 | string | 是 | PENDING |
| traceId | 链路追踪ID | string | 是 | a1b2c3d4 |

#### 5.X.5 响应样例

##### 5.X.5.1 成功响应

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "orderId": 123456789,
    "status": "PENDING"
  },
  "traceId": "a1b2c3d4"
}
```

##### 5.X.5.2 失败响应（业务异常）

```json
{
  "code": 400,
  "msg": "库存不足",
  "data": null,
  "traceId": "a1b2c3d4"
}
```

##### 5.X.5.3 失败响应（系统异常）

```json
{
  "code": 500,
  "msg": "系统繁忙，请稍后重试",
  "data": null,
  "traceId": "a1b2c3d4"
}
```

#### 5.X.6 错误码定义

| 错误码 | 含义 | HTTP状态码 |
|-------|------|----------|
| 200 | 成功 | 200 |
| ORDER_001 | 库存不足 | 400 |
| ORDER_002 | 余额不足 | 400 |
| 500 | 系统内部错误 | 500 |

---

## 6. 核心逻辑设计

### 6.1 关键业务伪代码

```java
// 示例：创建订单核心逻辑
@Transactional
public OrderDTO createOrder(CreateOrderRequest request) {
    // 1. 参数校验（Controller层已做基础校验，这里做业务校验）
    User user = userService.getAndValidate(request.getUserId());

    // 2. 库存预占（加锁）
    inventoryService.preOccupy(request.getItems());

    // 3. 计算金额（精度处理）
    BigDecimal totalAmount = calculateAmount(request);

    // 4. 写入订单（状态=待支付）
    Order order = orderRepository.save(buildOrder(user, totalAmount));

    // 5. 发送事务消息（最终一致性通知）
    // 注意：MQ发送在事务提交后执行，避免消息发出但事务回滚
    orderEventPublisher.publishCreated(order.getId());

    return OrderConverter.toDTO(order);
}
```

### 6.2 并发控制方案

- **乐观锁**：[描述使用场景，如更新库存时通过version字段防并发]
- **分布式锁**：[描述使用场景，如Redis SETNX防重复提交]
- **幂等设计**（参考 common-rules.md §2）：[具体实现方案]

### 6.3 事务边界说明

> 事务内禁止 RPC 调用、文件 IO、复杂计算。

- **本地事务**：[描述哪些操作在同一事务内]
- **分布式事务**：[强一致用Seata AT/最终一致用事务消息，说明选择依据]

---

## 7. 兼容性方案

- **数据迁移脚本**：[如有老数据需要迁移，提供SQL]
- **灰度开关**：[通过 Nacos 配置开关控制新功能，key：`feature.xxx.enabled`]
- **老接口兼容**：[旧接口保留策略及下线时间计划]

---

## 8. 测试计划（提测前自检）

### 8.1 单元测试覆盖点

| 测试类 | 测试方法 | 测试场景 |
|-------|---------|---------|
| `OrderServiceTest` | `testCreateOrder_success` | 正常创建订单 |
| `OrderServiceTest` | `testCreateOrder_insufficientStock` | 库存不足时抛业务异常 |

### 8.2 压测预估

| 场景 | 预期QPS | 测试工具 | 准入标准 |
|------|---------|---------|---------|
| 创建订单接口 | 500 QPS | JMeter | P99 < 200ms，错误率 < 0.1% |

### 8.3 自测 Checklist（提测前必须完成）

- [ ] 正常流程联调通过
- [ ] 异常场景测试（参数非法、库存不足、权限不足等）
- [ ] 幂等性验证（重复调用接口结果一致）
- [ ] 日志 TraceID 打印正确，无敏感信息
- [ ] 接口响应格式符合 `Result<T>` 规范
- [ ] 代码红线自查（参考 common-rules.md §1）
- [ ] 输出《自测报告》
