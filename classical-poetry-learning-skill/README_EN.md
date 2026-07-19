<!-- Language: [中文](README.md) | [English](README_EN.md) -->

# Classical Chinese Poetry Learning Skill

> Generate professional classical Chinese poetry appreciation articles in one step, tailored for WeChat public accounts and parent-child teaching. Content is easy to understand, exam-focused, bilingual-ready, and can auto-generate illustrations.

## Overview

This is a Claude Skill that helps parents, teachers, and content creators quickly produce high-quality classical Chinese poetry learning materials. The generated content is plain-spoken and accessible, closely tied to primary and secondary school exam points, and designed for parents to explain and children to understand.

Key highlights:

- **Standardized structure**: A consistent 7-module layout for easy batch production and reading
- **Content proofreading**: 7-dimension self-check to ensure zero errors in the original poem text, historical facts, and typos
- **Bilingual support**: Chinese-only or Chinese-English bilingual versions
- **Auto illustration**: Automatically generates and inserts illustrations based on the poem's imagery
- **WeChat cover image**: Generates a text-free visual background by default; verified title and author stay in structured metadata and WeChat fields
- **One-click publishing**: Converts the article into paste-ready WeChat HTML and creates a draft in the WeChat Official Account backend

## Features

### 1. Standard 7-Module Structure

Each article contains the following modules:

1. Original poem text (with error-prone character annotations)
2. Poet profile (child-friendly version)
3. Creative background (plain-language version)
4. Full plain-language translation (line-by-line, conversational)
5. Line-by-line in-depth appreciation (parent explanation focus)
6. Primary/secondary school exam points (test-oriented core)
7. Parent-child summary (brief recap)

### 2. Content Proofreading & Self-Check

After generation, a 7-dimension proofreading pass runs automatically:

| Dimension | What is checked |
|-----------|-----------------|
| Original text check | Character-by-character accuracy, punctuation |
| Historical facts check | Poet's dates, dynasty, creative background |
| Literary knowledge check | Genre, rhetoric, theme judgment |
| Language & wording check | Typos, proper nouns |
| Error-prone character check | Annotation accuracy and relevance |
| Exam point check | Practicality of dictation and answer templates |
| Bilingual check | Chinese-English alignment, translation quality |

### 3. Bilingual Support

- **Chinese-only** (default): `--lang=zh_cn`
- **Chinese-English bilingual**: `--lang=zh_cn,en_us`

### 4. Auto Illustration (Optional)

Recommends an illustration style based on the poem type, generates AI image prompts, and invokes an image generation backend:

| Poem type | Recommended style |
|-----------|-------------------|
| Landscape/pastoral poetry | Watercolor scene (watercolor-scene) |
| Frontier poetry | Ink wash (ink-notes-scene) |
| Homesickness poetry | Warm tones (warm-scene) |
| Object-chanting poetry | Nature style (nature-scene) |
| Philosophical poetry | Hand-drawn educational (hand-drawn-edu) |

See the [Illustration Guide](ILLUSTRATION_GUIDE.md) for details.

### 5. WeChat Cover Image (Optional)

Generate a cover image for WeChat publishing, keeping the same style as the content illustrations:

- Generate a **text-free background** by default so the image model cannot misspell the title, poet, or poem.
- Store title, dynasty, author, and poem lines once in `poem-meta.json`; populate WeChat `title` / `author` fields from that source of truth.
- Reserve a clean safe area for a future deterministic typesetting layer.
- Use `--allow-ai-text` only when the user explicitly accepts text-rendering risk, then verify every character.

The cover defaults to **2.35:1** (WeChat header image standard ratio), with the visual focal point inside the mobile safe zone. An optional 1:1 sharing thumbnail can also be generated.

### 6. Convert to HTML & Publish to WeChat Draft Box (Optional)

Convert the finished article into paste-ready WeChat HTML and push it to the Official Account draft box:

1. **Pick a theme & convert to HTML**: Choose one of **11 themes** (`references/themes/`) that fits the poem's mood and scenario (classical ink, minimal ink, vintage magazine, warm order, cyan grid, yamabuki, yanqi-lake, soft green, etc.) to generate WeChat layout with fully inline styles. Produces a preview version (with cover) and a publish version (body excludes the cover copy and main title).
2. **Create draft**: Use `scripts/wechat_mp_publish.py` to upload the cover, rewrite inline images, and create a draft. **Draft-only by default, never auto-publish.**
3. **Publish**: Only submit for publishing after explicit user confirmation (irreversible operation).

First-time use requires configuring the WeChat AppID/AppSecret (saved to `~/.config/wechat-mp/wechat.env.profile`). See the publishing section in SKILL.md and the [WeChat API reference](references/wechat_api.md).

> Always convert to HTML before publishing — do not feed raw Markdown to the publish script, or the layout will be lost.

## Usage

Trigger the skill with natural language:

```
Write an appreciation of "Quiet Night Thoughts" for a 2nd grader
Create bilingual learning material for "Spring Dawn" --lang=zh_cn,en_us
Write an appreciation of "Climbing Stork Tower" for 7th grade, focus on philosophy and exam points
Create learning material for "Viewing the Waterfall at Mount Lu" with watercolor illustrations
Make a WeChat cover for "Quiet Night Thoughts", consistent with the illustrations
Convert "Viewing the Waterfall at Mount Lu" to WeChat HTML and create a draft
```

### Trigger Keywords

- **Basic creation**: poetry learning material, WeChat article, poetry appreciation, explaining a poem to a child
- **Illustration**: with illustration, add images, generate pictures, insert illustrations
- **Cover image**: make a cover, cover image, WeChat cover, generate cover
- **HTML/Publishing**: convert to HTML, WeChat HTML, publish to WeChat, create draft, push to Official Account
- **Emphasize proofreading**: pay attention to proofreading, check typos, ensure historical accuracy

## Directory Structure

```
classical-poetry-learning-skill/
├── SKILL.md                        # Main skill file (core instructions)
├── README.md                       # Chinese README
├── README_EN.md                    # English README (this file)
├── ILLUSTRATION_GUIDE.md           # Illustration usage guide
├── scripts/
│   ├── generate-image.js           # Image generation script (codex / gemini)
│   └── wechat_mp_publish.py        # WeChat draft/publish script
├── references/
│   ├── template_zh_cn.md           # Chinese template
│   ├── template_zh_cn_en_us.md     # Bilingual template
│   ├── wechat_api.md               # WeChat Official Account API reference
│   └── themes/                     # WeChat HTML theme library (11 themes)
│       ├── index.md               # Theme selection index (scenario → theme)
│       ├── theme-classical-ink.md # Classical ink (recommended default)
│       ├── theme-*.md             # 10 more optional themes
│       └── examples/              # HTML previews for each theme
└── evals/
    └── evals.json                  # Test cases
```

## Requirements & Dependencies

### ✅ Works Out of the Box (Zero External Dependencies)

These features need **no third-party packages or external tools** — pure built-in capabilities:

- ✅ **Text creation**: Generate poetry appreciation articles (Chinese / bilingual)
- ✅ **Content proofreading**: 7-dimension automatic self-check
- ✅ **HTML conversion**: Convert to WeChat-ready HTML (11 themes, static, no CDN)
- ✅ **WeChat publishing**: Create drafts/publish (needs AppID/AppSecret, but no package install)

> 📦 **No third-party dependencies**:
> - `wechat_mp_publish.py` (Python) uses only the standard library. The optional `markdown` package degrades gracefully — it runs fine without it, only complex Markdown syntax falls back to plain rendering
> - `generate-image.js` (Node) uses only Node built-in modules — no `npm install`, no `package.json`

### ⚠️ Optional Features (Require External Tools)

These features depend on an **AI image generation tool**. Skip if you don't need illustrations/covers:

- **Illustration generation**: poem scene images, background scenes
- **Cover image generation**: text-free WeChat header background by default

**Required tools (install at least one)**:
1. **codex-cli** (OpenAI Codex CLI, recommended)
   - Install: `npm install -g codex-cli` or see https://openai.com/codex
   - Verify: `codex --version`
   
2. **agy** (Antigravity CLI, Google Gemini)
   - Install: see https://antigravity.google/docs/cli-getting-started
   - Verify: `agy --version`

### Environment Check

```bash
# Core features (required)
python3 --version   # Python 3.x (WeChat publishing)

# Illustration features (optional, install at least one)
node --version      # Node.js >= 14.0.0
which codex         # or which agy

# Test illustration environment
node scripts/generate-image.js --help

# Test publish script
python3 scripts/wechat_mp_publish.py --help
```

## Use Cases

- WeChat public account poetry articles
- Parent-child poetry learning materials
- Student exam preparation resources
- Bilingual poetry enlightenment content
- Classroom teaching aids

## License

For personal learning and content creation use.
