---
name: classical-poetry-learning
description: 创建和审校面向儿童、家长、教师及公众号读者的古诗词学习内容，支持中文或中英双语赏析、分龄讲解、课内考点、配图与封面、公众号 HTML、草稿创建和正式发布。当用户要讲解/赏析某首古诗词、制作亲子或备考材料、核查现有诗词文章、给诗词内容配图、生成公众号封面、转换公众号 HTML、创建公众号草稿或发布文章时使用。支持完整流程（写作→配图→HTML→发布）和单独步骤。支持批量处理多首诗词。即使用户只说”给孩子讲《静夜思》””检查这篇诗词赏析是否准确””把这篇发到公众号草稿箱””批量生成小学必背20首”也应触发。不要用于现代诗、一般文学创作或与古诗词无关的公众号排版。
---

# 古诗词学习内容创作

把古诗词材料做成准确、分龄、可讲、可复习、可发布的成品。先识别用户意图，只读取当前路径需要的 reference；不要为一次简单赏析加载整套生图和发布说明。

## 意图路由

一次请求可以组合多个意图，按表中顺序执行；后一步以前一步产物为输入。

**智能流程编排**：当用户请求包含完整流程（如"写《静夜思》，配图，发布到公众号"）时：

1. 识别完整意图并规划流程
   ```
   检测到完整流程请求
   
   📋 流程清单
   □ 1. 写作 (预计3分钟)
   □ 2. 配图 (预计12分钟)
       - 封面图
       - 意境图
       - 场景图
   □ 3. HTML转换 (预计2分钟)
   □ 4. 发布 (预计3分钟)
   
   总预计时间：20分钟
   关键确认点：3个（配图风格、HTML主题、发布确认）
   
   开始执行...
   ```

2. 创建 TaskList 显示所有阶段
3. 在关键批准点暂停确认（使用 AskUserQuestion）
4. 阶段间自动衔接，提供清晰选项
5. 最后提供完整交付报告

**单阶段路由**：

| 意图 | 主要产物 | 必读文件 | 授权边界 |
|---|---|---|---|
| 创作/改写 | Markdown 学习文章 | 对应语言模板 | 可直接执行 |
| 审校现有文章 | 问题清单或修订稿 | `references/content-review.md` | 未要求修改时只报告 |
| 配图/封面 | prompt 文件与图片 | `ILLUSTRATION_GUIDE.md` | 生成前确认关键视觉选择；用户明确“直接生成”可跳过 |
| 转公众号 HTML | 预览稿与发布稿 | `references/themes/index.md` + 选中的一个主题 | 可直接生成本地文件 |
| 创建公众号草稿 | 微信草稿 `media_id` | `references/publishing-workflow.md` | 先 dry-run；建草稿无需正式发布授权 |
| 正式发布 | 发布任务 `publish_id` | `references/publishing-workflow.md` | 当前对话中明确确认后才能执行 |

只问方法时回答方法；要求创作或修改时直接产出文件并验证。信息不足但有安全默认值时说明假设后继续；只有缺失信息会改变目标读者、版本或外部影响时才提问。

## 默认值

- 语言：中文 `zh_cn`；用户明确要求双语或 `--lang=zh_cn,en_us` 时生成中英双语。
- 读者：用户未给年龄时按“小学中高年级亲子共读”处理，并在交付中声明。
- 输出：Markdown；文件名为 `《诗词名》_古诗词鉴赏_中文版.md` 或 `《诗词名》_古诗词鉴赏_双语版.md`。
- 扩展模块：默认不加；只有内容确实需要时选 0–2 个。
- 公众号：默认只建草稿，不正式发布。

## 工作空间管理

**所有生成的内容自动组织到专属工作空间**，便于后期处理和归档：

### 工作空间结构

在当前工作目录下创建统一的 `release/` 目录（**已存在则复用，不新建**），每首诗词是其下的一个子目录：`release/<诗词名>/`

```
release/
├── 静夜思/
│   ├── .workflow-state.json           # 流程状态（自动生成）
│   ├── 《静夜思》_古诗词鉴赏_中文版.md   # 推文内容
│   ├── poem-metadata.json              # 诗词元数据（诗名、作者、朝代、诗句）
│   ├── imgs/
│   │   ├── prompts/                    # AI 绘图 prompt 文件
│   │   │   ├── 00-cover.md            # 封面 prompt
│   │   │   ├── 01-scene.md            # 意境图 prompt
│   │   │   └── 02-background.md       # 背景图 prompt
│   │   ├── cover-background.png       # 封面无字底图
│   │   ├── cover.png                  # 封面成品（含文字）
│   │   ├── illustration-01.png        # 配图1
│   │   └── illustration-02.png        # 配图2
│   ├── html/
│   │   ├── preview.html               # 预览稿（含封面）
│   │   └── publish.html               # 发布稿（无封面）
│   └── published/
│       ├── draft-info.json            # 草稿箱信息（media_id 等）
│       └── publish-info.json          # 发布信息（publish_id、URL）
└── 春晓/
    └── ...（同上结构）
```

### 工作空间初始化

**首次提到某首诗词时**，自动创建工作空间：

1. 确保根目录 `release/` 存在（已存在则复用，不重复创建）
2. 在其下创建诗词目录：`release/<诗词名>/`
3. 初始化 `.workflow-state.json`：
   ```json
   {
     "poem": "静夜思",
     "author": "李白",
     "dynasty": "唐",
     "workflow_id": "20260719-001",
     "created_at": "2026-07-19T10:30:00Z",
     "stages": {
       "writing": {"status": "pending"},
       "illustration": {"status": "pending"},
       "html_conversion": {"status": "pending"},
       "publishing": {"status": "pending"}
     },
     "next_action": "开始创作内容",
     "last_error": null
   }
   ```

### 路径解析规则

所有文件路径遵循统一规范：

- **工作空间根目录**：`./release/`（当前工作目录下；已存在则复用，不新建）
- **诗词子目录**：`./release/<诗词名>/`
  - 诗词名自动清理：去除书名号、空格、特殊字符
  - 示例：`《静夜思》` → `静夜思`、`登鹳雀楼（王之涣）` → `登鹳雀楼`
- **内容文件**：始终放在诗词子目录下
- **图片目录**：`imgs/`（统一小写）
- **HTML 目录**：`html/`
- **发布信息**：`published/`

### 自动化行为

每个阶段完成后，自动更新工作空间：

1. **写作阶段**：
   - 保存 Markdown 到诗词目录
   - 生成 `poem-metadata.json`（从 frontmatter 提取）
   - 更新 `.workflow-state.json`：`writing.status = "completed"`

2. **配图阶段**：
   - 创建 `imgs/prompts/` 保存所有 prompt 文件
   - 生成的图片保存到 `imgs/`，命名规范化
   - 更新 `.workflow-state.json`：记录已生成的图片清单

3. **HTML 转换**：
   - 创建 `html/` 目录
   - 保存预览稿和发布稿
   - 更新图片引用为相对路径（`../imgs/xxx.png`）

4. **发布阶段**：
   - 创建 `published/` 目录
   - 保存草稿/发布元信息（media_id、publish_id、URL）

### 恢复与继续

用户说"继续"、"恢复"、"接着做"时：

1. 扫描当前目录下的 `release/`
2. 查找最近修改的 `.workflow-state.json`（按 mtime 排序）
3. 读取 `next_action`，自动恢复到中断点
4. 提示用户：
   ```
   检测到未完成的工作：《静夜思》
   
   已完成：✅ 写作  ✅ 配图（2/3）
   待完成：⏳ 封面图  ⏳ HTML 转换  ⏳ 发布
   
   继续生成封面图？
   ```

### 批量处理

批量处理时，每首诗词独立工作空间，互不干扰：

```bash
# 用户提供诗词清单
cat > poem-list.txt <<EOF
静夜思
春晓
登鹳雀楼
EOF

# 结果自动组织
release/
├── 静夜思/（完整产物）
├── 春晓/（完整产物）
└── 登鹳雀楼/（完整产物）
```

并发处理时，`.workflow-state.json` 加锁避免冲突。

### 交付清单

每次完成时，生成交付清单：

```
✅ 《静夜思》创作完成

📁 工作空间：./release/静夜思/
📄 内容文件：《静夜思》_古诗词鉴赏_中文版.md (3.2 KB)
🖼️ 配图：3 张（cover.png, illustration-01.png, illustration-02.png）
📋 元数据：poem-metadata.json
🌐 HTML：preview.html, publish.html
📮 草稿箱：已创建（media_id: xxxxx）

下一步：
- 在微信公众号后台预览草稿
- 修改后重新生成 HTML：直接编辑 Markdown，再转一次
- 发布：明确确认后执行
```

## 工作流

**进度可视化**：对于多步骤流程（内容创作 + 配图 + HTML + 发布），使用 TaskCreate/TaskUpdate 工具显示进度，让用户了解当前状态和剩余工作。

**流程恢复**：每个工作空间创建 `.workflow-state.json` 记录流程状态

示例 - 流程状态文件：
```json
{
  "poem": "静夜思",
  "workflow_id": "20260718-001",
  "stages": {
    "writing": {"status": "completed", "output": "content.md"},
    "illustration": {"status": "in_progress", "style": "warm-scene"},
    "html_conversion": {"status": "pending"},
    "publishing": {"status": "pending"}
  },
  "next_action": "继续生成配图",
  "last_error": null
}
```

**错误恢复机制**：
- 检测工作空间中的 `.workflow-state.json`
- 用户说"继续"时，从 `next_action` 恢复
- 失败时记录 `last_error`，提供恢复选项：
  ```
  封面生成失败 (超时)
  
  恢复选项：
  (A) 重试 - 使用相同参数
  (B) 修改 prompt 后重试
  (C) 跳过封面，继续配图
  (D) 从头开始
  ```

**批量处理模式**：检测到批量请求时启用

示例 - 诗词列表文件 `poem-list.txt`：
```
静夜思
春晓
登鹳雀楼
```

批量执行流程：
1. 读取列表，确认诗词和配置
2. 为每首诗创建独立工作空间
3. 使用 TaskList 显示总体进度
4. 每完成一首，更新进度并报告
5. 最后生成汇总报告

批量配置：
- 统一目标年级、语言版本
- 统一配图风格（或每首独立选择）
- 统一 HTML 主题

**时间预期管理**：在开始耗时操作前告知预计时间
- 写作：2-5 分钟
- 配图：10-15 分钟（3张图）
  - 长时间操作使用 `run_in_background: true`
  - 每30-60秒报告一次进度
  - 示例：
    ```
    ⏳ 配图生成中
    
    当前：生成封面图
    进度：███████░░░ 70%
    已用时间：4分钟
    预计剩余：2分钟
    
    [提示：输入"取消"可停止生成]
    ```
- HTML转换：1-2 分钟
- 发布：2-3 分钟

**阶段衔接**：每个阶段完成后，主动提示下一步并提供选项

示例 - 写作完成后：
```
✓ 写作完成

📄 查看：《静夜思》_workspace/content.md

下一步建议：
• "生成配图" - 制作封面和配图（预计12分钟）
• "转换HTML" - 无图版公众号排版（预计2分钟）
• "修改内容" - 调整后再继续

你想继续哪一步？
```

示例 - 配图完成后：
```
✓ 配图完成（3张）

📸 封面：cover-final.jpg (900×383)
📸 配图：scene-01.png, scene-02.png

下一步建议：
• "转换HTML" - 公众号排版（预计2分钟）
• "重新生成封面" - 如不满意
• "发布" - 如已有HTML
```

**依赖检查**：在开始后续阶段前，检查前置依赖
- 配图：需要 poem-metadata.json
- HTML转换：需要 content.md 和 poem-metadata.json
- 发布：需要 publish.html
- 缺失时提示用户先完成前置步骤

**工作空间**：每首诗创建独立工作空间目录 `《诗词名》_workspace/`，集中管理所有相关文件：

**交付物分离**：使用 DELIVERABLES/ 目录存放最终交付物，便于用户识别

```
《静夜思》_workspace/
├── DELIVERABLES/            # ⭐ 最终交付物
│   ├── content.md           # 📄 最终内容
│   ├── cover.jpg            # 📸 封面
│   ├── images/              # 📸 配图
│   │   ├── scene-01.png
│   │   └── scene-02.png
│   ├── preview.html         # 🌐 预览版
│   └── publish.html         # ✅ 发布版（⭐ 用于发布）
│
├── workspace/               # 工作区（中间产物）
│   ├── poem-metadata.json
│   ├── prompts/
│   │   ├── cover.md
│   │   └── scene-01.md
│   ├── cover-background.png
│   └── wechat/
│       └── draft-info.json
│
└── .workflow-state.json     # 流程状态（可选）
```

原有结构（兼容）：
```
《静夜思》_workspace/
├── poem-metadata.json       # 核实的元数据
├── content.md               # 主内容（Markdown）
├── images/
│   ├── prompts/             # 图片生成 prompt
│   │   ├── cover.md
│   │   └── scene-01.md
│   ├── cover-background.png # 封面底图
│   ├── cover-final.jpg      # 封面成品
│   └── scene-01.png         # 配图
├── html/
│   ├── preview.html         # 预览稿
│   └── publish.html         # 发布稿
└── wechat/
    └── draft-info.json      # 草稿信息(media_id等)
```

**文件命名规范**：
- 使用描述性英文，kebab-case（如 `cover-final.jpg`）
- 避免中文文件名（跨平台兼容性）
- 图片序号用两位数（`scene-01.png`, `scene-02.png`）

### Step 1：确认最小输入

从用户消息和已有文件提取：

1. 诗词名；缺失且无法从输入判断时询问。
2. 目标读者年龄/年级；缺失时使用默认值。
3. 中文或双语；缺失时用中文。
4. 用户要创作、审校、配图、HTML、草稿还是正式发布。

不要重复询问用户已经给出的信息。

### Step 2：核实事实

诗词原文、作者、朝代、生卒年、体裁、创作时间和背景属于事实层，不能凭模糊记忆补齐。

- 当前运行时有可靠检索工具时，优先核对权威古籍、教材、博物馆/图书馆或权威教育来源。
- 无检索能力时，只使用高置信信息；不确定的创作年份、地点、作者年龄或背景明确标注“约”“据主流说法”“存在争议”，必要时删除无依据细节。
- 区分“史料事实”“主流文学解释”“教学化推断”，不要把推断写成定论。
- 年龄计算考虑是否已过生日无法确认，宜写“约 X 岁”，不要伪精确。

### Step 3：按模板创作

中文读取 `references/template_zh_cn.md`；双语读取 `references/template_zh_cn_en_us.md`。模板是内容结构的 source of truth，不在主文件重复展开。

必需内容：

1. 诗词原文与真正有用的易错提醒。
2. 诗人小档案与分龄生平说明。
3. 有证据的创作背景。
4. 逐句白话译文。
5. 逐句赏析：画面、关键词、手法、情感均有诗句依据。
6. 与目标学段相称的考点和答题思路。
7. 亲子小结。

可选扩展只在能帮助理解时加入：文化典故、地理物候、对比阅读、亲子讨论，最多两个。不要为了“完整”凑字数。

### Step 4：分龄与双语适配

- 学龄前/小学低年级：短句、具体画面、少术语；术语出现时立即解释。
- 小学中高年级：加入关键词、基本修辞和可操作默写提醒。
- 初中：增加证据链、炼字、结构、主旨和对比阅读，但仍用清楚的白话。
- 双语版保持信息对应；英文可以自然意译，但不能增加中文没有的事实。生平用过去时，作品分析通常用现在时。

### Step 5：审校

读取并执行 `references/content-review.md`。按“事实 → 文学判断 → 分龄表达 → 双语 → 格式”顺序检查，先修高风险错误，再修文风。

遇到无法核实的事实，不要用“自检通过”掩盖不确定性；在文中降级表述，并在交付报告列出未验证项。

### Step 6：保存与交付

保存 Markdown 成品，报告：

- 文件路径和语言版本。
- 目标年龄/年级及使用的默认假设。
- 已核实的关键事实与仍有争议的点。
- 已完成、跳过和失败的可选步骤。
- 如果用户还要求配图、HTML 或公众号操作，继续走下列对应路径。

## 配图与封面路径

只有用户要求图片时读取 `ILLUSTRATION_GUIDE.md` 和 `references/wechat-image-specs.md`。使用当前运行时可用的原生图片工具或本技能脚本，不把某个外部 CLI 写成唯一选择。

执行约束：

1. 先分析诗意和文章结构，推荐 1 个风格与 2–3 个配图位置。
2. 生成前把每张图的完整 prompt 写入 `imgs/prompts/NN-*.md`；prompt 是修改和复现的 source of truth。
3. 用户未指定且选择会显著改变结果时，给出推荐并确认一次；用户明确”直接生成/按默认”时说明假设后继续。
4. 每篇内容先创建 `poem-meta.json`，并按 `references/poem-meta.schema.json` 维护标题、朝代、作者与诗句；文章、HTML 标题和图片图注都读取这一个事实源。
5. **图片尺寸严格遵循微信公众号规范**（见 `references/wechat-image-specs.md`）：
   - 封面：生成 2.35:1 比例，目标尺寸 900×383
   - 配图：生成 16:9 比例，目标尺寸 900-1080 宽度
   - 不生成后再裁剪，直接在 prompt 中说明目标尺寸和用途
6. 封面制作采用两步法：
   - **Step 1**：生成无字底图（默认模式，禁止 AI 绘制任何文字）
   - **Step 2**：使用 `compose-cover.js` 从 `poem-meta.json` 读取并合成文字
7. 封面文字内容：
   - **必含**：诗名、”朝代·作者”
   - **诗句选择**：短诗（≤4句）显示全文；长诗显示 1-2 句代表名句
   - 文字绝不由图片模型生成或回忆，只能从 `poem-meta.json` 获取
8. 成图后逐字核对诗名、朝代、作者和诗句，并检查断句、标点、繁简体与遮挡；任一项不通过都不能交付或上传。
9. 已有同名输出时先备份或询问，不静默覆盖用户修改。

脚本入口（将 `{baseDir}` 替换为本技能目录绝对路径）：

```bash
# Step 1: 生成无字底图
node {baseDir}/scripts/generate-image.js \
  --prompt-file imgs/prompts/00-cover.md \
  --output imgs/00-cover-bg.png \
  --aspect-ratio 2.35:1

# Step 2: 合成封面文字
node {baseDir}/scripts/compose-cover.js \
  --meta poem-meta.json \
  --background imgs/00-cover-bg.png \
  --output imgs/00-cover-final.jpg \
  --lines auto

# 配图（直接生成，无需文字合成）
node {baseDir}/scripts/generate-image.js \
  --prompt-file imgs/prompts/01-scene.md \
  --output imgs/01-scene.png \
  --aspect-ratio 16:9
```

`compose-cover.js` 选项：
- `--lines auto`：自动选择（短诗全文，长诗 1-2 名句，默认）
- `--lines full`：强制显示全文
- `--lines 2`：显示指定行数
- `--title-only`：只显示标题和作者，不显示诗句

默认模式禁止 AI 生成任何可读文字（诗名、作者、诗句、印章、水印）。只有用户明确接受文字错漏风险且文字合成脚本不可用时，才可使用 `--allow-ai-text`；此模式生成后仍须逐字核对。

## 公众号 HTML 路径

1. 读取 `references/themes/index.md`，根据诗词气质、读者和配图推荐一个主题。
2. 用户未指定时使用推荐主题，不必为低风险本地转换阻塞；交付时说明选择，允许重做。
3. 只读取选中的一个 `theme-*.md`，不要混用多个主题的组件。
4. 所有 CSS 内联，不依赖 CDN。
5. **诗词原文移动端优化**（重要）：
   - 每句诗独立生成一个 `<p>` 标签，确保在窄屏上不会句内换行
   - 从 `poem-meta.json` 读取诗句数组，逐句生成 HTML
   - 最后一句使用 `margin:0`，其他句使用 `margin:0 0 6px`
   - 示例见 `references/mobile-poem-layout-guide.md`
6. 生成两份文件到文章目录的 `outputs/`：
   - `公众号预览稿.html`：可含封面和主标题，用于本地检查。
   - `公众号发布稿.html`：不含正文封面副本和主标题 `<h1>`，用于微信草稿。
7. 检查诗句换行、图片路径、移动端宽度和发布稿内容完整性。

## 公众号草稿与发布路径

读取 `references/publishing-workflow.md`，使用 `{baseDir}/scripts/wechat_mp_publish.py`。

- 真实凭据只能来自用户指定的安全位置、环境变量或 `~/.config/wechat-mp/wechat.env.profile`；不要打印、回显或写入文章目录。
- 必须先对 `公众号发布稿.html` 运行 `draft --dry-run` 并检查载荷，再创建草稿。
- 创建草稿后报告 `media_id` 并默认停止。
- `publish --confirm-publish` 会产生外部公开影响，只有用户在当前对话明确要求发布并确认目标后才可执行。
- fallback 若改变账号、发布状态或内容，不可静默采用。

## 失败处理

| 情况 | 行动 |
|---|---|
| 诗词或背景无法可靠核实 | 降级表述或删除细节，列入未验证项 |
| 图片后端不可用 | 保留 prompt 文件，报告可用的等价后端或询问用户 |
| prompt 要求图片内出现姓名/诗句 | 默认改为无字图；只有用户接受风险才使用 `--allow-ai-text` |
| AI 原生文字不准确 | 判定失败，不宣称已通过；回退为无字图与外部准确标题 |
| HTML 主题组件缺失 | 用同一主题令牌简化实现，不拼接其他主题 |
| 凭据、白名单或权限失败 | 停止外部调用，给出具体配置入口，不索取明文密钥到回复中 |
| dry-run 失败 | 不创建草稿；报告失败字段和最小修复步骤 |
| 正式发布未获确认 | 停在草稿或发布预备状态 |

## 完成验收

### 检查清单

**内容审校**：
- [ ] 诗词原文逐字核对，无遗漏或篡改
- [ ] 作者、朝代、背景事实准确，争议信息已标注
- [ ] 无错别字、标点错误
- [ ] 分龄语言适当，符合目标读者理解水平
- [ ] 考点与课标匹配，有诗句依据

**配图**（如有）：
- [ ] 封面文字准确（诗名、作者、诗句）
- [ ] 图片尺寸符合微信规范（封面 900×383，配图 1080×608）
- [ ] 配图与诗词意境契合
- [ ] 无文字遮挡、无主体截断

**HTML**（如有）：
- [ ] 在手机端显示正常（测试 320px-414px 宽度）
- [ ] 诗句每句独立一行，无句内换行
- [ ] 预览稿与发布稿职责分离，发布稿无重复封面和 `<h1>`

**公众号发布前**（如有）：
- [ ] 图片已上传微信服务器（本地路径已替换为微信 URL）
- [ ] 封面已设置（thumb_media_id 有效）
- [ ] 标题、作者字段正确
- [ ] dry-run 测试通过，检查了目标账号、标题、封面和正文

### 协作断点策略

**自动执行（无需确认）**：
- 核实诗词原文
- 创作标准 7 模块内容
- 保存 poem-metadata.json
- 生成 prompt 文件
- 转换 HTML（使用推荐主题）

**需要用户确认**：
- 配图风格选择（首次询问，使用 AskUserQuestion 提供选项）
- 是否生成配图
- HTML 主题选择（给推荐，允许更改）
- 创建公众号草稿
- 正式发布（必须明确确认）

**用户主动模式**：
- 用户说"直接生成，用默认配置" → 全程自动，只在关键错误时停止
- 用户说"我要一步步确认" → 每个决策点都询问

### 验收标准

**创作/审校**：

- 原文、作者、朝代和体裁无已知错误；争议信息已标注。
- 分析有诗句依据，不把常见套话当考点。
- 内容难度与目标年龄一致。
- 双语内容对应且英文语法自然（如适用）。
- 文件已保存，未验证项已报告。

### 图片/HTML

- prompt 已先落盘，图片实际存在且尺寸/格式合理。
- 默认图片无可读文字；若使用 `--allow-ai-text`，文字必须逐字核对并报告验证方式。
- HTML 预览稿与发布稿职责分离；发布稿无重复封面和 `<h1>`。

### 公众号

- dry-run 通过并检查了目标账号、标题、封面和正文。
- 草稿成功以真实 API 回执和 `media_id` 为准。
- 正式发布成功以 API 回执和 `publish_id` 为准；不要只相信命令退出码。

## Resources

| 文件 | 何时读取 |
|---|---|
| `references/template_zh_cn.md` | 中文内容创作 |
| `references/template_zh_cn_en_us.md` | 双语内容创作 |
| `references/content-review.md` | 内容审校或生成后的必做检查 |
| `references/poem-meta.schema.json` | 创建 `poem-meta.json` 与复用事实字段 |
| `ILLUSTRATION_GUIDE.md` | 用户要求配图或封面 |
| `references/wechat-image-specs.md` | 配图时了解微信公众号图片规格 |
| `references/mobile-poem-layout-guide.md` | HTML 转换时了解诗词移动端排版规范 |
| `references/themes/index.md` | 转公众号 HTML 时选择主题 |
| `references/themes/theme-*.md` | 选定主题后只读一个 |
| `references/publishing-workflow.md` | 建草稿、查状态或正式发布 |
| `references/wechat_api.md` | 微信 API 错误或字段细节 |
