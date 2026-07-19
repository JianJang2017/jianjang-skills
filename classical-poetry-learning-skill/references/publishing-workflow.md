# 微信公众号草稿与发布工作流

## 安全边界

- 默认只创建草稿，不正式发布。
- 不打印、回显或写入输出目录中的 AppSecret/access token。
- 真实凭据优先放在 `~/.config/wechat-mp/wechat.env.profile`，目录权限 `700`、文件权限 `600`；也可使用环境变量或用户明确指定的凭据文件。
- 正式发布是外部公开动作，当前对话没有明确确认时必须停止。

## 脚本

将 `{baseDir}` 替换为技能目录绝对路径：

```bash
python3 {baseDir}/scripts/wechat_mp_publish.py --help
```

脚本默认读取：

1. `~/.config/wechat-mp/wechat.env.profile`
2. `WECHAT_ACCESS_TOKEN` 或 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`
3. 显式命令行参数（不建议把密钥留在 shell history）

## 1. 创建草稿前 dry-run

`--article` 必须传已排版的 `公众号发布稿.html`，不要直接传 Markdown。封面优先用 JPEG（宽度 ≥ 900px、< 1MB），文内图控制在 1MB 以内，详见 `references/wechat_api.md` 的图片规格表。

```bash
python3 {baseDir}/scripts/wechat_mp_publish.py draft \
  --article <outputs/公众号发布稿.html> \
  --cover <imgs/00-cover.jpg> \
  --title <标题> \
  --author <作者署名> \
  --digest <摘要> \
  --dry-run
```

检查：正文没有重复封面、没有主标题 `<h1>`、诗句与图片齐全、标题/摘要/作者正确、目标凭据来源符合预期。

dry-run 现在会**一并校验文内图和封面的格式/大小/尺寸**，把 `40009`、`53401` 这类问题在发布前暴露：

- 装有 Pillow 时，超限图片会自动生成压缩副本 `*.wechat.jpg`（不覆盖原图），dry-run 输出的 `src` 指向副本；正式创建草稿时上传的也是副本。
- 未装 Pillow 时，dry-run 直接报错并提示 `pip install Pillow` 或手动转 JPEG / 缩小，此时应先修好图片再继续，不要跳过。

## 2. 创建草稿

dry-run 通过后，使用相同参数去掉 `--dry-run`。脚本会上传封面、上传并改写本地文内图片、创建草稿。

成功必须以微信 API 回执中的草稿 `media_id` 为准。报告 `media_id` 后默认停止，让用户到公众号后台预览。

## 3. 正式发布

只有用户明确确认发布目标和内容后执行：

```bash
python3 {baseDir}/scripts/wechat_mp_publish.py publish \
  --media-id <MEDIA_ID> \
  --confirm-publish
```

成功以返回的 `publish_id` 为准。查询状态：

```bash
python3 {baseDir}/scripts/wechat_mp_publish.py status --publish-id <PUBLISH_ID>
```

## 故障路由

| 错误 | 下一步 |
|---|---|
| 凭据缺失 | 到微信开发者平台获取/核对 AppID 与 AppSecret，安全写入配置 |
| `40164` / invalid ip | 将当前服务器出口 IP 加入公众号白名单 |
| `40001` | 核对凭据或 token 所属账号 |
| `48001` / `53504` / `53505` | 检查接口权限、认证状态和发布能力 |
| 图片上传失败 | 检查路径、格式和大小；不要跳过后冒充草稿完整 |
| API/网络失败 | 保留 dry-run 产物与 HTML，报告可重试步骤 |

字段、端点和更完整错误码见 `references/wechat_api.md`。

