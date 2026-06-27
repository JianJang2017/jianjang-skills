# 飞书 CLI 集成基础教程

本教程基于 `@larksuite/cli`（lark-cli），讲解如何从零开始把飞书消息推送集成到自动化脚本中。内容来自实战，包含常见报错的根因与解法。

---

## 1. 什么是 lark-cli

`lark-cli` 是飞书/Lark 官方命令行工具，封装了飞书开放平台的 API，让你在终端或脚本中直接操作：

- 发送消息（私聊 / 群聊）
- 管理群组、日历、联系人
- 调用任意开放平台 API

本技能用它来把每日邮件汇总报告推送到飞书。

---

## 2. 安装

```bash
# 方式一：安装客户端（推荐，全局可用）
npx @larksuite/cli@latest install

# 方式二：每次用 npx 临时拉起（无需安装）
npx @larksuite/cli@latest <command>
```

安装后命令名为 `lark-cli`，验证：

```bash
lark-cli --help
```

---

## 3. 认证与身份

### 3.1 两种发送身份

lark-cli 有**两种身份**，理解它们是用好工具的关键：

| 身份 | 标识 | 说明 | 典型限制 |
|------|------|------|----------|
| **bot**（机器人） | 应用本身 | 以应用/机器人名义操作 | 发群消息需机器人**已在群内** |
| **user**（用户） | 登录的真人 | 以你本人名义操作 | 需要 `im:message.send_as_user` 权限 |

用 `--as bot` 或 `--as user` 指定身份，缺省一般是 `auto`。

### 3.2 登录

```bash
# 基础登录（扫码或浏览器验证）
lark-cli auth login

# 申请特定权限范围登录
lark-cli auth login --scope "im:message.send_as_user"
```

> ⚠️ **交互式登录注意**：`auth login` 会阻塞并输出一个验证 URL，需要在浏览器打开完成授权。
> 在自动化/后台环境里它可能不输出 URL（检测到非交互终端会缓冲）。**这一步最好在真实终端里手动运行**，不要放到后台任务。

### 3.3 查看当前授权状态

```bash
lark-cli auth status
```

输出会包含：
- `appId`：当前应用 ID
- `identities.bot` / `identities.user`：两种身份的就绪状态
- `user.scope`：用户身份**已授权的权限列表**（排查权限问题时重点看这里）
- `user.openId`：你本人的 open_id

---

## 4. 发送消息

核心命令：`lark-cli im +messages-send`

### 4.1 发给个人（私聊）

```bash
# 纯文本
lark-cli im +messages-send --as bot --user-id "ou_xxx" --text "Hello World 👋"

# Markdown（自动优化为飞书富文本卡片）
lark-cli im +messages-send --as bot --user-id "ou_xxx" --markdown "## 标题\n正文内容"
```

> ✅ **bot 给个人发私信不需要任何群成员关系**，这是最省事的推送方式。

### 4.2 发到群聊

```bash
lark-cli im +messages-send --as bot --chat-id "oc_xxx" --text "群通知"
```

> ⚠️ **群消息的前提：机器人必须先被加进群**（见第 6 节）。

### 4.3 常用参数

| 参数 | 说明 |
|------|------|
| `--as` | 身份：`bot` / `user` / `auto` |
| `--user-id` | 目标用户 open_id（ou_xxx），与 `--chat-id` 互斥 |
| `--chat-id` | 目标群聊 chat_id（oc_xxx），与 `--user-id` 互斥 |
| `--text` | 纯文本内容 |
| `--markdown` | Markdown 内容（自动转富文本，图片 URL 自动解析） |
| `--dry-run` | 只打印请求不实际发送（注意：仍会校验权限） |
| `--idempotency-key` | 幂等键，防止重复发送 |

---

## 5. 如何获取 user_id 和 chat_id

消息发送需要目标 ID，获取方法：

```bash
# 查找用户 open_id（ou_xxx）
lark-cli contact +search-user --query "张三"

# 列出机器人/你所在的群聊，找 chat_id（oc_xxx）
lark-cli im +chat-list

# 按关键词搜索群聊
lark-cli im +chat-search --query "研发群"

# 查看自己的 open_id
lark-cli auth status   # 看 user.openId 字段
```

---

## 6. 高频报错与解法

实战中最常遇到的三个错误：

### 6.1 `230002: Bot/User can NOT be out of the chat`

**原因**：机器人不在目标群里，飞书禁止"群外机器人"往群里发消息。

**解法**（只能手动操作，重试无效）：
1. 打开目标群聊
2. 群设置 → 群机器人 → 添加机器人
3. 选择你登录 lark-cli 用的那个应用（`auth status` 里的 `appId`）
4. 加完即可发送

> 注意：这不是临时故障，机器人不进群，重试多少次都是同一个错。

### 6.2 `missing required scope(s): im:message.send_as_user`

**原因**：用 `--as user` 发消息，但应用没有开通"以用户身份发送消息"权限。

**解法**：
1. 在飞书开放平台给应用添加 `im:message.send_as_user` 权限（可能需管理员审批）
2. 重新授权登录：
   ```bash
   lark-cli auth login --scope "im:message.send_as_user"
   ```

> 💡 **替代方案**：如果只是想把通知发出去，优先用 `--as bot`，避免 user 权限的麻烦。
> bot 私信个人无需任何额外权限，是最稳的路径。

### 6.3 `auth login` 在后台不输出验证 URL

**原因**：CLI 检测到非交互式终端时会缓冲输出，验证 URL 出不来。

**解法**：在真实终端里前台运行 `auth login`，不要丢到后台任务或管道里。

---

## 7. 在脚本中集成（Python 示例）

通过 `subprocess` 调用 lark-cli，是脚本集成最简单的方式：

```python
import subprocess

def push_to_feishu(content, target_id, target_type="user", identity="bot", dry_run=False):
    """推送 Markdown 消息到飞书。返回 (是否成功, 输出/错误信息)。"""
    cmd = ["lark-cli", "im", "+messages-send", "--as", identity, "--markdown", content]

    if target_type == "chat":
        cmd += ["--chat-id", target_id]
    else:
        cmd += ["--user-id", target_id]

    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr.strip() or result.stdout.strip()
    return True, result.stdout.strip()
```

### 7.1 多目标批量推送

```python
def push_to_targets(content, user_ids, chat_ids, identity="bot"):
    """同时推送给多个用户和群聊。"""
    targets = [(uid, "user") for uid in user_ids] + [(cid, "chat") for cid in chat_ids]
    for target_id, target_type in targets:
        ok, msg = push_to_feishu(content, target_id, target_type, identity)
        print(f"{'✅' if ok else '❌'} {target_type} {target_id}")
        if not ok:
            print(f"   错误: {msg}")
```

### 7.2 从配置文件读取接收人

把接收人放进 `.env`，逗号分隔支持多个：

```env
# 接收用户的 open_id，多个用英文逗号分隔
FEISHU_USER_IDS=ou_aaa,ou_bbb
# 接收群聊的 chat_id，多个用英文逗号分隔
FEISHU_CHAT_IDS=oc_xxx,oc_yyy
# 发送身份
FEISHU_SEND_AS=bot
```

读取并拆分：

```python
def split_csv(value):
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]

user_ids = split_csv(os.environ.get("FEISHU_USER_IDS", ""))
chat_ids = split_csv(os.environ.get("FEISHU_CHAT_IDS", ""))
```

---

## 8. 最佳实践

1. **优先用 bot 身份**：bot 给个人发私信零门槛，省去 user 权限审批的麻烦。
2. **群推送先确认机器人在群里**：这是群消息成功的硬前提。
3. **接收人配置化**：放 `.env` 而非硬编码，方便增减接收人、复用脚本。
4. **支持多目标**：用逗号分隔列表，一次推送给多个用户/群。
5. **失败不中断**：批量推送时，单个目标失败应记录并继续，最后汇总成功/失败数。
6. **交互式登录手动做**：`auth login` 别放后台。
7. **定时任务前先 `--dry-run`**：确认接收人和内容无误，但记住 dry-run 仍会校验权限。

---

## 9. 配合定时任务

把推送脚本加入 cron，实现每日自动推送：

```bash
crontab -e

# 每天早上 8:00 推送昨日邮件汇总（接收人从 .env 读取）
0 8 * * * cd /path/to/enterprise-email-manager && \
  python scripts/push_feishu.py --days 1 2>&1 | tee -a logs/feishu_push.log
```

---

## 参考链接

- 飞书开放平台文档：https://open.feishu.cn/document/
- lark-cli GitHub：https://github.com/larksuite/cli
- 错误码查询：在报错的 `troubleshooter` URL 中查看具体建议

---

*本教程随 enterprise-email-manager 技能维护，示例命令均经过实测。*
