# Image Factory Skill

根据 prompt 生成 AI 图片，并**通过飞书 CLI 发送给用户/群组**，或**发布为小红书图文笔记**，或**发布为抖音图文**；也支持**从图片反推 prompt**、**优化 prompt**（含风格预设）、**从主体描述生成人物图 prompt**（主体一句话 + 风格预设 → 结构化单人写真 prompt，含镜头/光照/画质/负面提示）。

## 能做什么

**正向**：输入一句图片描述 → 自动生成图片 → 三条输出通道任选：

- **飞书**：推送到飞书的人或群。图片、配文与生成 prompt 合成**一条**富文本消息，prompt 以可复制文本附在图下；多目标时图片只上传一次、并发发送。
- **小红书**：把图片 + 标题/正文/话题发布为图文笔记。默认**停在「发布」按钮**等你人工确认（防误发），加 `--publish` 才自动发布。
- **抖音**：把图片 + 标题/简介发布为图文。同样默认**停在「发布」按钮**，加 `--publish` 才自动发布。

**反向**：

- **反推 prompt**：丢一张图给 `scripts/reverse-prompt.js`，自动反推出"用文生图模型最可能生成它的那条 prompt"，按 `[Style] + [Type] + [Content] + [Key elements]` 结构输出，可归档到 `prompts/`。支持 `--ignore-ui`（默认 ON，屏蔽 App/系统 UI 元素）和 `--keep-ui`（截图复刻场景保留 UI）。
- **优化 prompt**：`scripts/optimize-prompt.js` 把一段粗 prompt 按结构改写，支持 10 种风格预设（hand-drawn / blueprint / watercolor / cyberpunk / 3d / healing / minimal / photo / gufeng-portrait / photo-portrait），也支持 `keep`（保留原风格）。
- **生成人物图 prompt**：`scripts/generate-portrait-prompt.js` 从"一句话主体描述 + 风格预设"生成一条开箱即生图的单人人物图 prompt（含 [Style][Type][Content][Key elements] + 镜头/光照/画质词/负面提示），省去手写镜头/光照/画质词的麻烦。默认古风宫廷写真风（gufeng-portrait，从 `images/` 下四张「古代女子妆容」海报反推沉淀），也支持 photo-portrait（写实人像摄影）。

三者都跑在同样的 codex/agy 后端，无新依赖。可串联：`reverse | optimize | generate-image | send/publish` 或 `generate-portrait-prompt | generate-image | publish`。

```
"生成一张科技感的系统架构图，发给张三"
"给研发群发一张手绘风格的产品路线图，配文：Q2 规划草图"
"把 output/diagram.png 发给开发组和产品组"
"把这张图发一篇小红书笔记，标题 XX，正文 XX"
"生成一张赛博朋克城市夜景，发一篇抖音图文"
"这张图是怎么 prompt 出来的？"          # → reverse-prompt
"把这条 prompt 改成蓝图风"               # → optimize-prompt --style blueprint
"生成人物图 prompt：雪中红衣女子回眸"    # → generate-portrait-prompt（新）
```

## 快速开始

### 1. 安装依赖

```bash
# 图片生成后端（二选一）
npm install -g codex-cli          # 或访问 https://openai.com/codex
# 或 agy (Antigravity CLI): https://antigravity.google/docs/cli-getting-started

# 飞书 CLI
npx @larksuite/cli@latest install
lark-cli auth login
```

### 2. 配置接收人

复制 `.env.example` 为 `.env` 并填入你的接收人：

```bash
cp .env.example .env
```

```env
FEISHU_USER_IDS=ou_xxx,ou_yyy   # 用户 open_id
FEISHU_CHAT_IDS=oc_xxx          # 群聊 chat_id
FEISHU_SEND_AS=bot              # bot（推荐）| user
```

获取 ID：

```bash
lark-cli contact +search-user --query "张三"   # 查用户 open_id
lark-cli im +chat-list                         # 列出群聊 chat_id
lark-cli auth status                           # 查自己的 open_id
```

### 3. 使用

```bash
# 生成并发送（接收人读 .env）
python scripts/send_feishu_image.py --prompt "一张科技感的系统架构图"

# 指定接收人 + 配文
python scripts/send_feishu_image.py \
    --prompt "手绘风格的部署流程图" \
    --user-ids "ou_aaa,ou_bbb" \
    --chat-ids "oc_xxx" \
    --caption "Q2 部署架构草图"

# 发送已有图片（跳过生成）
python scripts/send_feishu_image.py --image output/diagram.png --user-ids "ou_aaa"

# 预览模式（不实际发送）
python scripts/send_feishu_image.py --prompt "测试图" --dry-run
```

## 参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `--prompt` | 图片生成提示词（与 `--image` 二选一） | - |
| `--image` | 已有图片路径（提供则跳过生成） | - |
| `--user-ids` | 接收用户 open_id，逗号分隔 | 读 `.env` |
| `--chat-ids` | 接收群聊 chat_id，逗号分隔 | 读 `.env` |
| `--caption` | 图片消息的标题行 | 🎨 AI 生成图片 |
| `--no-prompt-caption` | 不把生成 prompt 作为可复制文本附在消息里 | 否 |
| `--aspect-ratio` | 图片宽高比 | 16:9 |
| `--provider` | 生成后端：auto / codex / gemini | auto |
| `--as` | 发送身份：bot / user | 读 `.env`（缺省 bot） |
| `--dry-run` | 预览，不实际发送 | 否 |

## 常见报错

| 报错 | 原因 | 解法 |
|------|------|------|
| `230002: ...out of the chat` | 机器人不在群里 | 群设置 → 群机器人 → 添加机器人 |
| `im:resource` / `uploading image` | user 身份没有图片上传权限 | 改用 `--as bot`（发图最稳），或重新授权加 `im:resource:upload im:resource` |
| `missing scope: im:message.send_as_user` | user 身份缺发送权限 | 改用 `--as bot`，或开通权限后重新登录 |
| `No image generation backend` | 没装生成后端 | 安装 codex-cli 或 agy |

> 💡 **发图建议用 `--as bot`**：发图比发文本多需要上传权限，bot 身份默认就有。即使 `.env` 配的是 `user`，遇到上传权限报错就切到 bot。

更多见 `references/feishu-cli-guide.md`。

## 发布到小红书

把图片 + 标题/正文/话题发布为小红书图文笔记。基于 Playwright 独立 Chromium，**首次扫码登录、后续免登**。

### 1. 一次性准备

```bash
npm install            # 装 playwright 依赖
npm run setup:xhs      # = playwright install chromium，装浏览器内核
```

### 2. 发布

```bash
# 一条龙：只给 prompt → 自动生图 → 归档 prompt → 推导标题/正文 → 停在发布按钮
node scripts/publish_xiaohongshu.js \
    --prompt "赛博朋克风格的城市夜景，霓虹灯牌林立" \
    --topics "AI,赛博朋克"

# 全自动：给已有图 + 生图用的 prompt 文件，标题/正文自动推导
node scripts/publish_xiaohongshu.js \
    --image cover.png \
    --prompt-file prompts/20260628-01.md \
    --topics "AI,效率工具"

# 默认：填好内容后停在「发布」按钮，截图，等你人工确认（推荐，防误发）
node scripts/publish_xiaohongshu.js \
    --image cover.png \
    --title "我用AI做了张图" \
    --content "今天试了下AI生图，效果不错…" \
    --topics "AI,效率工具"

# 多图 + 正文从文件读 + 自动发布（显式 opt-in）
node scripts/publish_xiaohongshu.js \
    --image a.png,b.png --title "三图测评" --content-file body.md --publish

# 预览参数（不启动浏览器/不生图）
node scripts/publish_xiaohongshu.js --prompt "水彩风格的猫" --dry-run
```

**一条龙生成即发布**：不给 `--image`、只给 `--prompt`，脚本会先调 `generate-image.js` 生图（`--provider`/`--aspect-ratio` 默认 `auto`/`3:4`），归档 prompt，再走发布流程。

**标题/正文可自动推导**：缺省的标题按**图片画风**生成（手绘/水彩/科技感/治愈/赛博朋克/3D…），缺省的正文取 **prompt 精简版**（去掉「画一张…」指令套话和「高清渲染」等技术词）。显式 `--title`/`--content` 永远优先。先用 `--dry-run` 预览，输出会标注每项来源。

**首次运行**会弹出浏览器窗口让你扫码登录，登录态持久化到 `~/.image-factory-skill/xhs-profile`，之后免扫码。

> ⚠️ **默认不自动发布**：脚本填好封面/标题/正文/话题后停在「发布」按钮并截图，由你人工点发布。加 `--publish` 才自动点击。标题强校验 ≤20 字。

小红书参数与 selector 维护见 `references/xiaohongshu-publish-guide.md`。

## 发布到抖音

把图片 + 标题/简介发布为抖音图文。架构与小红书通道一致：Playwright 持久化登录，**首次扫码、后续免登**。

### 1. 一次性准备

```bash
npm install              # 装 playwright 依赖
npm run setup:douyin     # = playwright install chromium（与小红书共用内核）
```

### 2. 发布

```bash
# 一条龙：只给 prompt → 生图 → 推导标题/简介 → 停在发布按钮
node scripts/publish_douyin.js --prompt "赛博朋克风格的城市夜景" --topics "AI,夜景"

# 已有图 + 显式文案
node scripts/publish_douyin.js \
    --image cover.png --title "我的标题" --content "简介正文" --topics "AI"

# 多图 + 简介从文件读 + 自动发布
node scripts/publish_douyin.js \
    --image a.png,b.png --title "三图" --content-file body.md --publish

# 预览（不启动浏览器/不生图）
node scripts/publish_douyin.js --prompt "水彩风格的猫" --dry-run
```

**与小红书的区别**：标题上限 **30 字**（小红书 20）；抖音无独立话题下拉，`--topics` 作为 `#话题` 追加到简介末尾；登录态目录默认 `~/.image-factory-skill/douyin-profile`。标题/简介自动推导逻辑两者一致。

> ⚠️ **默认不自动发布**：同样停在「发布」按钮并截图，加 `--publish` 才自动点击。首次运行弹窗扫码登录（如需短信验证在窗口内完成）。

抖音参数与 selector 维护见 `references/douyin-publish-guide.md`。

## 文件结构

```
image-factory-skill/
├── SKILL.md                       # 技能定义与工作流
├── README.md
├── package.json                   # playwright 依赖 + setup 脚本
├── .env.example
├── scripts/
│   ├── generate-image.js          # 图片生成（codex / agy 双后端）
│   ├── send_feishu_image.py       # 编排：生成 + 飞书推送
│   ├── publish_xiaohongshu.js     # 发布到小红书（Playwright）
│   └── publish_douyin.js          # 发布到抖音（Playwright）
└── references/
    ├── feishu-cli-guide.md        # 飞书 CLI 完整教程
    ├── xiaohongshu-publish-guide.md  # 小红书发布 SOP + selector 维护
    └── douyin-publish-guide.md    # 抖音发布 SOP + selector 维护
```

## 致谢

小红书与抖音两条发布通道的发布流程与稳定性经验，参考并致谢以下两个开源技能：

- **小红书**：[xiaohongshu-ops-skill](https://github.com/Xiangyu-CAS/xiaohongshu-ops-skill) — 提供了小红书图文发布 SOP 与运行稳定性规则。
- **抖音**：[douyin-upload-mcp-skill](https://github.com/WJZ-P/douyin-upload-mcp-skill) — 提供了抖音创作者平台图文发布流程与页面元素定位思路。

本技能在二者基础上，统一改用 Playwright 持久化上下文重新实现，并接入图片生成与「停在发布按钮」的安全发布模型。感谢上述项目作者的开源贡献。
