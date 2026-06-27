#!/usr/bin/env python3
"""批量删除邮件，支持预览（dry-run）、移到垃圾箱、永久删除。

删除是危险操作。本脚本默认要求先用 --dry-run 预览，确认后再执行。
永久删除（--mode permanent）不可恢复，使用时务必谨慎。

用法见 --help。
"""

import os
import re
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_config import (  # noqa: E402
    load_env, connect_imap, decode_mime_header, build_search_criteria,
    search_messages, fetch_message, scan_by_header,
)

# 常见垃圾箱文件夹名（不同邮箱服务器命名不一）
TRASH_CANDIDATES = ["Trash", "Deleted Items", "已删除", "垃圾箱",
                    "Deleted Messages", "&XfJT0ZAB-"]

# 单次 UID 命令打包多少封。IMAP 的 COPY/STORE 支持逗号分隔的 UID 列表，
# 一次发多封能大幅减少往返次数，避免大批量时被服务器 autologout。
UID_CHUNK = 100


def _chunked(seq, n):
    """把序列按 n 个一组切分。"""
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _join_uids(uids):
    """把 UID 列表（bytes 或 str）拼成逗号分隔的字符串，供 IMAP 命令使用。"""
    parts = []
    for u in uids:
        parts.append(u.decode() if isinstance(u, bytes) else str(u))
    return ",".join(parts)


def find_trash_folder(conn):
    """探测服务器上的垃圾箱文件夹名。找不到则返回 None。"""
    status, folders = conn.list()
    if status != "OK":
        return None
    available = []
    for f in folders:
        line = f.decode(errors="replace") if isinstance(f, bytes) else str(f)
        available.append(line)
    for candidate in TRASH_CANDIDATES:
        for line in available:
            if candidate in line:
                # 提取引号中的文件夹名
                if '"' in line:
                    name = line.split('"')[-2]
                    return name
                return candidate
    return None


def preview_messages(conn, uids, folder=None):
    """拉取邮件头信息用于预览，返回列表。

    folder: 如果指定，先 select 该文件夹再 fetch（用于多文件夹场景）
    """
    if folder:
        conn.select('"%s"' % folder, readonly=True)

    rows = []
    for uid in uids:
        msg = fetch_message(conn, uid)
        if msg is None:
            continue
        rows.append({
            "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
            "from": decode_mime_header(msg.get("From")),
            "subject": decode_mime_header(msg.get("Subject")),
            "date": msg.get("Date", ""),
        })
    return rows


def delete(args):
    config = load_env()
    conn = connect_imap(config)

    # 验证正则表达式
    if args.from_match:
        try:
            re.compile(args.from_match)
        except re.error as e:
            sys.stderr.write(f"错误：--from-match 正则表达式语法错误：{e}\n")
            sys.stderr.write(f"您输入的表达式：{args.from_match}\n")
            sys.stderr.write("提示：常见正则语法 - | 表示或，. 匹配任意字符，* 表示0或多次，+ 表示1或多次\n")
            sys.exit(1)

    if args.subject_match:
        try:
            re.compile(args.subject_match)
        except re.error as e:
            sys.stderr.write(f"错误：--subject-match 正则表达式语法错误：{e}\n")
            sys.stderr.write(f"您输入的表达式：{args.subject_match}\n")
            sys.stderr.write("提示：常见正则语法 - | 表示或，. 匹配任意字符，* 表示0或多次，+ 表示1或多次\n")
            sys.exit(1)

    # 两种筛选方式：
    # 1) 客户端正则扫描（--from-match / --subject-match）：更可靠，能匹配 noreply 的各种变体
    # 2) 服务端 IMAP SEARCH（其余条件）：速度快，但子串匹配会漏掉变体
    folder_uid_map = {}  # {文件夹原始名: [uid列表]} 或 {文件夹原始名: [(uid, 可读名)]}

    if args.from_match or args.subject_match:
        result = scan_by_header(conn, args.folder,
                                from_regex=args.from_match,
                                subject_regex=args.subject_match,
                                all_folders=args.all_folders)
        if args.all_folders:
            # result 是 [(folder_raw, uid, folder_readable), ...]
            for folder_raw, uid, folder_readable in result:
                if folder_raw not in folder_uid_map:
                    folder_uid_map[folder_raw] = {'uids': [], 'readable': folder_readable}
                folder_uid_map[folder_raw]['uids'].append(uid)
        else:
            # result 是 [uid, ...]
            folder_uid_map[args.folder] = {'uids': result, 'readable': args.folder}
    else:
        if args.all_folders:
            print("--all-folders 目前仅支持与 --from-match 或 --subject-match 组合使用。")
            print("提示：服务端搜索（--sender/--subject）不支持跨文件夹，请用客户端正则扫描。")
            conn.logout()
            return
        charset, criteria = build_search_criteria(
            since=args.since, before=args.before, sender=args.sender,
            subject=args.subject,
            seen=args.seen if args.seen else None,
            unseen=args.unseen if args.unseen else None,
        )
        uids = search_messages(conn, args.folder, charset, criteria)
        folder_uid_map[args.folder] = {'uids': uids, 'readable': args.folder}

    total = sum(len(v['uids']) for v in folder_uid_map.values())

    if total == 0:
        print("没有匹配的邮件，无需删除。")
        conn.logout()
        return

    # 大量删除警告
    if total > 500 and not args.dry_run:
        print("=" * 70)
        print("⚠️  警告：您即将删除 %d 封邮件！" % total)
        print("=" * 70)
        if args.mode == "permanent":
            print("❌ 永久删除模式：邮件将不可恢复！")
        else:
            print("📁 移到垃圾箱模式：邮件可以从垃圾箱恢复")
        if args.yes:
            # 非交互模式（脚本/自动化）：已显式 --yes 确认，跳过键盘等待
            print("\n已通过 --yes 确认，跳过交互式确认，开始执行。\n")
        else:
            print("\n建议：")
            print("  1. 先使用 --dry-run 参数预览要删除的邮件")
            print("  2. 确认无误后再执行实际删除")
            print("\n按 Enter 继续，或 Ctrl+C 取消...")
            print("（非交互环境请改用 --yes 参数跳过此确认）")
            try:
                input()
            except KeyboardInterrupt:
                print("\n\n已取消删除操作。")
                conn.logout()
                return
            except EOFError:
                # 无法读取键盘输入（管道/重定向等非交互环境）
                sys.stderr.write(
                    "\n检测到非交互环境，无法读取确认输入。\n"
                    "如需在脚本/自动化中执行，请加 --yes 参数显式确认。\n")
                conn.logout()
                sys.exit(1)
            print()

    # 预览模式：只展示，不删除
    if args.dry_run:
        print("=== 预览模式（DRY RUN）：以下 %d 封邮件将被删除，但现在不会实际删除 ===\n" % total)

        # 按文件夹和发件人分组展示
        for folder_raw, info in folder_uid_map.items():
            uids = info['uids']
            folder_readable = info['readable']
            if len(folder_uid_map) > 1:  # 多文件夹时显示文件夹名
                print("【文件夹】%s —— %d 封" % (folder_readable, len(uids)))

            rows = preview_messages(conn, uids, folder_raw)

            # 按发件人分组展示，方便人工区分"推广/账号验证/内部通知"等不同类别，
            # 避免把验证邮件、公司构建告警等当成 newsletter 一起误删。
            groups = {}
            for r in rows:
                groups.setdefault(r["from"], []).append(r)

            idx = 0
            for sender in sorted(groups, key=lambda s: -len(groups[s])):
                items = groups[sender]
                if len(folder_uid_map) > 1:
                    print("  └─ 发件人：%s —— %d 封" % (sender, len(items)))
                    indent = "      "
                else:
                    print("【发件人】%s —— 共 %d 封" % (sender, len(items)))
                    indent = "  "
                for r in items:
                    idx += 1
                    print("%s%d. [%s] %s" % (indent, idx, r["date"], r["subject"]))
                print("")

        if len(folder_uid_map) > 1:
            print("共 %d 个文件夹、%d 封邮件。" % (len(folder_uid_map), total))
        else:
            print("共 %d 封邮件。" % total)
        print("确认无误后，去掉 --dry-run 参数并指定 --mode 执行真正的删除。")
        if args.mode == "permanent":
            print("⚠️  注意：你选择的是永久删除，该操作不可恢复！")
        conn.logout()
        return

    # 实际删除
    print("即将删除 %d 封邮件（模式：%s）..." % (total, args.mode))

    trash = None
    if args.mode == "trash":
        trash = find_trash_folder(conn)
        if not trash:
            sys.stderr.write(
                "未找到垃圾箱文件夹，无法执行 trash 模式。\n"
                "可改用 --mode permanent（永久删除），或手动指定垃圾箱名。\n")
            conn.logout()
            sys.exit(1)

    deleted = _delete_uids(conn, config, folder_uid_map, args.mode, trash)

    if args.mode == "trash":
        print("已将 %d 封邮件移到垃圾箱「%s」（可在垃圾箱中恢复）。" % (deleted, trash))
    else:
        print("已永久删除 %d 封邮件（不可恢复）。" % deleted)

    try:
        conn.logout()
    except Exception:
        pass


def _delete_uids(conn, config, folder_uid_map, mode, trash):
    """按文件夹批量删除邮件，返回实际处理的封数。

    关键设计（解决大批量时 IMAP autologout 的问题）：
    - UID 命令按 UID_CHUNK 个一批打包，减少往返次数；
    - 每批操作前后若连接被服务器超时断开，自动重连续传。
    COPY/STORE 都接受逗号分隔的 UID 列表，因此一条命令即可处理一批。
    """
    import imaplib

    def ensure_conn(c):
        """确保连接可用；不可用则重连并返回新连接。"""
        try:
            c.noop()
            return c
        except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError):
            return connect_imap(config)

    processed = 0
    for folder_raw, info in folder_uid_map.items():
        uids = info['uids']
        if not uids:
            continue
        conn = ensure_conn(conn)
        conn.select('"%s"' % folder_raw)

        for chunk in _chunked(uids, UID_CHUNK):
            ids = _join_uids(chunk)
            # 单批失败（多为 autologout）时重连并重做该批
            for attempt in (1, 2):
                try:
                    if mode == "trash":
                        conn.uid("COPY", ids, '"%s"' % trash)
                    conn.uid("STORE", ids, "+FLAGS", "(\\Deleted)")
                    break
                except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError) as e:
                    if attempt == 2:
                        raise
                    sys.stderr.write(
                        "连接中断（%s），正在重连续传...\n" % e)
                    conn = connect_imap(config)
                    conn.select('"%s"' % folder_raw)
            processed += len(chunk)

        conn = ensure_conn(conn)
        conn.select('"%s"' % folder_raw)
        conn.expunge()

    return processed


def main():
    p = argparse.ArgumentParser(description="批量删除邮件（支持预览/垃圾箱/永久删除）")
    p.add_argument("--folder", default="INBOX", help="邮箱文件夹（默认 INBOX）")
    p.add_argument("--since", help='起始时间，如 "2026-01-01" 或 "30 days ago"')
    p.add_argument("--before", help='结束时间，如 "365 days ago"')
    p.add_argument("--sender", help="发件人邮箱或名称（IMAP 服务端子串搜索，快但会漏变体）")
    p.add_argument("--subject", help="主题关键词（IMAP 服务端子串搜索）")
    p.add_argument("--from-match", dest="from_match",
                   help="发件人正则（客户端扫描，更可靠，能匹配 noreply/no-reply 等变体）")
    p.add_argument("--subject-match", dest="subject_match",
                   help="主题正则（客户端扫描）")
    p.add_argument("--all-folders", action="store_true",
                   help="递归搜索所有文件夹（需配合 --from-match 或 --subject-match 使用）")
    p.add_argument("--seen", action="store_true", help="只删除已读邮件")
    p.add_argument("--unseen", action="store_true", help="只删除未读邮件")
    p.add_argument("--mode", choices=["trash", "permanent"], default="trash",
                   help="trash=移到垃圾箱(可恢复)，permanent=永久删除(不可恢复)")
    p.add_argument("--dry-run", action="store_true",
                   help="预览模式，只显示将删除的邮件，不实际删除")
    p.add_argument("--yes", action="store_true",
                   help="跳过大批量删除时的交互式确认（用于脚本/自动化；务必先 --dry-run 确认过）")
    args = p.parse_args()
    delete(args)


if __name__ == "__main__":
    main()
