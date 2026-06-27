# Markdown to HTML Formatter

[中文](./README.md)

Turn a Markdown document into a beautifully formatted HTML article that **pastes cleanly into the WeChat Official Account editor or email clients**.

Core constraint: every style is inlined in a `style="..."` attribute — no `<style>` blocks, no external stylesheets, no `class` selectors. WeChat's editor and most email clients strip all of those and keep only inline styles. Output is fully inlined HTML in a 680px mobile-friendly container.

## What it does

- Reads a Markdown source (file path or raw text), maps each element to a theme component, and assembles finished HTML
- Ships **40 built-in themes** (original curated themes + markdown2wechat ports), selectable by name or auto-recommended from the content and its tone
- Renders code blocks with `&nbsp;`/`<br>` (not `<pre>`) so WeChat doesn't collapse whitespace
- Renders tables, quotes, lists, images, and semantic cards in the theme's style
- Bundles a validation script that flags style-dropping markup before you ship

## Quick start

The skill triggers automatically when you ask for formatting. Typical phrasings:

```
Format ~/notes/reading-notes.md into a WeChat article
Turn this markdown into nice HTML using the "cyan-grid" theme
Beautify this technical article into a web page I can paste into WeChat
Re-format this md with a different theme style
```

Output is written to a same-named `.html` next to the source by default, and the reply states which theme was used and why.

## Theme catalog

Themes fall into two groups. **Genre themes** are designed for a specific kind of writing; **style themes** are genre-neutral and matched by tone. When no theme is named, the skill matches by genre first, then falls back to the best-fitting style theme.

### Genre themes

| Theme | Name | Best for |
| --- | --- | --- |
| `native-blueprint` | 原生蓝图 | AI-Native, software engineering paradigms, technical strategy, architecture, long-form technical analysis. Black/white body + light-blue neon headings + dark code blocks |
| `cyan-grid` | 青格笔记 | Study plans, learning retros, resource lists, knowledge notes, tutorials. Light cyan grid-paper background + cyan headings + clean tables |

### Style themes (genre-neutral)

#### Original curated themes

| Theme | Name | Tone |
| --- | --- | --- |
| `minimal-ink` | 极简墨色 | Off-white paper, ink body, restrained whitespace — calm, slow reading for long text |
| `vintage-magazine` | 复古杂志 | Vintage paper, strong headings, journal kickers — print feel and narrative rhythm |
| `noir-stage` | 黑金舞台 | Dark page, gold highlights, spotlight emphasis — ceremony and strong pauses |
| `notebook-sticky` | 手账便签 | Warm paper, dashed borders, sticky-note highlights — friendly, casual journal feel |
| `warm-order` | 暖白秩序 | Warm-white page, low-saturation orange accents, tidy cards — calm and trustworthy |
| `bluegray-brief` | 蓝灰简报 | Blue-gray page, strict borders, large key numbers — compact, cool, scannable brief |
| `cool-blueprint` | 冷感蓝图 | Cool-white page, blue signal color, engineering info blocks — order and scannability |
| `green-editorial` | 森绿编辑 | Light-green page, editorial headings, side accent rules — fresh and organized |

#### markdown2wechat ports (m2w- series)

30 themes ported from the markdown2wechat project, prefixed `m2w-` to avoid naming conflicts. Cover a wide range of color palettes and styles:

| Theme | Name | Color/Style |
| --- | --- | --- |
| `m2w-simple` | 简 | Clean white, minimal decoration |
| `m2w-geek-black` | 极客黑 | Dark, strong code aesthetic |
| `m2w-obsidian` | 黑曜石 | Dark theme |
| `m2w-minimal-black` | 极简黑 | Minimal black |
| `m2w-night-purple` | 夜幕紫 | Night purple |
| `m2w-brilliant-purple` | 荧光紫 | Bright purple |
| `m2w-rose-purple` | 玫瑰紫 | Rose purple |
| `m2w-vivid-blue` | 灵动蓝 | Lively blue |
| `m2w-luminous-blue` | 极光蓝 | Aurora blue |
| `m2w-tech-blue` | 科技蓝 | Tech blue |
| `m2w-fullstack-blue` | 全栈蓝 | Full-stack blue |
| `m2w-orange-blue` | 橙蓝对撞 | Orange-blue contrast |
| `m2w-soft-green` | 柔和绿 | Soft green |
| `m2w-greenery` | 新绿 | Fresh green |
| `m2w-prairie-green` | 草原绿 | Prairie green |
| `m2w-tender-cyan` | 嫩青 | Tender cyan |
| `m2w-orchid-cyan` | 兰青 | Orchid cyan |
| `m2w-cupid-busy` | 丘比特忙 | Pink theme |
| `m2w-soft-pink` | 柔粉 | Soft pink |
| `m2w-lemon-yellow` | 柠檬黄 | Lemon yellow |
| `m2w-yamabuki` | 山吹黄 | Yamabuki yellow |
| `m2w-pornhub-yellow` | PH黄 | Yellow-black contrast |
| `m2w-orange-heart` | 橙心 | Orange theme |
| `m2w-scarlet` | 绯红 | Scarlet red |
| `m2w-double-shadow` | 双重影 | Dual shadow |
| `m2w-frontend-peak` | 前端之峰 | Frontend style |
| `m2w-weformat` | 微信式 | WeChat style |
| `m2w-smartisan-note-v2` | 锤子便签 | Note style |
| `m2w-singularity` | 奇点 | Sci-fi style |
| `m2w-yanqi-lake` | 雁栖湖 | Nature style |

Usage examples: `Format this article with m2w-geek-black theme` or `Switch to m2w-rose-purple style`



## Layout

```
markdown-to-html/
├── SKILL.md                      # Core skill instructions
├── README.md                     # Chinese docs
├── README_EN.md                  # This file
├── scripts/
│   ├── escape_code.py            # Escape code blocks into inline &nbsp;/<br> fragments
│   └── validate_html.py          # Flag style-dropping markup (<style>/class/missing charset)
├── references/themes/
│   ├── theme-<name>.md           # Each theme's component library (page shell + component snippets)
│   └── examples/<name>.html      # A full sample article per theme
└── evals/
    ├── evals.json                # Test cases
    └── inputs/                   # Test input markdown
```

## Helper scripts

```bash
# Escape code/flow-diagram text into an inline HTML fragment
# (HTML-escape + spaces to &nbsp; + newlines to <br>)
python3 scripts/escape_code.py --in snippet.txt
cat snippet.txt | python3 scripts/escape_code.py

# Validate that generated HTML pastes cleanly
# (reports <style>/class/missing charset, etc.)
python3 scripts/validate_html.py output.html
python3 scripts/validate_html.py output.html --strict   # fail on warnings too
```

## Adding a theme

Adding a theme requires no change to `SKILL.md`:

1. Add `references/themes/theme-<name>.md` following the existing structure — a first line stating the use case or visual positioning (genre themes start with "适用于…", style themes with "视觉定位：…，不绑定任何文章题材"), then design tokens, page shell, and component HTML snippets.
2. Add a matching `references/themes/examples/<name>.html` sample.

The skill auto-discovers and supports new themes.
