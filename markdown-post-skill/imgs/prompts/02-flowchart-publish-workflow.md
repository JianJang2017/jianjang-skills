---
illustration_id: 02
type: flowchart
style: sketch-notes
palette: macaron
output_file: ../02-flowchart-publish-workflow.png
aspect_ratio: "16:9"
---

Use case: infographic-diagram
Asset type: article illustration for a Chinese technical tutorial
Primary request: Create a hand-drawn process flow showing the recommended one-click Juejin publishing workflow from a Markdown file to a reviewed draft.

Title: "推荐发布链路：先存草稿"

Hand-drawn educational flowchart on warm cream paper. Slight wobble on all lines. Diagram-style visuals only, no realistic or photographic images.

Layout: left-to-right main flow with six rounded step cards, plus one small red caution branch below the script step for the optional `--publish` mode.

STEPS:
1. "本地 Markdown" - document card with local image thumbnails.
2. "`publish_juejin.py article.md`" - terminal command card.
3. "复用登录态" - browser profile/card with cookie icon.
4. "上传图片 + 写正文" - editor card with image upload arrow.
5. "返回 draft_url" - link card containing the label "draft_url".
6. "人工核对后发布" - person with checklist and publish button doodle.

CONNECTIONS: Wavy black arrows connect the six main steps. From step 2, draw a small downward Coral Red branch labeled "`--publish` 慎用" leading to "直接发布" with a warning triangle, then a curved arrow back to "建议先草稿".

LABELS: Use these exact visible labels only: "本地 Markdown", "publish_juejin.py", "复用登录态", "上传图片 + 写正文", "draft_url", "人工核对", "--publish 慎用", "建议先草稿".

COLORS: Warm Cream background (#F5F0E8); Black (#1A1A1A) for all lines and text; main cards rotate through Light Blue (#A8D8EA), Mint (#B5E5CF), Lavender (#D5C6E0), Peach (#FFD5C2); Coral Red (#E8655A) only for the direct-publish caution branch. Color values and color names are rendering guidance only — do not display color names, hex codes, or palette labels as visible text in the image.

STYLE: sketch-notes, hand-lettered Chinese text, rounded cards with dashed/solid borders, simple terminal/browser/editor icons, doodle stars and underlines used sparingly, generous white space. Text should be large and prominent with handwritten-style fonts. Keep minimal, focus on keywords. Human figures: simplified stylized silhouettes or symbolic representations, not photorealistic.

Constraints: keep the command simplified, no full filesystem paths, no tiny UI details, no logos, no watermark, no photorealism, no screenshots.
ASPECT: 16:9
