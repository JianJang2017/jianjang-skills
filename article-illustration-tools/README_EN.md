# Article Illustration Tools

Automatically illustrate markdown articles with AI-generated images using a three-dimension style system and production-ready image generation.

---

## Overview

Analyzes article structure, recommends optimal image positions, generates detailed prompts, and creates images using codex-cli or gemini backends with built-in reliability (timeout, retry, verification).

---

## Features

- 🎯 **Smart Analysis**: Automatically analyzes article structure and recommends image positions
- 🎨 **Three-Dimension Style System**: Type × Style × Palette (552 combinations from 21 presets)
- 🤖 **Dual Backends**: Codex CLI and Antigravity CLI (agy) with auto-detection
- 🚀 **Batch Generation**: Concurrent image generation with reliability (timeout, retry, verification)
- 📝 **Seamless Integration**: Automatically inserts images into markdown
- 🌐 **Bilingual**: Supports both English and Chinese

---

## Quick Start

### Installation

```bash
# Copy to Claude skills directory
cp -r article-illustration-tools ~/.claude/skills/

# Or extract from tarball
cd ~/.claude/skills
tar -xzf article-illustration-tools-1.0.0.tar.gz

# Verify installation
bash article-illustration-tools/scripts/test.sh
```

### Usage

**Trigger Keywords:**

- "illustrate article", "add images to article", "generate article images"
- "为文章配图", "给文章生成图片", "添加文章图片" (Chinese)

**Usage Scenarios:**

1. **Specify file + style**
   ```
   Illustrate this article: ./docs/guide.md with infographic style
   ```

2. **Paste content + specify style**
   ```
   Add images to this tutorial with hand-drawn style:
   [paste article content]
   ```

3. **Auto-recommend (smartest)**
   ```
   Illustrate this article, auto-recommend style and count:
   [paste article content]
   ```

**Best Practices:**
- Short articles (<1000 words): 1-2 images
- Medium articles (1000-3000 words): 3-4 images
- Long articles (3000-5000 words): 5-6 images
- Tutorials: 1 image per major step

---

## Requirements

### Essential
- **Node.js 14+**: Required for image generation script
  - macOS: `brew install node`
  - Linux: `sudo apt install nodejs npm` or `sudo yum install nodejs npm`
  - Windows: Download from [nodejs.org](https://nodejs.org)

### Image Generation Backend (at least one)

**Option 1: Codex CLI (Recommended)**
- **Website**: https://openai.com/zh-Hans-CN/codex
- **Install**: Visit website or `npm install -g codex-cli`
- **Verify**: `codex --version`
- **Configuration**: 
  - Check `~/.codex/config.toml`
  - If you see `service_tier` line, **delete it** (this causes errors)
  - Correct config should NOT have `service_tier` setting

**Option 2: Antigravity CLI**
- **Website**: https://antigravity.google/docs/cli-getting-started
- **Install**: `curl -fsSL https://antigravity.google/install.sh | sh`
- **Verify**: `agy --version`

---

## Style System: Three Dimensions

This skill uses a **Three-Dimension Style System** combining **Type × Style × Palette**:

| Dimension | Controls | Examples |
|-----------|----------|----------|
| **Type** | Information structure | infographic, scene, flowchart, comparison, framework, timeline |
| **Style** | Rendering aesthetic | sketch-notes, vector, blueprint, warm, etc. |
| **Palette** | Color scheme (optional) | macaron, warm, mono-ink, neon |

### Quick Presets (Recommended)

Bundle Type + Style + Palette in one preset. Pick by content category:

**📚 Knowledge & Education**
- `hand-drawn-edu` ⭐ **Default** - Hand-drawn educational infographic (warm cream paper, pastel blocks)
- `edu-visual` - Vector with macaron palette
- `knowledge-base` / `tutorial` / `process-flow` / `saas-guide`

**🔧 Technical & Engineering**
- `tech-explainer` - Blueprint infographic for API docs, system metrics
- `system-design` / `architecture` / `science-paper`

**📊 Data & Analysis**
- `data-report` - Editorial infographic for metrics, dashboards
- `versus` / `business-compare`

**📖 Narrative & Creative**
- `storytelling` - Warm scene for personal essays
- `lifestyle` / `history` / `evolution`

**🎭 Editorial & Opinion**
- `opinion-piece` / `cinematic` / `ink-notes-compare`

### Or use Core Styles directly

| Core Style | Best For |
|------------|----------|
| `hand-drawn` ⭐ | Default. Educational, friendly, universal |
| `vector` | Knowledge articles, tutorials, tech |
| `minimal-flat` | SaaS, productivity, knowledge sharing |
| `sci-fi` | AI, frontier tech, system design |
| `editorial` | Processes, data, journalism |
| `scene` | Narratives, emotional, lifestyle |
| `poster` | Opinion, editorial, cultural |

### Type × Style Compatibility

Not all combinations work equally well:

| | sketch-notes | vector | blueprint | warm | screen-print |
|---|:---:|:---:|:---:|:---:|:---:|
| infographic | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓ |
| scene | ✗ | ✓ | ✗ | ✓✓ | ✓✓ |
| flowchart | ✓✓ | ✓✓ | ✓✓ | ✓ | ✗ |
| comparison | ✓✓ | ✓✓ | ✓ | ✓ | ✓ |
| framework | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓ |
| timeline | ✓ | ✓ | ✓ | ✓ | ✓ |

✓✓ = highly recommended | ✓ = compatible | ✗ = avoid

---

## Image Generation Tool

The skill uses an advanced image generation wrapper (`scripts/generate-image.js`) with production-grade reliability:

### Key Features

- ✅ **Real Verification**: Ensures output files actually exist (not just process exit code)
- ✅ **Auto-Location**: Finds images in backend-specific directories and copies to requested path
- ⏱️ **Timeout Control**: Per-image timeout (default 5 minutes, configurable with `--timeout`)
- 🔄 **Retry Mechanism**: Automatic retry on failure (default 1 retry, configurable with `--retries`)
- 🚀 **Batch Mode**: Generate multiple images concurrently (`--batch tasks.json --concurrency N`)
- 🔒 **Concurrency-Safe**: Prevents multiple tasks from claiming the same source image
- 📊 **Machine-Readable Output**: Final JSON line for programmatic integration

### Single Image Generation

```bash
cd ~/.claude/skills/article-illustration-tools
node scripts/generate-image.js \
  --prompt-file prompts/01-image.md \
  --output imgs/01-image.png \
  --aspect-ratio 16:9 \
  --provider auto
```

### Batch Generation

```bash
# Create tasks.json
cat > tasks.json << 'EOF'
[
  {"prompt-file": "prompts/01.md", "output": "imgs/01.png"},
  {"prompt-file": "prompts/02.md", "output": "imgs/02.png"},
  {"prompt-file": "prompts/03.md", "output": "imgs/03.png"}
]
EOF

# Generate all images concurrently
node scripts/generate-image.js \
  --batch tasks.json \
  --concurrency 3 \
  --timeout 300 \
  --retries 1
```

### How It Works

**Codex Backend**:
1. Tracks existing session directories before invocation
2. Calls `codex exec` to generate image
3. Locates new image in `~/.codex/generated_images/<session>/`
4. Copies to requested output path
5. Verifies file exists and is non-empty

**Gemini Backend**:
1. Calls `agy -p` with generation prompt
2. Scans multiple candidate directories for artifacts
3. Extracts paths from stdout
4. Copies to requested output path
5. Verifies file exists and is non-empty

### Options

```
--provider, -p <auto|codex|gemini>   Backend selection (default: auto)
--prompt-file <path>                 Prompt markdown file
--output, -o <path>                  Output image path (verified)
--aspect-ratio, --ar <W:H>           Aspect ratio (default: 16:9)
--timeout <seconds>                  Per-image timeout (default: 300)
--retries <n>                        Retries on failure (default: 1)
--concurrency <n>                    Parallel batch jobs (default: 3)
--batch <tasks.json>                 Batch mode with JSON task list
```

---

## Workflow

1. **Analyze** article structure (headings, sections, paragraphs)
2. **Recommend** image positions and count based on content
3. **Choose** style using presets or custom Type × Style × Palette
4. **Generate** detailed prompts for each image
5. **Create** images using Codex CLI or Gemini with timeout/retry
6. **Insert** images into article with proper positioning
7. **Verify** output files exist and are valid

**Tips:**
- Well-structured articles (clear headings) produce better results
- Technical content works best with `tech-explainer`, `system-design`, or `blueprint`
- Tutorials benefit from `hand-drawn-edu` or `tutorial` presets
- Let AI auto-recommend when unsure (defaults to `hand-drawn-edu`)

---

## Output Structure

```
output-directory/
├── outline.md              # Image generation plan
├── prompts/               # Prompt files
│   ├── 01-image.md
│   └── 02-image.md
├── imgs/                  # Generated images
│   ├── 01-image.png
│   └── 02-image.png
└── article-with-images.md # Article with images
```

---

## Examples

### Technical Documentation
```
Illustrate this architecture guide with tech-explainer preset
```
**Result**: 5 blueprint-style diagrams showing architecture and components

### Tutorial
```
Add images to this deep learning tutorial with hand-drawn-edu preset
```
**Result**: 7 hand-drawn educational illustrations for each step

### API Documentation
```
Illustrate this API guide, auto-recommend
```
**Result**: 4 infographic-style reference charts (auto-selected `hand-drawn-edu`)

---

## Demo

### Test Scenario: Generate a Single Image

We demonstrate the image generation tool's capabilities with a simple test case:

**Prompt Content:**
> A cute fluffy orange tabby kitten leaping playfully through tall green grass in a sunlit meadow, chasing 3-4 colorful butterflies (yellow, blue, white) fluttering around. Warm golden-hour lighting with soft sun rays filtering through. Wildflowers like daisies and dandelions scattered in the grass. The kitten has wide curious eyes and outstretched paws mid-jump. Painterly storybook illustration style with soft edges, warm cozy atmosphere, bokeh background effect. Aspect ratio 16:9. Family-friendly, joyful, whimsical mood.

**Command:**
```bash
cd ~/.claude/skills/article-illustration-tools
node scripts/generate-image.js \
  --provider codex \
  --prompt-file demo/kitten-prompt.md \
  --output demo/kitten-codex.png \
  --aspect-ratio 16:9 \
  --timeout 240
```

**Generation Results:**

| Backend | Status | File Size | Resolution | Time | Tokens |
|---------|--------|-----------|------------|------|--------|
| **Codex** | ✅ Success | 2.1 MB | 1672×941 | ~42s | 27,311 |
| **Gemini** | ⚠️ Quota Exhausted | - | - | - | - |

**Output Example:**
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

**Key Features Verified:**
- ✅ **Real Verification**: Confirmed file exists and is non-empty (2.1 MB PNG)
- ✅ **Auto-Location**: Located image from `~/.codex/generated_images/<session>/` and copied to specified path
- ✅ **Failure Detection**: Correctly reported Gemini quota exhaustion error and retried
- ✅ **Machine-Readable**: Final line JSON output for programmatic integration

**View Generated Image:**
```bash
open demo/kitten-codex.png
# or
file demo/kitten-codex.png
# → PNG image data, 1672 x 941, 8-bit/color RGB, non-interlaced
```

Full prompt file: [demo/kitten-prompt.md](demo/kitten-prompt.md)

---

## Testing

Run the test suite:
```bash
cd ~/.claude/skills/article-illustration-tools/scripts
bash test.sh
```

This checks:
- Node.js version
- codex-cli availability
- agy (Antigravity CLI) availability
- Test image generation

---

## Troubleshooting

**Codex configuration error:**
```bash
# Edit config file
nano ~/.codex/config.toml
# Remove or comment out the service_tier line
```

**No backend available:**
Install at least one of Codex CLI or Antigravity CLI.

**Permission denied:**
```bash
chmod +x ~/.claude/skills/article-illustration-tools/scripts/*.sh
```

**Image generation timeout:**
Increase timeout: `--timeout 600` (10 minutes)

**Batch images identical:**
This was a bug, now fixed. Concurrent tasks no longer claim the same source image.

---

## Documentation

- **README.md** - Complete overview (bilingual)
- **README_EN.md** - English-only version (this file)
- **SKILL.md** - Complete workflow and technical details
- **scripts/README.md** - Image generation tool documentation

---

## License

MIT

---

## Contributing

Issues and pull requests are welcome!

---

**Version**: 1.0.0  
**Last Updated**: 2026-06-21  
**Project**: https://github.com/your-repo/article-illustration-tools
