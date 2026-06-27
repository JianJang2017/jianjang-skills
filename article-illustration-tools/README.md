# Article Illustration Tools

[中文](#中文) | [English](README_EN.md)

---

## 概述

为markdown文章自动配图的AI工具。分析文章结构、智能推荐图片位置、生成详细提示词，并使用codex-cli或gemini后端创建图片，带生产级可靠性保证。

---

## 功能特点

- 🎯 **智能分析**：自动分析文章结构并推荐图片位置
- 🎨 **三维风格系统**：Type × Style × Palette（21个预设，552种组合）
- 🤖 **双后端支持**：Codex CLI 和 Antigravity CLI (agy)，自动检测
- 🚀 **批量生成**：并发生成多张图片，带超时/重试/验证
- 📝 **无缝集成**：自动将图片插入到markdown中
- 🌐 **双语支持**：支持中英文

---

## 快速开始

### 安装

```bash
# 复制到Claude技能目录
cp -r article-illustration-tools ~/.claude/skills/

# 或从压缩包解压
cd ~/.claude/skills
tar -xzf article-illustration-tools-1.0.0.tar.gz

# 验证安装
bash article-illustration-tools/scripts/test.sh
```

### 使用方法

**触发关键词：**

中文："为文章配图"、"给文章生成图片"、"文章配图"、"生成文章插图"、"添加文章图片"

英文："illustrate article"、"add images to article"、"generate article images"

**使用场景：**

1. **指定文件 + 风格**
   ```
   为这篇文章配图：./docs/guide.md，使用信息图风格
   ```

2. **粘贴内容 + 指定风格**
   ```
   给这个教程配图，用手绘风格：
   [粘贴文章内容]
   ```

3. **自动推荐（最智能）**
   ```
   为下面的文章配图，自动推荐数量和风格：
   [粘贴文章内容]
   ```

**最佳实践：**
- 短文（<1000字）：1-2张图
- 中文（1000-3000字）：3-4张图
- 长文（3000-5000字）：5-6张图
- 教程：每个主要步骤1张图

---

## 依赖要求

### 必需
- **Node.js 14+**：运行图片生成脚本
  - macOS: `brew install node`
  - Linux: `sudo apt install nodejs npm` 或 `sudo yum install nodejs npm`
  - Windows: 从 [nodejs.org](https://nodejs.org) 下载

### 图片生成后端（至少一个）

**选项1：Codex CLI（推荐）**
- **官网**：https://openai.com/zh-Hans-CN/codex
- **安装**：访问官网或 `npm install -g codex-cli`
- **验证**：`codex --version`
- **配置**：
  - 检查 `~/.codex/config.toml`
  - 如果看到 `service_tier` 行，**删除它**（会导致错误）
  - 正确的配置不应该有 `service_tier` 设置

**选项2：Antigravity CLI**
- **官网**：https://antigravity.google/docs/cli-getting-started
- **安装**：`curl -fsSL https://antigravity.google/install.sh | sh`
- **验证**：`agy --version`

---

## 风格系统：三维设计

技能采用 **三维风格系统**：**Type（类型）× Style（风格）× Palette（调色板）**

| 维度 | 控制 | 示例 |
|------|------|------|
| **Type 类型** | 信息结构 | infographic, scene, flowchart, comparison, framework, timeline |
| **Style 风格** | 渲染美学 | sketch-notes, vector, blueprint, warm 等 |
| **Palette 调色板** | 配色方案（可选）| macaron, warm, mono-ink, neon |

### 推荐使用预设（Presets）

预设打包了 Type + Style + Palette，按内容类别选择：

**📚 知识教育类**
- `hand-drawn-edu` ⭐ **默认** - 手绘教育信息图（暖米纸、黑线、马卡龙色块）
- `edu-visual` - 矢量插画 + 马卡龙配色
- `knowledge-base` / `tutorial` / `process-flow` / `saas-guide`

**🔧 技术工程类**
- `tech-explainer` - 蓝图信息图，适合 API 文档、技术深度
- `system-design` / `architecture` / `science-paper`

**📊 数据分析类**
- `data-report` - 编辑风信息图，适合数据新闻、仪表盘
- `versus` / `business-compare`

**📖 叙事创意类**
- `storytelling` - 暖色场景，适合个人随笔
- `lifestyle` / `history` / `evolution`

**🎭 编辑观点类**
- `opinion-piece` / `cinematic` / `ink-notes-compare`

### 或直接使用核心风格

| 核心风格 | 最适合 |
|---------|--------|
| `hand-drawn` ⭐ | 默认。教育、友好、通用 |
| `vector` | 知识文章、教程、技术 |
| `minimal-flat` | SaaS、生产力、知识分享 |
| `sci-fi` | AI、前沿技术、系统设计 |
| `editorial` | 流程、数据、新闻 |
| `scene` | 叙事、情感、生活方式 |
| `poster` | 观点、编辑、文化 |

### Type × Style 兼容性

不是所有组合都同样有效：

| | sketch-notes | vector | blueprint | warm | screen-print |
|---|:---:|:---:|:---:|:---:|:---:|
| infographic | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓ |
| scene | ✗ | ✓ | ✗ | ✓✓ | ✓✓ |
| flowchart | ✓✓ | ✓✓ | ✓✓ | ✓ | ✗ |
| comparison | ✓✓ | ✓✓ | ✓ | ✓ | ✓ |
| framework | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓ |
| timeline | ✓ | ✓ | ✓ | ✓ | ✓ |

✓✓ = 强烈推荐 | ✓ = 兼容 | ✗ = 避免

---

## 图片生成工具

技能使用先进的图片生成封装工具（`scripts/generate-image.js`），具有生产级可靠性：

### 核心特性

- ✅ **真实验证**：确保输出文件实际存在（不只是检查进程退出码）
- ✅ **自动定位**：在后端专用目录中查找图片并复制到指定路径
- ⏱️ **超时控制**：单张图片超时限制（默认5分钟，可用 `--timeout` 配置）
- 🔄 **重试机制**：失败自动重试（默认重试1次，可用 `--retries` 配置）
- 🚀 **批量模式**：并发生成多张图片（`--batch tasks.json --concurrency N`）
- 🔒 **并发安全**：防止多个任务抢同一张源图片
- 📊 **机器可读输出**：最后一行 JSON 输出供程序化集成

### 单张图片生成

```bash
cd ~/.claude/skills/article-illustration-tools
node scripts/generate-image.js \
  --prompt-file prompts/01-image.md \
  --output imgs/01-image.png \
  --aspect-ratio 16:9 \
  --provider auto
```

### 批量生成

```bash
# 创建 tasks.json
cat > tasks.json << 'EOF'
[
  {"prompt-file": "prompts/01.md", "output": "imgs/01.png"},
  {"prompt-file": "prompts/02.md", "output": "imgs/02.png"},
  {"prompt-file": "prompts/03.md", "output": "imgs/03.png"}
]
EOF

# 并发生成所有图片
node scripts/generate-image.js \
  --batch tasks.json \
  --concurrency 3 \
  --timeout 300 \
  --retries 1
```

### 工作原理

**Codex 后端：**
1. 调用前记录已存在的 session 目录
2. 调用 `codex exec` 生成图片
3. 在 `~/.codex/generated_images/<session>/` 定位新图片
4. 复制到请求的输出路径
5. 验证文件存在且非空

**Gemini 后端：**
1. 调用 `agy -p` 执行生成提示词
2. 扫描多个候选目录查找 artifacts
3. 从 stdout 提取路径
4. 复制到请求的输出路径
5. 验证文件存在且非空

### 选项说明

```
--provider, -p <auto|codex|gemini>   后端选择（默认：auto）
--prompt-file <path>                 提示词 markdown 文件
--output, -o <path>                  输出图片路径（会验证）
--aspect-ratio, --ar <W:H>           宽高比（默认：16:9）
--timeout <seconds>                  单张图片超时（默认：300秒）
--retries <n>                        失败重试次数（默认：1）
--concurrency <n>                    批量并发数（默认：3）
--batch <tasks.json>                 批量模式，使用 JSON 任务列表
```

---

## 工作流程

1. **分析**文章结构（标题、章节、段落）
2. **推荐**图片位置和数量（基于内容分析）
3. **选择**风格（使用预设或自定义 Type × Style × Palette）
4. **生成**每张图的详细提示词
5. **创建**图片（使用 Codex CLI 或 Gemini，带超时/重试）
6. **插入**图片到文章中，位置准确
7. **验证**输出文件存在且有效

**技巧：**
- 结构清晰的文章（明确的标题层次）效果最好
- 技术内容适合 `tech-explainer`、`system-design` 或 `blueprint`
- 教程适合 `hand-drawn-edu` 或 `tutorial` 预设
- 不确定时让AI自动推荐（默认使用 `hand-drawn-edu`）

---

## 输出结构

```
output-directory/
├── outline.md              # 图片生成计划
├── prompts/               # 提示词文件
│   ├── 01-image.md
│   └── 02-image.md
├── imgs/                  # 生成的图片
│   ├── 01-image.png
│   └── 02-image.png
└── article-with-images.md # 带图片的文章
```

---

## 使用示例

### 技术文档
```
为这篇架构指南配图，使用tech-explainer预设
```
**结果**：5张蓝图风格的架构图展示组件和系统

### 教程文章
```
给这个深度学习教程配图，用hand-drawn-edu预设
```
**结果**：7张手绘教育插图对应每个步骤

### API文档
```
为这篇API指南配图，自动推荐
```
**结果**：4张信息图风格的参考图表（自动选择 `hand-drawn-edu`）

---

## Demo 演示

### 测试场景：生成单张图片

我们用一个简单的测试案例来演示图片生成工具的能力：

**Prompt内容：**
> 一只可爱的橙色小猫咪在阳光明媚的草地上追逐彩色蝴蝶。暖色调金色时光，柔和的阳光穿过场景。草地上散落着雏菊和蒲公英等野花。小猫眼睛圆睁充满好奇，空中伸展着小爪子。绘本插画风格，柔和边缘，温暖舒适的氛围，背景虚化效果。宽高比 16:9。家庭友好，欢乐，异想天开的情绪。

**执行命令：**
```bash
cd ~/.claude/skills/article-illustration-tools
node scripts/generate-image.js \
  --provider codex \
  --prompt-file demo/kitten-prompt.md \
  --output demo/kitten-codex.png \
  --aspect-ratio 16:9 \
  --timeout 240
```

**生成结果：**

| 后端 | 状态 | 文件大小 | 分辨率 | 耗时 | Tokens |
|------|------|----------|--------|------|--------|
| **Codex** | ✅ 成功 | 2.1 MB | 1672×941 | ~42秒 | 27,311 |
| **Gemini** | ⚠️ 配额耗尽 | - | - | - | - |

**输出示例：**
```
🎨 Article Illustration Tools - Image Generator
Available backends: codex, gemini
Selected provider: codex

[kitten-codex.png] Generating via codex...
[kitten-codex.png] ✅ 2161211 bytes → demo/kitten-codex.png

──────────────────────────────────────────
Summary: 1 succeeded, 0 failed (out of 1)
{"success":true,"count":1,"succeeded":1,"failed":0,"results":[...]}
```

**关键特性验证：**
- ✅ **真实验证**：确认文件存在且非空（2.1 MB PNG）
- ✅ **自动定位**：从 `~/.codex/generated_images/<session>/` 定位并复制到指定路径
- ✅ **失败检测**：Gemini配额耗尽时正确报告错误并重试
- ✅ **机器可读**：最后一行JSON输出供程序化集成

**查看生成的图片：**
```bash
open demo/kitten-codex.png
# 或
file demo/kitten-codex.png
# → PNG image data, 1672 x 941, 8-bit/color RGB, non-interlaced
```

完整prompt文件见：[demo/kitten-prompt.md](demo/kitten-prompt.md)

---

## 测试

运行测试脚本：
```bash
cd ~/.claude/skills/article-illustration-tools/scripts
bash test.sh
```

这将检查：
- Node.js 版本
- codex-cli 可用性
- agy (Antigravity CLI) 可用性
- 测试图片生成

---

## 故障排除

**Codex配置错误：**
```bash
# 编辑配置文件
nano ~/.codex/config.toml
# 删除或注释掉 service_tier 这一行
```

**没有可用的后端：**
至少安装Codex CLI或Antigravity CLI中的一个。

**权限错误：**
```bash
chmod +x ~/.claude/skills/article-illustration-tools/scripts/*.sh
```

**图片生成超时：**
增加超时时间：`--timeout 600`（10分钟）

**批量生成的图片相同：**
这是个bug，已修复。现在并发任务不会再抢同一张源图片。

---

## 文档

- **README.md** - 完整概览（本文件，中文）
- **README_EN.md** - 英文版本
- **SKILL.md** - 完整工作流程和技术细节
- **scripts/README.md** - 图片生成工具文档

---

## 许可证

MIT

---

## 贡献

欢迎提交问题和PR！

---

**版本**: 1.0.0  
**最后更新**: 2026-06-21  
**项目**: https://github.com/your-repo/article-illustration-tools
