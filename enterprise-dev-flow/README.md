# 企业级产品应用开发全流程技能包

<div align="center">

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/yourusername/enterprise-dev-flow)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-%3E%3D1.0.0-orange.svg)](https://claude.ai/code)
[![Tech Stack](https://img.shields.io/badge/Spring%20Cloud%20Alibaba-✓-brightgreen.svg)](https://spring.io/projects/spring-cloud-alibaba)

[English](README_EN.md) | 简体中文

</div>

---

## 📖 简介

企业级产品应用开发全流程技能包是一套专为 **Claude Code** 设计的智能开发助手工具集，覆盖从需求分析到测试验收的完整软件开发生命周期。

通过 5 个核心技能、25+ 规则文件和 6 个参考模板，帮助团队：
- ✅ 规范化需求文档（PRD）撰写
- ✅ 标准化技术设计方案输出
- ✅ 自动化任务拆分与计划生成
- ✅ 系统化测试用例设计
- ✅ 专业化测试报告产出

**适用技术栈：** Spring Cloud Alibaba + PostgreSQL + Redis + RocketMQ + MinIO

---

## ✨ 核心特性

### 🎯 全流程覆盖
从产品需求到测试验收，每个环节都有对应的专业技能支持，确保文档规范的一致性。

### 📚 规则模块化
25+ 细分规则文件（安全、数据库、API、代码质量、Git、测试、架构），统一维护，按需引用。

### 🔍 自动质量检查
每个技能内置质量检查清单，输出前自动验证是否符合企业级规范。

### 🚀 双格式输出
任务拆分技能同时输出项目管理清单（Markdown）和 Claude Code Plan，满足不同场景需求。

### 🛠️ 技术栈适配
专门针对 Spring Cloud Alibaba 生态优化，提供具体的技术实现指导。

---

## 🔄 开发流程

```mermaid
graph LR
    A[💡 产品需求] -->|prd-writer| B[📄 PRD文档]
    B -->|design-writer| C[🏗️ 设计文档]
    C -->|task-planner| D[📋 任务清单]
    D -->|开发实施| E[✅ 功能完成]
    B -->|test-designer| F[🧪 测试用例]
    E --> F
    F -->|执行测试| G[📊 测试数据]
    G -->|test-reporter| H[📈 测试报告]
    H -->|准出评估| I[🚀 上线发布]

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#ffe1f5
    style D fill:#e1ffe1
    style F fill:#f5e1ff
    style H fill:#ffe1e1
    style I fill:#90EE90
```

### 流程说明

1. **需求阶段**：产品经理使用 `prd-writer` 撰写规范的 PRD 文档
2. **设计阶段**：研发人员使用 `design-writer` 将 PRD 转化为技术设计方案
3. **计划阶段**：使用 `task-planner` 拆分任务，生成开发计划
4. **开发阶段**：研发团队按照任务清单实施开发
5. **测试准备**：测试工程师使用 `test-designer` 基于 PRD 设计测试用例
6. **测试执行**：执行测试用例，收集测试数据
7. **测试总结**：使用 `test-reporter` 生成测试报告
8. **准出评估**：根据测试报告决定是否上线

---

## 📦 技能列表

### 🎯 技能概览

| 技能 | 触发方式 | 功能描述 |
|------|---------|---------|
| **prd-writer** | "写PRD"、"帮我整理需求" | 引导产品经理输出企业级PRD，包含业务架构、功能详述、NFR、验收标准 |
| **design-writer** | "写设计文档"、"数据库怎么设计" | 将PRD转化为技术设计方案，生成时序图、DDL、缓存/MQ设计、接口文档 |
| **task-planner** | "帮我拆任务"、"出开发计划" | 拆解PRD/设计为可执行任务，输出Epic/Story/Task清单和Claude Code Plan |
| **test-designer** | "帮我写测试用例"、"这个功能怎么测" | 系统性设计测试用例，覆盖正常/异常/边界/安全/幂等/并发等8大维度 |
| **test-reporter** | "写测试报告"、"能不能上线" | 产出测试总结报告，包含用例统计、缺陷分析、准出评估、风险评估 |

---

### 📝 prd-writer - PRD 撰写技能

**工作流程：**

```mermaid
graph TD
    A[接收需求描述] --> B{信息是否完整?}
    B -->|否| C[向用户提问]
    C --> D[收集补充信息]
    D --> B
    B -->|是| E[结构化输出PRD]
    E --> F[业务架构设计]
    F --> G[功能详述]
    G --> H[数据字典定义]
    H --> I[验收标准AC]
    I --> J[非功能需求NFR]
    J --> K[质量自检]
    K --> L{是否通过?}
    L -->|否| M[修正问题]
    M --> K
    L -->|是| N[输出最终PRD]

    style A fill:#e1f5ff
    style N fill:#90EE90
    style K fill:#fff4e1
```

**核心功能：**
- ✅ 引导式提问，确保需求完整性
- ✅ 自动检查安全红线、幂等性设计
- ✅ 生成 Given-When-Then 格式验收标准
- ✅ 输出符合企业规范的完整 PRD

---

### 🏗️ design-writer - 设计文档撰写技能

**工作流程：**

```mermaid
graph TD
    A[读取PRD] --> B[需求理解与风险识别]
    B --> C[架构设计]
    C --> C1[绘制时序图]
    C --> C2[定义分层架构]
    C1 --> D[数据模型设计]
    C2 --> D
    D --> D1[数据库表设计]
    D --> D2[缓存设计Redis]
    D --> D3[消息队列设计MQ]
    D1 --> E[接口设计]
    D2 --> E
    D3 --> E
    E --> E1[RESTful API]
    E --> E2[统一响应格式]
    E --> E3[参数校验规则]
    E1 --> F[核心逻辑设计]
    E2 --> F
    E3 --> F
    F --> F1[并发控制]
    F --> F2[事务边界]
    F --> F3[幂等性实现]
    F1 --> G[安全设计自检]
    F2 --> G
    F3 --> G
    G --> H[输出设计文档]

    style A fill:#e1f5ff
    style H fill:#90EE90
    style G fill:#fff4e1
```

**核心功能：**
- ✅ 生成 Mermaid 时序图
- ✅ PostgreSQL DDL 脚本
- ✅ Redis 缓存设计（Key规范、一致性方案）
- ✅ RocketMQ 消息设计（Topic命名、幂等消费）
- ✅ RESTful 接口文档（含请求/响应示例）
- ✅ 并发控制、事务边界、幂等性方案

---

### 📋 task-planner - 任务拆分技能

**工作流程：**

```mermaid
graph TD
    A[读取PRD/设计文档] --> B{信息是否充足?}
    B -->|否| C[向用户确认]
    C --> D[补充技术细节]
    D --> B
    B -->|是| E[识别核心模块]
    E --> F[构建任务层级]
    F --> F1[Epic层级]
    F --> F2[Story层级]
    F --> F3[Task层级]
    F1 --> G[梳理依赖关系]
    F2 --> G
    F3 --> G
    G --> H[估算工时]
    H --> I[分配优先级]
    I --> J{输出格式?}
    J -->|项目管理| K[Markdown清单]
    J -->|Claude Code| L[Plan格式]
    K --> M[输出任务计划]
    L --> M

    style A fill:#e1f5ff
    style M fill:#90EE90
    style J fill:#fff4e1
```

**核心功能：**
- ✅ Epic → Story → Task 三层任务拆分
- ✅ 自动识别依赖关系和关键路径
- ✅ 工时估算和优先级分配
- ✅ 双格式输出：
  - Markdown 清单（可导入 Jira/禅道）
  - Claude Code Plan（可直接执行）

---

### 🧪 test-designer - 测试用例设计技能

**工作流程：**

```mermaid
graph TD
    A[读取PRD] --> B[提取验收标准AC]
    B --> C[梳理测试点]
    C --> C1[正常流程]
    C --> C2[业务异常]
    C --> C3[边界值]
    C --> C4[安全性]
    C --> C5[幂等性]
    C --> C6[并发场景]
    C1 --> D[确认测试范围]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    C6 --> D
    D --> E[编写测试用例]
    E --> E1[用例编号]
    E --> E2[前置条件]
    E --> E3[测试步骤]
    E --> E4[预期结果]
    E1 --> F[安全测试用例]
    E2 --> F
    E3 --> F
    E4 --> F
    F --> F1[SQL注入]
    F --> F2[XSS攻击]
    F --> F3[越权访问]
    F1 --> G[幂等性测试用例]
    F2 --> G
    F3 --> G
    G --> G1[重复提交]
    G --> G2[网络重试]
    G1 --> H[质量检查]
    G2 --> H
    H --> I[输出用例表格]

    style A fill:#e1f5ff
    style I fill:#90EE90
    style H fill:#fff4e1
```

**核心功能：**
- ✅ 8大维度测试覆盖：正常/异常/边界/安全/幂等/并发/兼容/体验
- ✅ 自动生成安全测试用例（SQL注入、XSS、越权）
- ✅ 自动生成幂等性测试用例（重复提交、网络重试）
- ✅ 输出完整用例表格（含优先级、前置条件、测试步骤、预期结果）

---

### 📊 test-reporter - 测试报告撰写技能

**工作流程：**

```mermaid
graph TD
    A[收集测试数据] --> B[数据完整性检查]
    B --> C{数据是否完整?}
    C -->|否| D[向用户确认]
    D --> A
    C -->|是| E[计算核心指标]
    E --> E1[执行率]
    E --> E2[通过率]
    E --> E3[修复率]
    E1 --> F[缺陷分析]
    E2 --> F
    E3 --> F
    F --> F1[等级分布]
    F --> F2[分类分析]
    F --> F3[遗留说明]
    F1 --> G[准出评估]
    F2 --> G
    F3 --> G
    G --> G1[对照准出标准]
    G --> G2[计算达标率]
    G1 --> H[风险识别]
    G2 --> H
    H --> H1[技术风险]
    H --> H2[业务风险]
    H --> H3[时间风险]
    H1 --> I[质量改进建议]
    H2 --> I
    H3 --> I
    I --> J[输出测试报告]

    style A fill:#e1f5ff
    style J fill:#90EE90
    style G fill:#fff4e1
```

**核心功能：**
- ✅ 自动计算关键指标（执行率、通过率、修复率）
- ✅ 缺陷分析（P0-P3等级分布、分类统计）
- ✅ 准出评估（对照标准逐项检查）
- ✅ 风险评估（技术/业务/时间风险）
- ✅ 质量改进建议

---

## 🚀 快速开始

### 安装

**方式一：符号链接（推荐）**

```bash
# 克隆或下载本项目
git clone https://github.com/yourusername/enterprise-dev-flow.git

# 创建符号链接
ln -s $(pwd)/enterprise-dev-flow ~/.claude/skills/enterprise-dev-flow
```

**方式二：直接复制**

```bash
cp -r enterprise-dev-flow ~/.claude/skills/
```

### 验证安装

```bash
# 检查技能包
ls ~/.claude/skills/enterprise-dev-flow/skills/*/SKILL.md
```

### 使用命令

```bash
# 在 Claude Code 中使用
/prd:writing-prd          # 撰写PRD
/dev:writing-design       # 撰写设计文档
/dev:planning-tasks       # 拆分任务
/test:designing-cases     # 设计测试用例
/test:writing-report      # 撰写测试报告
```

### 自然语言触发

也可以直接用自然语言：

```
"帮我写一个用户登录功能的PRD"
"根据这个PRD写详细设计"
"帮我把这个需求拆成开发任务"
"设计登录功能的测试用例"
"测试完了，帮我出测试报告"
```

---

## 📚 使用示例

### 场景 1：产品经理撰写 PRD

```
👤 用户：帮我写一个用户登录功能的PRD

🤖 Claude：[自动触发 prd-writer 技能]
我会帮你按照企业级规范输出PRD。先确认几个关键问题：

1. 登录方式支持哪些？
   - 账号密码登录
   - 手机验证码登录
   - 第三方登录（微信/支付宝）

2. 是否需要记住登录状态？有效期多久？

3. 连续登录失败是否需要锁定账号？锁定时长？

4. 是否需要支持多端登录？（PC/移动端/小程序）
```

### 场景 2：研发人员撰写设计文档

```
👤 用户：根据这个PRD帮我写详细设计

🤖 Claude：[自动触发 design-writer 技能]
我会将PRD转化为技术设计方案。先确认：

1. 预期的并发用户数大概多少？（影响性能设计）
2. 是否有老用户数据需要迁移？（影响兼容性设计）
3. 是否需要支持灰度发布？（影响接口版本设计）

确认后我会输出：
✓ 时序图（Mermaid格式）
✓ 数据库DDL（PostgreSQL）
✓ 缓存设计（Redis Key规范）
✓ 接口文档（RESTful + 统一响应格式）
✓ 核心逻辑伪代码
```

### 场景 3：拆分开发任务

```
👤 用户：帮我把这个设计方案拆成开发任务

🤖 Claude：[自动触发 task-planner 技能]
我会输出两种格式的任务计划：

📋 格式一：项目管理清单（Markdown）
- Epic: 用户登录模块
  - Story: 账号密码登录
    - Task: 实现登录接口
    - Task: 设计用户表结构
    - Task: 编写登录单测
  - Story: 手机验证码登录
    ...

📝 格式二：Claude Code Plan
可直接交给 Claude Code 按步骤执行的实施计划
```

---

## 📂 项目结构

```
enterprise-dev-flow/
├── plugin.json                 # 插件配置
├── commands/                   # 命令别名（5个）
│   ├── prd/writing-prd.md
│   ├── dev/writing-design.md
│   ├── dev/planning-tasks.md
│   ├── test/designing-cases.md
│   └── test/writing-report.md
├── skills/                     # 核心技能（5个）
│   ├── prd-writer/
│   ├── design-writer/
│   ├── task-planner/
│   ├── test-designer/
│   └── test-reporter/
└── references/                 # 参考文档
    ├── common-rules.md        # 通用规范
    ├── prd-template.md        # PRD模板
    ├── design-template.md     # 设计模板
    ├── test-template.md       # 测试模板
    ├── api-design-rules.md    # API规范
    ├── git_commit_rules.md    # Git规范
    └── rules/                 # 细分规则库（25个）
        ├── security/          # 安全规则（2个）
        ├── database/          # 数据库规则（4个）
        ├── api/               # 接口规则（6个）
        ├── code-quality/      # 代码质量规则（4个）
        ├── git/               # Git规则（3个）
        ├── testing/           # 测试规则（3个）
        └── architecture/      # 架构规则（3个）
```

---

## 🎓 规则库

### 安全规则
- 安全红线（敏感信息保护、SQL安全、越权防护）
- 敏感数据脱敏规范

### 数据库规则
- 表命名规范（`t_{biz}_{scope}_{model_name}`）
- 通用字段规范（6个必填字段）
- 索引设计规范
- SQL红线（禁止SELECT *、深分页等）

### API规则
- RESTful设计规范
- 统一响应格式（Result<T>）
- URL命名规范
- 参数校验规范
- 分页查询规范
- 错误码规范

### 代码质量规则
- 幂等性设计
- 状态机规范
- 事务边界控制
- 异常处理规范

### Git规则
- Commit Message格式
- 分支命名规范
- 提交前检查清单

### 测试规则
- 缺陷等级标准（P0-P3）
- 验收标准格式（Given-When-Then）
- 测试覆盖矩阵

### 架构规则
- 非功能性需求基线
- 缓存策略（Redis）
- 消息队列设计（RocketMQ）

---

## 🔧 技术栈

本技能包专为以下技术栈设计：

| 类别 | 技术 |
|------|------|
| 后端框架 | Spring Cloud Alibaba |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 消息队列 | RocketMQ |
| 文件存储 | MinIO |

---

## 📖 文档

- [安装指南](INSTALL.md)
- [更新日志](CHANGELOG.md)
- [优化报告](OPTIMIZATION_REPORT.md)
- [规则重构总结](RULES_REFACTORING_SUMMARY.md)

---

## 🤝 贡献

欢迎贡献代码、提交问题或建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 维护者

**Enterprise Dev Team**

---

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

---

## 📮 联系方式

- 提交 Issue：[GitHub Issues](https://github.com/yourusername/enterprise-dev-flow/issues)
- 邮件联系：your-email@example.com

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by Enterprise Dev Team

</div>
