#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件整理归类工具

按规则将邮件移动到指定文件夹，支持：
- 按发件人、主题、时间等条件筛选
- 自动创建目标文件夹
- dry-run 预览模式
- 递归搜索所有文件夹（--all-folders）
- 批量规则（从 JSON 配置文件读取）
"""
import os
import re
import sys
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_config import (  # noqa: E402
    load_env, connect_imap, decode_mime_header, build_search_criteria,
    search_messages, fetch_message, scan_by_header, list_all_folders,
)


def create_folder_if_not_exists(conn, folder_name):
    """创建文件夹（如果不存在）。

    返回: (是否成功, 错误信息或None)
    """
    # 先检查是否已存在
    status, folders = conn.list()
    if status != "OK":
        return False, "无法列出文件夹"

    for f in folders:
        line = f.decode(errors='replace') if isinstance(f, bytes) else str(f)
        if folder_name in line:
            return True, None  # 已存在

    # 不存在，创建
    status, data = conn.create('"%s"' % folder_name)
    if status == "OK":
        return True, None
    else:
        msg = data[0].decode() if data and data[0] else "未知错误"
        return False, msg


def preview_messages(conn, uids, folder=None):
    """拉取邮件头信息用于预览，返回列表。"""
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


def organize(args):
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
            conn.logout()
            sys.exit(1)

    if args.subject_match:
        try:
            re.compile(args.subject_match)
        except re.error as e:
            sys.stderr.write(f"错误：--subject-match 正则表达式语法错误：{e}\n")
            sys.stderr.write(f"您输入的表达式：{args.subject_match}\n")
            sys.stderr.write("提示：常见正则语法 - | 表示或，. 匹配任意字符，* 表示0或多次，+ 表示1或多次\n")
            conn.logout()
            sys.exit(1)

    folder_uid_map = {}  # {源文件夹原始名: {'uids': [...], 'readable': '可读名'}}

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
        print("没有匹配的邮件，无需整理。")
        conn.logout()
        return

    # 大量操作警告
    if total > 500 and not args.dry_run:
        print("=" * 70)
        print("⚠️  您即将移动 %d 封邮件到「%s」" % (total, args.target))
        print("=" * 70)
        print("\n建议：")
        print("  1. 先使用 --dry-run 参数预览要移动的邮件")
        print("  2. 确认目标文件夹正确")
        print("  3. 确认无误后再执行实际移动")
        print("\n按 Enter 继续，或 Ctrl+C 取消...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\n已取消移动操作。")
            conn.logout()
            return
        print()

    # 预览模式：只展示，不移动
    if args.dry_run:
        print("=== 预览模式（DRY RUN）：以下 %d 封邮件将移动到「%s」，但现在不会实际移动 ===\n"
              % (total, args.target))

        # 按源文件夹和发件人分组展示
        for folder_raw, info in folder_uid_map.items():
            uids = info['uids']
            folder_readable = info['readable']
            if len(folder_uid_map) > 1:
                print("【源文件夹】%s —— %d 封" % (folder_readable, len(uids)))

            rows = preview_messages(conn, uids, folder_raw)

            # 按发件人分组
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
                for r in items[:10]:  # 每个发件人最多显示 10 封，避免刷屏
                    idx += 1
                    print("%s%d. [%s] %s" % (indent, idx, r["date"], r["subject"]))
                if len(items) > 10:
                    print("%s   ... 还有 %d 封（省略）" % (indent, len(items) - 10))
                print("")

        if len(folder_uid_map) > 1:
            print("共 %d 个源文件夹、%d 封邮件 → 目标文件夹「%s」。" % (len(folder_uid_map), total, args.target))
        else:
            print("共 %d 封邮件 → 目标文件夹「%s」。" % (total, args.target))
        print("确认无误后，去掉 --dry-run 参数执行实际整理。")
        conn.logout()
        return

    # 实际整理：创建目标文件夹（如果不存在）→ 逐文件夹移动
    print("即将整理 %d 封邮件到「%s」..." % (total, args.target))

    success, err = create_folder_if_not_exists(conn, args.target)
    if not success:
        sys.stderr.write("无法创建目标文件夹「%s」：%s\n" % (args.target, err))
        conn.logout()
        sys.exit(1)

    moved = 0
    for folder_raw, info in folder_uid_map.items():
        uids = info['uids']
        # select 源文件夹（写模式）
        conn.select('"%s"' % folder_raw)
        for uid in uids:
            # COPY 到目标文件夹
            status, _ = conn.uid("COPY", uid, '"%s"' % args.target)
            if status == "OK":
                # 标记源邮件为已删除
                conn.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                moved += 1
        # expunge 清理已删除标记的邮件
        conn.expunge()

    conn.logout()
    print("整理完成：已将 %d 封邮件移动到「%s」。" % (moved, args.target))


def organize_by_rules(args):
    """按配置文件中的规则批量整理邮件。

    配置文件格式（JSON）：
    [
      {
        "name": "规则名称",
        "from_match": "发件人正则",
        "subject_match": "主题正则（可选）",
        "target": "目标文件夹",
        "all_folders": true
      },
      ...
    ]
    """
    if not os.path.exists(args.rules):
        sys.stderr.write("规则配置文件不存在：%s\n" % args.rules)
        sys.exit(1)

    with open(args.rules, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    if not isinstance(rules, list):
        sys.stderr.write("规则配置文件格式错误：根节点应为数组\n")
        sys.exit(1)

    print("=== 批量整理：共 %d 条规则 ===\n" % len(rules))

    for i, rule in enumerate(rules, 1):
        name = rule.get("name", "规则%d" % i)
        from_match = rule.get("from_match")
        subject_match = rule.get("subject_match")
        target = rule.get("target")
        all_folders = rule.get("all_folders", False)

        if not target:
            print("[%d/%d] %s：跳过（缺少 target）" % (i, len(rules), name))
            continue
        if not from_match and not subject_match:
            print("[%d/%d] %s：跳过（缺少 from_match 或 subject_match）" % (i, len(rules), name))
            continue

        print("[%d/%d] %s：from_match=%s, target=%s, all_folders=%s"
              % (i, len(rules), name, from_match or subject_match, target, all_folders))

        # 构造临时 args 对象
        class TempArgs:
            pass
        temp = TempArgs()
        temp.from_match = from_match
        temp.subject_match = subject_match
        temp.target = target
        temp.all_folders = all_folders
        temp.folder = "INBOX"
        temp.since = temp.before = temp.sender = temp.subject = None
        temp.seen = temp.unseen = False
        temp.dry_run = args.dry_run

        organize(temp)
        print("")

    print("批量整理完成。")


def main():
    p = argparse.ArgumentParser(description="邮件整理归类工具")
    subparsers = p.add_subparsers(dest="command", help="子命令")

    # 单条规则整理
    p_single = subparsers.add_parser("move", help="按单条规则整理邮件到指定文件夹")
    p_single.add_argument("--target", "-t", required=True, help="目标文件夹名称")
    p_single.add_argument("--folder", default="INBOX", help="源文件夹（默认 INBOX）")
    p_single.add_argument("--since", help='起始时间，如 "2026-01-01" 或 "30 days ago"')
    p_single.add_argument("--before", help='结束时间')
    p_single.add_argument("--sender", help="发件人邮箱或名称（IMAP 服务端子串搜索）")
    p_single.add_argument("--subject", help="主题关键词（IMAP 服务端子串搜索）")
    p_single.add_argument("--from-match", dest="from_match",
                          help="发件人正则（客户端扫描，更可靠）")
    p_single.add_argument("--subject-match", dest="subject_match",
                          help="主题正则（客户端扫描）")
    p_single.add_argument("--all-folders", action="store_true",
                          help="递归搜索所有文件夹（需配合 --from-match 或 --subject-match 使用）")
    p_single.add_argument("--seen", action="store_true", help="只整理已读邮件")
    p_single.add_argument("--unseen", action="store_true", help="只整理未读邮件")
    p_single.add_argument("--dry-run", action="store_true",
                          help="预览模式，只显示将整理的邮件，不实际移动")

    # 批量规则整理
    p_batch = subparsers.add_parser("batch", help="按配置文件中的规则批量整理邮件")
    p_batch.add_argument("--rules", "-r", required=True, help="规则配置文件路径（JSON 格式）")
    p_batch.add_argument("--dry-run", action="store_true", help="预览模式")

    args = p.parse_args()

    if args.command == "move":
        organize(args)
    elif args.command == "batch":
        organize_by_rules(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
