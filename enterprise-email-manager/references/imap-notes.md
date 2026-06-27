# IMAP / SMTP 技术细节

本文档记录企业邮箱操作中容易踩坑的技术细节，脚本已封装这些处理，
但在调试或扩展功能时可以参考。

## 中文编码处理

### 邮件头解码（接收）

邮件的主题、发件人名等头字段如果含中文，会按 RFC 2047 编码成形如
`=?utf-8?B?5L2g5aW9?=` 或 `=?gbk?Q?...?=` 的形式。直接读取会得到乱码，
必须用 `email.header.decode_header` 解码，并处理不同字符集（utf-8、gbk、gb2312）。

`email_config.decode_mime_header()` 已统一处理，包括解码失败时的兜底
（`errors="replace"`），避免单封异常邮件中断整个批处理。

### 搜索条件编码（查询）

IMAP 的 `SEARCH` 命令默认只支持 ASCII。按中文主题或中文发件人搜索时，
必须带上 `CHARSET UTF-8` 并把搜索词编码为 UTF-8 字节：

```python
conn.uid("SEARCH", "CHARSET", "UTF-8", "SUBJECT", "项目".encode("utf-8"))
```

`build_search_criteria()` 会检测条件是否含非 ASCII 字符，自动切换到带
CHARSET 的搜索模式。

### 附件文件名编码（发送/接收）

中文附件名同样需要编码。发送时用 `("utf-8", "", filename)` 元组形式
设置 Content-Disposition；接收时同样用 `decode_mime_header` 解码。

## 文件夹名

不同企业邮箱服务器的文件夹命名差异很大：

- 中文文件夹名可能是 UTF-7 修正编码（IMAP modified UTF-7），如「已删除」
  可能显示为 `&XfJT0ZAB-`
- 含空格或中文的文件夹名在 SELECT 时需要用双引号包裹

`delete_emails.find_trash_folder()` 通过 `LIST` 命令探测实际的垃圾箱名，
覆盖了常见的中英文命名（Trash、Deleted Items、已删除、垃圾箱等）。

## UID vs 序列号

IMAP 有两种邮件标识：

- **序列号（sequence number）**：随邮箱变化，删除邮件后会重新编号，不稳定
- **UID**：在一个文件夹内唯一且稳定

脚本统一使用 UID（`conn.uid(...)`），这样：
- 备份的文件名用 UID 命名，支持断点续传（重跑时已存在的 UID 文件会跳过）
- 删除操作针对 UID，不会因序列号变动而误删

## 删除的语义

IMAP 没有"直接删除"，删除分两步：

1. 给邮件打 `\Deleted` 标记：`STORE uid +FLAGS (\Deleted)`
2. 执行 `EXPUNGE` 真正从服务器移除打了标记的邮件

"移到垃圾箱"的实现是：先 `COPY` 到垃圾箱文件夹，再在原文件夹打 `\Deleted`
标记并 `EXPUNGE`。这样邮件在垃圾箱里还能恢复。

"永久删除"则跳过 COPY，直接打标记 + EXPUNGE。

## SSL 端口

常见企业邮箱：

| 协议 | SSL 端口 | 非 SSL 端口 |
|------|---------|-----------|
| IMAP | 993 | 143 |
| POP3 | 995 | 110 |
| SMTP | 465 | 25 |

脚本默认使用 SSL 端口（`IMAP4_SSL` / `SMTP_SSL`）。强烈建议始终用 SSL，
避免密码明文传输。

## 批量发送的频率限制

企业邮箱服务器通常对发信频率有限制，短时间发送大量邮件可能：
- 被限流（临时拒绝）
- 被判定为垃圾邮件源

`send_template.py` 默认在批量发送时每封之间 sleep 1 秒（`--delay` 可调）。
发送量很大时（上百封），考虑分批、加大延时，或与 IT 部门确认发信配额。

## 大邮箱备份的稳定性

备份成千上万封邮件时，IMAP 连接可能超时断开。当前脚本通过 UID 命名 +
跳过已存在文件实现断点续传——连接断了重新运行即可，已下载的不会重复下载。
如需更强健壮性，可改造为分批 FETCH + 定期重连。
