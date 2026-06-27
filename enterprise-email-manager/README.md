# 企业邮件管理器 (Enterprise Email Manager)

企业邮件自动化管理工具包，支持 IMAP/SMTP 协议的邮件备份、删除、整理和批量发送功能。

## 快速开始

### 1. 环境要求

- Python 3.6+（仅使用标准库，无需安装第三方依赖）
- 支持 IMAP/SMTP 的企业邮箱账号

### 2. 配置邮箱凭证

复制配置模板并填写你的邮箱信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 邮箱服务器配置（必填）
EMAIL_ADDRESS=your.email@company.com
EMAIL_PASSWORD=your_password_or_app_token
IMAP_SERVER=mail.company.com
IMAP_PORT=993
SMTP_SERVER=mail.company.com
SMTP_PORT=465

# 邮件签名信息（用于通用模板 template.html，发送模板邮件时自动读取）
SENDER_NAME=张三
SENDER_TITLE=产品经理
SENDER_DEPARTMENT=技术部
SENDER_PHONE=18800000000
SENDER_ADDRESS=某某市某某区某某大厦

# 公司信息（用于模板页脚等）
COMPANY_NAME=示例公司
COMPANY_WEBSITE=www.example.com
COMPANY_ADDRESS=某某市某某区某某路1号
```

> 邮箱服务器配置是所有功能的必填项；签名/公司信息仅在发送模板邮件时使用，可按需填写。

> ⚠️ **安全提示**：`.env` 文件已在 `.gitignore` 中，不会被提交到版本控制

### 3. 核心功能

#### 📥 邮件备份

将邮箱中的邮件导出为标准 `.eml` 格式文件，支持断点续传、灵活过滤和数量控制。适用于邮件归档、数据迁移、离职交接等场景。

**基础用法：**

```bash
# 备份收件箱所有邮件
python scripts/backup_emails.py --output-dir my_backup

# 备份最近30天的邮件
python scripts/backup_emails.py --days 30 --output-dir my_backup

# 备份特定发件人的邮件（服务器端搜索）
python scripts/backup_emails.py --sender "boss@company.com" --output-dir backup

# 备份包含关键字的邮件
python scripts/backup_emails.py --subject "项目" --output-dir project_backup
```

**高级过滤：**

```bash
# 限制备份数量（前100封）
python scripts/backup_emails.py --sender "hr@company.com" --limit 100 --output-dir hr_backup

# 备份指定文件夹
python scripts/backup_emails.py --folder "已发送" --output-dir sent_backup

# 备份所有文件夹（包括子文件夹）
python scripts/backup_emails.py --all-folders --output-dir full_backup

# 组合条件：最近7天的重要邮件
python scripts/backup_emails.py --days 7 --sender "ceo@company.com" --output-dir important
```

**安全特性：**
- ✅ 自动分批处理（每批100封），避免内存溢出
- ✅ 备份超过1000封时显示警告并倒计时5秒，防止误操作
- ✅ 支持 `--limit` 参数精确控制备份数量
- ✅ 断点续传：已备份的邮件自动跳过（基于文件名）
- ✅ 实时进度显示（每10封更新一次）
- ✅ 备份文件名格式：`YYYYMMDD_HHMMSS_主题.eml`，便于排序和查找

**输出示例：**
```
my_backup/
├── 20260615_093045_项目进度汇报.eml
├── 20260614_150230_会议纪要.eml
└── 20260613_102015_周报.eml
```

#### 🗑️ 邮件删除

安全批量删除邮件，内置多重保护机制防止误删。支持服务器端搜索和客户端正则匹配两种模式。

**两步删除流程（强制）：**

```bash
# 第一步：预览要删除的邮件（必需）
python scripts/delete_emails.py --from-match "noreply|newsletter" --dry-run

# 第二步：确认无误后执行删除（移到垃圾箱，可恢复）
python scripts/delete_emails.py --from-match "noreply|newsletter"
```

**常用场景：**

```bash
# 删除营销邮件（客户端正则匹配）
python scripts/delete_emails.py --from-match "noreply|newsletter|promotion" --dry-run

# 删除特定发件人（服务器端搜索，速度更快）
python scripts/delete_emails.py --sender "spam@example.com" --dry-run

# 删除包含特定主题的邮件
python scripts/delete_emails.py --subject-match "抽奖|中奖|特惠" --dry-run

# 删除旧邮件（超过180天）
python scripts/delete_emails.py --older-than 180 --dry-run

# 永久删除（不可恢复，谨慎使用！）
python scripts/delete_emails.py --from-match "spam@" --permanent --dry-run
```

**服务器端搜索 vs 客户端匹配：**

| 参数 | 模式 | 速度 | 灵活性 | 适用场景 |
|------|------|------|--------|----------|
| `--sender` | 服务器端 | 快 | 精确匹配 | 删除特定邮箱地址 |
| `--from-match` | 客户端正则 | 慢 | 模糊匹配 | 删除 `noreply`、`no-reply`、`noreply123` 等变体 |
| `--subject` | 服务器端 | 快 | 包含匹配 | 删除包含特定关键字的主题 |
| `--subject-match` | 客户端正则 | 慢 | 正则匹配 | 删除符合复杂模式的主题 |

**安全特性：**
- 🛡️ **强制预览**：首次运行自动进入 `--dry-run` 模式
- 🛡️ **正则验证**：自动验证正则表达式语法，错误时给出友好提示和修复建议
- 🛡️ **数量警告**：删除超过500封时显示醒目警告，要求手动输入 `yes` 确认
- 🛡️ **分组预览**：按发件人分组显示待删除邮件，快速识别误删风险
- 🛡️ **永久删除保护**：`--permanent` 模式有明确的"不可恢复"警告和二次确认
- 🛡️ **默认可恢复**：普通删除模式仅移动到垃圾箱，可通过邮箱客户端恢复

**预览输出示例：**
```
🔍 DRY RUN 模式 - 仅预览，不会实际删除
======================================================================

从文件夹 'INBOX' 搜索邮件...
找到 156 封匹配的邮件

按发件人分组预览：
----------------------------------------------------------------------
📧 noreply@newsletter.com (89 封)
   - [2026-06-15] 每日资讯推送
   - [2026-06-14] 本周热门文章
   ...

📧 promotion@shop.com (67 封)
   - [2026-06-16] 限时优惠活动
   - [2026-06-13] 618大促预告
   ...

⚠️  移除 --dry-run 参数以实际执行删除操作
```

#### 📂 邮件整理

按规则自动移动邮件到指定文件夹，支持单条规则手动执行和批量规则自动化处理，提升邮箱管理效率。

**单条规则整理：**

```bash
# 按发件人整理
python scripts/organize_emails.py move --sender "hr@company.com" --target "人力资源"

# 按主题整理
python scripts/organize_emails.py move --subject "发票" --target "财务/发票"

# 按时间范围整理
python scripts/organize_emails.py move --days 30 --target "最近30天"

# 组合条件：将最近7天来自项目组的邮件移到项目文件夹
python scripts/organize_emails.py move --days 7 --sender "project@" --target "项目/本周"

# 预览模式（推荐先预览）
python scripts/organize_emails.py move --sender "newsletter@" --target "通讯" --dry-run
```

**批量规则整理（推荐）：**

创建规则配置文件 `organize_rules.json`：

```json
[
  {
    "name": "人力资源邮件",
    "sender": "hr@company.com",
    "target_folder": "人力资源"
  },
  {
    "name": "财务发票",
    "subject": "发票",
    "target_folder": "财务/发票"
  },
  {
    "name": "营销邮件",
    "from_match": "newsletter|promotion|noreply",
    "target_folder": "营销"
  },
  {
    "name": "项目组邮件",
    "sender": "project-team@company.com",
    "subject": "项目",
    "target_folder": "项目/讨论"
  }
]
```

执行批量整理：

```bash
# 按规则批量整理
python scripts/organize_emails.py batch --rules-file organize_rules.json

# 预览模式（推荐）
python scripts/organize_emails.py batch --rules-file organize_rules.json --dry-run
```

**规则配置说明：**

| 字段 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `name` | 是 | 规则名称（用于日志显示） | `"人力资源邮件"` |
| `target_folder` | 是 | 目标文件夹（自动创建） | `"人力资源"` 或 `"工作/项目A"` |
| `sender` | 否 | 发件人邮箱（服务器端精确匹配） | `"hr@company.com"` |
| `from_match` | 否 | 发件人正则匹配（客户端） | `"noreply\|newsletter"` |
| `subject` | 否 | 主题关键字（服务器端包含匹配） | `"发票"` |
| `subject_match` | 否 | 主题正则匹配（客户端） | `"RE:.*项目"` |
| `days` | 否 | 最近N天的邮件 | `30` |

> 💡 **提示**：多个条件之间是 **AND** 关系（同时满足）

**安全特性：**
- ✅ **正则验证**：自动验证正则表达式语法，提供修复建议
- ✅ **数量警告**：移动超过500封时显示警告并要求确认
- ✅ **预览模式**：支持 `--dry-run` 预览移动效果
- ✅ **自动创建文件夹**：目标文件夹不存在时自动创建
- ✅ **支持子文件夹**：使用 `/` 分隔，如 `"财务/发票"`
- ✅ **批量执行报告**：显示每条规则的执行结果和统计

**批量执行输出示例：**
```
执行规则 1/3: 人力资源邮件
  条件: sender=hr@company.com
  目标文件夹: 人力资源
  ✅ 成功移动 45 封邮件

执行规则 2/3: 财务发票
  条件: subject=发票
  目标文件夹: 财务/发票
  ✅ 成功移动 12 封邮件

执行规则 3/3: 营销邮件
  条件: from_match=newsletter|promotion
  目标文件夹: 营销
  ✅ 成功移动 203 封邮件

======================================================================
📊 批量整理完成
总规则数: 3 条
成功: 3 条
失败: 0 条
总移动邮件数: 260 封
```

#### 📧 模板批量发送

使用模板发送个性化邮件，支持 HTML/纯文本模板、变量替换、批量发送、附件、预览模式等功能。

**模板系统特性：**
- ✅ 支持 HTML 和纯文本模板
- ✅ 自动从 `.env` 读取发件人签名信息
- ✅ 嵌入公司 Logo（自动检测 `assets/images/logo.png`）
- ✅ 响应式设计，兼容 Gmail、Outlook、Apple Mail
- ✅ 专业的企业邮件样式（可自定义品牌色）

**模板变量系统：**

模板中使用 `{{variable_name}}` 语法引用变量。

*必需变量（需在命令中传入）：*
- `{{recipient_name}}` - 收件人姓名
- `{{content}}` - 邮件正文内容

*可选变量：*
- `{{subject}}` - 邮件主题
- `{{email_title}}` - 邮件标题（在正文中显示）

*自动变量（从 `.env` 自动读取，无需传入）：*
- `{{sender_name}}` - 发件人姓名
- `{{sender_title}}` - 职位
- `{{sender_department}}` - 部门
- `{{sender_email}}` - 邮箱
- `{{sender_phone}}` - 电话
- `{{sender_address}}` - 地址
- `{{company_name}}` - 公司名称
- `{{company_website}}` - 公司网站
- `{{company_address}}` - 公司地址

**配置签名信息（.env 文件）：**

```env
# 发件人签名信息
SENDER_NAME=张三
SENDER_TITLE=产品经理
SENDER_DEPARTMENT=技术部
SENDER_PHONE=18800000000
SENDER_ADDRESS=某某市某某区某某大厦

# 公司信息
COMPANY_NAME=示例公司
COMPANY_WEBSITE=www.example.com
COMPANY_ADDRESS=某某市某某区某某路1号
```

**使用示例：**

*1. 发送单封邮件*

```bash
python scripts/send_template.py single \
  --template assets/templates/template.html \
  --to "zhangsan@example.com" \
  --subject "项目进度更新" \
  --var recipient_name="张三" \
  --var email_title="本周项目进度汇报" \
  --var content="尊敬的领导：<br><br>本周项目进展顺利，已完成以下工作：<br>1. 完成需求分析<br>2. 完成原型设计<br>3. 启动开发工作"

# 使用纯文本模板
python scripts/send_template.py single \
  --template assets/templates/meeting.txt \
  --to "team@company.com" \
  --subject "周会通知" \
  --var recipient_name="各位同事" \
  --var content="本周例会改到周四下午2点"
```

*2. 批量发送（CSV 格式）*

创建 `recipients.csv` 文件：

```csv
email,recipient_name,email_title,content
user1@example.com,李四,关于会议通知,您好！定于明天下午2点在会议室召开项目评审会议。
user2@example.com,王五,关于培训安排,您好！下周将举办新员工培训，请准时参加。
```

发送邮件：

```bash
python scripts/send_template.py batch \
  --template assets/templates/template.html \
  --recipients recipients.csv \
  --subject "{{email_title}}"
```

*3. 批量发送（JSON 格式）*

创建 `recipients.json` 文件：

```json
[
  {
    "email": "user1@example.com",
    "recipient_name": "李四",
    "email_title": "关于会议通知",
    "content": "您好！<br><br>定于明天下午2点在会议室召开项目评审会议。"
  },
  {
    "email": "user2@example.com",
    "recipient_name": "王五",
    "email_title": "关于培训安排",
    "content": "您好！<br><br>下周将举办新员工培训，请准时参加。"
  }
]
```

发送邮件：

```bash
python scripts/send_template.py batch \
  --template assets/templates/template.html \
  --recipients recipients.json \
  --subject "{{email_title}}"
```

*4. 发送带附件的邮件*

```bash
python scripts/send_template.py single \
  --template assets/templates/template.html \
  --to "user@example.com" \
  --subject "月度报告" \
  --var recipient_name="领导" \
  --var content="请查收本月工作报告和数据分析" \
  --attach "report.pdf" \
  --attach "data.xlsx"
```

*5. 预览模式（推荐先预览）*

使用 `--dry-run` 参数预览邮件效果，不实际发送：

```bash
python scripts/send_template.py batch \
  --template assets/templates/template.html \
  --recipients recipients.csv \
  --subject "{{email_title}}" \
  --dry-run
```

**预览输出示例：**
```
======================================================================
📧 预览模式（不会实际发送邮件）
======================================================================

发件人: sender@example.com
收件人数量: 2
模板类型: HTML
包含嵌入Logo: 是

----------------------------------------------------------------------

【邮件 1/2】
收件人: user1@example.com
主题: 关于会议通知
变量: {
  'recipient_name': '李四',
  'email_title': '关于会议通知',
  'sender_name': '张三',
  'sender_title': '产品经理',
  ...
}

正文预览（前200字符）:
----------------------------------------------------------------------
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <title>关于会议通知</title>
  </head>
  <body>
    <table style="max-width: 600px;">
      <tr><td>尊敬的 李四：</td></tr>
...
----------------------------------------------------------------------

✅ 预览完成。移除 --dry-run 参数以实际发送。
```

*6. 控制发送速率*

```bash
# 批量发送时，每封邮件间隔3秒（避免被识别为垃圾邮件）
python scripts/send_template.py batch \
  --template assets/templates/template.html \
  --recipients recipients.csv \
  --subject "通知" \
  --delay 3
```

**模板结构说明：**

通用模板 `assets/templates/template.html` 的结构：

```
┌─────────────────────────────────────┐
│   顶部品牌条（蓝色 #0066cc）          │
├─────────────────────────────────────┤
│   Logo（公司标识，居中）             │
├─────────────────────────────────────┤
│   称呼：尊敬的 {{recipient_name}}：   │
│   ▎标题：{{email_title}}（左色条）   │
│   正文：{{content}}                  │
├─────────────────────────────────────┤
│   ▎签名卡片（浅蓝底 + 左侧色条）      │
│     ┌──────┬────────────────────┐   │
│     │ 姓名 │ {{sender_name}}     │   │
│     │ 职位 │ {{sender_title}}    │   │
│     │ 部门 │ {{sender_department}}│  │
│     │ 邮箱 │ {{sender_email}}    │   │
│     │ 电话 │ {{sender_phone}}    │   │
│     │ 地址 │ {{sender_address}}  │   │
│     └──────┴────────────────────┘   │
├─────────────────────────────────────┤
│   公司信息（蓝色背景 + 白字）         │
│   - 公司名称、网站、地址              │
├─────────────────────────────────────┤
│   免责声明（容器外小字）             │
└─────────────────────────────────────┘
```

整体采用圆角卡片设计（10px 圆角 + 柔和阴影），最大宽度 600px，
桌面与移动端自适应。布局变化：

- **响应式宽度**：桌面端固定 600px 居中；屏幕宽度 ≤600px（手机）时容器自动撑满全宽、去除圆角，内边距由 40px 收窄至 20px，字号略放大，阅读更舒适
- **内容自适应**：正文中的图片自动等比缩放不超出容器（`max-width:100%`），长链接/长单词自动换行，邮箱地址按字符断行，避免横向溢出撑破版面
- **标题**：增加左侧蓝色色条强调，视觉层次更清晰
- **签名区**：改为浅蓝底卡片 + 左侧色条，整体更紧凑
- **落款**：采用属性标签表格，左列为标签（姓名/职位/部门/邮箱/电话/地址），右列为对应值，中间以竖线分隔，整齐对齐
- **页脚**：从灰底改为蓝色品牌底 + 白字，强化品牌识别
- **预览文字**：新增隐藏的收件箱预览文字（显示 `email_title`）

**安全特性：**
- ✅ **预览模式**：`--dry-run` 参数预览邮件内容和变量替换结果
- ✅ **速率控制**：`--delay` 参数控制发送间隔（默认1秒）
- ✅ **批量限制**：建议分批发送大量邮件，避免被邮件服务器限流
- ✅ **变量验证**：自动检查必需变量是否提供
- ✅ **附件大小检查**：发送前验证附件是否存在
- ✅ **自动签名**：从 `.env` 读取，避免硬编码敏感信息

**常用模板：**
- `assets/templates/template.html` - 通用企业邮件模板（带 Logo 和签名）
- `assets/templates/welcome.html` - 欢迎邮件模板
- `assets/templates/meeting.txt` - 会议通知模板（纯文本）

**模板开发提示：**
1. HTML 模板中使用 `<br>` 标签换行，不要使用 `\n`
2. 使用 inline CSS，避免被邮件客户端过滤
3. 最大宽度设置为 600px，适配移动端
4. 使用 table 布局，兼容性最佳
5. 先发给自己测试，确认样式正确后再批量发送

---

#### 📊 每日邮件汇总报告

自动分析指定时间范围内的邮件，按重要等级智能分类，生成结构化的汇总报告。帮助您快速了解邮箱状态，优先处理重要邮件。

**核心特性：**
- 🎯 **智能分类**：按紧急、重要、普通、低优先级四级自动分类
- 📊 **可视化报告**：支持 Markdown 和 HTML 两种格式
- 📈 **统计分析**：邮件数量、占比、发件人分布一目了然
- 🔔 **VIP 识别**：配置 VIP 发件人，自动标记为紧急
- ⏰ **定时任务**：可配合 cron 实现每日自动生成

**分类规则：**

| 等级 | 图标 | 规则 | 建议处理时间 |
|------|------|------|-------------|
| 紧急 | 🔴 | 标题含"紧急"/"urgent"/"ASAP"，或来自VIP | 立即处理 |
| 重要 | 🟠 | 包含附件、抄送多人(>3)、标记为重要 | 今日内处理 |
| 普通 | 🟢 | 常规工作邮件 | 常规处理 |
| 低优先级 | ⚪ | 通知类、营销类邮件 | 可延后处理 |

**基础用法：**

*1. 生成今日邮件汇总*

```bash
python scripts/daily_report.py --days 0 --output reports/today
```

输出文件：
- `reports/today.md` - Markdown 文本报告
- `reports/today.html` - HTML 可视化报告（可在浏览器中打开）

*2. 生成最近7天的周报*

```bash
python scripts/daily_report.py --days 7 --output reports/weekly
```

*3. 只生成 HTML 报告*

```bash
python scripts/daily_report.py --days 0 --format html --output reports/today
```

*4. 配置 VIP 发件人（自动标记为紧急）*

```bash
python scripts/daily_report.py --days 0 \
  --vip-senders "boss@company.com,ceo@company.com,hr@company.com" \
  --output reports/today
```

*5. 同时输出 JSON 数据*

```bash
python scripts/daily_report.py --days 0 --json --output reports/today
```

生成 `reports/today.json`，包含结构化数据供其他程序处理。

*6. 指定文件夹分析*

```bash
# 分析"已发送"文件夹
python scripts/daily_report.py --days 7 --folder "已发送" --output reports/sent_weekly
```

**报告内容示例：**

```markdown
# 📧 邮件汇总报告

**报告日期**: 2026年06月22日 (今日)
**生成时间**: 2026-06-22 10:30:15
**邮件总数**: 45 封

---

## 📊 统计概览

| 优先级 | 数量 | 占比 |
|--------|------|------|
| 🔴 紧急 | 3 | 6.7% |
| 🟠 重要 | 12 | 26.7% |
| 🟢 普通 | 25 | 55.6% |
| ⚪ 低优先级 | 5 | 11.1% |

---

## 🔴 紧急邮件 (3 封)

*需立即处理*

### 1. 紧急：Q2财报审核截止今日 📎
- **发件人**: cfo@company.com
- **时间**: Mon, 22 Jun 2026 09:15:23 +0800

### 2. ASAP: 客户投诉需立即响应
- **发件人**: support@company.com
- **时间**: Mon, 22 Jun 2026 08:45:10 +0800 (抄送5人)

...
```

**HTML 报告特性：**
- 📱 **响应式设计**：支持桌面和移动设备
- 🎨 **可视化统计卡片**：四色卡片展示各优先级统计
- 🔍 **信息完整**：附件标记、抄送人数、元数据清晰展示
- 🎯 **专业设计**：现代化 UI，适合管理层查看

**定时任务配置：**

每天早上 8:00 自动生成昨日邮件报告：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（替换为实际路径）
0 8 * * * cd /path/to/enterprise-email-manager && python scripts/daily_report.py --days 1 --vip-senders "boss@company.com" --output reports/$(date +\%Y-\%m-\%d) 2>&1 | tee -a logs/daily_report.log
```

每周一早上 9:00 生成上周汇总：

```bash
0 9 * * 1 cd /path/to/enterprise-email-manager && python scripts/daily_report.py --days 7 --output reports/weekly-$(date +\%Y-\%W)
```

**使用场景：**
- ☀️ **每日晨报**：早晨查看昨日或今日邮件概况，优先处理紧急事项
- 📅 **周报/月报**：定期回顾重要邮件，避免遗漏
- 🏖️ **假期归来**：长假后快速了解积压邮件的重要程度
- 👔 **管理层汇报**：生成 HTML 报告提交给上级
- 🤖 **自动化监控**：配合定时任务，每日自动生成并存档

**高级配置：**

创建配置文件 `vip_config.json`：

```json
{
  "vip_senders": [
    "ceo@company.com",
    "boss@company.com",
    "board@company.com"
  ],
  "urgent_keywords": [
    "紧急", "urgent", "asap", "立即", "马上", "critical"
  ],
  "low_priority_keywords": [
    "通知", "newsletter", "订阅", "广告", "营销"
  ]
}
```

**报告输出目录建议：**

```
reports/
├── daily/
│   ├── 2026-06-22.md
│   ├── 2026-06-22.html
│   └── 2026-06-22.json
├── weekly/
│   ├── 2026-W25.md
│   └── 2026-W25.html
└── archive/
    └── 2026-Q2.zip
```

---

#### 🔔 推送到飞书

将每日邮件汇总报告自动推送到飞书（个人消息或群聊）。

**前置条件：**

```bash
# 安装飞书 CLI
npx @larksuite/cli@latest install

# 登录（扫码或输入 token）
lark-cli auth login

# 查找群聊 ID（oc_xxx）
lark-cli im +chat-list

# 查找用户 ID（ou_xxx）
lark-cli contact +search-user --query "张三"
```

**推送今日汇总：**

```bash
# 推送给自己
python scripts/push_feishu.py --days 0 --user-id "ou_xxx"

# 推送到群聊
python scripts/push_feishu.py --days 0 --chat-id "oc_xxx"

# 推送时设置 VIP 发件人（自动标记紧急）
python scripts/push_feishu.py --days 0 --chat-id "oc_xxx" \
  --vip-senders "boss@company.com,ceo@company.com"

# 推送同时保存本地报告
python scripts/push_feishu.py --days 0 --user-id "ou_xxx" --save reports/today

# 预览模式（不实际发送）
python scripts/push_feishu.py --days 0 --user-id "ou_xxx" --dry-run
```

**定时自动推送（cron）：**

```bash
# 每天早上 8:00 推送昨日汇总到群聊
0 8 * * * cd /path/to/enterprise-email-manager && \
  python scripts/push_feishu.py --days 1 --chat-id "oc_xxx" \
  --vip-senders "boss@company.com" 2>&1 | tee -a logs/feishu_push.log
```

**飞书消息预览（Markdown 格式）：**

```
📧 邮件汇总报告 · 2026-06-22

时间范围: 今日  邮件总数: 45 封

| 等级       | 数量   | 说明       |
|------------|--------|------------|
| 🔴 紧急    | 3 封   | 需立即处理  |
| 🟠 重要    | 12 封  | 今日内处理  |
| 🟢 普通    | 25 封  | 常规处理    |
| ⚪ 低优先级 | 5 封  | 可延后处理  |

🔴 紧急邮件
1. 紧急：Q2财报审核截止今日 📎
   发件人: cfo@company.com
```

---

#### 📋 列出邮箱文件夹

查看邮箱中所有可用的文件夹：

```bash
python scripts/email_config.py --list-folders
```

## 技术特性

- ✅ **中文支持**：完整支持中文邮件主题、发件人、文件夹名
- ✅ **安全设计**：删除操作强制预览，防止误删
- ✅ **断点续传**：备份支持中断恢复
- ✅ **灵活过滤**：支持服务端搜索和客户端正则表达式
- ✅ **批量操作**：支持 JSON 配置批量处理
- ✅ **零依赖**：仅使用 Python 标准库

## 目录结构

```
enterprise-email-manager/
├── README.md                    # 本文档
├── SKILL.md                     # 详细使用文档
├── .env                         # 邮箱凭证（不提交到 git）
├── .env.example                 # 配置模板
├── scripts/                     # 核心脚本
│   ├── email_config.py          # 配置和工具类
│   ├── backup_emails.py         # 邮件备份
│   ├── delete_emails.py         # 邮件删除
│   ├── organize_emails.py       # 邮件整理
│   └── send_template.py         # 模板发送
├── assets/                      # 资源文件
│   ├── templates/               # 邮件模板
│   └── organize_rules_example.json
├── evals/                       # 评测用例
└── references/                  # 参考文档
```

## 常见问题

### 邮件删除相关

**Q: 为什么删除操作显示"未找到邮件"？**

A: IMAP 服务器端搜索可能无法匹配所有变体（如 `noreply` vs `no-reply` vs `noreply123`）。使用客户端正则匹配：

```bash
# ✅ 推荐：使用正则匹配所有变体
python scripts/delete_emails.py --from-match "no-?reply" --dry-run

# ❌ 不推荐：服务器端精确匹配可能遗漏
python scripts/delete_emails.py --sender "noreply" --dry-run
```

**Q: 如何恢复误删的邮件？**

A: 普通删除模式（不带 `--permanent`）会将邮件移到垃圾箱，可通过邮箱客户端恢复：
1. 打开邮箱客户端（如 Outlook、Foxmail）
2. 进入"垃圾箱"或"已删除"文件夹
3. 选中邮件，点击"恢复"或拖回收件箱

**Q: 为什么正则表达式不生效？**

A: 检查正则表达式语法，常见问题：
- 忘记转义特殊字符：`info@` 应写为 `info@`（`@` 无需转义）
- 或运算符：使用 `|` 分隔，如 `noreply|newsletter|promotion`
- 可选字符：使用 `?`，如 `no-?reply` 匹配 `noreply` 和 `no-reply`

脚本会自动验证语法并给出修复建议。

### 邮件整理相关

**Q: 如何查看邮箱中有哪些文件夹？**

```bash
python scripts/email_config.py --list-folders
```

**Q: 子文件夹如何表示？**

A: 使用 `/` 分隔父子文件夹，脚本会自动创建不存在的文件夹：

```bash
python scripts/organize_emails.py move --sender "finance@" --target "工作/财务/发票"
```

**Q: 规则文件中的多个条件是什么关系？**

A: 同一条规则中的多个条件是 **AND** 关系（同时满足）。如果需要 **OR** 关系，创建多条规则：

```json
[
  {
    "name": "人力资源邮件-1",
    "sender": "hr@company.com",
    "target_folder": "人力资源"
  },
  {
    "name": "人力资源邮件-2",
    "sender": "recruitment@company.com",
    "target_folder": "人力资源"
  }
]
```

或使用正则表达式：

```json
{
  "name": "人力资源邮件",
  "from_match": "hr@|recruitment@",
  "target_folder": "人力资源"
}
```

### 邮件备份相关

**Q: 备份的 .eml 文件如何打开？**

A: `.eml` 文件是标准邮件格式，可以用以下方式打开：
- **macOS Mail**：双击直接打开
- **Outlook**：拖拽文件到 Outlook 窗口，或 文件 → 打开
- **Thunderbird**：文件 → 打开已保存的邮件
- **Foxmail**：拖拽到邮箱列表

**Q: 如何备份特定文件夹？**

A: 先列出所有文件夹，再指定要备份的文件夹：

```bash
# 列出所有文件夹
python scripts/email_config.py --list-folders

# 备份特定文件夹
python scripts/backup_emails.py --folder "已发送" --output-dir sent_backup
```

**Q: 断点续传如何工作？**

A: 脚本会检查输出目录中已存在的 `.eml` 文件，自动跳过同名文件。如果备份中断，再次运行相同命令即可继续。

### 模板发送相关

**Q: 如何避免发送邮件时被识别为垃圾邮件？**

1. 使用 `--delay` 参数控制发送间隔（建议 2-5 秒）
2. 分批发送，避免短时间大量发送（建议每批不超过 50 封）
3. 确保邮件内容不包含垃圾邮件特征词（如"中奖"、"免费"、"点击这里"）
4. 配置完整的发件人签名（`.env` 文件）
5. 使用企业邮箱而非个人邮箱

```bash
# 推荐：每封间隔3秒，避免被限流
python scripts/send_template.py batch \
  --template template.html \
  --recipients recipients.csv \
  --delay 3
```

**Q: 模板中的 Logo 不显示怎么办？**

A: 确保 `assets/images/logo.png` 文件存在。脚本会自动将其嵌入邮件（使用 `cid:company_logo` 引用）。

**Q: 签名信息为空或显示 `{{sender_name}}`？**

A: 检查 `.env` 文件是否包含签名信息配置：

```bash
# 查看 .env 文件
cat .env

# 应包含以下配置
SENDER_NAME=张三
SENDER_TITLE=产品经理
SENDER_DEPARTMENT=技术部
```

如果变量未被替换，说明 `.env` 中缺少对应配置。

**Q: HTML 标签在正文中显示为文本？**

A: 确保使用的是 HTML 模板（`.html` 后缀），而非纯文本模板（`.txt` 后缀）。HTML 模板支持以下标签：
- `<br>` - 换行
- `<strong>` / `<b>` - 加粗
- `<em>` / `<i>` - 斜体
- `<a href="...">` - 超链接
- `<ul>` / `<ol>` / `<li>` - 列表

**Q: 如何自定义模板样式？**

A: 直接编辑 `assets/templates/template.html` 文件：
1. 修改颜色：搜索 `#0066cc`（蓝色）并替换为你的品牌色
2. 修改 Logo：替换 `assets/images/logo.png`
3. 修改布局：编辑 HTML 和 inline CSS（使用 table 布局保证兼容性）

**Q: CSV 文件编码问题（中文乱码）？**

A: 确保 CSV 文件使用 UTF-8 编码保存：
- **Excel**：另存为 → CSV UTF-8（逗号分隔）
- **Numbers**：导出 → CSV → 高级选项 → UTF-8
- **文本编辑器**：保存时选择 UTF-8 编码

### 配置相关

**Q: 如何测试邮箱配置是否正确？**

```bash
# 列出文件夹（测试 IMAP 连接）
python scripts/email_config.py --list-folders

# 发送测试邮件（测试 SMTP 连接）
python scripts/send_template.py single \
  --template assets/templates/meeting.txt \
  --to "your_email@company.com" \
  --subject "配置测试" \
  --var recipient_name="测试" \
  --var content="这是一封测试邮件"
```

**Q: 常见的 IMAP/SMTP 端口配置？**

| 邮箱服务商 | IMAP 服务器 | IMAP 端口 | SMTP 服务器 | SMTP 端口 |
|-----------|------------|----------|------------|----------|
| 腾讯企业邮箱 | imap.exmail.qq.com | 993 | smtp.exmail.qq.com | 465 |
| 阿里企业邮箱 | imap.mxhichina.com | 993 | smtp.mxhichina.com | 465 |
| 网易企业邮箱 | imap.ym.163.com | 993 | smtp.ym.163.com | 465 |
| Gmail | imap.gmail.com | 993 | smtp.gmail.com | 465 |
| Outlook | outlook.office365.com | 993 | smtp.office365.com | 587 |

**Q: 提示"登录失败"怎么办？**

1. 检查 `.env` 中的邮箱地址和密码是否正确
2. 确认邮箱已启用 IMAP/SMTP 服务（在邮箱设置中开启）
3. 某些邮箱需要使用"应用专用密码"而非主密码：
   - 腾讯企业邮箱：设置 → 客户端专用密码
   - Gmail：Google 账号 → 安全性 → 应用专用密码
4. 检查网络连接和防火墙设置（端口 993/465 是否开放）

## 安全建议

- 🔒 **密码安全**：定期更换邮箱密码，使用应用专用密码代替主密码（如果邮箱支持）
- 🔒 **配置文件**：不要将 `.env` 文件提交到版本控制（已在 `.gitignore` 中配置）
- 🔒 **删除操作**：务必先用 `--dry-run` 预览，确认无误后再执行
- 🔒 **永久删除**：`--permanent` 参数会永久删除邮件（不可恢复），需谨慎使用
- 🔒 **批量操作**：建议先在测试邮箱或小范围测试，确认无误后再大规模使用
- 🔒 **备份重要邮件**：执行删除或整理操作前，先备份重要邮件
- 🔒 **权限控制**：不要在共享服务器上明文存储 `.env` 文件
- 🔒 **日志审查**：定期检查脚本输出日志，发现异常及时处理

## 最佳实践

### 邮件管理工作流

**1. 定期清理（每周）：**
```bash
# 步骤1：预览要删除的营销邮件
python scripts/delete_emails.py --from-match "noreply|newsletter|promotion" --dry-run

# 步骤2：确认后执行删除
python scripts/delete_emails.py --from-match "noreply|newsletter|promotion"

# 步骤3：删除旧邮件（超过90天）
python scripts/delete_emails.py --older-than 90 --from-match "notification" --dry-run
python scripts/delete_emails.py --older-than 90 --from-match "notification"
```

**2. 自动化整理（每月）：**
```bash
# 使用规则文件批量整理
python scripts/organize_emails.py batch --rules-file organize_rules.json --dry-run
python scripts/organize_emails.py batch --rules-file organize_rules.json
```

**3. 离职交接备份：**
```bash
# 备份所有文件夹的邮件
python scripts/backup_emails.py --all-folders --output-dir handover_backup_$(date +%Y%m%d)

# 备份特定项目邮件
python scripts/backup_emails.py --subject "项目A" --output-dir projectA_backup
```

**4. 发送批量通知：**
```bash
# 步骤1：准备收件人列表（CSV 或 JSON）
# 步骤2：预览邮件效果
python scripts/send_template.py batch \
  --template template.html \
  --recipients recipients.csv \
  --dry-run

# 步骤3：确认后发送（控制速率）
python scripts/send_template.py batch \
  --template template.html \
  --recipients recipients.csv \
  --delay 3
```

### 常见使用场景

**场景1：新员工入职欢迎邮件**
```bash
python scripts/send_template.py single \
  --template assets/templates/welcome.html \
  --to "newemployee@company.com" \
  --subject "欢迎加入公司" \
  --var recipient_name="张三" \
  --var email_title="欢迎加入我们的团队！" \
  --var content="欢迎加入公司！<br><br>请在入职第一天携带以下材料：<br>1. 身份证原件及复印件<br>2. 学历证明<br>3. 一寸照片2张<br><br>期待与您共事！"
```

**场景2：季度报告发送**
```bash
# 准备收件人列表 managers.csv
python scripts/send_template.py batch \
  --template assets/templates/template.html \
  --recipients managers.csv \
  --subject "Q2季度业务报告" \
  --attach "Q2_report.pdf" \
  --attach "Q2_data.xlsx" \
  --delay 2
```

**场景3：清理垃圾邮件**
```bash
# 1. 删除所有营销邮件
python scripts/delete_emails.py --from-match "noreply|newsletter|promo|marketing" --dry-run
python scripts/delete_emails.py --from-match "noreply|newsletter|promo|marketing"

# 2. 删除超过180天的通知邮件
python scripts/delete_emails.py --older-than 180 --subject-match "通知|提醒|notification" --dry-run
python scripts/delete_emails.py --older-than 180 --subject-match "通知|提醒|notification"
```

**场景4：项目邮件归档**
```bash
# 1. 备份项目邮件
python scripts/backup_emails.py \
  --subject "项目Alpha" \
  --output-dir projectAlpha_archive \
  --days 365

# 2. 整理到专用文件夹
python scripts/organize_emails.py move \
  --subject "项目Alpha" \
  --target "项目归档/Alpha"
```

**场景5：整理历史邮件**
```json
// organize_rules.json
[
  {
    "name": "人力资源",
    "from_match": "hr@|recruitment@|talent@",
    "target_folder": "人力资源"
  },
  {
    "name": "财务",
    "from_match": "finance@|accounting@",
    "target_folder": "财务"
  },
  {
    "name": "技术通知",
    "subject_match": "系统|服务器|故障|维护",
    "target_folder": "技术/系统通知"
  },
  {
    "name": "营销",
    "from_match": "newsletter|noreply|promotion",
    "target_folder": "营销"
  }
]
```

```bash
python scripts/organize_emails.py batch --rules-file organize_rules.json
```

### 性能优化建议

1. **使用服务器端搜索**：对于精确匹配（如特定邮箱地址），使用 `--sender` 而非 `--from-match`，速度更快
2. **限制处理范围**：使用 `--days` 参数限制时间范围，避免处理全部历史邮件
3. **分批处理**：对于大量邮件（超过10000封），建议分多次处理
4. **避免高峰期**：在非工作时间执行批量操作，减少对邮件服务器的影响
5. **使用 `--limit` 参数**：测试时使用小数量验证，确认无误后再处理全部

### 脚本组合使用

**示例1：清理并归档**
```bash
# 1. 备份要清理的邮件
python scripts/backup_emails.py --from-match "newsletter" --output-dir newsletter_archive

# 2. 删除邮件
python scripts/delete_emails.py --from-match "newsletter"
```

**示例2：整理后批量通知**
```bash
# 1. 整理项目邮件
python scripts/organize_emails.py move --subject "项目X" --target "项目X"

# 2. 发送整理完成通知
python scripts/send_template.py single \
  --template meeting.txt \
  --to "team@company.com" \
  --subject "邮件整理完成" \
  --var recipient_name="各位" \
  --var content="项目X相关邮件已整理到专用文件夹"
```

## 更多文档

详细使用说明请参考 [SKILL.md](SKILL.md)

## 技术支持

如遇问题，请检查：
1. `.env` 配置是否正确
2. 网络连接是否正常
3. IMAP/SMTP 端口是否开放（993/465）
4. 邮箱是否启用了 IMAP/SMTP 服务
