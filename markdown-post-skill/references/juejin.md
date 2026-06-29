# 掘金编辑器参考：选择器、登录态、典型报错

DOM 变化时，把 `scripts/publish_juejin.py` 顶部的 `SELECTORS` 改一下基本就能跑通。这里记录每个选择器对应的 UI、备选写法和兜底逻辑。

## 〇、浏览器接入：CDP vs 持久化 profile（实测重要）

**Chrome 136+ 禁止对默认用户数据目录开启 `--remote-debugging-port`**（安全限制）。所以「用主 profile 起 Chrome + CDP 接入」这条路在新版 Chrome 上**根本连不上端口**——`curl localhost:9222` 永远超时，不是配置问题。

脚本的 `browser_cdp.get_context()` 因此做了自动回落：CDP 端口能连上就用 CDP，连不上就用 Playwright 自己的 chromium + 独立持久化 profile（`~/.markdown-post-skill/chrome-profile`）。首次跑要在弹出的窗口里登录一次掘金，cookies 落盘后长期复用。**实际绝大多数用户走的是持久化 profile 这条路。**

> 残留进程坑：脚本中断后 chromium 进程可能没死透，留下 `SingletonLock` 阻塞下次启动（表现为脚本卡在启动阶段无输出）。清理：
>
> ```bash
> # macOS / Linux
> pkill -9 -f ms-playwright && rm -f ~/.markdown-post-skill/chrome-profile/Singleton*
> ```
>
> ```powershell
> # Windows PowerShell
> Get-Process | Where-Object {$_.Path -like '*ms-playwright*'} | Stop-Process -Force
> Remove-Item "$env:USERPROFILE\.markdown-post-skill\chrome-profile\Singleton*" -Force -ErrorAction SilentlyContinue
> ```

## 一、登录态判定（实测：不要用头像选择器）

~~旧做法：goto 主页，看 `.avatar` 是否出现。~~ **这个判据不可靠**——掘金新版主页未登录态也有 `.avatar` 类元素（推荐用户头像等），会误判成已登录。

**可靠判据**：直接 goto 编辑器 `https://juejin.cn/editor/drafts/new?v=2`，看最终 URL——被重定向到 `passport.juejin.cn` / 含 `login` 就是未登录；停在 editor 且 `title === "写文章 - 掘金"`、`.cm-editor` 挂上了，就是已登录。脚本的 `_ensure_logged_in()` 在 `open_editor()` **之后**调用，正是检查这个最终 URL。

**不要自动跳登录页代填**——账号安全是底线。

## 二、编辑器 DOM

掘金当前编辑器是 [bytemd](https://github.com/bytedance/bytemd) 派生，底层是 CodeMirror 6。

| 元素 | 选择器 | 备注 |
|---|---|---|
| 标题输入 | `input.title-input` / `textarea.title-input` | 上方那条，直接 `fill()` 即可 |
| CodeMirror 容器 | `.bytemd .CodeMirror` / `.bytemd-editor .cm-editor` / `.cm-editor` | 三种历史命名 |
| CM 写入靶点 | `.cm-content` / `.bytemd .CodeMirror textarea` | **不能** `fill()`；只能 `keyboard.insert_text` 或剪贴板 paste |
| 自动保存状态 | `.save-status` / `.draft-status` / `:text('已保存')` | 等到「已保存」出现再走下一步；超 6s 兜底 Ctrl+S |

**实测：掘金新版正文图片没有工具栏 file input。** 用诊断脚本 dump 编辑器 DOM，整页只有两个 `input[type=file]`：
- `.coverselector_container input` —— **封面图**上传
- `.article-importer .file-input` —— **整篇 markdown 导入**

正文图片**只能靠 paste/drop 事件**触发（见 section 三）。所以旧文档里「点工具栏图片按钮 → hidden input → set_input_files」那条路在新版完全不存在，别再找它了。`window.bytemd` 之类的全局实例也没暴露上传钩子。

### 为什么不能用 `fill()` 写正文

CodeMirror 6 的 `.cm-content` 是 `contenteditable=true`，但内部用 `cm-line` 包每行，`fill()` 直接 set 整段 innerText 会导致 CM 内部 doc 状态和 DOM 不同步，刷新一下正文全没。

正确做法：先 click 让光标落在 CM 内 → Ctrl+A 全选 → Delete 清空 → `keyboard.insert_text(body)`。`insert_text` 触发的是底层 InputEvent，CM 能正确接收。

## 三、图片上传流程（实测：真实系统剪贴板 + 真实 ⌘V/Ctrl+V）

掘金新版正文图片**只接受 paste/drop 事件**，没有可 `set_input_files` 的 file input。能稳定跑通的唯一方法是模拟人类粘贴：

1. 把图片放进**真实操作系统剪贴板**：
   - **macOS**：`osascript -e 'set the clipboard to (read (POSIX file "x.png") as «class PNGf»)'`。`«class PNGf»` 只认 PNG，非 PNG 先用 `sips -s format png` 转。
   - **Windows**：PowerShell `Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile($p))`。System.Drawing.Image 直接支持 PNG/JPG/GIF/BMP/TIFF，不用先转格式。**必须用 STA 线程**（`powershell.exe -Sta`）。
   - 脚本通过 `subprocess.run` 调上述命令；按 `sys.platform` 自动分发。
2. `page.locator(editor_cm).click()` focus 编辑器，`⌘/Ctrl+End` 把光标移到文末。
3. 发**真实的** `page.keyboard.press("Meta+v")`（macOS）/ `"Control+v"`（Windows）。Chromium 读真实系统剪贴板，掘金的 paste handler 正常触发、走它自己的上传管道。
4. 轮询编辑器 markdown（`_get_editor_markdown` 读 CodeMirror 内容），diff 出新插入的 `![](cdn_url)` 里的 URL。
5. 上传成功后，正文里这张图已经在编辑器里了；脚本最后整段重写正文时用这个 CDN URL 替换原本地路径。

> Linux 暂未实现（可参考 `xclip -selection clipboard -t image/png -i x.png` 或 `wl-copy` 思路）。

### 走过的弯路（别再试这些）

按时间顺序试了 4 种，全失败——记下来免得重蹈覆辙：

| 方法 | 失败原因 |
|---|---|
| `expect_response` + host 白名单抓上传响应 | 掘金 CDN host / API 路径多变，过滤器抓不到 |
| 工具栏图片按钮 → hidden `input[type=file]` → `set_input_files` | **新版正文图片根本没有这个 input**（只有封面图和整篇导入两个 file input） |
| JS 里 `new ClipboardEvent('paste', {clipboardData: dt})` 合成派发 | `clipboardData` 是 readonly，合成事件带不动真实 File，编辑器收不到 |
| 封面图 file input 通道 `set_input_files` | 上传的是封面、且没稳定抓到响应 |

教训：**掘金这类编辑器，模拟真实用户操作（系统剪贴板 + 真实键事件）比任何"绕进内部 API"的取巧都稳。**

### 上传失败排查

- **30s 内编辑器没出现新 URL**：paste 没生效。先验证剪贴板真的有图：
  - **macOS**：`osascript -e 'clipboard info'`，输出应列出 `«class PNGf»`
  - **Windows PowerShell**：`Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::ContainsImage()`，应返回 `True`
  
  然后确认编辑器 focus 成功（用户在浏览器里能看到光标在 `.cm-editor` 内）。
- **401/403**：cookie 失效。让用户刷新一次 juejin 主页重新激活 session 后重跑。
- **413 / size too large**：掘金单图限 5MB；提示用户压一下图。

## 四、发布弹窗

点顶部「发布」后弹出，里面：

| 字段 | 选择器 | 注意事项 |
|---|---|---|
| 分类（单选） | `.category-list label` / `.category-select .item` | 必选，不选发不出去；脚本按 `inner_text` 包含匹配 |
| 标签（多选） | `input[placeholder*='标签']` + `.byte-select-dropdown .byte-select-option` | 标签必须是掘金已有的预设；脚本输入后从下拉选第一个匹配项；没匹配就跳过并告警 |
| 摘要 | `textarea[placeholder*='摘要']` | 可空；填了搜索结果会更完整 |
| 封面 | 弹窗内另一个 `input[type='file']` | 取 `last`，弹窗里它通常排在编辑器图片 input 之后 |
| 确认发布 | `.publish-popup button:has-text('确认')` / `button:has-text('确认并发布')` | 历史上文案改过几次 |
| 取消 | `button:has-text('取消')` | 取消后回到编辑器，草稿仍在 |

### 分类名（截至 2026 年中）

后端 / 前端 / Android / iOS / 人工智能 / 开发工具 / 代码人生 / 阅读

frontmatter 里 `category: 后端`、`category: AI`（会 fuzzy 匹配「人工智能」）都行。

### 标签不允许自创

普通用户在发布弹窗里**不能**新建标签——只能从预设列表里挑。frontmatter 里写了未收录的标签时，脚本会跳过并告警，让用户手动在浏览器里挑近似的。

## 五、典型错误信号

| stderr 上看到 | 原因 | 怎么办 |
|---|---|---|
| `CDP 不可用 ... 改用持久化 profile 模式` | Chrome 136+ 安全限制，主 profile 不接受远程调试 | 正常现象，脚本会自动用独立 profile；首次跑要扫码登录 |
| `掘金未登录（被重定向到登录页）` | 持久化 profile 里 cookies 失效 / 没登录 | 在弹出的浏览器里登录后重跑 |
| `30s 内编辑器没出现新图片 URL` | paste 没生效 | 看 section 三排查；最常见是 chromium 残留进程导致焦点不在编辑器 |
| `分类 'XXX' 没匹配到` | frontmatter 写错 / 掘金改了分类名 | 用户在弹窗里手选；或修 frontmatter |
| `标签 'XXX' 不在掘金预设里` | 自创了标签 | 改成预设标签，或在浏览器里手挑近似 |
| `images_uploaded < images_total` | 部分图上传失败 | 看 stderr 哪几张失败；图>5MB 先压；重跑通常就过 |
| `点了确认发布但 URL 没跳到文章页` | 弹窗里有未填项（分类/封面） | 在浏览器里看哪个红框，补完手动点发布 |
| 脚本启动后无任何输出、卡住 | 上一次脚本中断留下的 chromium 进程占着 SingletonLock | macOS/Linux: `pkill -9 -f ms-playwright && rm -f ~/.markdown-post-skill/chrome-profile/Singleton*` ; Windows: 见本文件顶部「〇、浏览器接入」章节 |

## 六、保留草稿，不要自动重发

脚本默认是「存草稿不发」。这是有意为之的设计选择：

- 文章发布是单向的；改文章只能编辑，删了重发会丢评论/点赞
- 让用户在浏览器里**最后核对一次**（特别是分类、标签、封面）再点发布最稳

要直接发布的，命令里必须显式带 `--publish`。
