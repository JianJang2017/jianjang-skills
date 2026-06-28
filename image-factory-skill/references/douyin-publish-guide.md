# 抖音图文发布指南（Playwright 版）

`scripts/publish_douyin.js` 的配套说明：发布流程、首次登录、selector 维护点、安全规则。

> 本脚本在 image-factory-skill 里用 **Playwright 持久化上下文**实现了「图文发布」这一条链路，与小红书通道（`publish_xiaohongshu.js`）架构一致。发布流程的致谢见 README「致谢」一节。

## 为什么用 Playwright 持久化上下文

抖音创作者平台没有公开的发帖 API，发图文必须依赖**已登录的浏览器会话**。参考仓库用 CDP 连接 + 后台 daemon 维持会话；本脚本改用 Playwright `launchPersistentContext`：

- 自包含，一次 `npm run setup:douyin`（= `playwright install chromium`）即可
- 登录态持久化到 `--user-data-dir`（默认 `~/.image-factory-skill/douyin-profile`），首次扫码、后续免登
- 直接 `setInputFiles` / `filechooser` 喂图，无需注入页面对象

## 一次性准备

```bash
cd image-factory-skill
npm install              # 装 playwright 依赖
npm run setup:douyin     # = playwright install chromium，装浏览器内核
```

## 首次登录（扫码）

第一次发布时没有登录态：

1. 脚本检测到未登录 → 以**可见窗口**打开 `creator.douyin.com`
2. 自动点「登录」入口弹出二维码（弹不出时请在窗口里手动点登录）
3. 用抖音 App 扫码；若触发**短信验证**，请在窗口内输入手机收到的验证码完成验证
4. 登录态存到 `--user-data-dir`，之后免扫码

> 登录态判定只认「高清发布」按钮（仅登录后出现）。**不要**用 `[class*="avatar"]` 当登录信号——登出态落地页也有 avatar 元素，会误判已登录。

## 发布流程（对齐参考仓库 SOP）

`creator.douyin.com` → 点「高清发布」进上传页 → 切「发布图文」tab → 点「上传图文」(filechooser 喂图) → 填「作品标题」(标准 input) → 填「作品简介」(slate contenteditable) → 选配乐(默认「推荐」第一首) → 停在「发布」按钮。

- **首图即封面**：`--image` 的第一张作为封面
- **标题 ≤ 30 字**：脚本强校验，超限 fail-fast 提示压缩（抖音标题上限比小红书宽）
- **话题**：抖音没有小红书那种独立话题下拉，`--topics` 会作为 `#话题` **追加到简介末尾**
- **配乐（默认开启）**：填完简介后自动点「选择音乐」→ 在「推荐」tab → hover 第一首歌曲项 → 点浮现的「使用」。加 `--no-music` 跳过。失败仅警告、不阻断发布。
  - 选择器：入口 `div[class*="container-right"]:has-text("选择音乐")`；歌曲项 `div[class*="song-info"]`；「使用」按钮 `button[class*="apply-btn"]`（**仅 hover 歌曲项时浮现**，故用 `mouse.move` 到歌曲项中心再点）。

## 安全规则：默认停在发布按钮

**默认 = 填好图片/标题/简介后停在「发布」按钮，截图，不点发布。** 避免误发。

- 默认：停手 + 全页截图（`/tmp/douyin-publish-<时间>.png`），由你在窗口里人工点发布
- `--publish`：显式 opt-in，脚本自动点发布并检测 toast（含「发布成功」即成功）

> ⚠️ **`--publish` 会自动强制可见窗口（headed）**——抖音的发布动作在无头模式下会被
> 反自动化拦截：点击后稳定卡在「正在发布」永不完成（实测无头连续多次均未落地，
> 作品数不变；可见窗口一次成功并跳转作品管理页）。所以即使你没加 `--headed`，
> 只要带 `--publish`，脚本也会自动切 headed 并打印提示。默认停手 / `--dry-run` 不受影响。

## 用法速查

```bash
# 一条龙：只给 prompt → 生图 → 推导标题/简介 → 停在发布按钮
node scripts/publish_douyin.js --prompt "赛博朋克风格的城市夜景" --topics "AI,夜景"

# 已有图 + 显式文案
node scripts/publish_douyin.js \
  --image cover.png --title "我的标题" --content "简介正文" --topics "AI"

# 自动发布（显式 opt-in）
node scripts/publish_douyin.js --image a.png,b.png --title "三图" --content-file body.md --publish

# 预览（不启动浏览器/不生图）
node scripts/publish_douyin.js --prompt "水彩风格的猫" --dry-run
```

标题/简介自动推导逻辑与小红书通道完全一致（画风→标题、prompt 精简→简介），详见
`references/xiaohongshu-publish-guide.md` 的「标题/正文自动推导」一节。

## Selector 维护点（改版必看）

抖音创作者平台会改版。所有 selector 集中在脚本顶部的 `SELECTORS` 块，每个键是多候选列表。某步报「selector 可能已失效」时：

1. 用 `--headed` 跑一遍，开 DevTools 看真实 DOM
2. 在对应键把新 selector 加到候选列表最前面

常见失效点与对应键：

| 现象 | selector 键 |
|---|---|
| 进不了上传页 | `hdPublishBtn` |
| 切不到图文 tab | `tabImageText` |
| 找不到上传入口 | `uploadImageTextBtn` / `uploadFileInput` |
| 标题/简介填不进 | `titleInput` / `descriptionInput` |
| 配乐没选上 | `musicEntry` / `musicRecommendTab` / `musicSongItem` / `musicUseBtn`（「使用」按钮 hover 歌曲项才浮现） |
| 找不到发布按钮 | `publishContainer`（按钮在容器内按文本「发布」筛） |
| 误判登录态 | `loggedIn`（务必只认高清发布按钮） |

## 常见问题

| 现象 | 处理 |
|---|---|
| `未安装 playwright` | `npm install && npm run setup:douyin` |
| `启动 Chromium 失败` | `npx playwright install chromium` |
| 登录超时 | 重跑，或 `--headed` 手动登录一次 |
| 扫码后卡住 | 可能需要短信验证，在窗口内完成验证码输入 |
| 标题超长报错 | 压缩到 ≤30 字 |
| 发布失败 toast | 按 toast 文案排查（如违规词、图片不合规） |
| 点发布后一直「正在发布」、作品数不变 | **无头模式被反自动化拦截**。用 `--publish` 会自动切 headed；若仍卡，手动加 `--headed` 在可见窗口里发。成功标志＝跳转 `/content/manage` 或出现「发布成功」toast |
| 发布按钮点了没反应 | 该按钮 `position:fixed` 且在长表单底部，`scrollIntoViewIfNeeded()+.click()` 会落点错误；脚本已改为 JS `scrollIntoView({block:'center'})` + `mouse.click` 真实中心坐标 |
