# Enterprise Product Development Workflow Skill Pack

<div align="center">

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/JianJang2017/jianjang-skills/tree/master/enterprise-dev-flow)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-%3E%3D1.0.0-orange.svg)](https://claude.ai/code)
[![Tech Stack](https://img.shields.io/badge/Spring%20Cloud%20Alibaba-✓-brightgreen.svg)](https://spring.io/projects/spring-cloud-alibaba)

English | [简体中文](README.md)

</div>

---

## 📖 Introduction

The Enterprise Product Development Workflow Skill Pack is an intelligent development assistant toolkit designed for **Claude Code**, covering the complete software development lifecycle from requirements analysis to testing and acceptance.

With 5 core skills, 25+ rule files, and 6 reference templates, it helps teams:
- ✅ Standardize Product Requirements Document (PRD) writing
- ✅ Normalize technical design documentation
- ✅ Automate task breakdown and planning
- ✅ Systematize test case design
- ✅ Professionalize test report generation

**Tech Stack:** Spring Cloud Alibaba + PostgreSQL + Redis + RocketMQ + MinIO

---

## ✨ Key Features

### 🎯 Full Lifecycle Coverage
Professional skill support for every stage from product requirements to testing acceptance, ensuring documentation consistency.

### 📚 Modular Rules
25+ granular rule files (security, database, API, code quality, Git, testing, architecture), centrally maintained and referenced on demand.

### 🔍 Automatic Quality Checks
Each skill includes built-in quality checklists, automatically validating compliance with enterprise standards before output.

### 🚀 Dual Format Output
Task planning skill outputs both project management lists (Markdown) and Claude Code Plans for different scenarios.

### 🛠️ Tech Stack Optimized
Specifically optimized for Spring Cloud Alibaba ecosystem with concrete technical implementation guidance.

---

## 🔄 Development Workflow

```mermaid
graph LR
    A[💡 Requirements] -->|prd-writer| B[📄 PRD]
    B -->|design-writer| C[🏗️ Design Doc]
    C -->|task-planner| D[📋 Task List]
    D -->|Development| E[✅ Features Done]
    B -->|test-designer| F[🧪 Test Cases]
    E --> F
    F -->|Execute Tests| G[📊 Test Data]
    G -->|test-reporter| H[📈 Test Report]
    H -->|Release Criteria| I[🚀 Launch]

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#ffe1f5
    style D fill:#e1ffe1
    style F fill:#f5e1ff
    style H fill:#ffe1e1
    style I fill:#90EE90
```

### Workflow Description

1. **Requirements Phase**: PM uses `prd-writer` to create standardized PRD
2. **Design Phase**: Developers use `design-writer` to transform PRD into technical design
3. **Planning Phase**: Use `task-planner` to break down tasks and generate dev plan
4. **Development Phase**: Dev team implements according to task list
5. **Test Preparation**: QA uses `test-designer` to design test cases based on PRD
6. **Test Execution**: Execute test cases and collect test data
7. **Test Summary**: Use `test-reporter` to generate test report
8. **Release Criteria**: Decide whether to launch based on test report

---

## 📦 Skill List

### 🎯 Skill Overview

| Skill | Trigger | Description |
|-------|---------|-------------|
| **prd-writer** | "write PRD", "organize requirements" | Guide PMs to output enterprise-grade PRDs with business architecture, features, NFRs, and acceptance criteria |
| **design-writer** | "write design doc", "how to design database" | Transform PRD into technical design with sequence diagrams, DDL, cache/MQ design, and API docs |
| **task-planner** | "break down tasks", "create dev plan" | Decompose PRD/design into executable tasks, output Epic/Story/Task list and Claude Code Plan |
| **test-designer** | "write test cases", "how to test this" | Systematically design test cases covering 8 dimensions: normal/exception/boundary/security/idempotency/concurrency |
| **test-reporter** | "write test report", "ready to launch?" | Generate test summary reports with case statistics, defect analysis, release criteria, and risk assessment |

---

### 📝 prd-writer - PRD Writing Skill

**Workflow:**

```mermaid
graph TD
    A[Receive Requirements] --> B{Info Complete?}
    B -->|No| C[Ask User Questions]
    C --> D[Collect Additional Info]
    D --> B
    B -->|Yes| E[Structure PRD Output]
    E --> F[Business Architecture]
    F --> G[Feature Details]
    G --> H[Data Dictionary]
    H --> I[Acceptance Criteria]
    I --> J[Non-Functional Requirements]
    J --> K[Quality Check]
    K --> L{Pass?}
    L -->|No| M[Fix Issues]
    M --> K
    L -->|Yes| N[Output Final PRD]

    style A fill:#e1f5ff
    style N fill:#90EE90
    style K fill:#fff4e1
```

**Key Features:**
- ✅ Guided questioning for requirement completeness
- ✅ Auto-check security red lines and idempotency design
- ✅ Generate Given-When-Then format acceptance criteria
- ✅ Output enterprise-standard complete PRD

---

### 🏗️ design-writer - Design Documentation Skill

**Workflow:**

```mermaid
graph TD
    A[Read PRD] --> B[Requirement Analysis & Risk ID]
    B --> C[Architecture Design]
    C --> C1[Draw Sequence Diagram]
    C --> C2[Define Layered Architecture]
    C1 --> D[Data Model Design]
    C2 --> D
    D --> D1[Database Table Design]
    D --> D2[Cache Design Redis]
    D --> D3[Message Queue Design MQ]
    D1 --> E[API Design]
    D2 --> E
    D3 --> E
    E --> E1[RESTful API]
    E --> E2[Unified Response Format]
    E --> E3[Parameter Validation]
    E1 --> F[Core Logic Design]
    E2 --> F
    E3 --> F
    F --> F1[Concurrency Control]
    F --> F2[Transaction Boundary]
    F --> F3[Idempotency Implementation]
    F1 --> G[Security Design Check]
    F2 --> G
    F3 --> G
    G --> H[Output Design Doc]

    style A fill:#e1f5ff
    style H fill:#90EE90
    style G fill:#fff4e1
```

**Key Features:**
- ✅ Generate Mermaid sequence diagrams
- ✅ PostgreSQL DDL scripts
- ✅ Redis cache design (key conventions, consistency)
- ✅ RocketMQ message design (topic naming, idempotent consumption)
- ✅ RESTful API docs (with request/response examples)
- ✅ Concurrency control, transaction boundary, idempotency solutions

---

### 📋 task-planner - Task Planning Skill

**Workflow:**

```mermaid
graph TD
    A[Read PRD/Design Doc] --> B{Info Sufficient?}
    B -->|No| C[Confirm with User]
    C --> D[Supplement Tech Details]
    D --> B
    B -->|Yes| E[Identify Core Modules]
    E --> F[Build Task Hierarchy]
    F --> F1[Epic Level]
    F --> F2[Story Level]
    F --> F3[Task Level]
    F1 --> G[Map Dependencies]
    F2 --> G
    F3 --> G
    G --> H[Estimate Effort]
    H --> I[Assign Priority]
    I --> J{Output Format?}
    J -->|Project Mgmt| K[Markdown List]
    J -->|Claude Code| L[Plan Format]
    K --> M[Output Task Plan]
    L --> M

    style A fill:#e1f5ff
    style M fill:#90EE90
    style J fill:#fff4e1
```

**Key Features:**
- ✅ Epic → Story → Task three-level breakdown
- ✅ Auto-identify dependencies and critical path
- ✅ Effort estimation and priority assignment
- ✅ Dual format output:
  - Markdown list (importable to Jira/Zendao)
  - Claude Code Plan (directly executable)

---

### 🧪 test-designer - Test Case Design Skill

**Workflow:**

```mermaid
graph TD
    A[Read PRD] --> B[Extract Acceptance Criteria]
    B --> C[Identify Test Points]
    C --> C1[Normal Flow]
    C --> C2[Business Exceptions]
    C --> C3[Boundary Values]
    C --> C4[Security]
    C --> C5[Idempotency]
    C --> C6[Concurrency]
    C1 --> D[Confirm Test Scope]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    C6 --> D
    D --> E[Write Test Cases]
    E --> E1[Case ID]
    E --> E2[Preconditions]
    E --> E3[Test Steps]
    E --> E4[Expected Results]
    E1 --> F[Security Test Cases]
    E2 --> F
    E3 --> F
    E4 --> F
    F --> F1[SQL Injection]
    F --> F2[XSS Attack]
    F --> F3[Unauthorized Access]
    F1 --> G[Idempotency Test Cases]
    F2 --> G
    F3 --> G
    G --> G1[Duplicate Submission]
    G --> G2[Network Retry]
    G1 --> H[Quality Check]
    G2 --> H
    H --> I[Output Case Table]

    style A fill:#e1f5ff
    style I fill:#90EE90
    style H fill:#fff4e1
```

**Key Features:**
- ✅ 8-dimension test coverage: normal/exception/boundary/security/idempotency/concurrency/compatibility/UX
- ✅ Auto-generate security test cases (SQL injection, XSS, unauthorized access)
- ✅ Auto-generate idempotency test cases (duplicate submission, network retry)
- ✅ Output complete case table (with priority, preconditions, steps, expected results)

---

### 📊 test-reporter - Test Report Skill

**Workflow:**

```mermaid
graph TD
    A[Collect Test Data] --> B[Data Completeness Check]
    B --> C{Data Complete?}
    C -->|No| D[Confirm with User]
    D --> A
    C -->|Yes| E[Calculate Key Metrics]
    E --> E1[Execution Rate]
    E --> E2[Pass Rate]
    E --> E3[Fix Rate]
    E1 --> F[Defect Analysis]
    E2 --> F
    E3 --> F
    F --> F1[Severity Distribution]
    F --> F2[Category Analysis]
    F --> F3[Remaining Issues]
    F1 --> G[Release Criteria Check]
    F2 --> G
    F3 --> G
    G --> G1[Compare with Standards]
    G --> G2[Calculate Compliance]
    G1 --> H[Risk Identification]
    G2 --> H
    H --> H1[Technical Risks]
    H --> H2[Business Risks]
    H --> H3[Timeline Risks]
    H1 --> I[Quality Improvement Suggestions]
    H2 --> I
    H3 --> I
    I --> J[Output Test Report]

    style A fill:#e1f5ff
    style J fill:#90EE90
    style G fill:#fff4e1
```

**Key Features:**
- ✅ Auto-calculate key metrics (execution rate, pass rate, fix rate)
- ✅ Defect analysis (P0-P3 severity distribution, category statistics)
- ✅ Release criteria check (item-by-item verification)
- ✅ Risk assessment (technical/business/timeline risks)
- ✅ Quality improvement suggestions

---

## 🚀 Quick Start

### Installation

**Method 1: Symbolic Link (Recommended)**

```bash
# Clone or download this project
git clone https://github.com/JianJang2017/jianjang-skills.git

# Create symbolic link
ln -s $(pwd)/jianjang-skills/enterprise-dev-flow ~/.claude/skills/enterprise-dev-flow
```

**Method 2: Direct Copy**

```bash
cp -r enterprise-dev-flow ~/.claude/skills/
```

### Verify Installation

```bash
# Check skill pack
ls ~/.claude/skills/enterprise-dev-flow/skills/*/SKILL.md
```

### Use Commands

```bash
# In Claude Code
/prd:writing-prd          # Write PRD
/dev:writing-design       # Write design doc
/dev:planning-tasks       # Break down tasks
/test:designing-cases     # Design test cases
/test:writing-report      # Write test report
```

### Natural Language Triggers

You can also use natural language:

```
"Help me write a PRD for user login"
"Write detailed design based on this PRD"
"Break down this requirement into dev tasks"
"Design test cases for login feature"
"Test is done, help me write the report"
```

---

## 📚 Usage Examples

### Scenario 1: PM Writing PRD

```
👤 User: Help me write a PRD for user login feature

🤖 Claude: [Automatically triggers prd-writer skill]
I'll help you output a PRD following enterprise standards.
Let me confirm some key questions:

1. Which login methods to support?
   - Username/password
   - Phone verification code
   - Third-party login (WeChat/Alipay)

2. Need to remember login state? How long?

3. Should account be locked after consecutive failed attempts? Lock duration?

4. Support multi-device login? (PC/Mobile/Mini-program)
```

### Scenario 2: Developer Writing Design Doc

```
👤 User: Write detailed design based on this PRD

🤖 Claude: [Automatically triggers design-writer skill]
I'll transform the PRD into technical design. Let me confirm:

1. Expected concurrent users? (affects performance design)
2. Need to migrate existing user data? (affects compatibility)
3. Need to support gradual rollout? (affects API versioning)

After confirmation, I'll output:
✓ Sequence diagram (Mermaid format)
✓ Database DDL (PostgreSQL)
✓ Cache design (Redis key conventions)
✓ API documentation (RESTful + unified response format)
✓ Core logic pseudocode
```

### Scenario 3: Breaking Down Tasks

```
👤 User: Break down this design into dev tasks

🤖 Claude: [Automatically triggers task-planner skill]
I'll output two formats of task plans:

📋 Format 1: Project Management List (Markdown)
- Epic: User Login Module
  - Story: Username/Password Login
    - Task: Implement login API
    - Task: Design user table structure
    - Task: Write login unit tests
  - Story: Phone Verification Login
    ...

📝 Format 2: Claude Code Plan
Implementation plan that Claude Code can execute step by step
```

---

## 📂 Project Structure

```
enterprise-dev-flow/
├── plugin.json                 # Plugin configuration
├── commands/                   # Command aliases (5)
│   ├── prd/writing-prd.md
│   ├── dev/writing-design.md
│   ├── dev/planning-tasks.md
│   ├── test/designing-cases.md
│   └── test/writing-report.md
├── skills/                     # Core skills (5)
│   ├── prd-writer/
│   ├── design-writer/
│   ├── task-planner/
│   ├── test-designer/
│   └── test-reporter/
└── references/                 # Reference docs
    ├── common-rules.md        # Common rules
    ├── prd-template.md        # PRD template
    ├── design-template.md     # Design template
    ├── test-template.md       # Test template
    ├── api-design-rules.md    # API guidelines
    ├── git_commit_rules.md    # Git conventions
    └── rules/                 # Granular rules (25)
        ├── security/          # Security rules (2)
        ├── database/          # Database rules (4)
        ├── api/               # API rules (6)
        ├── code-quality/      # Code quality rules (4)
        ├── git/               # Git rules (3)
        ├── testing/           # Testing rules (3)
        └── architecture/      # Architecture rules (3)
```

---

## 🎓 Rule Library

### Security Rules
- Security red lines (sensitive data protection, SQL security, authorization)
- Sensitive data masking standards

### Database Rules
- Table naming convention (`t_{biz}_{scope}_{model_name}`)
- Common fields standard (6 mandatory fields)
- Index design guidelines
- SQL red lines (no SELECT *, no deep pagination, etc.)

### API Rules
- RESTful design guidelines
- Unified response format (Result<T>)
- URL naming conventions
- Parameter validation standards
- Pagination query standards
- Error code conventions

### Code Quality Rules
- Idempotency design
- State machine specifications
- Transaction boundary control
- Exception handling standards

### Git Rules
- Commit message format
- Branch naming conventions
- Pre-commit checklist

### Testing Rules
- Defect severity levels (P0-P3)
- Acceptance criteria format (Given-When-Then)
- Test coverage matrix

### Architecture Rules
- Non-functional requirements baseline
- Cache strategy (Redis)
- Message queue design (RocketMQ)

---

## 🔧 Tech Stack

This skill pack is designed for the following tech stack:

| Category | Technology |
|----------|------------|
| Backend Framework | Spring Cloud Alibaba |
| Database | PostgreSQL |
| Cache | Redis |
| Message Queue | RocketMQ |
| File Storage | MinIO |

---

## 📖 Documentation

- [Installation Guide](INSTALL.md)
- [Changelog](CHANGELOG.md)
- [Optimization Report](OPTIMIZATION_REPORT.md)
- [Rules Refactoring Summary](RULES_REFACTORING_SUMMARY.md)

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork this project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

---

## 👥 Maintainers

**Enterprise Dev Team**

---

## 🙏 Acknowledgments

Thanks to all contributors who have helped this project!

---

## 📮 Contact

- Submit Issues: [GitHub Issues](https://github.com/JianJang2017/jianjang-skills/issues)
- Email: jianjang2017@gmail.com

---

<div align="center">

**If this project helps you, please give it a ⭐️ Star!**

Made with ❤️ by Enterprise Dev Team

</div>
