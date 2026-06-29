# 小红书发布指南（Playwright 版）

本文件是 `scripts/publish_xiaohongshu.js` 的配套说明：发布 SOP、首次登录、selector 维护点、安全规则。

> 本脚本在**没有 OpenClaw**的环境里用 **Playwright 独立 Chromium** 实现了「图文发布」这一条链路。发布 SOP 与稳定性经验的致谢见 README「致谢」一节。

## 为什么用 Playwright 而不是 OpenClaw

小红书没有公开的发帖 API，发笔记必须依赖一个**已登录的浏览器会话**。参考仓库靠 OpenClaw 的 `browser` 工具（`profile=openclaw`）。本机没有 OpenClaw、`claw`、`clawhub`，也没有 Claude Code 的 browser 工具，所以改用 Playwright：

- 自包含，`npx playwright install chromium` 一次即可
- 持久化登录态（`launchPersistentContext`），首次扫码、后续免登
- 直接 `setInputFiles` 喂 `<input type=file>`，**没有** OpenClaw `browser.upload` 的 `/tmp/openclaw/uploads` 路径白名单限制

## 一次性准备

```bash
cd image-factory-skill
npm install            # 装 playwright 依赖
npm run setup:xhs      # = playwright install chromium，装浏览器内核
```

## 首次登录（扫码）

第一次发布时还没有登录态：

1. 脚本检测到未登录 → 自动以**可见窗口**打开小红书登录页
2. 用小红书 App 扫描窗口里的二维码
3. 脚本轮询到登录态后继续；登录态存到 `--user-data-dir`（默认 `~/.image-factory-skill/xhs-profile`）
4. 之后再发布**免扫码**，无头模式也能跑

登录态过期时，脚本会再次转可见窗口引导扫码。也可手动 `--headed` 强制开窗口登录一次。

## 图文发布三要素与规则

对齐 `xiaohongshu-ops` 的 `xhs-publish-flows.md`：

- **三要素必须齐全**：封面（首图）、标题、正文
- **标题 ≤ 20 字**：脚本强校验，超限直接 fail-fast 并提示压缩
- **话题用 UI 选项**：脚本逐个输入 `#话题` 后选下拉项，而不是纯文本粘贴一堆 `#`，避免丢失 topic entity（实操经验）
- **首图即封面**：`--image` 的第一张作为封面

## 生成即发布（--prompt 一条龙）

不给 `--image`、只给 `--prompt "<描述>"` 时，脚本自己跑完整条链路：

1. **生图** —— 调同目录 `generate-image.js`（codex / agy，与飞书通道同一套后端）
2. **归档 prompt** —— 写到 `prompts/YYYYMMDD-NN.md`（命名与 `send_feishu_image.py` 一致）
3. **推导标题/正文** —— 见下一节
4. **发布** —— 默认停在发布按钮

生图相关参数（仅在生成时有效）：

- `--provider auto|codex|gemini`：后端，默认 `auto`
- `--aspect-ratio` / `--ar`：宽高比，默认 `3:4`（小红书竖图友好）
- `--output` / `-o`：生成图保存路径，默认临时文件

容错：若 `generate-image.js` 报错/超时但 codex 已把图写进 `~/.codex/generated_images/`，脚本会兜底捞回最新那张——和飞书编排脚本同样的逻辑。

```bash
node scripts/publish_xiaohongshu.js \
  --prompt "赛博朋克风格的城市夜景，霓虹灯牌林立" \
  --provider codex --ar 3:4 \
  --topics "AI,赛博朋克"
```

## 标题/正文自动推导（--prompt / --prompt-file）

无论是 `--prompt`（现生）还是 `--prompt-file`（已归档），**没显式给的**标题/正文都会自动补上：

- **标题 ← 图片画风 + 主体**。从关键词表识别画风，拼上 prompt 首句主体，收口到 20 字。
  - 例：prompt 含「手绘风格的三层 Web 架构图」→ 标题 `手绘风的三层 Web 架构图`
  - 会去掉重复风格词（避免「手绘风的手绘…」）和「画一张/帮我」等指令套话
- **正文 ← prompt 精简版**。去掉开头指令套话（「画一张…风格的」）和技术尾巴（「高清渲染」「景深效果」「16:9」等），截到约 80 字的自然语言。

**优先级**：显式 `--title` / `--content` / `--content-file` > prompt 推导。都没有则报错。

**画风词表维护**：识别逻辑在脚本顶部的 `STYLE_KEYWORDS` 数组（`[命中词, 展示标签]`）。已覆盖手绘/水彩/插画/像素/低多边形/等距 2.5D/赛博朋克/故障艺术/国潮/新中式/水墨/吉卜力/黏土/折纸/C4D/皮克斯/超写实/治愈等几十种。要加新画风就往里加一行；**注意 `detectStyle` 用 `includes` 顺序匹配，越具体/越长的词要排在它的子串词之前**（如「扁平插画」排在「扁平」前，「新中式」排在「中式」前），否则会被短词抢先命中。

> 强烈建议先 `--dry-run`：输出会给每项标注来源 `(--title)` / `(按图片风格自动生成)` / `(prompt 精简)`，确认无误再发。

## 安全规则：默认停在发布按钮

**默认行为 = 填好所有内容后停在「发布」按钮，截图，不点发布。** 这与 `xiaohongshu-ops` 的「到发布页停手，等用户确认」一致，避免误发。

- 默认：停手 + 截图（`/tmp/xhs-publish-<时间>.png`），由你在浏览器窗口里人工点发布
- `--publish`：显式 opt-in，脚本自动点发布并校验成功提示

## 用法速查

```bash
# 默认：停在发布按钮（推荐）
node scripts/publish_xiaohongshu.js \
  --image cover.png \
  --title "我用AI做了张图" \
  --content "今天试了下AI生图，效果不错…" \
  --topics "AI,效率工具"

# 多图 + 正文从文件读 + 自动发布
node scripts/publish_xiaohongshu.js \
  --image a.png,b.png,c.png \
  --title "三图测评" \
  --content-file body.md \
  --publish

# 预览参数（不启动浏览器）
node scripts/publish_xiaohongshu.js --image x.png --title "x" --content "y" --dry-run
```

## Selector 维护点（改版必看）

小红书创作后台会改版，导致定位失效。**所有 selector 集中在脚本顶部的 `SELECTORS` 常量块**，每个动作配了多个候选 + 失败重试 1 次。当某一步报「selector 可能已失效」时：

1. 用 `--headed` 跑一遍，打开 DevTools 看真实 DOM
2. 在 `SELECTORS` 里对应的键（如 `uploadInput` / `titleInput` / `contentEditor` / `publishButton`）**把新的 selector 加到候选列表最前面**
3. 重跑验证

常见失效点：
- `uploadInput`：上传 `<input type=file>` 的 class 变了
- `titleInput` / `contentEditor`：编辑页输入框结构调整
- `topicOption`：话题下拉的列表项 class 变了
- `publishButton`：发布按钮文案/class 变了

### 2026 改版踩坑（已在脚本中处理，改版回归时参考）

这次改版有三个不靠常规 selector 就发现不了的坑，脚本已专门绕开：

1. **页面默认落在「上传视频」tab**，必须先切到「上传图文」。判断切换是否成功
   **不能看 `.creator-tab.active`**——`.active` class 挂在一个定位在屏外
   （`x:-9726`）的隐藏副本上，永远不可靠。正确判据是「出现 `accept` 含
   `png/jpg/webp` 的 `<input type=file>`」。见 `switchToImageTextTab()`。
2. **`.creator-tab` 有多个同名节点**，部分在屏外。要挑 `boundingBox().x>=0 && y>=0`
   的那个；且内层 `.title` span 会拦截指针事件，需 **force 点击**父节点。
3. **发布按钮是自定义元素 `<xhs-publish-btn>`，shadowRoot 为 closed**，内部 button
   用任何 selector / 穿透都拿不到。host 上有属性可读：
   `submit-text="发布" save-text="暂存离开" submit-disabled`。脚本用 host 作锚点，
   `--publish` 时**截 host 截图、扫描品牌红（≈255,36,66）像素定位「发布」按钮质心再坐标点击**
   （见 `decodePNG()` / `findRedButtonOffset()`）。
   ⚠️ **「发布」按钮不在栏最右，而是偏中位置**（实测 680px 栏内 x≈352–471，质心 412）；
   早期按「host 右侧」点击会完全打偏、点不动也不报错。扫不到红块时退回 `width*0.6` 经验坐标。
   隐藏 `<input>` / sticky 的 host 都可能不被判为 visible，故定位一律用
   `waitFor({state:'attached'})` 而非 `firstVisible`。
4. **发布成功判据**：跳转到 `/publish/success`（最可靠），其次看「发布成功」文案。
   旧的 `publishSuccess` 文案选择器单独用会漏判。
5. **内容类型声明（默认勾「笔记含AI合成内容」）**：表单底部 `d-select` 下拉。
   点 `div.d-select-main:has-text("添加内容类型声明")` 开下拉 → 选
   `.d-grid-item:has-text("笔记含AI合成内容")`（注意是「**合成**」不是「生成」，
   与抖音文案不同）→ 选完**必须收起浮层**再去点发布，否则浮层盖住发布按钮导致点击失效。
   收浮层用 `Escape` + 点回**标题输入框**（表单内安全元素）——
   ⚠️ **切勿盲点屏幕左上角 `(60,200)` 空白**，那里是侧边栏导航，会误触跳走整个页面。
   见 `selectAIDeclaration()`，`--no-ai-declare` 可关。
6. ⚠️ **viewport 必须保持 `1280×900`**：发布按钮红色像素定位（第 3 点）的坐标依赖此尺寸。
   曾为容纳声明下拉把高度改到 1400，结果 sticky 发布栏渲染位置偏移、红点坐标全部打偏、
   **所有发布静默失败**（点了不报错但发不出去）。声明下拉用 `scrollIntoViewIfNeeded`
   解决屏外问题即可，**不要动 viewport**。

> **另一个静默坑（非脚本 bug，平台行为）**：标题/话题里带版权 IP 词（如「原神」「凝光」
> 「cos」「空姐」）会被小红书**静默拦截**——点发布后无报错、无草稿、无审核记录，笔记就是发不出去。
> 同一张图换成通用文案即可正常发布。发同人/版权题材时需做去 IP 文案处理。

## 失败与降级

对齐参考仓库的「失败与修复」：

- 关键步骤（上传、进编辑页、点发布）失败先重试 1 次再降级报错
- 保留已完成进度，回传**一个**需要人工的动作（如「请人工点击发布」）
- 不做盲目重复点击

## 常见问题

| 现象 | 处理 |
|---|---|
| `未安装 playwright` | `npm install && npm run setup:xhs` |
| `启动 Chromium 失败` | `npx playwright install chromium` 装内核 |
| 登录超时 | 重跑，或 `--headed` 手动登录一次 |
| `找不到图片上传入口` | selector 失效，按上面「Selector 维护点」更新 `uploadInput` |
| 标题超长报错 | 压缩到 ≤20 字 |
| 话题没挂上 | 下拉没弹出时脚本会退化为文本话题；可改 `topicOption` selector |
