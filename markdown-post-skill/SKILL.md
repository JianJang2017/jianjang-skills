---
name: markdown-post-skill
description: "把本地 Markdown 文章发布到内容平台（目前覆盖：稀土掘金 juejin.cn、讯飞内部的飞帆 feifan.iflytek.com）。统一通过 Playwright 接入用户已登录的 Chrome，自动开编辑器、写入标题正文、把正文里的本地图片上传到平台图床并替换链接、按 frontmatter 预填分类/标签/封面/摘要，默认存草稿等用户人工点发布。当用户说『把这篇 md/文章发到掘金 / 同步到稀土掘金 / 在掘金存个草稿 / 用 Playwright 发掘金 / 走 chrome 自动化把文章传到 juejin』，或说『发到飞帆 / 上传到 feifan / 同步到讯飞飞帆 / 把文章贴到 iflytek 飞帆』，或丢一个 .md 文件并提到 juejin/掘金/飞帆/feifan 时，使用本 skill。即使用户只说『发掘金』『发飞帆』没提图片，也用本 skill——本地图片自动上传到平台 CDN 是核心价值之一。不负责：写文章本身（让 LLM 直接出 md）、把 md 排成 HTML（走 markdown-to-html）、发到飞书知识库（走 markdown-to-feishu-skill）。"
metadata:
  requires:
    python: ">=3.9"
    pip: ["playwright>=1.40"]
    bins: ["playwright"]
  config: "图片上传走真实系统剪贴板 + 真实 ⌘V/Ctrl+V，所以脚本同时支持 macOS 与 Windows（Linux 暂未实现剪贴板分支）。优先复用已登录 Chrome（CDP 接入 localhost:9222）；连不上则自动回落到 Playwright 自带 chromium + 持久化独立 profile（首次需登录一次，cookies 落盘后长期复用）。Chrome 136+ 安全限制不允许对主 profile 启用远程调试，这种情况直接跑脚本即可，回落是默认行为。CDP 地址等可在 skill 根目录 .env 配（复制 .env.example）。"
---

# markdown-post-skill

把本地 Markdown（可能带本地图片）发布到内容平台。两个核心难点一次性解掉：

1. **登录态复用**：这些平台都没有开放 API，必须走浏览器；让用户每次重新登录/扫码很糟。本 skill 走 Playwright 的 `connect_over_cdp` 接入用户**已登录的 Chrome**，账号、cookie、SSO 全部继承。
2. **本地图片**：`![](./img/a.png)` 这种本地路径直接塞进编辑器，发布后图片**链不到**。本 skill 在写正文前先把每张本地图走平台自己的上传通道传到平台 CDN，把返回的 URL 替换回 markdown，再写入编辑器。

> 默认行为是**存草稿**——脚本写完正文、上传完图片、预填好元数据后就停下，把 URL 还给用户，由用户在浏览器里人工核对并点「发布」。要直接发布需显式加 `--publish`。这是有意为之：内容平台的发布是单向操作，让人最终把关一次值得。

## 平台选择

| 平台 | 入口 | 脚本 | 状态 |
|---|---|---|---|
| 稀土掘金 | https://juejin.cn | `scripts/publish_juejin.py` | 实测跑通（macOS / Windows） |
| 飞帆（讯飞内网） | https://feifan.iflytek.com/writeAnArticle | `scripts/publish_feifan.py` | 实测跑通（macOS） |

判断用户想发哪：用户说"掘金/juejin/稀土"→掘金；说"飞帆/feifan/讯飞"→飞帆；都没提就**问一次**，不要瞎猜（发错平台没法撤）。

## 开始前 —— 确认 Chrome 接入方式

> **平台支持**：脚本在 macOS 和 Windows 上跑通过；Linux 的剪贴板分支没实现（图片上传走系统剪贴板，Linux 需要 xclip/wl-copy，留给后续）。

本 skill 假定用户已经：

1. 用 `--remote-debugging-port=9222` 启动了一个 Chrome 实例（保留主 profile，登录态都在）—— **可选**，连不上脚本会自动回落到持久化独立 profile（首次需要登录一次）
2. 已在该浏览器登录目标平台（掘金 → juejin.cn 右上角有头像；飞帆 → SSO 登录后能进 writeAnArticle）

> **重要**：Chrome 136+ 出于安全考虑，禁止对默认 user-data-dir 启用 `--remote-debugging-port`——所以即使你用下面的命令带主 profile 启动，端口可能不监听。这种情况**直接跑脚本就行**——它会自动用 Playwright 自带的 chromium + 独立 profile 接入，首次登录一次后长期复用。

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome"

# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.config/google-chrome"
```

```powershell
# Windows PowerShell
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:LOCALAPPDATA\Google\Chrome\User Data"
```

> 在 Chrome 136+ 上用主 profile 启动时端口可能不监听（安全限制），脚本会无缝回落到独立 profile。
> 如果你想强制走 CDP，给 Chrome 换一个独立 user-data-dir（macOS `/tmp/chrome-post`、Windows `C:\temp\chrome-post`），首次在那个 Chrome 里登录目标平台一次即可。

CDP 地址默认 `http://localhost:9222`，可由 `.env` 的 `CDP_URL` 覆盖。

## 推荐：一键发布

### 掘金

```bash
python3 <skill>/scripts/publish_juejin.py <file>.md \
  [--title "覆盖 frontmatter 的标题"] \
  [--publish] \
  [--cdp-url http://localhost:9222] \
  [--draft-id <已有草稿id>]
```

### 飞帆

```bash
python3 <skill>/scripts/publish_feifan.py <file>.md \
  [--title "..."] \
  [--publish] \
  [--cdp-url http://localhost:9222]
```

成功后 stdout 是 JSON：

```json
{
  "platform": "juejin",
  "draft_url": "https://juejin.cn/editor/drafts/<id>",
  "article_url": null,            // --publish 模式下是文章 URL
  "title": "...",
  "images_uploaded": 3,
  "images_total": 3,
  "status": "draft" | "published",
  "notes": []
}
```

## 内部流程（理解原理才能排错）

两个脚本共享一套主流程，只在「平台特有的 DOM 选择器、上传响应过滤、保存/发布按钮」上有差异——共享部分在 `scripts/_common.py`，平台特定部分在各自脚本顶部的 `SELECTORS` dict。流程：

1. **解析 frontmatter**：从 md 顶部 YAML 取 `title/category/column/tags/cover/summary`；缺的字段从命令行参数补，再缺就用文件名/留空。
2. **扫本地图片**：正则匹配 `![alt](path)`，区分 `http(s)://` 和本地路径；缺失的本地图保留原引用并在 stderr 告警。
3. **接入 Chrome**：`browser_cdp.get_context()` 优先 `connect_over_cdp(CDP_URL)`；连不上就回落到 `launch_persistent_context(user_data_dir=~/.markdown-post-skill/chrome-profile)`。
4. **打开编辑器 + 登录态判定**：登录态判定用 URL 检查（被重定向到 passport/sso 就是没登录）而不是头像选择器（不可靠）。**不自动登录**——账号安全是底线。
5. **上传图片（剪贴板路径）**：合成 ClipboardEvent 没法带真实 File（`clipboardData` readonly），file input 也不通用——只有「真实系统剪贴板 + 真实 ⌘V/Ctrl+V」稳定。`_common.load_image_to_clipboard` 按 `sys.platform` 分发：macOS 用 osascript+sips（需先转 PNG），Windows 用 PowerShell + `System.Windows.Forms.Clipboard.SetImage`（STA 线程，EncodedCommand 传脚本，零依赖）。粘贴后轮询编辑器 markdown 内容，diff 出新增的 `![](url)` 里的 URL。
6. **写正文 + 标题**：`_common.write_into_editor` 优先用 CodeMirror 6 的 `view.dispatch({changes:...})` 整段替换（O(1)），大文本下比 `keyboard.insert_text` 快几个数量级——后者在 CM6 里逐字符触发 InputEvent 会卡死。CM6 找不到就回落到 keyboard 路径。
7. **平台分叉**：
   - **掘金**：等自动保存 → 草稿模式到此结束；`--publish` 才打开发布弹窗、选分类、加标签、传封面、填摘要、点确认发布。掘金的元数据**只在发布弹窗里生效**，草稿模式预填了点取消就丢，所以草稿模式不碰弹窗，把元数据回显给用户照填。
   - **飞帆**：默认是 TinyMCE 富文本编辑器，脚本启动后**先点「切换MD编辑器」**切到 CodeMirror 6 模式（栈和掘金一致，复用一套上传/写入逻辑）。草稿模式写完即结束（飞帆自动保存）；`--publish` 模式点「发布」触发**模板选择弹窗**（飞帆要求选模板进入发布流程），脚本不替用户选模板，输出 `status: awaiting_template_selection` 让用户在浏览器里完成最终发布。
8. **返回**：从当前 URL 解析草稿/文章 id，组装 JSON 打印到 stdout。

## 配置（.env）

```ini
CDP_URL=http://localhost:9222
JUEJIN_DEFAULT_CATEGORY=                # 可选：frontmatter 没写 category 时的掘金默认值
FEIFAN_DEFAULT_CATEGORY=                # 可选：飞帆默认分类
JUEJIN_TIMEOUT_MS=30000
FEIFAN_TIMEOUT_MS=30000
```

`.env` 已被仓库根 `.gitignore` 忽略。所有字段都可选。

## frontmatter 约定

```yaml
---
title: 在 Spring Boot 里用 RocketMQ 做事务消息
category: 后端                # 平台一级分类。掘金：后端/前端/Android/iOS/人工智能/开发工具/代码人生/阅读。飞帆：实测分类/标签都在「点发布」后的模板选择弹窗里（脚本不替用户选模板），frontmatter 写了也只会作为 notes 提示给用户照填，所以飞帆这里随便写或留空均可。
column: 后端深水区             # 可选，专栏名
tags: [Java, Spring Boot, RocketMQ, 微服务]  # 平台预设标签
cover: ./cover.png            # 封面：本地路径或 http(s):// URL，本地的会先上传
summary: 用 RocketMQ 4.5+ 的事务消息特性串联本地事务和下游消费。
---
```

- **title 必填**：没有就报错，用 `--title` 可以临时覆盖。
- **category 不匹配**：掘金脚本用 `inner_text` 包含匹配；找不到时告警并跳过分类预填，用户在浏览器里手选。
- **掘金 tags**：必须是掘金已有的预设；找不到匹配就丢弃该 tag 并告警，**不会自动创建**（掘金不允许）。
- **飞帆元数据**：实测飞帆的分类/标签/封面在「点发布」后的**模板选择弹窗**里，脚本不替用户选模板（不同模板跨频道/审核流程，错选不可撤）。frontmatter 里的 category/tags/summary 会在 `notes` 里回显，让用户人工填弹窗时照填。

## 关键约束

- **登录态**：本 skill 不做登录，依赖用户已登录的 Chrome。检测到未登录就停下，不要自动打开登录页或代填——账号安全是底线，**对内网 SSO 尤其重要**。
- **写操作前告知**：上传图片、写入正文、（可选的）正式发布都是写操作。批量执行前把计划（标题、图片张数、是否发布、目标平台）告诉用户。`--publish` 是高风险操作，必须用户在命令里显式带这个参数才会触发。
- **缺图不静默**：本地图片不存在或上传失败时，保留原 markdown 引用并在 stderr 告警；最终结果 `images_uploaded < images_total` 时显式告诉用户缺失清单，问补文件还是接受占位。
- **平台选错没法撤**：用户没明确说发哪个平台时，**问一次**再跑；发到错平台尤其是公司内网平台没法干净撤回。

## 失败与边界

- **「CDP 不可用，改用持久化 profile」**：这是正常日志不是错误。Chrome 136+ 不允许主 profile 启用远程调试，脚本无缝回落到独立 profile。首次会让用户登录一次。
- **未登录**：登录态判定用 URL 检查（被重定向到 passport/sso）。直接停，让用户在浏览器里登录后重跑。
- **图片上传 401/403**：cookie/session 失效，让用户在浏览器刷新一下目标平台主页重新激活后重跑。
- **图片上传 30s 没出新 URL**：剪贴板没真的拿到图。验证剪贴板内容（macOS `osascript -e 'clipboard info'`；Windows `[System.Windows.Forms.Clipboard]::ContainsImage()`）；确认编辑器 focus 成功。
- **CodeMirror 大文本卡死**：旧版 `keyboard.insert_text` 在 CM6 大正文下数分钟无响应，现已切到 `view.dispatch` 整段替换。如果用户报告"卡在写入正文那一步"，检查 `_common.write_into_editor` 是否找到了 CM6 实例（找不到会回落到 keyboard 路径）。
- **选择器找不到**（DOM 变了）：所有平台特定 selector 集中在 `scripts/publish_<platform>.py` 顶部的 `SELECTORS` dict。掘金参照 `references/juejin.md`；飞帆参照 `references/feifan.md`。
- **残留 chromium 进程占着 SingletonLock**：脚本启动后无任何输出、卡住。清理：macOS/Linux `pkill -9 -f ms-playwright && rm -f ~/.markdown-post-skill/chrome-profile/Singleton*`；Windows 见 `references/juejin.md`。
- **markdown 无图**：自动跳过图片上传，退化为「打开编辑器 + 写正文 + 保存」。
- **Linux 平台**：浏览器接入可用，但图片上传的剪贴板分支未实现（xclip / wl-copy 留 TODO）。

## 参考

- `references/juejin.md` — 掘金编辑器选择器、登录态判定、走过的弯路、典型报错与对策（含 macOS/Windows）
- `references/feifan.md` — 飞帆双编辑器模式切换、CodeMirror 6 dispatch 写入、上传 API、典型报错
- `scripts/_common.py` — 跨平台共享逻辑（Plan、扫图、剪贴板上传、CM6 写入、CDN URL 提取）
- `scripts/browser_cdp.py` — CDP 接入 + 持久化 profile 双模式自动回落
- `scripts/frontmatter.py` — 零依赖 YAML frontmatter 解析
