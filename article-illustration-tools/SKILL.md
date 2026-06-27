---
name: article-illustration-tools
description: Analyzes markdown articles, automatically recommends illustration positions based on section structure, generates prompts, and creates images using codex-cli or gemini backends. Use when user asks to "illustrate article", "add images to article", "generate article images", "为文章配图", or "给文章生成图片".
version: 1.0.0
---

# Article Illustration Tools

Automatically analyze markdown articles, recommend illustration positions, generate prompts, and create images with customizable styles.

## Overview

This skill helps you add illustrations to markdown articles by:
1. Analyzing article structure (headings, sections, paragraphs)
2. Automatically recommending where to place images
3. Generating detailed prompts for each image
4. Creating images using AI image generation backends
5. Inserting image references into the markdown

## When to Use

Use this skill when you need to:
- Add visual aids to technical articles
- Illustrate tutorial content
- Create images for blog posts
- Generate diagrams for documentation

## Workflow

### Step 1: Input Analysis

**Accept article input in two ways:**

1. **File path**: User provides a markdown file path
   ```
   Example: "为这篇文章配图：./docs/tutorial.md"
   ```

2. **Pasted content**: User pastes markdown content directly
   ```
   Example: "给下面这篇文章配图：\n# My Article\n..."
   ```

**Actions:**
- Read the markdown content
- Identify the article structure:
  - Main headings (h1, h2, h3)
  - Sections and subsections (including all levels)
  - Paragraph count per section
  - Key concepts and topics
  
**⚠️ Important for tutorials/step-by-step articles:**
- Count ALL steps carefully, including final steps like "改进", "总结", "实战技巧"
- For "第X步" style articles, verify the total count matches (e.g., 第一步 through 第七步 = 7 steps)
- Don't skip final sections even if they seem like summaries

### Step 2: Recommend Image Positions

**Automatic Analysis:**

Analyze the article and recommend image positions based on:
- **Section length**: Longer sections (5+ paragraphs) may need 1-2 images
- **Section purpose**: 
  - Conceptual sections → info graphics or diagrams
  - Process descriptions → flowcharts or step illustrations
  - Comparisons → comparison charts or side-by-side scenes
  - Stories/examples → scene illustrations
- **Technical density**: Technical content benefits from more visual aids

**Recommendation format:**

Generate a recommendation like:
```
Based on the article structure, I recommend X images:

1. After "Introduction" section - Overview diagram showing the main concept
2. After "Architecture" section - System architecture infographic
3. After "Workflow" section - Process flowchart
4. After "Results" section - Data visualization or comparison chart
```

### Step 3: Confirm Style and Settings

This skill uses a **Three-Dimension Style System**: **Type × Style × Palette**

Each illustration is defined by three orthogonal dimensions that combine freely:

| Dimension | Controls | Examples |
|-----------|----------|----------|
| **Type** | Information structure | infographic, scene, flowchart, comparison, framework, timeline |
| **Style** | Rendering aesthetic | sketch-notes, vector-illustration, blueprint, watercolor, etc. |
| **Palette** | Color scheme (optional) | macaron, warm, mono-ink, neon |

**Use AskUserQuestion with these questions:**

#### Q1: Preset or Custom (REQUIRED)

Recommend a preset based on content analysis (Step 2). Presets bundle Type + Style + optional Palette:

**📚 Knowledge & Education:**
- `hand-drawn-edu` (⭐ **Default**) - Hand-drawn educational infographic. Warm cream paper, black lines, pastel blocks. Best for: general knowledge articles, concept explainers, onboarding
- `edu-visual` - Vector illustration with macaron palette. Best for: knowledge summaries, educational articles
- `knowledge-base` - Vector illustration. Best for: tutorials, how-to guides
- `saas-guide` - Notion style. Best for: SaaS docs, product guides
- `tutorial` - Flowchart + vector. Best for: step-by-step tutorials
- `process-flow` - Flowchart + notion. Best for: workflow documentation

**🔧 Technical & Engineering:**
- `tech-explainer` - Blueprint infographic. Best for: API docs, system metrics, technical deep-dives
- `system-design` - Blueprint framework. Best for: architecture diagrams, system design
- `architecture` - Vector framework. Best for: component relationships, module structure
- `science-paper` - Scientific style. Best for: research findings, academic content

**📊 Data & Analysis:**
- `data-report` - Editorial infographic. Best for: data journalism, metrics, dashboards
- `versus` - Vector comparison. Best for: tech comparisons, framework shootouts
- `business-compare` - Elegant comparison. Best for: product evaluations, strategy

**📖 Narrative & Creative:**
- `storytelling` - Warm scene. Best for: personal essays, growth stories
- `lifestyle` - Watercolor scene. Best for: travel, wellness, creative
- `history` - Elegant timeline. Best for: historical overviews
- `evolution` - Warm timeline. Best for: progress narratives

**🎭 Editorial & Opinion:**
- `opinion-piece` - Screen-print scene. Best for: op-eds, commentary
- `cinematic` - Screen-print scene. Best for: dramatic narratives, cultural essays
- `ink-notes-compare` - Ink notes + mono-ink. Best for: before/after essays, mindset shifts

**Or choose Custom** - manually specify Type + Style + Palette in Q2-Q4.

#### Q2: Type (if Custom chosen)

| Type | Best For |
|------|----------|
| `infographic` | Data, metrics, technical concepts |
| `scene` | Narratives, emotional, lifestyle |
| `flowchart` | Processes, workflows, algorithms |
| `comparison` | Side-by-side, vs, before/after |
| `framework` | Models, architecture, principles |
| `timeline` | History, evolution, progress |

#### Q3: Style (if Custom chosen)

**Core Styles** (recommended for most cases):

| Core Style | Maps To | Best For |
|------------|---------|----------|
| `hand-drawn` | sketch-notes | ⭐ **Default.** Warm cream paper, black hand-drawn lines, pastel blocks |
| `vector` | vector-illustration | Knowledge articles, tutorials, tech content |
| `minimal-flat` | notion | General, knowledge sharing, SaaS |
| `sci-fi` | blueprint | AI, frontier tech, system design |
| `editorial` | editorial | Processes, data, journalism |
| `scene` | warm/watercolor | Narratives, emotional, lifestyle |
| `poster` | screen-print | Opinion, editorial, cultural, cinematic |

**Full Style Gallery** (for granular control):

`vector-illustration`, `notion`, `elegant`, `warm`, `minimal`, `blueprint`, `watercolor`, `editorial`, `scientific`, `chalkboard`, `fantasy-animation`, `flat`, `flat-doodle`, `intuition-machine`, `nature`, `pixel-art`, `playful`, `retro`, `sketch`, `screen-print`, `sketch-notes`, `ink-notes`, `vintage`

#### Q4: Palette (Optional, if Custom chosen)

Overrides style's default colors:

| Palette | Look |
|---------|------|
| `macaron` | Soft pastel blocks on warm cream — friendly, educational |
| `warm` | Warm earthy tones — cozy, lifestyle |
| `mono-ink` | Black ink on white — minimal, professional |
| `neon` | Bright neon on dark — modern, futuristic |
| (default) | Use the style's built-in colors |

#### Q5: Density (REQUIRED)

| Density | Image Count | Best For |
|---------|-------------|----------|
| `minimal` | 1-2 | Short articles, single concept |
| `balanced` | 3-5 | ⭐ **Recommended.** Most articles |
| `per-section` | 1 per major section | Long-form content |
| `rich` | 6+ | Visual-heavy, tutorials |

### Type × Style Compatibility

Not all combinations work equally well:

| | sketch-notes | vector | notion | blueprint | warm | watercolor | screen-print |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| infographic | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓ | ✓ |
| scene | ✗ | ✓ | ✓ | ✗ | ✓✓ | ✓✓ | ✓✓ |
| flowchart | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓ | ✗ | ✗ |
| comparison | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ |
| framework | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓ | ✗ | ✓ |
| timeline | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✓ |

✓✓ = highly recommended | ✓ = compatible | ✗ = avoid

### Auto Selection by Content Signals

When recommending in Step 2, use these signal → preset mappings:

| Content Signals | Recommended Preset |
|-----------------|---------------------|
| **No strong signal / general** | ⭐ `hand-drawn-edu` |
| Knowledge, concept, tutorial, learning | `hand-drawn-edu`, `edu-visual` |
| How-to, steps, workflow, process | `hand-drawn-edu-flow`, `tutorial` |
| API, metrics, data, technical | `tech-explainer`, `data-report` |
| Tech, AI, programming, code | `tech-explainer`, `system-design` |
| Framework, architecture, principles | `system-design`, `architecture` |
| vs, pros/cons, before/after | `versus`, `ink-notes-compare` |
| Manifesto, mindset shift | `ink-notes-compare`, `ink-notes-framework` |
| Story, emotion, journey, personal | `storytelling`, `lifestyle` |
| History, timeline, evolution | `history`, `evolution` |
| Opinion, editorial, cultural | `opinion-piece`, `cinematic` |
| Biology, chemistry, scientific | `science-paper` |
| Explainer, journalism, magazine | `data-report` |

### Step 4: Generate Outline

Create an `outline.md` file in the output directory with:

```markdown
---
article: [article title or filename]
style: [chosen style]
image_count: [number]
output_dir: [path to imgs/ directory]
created: [timestamp]
---

# Illustration Outline

## Image 1: [Descriptive Title]
**Position**: After section "[Section Name]" (after paragraph X)
**Purpose**: [Why this image is needed - e.g., "Visualize the three-layer architecture"]
**Type**: [infographic/scene/diagram/etc.]
**Content Description**: [What should be shown in the image]
**Key Elements**: 
- Element 1
- Element 2
- Element 3
**Filename**: 01-[slug].png

## Image 2: [Descriptive Title]
...
```

**Save location:**
- If input is a file: `[article-directory]/imgs/outline.md`
- If pasted content: `./illustrations-[timestamp]/outline.md`

### Step 5: Generate Prompts

For each image in the outline, create a detailed prompt file.

**Prompt file structure:**

```markdown
---
image_number: 1
title: [Descriptive Title]
type: [infographic | scene | flowchart | comparison | framework | timeline]
style: [sketch-notes | vector-illustration | blueprint | warm | etc.]
palette: [macaron | warm | mono-ink | neon | default]
preset: [hand-drawn-edu | tech-explainer | etc., or "custom"]
aspect_ratio: "16:9"
---

# Image Prompt: [Title]

## Visual Type
[infographic/scene/flowchart/comparison/framework/timeline]

## Main Content
[Detailed description of what should be in the image]

## Key Elements
- [Element 1 with specific details]
- [Element 2 with specific details]
- [Element 3 with specific details]

## Style Guidelines
- [Style-specific instructions based on chosen style]
- [Color palette suggestions]
- [Composition notes]

## Text/Labels (if applicable)
- [Text that should appear in the image]
- [Labels for diagram elements]

## Context
[Brief context from the article to help the AI understand the purpose]

---

PROMPT:
[Final consolidated prompt for image generation, incorporating all above elements in a clear, structured way]
```

**Save location:**
- `[output-dir]/prompts/01-[slug].md`
- `[output-dir]/prompts/02-[slug].md`
- etc.

**Naming convention:**
- Use 2-digit numbers: 01, 02, 03...
- Use kebab-case slugs from titles
- Example: `01-system-architecture.md`, `02-workflow-diagram.md`

### Step 6: Generate Images

**Use the bundled image generation script:**

The skill includes `scripts/generate-image.js` which supports two backends:
- **codex-cli**: Codex's built-in image generation
- **gemini (agy)**: Antigravity CLI with generate_image tool

**For each prompt file, generate the image:**

```bash
node scripts/generate-image.js \
  --prompt-file [output-dir]/prompts/01-[slug].md \
  --output [output-dir]/01-[slug].png \
  --aspect-ratio 16:9 \
  --provider auto
```

The script will:
1. Auto-detect available providers (codex-cli or agy)
2. Read the PROMPT section from the markdown file
3. Call the appropriate backend
4. Save the image to the specified output path

**Provider selection:**
- `--provider auto` (default): Auto-detect codex or gemini
- `--provider codex`: Force use of codex-cli
- `--provider gemini`: Force use of agy (Antigravity CLI)

**Batch Generation:**

Generate images in parallel when possible:
- Default batch size: 3-4 images at a time
- Wait for all images in a batch before proceeding
- Retry failed images once

**Error Handling:**

⚠️ **CRITICAL: Always complete Step 7 regardless of image generation results**

If image generation fails:
1. Log the error with details
2. Retry once with the same prompt
3. If still fails:
   - Continue with remaining images (don't stop the entire process)
   - Keep track of which images succeeded/failed
   - Proceed to Step 7 even with partial results
4. In Step 7, insert references for ALL images (even failed ones will show as broken links, which is better than skipping the insertion step entirely)

**Verification before proceeding to Step 7:**
- Count how many images were successfully generated
- Log: "Successfully generated X/Y images"
- If some failed, note which ones
- **Always proceed to Step 7** - don't skip it even if all images failed

### Step 7: Insert Images into Article

⚠️ **This step is MANDATORY - execute even if image generation had failures**

**Insertion Logic:**

For each planned image (from outline.md):
1. Find the insertion position in the markdown (after the specified section/paragraph)
2. Insert image reference with alt text:
   ```markdown
   ![Description based on image title](imgs/01-system-architecture.png)
   ```
3. Add a blank line before and after the image for readability
4. **Insert references for ALL images from the outline, even if generation failed** - broken image links are acceptable

**Important:**
- This step must execute even if Step 6 had errors
- Use the filenames from outline.md, not from actual generated files
- The goal is to produce a complete article with image placeholders
   ```
3. Add a blank line before and after the image for readability

**Output:**

- If input was a file:
  - Create backup: `[filename].backup.md`
  - Modify original file with image references
  - Images in: `[article-dir]/imgs/`
  
- If input was pasted:
  - Save modified article: `./illustrations-[timestamp]/article-with-images.md`
  - Images in: `./illustrations-[timestamp]/imgs/`

### Step 8: Summary

Provide a completion summary:

```
✅ Article Illustration Complete!

📄 Article: [title or filename]
🎨 Style: [chosen style]
🖼️ Images Generated: X/Y successful
📁 Output Directory: [path]

Generated Images:
1. ✅ 01-system-architecture.png - System architecture overview
2. ✅ 02-workflow-diagram.png - Processing workflow
3. ❌ 03-comparison.png - Failed (skipped)
4. ✅ 04-results.png - Performance results

📝 Files Created:
- outline.md - Generation plan
- prompts/ - Individual prompt files
- imgs/ - Generated images
- [article-name]-with-images.md - Updated article (if pasted content)

Next Steps:
- Review the images in the article
- Adjust any prompts if needed and regenerate specific images
- Commit changes to version control
```

## Style Guidelines

### Infographic Style
- Clean, structured layouts
- Clear data visualization
- Professional color schemes
- Icons and symbols
- Text labels for clarity
- Best for: technical concepts, architectures, data, comparisons

### Scene Style
- Illustrative, artistic
- Atmospheric and narrative
- Rich colors and details
- Conveys emotion and context
- Best for: stories, examples, use cases, conceptual illustrations

### Diagram Style
- Flowcharts and process diagrams
- Clear connections and flow
- Minimal decoration
- Focus on structure and relationships
- Best for: workflows, algorithms, decision trees, system flows

### Hand-drawn Style
- Sketch-like appearance
- Friendly and approachable
- Casual and warm
- Best for: tutorials, educational content, casual blogs

### Minimal Style
- Flat design
- Limited color palette
- Simple shapes
- Modern and clean
- Best for: professional content, minimalist aesthetics

## Directory Structure

After running this skill, the directory structure will be:

```
[article-directory]/
├── article.md (original, backed up if modified)
├── article.backup.md (backup of original)
└── imgs/
    ├── outline.md (generation plan)
    ├── prompts/
    │   ├── 01-system-architecture.md
    │   ├── 02-workflow-diagram.md
    │   └── 03-results.md
    ├── 01-system-architecture.png
    ├── 02-workflow-diagram.png
    └── 03-results.png
```

## Modifying and Regenerating

**To regenerate a specific image:**

1. Edit the prompt file: `imgs/prompts/XX-[slug].md`
2. Run `scripts/generate-image.js` with the updated prompt file
3. Overwrite the existing image file

**To add more images:**

1. Update `outline.md` with new image entries
2. Create new prompt files
3. Generate new images
4. Insert references into the article

**To change styles:**

1. Update prompt files with new style guidelines
2. Regenerate all images or specific images
3. No need to modify the article markdown

## Tips for Best Results

1. **Article Structure**: Well-structured articles with clear sections produce better recommendations
2. **Section Length**: Each major section (5+ paragraphs) benefits from at least one image
3. **Technical Content**: Technical articles benefit from infographic or diagram styles
4. **Narrative Content**: Stories and examples work better with scene style
5. **Consistency**: Use the same style throughout an article for visual coherence (unless "mixed" is intentionally chosen)
6. **Prompt Quality**: More detailed prompts produce better images - the skill generates detailed prompts automatically
7. **Review Before Insert**: Generate all images first, review them, then insert into the article

## Dependencies

### Essential
- **Node.js** (>=14.0.0): Required to run the image generation script
  - Verification: `node --version`
  - Installation: See INSTALLATION.md

### Image Generation Backend (at least one required)

The skill requires at least one of these tools to generate images:

#### Codex CLI (Recommended)
- **Tool**: codex-cli
- **Provider**: OpenAI Codex
- **Website**: https://openai.com/zh-Hans-CN/codex
- **Command**: `codex`
- **Installation**: Visit https://openai.com/zh-Hans-CN/codex or `npm install -g codex-cli`
- **Verification**: `codex --version`
- **Note**: Remove `service_tier` from `~/.codex/config.toml` if present
- **Features**: 
  - High-quality image generation
  - Multiple styles (infographic, diagram, hand-drawn, etc.)
  - 16:9 aspect ratio support

#### Antigravity CLI
- **Tool**: agy
- **Provider**: Google Gemini
- **Website**: https://antigravity.google/docs/cli-getting-started
- **Command**: `agy`
- **Installation**: Follow https://antigravity.google/docs/cli-getting-started
- **Verification**: `agy --version`
- **Features**:
  - Fast image generation
  - Uses Gemini's `generate_image` tool
  - Easy to use

### Verification

Run the test script to check your setup:
```bash
bash scripts/test.sh
```

The script will:
- Check for Node.js
- Detect available backends (codex-cli and/or agy)
- Run generation tests

For detailed installation instructions, see **INSTALLATION.md**.

## Example Usage

**Example 1: Technical article with file path**
```
User: "为这篇文章配图：./docs/architecture-guide.md"

→ Analyze article structure
→ Recommend 3 images (intro diagram, architecture infographic, workflow diagram)
→ Ask user to choose style: infographic
→ Generate outline.md and prompt files
→ Generate images using scripts/generate-image.js
→ Insert images into article
→ Output: article.md updated, imgs/ folder created with 3 images
```

**Example 2: Tutorial with pasted content**
```
User: "给下面这个教程配图：\n# Python入门教程\n..."

→ Analyze pasted content
→ Recommend 5 images for tutorial steps
→ Ask user to choose style: hand-drawn
→ Generate outline and prompts
→ Generate images
→ Save to ./illustrations-[timestamp]/
→ Output: article-with-images.md with all images inserted
```

**Example 3: Mixed style article**
```
User: "为这篇文章配图，用混合风格"

→ Analyze article
→ User chooses "mixed" style
→ Generate outline with different styles per section:
  - Intro: infographic
  - Story section: scene
  - Process section: diagram
  - Results: infographic
→ Generate all images with appropriate styles
→ Insert into article
```