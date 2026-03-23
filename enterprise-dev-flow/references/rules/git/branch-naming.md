# 分支命名规范

> 适用范围：所有 Git 分支管理，适用于所有开发人员

---

## 1. 规则说明

统一的分支命名规范能够清晰表达分支的用途和生命周期，便于团队协作和代码管理。本规范定义了 Git 分支的命名规则和工作流程。

## 2. 规则内容

### 2.1 分支类型

| 分支类型 | 命名规则 | 说明 | 生命周期 |
|---------|---------|------|---------|
| 主分支 | master | 生产环境代码，只能通过合并更新 | 永久 |
| 开发分支 | main-develop-v{version} | 开发环境代码，集成所有功能 | 永久 |
| 功能分支 | feature/{feature-name} | 新功能开发 | 临时 |
| 修复分支 | bugfix/{bug-name} | bug 修复 | 临时 |
| 热修复分支 | hotfix/{hotfix-name} | 紧急修复生产问题 | 临时 |
| 发布分支 | release/{version} | 发布准备 | 临时 |

### 2.2 分支命名规则

- 使用小写字母
- 多个单词使用连字符（-）分隔
- 功能分支以 `feature/` 开头
- 修复分支以 `bugfix/` 开头
- 热修复分支以 `hotfix/` 开头
- 发布分支以 `release/` 开头

### 2.3 分支工作流

#### 功能开发流程

1. 从开发分支创建功能分支
2. 在功能分支上开发
3. 推送功能分支到远程
4. 创建 Pull Request，合并到开发分支
5. 代码审查通过后，合并到开发分支
6. 删除功能分支

#### Bug 修复流程

1. 从开发分支创建修复分支
2. 在修复分支上修复 bug
3. 推送修复分支到远程
4. 创建 Pull Request，合并到开发分支
5. 代码审查通过后，合并到开发分支
6. 删除修复分支

#### 热修复流程

1. 从主分支创建热修复分支
2. 在热修复分支上修复问题
3. 推送热修复分支到远程
4. 创建 Pull Request，合并到主分支和开发分支
5. 代码审查通过后，合并到主分支和开发分支
6. 删除热修复分支

## 3. 示例

### 正确示例

```bash
# 主分支
master

# 开发分支
main-develop-v0.5
main-develop-v1.0

# 功能分支
feature/user-health-record
feature/report-analysis
feature/payment-integration

# 修复分支
bugfix/report-parse-error
bugfix/login-timeout
bugfix/data-inconsistency

# 热修复分支
hotfix/security-vulnerability
hotfix/payment-failure
hotfix/data-loss

# 发布分支
release/v0.5.0
release/v1.0.0
```

### 错误示例

```bash
# ❌ 使用大写字母
Feature/UserHealthRecord
BUGFIX/report-parse-error

# ❌ 使用下划线
feature/user_health_record
bugfix/report_parse_error

# ❌ 没有使用前缀
user-health-record
report-parse-error

# ❌ 分支名称不明确
feature/new-feature
bugfix/fix-bug
```

## 4. 检查清单

- [ ] 分支名称使用小写字母
- [ ] 多个单词使用连字符（-）分隔
- [ ] 功能分支以 `feature/` 开头
- [ ] 修复分支以 `bugfix/` 开头
- [ ] 热修复分支以 `hotfix/` 开头
- [ ] 发布分支以 `release/` 开头
- [ ] 分支名称清晰明确，能够表达分支用途
- [ ] 临时分支在合并后及时删除

---

**版本：** 1.0
**最后更新：** 2026-03-23
