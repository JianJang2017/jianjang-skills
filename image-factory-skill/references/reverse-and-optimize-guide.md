# Reverse-Prompt & Optimize-Prompt — 设计与维护说明

这份指南配套 `scripts/reverse-prompt.js` 和 `scripts/optimize-prompt.js`，
解释它们为什么这么写，怎么排查问题，以及在 codex/agy 后端行为变化时该怎么改。

> 主用法在 [SKILL.md](../SKILL.md) 的 "Reverse-Engineer & Optimize Prompts" 章节。这里
> 只放维护者视角的内容。

## 为什么做这个

`image-factory-skill` 原本是一条单向流水线：**prompt → 图 → 发飞书/小红书/抖音**。

但实际用下来有两个反向需求高频出现：

1. **看图猜 prompt**：刷到一张图想"复刻一张同风格的"，手写 prompt 很费劲，让模型反推一下就行。
2. **粗 prompt 打磨**：随手写的 prompt 经常缺风格、缺类型、缺关键元素，生图质量起伏大。专门一步"按结构改写"能稳定质量。

两个能力都不需要新依赖 — codex/agy 本身既能看图也能写 prompt — 所以做成两个独立、可串联的小脚本，而不是塞进 `generate-image.js`。

## 设计原则

1. **输出格式与 `prompts/` 归档完全一致**：frontmatter + `PROMPT:` 块。这样 reverse → optimize → generate 是一条顺滑的 pipe，每一步都能 `--prompt-file` 喂下一步。
2. **stderr 与 stdout 严格分流**：人看的日志（`🔍 反推中...`）走 stderr，机器要的 PROMPT 本体走 stdout。这样 `reverse-prompt | optimize-prompt --stdin` 不会被日志污染。
3. **后端调用结构与 `generate-image.js` 对齐**：同样的 `spawn` + 超时 + 重试 + `which` 探活。一处行为变了好同步。
4. **风格预设是注入，不是强约束**：把 `--style hand-drawn` 翻译成"中文描述 + 英文关键词组"两段，提示后端融入；不会强行要求后端必须用这些词。极端情况下 codex 仍然可能选别的词，但实测加了关键词组的稳定性比纯中文描述好不少。
5. **`--dry-run` 永不调后端**：方便快速验证 prompt 拼装、文件解析、风格预设字典是否正确，且不烧 token。

## 后端调用契约

两个脚本对后端的指令都遵循：

> **严格按下面格式输出，不要有其它任何字：**
> `PROMPT:\n<...>` （后面可能跟 `STYLE_TAG:` / `ASPECT_HINT:` / `NOTES:`）

但 codex/agy 经常会在前后包一层 "Thinking..." / "Generated:" / token 统计行。
解析器（`parseBackendOutput`）按这两条规则兜底：

1. **区段匹配**：用形如 `/PROMPT:\s*\n([\s\S]+?)(?=\n\s*(?:STYLE_TAG|ASPECT_HINT|NOTES)\s*:|\Z)/` 抓 PROMPT 段，结尾是下一个标签 _或_ 真·字符串末尾 (`\Z`)。
2. **彻底找不到 `PROMPT:` 时**，去掉噪声行（`thinking` / `codex` / `tokens used` / `[xxx]`）后整段当 prompt 用。这是兜底，不应该常触发；如果常触发，说明后端 prompt 模板要重写。

> ⚠️ 不要把 `\Z` 换成 `$` —— 那是 JS 正则的 _行尾_，会在多段 prompt 上漏掉后续段落。这是 `generate-image.js` 历史上踩过的坑（见 SKILL.md "Prompt Archiving" 一节）。

## 风格预设的取舍

| Preset | 关键词来源 | 备注 |
|--------|-----------|------|
| `hand-drawn` | SKILL.md 现有手绘风约定（warm cream / black ink lines / pastel blocks） | 对齐 article-illustration-tools 的视觉风 |
| `blueprint`  | 经典科技图风格 | grid 背景对生图模型识别度高 |
| `watercolor` | 通用美术词 | `ink bleed` 能让边缘有水彩感 |
| `cyberpunk`  | 通用 | `magenta + cyan` 比单写 "neon" 出图更稳 |
| `3d`         | octane render look 是常用 cue | 不写"render"模型容易给 2D 插画 |
| `healing`    | 治愈系 | low saturation + warm tone 是关键 |
| `minimal`    | 极简海报常用 | oversized typography + whitespace |
| `photo`      | 摄影风 | 35mm + cinematic 给电影感 |
| `keep`       | — | 仅结构化，让风格随原 prompt |
| `auto`       | — | 让后端自选 |

**加新预设时**：往 `STYLE_PRESETS` 字典里加一个 key，提供 `{ zh, keywords }` 即可。`zh` 是中文描述（写给后端读），`keywords` 是英文修饰词（让后端融入到 [Style] / [Key elements] 段）。

## 常见问题

### Q: reverse 出来的 prompt 总是大段散文，不像 prompt

A: 模板已经强调"指令句而非描述句"+"100-220 字符目标"，但 codex 偶尔仍会写长。可以：
- 加 `--verbose` 看原始输出，确认是模型没听话还是解析器漏了；
- 调小 `--timeout`（不是根治，只是让长输出更早被砍）；
- 在 `buildAnalysisPrompt` 里加更狠的样例反例（"不要写：这是一张……"）。

### Q: optimize 出来的 prompt 把原内容改没了

A: 一般是 `--style` 选得太强势。试试 `--style keep`（仅结构化）或加 `--verbose` 看 NOTES 备注，备注里如果写"重写了主体"就是过度改写，需要在模板里加"保留原 prompt 的核心语义，不要凭空增删"——已经有这句了，但 codex 不一定 100% 遵守。

### Q: 我想反推一张本地不存在的远程图

A: 现在脚本只接受本地路径。先 `curl -o /tmp/x.png <url>` 下载，再丢进 `--image`。后续可以加 `--url`，目前不在 v1.3 范围。

### Q: 串联 pipe 时 stdin 拿到空 prompt

A: 两种情况：
1. 前一步把 prompt 写到了 stderr（不该）— 检查是否误用了 `console.error` 输出主体；
2. 前一步出错退出码非 0 — 用 `set -o pipefail` 或拆开跑确认每一步。

### Q: codex 报 "Image not accessible"

A: 把 `--image` 改成绝对路径再试一遍（`reverse-prompt.js` 已经 `resolve()` 过，但有时 codex 沙箱限制访问范围，把图放进当前工作目录或 `~/` 下通常能解决）。

## 与 article-illustration-tools 的关系

`image-factory-skill` 的 `generate-image.js` 是从 article-illustration-tools 拷来的。
反推/优化能力是这个技能新加的，**不是从 article-illustration-tools 同步过来的**。
也就是说：

- 改 `generate-image.js` 时要考虑是不是要同步回 article-illustration-tools；
- 改 `reverse-prompt.js` / `optimize-prompt.js` / `generate-portrait-prompt.js` 就只在本仓库改即可。

## 扩展风格库（styles.js）

从 v1.4.0 起，风格预设统一沉淀在 `scripts/styles.js`（共享模块），`reverse` / `optimize` / `portrait` 三个脚本都复用这一份。**扩展风格 = 往 styles.js 加一条**。

每条预设的字段：
- `label`（中文名，给人看）
- `zh`（中文风格描述，写进后端 prompt）
- `keywords`（英文修饰词组，让后端融入 [Style] / [Key elements] 段）
- `kind`（'general' 通用 / 'portrait' 人物写真专用）
- `portrait`（仅 kind==='portrait' 时给：人物图专用的拍摄指引，含 camera / lighting / composition / quality / negative 五项）

**Example — 加一个"赛博朋克人物写真"风格**：

```javascript
// scripts/styles.js
export const STYLE_PRESETS = {
  // ... 现有预设 ...

  'cyberpunk-portrait': {
    label: '赛博朋克人物',
    kind: 'portrait',
    zh: '赛博朋克人物写真，霓虹灯光、雨夜街景、高对比、未来感服饰',
    keywords: 'cyberpunk portrait, neon lights, rainy night background, high contrast, futuristic outfit, magenta + cyan lighting',
    portrait: {
      camera: '半身特写，浅景深，35mm 视角',
      lighting: '霓虹灯主光源，侧逆光，高对比色温（magenta + cyan）',
      composition: '三分构图，雨夜街景背景虚化，霓虹招牌点缀',
      quality: '高细节、photorealistic、masterpiece、best quality、8k',
      negative: '避免：低分辨率、变形手部、水印、UI、多余文字、四宫格',
    },
  },
};
```

加完后：
- `generate-portrait-prompt.js --list-styles` 会自动列出这个新风格（标记 [人物]）
- `optimize-prompt.js --list-styles` 也能看到（标记 [人物]）
- `reverse-prompt.js` 反推时如果后端给出的 STYLE_TAG 匹配这个 key，frontmatter 会记录（虽然 reverse 不主动用预设，但读取预设来规范化 style_tag）

