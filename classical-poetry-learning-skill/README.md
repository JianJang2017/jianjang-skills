<!-- Language: [中文](README.md) | [English](README_EN.md) -->

# 古诗词学习内容创作技能

> 一键生成专业的古诗词鉴赏推文，适配公众号发布和亲子教学。内容通俗易懂、紧扣考点、支持中英双语，并可自动配图。

## 简介

这是一个 Claude Skill，帮助家长、老师和内容创作者快速生成高质量的古诗词学习材料。生成的内容风格通俗易懂，紧扣中小学考点，适配家长讲解和儿童理解。

核心特点：

- **结构规范**：统一的 7 模块标准结构，便于批量生产和阅读
- **内容审校**：7 大维度自检，确保诗词原文、历史事实、错别字零差错
- **双语支持**：纯中文版 / 中英双语版
- **自动配图**：根据诗词意境自动生成插图并插入推文
- **公众号封面**：默认生成无字意境背景，准确诗名与作者由公众号标题字段承载；AI 原生文字为显式高风险选项
- **一键发布**：转成公众号可粘贴的 HTML，并创建到微信公众号草稿箱

## 功能特性

### 1. 标准 7 模块结构

每篇推文包含以下模块：

1. 诗词原文（带易错字标注）
2. 诗人小档案（孩子易懂版）
3. 创作背景（白话通俗版）
4. 全文白话译文（逐句对应，口语化）
5. 逐句深度赏析（亲子讲解重点）
6. 中小学必考考点（应试核心）
7. 亲子小结（简短复盘）

### 2. 内容审校与自检

生成后自动执行 7 大维度审校：

| 维度 | 检查内容 |
|------|---------|
| 诗词原文核查 | 逐字核对，标点规范 |
| 历史事实核查 | 诗人生卒年、朝代、创作背景 |
| 文学知识核查 | 体裁、修辞、主旨判断 |
| 语言文字核查 | 错别字、专有名词 |
| 易错字标注核查 | 标注准确性和针对性 |
| 考点准确性核查 | 默写、答题模板实用性 |
| 双语版本核查 | 中英对照、翻译质量 |

### 3. 双语支持

- **纯中文版**（默认）：`--lang=zh_cn`
- **中英双语版**：`--lang=zh_cn,en_us`

### 4. 自动配图（可选）

根据诗词类型自动推荐配图风格，生成 AI 绘图 prompt 并调用图片生成后端。**图片尺寸严格遵循微信公众号规范，直接生成目标尺寸，无需二次裁剪**：

| 图片类型 | 尺寸 | 比例 | 用途 |
|---------|------|------|------|
| 封面图 | 900×383 | 2.35:1 | 公众号首图 |
| 配图 | 1080×608 | 16:9 | 文内插图 |

| 诗词类型 | 推荐风格 |
|---------|---------|
| 山水田园诗 | 水彩场景（watercolor-scene） |
| 边塞诗 | 水墨风格（ink-notes-scene） |
| 思乡诗 | 温暖色调（warm-scene） |
| 咏物诗 | 自然风格（nature-scene） |
| 哲理诗 | 手绘教育（hand-drawn-edu） |

详见 [配图功能使用指南](ILLUSTRATION_GUIDE.md)。

### 5. 公众号封面图（可选）

封面图采用**两步法**生成，确保文字准确且尺寸符合微信规范：

**Step 1**：生成无字底图
- 使用 `generate-image.js` 生成 2.35:1 比例的干净背景
- 禁止 AI 绘制任何文字（诗名、作者、诗句）

**Step 2**：合成准确文字
- 使用 `compose-cover.js` 从 `poem-meta.json` 读取核实的诗名、朝代、作者、诗句
- 使用 Chrome headless + HTML/CSS 排版，确保文字准确无误
- **短诗（≤4句）**：显示全文
- **长诗（>4句）**：显示 1-2 句代表名句
- 输出 900×383 标准尺寸，符合微信公众号首图规范

**优势**：
- ✅ 诗名、作者、诗句 100% 准确（从核实的 JSON 读取）
- ✅ 无需手动检查或修正 AI 生成的错别字
- ✅ 直接生成微信尺寸，无需二次裁剪
- ✅ 短诗全文、长诗名句，自动适配

封面尺寸默认 **900×383（2.35:1）**，是微信公众号首图推荐尺寸。

### 6. 转 HTML 与发布公众号草稿箱（可选）

把做好的推文转成微信公众号可粘贴的 HTML，并推送到公众号草稿箱：

1. **选主题转 HTML**：从 **11 个主题库**（`references/themes/`）里按诗词情绪和场景选一个（古典水墨、极简墨色、复古杂志、暖白秩序、青格笔记、山吹、雁栖湖、萌绿等），生成公众号排版稿，样式全内联。生成预览稿（含封面）和发布稿（正文不含封面副本和主标题）两份。
2. **创建草稿**：用 `scripts/wechat_mp_publish.py` 上传封面、改写文内图、创建草稿。**默认只建草稿不发布**。
3. **发布**：仅在用户明确确认后才提交发布（不可逆操作）。

首次使用需配置微信公众号 AppID/AppSecret（写入 `~/.config/wechat-mp/wechat.env.profile`）。详见 SKILL.md 的发布章节和 [微信 API 说明](references/wechat_api.md)。

> 发布前务必先转成 HTML 再发布——不要直接把 Markdown 丢给发布脚本，否则排版会丢失。

## 使用方法

直接用自然语言触发技能：

```
帮我写《静夜思》的古诗词赏析，小学二年级
制作《春晓》的学习材料，要双语版 --lang=zh_cn,en_us
写《登鹳雀楼》的赏析，初一，重点讲哲理和考点
制作《望庐山瀑布》的学习材料，用水彩风格配图
给《静夜思》做个公众号封面，风格和配图保持一致
把《望庐山瀑布》转成公众号 HTML 并发到草稿箱
```

### 触发关键词

- **基础创作**：古诗词学习材料、公众号推文、诗词赏析、给孩子讲解某首诗
- **配图功能**：带插图、配图、生成图片、加上插图
- **封面图**：配封面、封面图、公众号封面、做个封面
- **HTML/发布**：转成 HTML、公众号 HTML、发布到公众号、发到草稿箱、创建公众号草稿
- **强调审校**：特别注意审校、检查错别字、确保历史准确

## 目录结构

```
classical-poetry-learning-skill/
├── SKILL.md                        # 技能主文件（核心指令）
├── README.md                       # 中文说明（本文件）
├── README_EN.md                    # 英文说明
├── ILLUSTRATION_GUIDE.md           # 配图功能使用指南
├── scripts/
│   ├── generate-image.js           # 图片生成脚本（codex / gemini）
│   └── wechat_mp_publish.py        # 公众号草稿/发布脚本
├── references/
│   ├── template_zh_cn.md           # 中文版模板
│   ├── template_zh_cn_en_us.md     # 双语版模板
│   ├── wechat_api.md               # 微信公众号 API 说明
│   └── themes/                     # 公众号 HTML 主题库（11 个）
│       ├── index.md               # 主题选择索引（场景 → 主题）
│       ├── theme-classical-ink.md # 古典水墨（推荐默认）
│       ├── theme-*.md             # 其余 10 个可选主题
│       └── examples/              # 各主题的 HTML 预览
└── evals/
    └── evals.json                  # 测试用例
```

## 环境要求与依赖说明

### ✅ 开箱即用（零外部依赖）

以下功能**不需要安装任何第三方包或外部工具**，纯内置能力可直接运行：

- ✅ **文本创作**：生成古诗词鉴赏推文（纯中文版 / 双语版）
- ✅ **内容审校**：7 大维度自动校验（诗词原文、历史事实、易错字等）
- ✅ **HTML 转换**：把推文转换为公众号排版 HTML（11 个主题，纯静态无 CDN）
- ✅ **公众号发布**：创建微信公众号草稿/发布（需配置 AppID/AppSecret，但无需装包）

> 📦 **无第三方依赖**：
> - `wechat_mp_publish.py`（Python）仅用标准库，可选的 `markdown` 包已做优雅降级——没装也能跑，只是部分复杂 Markdown 语法退化为朴素渲染
> - `generate-image.js`（Node）仅用 Node 内置模块，无需 `npm install`，没有 `package.json`

### ⚠️ 可选功能（需要外部工具）

以下功能依赖 **AI 图像生成工具** 和 **Chrome 浏览器**，如不需要配图/封面功能可跳过：

- **配图生成**：诗词意境图、创作背景场景图
- **封面图生成**：公众号首图（两步法：无字底图 + 准确文字合成）

**必需工具**：

1. **AI 图像生成后端（至少安装一个）**
   - **codex-cli**（OpenAI Codex CLI，推荐）
     - 安装：`npm install -g codex-cli` 或参考 https://openai.com/codex
     - 验证：`codex --version`
   
   - **agy**（Antigravity CLI，Google Gemini）
     - 安装：参考 https://antigravity.google/docs/cli-getting-started
     - 验证：`agy --version`

2. **Chrome 浏览器（封面文字合成必需）**
   - **macOS**: `/Applications/Google Chrome.app`
   - **Windows**: `C:\Program Files\Google\Chrome\Application\chrome.exe`
     - 或 `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`
     - 或 `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe`
   - **Linux**: `google-chrome` 或 `chromium`
   - 用途：使用 headless 模式渲染 HTML 为图片，实现准确的封面文字合成
   - 验证：
     - macOS/Linux: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version`
     - Windows: `"C:\Program Files\Google\Chrome\Application\chrome.exe" --version`

**Windows 用户注意**：
- Chrome 必须安装在默认位置，或确保 `chrome.exe` 在系统 PATH 中
- 如遇到"Chrome not found"错误，请检查 Chrome 安装路径
- 中文字体使用系统默认的宋体（SimSun）或微软雅黑（Microsoft YaHei）

### 环境检查

```bash
# 基础功能（必需）
python3 --version   # Python 3.x（公众号发布）

# 配图功能（可选，至少装一个）
node --version      # Node.js >= 14.0.0
which codex         # 或 which agy

# 封面文字合成（可选）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version

# 测试配图环境
node scripts/generate-image.js --help

# 测试封面文字合成
node scripts/compose-cover.js --help

# 只检查最终 prompt 策略，不调用生图后端
node scripts/generate-image.js --prompt-file imgs/prompts/00-cover.md --check-prompt

# 测试发布脚本
python3 scripts/wechat_mp_publish.py --help
```

### 微信公众号配置（发布功能必需）

首次使用公众号发布功能，需配置 **AppID / AppSecret**：

```bash
mkdir -p ~/.config/wechat-mp && chmod 700 ~/.config/wechat-mp
# 创建配置文件 ~/.config/wechat-mp/wechat.env.profile，内容：
#   WECHAT_APP_ID=wx...
#   WECHAT_APP_SECRET=...
chmod 600 ~/.config/wechat-mp/wechat.env.profile
```

详见技能目录下的 `wechat.env.profile.example` 示例文件。

## 适用场景

- 公众号古诗词推文创作
- 亲子古诗词学习材料制作
- 学生考试备考资料准备
- 双语古诗词启蒙内容
- 课堂教学辅助材料

## 许可

供个人学习和内容创作使用。
