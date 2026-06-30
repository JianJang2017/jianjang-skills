---
name: image-factory-skill
description: Generate AI images from prompts and either send them to Feishu (Lark) users/group chats via lark-cli, OR publish them as Xiaohongshu (RedNote/小红书) image-text notes, OR publish them as Douyin (抖音) image-text posts — both via persistent Playwright browser sessions. ALSO supports reverse-engineering a generation prompt from an existing image, optimizing an existing prompt by style preset, AND generating character portrait prompts from scratch (subject + style preset → ready-to-use portrait prompt with camera/lighting/quality terms), all via codex-cli / agy. Use when user asks to "generate an image and send to Feishu", "create image and push to lark", "生成图片并发送到飞书", "给某某发一张图", "发布到小红书", "发一篇小红书笔记", "publish to xiaohongshu / rednote", "发布到抖音", "发一篇抖音图文", "publish to douyin", OR when user wants to "反推 prompt", "看图猜 prompt", "reverse prompt from image", "image to prompt", "把这张图变成 prompt", "优化 prompt", "改写 prompt", "polish prompt", "optimize image prompt", OR "生成人物图 prompt", "写一条人物写真 prompt", "generate portrait prompt", "character prompt from subject", "古风人物提示词", or wants to push AI-generated images to Feishu/Xiaohongshu/Douyin OR turn an image back into a reusable text-to-image prompt OR restructure a rough prompt under a specific style preset (hand-drawn / blueprint / watercolor / cyberpunk / 3d / healing / minimal / photo / gufeng-portrait / photo-portrait) OR create a ready-to-use character portrait prompt from a simple subject description (one-liner → structured prompt with style/camera/lighting/quality/negative).
version: 1.6.0
---

# Image Factory Skill

Generate AI images from text prompts and automatically send them to Feishu (Lark) users or group chats.

## Overview

This skill combines AI image generation with Feishu messaging to:
1. Accept a text prompt describing the desired image
2. Generate the image using AI backends (codex-cli or gemini/agy)
3. Send the image to specified Feishu users or group chats
4. Optionally include a text caption with the image

## When to Use

Use this skill when the user wants to:
- Generate an image and send it to someone on Feishu
- Create visual content for team communication
- Send AI-generated illustrations to group chats
- Quickly produce and share images without manual upload

## Workflow

### Step 1: Collect Image Requirements

**Get from user:**
1. **Prompt**: Text description of the image to generate
2. **Recipients** (optional, falls back to `.env` config):
   - User IDs (open_id format: `ou_xxx`)
   - Chat IDs (group chat format: `oc_xxx`)
3. **Caption** (optional): Text message to accompany the image
4. **Aspect ratio** (optional, default `16:9`): Image dimensions

**Example user inputs:**
```
"生成一张科技感的系统架构图，发给张三"
"Create a flowchart showing the deployment process and send to the dev group"
"给研发群发一张手绘风格的产品路线图，配文：Q2规划草图"
```

### Step 2: Verify Configuration

**Check `.env` for required Feishu settings:**

```bash
# From .env file
FEISHU_USER_IDS=ou_xxx,ou_yyy      # Default user recipients
FEISHU_CHAT_IDS=oc_xxx,oc_yyy      # Default group chat recipients
FEISHU_SEND_AS=bot                 # Identity: bot | user
```

**If recipients not provided by user AND not in `.env`:**
- Ask user to provide at least one recipient (user ID or chat ID)
- Or guide them to configure `.env`

**Identity (`FEISHU_SEND_AS`):**
- `bot` (recommended for images): Send as the application/bot
  - ✅ No special permissions needed for user DMs
  - ✅ Has image upload permission out of the box
  - ⚠️ Bot must be added to groups before sending there
- `user`: Send as the authenticated user
  - ✅ Can send to any group the user is in
  - ⚠️ Requires `im:message.send_as_user` for text AND `im:resource:upload` + `im:resource` for images
  - ⚠️ **Sending images needs MORE than sending text.** A user identity that can send text messages often still cannot upload images. If you hit `im:resource` / `uploading image` errors, switch to `--as bot` (simplest) or re-authorize with the resource scopes.

> 💡 **For this skill specifically, prefer `--as bot`.** Image sending requires upload permissions that the bot identity has by default. Even if `.env` sets `FEISHU_SEND_AS=user`, fall back to `bot` if you see an upload/resource permission error — text-only setups frequently lack image upload scope.

### Step 3: Generate Image

**Use the bundled `generate-image.js` script:**

```bash
node scripts/generate-image.js \
  --prompt-file <temp-prompt.md> \
  --output <temp-image.png> \
  --aspect-ratio 16:9 \
  --provider auto
```

**Generate N distinct images from ONE prompt (--count/-n):**

```bash
node scripts/generate-image.js \
  --prompt-file <temp-prompt.md> \
  --output <base.png> \
  --count 3
# → base-1.png, base-2.png, base-3.png
```

The same prompt run N times produces N different images (codex/agy are non-deterministic).
Outputs are suffixed `-1..-N` off the base `--output` path.

**The script:**
- Auto-detects available backends (codex-cli or agy)
- Supports two providers:
  - **codex-cli**: OpenAI Codex image generation
  - **gemini (agy)**: Google Antigravity CLI
- Includes timeout (5 min) and retry (1 attempt)
- Verifies output file exists after generation
- **Count mode**: generates N images concurrently (bounded by `--concurrency`, default 3)

**Prompt format:**

Create a temporary markdown file with the user's prompt:
```markdown
---
aspect_ratio: "16:9"
---

PROMPT:
<user's image description>
```

The script extracts the `PROMPT:` section for generation.

**Error handling:**
- If generation fails after retry, report the error to user
- Include details from script stderr
- Don't proceed to Step 4 if no image was generated

### Step 4: Send to Feishu

**Use the Python orchestrator `send_feishu_image.py`:**

```bash
python scripts/send_feishu_image.py \
  --image <generated-image.png> \
  --user-ids "ou_xxx,ou_yyy" \
  --chat-ids "oc_zzz" \
  --caption "Optional message text" \
  --as bot
```

**Send multiple images as one message:**

```bash
# Pre-generated images (comma-separated)
python scripts/send_feishu_image.py \
  --image "a.png,b.png,c.png" \
  --user-ids "ou_xxx"

# Generate N images from one prompt, send as one multi-image message
python scripts/send_feishu_image.py \
  --prompt "手绘风格的系统架构图" \
  --count 3 \
  --user-ids "ou_xxx"
```

**The script handles:**
- Generating N images from one prompt with `--count` (outputs suffixed -1..-N)
- Sending multiple images (N img blocks) in a single rich-text `post` message
- Uploading each image once, sending to all targets concurrently
- Combining image(s) + caption + copyable prompt into one message
- Working around lark-cli's path restrictions (uses relative paths with cwd)
- Identity selection (bot vs user)
- Detailed success/failure reporting per target

**Send logic (optimized):**

1. Upload the image **once** via `lark-cli im images create` → get a reusable `image_key`
2. Build one `post` message containing the image + caption (title) + the generation prompt as a copyable text line
3. Send that same message to all targets **concurrently** (thread pool)
4. Log success ✅ or failure ❌ per target; one failure doesn't block the rest

This replaces the old per-target re-upload + separate caption message (2N requests) with
1 upload + N parallel sends. The full prompt is attached as selectable/copyable text so
recipients can long-press to copy it. Pass `--no-prompt-caption` to omit the prompt text.

**Important:** lark-cli requires the image path to be relative (no `/` prefix, no `..`), so the orchestrator:
- Changes working directory to the image's parent folder
- Passes only the image filename to lark-cli
- This avoids the "absolute paths rejected" error

### Step 5: Report Results

**Success summary:**

```
✅ Image generated and sent!

🖼️ Image: <filename>
📤 Sent to: 2 users + 1 group chat (as bot)

Results:
  ✅ 👤 用户 ou_xxx
  ✅ 👤 用户 ou_yyy
  ✅ 👥 群聊 oc_zzz

📝 Caption: "Optional message text"
```

**Partial failure:**

```
⚠️ Image sent with some failures

🖼️ Image: <filename>
📤 Sent to: 1/2 users, 0/1 groups

Results:
  ✅ 👤 用户 ou_xxx
  ❌ 👤 用户 ou_yyy
      错误: Bot/User can NOT be out of the chat (230002)
  ❌ 👥 群聊 oc_zzz
      错误: Bot not in group - add bot to the group first

💡 Troubleshooting:
- Error 230002: Bot must be added to the group chat first
- Permission errors: Check FEISHU_SEND_AS and user scopes
```

**Include actionable guidance for common errors:**
- `230002`: Bot not in group → guide user to add bot
- Permission errors → suggest `lark-cli auth status` to check scopes
- `im:message.send_as_user` missing → suggest using `--as bot` instead

## Publish to Xiaohongshu (小红书 / RedNote)

This skill has a second, parallel output channel alongside Feishu: publish a
generated (or existing) image as a Xiaohongshu **image-text note** via a
persistent Playwright browser session.

> **Why a browser, not an API:** Xiaohongshu has no public posting API — a note
> can only be published from a logged-in browser session. Since this environment
> has no OpenClaw/claw tools, the `publish_xiaohongshu.js` script implements the
> **image-text publish flow** on a self-contained Playwright Chromium.

### When to Use

- User asks to "发布到小红书", "发一篇小红书笔记", "publish to xiaohongshu / rednote"
- User has an image (just generated, or pre-existing) plus a title/body to post

### Scope (intentional boundary)

This channel handles **image + title/body/topics**. It does NOT reply to
comments or do account analysis — that's the broader xiaohongshu-ops territory
and out of scope here. You can pass the copy explicitly (`--title`/`--content`),
or let the script **auto-derive it from the generation prompt** (`--prompt-file`):
title from the image's visual style, body from a condensed prompt. Explicit
values always win over auto-derivation.

### Auto-derive title & body from the prompt

When you publish a freshly generated image, you usually already have its prompt
(archived under `prompts/YYYYMMDD-NN.md`). Pass it with `--prompt-file` and the
script fills in whatever copy you didn't give explicitly:

- **Title** ← the image's **visual style** + subject, e.g. a prompt containing
  "手绘风格的三层 Web 架构图" → title `手绘风的三层 Web 架构图` (capped at 20 chars).
  Style is matched from a keyword table (手绘/水彩/科技感/治愈/赛博朋克/3D…).
- **Body** ← a **condensed, de-prompted** version: instruction phrasing
  ("画一张…风格的") and technical tails ("高清渲染", "景深效果", aspect ratios)
  are stripped, then trimmed to ~80 chars of natural-reading text.

```bash
# Fully auto: only image + prompt-file (title & body derived)
node scripts/publish_xiaohongshu.js \
  --image cover.png \
  --prompt-file prompts/20260628-01.md \
  --topics "AI,架构"

# Mix: derive the body, but set the title yourself
node scripts/publish_xiaohongshu.js \
  --image cover.png --prompt-file prompts/20260628-01.md \
  --title "我用AI画了张架构图"
```

Always preview with `--dry-run` first — it prints the final title/body and tags
each with its source `(--title)` / `(按图片风格自动生成)` / `(prompt 精简)` so
you can sanity-check before anything touches the browser.

### Generate-and-publish in one shot

You don't need a pre-made image. Pass `--prompt "<描述>"` (no `--image`) and the
script runs the whole pipeline itself: **generate the image** (via the same
`generate-image.js` / codex / agy backend the Feishu channel uses) → **archive
the prompt** to `prompts/YYYYMMDD-NN.md` → **derive title & body** from that
prompt → publish (still stopping at the publish button by default).

```bash
# One shot: prompt → image → derived copy → publish page (stops at the button)
node scripts/publish_xiaohongshu.js \
  --prompt "赛博朋克风格的城市夜景，霓虹灯牌林立" \
  --topics "AI,赛博朋克"

# Generate N different images from one prompt, publish as one multi-image note
node scripts/publish_xiaohongshu.js \
  --prompt "手绘风格的系统架构图" \
  --count 3 \
  --topics "AI,架构"

# Same, with generation knobs + your own title, auto-publish
node scripts/publish_xiaohongshu.js \
  --prompt "水彩风格的猫躺在窗台" \
  --provider codex --aspect-ratio 3:4 \
  --title "周末的猫" --publish
```

Generation flags (only used when generating, i.e. no `--image`):
`--provider auto|codex|gemini`, `--aspect-ratio` (default `3:4`, vertical for
XHS), `--count`/`-n` (generate N distinct images from one prompt → one
multi-image note), `--output` (defaults to a temp file). If generation
fails/times out but codex already wrote the image, the script recovers it from
`~/.codex/generated_images/` — same fallback as the Feishu orchestrator.

> **Multi-image timeout & recovery:** with `--count N`, the per-image timeout
> budget scales to `5min × N` so the generator isn't SIGKILL'd before it prints
> its final JSON. Even if the JSON is lost (process killed, stdout truncated),
> the publisher falls back to scanning the `-1..-N` suffixed output paths on
> disk, so already-generated images are still published. Stops gracefully with
> whatever succeeded if fewer than N images land.

### One-Time Setup

```bash
cd image-factory-skill
npm install            # installs the playwright dependency
npm run setup:xhs      # = playwright install chromium (downloads the browser)
```

### First Login (QR scan, once)

On the first publish there's no saved session:

1. The script detects "not logged in" and opens a **visible** browser window on
   the Xiaohongshu login page
2. Scan the QR code with the Xiaohongshu app
3. The session is persisted to `--user-data-dir` (default
   `~/.image-factory-skill/xhs-profile`); later runs skip the QR scan
4. If the session expires, the script re-opens a visible window to re-scan

### Publish (default = stop at the publish button)

**By default the script fills cover + title + body + topics, then STOPS at the
"发布" button, takes a screenshot, and does NOT click publish.** This matches
xiaohongshu-ops's safety rule ("stop at the publish page, wait for user
confirmation") and prevents accidental posting. Pass `--publish` to actually
click publish.

> **Stop mode keeps the window open.** When stopping at the button (no
> `--publish`), the script forces a **headed (visible) browser** and keeps it
> open until you close it yourself — it does NOT auto-close after a few seconds.
> Review the filled content in the window, click 「发布」 manually, then close the
> window and the script exits. (Earlier the window was headless / closed after
> 1.5s, so it flashed by before you could act — fixed.)

```bash
# Default: fill everything, stop at the publish button (recommended)
node scripts/publish_xiaohongshu.js \
  --image cover.png \
  --title "我用AI做了张图" \
  --content "今天试了下AI生图，效果不错…" \
  --topics "AI,效率工具"

# Multi-image, body from file, auto-publish (explicit opt-in)
node scripts/publish_xiaohongshu.js \
  --image a.png,b.png,c.png \
  --title "三图测评" \
  --content-file body.md \
  --publish

# Preview args without launching a browser
node scripts/publish_xiaohongshu.js --image x.png --title "x" --content "y" --dry-run
```

### Rules (aligned with xiaohongshu-ops publish SOP)

- **Three required elements**: cover (first image), title, body
- **Title ≤ 20 chars** — hard-validated; over-limit fails fast with a "compress"
  hint
- **Topics via UI dropdown**, not pasted text — the script types `#topic` then
  selects the dropdown item so the topic entity isn't lost
- **First image = cover**
- **AI-content declaration (default ON)**: selects 「添加内容类型声明 → 笔记含AI合成内容」
  (note: 「合成」, not 「生成」 like Douyin). Pass `--no-ai-declare` to skip. After
  picking, the script dismisses the dropdown overlay (Escape + click the title
  input) so it doesn't cover the publish button. Failure only warns.
- **⚠️ Viewport is locked at 1280×900**: the publish button's red-pixel click
  coordinates depend on it. Raising the height (e.g. to fit the declaration
  dropdown) shifts the sticky publish bar and makes every publish silently fail.
- **⚠️ Copyrighted-IP text is silently blocked**: titles/topics with IP terms
  (原神/凝光/cos/空姐 …) get rejected by XHS with no error, no draft, no review
  record — the note just never posts. Same image with generic copy publishes
  fine. De-IP the copy for fan/IP content.

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--image`, `-i` | Existing image path(s), comma-separated or repeated (first = cover) | required unless `--prompt`/`--prompt-file` given |
| `--prompt`, `-P` | Generation prompt: when no `--image`, generate the image first, then publish | - |
| `--provider` | Generation backend `auto`/`codex`/`gemini` (only when generating) | auto |
| `--aspect-ratio`, `--ar` | Image aspect ratio (only when generating) | 3:4 |
| `--output`, `-o` | Save path for the generated image (only when generating) | temp file |
| `--title`, `-t` | Note title (≤20 chars, hard-validated) | derived from prompt style if omitted |
| `--content`, `-c` | Body text | derived from prompt if omitted |
| `--content-file` | Read body from a file | - |
| `--prompt-file` | Prompt file (`prompts/YYYYMMDD-NN.md`); image source AND/OR title/body derivation | - |
| `--topics` | Topics, comma-separated (no `#`, added automatically) | - |
| `--publish` | Actually click publish (default: stop at the button) | false |
| `--headed` | Show the browser window (auto-on when not logged in) | false |
| `--user-data-dir` | Persistent login profile dir | `~/.image-factory-skill/xhs-profile` |
| `--screenshot` | Screenshot path when stopping | `/tmp/xhs-publish-<ts>.png` |
| `--timeout` | Per-step timeout (ms) | 30000 |
| `--dry-run` | Preview args/steps, no browser, no generation | false |

Image, title, and body must each be resolvable: an image comes from `--image`
OR from generating with `--prompt`/`--prompt-file`; title/body come from explicit
flags OR prompt derivation. Explicit values always win.

`XHS_USER_DATA_DIR` env var is equivalent to `--user-data-dir`.

**Exit codes:** `0` success (stopped at button, or published) / `1` failure.

### Selector Maintenance

Xiaohongshu revamps its creator UI periodically. All selectors live in the
`SELECTORS` block at the top of `publish_xiaohongshu.js`, each with multiple
candidates + one retry. When a step reports "selector may be stale", run with
`--headed`, inspect the real DOM, and prepend the new selector to the relevant
key. See `references/xiaohongshu-publish-guide.md` for the full maintenance
guide and troubleshooting table.

## Publish to Douyin (抖音)

A third output channel: publish a generated (or existing) image as a Douyin
**image-text post (图文)** via a persistent Playwright session — same shape as
the Xiaohongshu channel.

> **Why a browser:** Douyin's creator platform has no public posting API; an
> image-text post can only be published from a logged-in browser session. The
> flow (creator.douyin.com → 高清发布 → 发布图文 tab → 上传图文 → 标题/简介 →
> 发布) runs on a Playwright persistent context.

### When to Use

- User asks to "发布到抖音", "发一篇抖音图文", "publish to douyin"
- User has an image (just generated, or pre-existing) plus a title/description

### One-Time Setup

```bash
cd image-factory-skill
npm install              # installs the playwright dependency
npm run setup:douyin     # = playwright install chromium (shared with the XHS channel)
```

### First Login (QR scan, once)

1. The script detects "not logged in" and opens a **visible** window on
   `creator.douyin.com`, auto-clicking the 「登录」entry to surface the QR
2. Scan with the Douyin app; if SMS verification is triggered, complete it in
   the window
3. Session persists to `--user-data-dir` (default
   `~/.image-factory-skill/douyin-profile`); later runs skip the QR scan

> Login is detected only by the 「高清发布」button (present only when logged in).
> Avatar elements are NOT used — the logged-out landing page has them too.

### Publish (default = stop at the publish button)

**Same safety model as XHS:** fill image + title + description, then STOP at the
「发布」button and screenshot. Pass `--publish` to actually click publish (then
the script checks the success toast).

```bash
# One shot: prompt → image → derived title/description → publish page (stops)
node scripts/publish_douyin.js --prompt "赛博朋克风格的城市夜景" --topics "AI,夜景"

# Generate N different images from one prompt, publish as one multi-image post
node scripts/publish_douyin.js \
  --prompt "手绘风格的部署流程图" \
  --count 3 \
  --topics "AI,架构"

# Existing image + explicit copy
node scripts/publish_douyin.js \
  --image cover.png --title "我的标题" --content "简介正文" --topics "AI"

# Multi-image, description from file, auto-publish
node scripts/publish_douyin.js \
  --image a.png,b.png --title "三图" --content-file body.md --publish

# Preview only (no browser, no generation)
node scripts/publish_douyin.js --prompt "水彩风格的猫" --dry-run
```

### Differences from the XHS channel

- **Title cap is 30 chars** (XHS is 20) — hard-validated all the same.
- **Topics**: Douyin has no separate topic dropdown, so `--topics` are appended
  to the description as `#tag` text.
- **Background music (default ON)**: after filling the description, the script
  auto-selects the **first track in the 「推荐」(Recommended) list** (open 选择音乐
  → hover first song → click 使用). Pass `--no-music` to skip. Failure only warns
  and does not block publishing.
- **AI-content declaration (default ON, compliance-critical)**: AI-generated
  content must be declared on Douyin or it's flagged as a violation / throttled.
  The script auto-selects 「自主声明 → 内容由AI生成」 (open the declaration entry →
  pick the 内容由AI生成 radio → click 确定). Pass `--no-ai-declare` to skip.
  Failure **warns loudly** (missing declaration is a compliance risk) and asks
  you to pick it manually in the window.
- **`--publish` forces a headed (visible) browser**: Douyin's publish action is
  blocked under headless (click → stuck on 「正在发布」 forever, never lands). The
  script auto-switches to headed when `--publish` is set; default stop-at-button
  and `--dry-run` stay headless. (XHS publishes fine headless — this is
  Douyin-specific.)
- **Aspect ratio** default `3:4` (vertical), same as XHS.
- **Profile dir**: `~/.image-factory-skill/douyin-profile` (env override:
  `DOUYIN_USER_DATA_DIR`).
- Title/description auto-derivation (style→title, condensed prompt→body) is
  **identical** to the XHS channel.

### Arguments

Same as `publish_xiaohongshu.js` except `--topics` go into the description and
`--title` allows ≤30 chars. Run `node scripts/publish_douyin.js --help` for the
full list.

### Selector Maintenance

All selectors live in the `SELECTORS` block at the top of `publish_douyin.js`.
When a step reports a stale selector, run with `--headed`, inspect the DOM, and
prepend the new selector. See `references/douyin-publish-guide.md` for the full
maintenance table (keys: `hdPublishBtn` / `tabImageText` / `uploadImageTextBtn`
/ `uploadFileInput` / `titleInput` / `descriptionInput` / `publishContainer` /
`loggedIn`).

## Reverse-Engineer & Optimize Prompts

A fourth capability, parallel to the three publish channels: **turn an image
back into a reusable text-to-image prompt** (reverse), and **restructure /
upgrade an existing prompt under a style preset** (optimize). Both run on the
same `codex-cli` / `agy` backends as image generation, so no extra
dependencies. Output format is identical to `prompts/YYYYMMDD-NN.md`, which
means the whole pipeline composes:

```
某张图 ──reverse──▶ prompt ──optimize──▶ 更好的 prompt ──generate-image──▶ 新图 ──send/publish──▶ ...
```

### When to use

- 「这张图是怎么 prompt 出来的？」 / "reverse prompt from this image"
- 「这条 prompt 太糙了，能不能 polish 一下」 / "optimize this prompt for blueprint style"
- 想批量基于一张参考图迭代变体 — 先反推、改风格、再生成
- 给 Xiaohongshu / Douyin 图文反向准备 prompt（已发出去的图想再产一批同风格的）

### Reverse: image → prompt

`scripts/reverse-prompt.js` 读取一张图，让 codex/agy 反推出"最可能生成这张图
的 prompt"，按 `[Style] + [Type] + [Content] + [Key elements]` 结构输出，附带
`STYLE_TAG`（风格标签）和 `ASPECT_HINT`（建议长宽比）。

```bash
# 看图说话：prompt 直接打到 stdout（其他日志走 stderr，便于 pipe）
node scripts/reverse-prompt.js -i cover.png

# 反推 + 归档到 prompts/YYYYMMDD-NN.md（source: reverse 标记）
node scripts/reverse-prompt.js -i cover.png --archive --ar 3:4

# 写到独立文件，用 agy 后端
node scripts/reverse-prompt.js -i cover.png -p agy -o reversed.md

# 机器消费：仅输出 JSON
node scripts/reverse-prompt.js -i cover.png --json
```

**Key arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `--image`, `-i` | 源图片路径 | required |
| `--output`, `-o` | 输出文件（带 frontmatter） | - |
| `--archive` | 自动归档到 `prompts/YYYYMMDD-NN.md` | false |
| `--provider`, `-p` | `auto` / `codex` / `agy` | auto |
| `--lang`, `-l` | `zh` 中文主体技术词英文 / `en` / `auto` | zh |
| `--aspect-ratio`, `--ar` | 写入归档文件的 aspect_ratio | auto |
| `--json` | 仅输出 JSON 到 stdout | false |
| `--dry-run` | 打印调用计划，不实际跑后端 | false |

**Output format**（归档/`--output` 文件）：

```yaml
---
aspect_ratio: "3:4"
provider: codex
source: reverse
source_image: /abs/path/to/cover.png
style_tag: hand-drawn
timestamp: 2026-06-29T...
---

PROMPT:
<反推出来的 prompt 主体>
```

stdout 上的裸 PROMPT 文本可以直接 pipe，例如 `node reverse-prompt.js -i a.png | node optimize-prompt.js --stdin -s blueprint`。

### Optimize: prompt → 更好的 prompt

`scripts/optimize-prompt.js` 接受一段原始 prompt（来自用户、reverse-prompt、
或 `prompts/` 归档文件），按 `[Style] + [Type] + [Content] + [Key elements]`
结构改写，可指定风格预设。仅做改写，不调用生图 — 想生图就把 stdout 喂回
`generate-image.js`。

```bash
# 字面 prompt + 风格预设
node scripts/optimize-prompt.js \
  --prompt "画一张三层 web 架构图" \
  --style blueprint \
  --archive --ar 16:9

# 复用归档过的 prompt（路径直接给 prompts/ 下的文件即可）
node scripts/optimize-prompt.js \
  --prompt-file prompts/20260628-01.md \
  --style hand-drawn -o optimized.md

# 从 stdin 读（适合串联）
node scripts/reverse-prompt.js -i cover.png \
  | node scripts/optimize-prompt.js --stdin --style cyberpunk --archive

# 看可用风格预设
node scripts/optimize-prompt.js --list-styles
```

**Style presets**（与 SKILL.md 内现有的风格关键词表对齐）：

| Preset | 中文描述 | 关键词 |
|--------|---------|--------|
| `hand-drawn` | 手绘风 | warm cream background, black ink lines, pastel color blocks |
| `blueprint`  | 科技蓝图 | blueprint grid, white wireframe lines, cyan tone |
| `watercolor` | 水彩 | soft light, paper texture, ink bleed |
| `cyberpunk`  | 赛博朋克 | neon lights, rainy night, magenta + cyan |
| `3d`         | 3D 渲染 | soft lighting, depth of field, realistic materials |
| `healing`    | 治愈系 | soft palette, low saturation, warm tone |
| `minimal`    | 极简 | generous whitespace, oversized typography |
| `photo`      | 摄影风 | natural light, cinematic, 35mm look |
| `keep`       | 保留原风格 | 仅做结构化和措辞润色，不替换风格 |
| `auto`       | 自动 | 由后端按原 prompt 语境判断（默认） |

**Key arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `--prompt` / `--prompt-file` / `--stdin` | 原始 prompt 来源（三选一） | required |
| `--style`, `-s` | 见上表 | auto |
| `--lang`, `-l` | `zh` / `en` / `auto` | zh |
| `--provider`, `-p` | `auto` / `codex` / `agy` | auto |
| `--output`, `-o` | 优化后 prompt 写入文件 | - |
| `--archive` | 自动归档到 `prompts/YYYYMMDD-NN.md`（`source: optimize`） | false |
| `--aspect-ratio`, `--ar` | 写入归档/输出文件的 aspect_ratio | auto |
| `--json` | 仅输出 JSON | false |
| `--dry-run` | 打印 optimization prompt 预览，不调后端 | false |

归档文件的 frontmatter 标记 `source: optimize`、`style: <preset>`，便于之后区分。

### Common pipelines

**A. 「我有一张图，想要一张同风格但内容稍改的新图」**

```bash
# 1. 反推
node scripts/reverse-prompt.js -i original.png --archive --ar 3:4
# → prompts/20260629-01.md  (source: reverse)

# 2. 优化 / 改内容（手动 edit 那个 md 文件里的 PROMPT 段，或用 optimize）
node scripts/optimize-prompt.js \
  --prompt-file prompts/20260629-01.md --style keep --archive
# → prompts/20260629-02.md  (source: optimize)

# 3. 生图
node scripts/generate-image.js \
  --prompt-file prompts/20260629-02.md --output new.png --ar 3:4

# 4. 发飞书 / 发小红书 / 发抖音（任选其一）
python scripts/send_feishu_image.py --image new.png --user-ids ou_xxx
```

**B. 「这条粗略的 prompt 帮我打磨成蓝图风」**

```bash
node scripts/optimize-prompt.js \
  --prompt "三层 web 架构图：前端、API、数据库" \
  --style blueprint --archive --ar 16:9
# → 输出 + 归档好的 prompt
```

**C. 「直接走完反推 → 优化 → 生图 → 发抖音」**

```bash
node scripts/reverse-prompt.js -i ref.png \
  | node scripts/optimize-prompt.js --stdin --style cyberpunk -o /tmp/p.md \
  && node scripts/generate-image.js --prompt-file /tmp/p.md --output /tmp/new.png --ar 3:4 \
  && node scripts/publish_douyin.js --image /tmp/new.png --prompt-file /tmp/p.md
```

### Error handling

- **后端不可用**：脚本启动时 `which codex / which agy`，两个都没装就报 `没找到可用的后端`。装 codex-cli 或 agy 任一即可（与图片生成共用）。
- **后端没产出 `PROMPT:` 段**：脚本会去掉常见噪声（thinking / tokens used 行）后兜底当作 prompt 返回，但 stderr 会提示，加 `--verbose` 看后端原始输出再判断。
- **超时**：默认 3 分钟；`--timeout 300` 可调大。
- **图片读不到**：reverse 启动前做 `stat()`，找不到立刻报错。

### Limitations

1. 后端是 codex/agy，**没有专门的视觉模型**：反推质量与后端读图能力强相关。codex 通常优于 agy。
2. 风格预设是"关键词 + 中文描述"的提示注入，不保证后端 100% 遵循 — 复杂场景下可能要手工再润色一遍。
3. 不做对抗性 prompt 评估，也不打分 — 这是个生成器，不是评估器。

## Generate Portrait Prompt (Character/Figure from Scratch)

A third parallel capability: **主体描述 + 风格预设 → 一条开箱即生图的人物图 prompt**。

与前两个（reverse / optimize）的区别：
- reverse:图 → prompt（已有图，反推）
- optimize:prompt → 更好的 prompt（已有 prompt，改写）
- **portrait:主体一句话 + 风格 → 完整人物图 prompt**（**从零开始**，按风格生成一条含 [Style][Type][Content][Key elements] + 镜头/光照/画质/负面提示的单人写真 prompt）

适合场景：你知道要画什么人物主体（"雪中红衣女子回眸"/"咖啡馆看书的女孩"），但不想从零拼 prompt、不确定镜头/光照/画质词该怎么写 — 交给这个脚本，它会基于风格预设（如 gufeng-portrait 古风宫廷写真 / photo-portrait 写实人像摄影）生成一条符合生图要求的完整 prompt。

### When to use

- 「我想要一张古风人物图，主体是 XX，帮我写条生图 prompt」
- 「生成人物图提示词：一位临窗抚琴的少女」
- 「写一条"雪中红衣女子回眸"的古风写真 prompt」
- 想快速出人物图，但不想手写一长串 [Style] + camera + lighting + quality + negative

### Usage

`scripts/generate-portrait-prompt.js` 输入主体（`--subject`）+ 风格（`--style`），用 codex/agy 生成结构化的单人人物图 prompt。stdout 裸 prompt 可 pipe 给 `generate-image.js`。

```bash
# 最简：一句话主体，用默认古风写真风格，归档
node scripts/generate-portrait-prompt.js -S "雪中红衣女子回眸" --archive

# 指定风格 photo-portrait，写入文件
node scripts/generate-portrait-prompt.js \
  -S "咖啡馆里看书的女孩" -s photo-portrait -o p.md --ar 3:4

# 生成后直接喂给 generate-image.js（pipe）
node scripts/generate-portrait-prompt.js -S "临窗抚琴的古风少女" \
  | node scripts/generate-image.js --stdin --output out.png --ar 3:4

# 看可用风格预设（[人物] 标记的是人物写真专用）
node scripts/generate-portrait-prompt.js --list-styles
```

**Key arguments:** `--subject/-S`（必填，主体一句话）、`--style/-s`（默认 gufeng-portrait）、`--archive`（归档到 prompts/，source: portrait）、`--output/-o`（写文件）、`--ar`（默认 3:4）、`--list-styles`（看风格）、`--dry-run`（打印 generation prompt 预览）。

**可用风格**（人物写真专用，`kind: 'portrait'`）：
- `gufeng-portrait`（古风宫廷写真）：warm cream 米白背景、金线质感、柔焦棚拍、汉服盘发珠钗、清透古风妆
- `photo-portrait`（写实人像摄影）：自然光、真实皮肤质感、电影感

通用风格（hand-drawn / blueprint 等）也能用，但没有专门的人物拍摄指引。**扩展风格**：编辑 `scripts/styles.js`，加一条 `kind: 'portrait'` 预设（含 camera/lighting/composition/quality/negative）即可。

**Output format**（归档文件）：frontmatter 含 `source: portrait` + `style` + `subject` + `negative`，PROMPT 主体含 [Style][Type][Content][Key elements] 四段 + 画质词。Negative 在 frontmatter 里，生图时作为负面提示传给后端。

**设计说明**：

1. **为什么不直接用 optimize？** optimize 是"改写已有 prompt"；portrait 是"从主体一句话凭空生成"，输入不同。Portrait 生成的 prompt 已经是结构化 + 带画质词/负面提示的"开箱即生图"版本。
2. **默认 gufeng-portrait？** 从 `images/` 下四张「古代女子妆容」海报反推沉淀的风格，古风人物是高频需求，默认就给它。
3. **能否多人/群像？** 不能。本脚本专注"单人人物写真"，prompt 模板明确要求单人，负面提示屏蔽了"四宫格/多人/拼图"。多人群像用 optimize 或手写。





The skill uses `scripts/send_feishu_image.py` as the main orchestrator. You can call it directly or via the skill workflow.

**Basic usage:**

```bash
# Generate and send (orchestrator handles both)
python scripts/send_feishu_image.py \
  --prompt "A hand-drawn system architecture diagram" \
  --user-ids "ou_xxx" \
  --chat-ids "oc_yyy"

# Send existing image
python scripts/send_feishu_image.py \
  --image existing-image.png \
  --user-ids "ou_xxx"

# With caption and custom settings
python scripts/send_feishu_image.py \
  --prompt "Tech infographic showing deployment pipeline" \
  --user-ids "ou_aaa,ou_bbb" \
  --chat-ids "oc_zzz" \
  --caption "Q2 deployment architecture" \
  --aspect-ratio "16:9" \
  --as bot
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `--prompt` | Image generation prompt (required if `--image`/`--prompt-file` not provided) | - |
| `--prompt-file` | Prompt markdown file; used to generate, OR attached as copyable text in `--image` mode | - |
| `--image` | Pre-generated image path(s); comma-separated for multi-image (skips generation) | - |
| `--count`, `-n` | Generate N distinct images from one prompt, send as one multi-image message | 1 |
| `--user-ids` | Comma-separated user open_ids (ou_xxx) | From `.env` |
| `--chat-ids` | Comma-separated group chat_ids (oc_xxx). Pass `--chat-ids ""` to send to users only (overrides `.env`) | From `.env` |
| `--caption` | Title line of the image message | "🎨 AI 生成图片" |
| `--copywriting`, `--copy` | Social-media post copy, attached as a standalone paragraph above the prompt (long-press to copy whole) | - |
| `--tags` | Social-media tags, comma-separated (auto-prefixed with `#`), appended to the copy paragraph | - |
| `--no-prompt-caption` | Don't attach the generation prompt as copyable text | False |
| `--aspect-ratio` | Image aspect ratio (e.g., 16:9, 1:1, 4:3) | 16:9 |
| `--as` | Send identity: `bot` or `user` | From `.env` (default: bot) |
| `--dry-run` | Preview without actually sending | False |

**Message layout** (paragraphs, social-media friendly): `[N images] → [📋 copy + tags, one standalone paragraph] → [📝 Prompt]`. Feishu has no native "copy button" for post messages, so the copy+tags are merged into one continuous paragraph — long-press it in Feishu to select & copy the whole block in one go. (An interactive-card code block *does* expose a copy button, but renders in monospace like a code box; the merged-paragraph approach was chosen for natural styling.)

**Exit codes:**
- `0`: All targets succeeded
- `1`: At least one target failed (or generation failed)

## Prompt Archiving

Every successful image generation **automatically archives both the prompt and
the generated image(s)** to the skill's `prompts/` directory, for later
classification and reuse.

**Naming convention** (prompt and images share the same `YYYYMMDD-NN` prefix,
so you can sort/filter the whole library by date or sequence):

```
prompts/
├── YYYYMMDD-NN.md                  ← prompt + frontmatter
└── images/
    ├── YYYYMMDD-NN.png             ← single-image generation
    ├── YYYYMMDD-NN-1.png           ← multi-image (--count N), image 1
    ├── YYYYMMDD-NN-2.png           ← multi-image, image 2
    └── YYYYMMDD-NN-N.png           ← ...
```

- `YYYYMMDD` — generation date
- `NN` — zero-padded daily sequence number, starting at `01`
- `-1..-N` suffix appears **only** when `--count >= 2`; single-image generation
  uses the bare `YYYYMMDD-NN.<ext>` so the prompt and its image are an obvious
  pair

Each archived prompt file carries frontmatter (`aspect_ratio`, `provider`,
`timestamp`) plus the full `PROMPT:` body. To reuse an archived prompt:

```bash
python scripts/send_feishu_image.py --prompt-file prompts/20260625-01.md
```

Archiving is handled by `archive_prompt()` + `archive_images()` in the three
publish entry points (`send_feishu_image.py`, `publish_xiaohongshu.js`,
`publish_douyin.js`) — same naming logic everywhere, no manual sequence
management needed. Image archiving is **best-effort**: failures only warn and
never block the send/publish flow (the archive is for later regrouping, not a
prerequisite for delivery). See `prompts/README.md` for details.

> **Note on full-prompt fidelity:** The prompt parser uses `\Z` (true
> end-of-string), not `$` (end-of-line). An earlier bug used `$` with the
> multiline flag, which truncated multi-paragraph prompts to the first
> paragraph only — both when generating and when attaching the copyable prompt
> text. Multi-paragraph prompts now generate and attach in full.

## Configuration

### Environment Variables (`.env`)

```bash
# ───────────────────────────────────────────────
# 飞书推送配置
# ───────────────────────────────────────────────
# 接收用户的 open_id，多个用英文逗号分隔（ou_xxx,ou_yyy）
FEISHU_USER_IDS=ou_b8ad79xxxxxxxxxxxxxxxxxxxxxxxxxx

# 接收群聊的 chat_id，多个用英文逗号分隔（oc_xxx,oc_yyy）
FEISHU_CHAT_IDS=oc_6f8ae48xxxxxxxxxxxxxxxxxxxxxxxxxx

# 发送身份：bot（机器人，默认推荐）| user（用户本人，需 im:message.send_as_user 权限）
FEISHU_SEND_AS=bot
```

**To find user/chat IDs:**

```bash
# Find user open_id
lark-cli contact +search-user --query "张三"

# List available group chats
lark-cli im +chat-list

# Search for a specific group
lark-cli im +chat-search --query "研发群"

# Check your own open_id
lark-cli auth status
```

### Feishu CLI Setup

**Prerequisites:**
1. Install lark-cli: `npx @larksuite/cli@latest install`
2. Authenticate: `lark-cli auth login`
3. (Optional) For user identity: `lark-cli auth login --scope "im:message.send_as_user"`

**Verify setup:**
```bash
lark-cli auth status
```

Should show:
- `identities.bot`: Ready
- `identities.user`: Ready (if using `--as user`)
- `user.scope`: Should include `im:message.send_as_user` if using user identity

See `references/feishu-cli-guide.md` for detailed setup and troubleshooting.

## Image Generation Backends

The skill requires **at least one** of these tools:

### Codex CLI (Recommended)
- **Command**: `codex`
- **Install**: https://openai.com/zh-Hans-CN/codex or `npm install -g codex-cli`
- **Verify**: `codex --version`
- **Note**: If you see config errors, remove `service_tier` from `~/.codex/config.toml`

### Antigravity CLI (Gemini)
- **Command**: `agy`
- **Install**: https://antigravity.google/docs/cli-getting-started
- **Verify**: `agy --version`

The `generate-image.js` script auto-detects which backend is available and uses it. If both are available, it prefers codex by default.

## Error Handling

### Common Errors

**Generation failures:**
- `No image generation backend available` → Install codex-cli or agy
- `Command timed out` → Image generation took >5 minutes, may succeed on retry
- `Codex returned but no image found` → Check `~/.codex/generated_images/` permissions

**Feishu send failures:**
- `230002: Bot/User can NOT be out of the chat` → Bot must be added to the group first
  - Solution: Open group settings → Add bot → Try again
- `missing required scope(s): im:message.send_as_user` → Using `--as user` without permission
  - Solution: Use `--as bot` instead, or request permission and re-login
- `im:resource:upload` / `uploading image` error → User identity lacks image upload permission
  - This is separate from text-send permission — sending images needs more scopes than sending text
  - Solution: Use `--as bot` (has upload by default), or re-authorize: `lark-cli auth login --scope "im:resource:upload im:resource"`
- `Invalid open_id or chat_id` → Check ID format (ou_xxx for users, oc_xxx for groups)

**Path errors:**
- lark-cli rejects absolute paths → The orchestrator handles this automatically
- If you see path errors, ensure you're using the provided `send_feishu_image.py` script

### Troubleshooting Workflow

1. **Check backends**: `which codex && which agy`
2. **Test generation**: `node scripts/generate-image.js --prompt test.md --output test.png`
3. **Check lark-cli**: `lark-cli auth status`
4. **Verify recipients**: `lark-cli im +chat-list` to confirm bot/user is in target groups
5. **Dry-run**: Use `--dry-run` flag to preview without sending

## Examples

### Example 1: Quick image to one person

```
User: "生成一张手绘风格的流程图，发给张三 (ou_abc123)"

→ Create prompt: "A hand-drawn flowchart showing [inferred context]"
→ Generate image via codex-cli
→ Send to ou_abc123 as bot
→ Report: ✅ Image sent successfully
```

### Example 2: Batch send to team

```
User: "创建一个科技感的系统架构图，发给开发组和产品组"

→ User provides chat IDs: oc_dev123, oc_product456
→ Generate image with tech/blueprint style
→ Send to both groups
→ Report success per group
```

### Example 3: With caption

```
User: "给研发群发一张产品路线图，配文：Q2 规划草图，请大家review"

→ Generate roadmap-style image
→ Send image to oc_xxx
→ Follow up with markdown caption
→ Report: ✅ Image + caption sent
```

### Example 4: Send existing image

```
User: "把 output/diagram.png 这个图发给张三和李四"

→ Skip generation
→ Send diagram.png to multiple users
→ Report: ✅ Sent to 2 users
```

## Best Practices

1. **Prompt Quality**: Clear, detailed prompts produce better images
   - ✅ "A hand-drawn infographic showing three-tier web architecture with frontend, API layer, and database"
   - ❌ "架构图"

2. **Recipient Verification**: Before sending to groups, ensure bot is a member
   - Use `lark-cli im +chat-list` to verify

3. **Identity Selection**:
   - Use `bot` for most cases (simpler, fewer permissions needed)
   - Use `user` only when you need to send as yourself and have proper permissions

4. **Caption Usage**: Captions help provide context
   - Use for version info, status updates, or action items
   - Keep concise (1-2 sentences)

5. **Batch Sending**: The script continues even if one target fails
   - Review the summary to see which recipients succeeded
   - Retry failed targets individually if needed

6. **Temporary Files**: Generated images are saved to `/tmp/feishu-image-*.png` by default
   - Cleaned up automatically
   - Use `--output` to save to a specific location

## Tips for Generating Good Images

Based on the article-illustration-tools patterns:

**For technical content:**
- Prompt: "A blueprint-style infographic showing..."
- Works well for: Architecture diagrams, system designs, API flows

**For tutorials/processes:**
- Prompt: "A hand-drawn flowchart illustrating..."
- Works well for: Step-by-step guides, decision trees, workflows

**For data/metrics:**
- Prompt: "A clean vector illustration showing data comparison..."
- Works well for: Charts, comparisons, metrics dashboards

**General structure:**
```
[Style] + [Type] + [Content] + [Key elements]

Example: "A hand-drawn infographic showing a three-layer web architecture 
with labeled components: React frontend, Node.js API, and PostgreSQL database. 
Use warm cream background with black lines and pastel blocks."
```

## Dependencies

- **Node.js** (>=14.0.0): For `generate-image.js`
- **Python** (>=3.6): For orchestrator script
- **lark-cli**: Feishu/Lark command-line tool (Feishu channel only)
- **Image backend**: codex-cli OR agy (at least one required for generation)
- **Playwright** (Xiaohongshu channel only): `npm install` + `npm run setup:xhs`
  (= `playwright install chromium`). Node >=18 recommended for this channel.

Run verification:
```bash
node --version      # Should be >=14 (>=18 for the XHS channel)
python3 --version   # Should be >=3.6
lark-cli --version  # Should show installed version (Feishu channel)
which codex || which agy  # At least one should exist (for generation)
# Xiaohongshu channel:
npm run setup:xhs && node scripts/publish_xiaohongshu.js --help
```

## Reference Documentation

- `references/feishu-cli-guide.md` - Complete Feishu CLI setup and troubleshooting
- `references/xiaohongshu-publish-guide.md` - Xiaohongshu publish SOP, first login, selector maintenance
- `references/douyin-publish-guide.md` - Douyin publish SOP, first login, selector maintenance
- `references/reverse-and-optimize-guide.md` - 反推 / 优化 prompt 的设计说明、style preset 表、常见问题、扩展风格库方法
- `scripts/styles.js` - 共享风格预设库（reverse / optimize / portrait 三个脚本共用）；扩展风格只需编辑此文件
- `scripts/generate-image.js` - Image generation implementation (from article-illustration-tools)
- `scripts/reverse-prompt.js` - 图片 → prompt 反推 (codex / agy)
- `scripts/optimize-prompt.js` - prompt → 优化 prompt（含风格预设, codex / agy）
- `scripts/generate-portrait-prompt.js` - 主体描述 + 风格 → 人物图 prompt（从零生成，含镜头/光照/画质/负面提示，codex / agy）
- `scripts/publish_xiaohongshu.js` - Xiaohongshu image-text note publisher (Playwright)
- `scripts/publish_douyin.js` - Douyin image-text post publisher (Playwright)
- Feishu Open Platform: https://open.feishu.cn/document/
- lark-cli GitHub: https://github.com/larksuite/cli

## Limitations

1. **Image size**: Generated images typically 1-3MB (within lark-cli limits)
2. **Timeout**: 5 minutes per image generation (configurable in generate-image.js)
3. **Concurrency**: Serial sending to avoid rate limits
4. **File types**: PNG only (lark-cli also supports JPG/WebP if you modify the script)
5. **Group access**: Bot identity requires bot to be pre-added to groups

## Future Enhancements

Potential improvements (not implemented):
- Batch prompt processing (multiple images in one command)
- Style presets from article-illustration-tools
- Image editing/retry workflow
- Progress notifications for long generations
- Template library for common diagram types
