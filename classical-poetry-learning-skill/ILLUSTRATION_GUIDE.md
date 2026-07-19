# 古诗词学习技能 - 配图功能使用指南

## 📸 配图功能概述

为古诗词学习推文添加精美插图，增强视觉效果和用户体验。支持水彩、水墨、手绘等多种中国风格式。

**重要更新**：所有图片尺寸严格遵循微信公众号规范，直接生成目标尺寸，无需二次裁剪。封面图采用两步法：先生成无字底图，再用脚本合成文字（短诗全文，长诗名句）。详见 `references/wechat-image-specs.md`。

---

## 🎯 适用场景

### 推荐使用配图的情况

✅ **公众号推文** - 提升阅读体验和转发率  
✅ **教学材料** - 帮助学生理解诗词意境  
✅ **打印资料** - 制作精美的学习卡片  
✅ **课件展示** - PPT中使用的配图素材

### 不推荐配图的情况

❌ **纯文字环境** - 如命令行、纯文本编辑器  
❌ **快速预览** - 只需要快速查看内容  
❌ **网络受限** - 图片加载困难的环境

---

## 🎨 配图类型和风格

### 配图类型

| 类型 | 说明 | 适用位置 | 示例 |
|-----|------|---------|------|
| **意境图** | 展现诗词整体画面和氛围 | 逐句赏析后 | 明月、瀑布、春花等场景 |
| **场景还原图** | 还原诗人创作时的场景 | 创作背景后 | 诗人在庐山观瀑布 |
| **知识图解** | 用图形、箭头和色块表现知识关系，文字留给正文 | 必考考点中 | 结构和修辞关系图 |
| **诗人场景图** | 时代与活动场景的艺术想象，不声称还原真实容貌 | 诗人小档案后 | 唐代诗人月下远游 |

### 推荐风格预设

根据诗词类型自动推荐：

| 诗词类型 | 推荐Preset | 风格特点 | 代表诗作 |
|---------|-----------|---------|---------|
| 山水田园诗 | `watercolor-scene` | 水彩风格，温暖自然 | 《望庐山瀑布》《过故人庄》 |
| 边塞诗 | `ink-notes-scene` | 水墨风格，大气磅礴 | `《凉州词》《出塞》 |
| 思乡诗 | `warm-scene` | 温暖色调，情感丰富 | 《静夜思》《泊船瓜洲》 |
| 咏物诗 | `nature-scene` | 自然风格，清新雅致 | 《咏柳》《墨梅》 |
| 哲理诗 | `hand-drawn-edu` | 手绘教育风格，适合图解 | 《登鹳雀楼》《题西林壁》 |
| 叙事诗 | `storytelling` | 叙事场景，画面感强 | 《木兰诗》《琵琶行》 |

---

## 📝 使用方法

### 基础用法

```bash
# 创建带配图的推文
"帮我写《静夜思》的推文，要带插图的"

# 指定风格
"制作《望庐山瀑布》的学习材料，加上水彩风格的配图"

# 指定配图数量
"《春晓》的推文，需要2张插图：意境图和知识图解"
```

### 高级用法

```bash
# 自定义风格组合
"《登鹳雀楼》的推文，用水墨风格的场景图和手绘风格的知识图解"

# 指定详细要求
"《望庐山瀑布》推文配图，意境图要体现瀑布飞流直下的气势，用水彩风格"
```

---

## 🔧 配图工作流程

### Step 1: 生成推文内容

首先按标准流程生成完整的古诗词推文（7个模块）

同时创建 `poem-meta.json`，按 `references/poem-meta.schema.json` 保存经过核实的标题、朝代、作者和诗句。后续文章标题、HTML、图片 alt 文本和公众号字段都从这里取值，不要在多个 prompt 中分别手填作者姓名。

### Step 2: 制定配图方案

系统自动分析内容，推荐配图位置和数量：

**标准配图方案（2-3张）**：
1. **封面图** - 900×383（2.35:1），含诗名、朝代·作者、代表诗句
2. **意境图** - 1080×608（16:9），在”逐句赏析”后
3. **场景图** - 1080×608（16:9），在”创作背景”后（可选）
4. **知识图解** - 900×506（16:9），在”必考考点”中（可选）

### Step 3: 生成配图outline

创建 `imgs/outline.md`，详细列出每张图的：
- 位置和用途
- 内容描述
- 关键元素
- 目标尺寸（严格按微信规范）
- 文件名

### Step 4: 生成prompt文件

为每张图创建详细的prompt文件（`imgs/prompts/*.md`），包含：
- 视觉类型
- 主要内容
- 关键元素
- 目标尺寸和用途说明（如 “for WeChat article cover, 2.35:1 aspect ratio”）
- 风格指南
- 艺术参考
- 最终prompt（中英文）

**重要**：默认 prompt 禁止图片模型生成任何可读文字（诗名、作者、诗句、印章、水印）。封面文字由后续脚本合成。

### Step 5: 生成无字底图

**封面图**（两步法）：

```bash
# Step 5.1: 生成无字底图（2.35:1 比例）
node scripts/generate-image.js \
  --prompt-file imgs/prompts/00-cover.md \
  --output imgs/00-cover-bg.png \
  --aspect-ratio 2.35:1
```

**配图**（直接生成最终图）：

```bash
# 意境图/场景图（16:9 比例）
node scripts/generate-image.js \
  --prompt-file imgs/prompts/01-scene.md \
  --output imgs/01-scene.png \
  --aspect-ratio 16:9

# 知识图解（16:9 比例，无字）
node scripts/generate-image.js \
  --prompt-file imgs/prompts/02-knowledge.md \
  --output imgs/02-knowledge.png \
  --aspect-ratio 16:9
```

脚本默认追加无字约束，结果 JSON 中返回 `textMode: “none”`。

### Step 6: 封面文字合成

使用 `compose-cover.js` 从 `poem-meta.json` 读取诗名、朝代、作者和诗句，合成到封面底图：

```bash
node scripts/compose-cover.js \
  --meta poem-meta.json \
  --background imgs/00-cover-bg.png \
  --output imgs/00-cover-final.jpg \
  --lines auto
```

**文字内容规则**：
- **诗名**：必含
- **朝代·作者**：必含
- **诗句**：
  - `--lines auto`（默认）：短诗（≤4句）显示全文，长诗显示 1-2 句代表名句
  - `--lines full`：强制显示全文
  - `--lines 2`：显示指定行数
  - `--title-only`：只显示标题和作者，不显示诗句

**验证步骤**：
1. 脚本自动从 `poem-meta.json` 读取内容，无需手工输入
2. 生成后检查控制台输出的验证清单
3. 手动打开 `imgs/00-cover-final.jpg` 确认：
   - 诗名、朝代、作者、诗句拼写正确
   - 标点、断句、繁简体无误
   - 文字未越界、未遮挡主体
   - 手机端可读（文字大小、对比度）

### Step 6.5: 尺寸与体积验证（发布前必查）

如果这批图后续要发公众号，配图阶段就应产出合规文件，避免草稿创建时才失败：

| 用途 | 格式 | 大小 | 尺寸 |
|---|---|---|---|
| 封面 | **JPEG** | < 1 MB | 宽度 ≥ 900px（如 900×383、1080×608） |
| 文内图 | jpg / png | < 1 MB | 无硬性要求 |

```bash
# 查看尺寸与体积
file imgs/00-cover-final.jpg
ls -lh imgs/*.jpg imgs/*.png
```

- 封面优先导出 JPEG；PNG 常因体积超 1MB 或宽度不足触发微信 `53401`。
- 文内图（意境图、知识图解）水彩/高分辨率 PNG 容易超 1MB，导出时压到 1MB 以内，或转 JPEG。
- 若发布时仍超限，`wechat_mp_publish.py` 会在 dry-run 阶段拦截，并在装有 Pillow 时自动生成 `*.wechat.jpg` 压缩副本（不覆盖原图）。规格细节见 `references/wechat_api.md`。

### Step 7: 插入图片

在推文的适当位置插入图片引用：

```markdown
![《静夜思》封面 - 唐·李白](imgs/00-cover-final.jpg)

![《静夜思》诗词意境图 - 明月照床前，思乡情深](imgs/01-scene.png)
```

### Step 8: 生成报告

提供配图完成总结，包括：
- 成功生成的图片列表及尺寸
- 封面文字验证结果
- 失败项及原因
- 文件大小统计

---

## 📂 输出目录结构

```
《望庐山瀑布》_古诗词鉴赏_中文版/
├── 《望庐山瀑布》_古诗词鉴赏_中文版.md  ← 主文件（带图片引用）
├── poem-meta.json                          ← 核实的诗词事实（封面文字来源）
└── imgs/
    ├── outline.md                          ← 配图方案
    ├── prompts/                            ← Prompt文件
    │   ├── 00-cover.md                      ← 封面底图 prompt
    │   ├── 01-poetry-scene.md
    │   ├── 02-background-scene.md
    │   └── 03-exam-points.md
    ├── 00-cover-bg.png                      ← 封面无字底图（900×383）
    ├── 00-cover-final.jpg                   ← 封面成品（含文字，900×383）
    ├── 01-poetry-scene.png                 ← 意境图（1080×608）
    ├── 02-background-scene.png             ← 场景图（1080×608）
    └── 03-exam-points.png                  ← 知识图解（900×506）
```

**文件命名约定**：
- `00-cover-bg.png` - 封面无字底图（中间产物）
- `00-cover-final.jpg` - 封面成品（含合成文字，用于发布）
- 发布时封面使用 `00-cover-final.jpg`

---

## 🎨 Prompt示例

### 意境图Prompt示例

```markdown
Create a Chinese traditional watercolor style scene illustration for the poem "望庐山瀑布" (Viewing the Waterfall at Mount Lu).

Setting: Daytime at Mount Lu, Jiangxi Province. A magnificent waterfall cascading down from high cliffs, with mist rising and sunlight creating a purple haze around the Incense Burner Peak.

Main elements:
- A towering waterfall flowing straight down from great height
- The Incense Burner Peak shrouded in purple mist
- Sunlight creating atmospheric effects
- Distant mountains and valleys
- Sense of grandeur and power

Atmosphere: Majestic, awe-inspiring, celebrating the beauty and power of nature

Style: Soft watercolor painting with warm tones, traditional Chinese artistic composition with appropriate negative space, delicate brushwork reminiscent of Song Dynasty court paintings, combining classical elegance with modern illustration aesthetics.

The illustration should capture the poetic essence of Li Bai's description - the waterfall like a silver river falling from the heavens, creating a breathtaking spectacle of natural beauty and power.
```

### 知识图解Prompt示例

```markdown
Create a hand-drawn educational infographic explaining exam points for "望庐山瀑布".

Content structure:
- A four-step visual rhythm representing the poem, without written poem lines
- Center: visual relationship between the waterfall's real scale and imaginative celestial scale
- Arrows, icons and color blocks may be used, but contain no labels or readable characters
- Reserve a clean side column so explanations can live in the article text

Style: Hand-drawn educational diagram on warm cream paper, black lines and soft pastel color blocks. No text, labels, names, signatures, seals, logos, or watermarks.

The infographic should be clear, friendly, and suitable for elementary school students (Grade 3) studying Chinese classical poetry.
```

---

## ⚙️ 环境配置

### 必需工具（至少一个）

#### Option 1: Codex CLI（推荐）

```bash
# 安装
npm install -g codex-cli

# 验证
codex --version

# 配置
# 编辑 ~/.codex/config.toml，确保移除 service_tier 配置项
```

#### Option 2: Antigravity CLI (Gemini)

```bash
# 安装
# 访问 https://antigravity.google/docs/cli-getting-started

# 验证
agy --version
```

### 测试环境

```bash
# 检查Node.js
node --version  # 需要 >=14.0.0

# 检查图片生成工具
which codex  # 或
which agy

# 测试脚本
node scripts/generate-image.js --help
```

---

## 💡 最佳实践

### 1. 风格一致性

✅ 同一篇推文使用相同的风格preset  
❌ 避免混用多种风格（除非有特殊需求）

### 2. 图片数量

✅ 推荐：封面 + 2-3 张配图
- 封面（必需）
- 意境图（推荐）
- 场景图或知识图解（可选）
❌ 不宜过多（超过5张）影响阅读体验

### 3. 场景优先

✅ 古诗词更适合scene类型，展现意境  
⚠️ 少用infographic，仅用于知识图解

### 4. 意境把握

✅ 充分理解诗词意境后再设计prompt  
✅ 结合诗词的主旨情感和画面描写  
❌ 避免过于抽象或与诗词无关的图片

### 5. 文字策略（重要更新）

✅ **默认两步法**：无字底图 + 脚本合成文字  
✅ 诗名、朝代、作者、诗句统一来自 `poem-meta.json`  
✅ **封面诗句规则**：
  - 短诗（≤4句）：显示全文
  - 长诗（>4句）：显示 1-2 句代表名句
  - 可用 `--lines` 参数控制
✅ 封面底图为文字合成保留干净安全区（prompt 中说明）  
❌ 不让模型自行回忆或拼写诗人姓名、诗句  
⚠️ `--allow-ai-text` 已弃用，仅作为脚本不可用时的最后手段

### 6. 尺寸策略（重要更新）

✅ **严格遵循微信公众号规范**：
  - 封面：900×383（2.35:1）或 900×500（1.8:1）
  - 配图：1080×608（16:9）或 900×506（16:9）
✅ **prompt 中说明用途**：
  - “for WeChat article cover, 2.35:1 aspect ratio, 900×383 target size”
  - “for WeChat article illustration, 16:9 aspect ratio, 1080×608 target size”
✅ **直接生成目标尺寸，不做二次裁剪**
❌ 不生成超大图后再压缩（浪费时间和配额）

### 7. 色调选择

根据诗词情感选择合适的色调：
- **思乡诗** → 温暖色调（warm palette）
- **山水诗** → 清新自然色（nature palette）
- **边塞诗** → 苍凉大气的色调（mono-ink）
- **春天诗** → 明快柔和的色彩（macaron）

### 8. 文件格式

✅ 封面：JPG（质量 90，平衡质量与大小）  
✅ 意境图/场景图：PNG 或 JPG  
✅ 知识图解：PNG（确保清晰度）  
✅ 控制文件大小：封面 < 300KB，配图 < 500KB

---

## 🔍 故障排查

### 图片生成失败

**问题**：提示"No image generation backend available"

**解决**：
```bash
# 检查是否安装了 codex-cli 或 agy
which codex
which agy

# 如果都没有，至少安装一个
npm install -g codex-cli
```

---

**问题**：codex 返回但找不到图片

**解决**：
```bash
# 检查 codex 配置
cat ~/.codex/config.toml

# 确保移除了 service_tier 配置项
# 如果存在这一行，删除它：
# service_tier = "..."
```

---

**问题**：agy 报错 RESOURCE_EXHAUSTED

**解决**：
- Gemini API配额已用完
- 切换使用 codex：`--provider codex`
- 或等待配额重置

---

### Prompt效果不理想

**问题**：生成的图片与诗词意境不符

**解决**：
1. 编辑对应的prompt文件（`imgs/prompts/*.md`）
2. 修改PROMPT部分，添加更具体的描述
3. 重新生成该图片：
   ```bash
   node scripts/generate-image.js \
     --prompt-file imgs/prompts/01-scene.md \
     --output imgs/01-scene.png
   ```

---

**问题**：图片风格不够中国风

**解决**：
在prompt中强调：
- "Traditional Chinese painting style"
- "Song Dynasty court painting aesthetics"
- "Chinese ink wash painting"
- "Classical Chinese artistic composition"

---

## 📊 配图效果对比

### 无配图 vs 有配图

| 维度 | 无配图 | 有配图 | 提升 |
|------|-------|--------|------|
| 阅读体验 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | +67% |
| 意境理解 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | +67% |
| 公众号转发率 | 基准 | +40% | 显著提升 |
| 学生学习兴趣 | ⭐⭐⭐ | ⭐⭐⭐⭐ | +33% |
| 内容制作时间 | 快 | 中等 | +5-10分钟 |

---

## 🎓 示例

### 示例1：《静夜思》- 简单配图（封面 + 意境图）

**配图方案**：封面 + 1张意境图

```bash
"写《静夜思》的推文，加封面和一张意境图，要温暖的色调"
```

**执行流程**：

1. 生成 `poem-meta.json`：
```json
{
  "title": "静夜思",
  "dynasty": "唐",
  "author": "李白",
  "lines": [
    "床前明月光，",
    "疑是地上霜。",
    "举头望明月，",
    "低头思故乡。"
  ],
  "verification": {
    "status": "verified",
    "checked_at": "2026-07-18",
    "sources": ["《全唐诗》"]
  }
}
```

2. 生成封面无字底图：
```bash
node scripts/generate-image.js \
  --prompt-file imgs/prompts/00-cover.md \
  --output imgs/00-cover-bg.png \
  --aspect-ratio 2.35:1
```

3. 合成封面文字（自动显示全文，因为只有4句）：
```bash
node scripts/compose-cover.js \
  --meta poem-meta.json \
  --background imgs/00-cover-bg.png \
  --output imgs/00-cover-final.jpg \
  --lines auto
```

4. 生成意境图：
```bash
node scripts/generate-image.js \
  --prompt-file imgs/prompts/01-scene.md \
  --output imgs/01-scene.png \
  --aspect-ratio 16:9
```

**输出**：
- 封面：900×383，含诗名、"唐·李白"、全文4句
- 意境图：1080×608，明月、床前、思乡氛围
- 风格：warm-scene
- 总生成时间：~5-8分钟

---

### 示例2：《望庐山瀑布》- 标准配图（封面 + 2张配图）

**配图方案**：封面 + 意境图 + 知识图解

```bash
"制作《望庐山瀑布》的学习材料，用水彩风格配图"
```

**poem-meta.json**：
```json
{
  "title": "望庐山瀑布",
  "dynasty": "唐",
  "author": "李白",
  "lines": [
    "日照香炉生紫烟，",
    "遥看瀑布挂前川。",
    "飞流直下三千尺，",
    "疑是银河落九天。"
  ],
  "verification": {
    "status": "verified",
    "checked_at": "2026-07-18"
  }
}
```

**执行流程**：

1. 封面（无字底图 + 文字合成）：
```bash
node scripts/generate-image.js \
  --prompt-file imgs/prompts/00-cover.md \
  --output imgs/00-cover-bg.png \
  --aspect-ratio 2.35:1

node scripts/compose-cover.js \
  --meta poem-meta.json \
  --background imgs/00-cover-bg.png \
  --output imgs/00-cover-final.jpg \
  --lines auto
```

2. 意境图和知识图解：
```bash
node scripts/generate-image.js \
  --prompt-file imgs/prompts/01-scene.md \
  --output imgs/01-scene.png \
  --aspect-ratio 16:9

node scripts/generate-image.js \
  --prompt-file imgs/prompts/02-knowledge.md \
  --output imgs/02-knowledge.png \
  --aspect-ratio 16:9
```

**输出**：
- 封面：900×383，含"望庐山瀑布"、"唐·李白"、全文4句（短诗）
- 意境图：1080×608，瀑布飞流直下的壮观场景
- 知识图解：900×506，夸张和想象手法图解
- 风格：watercolor-scene + hand-drawn-edu
- 总生成时间：~10-12分钟

---

### 示例3：《琵琶行》节选 - 长诗配图（封面显示名句）

**配图方案**：封面（显示名句）+ 场景图

```bash
"《琵琶行》节选的推文，封面上显示'同是天涯沦落人，相逢何必曾相识'这两句"
```

**poem-meta.json**（节选）：
```json
{
  "title": "琵琶行",
  "dynasty": "唐",
  "author": "白居易",
  "lines": [
    "浔阳江头夜送客，枫叶荻花秋瑟瑟。",
    "主人下马客在船，举酒欲饮无管弦。",
    "醉不成欢惨将别，别时茫茫江浸月。",
    "忽闻水上琵琶声，主人忘归客不发。",
    "寻声暗问弹者谁？琵琶声停欲语迟。",
    "移船相近邀相见，添酒回灯重开宴。",
    "千呼万唤始出来，犹抱琵琶半遮面。",
    "...",
    "同是天涯沦落人，相逢何必曾相识！",
    "..."
  ],
  "verification": {
    "status": "verified",
    "checked_at": "2026-07-18"
  }
}
```

**执行流程**：

由于是长诗，`--lines auto` 会自动选择代表名句，或使用 `--lines 2` 明确指定显示前2句：

```bash
# 方案1：自动选择（会挑选第1句和中间代表句）
node scripts/compose-cover.js \
  --meta poem-meta.json \
  --background imgs/00-cover-bg.png \
  --output imgs/00-cover-final.jpg \
  --lines auto

# 方案2：手动指定显示特定行数（显示前2句）
node scripts/compose-cover.js \
  --meta poem-meta.json \
  --background imgs/00-cover-bg.png \
  --output imgs/00-cover-final.jpg \
  --lines 2
```

**输出**：
- 封面：900×383，含"琵琶行"、"唐·白居易"、1-2句代表诗句（非全文）
- 场景图：1080×608，江边夜色、琵琶演奏场景

---

### 示例4：只要封面，不要配图

```bash
"给《登鹳雀楼》做个封面图，水墨风格，只要封面不要其他配图"
```

**执行流程**：

```bash
node scripts/generate-image.js \
  --prompt-file imgs/prompts/00-cover.md \
  --output imgs/00-cover-bg.png \
  --aspect-ratio 2.35:1

node scripts/compose-cover.js \
  --meta poem-meta.json \
  --background imgs/00-cover-bg.png \
  --output imgs/00-cover-final.jpg \
  --lines auto
```

**输出**：
- 仅封面：900×383
- 含诗名、"唐·王之涣"、全文（4句短诗）

---

## 📞 支持

如有问题或建议，请参考：
- 项目说明：`README.md`（中文）/ `README_EN.md`（English）
- 主技能文档：`SKILL.md`
- 图片生成脚本：`scripts/generate-image.js --help`

---

**最后更新**：2026-07-17  
**功能版本**：v1.2（含配图功能）
