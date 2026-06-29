# 飞帆（feifan.iflytek.com）参考：实测验证版

**实测状态**：2026-06-29 验证通过。两个测试草稿都成功创建并写入了 4 张图。

## 一、平台架构（实测）

飞帆是讯飞内部技术社区，前端用 antd-react + 自家组件库（`css-elemcb` 前缀）。**编辑器有两套**：

1. **默认 TinyMCE**（富文本）—— 在 iframe `#tinymceEditor_ifr` 里
2. **MD 模式**（CodeMirror 6 / md-editor-v3）—— 在主页面 `.cm-editor`

本 skill **强制切到 MD 模式**——`open_editor` 第一件事就是点「切换MD编辑器」。原因：
- MD 模式下编辑器栈和掘金一致（CodeMirror 6），剪贴板上传方案 100% 复用
- 富文本模式要操作 TinyMCE iframe，注入 markdown 还要转 HTML，复杂得多

## 二、登录态

飞帆走讯飞 SSO，未登录时浏览器被重定向到 `https://sso.iflytek.com:8443/sso/login`。
脚本的 `_ensure_logged_in()` 检查 URL 含 `sso.iflytek` / `passport` / `/login` 就停止
并提示用户登录。**不要自动代填账号**——这是公司账号，账号安全是底线。

持久化 profile 在 `~/.markdown-post-skill/chrome-profile`，首次登录后 cookies 落盘，
之后可以长期复用。

## 三、关键选择器（已实测）

| 元素 | 选择器 | 备注 |
|---|---|---|
| MD 编辑器（切换后）| `.cm-editor` | CodeMirror 6；`.cm-content` 是 contenteditable 写入靶点 |
| 标题输入 | `input[placeholder='请输入标题']` | 顶部 ant-input；`maxlength=200` |
| 切换 MD/富文本 | `text=切换MD编辑器` / `text=切换富文本编辑器` | class 带 hash 后缀会变，**按文本找最稳** |
| 顶部发布按钮 | `.publishAnArticle___NKhGM`（class 带 hash） | 点击会弹模板选择，**不是直接发布** |
| 模板选择弹窗 | `[class*='templateModalArea']` / `[class*='templateModalList']` | 飞帆要求选模板才能发布；脚本不替用户做这个决定 |
| 预览按钮 | `.preview___NLfz7` | 不用 |
| 「发布/投递」 | `#publishButton_header` | 顶部导航的按钮，和正文区的「发布」是不同入口 |

## 四、图片上传通道（实测）

**API**：`POST https://feifan.iflytek.com/teclib-file-service/userApi/file/upload`
**响应**（实测）：
```json
{
  "code": 0,
  "msg": "SUCCESS",
  "data": {
    "key": "2026/6/29/.../657.png",
    "url": "/oss/2026/6/29/.../657.png",
    "src": "/oss/2026/6/29/.../657.png"
  },
  "requestId": "..."
}
```

注意 `url` 是**相对路径** `/oss/...`，不是绝对 URL——这一点和掘金（绝对 URL）不同。
脚本 `_common._MD_IMG_URL_RE` 已经放宽匹配，接受 `/` 开头的相对路径。

**上传触发方式**（两条都能用）：
1. **剪贴板 paste**（脚本默认走这条，和掘金统一）：把图片写进操作系统剪贴板（macOS 用 osascript，Windows 用 PowerShell `Clipboard.SetImage`，由 `_common.load_image_to_clipboard` 按 `sys.platform` 自动分发） → 编辑器 focus → 真实 ⌘V/Ctrl+V。
   编辑器自动插入 `![](/oss/.../x.png 'image.png')`。
2. **set_input_files**（备用）：飞帆的 MD 编辑器有两个 `accept=image/*` 的 file input
   （`.md-editor > input[type=file]` 和 `.md-editor-modal-body > input`），任一都能上传。
   暂未在脚本里用，留作 paste 失败时的兜底。

## 五、CodeMirror 6 写正文：用 dispatch，不要 insert_text

**实测教训**：飞帆 md-editor-v3 在 `keyboard.insert_text(7KB)` 时会卡死（CM6 逐字符
触发 InputEvent + markdown 重解析 + autosave，长文本下数分钟无响应）。

`_common.write_into_editor` 现在优先走 CM6 dispatch：
```js
const view = root._view || root.view || ...;
view.dispatch({changes: {from: 0, to: view.state.doc.length, insert: body}});
```
md-editor-v3 把 EditorView 挂在 `.cm-editor._view`（实测）。这是 O(1) 整段替换，
对掘金的 bytemd（也是 CM6）同样适用。找不到 `_view` 时回落到 `keyboard.insert_text`。

## 六、发布流程：脚本到草稿为止

`--publish` 模式下脚本只点「发布」按钮，触发模板选择弹窗。**不替用户选模板**——
不同模板对应不同频道/审核流程，错选不可撤回。所以输出会是：

```json
{"status": "awaiting_template_selection", "notes": [...]}
```

让用户在浏览器里选模板后人工完成最终发布。默认草稿模式（不带 `--publish`）则脚本
写完就结束，连发布按钮都不碰。

## 七、典型错误

| stderr 看到 | 原因 | 怎么办 |
|---|---|---|
| `飞帆未登录（被重定向到 SSO 登录页）` | cookies 失效或第一次跑 | 在浏览器里手动登录 |
| `既找不到「切换MD编辑器」也找不到 .cm-editor` | 飞帆 UI 改版 / SSO 没完全完成 | 在浏览器里手动等编辑器加载完，重跑 |
| `30s 内编辑器没出现新图片 URL` | paste 触发但响应字段名变了 | 在浏览器 DevTools 抓 `file/upload` 看响应——若 `data.url` 改名了，更新 `_common._MD_IMG_URL_RE` |
| 脚本卡在「上传完图片之后」5+ 分钟 | `write_into_editor` 退化到 `keyboard.insert_text` 路径 + 大文本 | 用 v6 诊断脚本检查 `.cm-editor._view` 字段名，更新 `_common.write_into_editor` 里的字段探测列表 |

## 八、走过的弯路（别再试）

- ~~工具栏 file input + set_input_files~~：飞帆默认 TinyMCE 模式下 DOM 完全不同，
  转 MD 模式后 set_input_files 也能跑通但不如 paste 通用
- ~~监听响应的 host 白名单~~：飞帆 host = `feifan.iflytek.com` 本身，不需要 CDN host 过滤
- ~~`keyboard.insert_text` 写大正文~~：CM6 + 飞帆 md-editor-v3 下会卡死，必须用 dispatch
