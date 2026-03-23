# 企业级产品应用开发全流程技能包 - 更新日志

## 版本：1.1.0
**更新日期：** 2026-03-23

---

## 本次更新内容

### 1. 数据库设计规范增强 ✅

#### 表命名规范
- **格式：** `t_{biz}_{scope}_{model_name}`
- **示例：** `t_order_core_info`、`t_user_auth_account`、`t_payment_biz_record`

#### 通用字段（6个必填）
```sql
enabled     TINYINT(1)   NOT NULL DEFAULT 1  -- 是否有效：0-无效，1-有效
create_by   VARCHAR(64)  NOT NULL             -- 创建人
create_time TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
update_by   VARCHAR(64)  NOT NULL             -- 更新人
update_time TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
remark      VARCHAR(500) NULL                 -- 备注
```

#### 索引规范
- 单表不超过5个
- **关键业务属性（高频查询字段）必须建立索引**
- 区分度低的字段禁止单独建索引

**更新文件：**
- `references/design-template.md` - §4.1 数据库设计
- `skills/design-writer/SKILL.md` - 第四步：数据模型设计

---

### 2. 代码提交规范集成 ✅

#### Commit Message 格式
```
<type>: <subject>

<body>

<footer>
```

#### 提交类型
- `feat` - 新功能
- `fix` - 修复 bug
- `docs` - 文档更新
- `style` - 代码格式调整
- `refactor` - 重构
- `perf` - 性能优化
- `test` - 测试相关
- `chore` - 构建/工具相关
- `revert` - 回滚

#### 分支命名规范
- 主分支：`master`
- 开发分支：`main-develop-v{version}`
- 功能分支：`feature/{feature-name}`
- 修复分支：`bugfix/{bug-name}`
- 热修复分支：`hotfix/{hotfix-name}`
- 发布分支：`release/{version}`

**新增文件：**
- `references/git_commit_rules.md` - 完整的 Git 提交规范文档（565行）

**更新文件：**
- `references/common-rules.md` - §9 代码提交规范摘要

---

### 3. 接口设计规范新增 ✅

#### 统一响应格式
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": { ... },
  "traceId": "a1b2c3d4e5f6"
}
```

#### URL 设计规范
- 格式：`/{api-prefix}/{version}/{resource}/{action}`
- 资源名称使用复数形式
- 使用小写字母，多个单词用连字符（-）分隔
- 避免使用动词，用 HTTP Method 表达操作

#### 接口文档必须包含的章节
1. **接口说明** - 接口地址、请求方式、参数格式、功能描述、是否需要认证、幂等性说明
2. **请求参数** - 使用表格定义所有参数（参数名称、说明、类型、是否必填、取值范围、示例值）
3. **请求参数样例** - 提供完整的 JSON 请求示例
4. **响应参数** - 使用表格定义所有响应字段（包括嵌套字段）
5. **响应样例** - 提供成功响应和失败响应的完整 JSON 示例

#### 响应码规范
| 状态码 | 说明 | 使用场景 |
|-------|------|---------|
| 200 | OK | 请求成功 |
| 400 | Bad Request | 参数校验失败 |
| 401 | Unauthorized | 未认证（未登录） |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 系统内部错误 |

#### 参数校验规范
- 所有请求参数必须在 Controller 层使用 `@Valid` 或 `@Validated` 进行校验
- 必须定义校验规则：长度、范围、格式、必填
- 复杂业务规则校验在 Service 层进行

#### 分页查询规范
- 标准分页参数：`pageNum`（页码，默认1）、`pageSize`（每页数量，默认10，最大100）
- 响应格式包含：`total`、`pageNum`、`pageSize`、`pages`、`list`
- 禁止深分页（pageNum > 1000），改用游标分页

#### 接口安全规范
- 需要认证的接口必须在请求头携带 Token：`Authorization: Bearer {token}`
- 敏感信息必须脱敏展示（手机号、身份证号等）
- 日志中禁止打印敏感信息（密码、密钥等）
- 关键操作接口需要实现防重放机制

**新增文件：**
- `references/api-design-rules.md` - 完整的 API 接口设计规范文档（包含9个章节）

**更新文件：**
- `references/design-template.md` - §5 API 接口设计
- `skills/design-writer/SKILL.md` - 第五步：接口设计
- `references/common-rules.md` - §10 接口设计规范摘要
- `plugin.json` - 添加 api-design-rules 参考文档

---

## 技能包最终结构

```
enterprise-dev-flow/
├── plugin.json                    # 插件配置（已更新）
├── README.md                      # 使用说明
├── commands/                      # 命令别名（4个）
│   ├── dev/
│   │   ├── writing-design.md     # dev:writing-design
│   │   └── planning-tasks.md     # dev:planning-tasks
│   └── test/
│       ├── designing-cases.md    # test:designing-cases
│       └── writing-report.md     # test:writing-report
├── skills/                        # 核心技能（5个）
│   ├── prd-writer/
│   ├── design-writer/            # ✅ 已更新
│   ├── task-planner/
│   ├── test-designer/
│   └── test-reporter/
└── references/                    # 公共规则库（6个）
    ├── common-rules.md           # ✅ 已更新（新增 §9、§10）
    ├── design-template.md        # ✅ 已更新（§4.1、§5）
    ├── prd-template.md
    ├── test-template.md
    ├── git_commit_rules.md       # ✅ 新增
    └── api-design-rules.md       # ✅ 新增
```

**总文件数：** 17 个文件
**参考文档：** 6 个（新增 2 个）

---

## 规范覆盖范围

### 数据库设计规范
- ✅ 表命名规范（`t_{biz}_{scope}_{model_name}`）
- ✅ 通用字段规范（6个必填字段）
- ✅ 索引规范（关键业务属性必须建索引）
- ✅ SQL 红线（禁止 SELECT *、深分页等）

### 代码提交规范
- ✅ Commit Message 格式（type: subject）
- ✅ 提交类型（feat/fix/docs/refactor/test/chore 等）
- ✅ 分支命名规范（feature/bugfix/hotfix/release）
- ✅ 提交前检查清单

### 接口设计规范
- ✅ RESTful 风格
- ✅ 统一响应格式（Result<T>）
- ✅ URL 设计规范
- ✅ 响应码规范（HTTP 状态码 + 业务状态码）
- ✅ 参数校验规范
- ✅ 分页查询规范
- ✅ 接口安全规范
- ✅ 接口文档结构规范

### 通用规范
- ✅ 安全红线（敏感信息保护、SQL 安全、越权防护）
- ✅ 幂等性设计规范
- ✅ 状态机定义规范
- ✅ 缺陷等级标准（P0-P3）
- ✅ 验收标准格式（Given-When-Then）
- ✅ 非功能性需求基线
- ✅ 数据字典规范
- ✅ 发布安全规范

---

## 使用方式

### 安装
```bash
# 方法1：直接复制
cp -r enterprise-dev-flow ~/.claude/skills/

# 方法2：符号链接（推荐）
ln -s $(pwd)/enterprise-dev-flow ~/.claude/skills/enterprise-dev-flow
```

### 命令使用
```bash
# 研发阶段
/dev:writing-design      # 写详细设计文档
/dev:planning-tasks      # 拆分任务计划

# 测试阶段
/test:designing-cases    # 设计测试用例
/test:writing-report     # 写测试报告

# 或者直接用自然语言触发
"帮我写详细设计"
"拆分一下开发任务"
"设计测试用例"
"出测试报告"
```

---

## 质量评估

**插件验证器评分：** 9.5/10
- ✅ 结构规范性：10/10
- ✅ 内容完整性：10/10
- ✅ 文档质量：9/10
- ✅ 实用性：10/10

---

## 下一步建议

### 可选优化（优先级 P2）

1. **补充 prd-writer 命令**
   - 路径：`commands/dev/writing-prd.md`
   - 内容：调用 `skills/prd-writer/SKILL.md`

2. **添加示例文件**
   - `examples/sample-prd.md` - PRD 示例
   - `examples/sample-design.md` - 设计文档示例
   - `examples/sample-api-doc.md` - 接口文档示例
   - `examples/sample-testcases.md` - 测试用例示例

3. **添加 .gitignore**（如果需要版本控制）
   ```
   .DS_Store
   *.swp
   *~
   ```

---

## 技术栈

- **后端框架：** Spring Cloud Alibaba
- **数据库：** PostgreSQL
- **缓存：** Redis
- **消息队列：** RocketMQ
- **文件存储：** MinIO

---

## 许可证

MIT License

---

**维护者：** Enterprise Dev Team
**最后更新：** 2026-03-23
**版本：** 1.1.0
