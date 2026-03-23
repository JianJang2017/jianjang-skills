# 企业级开发流程规则库

本目录包含企业级开发流程中的各类规范和规则，按照类型分类组织。

## 目录结构

```
rules/
├── security/                      # 安全相关规则
│   ├── security-red-lines.md     # 安全红线（敏感信息保护、SQL安全、越权防护）
│   └── sensitive-data.md         # 敏感信息脱敏规范
├── database/                      # 数据库相关规则
│   ├── table-naming.md           # 表命名规范（t_{biz}_{scope}_{model_name}）
│   ├── common-fields.md          # 通用字段规范（6个必填字段）
│   ├── index-rules.md            # 索引规范
│   └── sql-red-lines.md          # SQL红线（禁止SELECT *等）
├── api/                           # 接口相关规则
│   ├── restful-design.md         # RESTful设计规范
│   ├── response-format.md        # 统一响应格式（Result<T>）
│   ├── url-naming.md             # URL命名规范
│   └── error-codes.md            # 错误码规范
├── code-quality/                  # 代码质量相关规则
│   ├── idempotency.md            # 幂等性设计
│   ├── state-machine.md          # 状态机规范
│   └── transaction-boundary.md   # 事务边界规范
├── git/                           # Git相关规则
│   ├── commit-message.md         # 提交信息格式
│   ├── branch-naming.md          # 分支命名规范
│   └── commit-checklist.md       # 提交前检查清单
├── testing/                       # 测试相关规则
│   ├── defect-severity.md        # 缺陷等级标准（P0-P3）
│   └── test-coverage-matrix.md   # 测试覆盖矩阵
└── architecture/                  # 架构相关规则
    ├── nfr-baseline.md           # 非功能性需求基线
    ├── cache-strategy.md         # 缓存策略（Redis）
    └── mq-design.md              # 消息队列设计（RocketMQ）
```

## 使用说明

### 1. 规则引用方式

在文档中引用规则时，使用以下格式：

```markdown
**[规则名称]** - 详见 `rules/category/rule-name.md`

简要说明（1-2句话概括核心要点）
```

### 2. 规则适用场景

| 规则类别 | 适用角色 | 使用阶段 |
|---------|---------|---------|
| security/ | 所有角色 | 全流程 |
| database/ | 产品、研发、测试 | 设计、开发、测试 |
| api/ | 产品、研发、测试 | 设计、开发、测试 |
| code-quality/ | 研发、测试 | 开发、测试 |
| git/ | 研发 | 开发 |
| testing/ | 测试 | 测试 |
| architecture/ | 产品、研发 | 设计 |

### 3. 规则优先级

| 优先级 | 说明 | 违反后果 |
|-------|------|---------|
| P0（强制） | 安全红线、SQL红线 | 阻断上线 |
| P1（必须） | 数据库规范、接口规范 | 代码审查不通过 |
| P2（建议） | 最佳实践、优化建议 | 建议修改 |

### 4. 规则更新流程

1. 提出规则变更需求
2. 团队评审讨论
3. 更新规则文档
4. 通知相关人员
5. 更新引用文档

## 已完成的规则文件

### 安全规则（security/）
- ✅ security-red-lines.md - 安全红线规范
- ✅ sensitive-data.md - 敏感信息脱敏规范

### 数据库规则（database/）
- ✅ table-naming.md - 表命名规范
- ✅ common-fields.md - 通用字段规范
- ✅ index-rules.md - 索引规范
- ✅ sql-red-lines.md - SQL红线规范

### 其他规则（待完善）
- ⏳ api/ - 接口相关规则（参考 references/api-design-rules.md）
- ⏳ code-quality/ - 代码质量规则（参考 references/common-rules.md）
- ⏳ git/ - Git规则（参考 references/git_commit_rules.md）
- ⏳ testing/ - 测试规则（参考 references/test-template.md）
- ⏳ architecture/ - 架构规则（参考 references/design-template.md）

## 维护说明

- 规则文件应保持独立、可复用
- 规则文件之间可以相互引用
- 保持 Markdown 格式规范
- 每个规则文件包含：标题、适用范围、规则内容、示例、检查清单

---

**文档版本**: 1.0
**创建日期**: 2026-03-23
**维护者**: 企业开发团队
