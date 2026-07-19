# 企业级产品应用开发全流程技能包 - 安装指南

## 📋 系统要求

### 必需条件
- **Claude Code**: >= 1.0.0
- **操作系统**: macOS / Linux / Windows (WSL)
- **Shell**: bash 或 zsh

### 推荐配置
- 磁盘空间: 至少 10MB 可用空间
- 网络连接: 用于下载和更新

---

## 🚀 安装方法

### 方式一：.skill 文件安装（推荐，适合普通用户）

这是最简单的安装方式，适合不需要修改源码的用户。

#### 步骤 1：获取 .skill 文件

**选项 A：从 GitHub Releases 下载**

```bash
# 访问 GitHub Releases 页面
# https://github.com/JianJang2017/jianjang-skills/releases
# 下载最新版本的 enterprise-dev-flow-v2.2.0.skill
```

**选项 B：自己打包**

```bash
# 克隆仓库
git clone https://github.com/JianJang2017/jianjang-skills.git
cd jianjang-skills/enterprise-dev-flow

# 运行打包脚本
bash package.sh

# 打包完成后会生成 enterprise-dev-flow-v2.2.0.skill 文件
```

#### 步骤 2：安装 .skill 文件

**方法 A：拖拽安装（最简单）**

直接将 `.skill` 文件拖拽到 Claude Code 窗口即可自动安装。

**方法 B：命令行安装**

```bash
# 安装 .skill 文件
claude skill install enterprise-dev-flow-v2.2.0.skill

# 或使用绝对路径
claude skill install /path/to/enterprise-dev-flow-v2.2.0.skill
```

---

### 方式二：符号链接安装（推荐，适合开发者）

这种方式适合需要修改源码或频繁更新的开发者，修改源文件会立即生效。

```bash
# 1. 克隆仓库到本地
git clone https://github.com/JianJang2017/jianjang-skills.git
cd jianjang-skills

# 2. 创建符号链接到 Claude Code 插件目录
ln -s "$(pwd)/enterprise-dev-flow" ~/.claude/plugins/enterprise-dev-flow

# 优势：可以直接修改源码，git pull 即可更新
```

---

### 方式三：直接复制（不推荐）

适合离线环境或特殊需求。

```bash
# 克隆仓库
git clone https://github.com/JianJang2017/jianjang-skills.git

# 复制到 Claude Code 插件目录
cp -r jianjang-skills/enterprise-dev-flow ~/.claude/plugins/

# 缺点：更新时需要重新复制
```

---

## ✅ 验证安装

安装完成后，使用验证脚本检查安装是否成功。

### 自动验证（推荐）

```bash
# 进入技能包目录
cd ~/.claude/plugins/enterprise-dev-flow

# 运行验证脚本
bash verify-install.sh
```

验证脚本会检查：
- ✓ 核心文件完整性（plugin.json、README.md、LICENSE 等）
- ✓ 5 个技能文件是否存在
- ✓ 25+ 规则文件是否完整
- ✓ 6 个参考模板是否存在
- ✓ 命令别名配置是否正确

### 手动验证

如果无法运行验证脚本，可以手动检查：

```bash
# 检查插件目录是否存在
ls ~/.claude/plugins/enterprise-dev-flow

# 检查 5 个核心技能文件
ls ~/.claude/plugins/enterprise-dev-flow/skills/*/SKILL.md

# 应该看到以下 5 个文件：
# - prd-writer/SKILL.md
# - design-writer/SKILL.md
# - task-planner/SKILL.md
# - test-designer/SKILL.md
# - test-reporter/SKILL.md

# 检查规则文件
ls ~/.claude/plugins/enterprise-dev-flow/references/rules/

# 应该看到以下目录：
# - security/      (2个规则文件)
# - database/      (4个规则文件)
# - api/           (6个规则文件)
# - code-quality/  (4个规则文件)
# - git/           (3个规则文件)
# - testing/       (3个规则文件)
# - architecture/  (3个规则文件)
```

---

## 🎯 使用方式

安装成功后，可以通过以下两种方式使用技能包。

### 方式一：命令触发（精确控制）

在 Claude Code 对话框中输入命令：

```bash
/prd:writing-prd          # 撰写产品需求文档
/dev:writing-design       # 撰写技术设计文档
/dev:planning-tasks       # 拆分开发任务并生成计划
/test:designing-cases     # 设计测试用例
/test:writing-report      # 撰写测试总结报告
```

### 方式二：自然语言触发（智能识别）

技能会自动识别以下关键词并触发：

| 技能 | 触发关键词示例 |
|------|--------------|
| **prd-writer** | "写PRD"、"需求文档"、"产品设计"、"整理需求" |
| **design-writer** | "写设计"、"技术方案"、"架构设计"、"数据库怎么建" |
| **task-planner** | "拆任务"、"排期"、"开发计划"、"怎么分工" |
| **test-designer** | "测试用例"、"怎么测"、"测试点"、"边界值" |
| **test-reporter** | "测试报告"、"测试总结"、"能不能上线"、"质量评估" |

**示例对话：**

```
👤 "帮我写一个用户登录功能的PRD"
🤖 [自动触发 prd-writer]

👤 "根据这个PRD写详细设计，数据库用PostgreSQL"
🤖 [自动触发 design-writer]

👤 "帮我把这个需求拆成开发任务"
🤖 [自动触发 task-planner]
```

---

## 🔧 常见问题排查

### 问题 1：技能无法触发

**症状：** 输入命令或关键词后，技能没有被触发。

**解决方案：**

```bash
# 1. 检查技能包是否正确安装
ls ~/.claude/plugins/enterprise-dev-flow/skills/*/SKILL.md

# 2. 检查 plugin.json 是否存在
cat ~/.claude/plugins/enterprise-dev-flow/plugin.json

# 3. 重启 Claude Code
# 关闭并重新打开 Claude Code 应用

# 4. 检查 SKILL.md 文件格式
# 确保每个 SKILL.md 文件开头有正确的 YAML frontmatter
head -20 ~/.claude/plugins/enterprise-dev-flow/skills/prd-writer/SKILL.md
```

### 问题 2：引用文件找不到

**症状：** 技能运行时提示找不到规则文件或模板文件。

**解决方案：**

```bash
# 检查 references 目录结构是否完整
ls -R ~/.claude/plugins/enterprise-dev-flow/references/

# 应该包含以下文件：
# - common-rules.md
# - prd-template.md
# - design-template.md
# - test-template.md
# - api-design-rules.md
# - git_commit_rules.md
# - rules/ (目录，包含 25+ 规则文件)

# 如果文件缺失，重新安装技能包
```

### 问题 3：验证脚本无法运行

**症状：** 运行 `verify-install.sh` 时报错。

**解决方案：**

```bash
# 1. 确保在技能包根目录运行
cd ~/.claude/plugins/enterprise-dev-flow

# 2. 检查脚本是否有执行权限
ls -l verify-install.sh

# 3. 添加执行权限（如果需要）
chmod +x verify-install.sh

# 4. 使用 bash 显式运行
bash verify-install.sh
```

### 问题 4：符号链接失效

**症状：** 使用符号链接安装后，技能无法使用。

**解决方案：**

```bash
# 1. 检查符号链接是否正确
ls -l ~/.claude/plugins/enterprise-dev-flow

# 2. 检查源目录是否存在
# 如果源目录被移动或删除，需要重新创建符号链接

# 3. 删除旧的符号链接
rm ~/.claude/plugins/enterprise-dev-flow

# 4. 重新创建符号链接
ln -s /path/to/source/enterprise-dev-flow ~/.claude/plugins/enterprise-dev-flow
```

### 问题 5：打包脚本失败

**症状：** 运行 `package.sh` 时报错。

**解决方案：**

```bash
# 1. 确保在技能包根目录运行
cd /path/to/enterprise-dev-flow

# 2. 检查必要文件是否存在
ls plugin.json README.md LICENSE

# 3. 检查 tar 命令是否可用
which tar

# 4. 手动打包（如果脚本失败）
tar -czf enterprise-dev-flow-v2.2.0.skill \
  --exclude='.git' \
  --exclude='.DS_Store' \
  --exclude='*workspace' \
  --exclude='*/evals' \
  .
```

---

## 🗑️ 卸载方法

### 卸载 .skill 文件安装

```bash
# 使用 Claude Code 命令卸载
claude skill uninstall enterprise-dev-flow

# 或手动删除
rm -rf ~/.claude/plugins/enterprise-dev-flow
```

### 卸载符号链接安装

```bash
# 删除符号链接（不会删除源文件）
rm ~/.claude/plugins/enterprise-dev-flow

# 如果需要删除源文件
rm -rf /path/to/source/enterprise-dev-flow
```

### 卸载直接复制安装

```bash
# 删除整个目录
rm -rf ~/.claude/plugins/enterprise-dev-flow
```

---

## 🔄 更新方法

### 更新 .skill 文件安装

```bash
# 1. 下载新版本的 .skill 文件
# 2. 卸载旧版本
claude skill uninstall enterprise-dev-flow

# 3. 安装新版本
claude skill install enterprise-dev-flow-v2.2.0.skill
```

### 更新符号链接安装

```bash
# 进入源目录
cd /path/to/source/enterprise-dev-flow

# 拉取最新代码
git pull origin master

# 无需重新安装，修改会立即生效
```

### 更新直接复制安装

```bash
# 1. 删除旧版本
rm -rf ~/.claude/plugins/enterprise-dev-flow

# 2. 复制新版本
cp -r /path/to/new/enterprise-dev-flow ~/.claude/plugins/
```

---

## 📂 技能包结构

```
enterprise-dev-flow/
├── plugin.json              # 插件配置
├── README.md                # 使用说明
├── INSTALL.md               # 安装指南（本文档）
├── LICENSE                  # 许可证
├── package.sh               # 打包脚本
├── verify-install.sh        # 验证脚本
├── commands/                # 命令别名（5个）
│   ├── prd/writing-prd.md
│   ├── dev/writing-design.md
│   ├── dev/planning-tasks.md
│   ├── test/designing-cases.md
│   └── test/writing-report.md
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
        ├── security/       # 安全规则（2个）
        ├── database/       # 数据库规则（4个）
        ├── api/            # 接口规则（6个）
        ├── code-quality/   # 代码质量规则（4个）
        ├── git/            # Git规则（3个）
        ├── testing/        # 测试规则（3个）
        └── architecture/   # 架构规则（3个）
```

---

## 🎓 技术栈

本技能包专为以下技术栈设计：

| 类别 | 技术 |
|------|------|
| 后端框架 | Spring Cloud Alibaba |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 消息队列 | RocketMQ |
| 文件存储 | MinIO |

---

## 📞 支持

- **版本：** 2.2.0
- **更新日期：** 2026-03-27
- **维护者：** Enterprise Dev Team
- **许可证：** MIT

### 获取帮助

- 提交 Issue：[GitHub Issues](https://github.com/JianJang2017/jianjang-skills/issues)
- 邮件联系：jianjang2017@gmail.com
- 查看文档：[README.md](README.md)

---

## 📚 相关文档

- [README.md](README.md) - 技能包使用说明
- [README_EN.md](README_EN.md) - English Documentation
- [CHANGELOG.md](CHANGELOG.md) - 版本更新日志

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by Enterprise Dev Team

</div>
