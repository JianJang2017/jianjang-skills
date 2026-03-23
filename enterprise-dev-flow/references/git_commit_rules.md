# Git 提交规范

## 概述

本文档定义了 ChatDr.Module.Service 项目的 Git 提交规范，旨在确保提交历史的清晰性和可追溯性。所有开发人员在提交代码时必须遵守本规范。

## 提交信息格式

### 基本格式

```
<type>: <subject>

<body>

<footer>
```

### 格式说明

- **type**: 提交类型（必需）
- **subject**: 提交主题（必需）
- **body**: 提交详情（可选）
- **footer**: 提交备注（可选）

### 示例

```
feat: 新增用户健康档案查询接口

实现用户健康档案的分页查询功能，支持按时间范围和指标类型过滤。

Closes #123
```

## 提交类型（Type）

### 类型列表

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat: 新增用户健康档案查询接口 |
| fix | 修复 bug | fix: 修复报告解析失败的问题 |
| docs | 文档更新 | docs: 更新 API 设计规范文档 |
| style | 代码格式调整（不影响功能） | style: 格式化代码，统一缩进 |
| refactor | 重构（不新增功能，不修复 bug） | refactor: 重构用户服务层代码 |
| perf | 性能优化 | perf: 优化健康档案查询性能 |
| test | 测试相关 | test: 新增用户服务单元测试 |
| chore | 构建/工具相关 | chore: 升级 Spring Boot 版本 |
| revert | 回滚 | revert: 回滚 feat: 新增用户健康档案查询接口 |

### 类型选择原则

- **feat**: 新增功能、新增接口、新增模块
- **fix**: 修复 bug、修复异常、修复性能问题
- **docs**: 更新文档、新增文档、修改注释
- **style**: 代码格式化、空格调整、分号补充（不影响代码逻辑）
- **refactor**: 代码重构、优化代码结构（不新增功能，不修复 bug）
- **perf**: 性能优化、查询优化、缓存优化
- **test**: 新增测试、修改测试、删除测试
- **chore**: 依赖升级、构建配置、工具配置
- **revert**: 回滚之前的提交

## 提交主题（Subject）

### 基本规则

- 使用中文描述
- 简明扼要，不超过 50 个字符
- 使用动词开头，如"新增"、"修复"、"优化"
- 不要以句号结尾
- 首字母不要大写（中文无此要求）

### 正确示例

```
feat: 新增用户健康档案查询接口
fix: 修复报告解析失败的问题
docs: 更新 API 设计规范文档
refactor: 重构用户服务层代码
perf: 优化健康档案查询性能
```

### 错误示例

```
feat: 新增用户健康档案查询接口。              # 不要以句号结尾
fix: 修复了报告解析失败的问题                 # 不要使用"了"等助词
docs: 更新了 API 设计规范文档，增加了示例     # 主题过长，应拆分为多个提交
refactor: 代码重构                           # 主题不明确，应说明重构了什么
```

## 提交详情（Body）

### 基本规则

- 使用中文描述
- 详细说明提交的内容、原因、影响
- 每行不超过 72 个字符
- 与主题之间空一行

### 内容建议

- **是什么**: 说明做了什么改动
- **为什么**: 说明为什么要做这个改动
- **怎么做**: 说明如何实现的（可选）
- **影响**: 说明对系统的影响（可选）

### 示例

```
feat: 新增用户健康档案查询接口

实现用户健康档案的分页查询功能，支持按时间范围和指标类型过滤。

主要改动：
1. 新增 UserHealthRecordController.query 接口
2. 新增 UserHealthRecordService.query 方法
3. 新增 UserHealthRecordQueryReq 请求 DTO
4. 新增 UserHealthRecordResp 响应 DTO

影响：
- 前端可以调用此接口查询用户健康档案
- 需要更新 API 文档
```

## 提交备注（Footer）

### 关联 Issue

使用 `Closes`、`Fixes`、`Resolves` 关联 Issue。

```
Closes #123
Fixes #456
Resolves #789
```

### 不兼容变更

使用 `BREAKING CHANGE` 标记不兼容变更。

```
BREAKING CHANGE: 修改了用户健康档案查询接口的响应格式

原响应格式：
{
  "code": 0,
  "data": [...]
}

新响应格式：
{
  "code": 0,
  "data": {
    "total": 100,
    "list": [...]
  }
}
```

## 提交规范示例

### 新增功能

```
feat: 新增用户健康档案查询接口

实现用户健康档案的分页查询功能，支持按时间范围和指标类型过滤。

主要改动：
1. 新增 UserHealthRecordController.query 接口
2. 新增 UserHealthRecordService.query 方法
3. 新增 UserHealthRecordQueryReq 请求 DTO
4. 新增 UserHealthRecordResp 响应 DTO

Closes #123
```

### 修复 bug

```
fix: 修复报告解析失败的问题

问题描述：
当报告图片质量较差时，OCR 识别失败，导致报告解析失败。

解决方案：
1. 增加图片预处理，提高图片质量
2. 增加 OCR 识别重试机制
3. 增加异常处理，避免解析失败导致系统异常

Fixes #456
```

### 文档更新

```
docs: 更新 API 设计规范文档

新增以下内容：
1. RESTful 设计原则
2. 请求设计规范
3. 响应设计规范
4. 错误码规范
```

### 代码重构

```
refactor: 重构用户服务层代码

优化代码结构，提高代码可读性和可维护性。

主要改动：
1. 拆分 UserService，按功能划分为多个 Service
2. 提取公共方法到 UserServiceHelper
3. 优化异常处理逻辑
4. 优化日志记录
```

### 性能优化

```
perf: 优化健康档案查询性能

问题描述：
健康档案查询接口响应时间过长，影响用户体验。

优化方案：
1. 增加 Redis 缓存，缓存热点数据
2. 优化 SQL 查询，增加索引
3. 使用分页查询，限制查询数量

优化效果：
- 查询响应时间从 2s 降低到 200ms
- 数据库查询次数减少 80%
```

### 测试相关

```
test: 新增用户服务单元测试

新增以下测试用例：
1. 测试用户创建功能
2. 测试用户查询功能
3. 测试用户更新功能
4. 测试用户删除功能

测试覆盖率：85%
```

### 构建/工具相关

```
chore: 升级 Spring Boot 版本

升级 Spring Boot 从 2.6.0 到 2.7.0

主要变更：
1. 更新 pom.xml 依赖版本
2. 修复不兼容的 API 调用
3. 更新配置文件

影响：
- 提升系统性能
- 修复安全漏洞
```

### 回滚

```
revert: 回滚 feat: 新增用户健康档案查询接口

回滚原因：
该功能存在性能问题，导致系统响应缓慢，需要重新设计。

This reverts commit 1234567890abcdef.
```

## 分支管理规范

### 分支类型

| 分支类型 | 命名规则 | 说明 | 示例 |
|---------|---------|------|------|
| 主分支 | master | 生产环境代码 | master |
| 开发分支 | main-develop-v{version} | 开发环境代码 | main-develop-v0.5 |
| 功能分支 | feature/{feature-name} | 新功能开发 | feature/user-health-record |
| 修复分支 | bugfix/{bug-name} | bug 修复 | bugfix/report-parse-error |
| 热修复分支 | hotfix/{hotfix-name} | 紧急修复 | hotfix/security-vulnerability |
| 发布分支 | release/{version} | 发布准备 | release/v0.5.0 |

### 分支命名规范

- 使用小写字母
- 多个单词使用连字符（-）分隔
- 功能分支以 `feature/` 开头
- 修复分支以 `bugfix/` 开头
- 热修复分支以 `hotfix/` 开头
- 发布分支以 `release/` 开头

### 分支工作流

#### 功能开发流程

1. 从开发分支创建功能分支

```bash
git checkout main-develop-v0.5
git pull origin main-develop-v0.5
git checkout -b feature/user-health-record
```

2. 在功能分支上开发

```bash
# 开发代码
git add .
git commit -m "feat: 新增用户健康档案查询接口"
```

3. 推送功能分支

```bash
git push origin feature/user-health-record
```

4. 创建 Pull Request，合并到开发分支

5. 代码审查通过后，合并到开发分支

6. 删除功能分支

```bash
git branch -d feature/user-health-record
git push origin --delete feature/user-health-record
```

#### Bug 修复流程

1. 从开发分支创建修复分支

```bash
git checkout main-develop-v0.5
git pull origin main-develop-v0.5
git checkout -b bugfix/report-parse-error
```

2. 在修复分支上修复 bug

```bash
# 修复 bug
git add .
git commit -m "fix: 修复报告解析失败的问题"
```

3. 推送修复分支

```bash
git push origin bugfix/report-parse-error
```

4. 创建 Pull Request，合并到开发分支

5. 代码审查通过后，合并到开发分支

6. 删除修复分支

```bash
git branch -d bugfix/report-parse-error
git push origin --delete bugfix/report-parse-error
```

#### 热修复流程

1. 从主分支创建热修复分支

```bash
git checkout master
git pull origin master
git checkout -b hotfix/security-vulnerability
```

2. 在热修复分支上修复问题

```bash
# 修复问题
git add .
git commit -m "fix: 修复安全漏洞"
```

3. 推送热修复分支

```bash
git push origin hotfix/security-vulnerability
```

4. 创建 Pull Request，合并到主分支和开发分支

5. 代码审查通过后，合并到主分支和开发分支

6. 删除热修复分支

```bash
git branch -d hotfix/security-vulnerability
git push origin --delete hotfix/security-vulnerability
```

## 提交规范检查

### 提交前检查

- [ ] 提交类型是否正确？
- [ ] 提交主题是否简明扼要？
- [ ] 提交详情是否清晰？
- [ ] 是否关联了 Issue？
- [ ] 代码是否已测试？
- [ ] 代码是否符合编码规范？

### 使用 Git Hooks

使用 Git Hooks 自动检查提交信息格式。

#### commit-msg Hook

创建 `.git/hooks/commit-msg` 文件：

```bash
#!/bin/sh

commit_msg_file=$1
commit_msg=$(cat "$commit_msg_file")

# 检查提交信息格式
if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|perf|test|chore|revert): .+"; then
    echo "错误：提交信息格式不正确"
    echo "格式：<type>: <subject>"
    echo "类型：feat, fix, docs, style, refactor, perf, test, chore, revert"
    exit 1
fi

# 检查提交主题长度
subject=$(echo "$commit_msg" | head -n 1)
if [ ${#subject} -gt 50 ]; then
    echo "错误：提交主题过长（超过 50 个字符）"
    exit 1
fi

exit 0
```

赋予执行权限：

```bash
chmod +x .git/hooks/commit-msg
```

## 最佳实践

### 提交频率

- 每完成一个小功能就提交一次
- 不要等到完成所有功能才提交
- 不要一次提交过多改动

### 提交粒度

- 每次提交只做一件事
- 不要在一次提交中混合多个功能或修复
- 不要在一次提交中修改多个模块

### 提交顺序

- 先提交功能代码，再提交测试代码
- 先提交核心功能，再提交辅助功能
- 先提交代码，再提交文档

### 提交审查

- 提交前检查代码变更
- 提交前运行测试
- 提交前格式化代码

```bash
# 查看代码变更
git diff

# 查看暂存区变更
git diff --cached

# 运行测试
mvn test

# 格式化代码
mvn spotless:apply
```

### 提交回滚

如果提交有误，可以回滚提交。

```bash
# 回滚最后一次提交（保留代码变更）
git reset --soft HEAD~1

# 回滚最后一次提交（丢弃代码变更）
git reset --hard HEAD~1

# 回滚指定提交
git revert <commit-id>
```

## 常见问题

### 提交信息写错了怎么办？

```bash
# 修改最后一次提交信息
git commit --amend

# 修改历史提交信息
git rebase -i HEAD~3  # 修改最近 3 次提交
```

### 提交了不该提交的文件怎么办？

```bash
# 从暂存区移除文件
git reset HEAD <file>

# 从提交中移除文件
git rm --cached <file>
git commit --amend
```

### 忘记关联 Issue 怎么办？

```bash
# 修改最后一次提交信息，添加 Issue 关联
git commit --amend
```

### 提交到错误的分支怎么办？

```bash
# 回滚提交
git reset --hard HEAD~1

# 切换到正确的分支
git checkout correct-branch

# 重新提交
git cherry-pick <commit-id>
```

---

**文档版本**: 1.0
**创建日期**: 2026-03-09
**最后更新**: 2026-03-09
**维护者**: ChatDr 开发团队

