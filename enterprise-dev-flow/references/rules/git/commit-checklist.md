# 提交前检查清单

> 适用范围：所有 Git 代码提交前的检查，适用于所有开发人员

---

## 1. 规则说明

提交前检查能够确保代码质量，避免将问题代码提交到代码仓库。本规范定义了提交前必须完成的检查项，确保每次提交都是高质量的。

## 2. 规则内容

### 2.1 提交类型检查

- [ ] 提交类型是否正确？
  - feat：新功能
  - fix：修复 bug
  - docs：文档更新
  - style：代码格式调整
  - refactor：重构
  - perf：性能优化
  - test：测试相关
  - chore：构建/工具相关
  - revert：回滚

### 2.2 提交主题检查

- [ ] 提交主题是否简明扼要？（不超过 50 个字符）
- [ ] 提交主题是否使用动词开头？（新增、修复、优化）
- [ ] 提交主题是否没有以句号结尾？
- [ ] 提交主题是否清晰表达了改动内容？

### 2.3 代码测试检查

- [ ] 代码是否已在本地测试通过？
- [ ] 单元测试是否已编写并通过？
- [ ] 集成测试是否已通过？
- [ ] 是否已在开发环境验证？

### 2.4 编码规范检查

- [ ] 代码是否符合编码规范？
- [ ] 代码是否已格式化？
- [ ] 是否有未使用的导入？
- [ ] 是否有未使用的变量？
- [ ] 是否有代码注释？

### 2.5 安全检查

- [ ] 是否包含敏感信息？（密码、密钥、Token）
- [ ] 是否有 SQL 注入风险？
- [ ] 是否有 XSS 注入风险？
- [ ] 是否有越权访问风险？

### 2.6 Issue 关联检查

- [ ] 是否关联了 Issue？（如有）
- [ ] Issue 是否已解决？
- [ ] 是否需要更新文档？

### 2.7 提交内容检查

- [ ] 是否只提交了相关的文件？
- [ ] 是否误提交了不相关的文件？
- [ ] 是否误提交了临时文件？
- [ ] 是否误提交了配置文件？

## 3. 示例

### 正确示例

**提交前检查：**
```bash
# 1. 查看代码变更
git diff

# 2. 查看暂存区变更
git diff --cached

# 3. 运行测试
mvn test

# 4. 格式化代码
mvn spotless:apply

# 5. 检查代码规范
mvn checkstyle:check

# 6. 提交代码
git add src/main/java/com/example/service/UserService.java
git commit -m "feat: 新增用户健康档案查询接口"
```

### 错误示例

```bash
# ❌ 没有运行测试就提交
git add .
git commit -m "feat: 新增用户健康档案查询接口"

# ❌ 提交了所有文件，包括不相关的文件
git add -A
git commit -m "feat: 新增用户健康档案查询接口"

# ❌ 提交了敏感信息
git add application.yml  # 包含数据库密码
git commit -m "feat: 新增用户健康档案查询接口"

# ❌ 提交信息不明确
git commit -m "fix: 修复问题"
```

## 4. 检查清单

### 提交前必须完成的检查

- [ ] 提交类型是否正确？
- [ ] 提交主题是否简明扼要？
- [ ] 代码是否已测试？
- [ ] 代码是否符合编码规范？
- [ ] 是否关联了 Issue（如有）？
- [ ] 是否包含敏感信息？
- [ ] 是否只提交了相关的文件？

### 使用 Git Hooks 自动检查

**commit-msg Hook：**

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

**pre-commit Hook：**

创建 `.git/hooks/pre-commit` 文件：

```bash
#!/bin/sh

# 运行测试
echo "运行测试..."
mvn test
if [ $? -ne 0 ]; then
    echo "错误：测试未通过"
    exit 1
fi

# 检查代码规范
echo "检查代码规范..."
mvn checkstyle:check
if [ $? -ne 0 ]; then
    echo "错误：代码规范检查未通过"
    exit 1
fi

exit 0
```

赋予执行权限：

```bash
chmod +x .git/hooks/pre-commit
```

---

**版本：** 1.0
**最后更新：** 2026-03-23
