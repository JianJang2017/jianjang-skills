# URL 命名规范

> 适用范围：所有 HTTP API 接口 URL 设计，适用于产品经理定义接口路径、研发人员实现接口

---

## 1. 规则说明

统一的 URL 命名规范能够提高接口的可读性和可维护性，使接口更加直观易懂。本规范定义了企业级应用中 URL 的命名规则和最佳实践。

## 2. 规则内容

### 2.1 URL 结构

标准 URL 结构如下：

```
/{api-prefix}/{version}/{resource}/{action}
```

| 段 | 说明 | 是否必需 | 示例 |
|----|------|---------|------|
| api-prefix | API 前缀 | 是 | api |
| version | 版本号 | 是 | v1、v2 |
| resource | 资源名称（复数） | 是 | users、orders、products |
| action | 操作（非标准 CRUD） | 否 | login、logout、export |

### 2.2 命名规则

1. **使用小写字母**：所有字母必须小写
2. **使用连字符分隔**：多个单词使用连字符（-）分隔，不使用下划线（_）
3. **资源名称用复数**：表示资源集合时使用复数形式
4. **避免使用动词**：用 HTTP Method 表达操作，URL 只表示资源
5. **层级不超过 3 层**：避免 URL 过深，影响可读性

### 2.3 标准 CRUD 操作

| 操作 | HTTP Method | URL 格式 | 示例 |
|------|------------|---------|------|
| 查询列表 | GET | /api/{version}/{resources} | /api/v1/users |
| 查询详情 | GET | /api/{version}/{resources}/{id} | /api/v1/users/10001 |
| 创建 | POST | /api/{version}/{resources} | /api/v1/users |
| 全量更新 | PUT | /api/{version}/{resources}/{id} | /api/v1/users/10001 |
| 部分更新 | PATCH | /api/{version}/{resources}/{id} | /api/v1/users/10001 |
| 删除 | DELETE | /api/{version}/{resources}/{id} | /api/v1/users/10001 |

### 2.4 非标准操作

对于非标准 CRUD 操作，可以在资源后添加动作：

```
POST /api/v1/users/login
POST /api/v1/orders/cancel
POST /api/v1/reports/export
```

### 2.5 资源层级关系

使用 URL 层级表示资源之间的从属关系：

```
GET /api/v1/users/{userId}/orders
GET /api/v1/orders/{orderId}/items
```

## 3. 示例

### 正确示例

```
# 用户相关
GET    /api/v1/users                    # 查询用户列表
GET    /api/v1/users/10001              # 查询指定用户
POST   /api/v1/users                    # 创建用户
PUT    /api/v1/users/10001              # 更新用户
DELETE /api/v1/users/10001              # 删除用户
POST   /api/v1/users/login              # 用户登录

# 订单相关
GET    /api/v1/orders                   # 查询订单列表
GET    /api/v1/orders/20001             # 查询指定订单
POST   /api/v1/orders                   # 创建订单
POST   /api/v1/orders/cancel            # 取消订单

# 用户订单（层级关系）
GET    /api/v1/users/10001/orders       # 查询指定用户的订单列表

# 多词资源
GET    /api/v1/user-profiles            # 用户档案
GET    /api/v1/order-items              # 订单明细
```

### 错误示例

```
# ❌ 使用动词
GET /api/v1/getUser
POST /api/v1/createUser
POST /api/v1/deleteOrder

# ❌ 使用单数形式
GET /api/v1/user
GET /api/v1/order

# ❌ 使用下划线
GET /api/v1/user_profiles
GET /api/v1/order_items

# ❌ 使用大写字母
GET /api/v1/Users
GET /api/v1/UserProfiles

# ❌ 缺少版本号
GET /api/users

# ❌ URL 层级过深
GET /api/v1/users/10001/orders/20001/items/30001/details

# ❌ 不使用 HTTP 方法语义
POST /api/v1/users/delete
GET /api/v1/users/create
```

## 4. 检查清单

- [ ] URL 包含 API 前缀（api）
- [ ] URL 包含版本号（v1、v2）
- [ ] 资源名称使用复数形式
- [ ] 使用小写字母
- [ ] 多个单词使用连字符（-）分隔
- [ ] 不包含动词（标准 CRUD 操作）
- [ ] 非标准操作在资源后添加动作
- [ ] URL 层级不超过 3 层
- [ ] 使用路径参数表示资源 ID

---

**版本：** 1.0
**最后更新：** 2026-03-23
