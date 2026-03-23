# 数据库表命名规范

> 定义数据库表的统一命名规则

## 适用范围

本规范适用于：
- 产品经理在PRD中定义数据实体
- 研发人员设计数据库表结构
- 测试工程师理解数据模型

## 1. 表命名格式

### 1.1 命名规则

**格式：** `t_{biz}_{scope}_{model_name}`

| 段 | 说明 | 示例值 |
|----|------|-------|
| `t_` | 固定前缀（table） | - |
| `{biz}` | 业务域 | order、user、payment、inventory、product |
| `{scope}` | 模块/范围 | core、info、log、config、detail、stat |
| `{model_name}` | 模型名称 | record、item、snapshot、relation、history |

### 1.2 命名示例

| 表名 | 说明 | 业务域 | 模块 | 模型 |
|------|------|-------|------|------|
| `t_order_core_info` | 订单核心信息表 | order | core | info |
| `t_order_detail_item` | 订单明细项表 | order | detail | item |
| `t_order_log_record` | 订单日志记录表 | order | log | record |
| `t_user_auth_account` | 用户认证账号表 | user | auth | account |
| `t_user_info_profile` | 用户信息档案表 | user | info | profile |
| `t_payment_biz_record` | 支付业务记录表 | payment | biz | record |
| `t_payment_log_history` | 支付日志历史表 | payment | log | history |
| `t_inventory_core_stock` | 库存核心库存表 | inventory | core | stock |
| `t_product_info_detail` | 商品信息详情表 | product | info | detail |
| `t_product_stat_summary` | 商品统计汇总表 | product | stat | summary |

## 2. 业务域（biz）定义

### 2.1 常见业务域

| 业务域 | 说明 | 适用场景 |
|-------|------|---------|
| `order` | 订单域 | 订单创建、支付、发货、完成等 |
| `user` | 用户域 | 用户注册、登录、信息管理等 |
| `payment` | 支付域 | 支付、退款、对账等 |
| `inventory` | 库存域 | 库存管理、出入库等 |
| `product` | 商品域 | 商品信息、分类、属性等 |
| `marketing` | 营销域 | 优惠券、活动、推广等 |
| `logistics` | 物流域 | 发货、配送、签收等 |
| `finance` | 财务域 | 账单、结算、发票等 |
| `customer` | 客户域 | 客户信息、关系管理等 |
| `system` | 系统域 | 系统配置、权限、日志等 |

### 2.2 业务域选择原则

- 按照DDD领域驱动设计划分
- 一个表只属于一个业务域
- 业务域名称使用单数形式
- 业务域名称使用英文小写

## 3. 模块/范围（scope）定义

### 3.1 常见模块

| 模块 | 说明 | 适用场景 |
|------|------|---------|
| `core` | 核心模块 | 业务核心数据，如订单主表、用户主表 |
| `info` | 信息模块 | 详细信息数据，如用户档案、商品详情 |
| `detail` | 明细模块 | 明细数据，如订单明细、账单明细 |
| `log` | 日志模块 | 日志记录，如操作日志、变更日志 |
| `config` | 配置模块 | 配置数据，如系统配置、业务规则 |
| `stat` | 统计模块 | 统计汇总数据，如销售统计、用户统计 |
| `relation` | 关系模块 | 关联关系数据，如用户关注、商品关联 |
| `auth` | 认证模块 | 认证授权数据，如账号、角色、权限 |
| `biz` | 业务模块 | 通用业务数据，如支付记录、退款记录 |

### 3.2 模块选择原则

- 根据数据的功能和用途选择
- 一个表只属于一个模块
- 模块名称使用英文小写
- 优先使用标准模块名称

## 4. 模型名称（model_name）定义

### 4.1 常见模型名称

| 模型名称 | 说明 | 适用场景 |
|---------|------|---------|
| `info` | 信息 | 主体信息表 |
| `record` | 记录 | 业务记录表 |
| `item` | 项/条目 | 明细项表 |
| `detail` | 详情 | 详细信息表 |
| `snapshot` | 快照 | 历史快照表 |
| `history` | 历史 | 历史记录表 |
| `summary` | 汇总 | 汇总统计表 |
| `relation` | 关系 | 关联关系表 |
| `account` | 账号 | 账号信息表 |
| `profile` | 档案 | 档案信息表 |
| `stock` | 库存 | 库存数据表 |
| `config` | 配置 | 配置数据表 |

### 4.2 模型名称选择原则

- 使用英文单词，避免缩写
- 使用单数形式
- 名称要能准确表达表的内容
- 避免使用过于宽泛的名称（如 data、table）

## 5. 命名规范检查清单

在创建表之前，必须逐项检查：

- [ ] 表名符合 `t_{biz}_{scope}_{model_name}` 格式
- [ ] 业务域（biz）选择正确且使用单数形式
- [ ] 模块（scope）选择正确且使用标准名称
- [ ] 模型名称（model_name）准确表达表的内容
- [ ] 表名使用小写字母和下划线
- [ ] 表名长度不超过64个字符
- [ ] 表名在数据库中唯一

## 6. 错误示例

| 错误表名 | 问题 | 正确表名 |
|---------|------|---------|
| `order_info` | 缺少 `t_` 前缀 | `t_order_core_info` |
| `t_orders_info` | 业务域使用复数形式 | `t_order_core_info` |
| `t_order_info` | 缺少模块（scope） | `t_order_core_info` |
| `t_order_core` | 缺少模型名称 | `t_order_core_info` |
| `t_order_core_data` | 模型名称过于宽泛 | `t_order_core_info` |
| `t_ord_core_info` | 业务域使用缩写 | `t_order_core_info` |
| `t_Order_Core_Info` | 使用大写字母 | `t_order_core_info` |

## 7. 特殊场景处理

### 7.1 中间表命名

**格式：** `t_{biz}_relation_{entity1}_{entity2}`

**示例：**
- `t_user_relation_follow` - 用户关注关系表
- `t_product_relation_category` - 商品分类关系表

### 7.2 临时表命名

**格式：** `t_temp_{biz}_{purpose}_{date}`

**示例：**
- `t_temp_order_migration_20260323` - 订单迁移临时表

### 7.3 归档表命名

**格式：** `t_{biz}_{scope}_{model_name}_archive_{year}`

**示例：**
- `t_order_core_info_archive_2025` - 2025年订单归档表

---

**文档版本**: 1.0
**创建日期**: 2026-03-23
**适用项目**: 所有企业级项目
