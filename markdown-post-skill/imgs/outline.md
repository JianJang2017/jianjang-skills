---
type: flowchart
density: balanced
style: sketch-notes
palette: macaron
image_count: 4
language: zh
backend: imagegen
---

## Illustration 1

**Position**: After section "一、这个技能能做什么"
**Purpose**: Give readers a one-screen mental model of what `markdown-post-skill` automates before they enter setup details.
**Visual Content**: Five capability cards: open editor, upload local images, write title/body, prefill metadata, save draft for review.
**Type Application**: Educational overview infographic with light flow arrows.
**Filename**: 01-infographic-skill-capabilities.png

## Illustration 2

**Position**: After section "四、一键发布"
**Purpose**: Clarify the recommended draft workflow and the optional direct-publish path.
**Visual Content**: A command-to-draft flow: Markdown article -> publish_juejin.py -> browser/editor -> draft_url -> manual review -> publish, with `--publish` shown as a red caution branch.
**Type Application**: Left-to-right hand-drawn process flow.
**Filename**: 02-flowchart-publish-workflow.png

## Illustration 3

**Position**: After section "五、图片上传原理（技术细节）"
**Purpose**: Explain why clipboard paste is the stable image upload path for Juejin's new editor.
**Visual Content**: Pipeline from local image to OS clipboard to real keyboard paste to Juejin paste handler to CDN URL to Markdown replacement.
**Type Application**: Technical flowchart with a small failed-methods corner.
**Filename**: 03-flowchart-clipboard-upload.png

## Illustration 4

**Position**: After section "六、常见问题排查"
**Purpose**: Turn troubleshooting text into a quick visual decision map.
**Visual Content**: Four common symptoms and fixes: stuck startup -> clear SingletonLock, not logged in -> refresh login, upload failure -> check clipboard/focus/size/path, category/tag mismatch -> choose Juejin preset.
**Type Application**: Decision map / troubleshooting flowchart.
**Filename**: 04-flowchart-troubleshooting-map.png
