<!-- LANG_SWITCH -->
[中文](./README.md) | **English**

# Image Prompt Factory 🎨

> A Claude skill that generates professional image prompts for **GPT-image / DALL-E**.

Core idea: **picture the scene clearly in your head first, then describe it in flowing natural language** — instead of filling in a rigid template cell by cell. GPT-image responds best to paragraph-style natural language, a sense of scene, and internal logic, so this skill produces **coherent descriptive prompts** rather than loose tag strings.

## ✨ Features

- **18 styles**: Ancient/Guofeng, Japanese, Korean/CCD, Urban street, Office/intellectual, Loungewear/soft-light, Beach/vacation, 3D CG, Lifestyle, New-Chinese, Retro Hong Kong, French-lazy, Travel/vacation, Sporty/active, Studio-retouched, E-commerce try-on, Ultra-close real face, Low-key cinematic
- **Optimized for GPT-image**: paragraph-style natural language, no negative prompts / SD spells / MJ parameters
- **Style DNA cards**: a dedicated reference per style with trigger words, visual traits, language style, and writing tips
- **Standard demos + real sample images**: every style ships a ready-to-reuse prompt and its generated image
- **Configurable aspect ratio**: defaults to 9:16 vertical (social-media friendly), also supports 16:9 / 1:1
- **Extensible**: add your own styles following `references/extension-guide.md`

## 🚀 Usage

Trigger it in Claude with plain natural language (Chinese or English):

```
"Write me an image prompt for an ancient-style noble lady in a spring courtyard, pink hanfu"
"I want a Korean CCD-style photo, late-night cafe"
"Give me a generation prompt, office / intellectual style"
```

The skill will:
1. Identify the style direction
2. Read the matching style DNA (`references/`)
3. Reference the standard demo (`prompts/examples/`)
4. Picture the scene, then output a paragraph-style prompt in natural language

## 📐 Output format

```
【Style】[style name · sub-category]
【Aspect】1024x1792 (9:16 vertical)

【Prompt】
[2-4 natural paragraphs: scene+subject → outfit+makeup → pose+background → light+lens+texture]
```

## 📂 Structure

```
image-prompt-factory/
├── SKILL.md                    # Core workflow
├── README.md                   # Chinese docs
├── README.en.md                # English docs (this file)
├── references/                 # Style DNA cards + general spec
│   ├── 01-guofeng.md ~ 18-low-key-cinematic.md
│   ├── prompt-template.md      # General writing spec
│   └── extension-guide.md      # Extension guide
└── prompts/
    ├── examples/               # 18 standard demo prompts
    └── images/                 # matching generated sample images
```

---

## 🖼️ Style samples & images

Click any image or **📄 prompt** to view the full standard demo for that style (GPT-image / codex channel, 9:16 vertical).

<table>
<tr><td align="center" width="33%"><a href="prompts/examples/01-guofeng-example.md"><img src="prompts/images/01-guofeng.png" width="240" alt="Ancient / Guofeng"></a><br><b>Ancient / Guofeng</b><br><sub><a href="prompts/examples/01-guofeng-example.md">📄 prompt</a></sub></td><td align="center" width="33%"><a href="prompts/examples/02-japanese-example.md"><img src="prompts/images/02-japanese.png" width="240" alt="Japanese"></a><br><b>Japanese</b><br><sub><a href="prompts/examples/02-japanese-example.md">📄 prompt</a></sub></td><td align="center" width="33%"><a href="prompts/examples/03-korean-ccd-example.md"><img src="prompts/images/03-korean-ccd.png" width="240" alt="Korean / CCD"></a><br><b>Korean / CCD</b><br><sub><a href="prompts/examples/03-korean-ccd-example.md">📄 prompt</a></sub></td></tr>
<tr><td align="center" width="33%"><a href="prompts/examples/04-urban-example.md"><img src="prompts/images/04-urban.png" width="240" alt="Urban / Street"></a><br><b>Urban / Street</b><br><sub><a href="prompts/examples/04-urban-example.md">📄 prompt</a></sub></td><td align="center" width="33%"><a href="prompts/examples/05-workplace-example.md"><img src="prompts/images/05-workplace.png" width="240" alt="Office / Intellectual"></a><br><b>Office / Intellectual</b><br><sub><a href="prompts/examples/05-workplace-example.md">📄 prompt</a></sub></td><td align="center" width="33%"><a href="prompts/examples/06-homewear-example.md"><img src="prompts/images/06-homewear.png" width="240" alt="Loungewear / Home"></a><br><b>Loungewear / Home</b><br><sub><a href="prompts/examples/06-homewear-example.md">📄 prompt</a></sub></td></tr>
<tr><td align="center" width="33%"><a href="prompts/examples/07-swimwear-example.md"><img src="prompts/images/07-swimwear.png" width="240" alt="Swimwear / Beach"></a><br><b>Swimwear / Beach</b><br><sub><a href="prompts/examples/07-swimwear-example.md">📄 prompt</a></sub></td><td align="center" width="33%"><a href="prompts/examples/08-3dcg-example.md"><img src="prompts/images/08-3dcg.png" width="240" alt="3D CG / Fantasy"></a><br><b>3D CG / Fantasy</b><br><sub><a href="prompts/examples/08-3dcg-example.md">📄 prompt</a></sub></td><td align="center" width="33%"><a href="prompts/examples/09-lifestyle-example.md"><img src="prompts/images/09-lifestyle.png" width="240" alt="Lifestyle"></a><br><b>Lifestyle</b><br><sub><a href="prompts/examples/09-lifestyle-example.md">📄 prompt</a></sub></td></tr>
</table>

### New styles (sample images pending)

These 9 styles already ship a full style DNA card and standard demo; sample images will join the grid later:

| Style | One-line positioning | Standard demo |
| --- | --- | --- |
| New-Chinese / Oriental | Tea room, screens, improved new-Chinese wear, negative space (not costume drama) | [📄 prompt](prompts/examples/10-new-chinese-example.md) |
| Retro Hong Kong | Old HK film still, neon side light, low-saturation film | [📄 prompt](prompts/examples/11-hongkong-retro-example.md) |
| French-lazy | Creamy warm white, apartment morning light, relaxed elegance | [📄 prompt](prompts/examples/12-french-lazy-example.md) |
| Travel / vacation | Vacation travel shots, island sunset, destination vibe | [📄 prompt](prompts/examples/13-travel-vacation-example.md) |
| Sporty / active | Tennis, track, gym, healthy lines, energetic motion | [📄 prompt](prompts/examples/14-sporty-active-example.md) |
| Studio-retouched | Pro studio shoot, clean lighting, commercial headshot | [📄 prompt](prompts/examples/15-studio-retouched-example.md) |
| E-commerce try-on | Product hero shot, accurate garment, no color shift | [📄 prompt](prompts/examples/16-ecommerce-tryon-example.md) |
| Ultra-close real face | Close-up unretouched, pores & micro-texture, de-AI look | [📄 prompt](prompts/examples/17-ultra-close-real-face-example.md) |
| Low-key cinematic | Dark-key stills, readable shadows, narrative mood | [📄 prompt](prompts/examples/18-low-key-cinematic-example.md) |

---

## 🔧 Adding a new style

See `references/extension-guide.md`. Roughly three steps:
1. Add a style DNA card `10-yourstyle.md` under `references/`
2. Add a standard demo under `prompts/examples/`
3. Register it in the style list in `SKILL.md`

## ⚠️ Notes

- All subjects in the prompts are **adults** (ages 22-28); no minor-related descriptions
- Sample images are generated via the GPT-image / codex channel, for skill demonstration only
- Generation never impersonates real people's names or identities
