# 图片生成 + 飞书推送 基础教程

本教程讲解如何从一句 prompt 出发，生成 AI 图片并通过飞书 CLI 推送到指定的人或群。
内容来自实战，包含图片发送区别于文本发送的关键坑点。文本消息的通用基础请先看
[feishu-cli-guide.md](./feishu-cli-guide.md)，本篇只讲「图片」这条链路。

---

## 1. 这个技能做什么

一条链路三步走：

```
一句图片描述  →  调本地模型生成图片  →  通过 lark-cli 推送到飞书
```

- **生成**：调用 `generate-image.js`，支持 codex 与 gemini(agy) 两个后端
- **发送**：调用 `lark-cli`，图片 + 配文 + 可复制 prompt 合成**一条**富文本消息
- **多目标**：图片只上传一次，并发发给所有用户/群

---

## 2. 准备工作

### 2.1 图片生成后端（二选一即可）

| 后端 | 命令 | 安装/文档 |
|------|------|-----------|
| **codex** | `codex` | OpenAI Codex CLI |
| **gemini** | `agy` | Antigravity CLI |

验证是否就绪：

```bash
which codex   # codex 后端
which agy     # gemini 后端
```

两个都装了就用 `--provider auto`（默认），脚本自动挑可用的。

### 2.2 飞书 CLI

```bash
npx @larksuite/cli@latest install   # 安装后命令为 lark-cli
lark-cli auth status                # 确认已登录
```

详见 [feishu-cli-guide.md](./feishu-cli-guide.md) 第 2、3 节。

### 2.3 接收人配置（`.env`）

```env
# 接收用户 open_id，多个逗号分隔
FEISHU_USER_IDS=ou_aaa,ou_bbb
# 接收群聊 chat_id，多个逗号分隔
FEISHU_CHAT_IDS=oc_xxx
# 发送身份：图片务必用 bot（见第 5 节）
FEISHU_SEND_AS=bot
```

---

## 3. 最快上手

```bash
# 生成并发送（接收人读 .env）
python scripts/send_feishu_image.py --prompt "一张科技感的系统架构图"

# 指定接收人 + 竖版 + 标题
python scripts/send_feishu_image.py \
    --prompt "古风仙侠人物写真，临水水榭" \
    --aspect-ratio "9:16" \
    --chat-ids "oc_xxx" \
    --caption "🎴 古风写真"

# 指定生成后端
python scripts/send_feishu_image.py --prompt "雨夜玻璃花房肖像" --provider gemini

# 发送已有图片（跳过生成）
python scripts/send_feishu_image.py --image output/diagram.png --user-ids "ou_aaa"

# 预览模式（不实际发送，仍会校验权限）
python scripts/send_feishu_image.py --prompt "测试图" --dry-run
```

---

## 4. 图片生成：两个后端

脚本内部调用 `generate-image.js`：

```bash
node scripts/generate-image.js \
  --prompt-file prompt.md \
  --output out.png \
  --aspect-ratio 9:16 \
  --provider auto      # auto | codex | gemini
```

- **codex**：把图写进 `~/.codex/generated_images/<session>/`，再复制到 `--output`
- **gemini(agy)**：把图写进会话产物目录，脚本从 stdout 解析路径后复制

> ⚠️ **生成是整条链路最慢的一环**（图片模型本身要跑几分钟），这部分快不了。
> 发送侧已经优化到秒级，瓶颈始终在模型推理。建议把生成命令放到**后台任务**跑，
> 别在前台干等。

> 💡 **codex 兜底**：codex 在沙箱里"自己复制到 output"可能失败，或生成耗时触发超时——
> 但原图通常已落盘。脚本会扫描 `~/.codex/generated_images/` 捞回本次刚生成的图，
> 不让结果白白丢掉。

---

## 5. 发送图片：和发文本不一样

这是本技能最关键的一节。**图片发送 ≠ 文本发送**，权限和路径都有坑。

### 5.1 图片身份必须用 bot

| 操作 | 需要的权限 | 说明 |
|------|-----------|------|
| 发文本 | `im:message.send_as_user`（user 身份） | user 可发文本 |
| **上传图片** | `im:resource:upload` + `im:resource` | 这两个权限 **bot 默认就有** |

实战结论：**图片一律用 `--as bot`**。即便 `.env` 配了 `FEISHU_SEND_AS=user`，
碰到 `im:resource` / `99991679` 这类报错就退回 bot。脚本默认就是 bot。

### 5.2 lark-cli 拒绝绝对路径

`--image` 不接受绝对路径，也不接受 `..`。脚本的解法：

```python
image_dir  = os.path.dirname(os.path.abspath(image_path))
image_name = os.path.basename(image_path)
# 切到图片所在目录，只传文件名
subprocess.run(["lark-cli", "im", "images", "create", ...,
                "--file", f"image={image_name}"], cwd=image_dir)
```

### 5.3 上传一次，复用 image_key

直接对每个目标都传一遍 `--image 本地图` 会**重复上传**（N 个目标传 N 次）。
正确做法是先上传一次拿到 `image_key`，再复用：

```bash
# 1) 上传一次（bot-only 接口）
lark-cli im images create --as bot \
  --data '{"image_type":"message"}' \
  --file image=pic.png
# → { "data": { "image_key": "img_v3_xxx" } }

# 2) image_key 复用到所有目标
lark-cli im +messages-send --as bot --chat-id oc_xxx \
  --msg-type post --content '<见 5.4>'
```

### 5.4 图 + 配文 + 可复制 prompt 合一

用 `post` 富文本把图片、标题、prompt 放进**一条**消息。`post` 的文本默认
可选中复制，用户长按即可拷走 prompt：

```json
{
  "zh_cn": {
    "title": "🎨 AI 生成图片",
    "content": [
      [{ "tag": "img",  "image_key": "img_v3_xxx" }],
      [{ "tag": "text", "text": "📝 Prompt: 一只赛博朋克风格的猫" }]
    ]
  }
}
```

> Feishu 消息 API 没有原生「折叠/收缩」文本元素，所以做不到真折叠；
> 可复制文本是目前最实用的方案。若一定要折叠，需改用 interactive 卡片
> 的折叠面板组件，成本更高。

---

## 6. 高频报错与解法

文本相关错误见 [feishu-cli-guide.md](./feishu-cli-guide.md) 第 6 节，这里只列图片特有的。

### 6.1 `99991679` / `missing scope: im:resource:upload`

**原因**：用 user 身份上传图片，缺上传权限。
**解法**：改用 `--as bot`。bot 默认有上传权限，这是最稳的路径。

### 6.2 `absolute paths and .. are rejected`

**原因**：`--image` / `--file` 传了绝对路径或含 `..`。
**解法**：切到图片所在目录、只传文件名（脚本已用 `cwd` 处理，见 5.2）。

### 6.3 codex 生成成功但报 "Operation not permitted" / 超时

**原因**：codex 在沙箱里复制图片到目标目录失败，或生成耗时触发 5 分钟超时。
**解法**：脚本的兜底逻辑会从 `~/.codex/generated_images/` 捞回原图（见第 4 节）。
一般无需手动干预。

### 6.4 `230002: Bot/User can NOT be out of the chat`

**原因**：机器人不在目标群里。
**解法**：把对应应用的机器人手动加进群（见 feishu-cli-guide.md 6.1）。重试无效。

---

## 7. 命令行参数速查

| 参数 | 说明 | 默认 |
|------|------|------|
| `--prompt` | 图片生成提示词（与 `--image` 二选一） | - |
| `--image` | 已有图片路径（提供则跳过生成） | - |
| `--user-ids` | 接收用户 open_id，逗号分隔 | 读 `.env` |
| `--chat-ids` | 接收群聊 chat_id，逗号分隔 | 读 `.env` |
| `--caption` | 图片消息的标题行 | 🎨 AI 生成图片 |
| `--no-prompt-caption` | 不把 prompt 作为可复制文本附在消息里 | 否 |
| `--aspect-ratio` | 图片宽高比（9:16 / 16:9 / 1:1 …） | 16:9 |
| `--provider` | 生成后端：auto / codex / gemini | auto |
| `--as` | 发送身份：bot / user（图片建议 bot） | 读 `.env`（缺省 bot） |
| `--dry-run` | 预览不发送（仍校验权限） | 否 |

**退出码**：`0` 全部成功；`1` 至少一个目标失败或生成失败。

---

## 8. 最佳实践

1. **图片一律 bot 身份**：上传权限 bot 默认就有，省去 user 权限审批。
2. **生成放后台**：模型推理几分钟起步，别前台干等，跑后台任务再回收结果。
3. **9:16 出人像、16:9 出图表**：按用途选宽高比。
4. **prompt 写清楚**：细节越具体出图越稳，负面约束能有效压掉不想要的元素。
5. **一次上传多目标复用**：脚本已内置，多人/多群推送不重复上传。
6. **接收人配置化**：放 `.env`，方便增减、复用脚本。
7. **先 `--dry-run`**：批量发送前确认接收人和身份，注意 dry-run 仍会校验权限。

---

## 参考链接

- 飞书开放平台文档：https://open.feishu.cn/document/
- lark-cli GitHub：https://github.com/larksuite/cli
- 文本消息基础教程：[feishu-cli-guide.md](./feishu-cli-guide.md)

---

*本教程随 image-factory-skill 技能维护，示例命令均经过实测。*
