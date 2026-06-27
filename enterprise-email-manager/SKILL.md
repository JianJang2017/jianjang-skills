---
name: enterprise-email-manager
description: 企业邮箱管理工具，用于备份邮箱内容到本地、删除邮件、发送模版邮件、生成每日邮件汇总报告等操作。当用户提到"邮箱备份"、"导出邮件"、"批量删除邮件"、"发送模版邮件"、"邮件管理"、"清理邮箱"、"邮件归档"、"EML导出"、"邮件批量处理"、"邮件汇总报告"、"每日邮件汇总"、"邮件优先级分析"、"邮件统计"或需要对企业邮箱进行自动化管理时触发。支持IMAP/SMTP协议，可按时间、发件人、主题等多种条件筛选邮件，支持附件备份和模版变量替换。即使用户没有明确提到"技能"或"企业邮箱管理器"，只要涉及邮件的自动化处理、批量操作、备份、清理或汇总分析，都应该使用本技能。
---

# 企业邮箱管理技能

帮助用户自动化管理企业邮箱，包括邮件备份、批量删除、模版发送等功能。

## 前提条件

使用本技能前，必须确保 `.env` 文件已配置邮箱凭证。如果不存在，创建 `.env` 文件并添加：

```bash
# 邮箱服务器配置
EMAIL_ADDRESS=your-email@company.com
EMAIL_PASSWORD=your-password-or-app-token
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

> 邮箱服务器配置是所有功能的必填项；签名/公司信息仅在发送模板邮件时使用，可按需填写。完整模板见 `.env.example`。

⚠️ **安全提醒**：`.env` 文件已在 `.gitignore` 中，不会被提交到 git。请妥善保管密码。

---

## 核心功能

### 1. 邮件备份

将邮箱中的邮件导出为 EML 格式到本地，支持按条件筛选和分文件夹保存。

**支持的筛选条件**：
- 时间范围：`since="2026-01-01"` 或 `before="2026-06-01"`
- 发件人：`sender="boss@company.com"`
- 主题关键词：`subject="项目报告"`
- 是否已读：`seen=True` 或 `seen=False`
- 指定文件夹：`folder="工作"`（默认为 `INBOX`）
- **递归搜索所有文件夹**：`--all-folders`（需配合 `--from-match` 或 `--subject-match` 使用）

**使用方式**：

调用 `scripts/backup_emails.py`，传入筛选参数。脚本会自动：
- 连接到 IMAP 服务器
- 根据条件搜索邮件
- 按邮箱文件夹结构创建本地目录
- 将每封邮件保存为 `.eml` 文件
- 下载并保存附件到 `attachments/` 子目录

**示例**：

```bash
# 备份所有邮件
python scripts/backup_emails.py --output ./email_backup

# 备份最近 30 天的邮件
python scripts/backup_emails.py --since "30 days ago" --output ./recent_emails

# 备份特定发件人的邮件
python scripts/backup_emails.py --sender "manager@company.com" --output ./manager_emails

# 备份包含特定关键词的邮件
python scripts/backup_emails.py --subject "季度报告" --output ./reports

# 备份指定文件夹
python scripts/backup_emails.py --folder "项目A" --output ./project_a_emails

# 递归搜索所有文件夹，备份某个发件人的全部邮件（不管在哪个文件夹）
python scripts/backup_emails.py --from-match "boss@company\.com" --all-folders --output ./boss_all_emails
```

---

### 2. 删除邮件

批量删除符合条件的邮件。删除是不可逆操作（尤其是永久删除），所以脚本设计了安全机制。

**两种删除模式**：
- **移到垃圾箱**（默认，可恢复）：`--mode trash`，邮件移动到垃圾箱文件夹
- **永久删除**（不可恢复）：`--mode permanent`，直接从服务器删除

**安全机制——先预览，再删除**：

删除前必须先用 `--dry-run` 预览将要删除的邮件，把列表展示给用户确认后，再执行实际删除。这能避免误删重要邮件。永久删除属于高风险操作，执行前一定要让用户明确确认。

**两种筛选方式**——选对方式很关键：

- **服务端搜索**（`--sender` / `--subject`）：速度快，但 IMAP 服务器的子串搜索经常漏掉变体。比如搜 `--sender noreply`，能匹配到 `notice-noreply@x.com`，却漏掉 `no-reply@x.com`（带连字符）。适合发件人地址精确已知的场景。
- **客户端正则扫描**（`--from-match` / `--subject-match`）：先取回全部邮件头再用正则匹配，更可靠、更全面。清理 newsletter、推广、no-reply 这类"模糊一类"邮件时，**优先用这个**。

其余筛选条件（时间、已读状态、文件夹）与备份相同，可与上面任一方式组合。**当邮件可能被邮箱规则自动分类到不同文件夹时，加 `--all-folders` 递归搜索全部文件夹**（需配合 `--from-match` 或 `--subject-match` 使用）。

**示例**：

```bash
# 清理各种 noreply 变体（推荐用正则扫描，能覆盖 no-reply / noreply / no_reply）
python scripts/delete_emails.py --from-match "no.?reply" --dry-run

# 发件人地址精确已知时，用服务端搜索更快
python scripts/delete_emails.py --sender "newsletter@spam.com" --dry-run

# 递归搜索所有文件夹，删除某个发件人的全部邮件（不管在哪个文件夹）
python scripts/delete_emails.py --from-match "zhgl\.info@aliyun\.com" --all-folders --dry-run

# 用户确认后，移到垃圾箱
python scripts/delete_emails.py --from-match "no.?reply" --mode trash

# 删除一年前的已读邮件（先预览）
python scripts/delete_emails.py --before "365 days ago" --seen --dry-run

# 永久删除（高风险，需用户明确确认）
python scripts/delete_emails.py --subject "测试邮件" --mode permanent

# 大批量删除（>500 封）在脚本/自动化环境中执行时，加 --yes 跳过交互确认
# （务必先 --dry-run 预览过；脚本会自动分批 + 断线重连，避免 IMAP 超时）
python scripts/delete_emails.py --since "2025-01-01" --before "2026-01-01" --mode permanent --yes
```

**工作流程（清理"一类"邮件时尤其重要）**：

1. 用户提出删除需求时，先运行 `--dry-run` 预览。清理 newsletter/推广这类模糊需求时，用 `--from-match` 正则扫描，覆盖面更全。
2. **审视预览结果，不要盲目全删**。预览按发件人分组输出，正是为了让你判断每一组属于哪一类。`noreply` 是个很宽的特征，匹配出来的往往混着三类性质完全不同的邮件：
   - **真正的推广/营销邮件**——通常是用户想删的
   - **账号验证/交易类邮件**（如"Verify your Email"、发票、密码重置）——删了可能影响账号找回，一般要保留
   - **公司内部系统通知**（如 CI/CD 构建告警 `xxx_noreply@本公司域名`）——多半是用户需要的，不该当 newsletter 删掉
3. 把分组后的列表和你的分类判断一起讲给用户，明确建议删哪些、保留哪些，而不是把匹配到的全部一删了事。
4. 用户确认后，针对确认要删的范围执行真正的删除（必要时收窄筛选条件，只删某几个发件人）。
5. 如果是永久删除，额外提醒不可恢复。

> 为什么强调分类：批量删除是不可逆的（永久删除尤甚）。一个 `noreply` 规则下，验证邮件和公司构建通知很容易被误伤。多花一步做分类判断，比删错后追悔莫及划算得多。

---

### 3. 邮件整理归类

按规则把邮件移动到指定文件夹，方便清理收件箱、建立分类体系。整理是"移动"而非删除——邮件不会丢失，只是换了个位置，所以比删除安全；但仍建议先 `--dry-run` 预览，确认归类范围符合预期。

脚本：`scripts/organize_emails.py`，有两个子命令：

- **`move`**：按单条规则整理（命令行指定条件 + 目标文件夹）
- **`batch`**：按 JSON 配置文件批量执行多条规则（适合定期清理）

**核心行为**：
- 目标文件夹不存在时**自动创建**
- 支持与删除/备份相同的筛选方式（`--from-match` / `--subject-match` 客户端正则、`--sender` / `--subject` 服务端搜索）
- 支持 `--all-folders` 从所有文件夹中找出符合条件的邮件统一归类（这点很关键：散落在各处的同类邮件可以一次收拢到一个文件夹）

**单条规则示例**：

```bash
# 预览：把所有"参会通知/会议变更"邮件归类到「会议-通知」（先看范围）
python scripts/organize_emails.py move --subject-match "参会通知|会议变更" --target "会议-通知" --dry-run

# 确认后执行：把某系统发件人的告警邮件从所有文件夹收拢到「系统监控」
python scripts/organize_emails.py move --from-match "zhgl\.info@aliyun\.com" --target "系统监控" --all-folders

# 把某发件人的邮件归类（仅在 INBOX 内）
python scripts/organize_emails.py move --sender "hr@company.com" --target "人力资源"
```

**批量规则示例**：

```bash
# 先预览所有规则的效果
python scripts/organize_emails.py batch --rules my_rules.json --dry-run

# 确认后执行
python scripts/organize_emails.py batch --rules my_rules.json
```

规则配置文件（JSON 数组，每条规则一个对象），参考 `assets/organize_rules_example.json`：

```json
[
  {
    "name": "整理系统告警",
    "from_match": "zhgl\\.info@aliyun\\.com",
    "target": "系统监控",
    "all_folders": true
  },
  {
    "name": "整理会议通知",
    "subject_match": "参会通知|会议变更",
    "target": "会议-通知",
    "all_folders": false
  }
]
```

字段说明：`name`（规则名，仅用于日志）、`from_match`/`subject_match`（至少有一个）、`target`（目标文件夹，必填）、`all_folders`（是否递归所有文件夹，默认 false）。

**工作流程**：
1. 用户提出整理需求时，先用 `--dry-run` 预览，把"哪些邮件 → 哪个文件夹"的清单展示给用户。
2. 整理是移动而非删除，相对安全，但如果归类范围很大或涉及重要邮件，仍要让用户确认后再执行。
3. 执行后告知用户实际移动了多少封、目标文件夹是否新建。

> 整理 vs 删除：整理只是换文件夹，可随时再移回来，比删除可逆。但 `--all-folders` 跨文件夹归类时，注意别把本就该留在某专属文件夹的邮件错误收拢走——预览时核对源文件夹分布。

---

### 4. 发送模版邮件

基于模版发送邮件，支持纯文本/HTML 格式、变量替换、批量发送和附件。

**模版机制**：

模版存放在 `assets/templates/` 目录，使用 `{{变量名}}` 作为占位符。脚本会用收件人数据替换占位符，实现个性化发送。

模版文件示例（`assets/templates/welcome.html`）：
```html
<p>尊敬的 {{name}}：</p>
<p>欢迎加入 {{company}}！您的工号是 {{employee_id}}。</p>
```

收件人数据可以是单个收件人（命令行参数）或批量收件人（CSV/JSON 文件）。

**示例**：

```bash
# 发送单封纯文本邮件
python scripts/send_template.py \
  --to "alice@company.com" \
  --subject "会议通知" \
  --template meeting.txt \
  --var name=Alice --var date=2026-06-20

# 发送 HTML 模版邮件
python scripts/send_template.py \
  --to "bob@company.com" \
  --subject "欢迎" \
  --template welcome.html \
  --var name=Bob --var company=示例公司 --var employee_id=12345

# 批量发送（从 CSV 读取收件人和变量）
python scripts/send_template.py \
  --recipients recipients.csv \
  --subject "{{name}}，您的月度报告" \
  --template monthly_report.html

# 带附件发送
python scripts/send_template.py \
  --to "team@company.com" \
  --subject "项目文档" \
  --template notice.html \
  --attach ./report.pdf --attach ./data.xlsx
```

**批量收件人 CSV 格式**（第一行为表头，列名对应模版变量）：
```csv
email,name,company,employee_id
alice@company.com,Alice,示例公司,12345
bob@company.com,Bob,示例公司,12346
```

**注意**：批量发送时，主题行也支持 `{{变量}}` 替换，可以实现每个收件人不同的主题。

---

### 5. 每日邮件汇总报告

自动分析指定时间范围内的邮件，按重要等级分类（紧急/重要/普通/低优先级），生成结构化的汇总报告。

**重要等级分类规则**：

- 🔴 **紧急 (Urgent)**: 
  - 标题包含"紧急"/"urgent"/"ASAP"/"立即"/"马上"等关键词
  - 来自VIP发件人（可配置）
  - 邮件头标记为高优先级

- 🟠 **重要 (Important)**: 
  - 包含附件
  - 抄送多人（>3人）
  - 需要今日内处理

- 🟢 **普通 (Normal)**: 
  - 常规工作邮件

- ⚪ **低优先级 (Low)**: 
  - 通知类邮件（标题含"通知"/"notification"）
  - 营销类邮件（含"订阅"/"广告"/"营销"/"unsubscribe"等）

**输出格式**：

1. **Markdown报告** - 纯文本，易于阅读和归档
2. **HTML可视化报告** - 带样式、统计图表，适合浏览器查看
3. **JSON结构化数据**（可选）- 供其他程序处理

**示例**：

```bash
# 生成今日邮件汇总（Markdown + HTML）
python scripts/daily_report.py --days 0 --output reports/today

# 生成最近7天的周报
python scripts/daily_report.py --days 7 --output reports/weekly

# 只生成HTML可视化报告
python scripts/daily_report.py --days 0 --format html --output reports/today

# 指定VIP发件人（自动标记为紧急）
python scripts/daily_report.py --days 0 \
  --vip-senders "boss@company.com,ceo@company.com" \
  --output reports/today

# 同时输出JSON数据
python scripts/daily_report.py --days 0 --json --output reports/today
```

**报告内容**：

- 📊 统计概览：按优先级分类的数量和占比
- 📧 详细列表：每封邮件的主题、发件人、时间、附件状态
- 🏷️ 智能标记：附件图标、抄送人数等元信息

**使用场景**：

- 每日早晨查看昨日或今日邮件概况
- 每周生成周报，回顾重要邮件
- 长假归来快速了解积压邮件
- 定时任务自动生成报告（可结合cron）

**定时任务示例**（每天早上8点生成昨日报告）：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（根据实际路径调整）
0 8 * * * cd /path/to/enterprise-email-manager && python scripts/daily_report.py --days 1 --output reports/$(date +\%Y-\%m-\%d) --vip-senders "boss@company.com"
```

---

### 6. 推送邮件汇总到飞书

将每日邮件汇总报告自动推送到飞书（个人消息或群聊），依赖 `lark-cli`。

**前置条件**：

```bash
# 安装飞书 CLI
npx @larksuite/cli@latest install

# 登录（按提示扫码或输入 token）
lark-cli auth login
```

**示例**：

```bash
# 推送今日汇总给自己
python scripts/push_feishu.py --days 0 --user-id "ou_xxx"

# 推送到团队群聊
python scripts/push_feishu.py --days 0 --chat-id "oc_xxx"

# 推送最近7天 + 设置VIP发件人
python scripts/push_feishu.py --days 7 --chat-id "oc_xxx" \
  --vip-senders "boss@company.com,ceo@company.com"

# 推送同时保存本地 Markdown 报告
python scripts/push_feishu.py --days 0 --user-id "ou_xxx" --save reports/today

# 预览模式（不实际发送，仅打印请求）
python scripts/push_feishu.py --days 0 --user-id "ou_xxx" --dry-run
```

**飞书消息内容**（Markdown 格式，自动优化）：

```
## 📧 邮件汇总报告 · 2026-06-22

时间范围: 今日  邮件总数: 45 封

| 等级      | 数量    | 说明      |
|-----------|---------|-----------|
| 🔴 紧急   | 3 封    | 需立即处理 |
| 🟠 重要   | 12 封   | 今日内处理 |
| 🟢 普通   | 25 封   | 常规处理   |
| ⚪ 低优先级 | 5 封   | 可延后处理 |

---
### 🔴 紧急邮件
1. **紧急：Q2财报审核截止今日** 📎
   发件人: `cfo@company.com`
...
```

**每日自动推送（cron）**：

```bash
# 每天早上 8:00 推送昨日汇总到群聊
0 8 * * * cd /path/to/enterprise-email-manager && python scripts/push_feishu.py --days 1 --chat-id "oc_xxx" --vip-senders "boss@company.com" 2>&1 | tee -a logs/feishu_push.log
```

> 如何获取 chat_id 或 user_id：
> - 用 `lark-cli im +chat-list` 查看群聊列表，找到 `chat_id`（oc_xxx）
> - 用 `lark-cli contact +search-user --query "姓名"` 查找用户的 `open_id`（ou_xxx）

---

## 脚本说明

| 脚本 | 功能 |
|------|------|
| `scripts/email_config.py` | 共享模块：加载 `.env` 配置、IMAP/SMTP 连接封装、文件夹列举 |
| `scripts/backup_emails.py` | 备份邮件为 EML 文件，含附件（支持 `--all-folders`） |
| `scripts/delete_emails.py` | 批量删除邮件（支持预览、垃圾箱、永久删除、`--all-folders`） |
| `scripts/organize_emails.py` | 邮件整理归类到指定文件夹（单条规则 `move` / 批量规则 `batch`） |
| `scripts/send_template.py` | 发送模版邮件（变量替换、批量、附件） |
| `scripts/daily_report.py` | **新增** 每日邮件汇总报告（按重要等级分类，支持Markdown/HTML输出） |
| `scripts/push_feishu.py` | **新增** 推送每日邮件汇总到飞书（支持用户/群聊，依赖 lark-cli） |

所有脚本都支持 `--help` 查看完整参数。脚本会自动从项目根目录的 `.env` 文件读取配置。

详细的中文搜索、编码处理等技术细节见 `references/imap-notes.md`。

飞书 CLI 的安装、认证、发消息、踩坑解法见 `references/feishu-cli-guide.md`。

---

## 注意事项

1. **凭证安全**：密码只存在 `.env` 中，永远不要把密码硬编码到脚本或打印到终端。脚本输出中不应出现密码明文。
2. **删除前必预览**：删除是危险操作，永久删除不可恢复。务必先 `--dry-run`，让用户确认后再删。
3. **中文编码**：企业邮件常含中文主题和发件人名，搜索和显示都要正确处理 RFC 2047 编码，脚本已封装好。
4. **连接稳定性**：备份大量邮件时可能超时，脚本支持断点续传（已备份的邮件会跳过）。
5. **批量发送频率**：批量发送时，部分企业邮箱服务器有频率限制，脚本默认在每封之间加短暂延时，避免被判为垃圾邮件。
6. **测试先行**：批量发送前，建议先发一封给自己验证模版渲染效果，确认无误再群发。

