# 企业级产品应用开发全流程技能包 - 安装指南

## 快速安装

### 方式一：符号链接（推荐）

适合开发和频繁更新的场景，修改源文件会立即生效。

```bash
ln -s $(pwd)/enterprise-dev-flow ~/.claude/skills/enterprise-dev-flow
```

### 方式二：直接复制

适合稳定使用的场景。

```bash
cp -r enterprise-dev-flow ~/.claude/skills/
```

## 验证安装

```bash
# 检查技能包是否存在
ls ~/.claude/skills/enterprise-dev-flow

# 查看所有技能
ls ~/.claude/skills/enterprise-dev-flow/skills/*/SKILL.md
```

## 可用命令

安装后，可以在 Claude Code 中使用以下命令：

### 产品阶段
- `/prd:writing-prd` - 撰写产品需求文档（PRD）

### 研发阶段
- `/dev:writing-design` - 撰写研发详细设计文档
- `/dev:planning-tasks` - 拆分研发任务与生成实施计划

### 测试阶段
- `/test:designing-cases` - 设计测试用例
- `/test:writing-report` - 撰写测试总结报告

## 自然语言触发

除了使用命令，也可以直接用自然语言触发技能：

**产品需求文档：**
- "写PRD"
- "帮我整理需求"
- "出需求文档"

**研发设计：**
- "写设计文档"
- "写技术方案"
- "数据库怎么设计"

**任务拆分：**
- "帮我拆任务"
- "出一个开发计划"
- "这个需求怎么做"

**测试用例：**
- "帮我写测试用例"
- "这个功能怎么测"
- "测试覆盖哪些点"

**测试报告：**
- "写测试报告"
- "能不能上线"
- "质量评估"

## 技能包结构

```
enterprise-dev-flow/
├── plugin.json              # 插件配置
├── commands/                # 命令别名（5个）
├── skills/                  # 核心技能（5个）
│   ├── prd-writer/         # PRD撰写
│   ├── design-writer/      # 设计文档撰写
│   ├── task-planner/       # 任务拆分
│   ├── test-designer/      # 测试用例设计
│   └── test-reporter/      # 测试报告撰写
└── references/              # 参考文档
    ├── common-rules.md     # 通用规范
    ├── prd-template.md     # PRD模板
    ├── design-template.md  # 设计模板
    ├── test-template.md    # 测试模板
    ├── api-design-rules.md # API规范
    ├── git_commit_rules.md # Git规范
    └── rules/              # 细分规则库（25个规则文件）
        ├── security/       # 安全规则
        ├── database/       # 数据库规则
        ├── api/            # 接口规则
        ├── code-quality/   # 代码质量规则
        ├── git/            # Git规则
        ├── testing/        # 测试规则
        └── architecture/   # 架构规则
```

## 技术栈

本技能包专为以下技术栈设计：

- **后端框架：** Spring Cloud Alibaba
- **数据库：** PostgreSQL
- **缓存：** Redis
- **消息队列：** RocketMQ
- **文件存储：** MinIO

## 卸载

```bash
# 如果是符号链接
rm ~/.claude/skills/enterprise-dev-flow

# 如果是直接复制
rm -rf ~/.claude/skills/enterprise-dev-flow
```

## 更新

### 符号链接方式
直接在源目录修改文件即可，无需重新安装。

### 复制方式
```bash
# 删除旧版本
rm -rf ~/.claude/skills/enterprise-dev-flow

# 复制新版本
cp -r enterprise-dev-flow ~/.claude/skills/
```

## 故障排查

### 技能无法触发

1. 检查技能包是否正确安装：
   ```bash
   ls ~/.claude/skills/enterprise-dev-flow/skills/*/SKILL.md
   ```

2. 检查 SKILL.md 文件格式是否正确（YAML frontmatter）

3. 重启 Claude Code

### 引用文件找不到

检查 references 目录结构是否完整：
```bash
ls ~/.claude/skills/enterprise-dev-flow/references/rules/
```

## 支持

- **版本：** 2.1.0
- **更新日期：** 2026-03-23
- **维护者：** Enterprise Dev Team
- **许可证：** MIT

## 相关文档

- `README.md` - 技能包使用说明
- `CHANGELOG.md` - 版本更新日志
- `OPTIMIZATION_REPORT.md` - 专业性优化报告
- `RULES_REFACTORING_SUMMARY.md` - 规则重构总结
