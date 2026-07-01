---
illustration_id: 03
type: flowchart
style: sketch-notes
palette: macaron
output_file: ../03-flowchart-clipboard-upload.png
aspect_ratio: "16:9"
---

Use case: infographic-diagram
Asset type: article illustration for a Chinese technical tutorial
Primary request: Create a technical hand-drawn flowchart explaining the stable clipboard-based image upload mechanism used for Juejin's new editor.

Title: "图片上传为什么走剪贴板"

Hand-drawn educational flowchart on warm cream paper. Slight wobble on all lines. Diagram-style visuals only, no realistic or photographic images.

Layout: main pipeline across the center with six connected cards; a small top-right "失败路线" corner with three crossed-out mini notes.

STEPS:
1. "本地图片" - file icon labeled PNG/JPG/WEBP.
2. "写入系统剪贴板" - clipboard icon with small platform tags "macOS osascript" and "Windows PowerShell".
3. "真实键盘粘贴" - keycap doodle "⌘V / Ctrl+V".
4. "Juejin paste handler" - editor card receiving the paste event.
5. "返回 CDN URL" - cloud/link icon.
6. "替换 Markdown 路径" - document icon changing "./img/a.png" into "CDN URL".

FAILED METHODS CORNER:
- "合成 ClipboardEvent" crossed out.
- "抓 XHR 白名单" crossed out.
- "封面 file input" crossed out.

CONNECTIONS: Thick wavy black arrows for the stable path. Use one Coral Red small label "不稳定" on the failed-methods corner, not on the main path.

LABELS: Use these exact visible labels only: "本地图片", "系统剪贴板", "⌘V / Ctrl+V", "paste handler", "CDN URL", "替换 Markdown 路径", "ClipboardEvent", "XHR 白名单", "封面 input", "稳定方案".

COLORS: Warm Cream background (#F5F0E8); Black (#1A1A1A) for all lines and text; main cards use Light Blue (#A8D8EA), Mint (#B5E5CF), Lavender (#D5C6E0), Peach (#FFD5C2); Coral Red (#E8655A) for crossed-out failed paths only. Color values and color names are rendering guidance only — do not display color names, hex codes, or palette labels as visible text in the image.

STYLE: sketch-notes, handwritten Chinese labels, wobbly arrows, small doodles, friendly technical explainer, clean composition and generous white space. Text should be large and prominent with handwritten-style fonts. Keep minimal, focus on keywords.

Constraints: no real Juejin logo, no browser screenshots, no long code snippets, no dense paragraphs, no watermark, no photorealism.
ASPECT: 16:9
