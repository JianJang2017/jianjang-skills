# Image Factory Skill

根据 prompt 生成 AI 图片，并通过飞书 CLI 发送给指定用户或群组。

## 能做什么

输入一句图片描述 → 自动生成图片 → 推送到飞书的人或群。图片、配文与生成 prompt 合成**一条**富文本消息，prompt 以可复制文本附在图下；多目标时图片只上传一次、并发发送。

```
"生成一张科技感的系统架构图，发给张三"
"给研发群发一张手绘风格的产品路线图，配文：Q2 规划草图"
"把 output/diagram.png 发给开发组和产品组"
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

## 文件结构

```
image-factory-skill/
├── SKILL.md                       # 技能定义与工作流
├── README.md
├── .env.example
├── scripts/
│   ├── generate-image.js          # 图片生成（codex / agy 双后端）
│   └── send_feishu_image.py       # 编排：生成 + 飞书推送
└── references/
    └── feishu-cli-guide.md        # 飞书 CLI 完整教程
```
