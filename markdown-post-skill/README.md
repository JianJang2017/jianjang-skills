# markdown-post-skill

把本地 Markdown 文章发布到内容平台。目前覆盖：

| 平台 | 入口 | 脚本 | 状态 |
|---|---|---|---|
| 稀土掘金 | https://juejin.cn | `scripts/publish_juejin.py` | 实测跑通（macOS / Windows） |
| 飞帆（讯飞内网） | https://feifan.iflytek.com/writeAnArticle | `scripts/publish_feifan.py` | 实测跑通（macOS） |

详细工作流见 [SKILL.md](./SKILL.md)。

## 快速开始

```bash
# 1. 安装依赖（一次性）
pip install -r scripts/requirements.txt
playwright install chromium

# 2. 直接跑——首次会弹出独立 Chromium 让你登录目标平台，cookies 落盘后长期复用
python3 scripts/publish_juejin.py path/to/article.md
# 或
python3 scripts/publish_feifan.py path/to/article.md

# 直接发布（不存草稿）加 --publish
python3 scripts/publish_juejin.py path/to/article.md --publish

# （可选）复制 .env 自定义 CDP 地址、默认分类、超时等
cp .env.example .env
```

### 关于浏览器：默认走持久化独立 profile

脚本默认行为：用 Playwright 自带的 chromium + 独立持久化 profile（`~/.markdown-post-skill/chrome-profile`），首次需要登录一次，之后长期复用。**不需要你启动任何东西**，跑就行。

如果你想让脚本接入**你已经登录好的 Chrome**（CDP 模式，省一次登录），可以这样启动 Chrome：

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome"
```

```powershell
# Windows PowerShell
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:LOCALAPPDATA\Google\Chrome\User Data"
```

> **Chrome 136+ 限制**：用主 profile 启动时远程调试端口可能不监听（Chrome 安全限制）。这种情况脚本会自动回落到独立 profile 模式——无感知。如果你**真的想强制 CDP**，给 Chrome 换一个独立 `--user-data-dir`（macOS `/tmp/chrome-post`、Windows `C:\temp\chrome-post`）首次登录一次即可。

### 平台支持

| OS | 状态 |
|---|---|
| macOS | ✅ 实测 |
| Windows 10/11 | ✅ 实测命令构造单测；剪贴板走 PowerShell `Clipboard.SetImage` |
| Linux | ⚠️ 浏览器接入可用，但图片上传的剪贴板分支未实现（xclip/wl-copy 留 TODO） |

## frontmatter 示例

```yaml
---
title: 在 Spring Boot 里用 RocketMQ 做事务消息
category: 后端
column: 后端深水区
tags: [Java, Spring Boot, RocketMQ, 微服务]
cover: ./cover.png
summary: 用 RocketMQ 4.5+ 的事务消息特性串联本地事务和下游消费。
---

# 正文...
```

## 设计取舍

- **图片上传走真实剪贴板**：合成 ClipboardEvent / file input 在掘金和飞帆都不通，只有「系统剪贴板 + 真实键事件」模拟人类粘贴最稳。macOS 走 osascript+sips，Windows 走 PowerShell `Clipboard.SetImage`——`_common.load_image_to_clipboard` 自动按 `sys.platform` 分发。
- **浏览器接入自动回落**：CDP 优先（如果用户启了远程调试端口），否则用持久化独立 profile，体验差不多。
- **默认存草稿**：发布是单向操作，最后让用户在浏览器里核对一次再点发布。要直接发用 `--publish`。
- **跨平台共享 + 平台特化**：通用逻辑在 `_common.py`，每个平台一个 `publish_<name>.py`，选择器集中在脚本顶部的 `SELECTORS` dict 和 `references/<name>.md`。加新平台照葫芦画瓢。
