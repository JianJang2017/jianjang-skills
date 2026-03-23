# 分页查询规范

> 适用范围：所有需要分页的列表查询接口，适用于产品经理定义分页需求、研发人员实现分页逻辑

---

## 1. 规则说明

分页查询是处理大数据量列表的标准方式，能够提高接口性能和用户体验。本规范定义了统一的分页参数和响应格式，确保分页接口的一致性。

## 2. 规则内容

### 2.1 标准分页参数

| 参数名称 | 参数说明 | 参数类型 | 是否必填 | 默认值 | 取值范围 |
|---------|---------|---------|---------|-------|---------|
| pageNum | 页码（从1开始） | int | 否 | 1 | >= 1 |
| pageSize | 每页数量 | int | 否 | 10 | 1-100 |

### 2.2 分页请求示例

**GET 请求（Query 参数）：**
```
GET /api/v1/users?pageNum=1&pageSize=10
```

**POST 请求（Body 参数）：**
```json
{
  "pageNum": 1,
  "pageSize": 10,
  "keyword": "张三"
}
```

### 2.3 分页响应格式

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "total": 100,
    "pageNum": 1,
    "pageSize": 10,
    "pages": 10,
    "list": [
      { "userId": 1, "nickname": "用户1" },
      { "userId": 2, "nickname": "用户2" }
    ]
  },
  "traceId": "a1b2c3d4e5f6"
}
```

### 2.4 分页响应字段说明

| 字段名称 | 字段说明 | 字段类型 | 是否必返 |
|---------|---------|---------|---------|
| total | 总记录数 | long | 是 |
| pageNum | 当前页码 | int | 是 |
| pageSize | 每页数量 | int | 是 |
| pages | 总页数 | int | 是 |
| list | 数据列表 | array | 是 |

### 2.5 分页性能约束

1. **单页最大数量**：不超过 100 条，防止单次查询数据量过大
2. **禁止深分页**：pageNum > 1000 时，改用游标分页
3. **必须建立索引**：大数据量查询必须在查询条件字段上建立索引
4. **总数优化**：数据量超过 10000 时，可以不返回精确 total，返回 "10000+"

### 2.6 游标分页（深分页场景）

对于深分页场景（pageNum > 1000），使用游标分页：

**请求参数：**
```json
{
  "cursor": "eyJpZCI6MTAwMDF9",  // 上一页最后一条记录的游标
  "pageSize": 10
}
```

**响应格式：**
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "hasMore": true,
    "nextCursor": "eyJpZCI6MTAwMTF9",
    "list": [
      { "userId": 10001, "nickname": "用户1" },
      { "userId": 10002, "nickname": "用户2" }
    ]
  },
  "traceId": "a1b2c3d4e5f6"
}
```

## 3. 示例

### 正确示例

**请求 DTO：**
```java
@Data
public class UserQueryReq {

    @Min(value = 1, message = "页码至少为1")
    private Integer pageNum = 1;

    @Min(value = 1, message = "每页数量至少为1")
    @Max(value = 100, message = "每页数量不能超过100")
    private Integer pageSize = 10;

    private String keyword;
}
```

**响应 DTO：**
```java
@Data
public class PageResult<T> {

    private Long total;

    private Integer pageNum;

    private Integer pageSize;

    private Integer pages;

    private List<T> list;
}
```

**Controller 层：**
```java
@GetMapping
public Result<PageResult<UserResp>> queryUsers(
    @Valid UserQueryReq req) {
    PageResult<UserResp> result = userService.queryUsers(req);
    return Result.success(result);
}
```

**Service 层（使用 MyBatis-Plus）：**
```java
@Override
public PageResult<UserResp> queryUsers(UserQueryReq req) {
    // 构建分页对象
    Page<User> page = new Page<>(req.getPageNum(), req.getPageSize());

    // 构建查询条件
    LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
    if (StringUtils.isNotBlank(req.getKeyword())) {
        wrapper.like(User::getNickname, req.getKeyword())
               .or()
               .like(User::getPhone, req.getKeyword());
    }

    // 执行分页查询
    Page<User> result = userMapper.selectPage(page, wrapper);

    // 转换为响应对象
    PageResult<UserResp> pageResult = new PageResult<>();
    pageResult.setTotal(result.getTotal());
    pageResult.setPageNum(req.getPageNum());
    pageResult.setPageSize(req.getPageSize());
    pageResult.setPages((int) result.getPages());
    pageResult.setList(result.getRecords().stream()
        .map(UserConverter::toResp)
        .collect(Collectors.toList()));

    return pageResult;
}
```

### 错误示例

```java
// ❌ 没有限制 pageSize 最大值
@Data
public class UserQueryReq {
    private Integer pageNum = 1;
    private Integer pageSize = 10;  // 缺少 @Max 限制
}

// ❌ 直接返回 List，没有分页信息
@GetMapping
public Result<List<UserResp>> queryUsers(UserQueryReq req) {
    List<UserResp> list = userService.queryUsers(req);
    return Result.success(list);  // 缺少 total、pages 等信息
}

// ❌ 使用 LIMIT offset, size 实现深分页
SELECT * FROM t_user
WHERE enabled = 1
ORDER BY create_time DESC
LIMIT 10000, 10;  // offset 过大，性能差

// ❌ 没有建立索引的分页查询
SELECT * FROM t_user
WHERE nickname LIKE '%张三%'  // 模糊查询无法使用索引
ORDER BY create_time DESC
LIMIT 0, 10;

// ❌ 分页参数从 0 开始
{
  "pageNum": 0,  // 应该从 1 开始
  "pageSize": 10
}
```

## 4. 检查清单

- [ ] 使用标准分页参数（pageNum、pageSize）
- [ ] pageNum 从 1 开始
- [ ] pageSize 默认值为 10
- [ ] pageSize 最大值不超过 100
- [ ] 响应包含 total、pageNum、pageSize、pages、list 字段
- [ ] 深分页（pageNum > 1000）使用游标分页
- [ ] 查询条件字段建立了索引
- [ ] 避免使用 SELECT *
- [ ] 避免使用前缀模糊查询（LIKE '%xxx'）
- [ ] 大数据量场景考虑不返回精确 total

---

**版本：** 1.0
**最后更新：** 2026-03-23
