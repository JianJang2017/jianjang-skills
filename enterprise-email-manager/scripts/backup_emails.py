#!/usr/bin/env python3
"""备份邮件为 EML 文件。

将符合筛选条件的邮件保存到本地，每封邮件一个 .eml 文件，
附件单独保存到 attachments/ 子目录。已备份的邮件会跳过（断点续传）。

用法见 --help。
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_config import (  # noqa: E402
    load_env, connect_imap, decode_mime_header, build_search_criteria,
    search_messages, fetch_message, safe_filename, scan_by_header,
)


def get_attachments(msg):
    """提取邮件中的附件，返回 [(文件名, 字节内容), ...]。"""
    attachments = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        disposition = str(part.get("Content-Disposition") or "")
        if "attachment" in disposition.lower():
            filename = part.get_filename()
            if filename:
                filename = decode_mime_header(filename)
                payload = part.get_payload(decode=True)
                if payload:
                    attachments.append((safe_filename(filename), payload))
    return attachments


def backup(args):
    config = load_env()
    conn = connect_imap(config)

    folder_uid_map = {}  # {文件夹原始名: {'uids': [...], 'readable': '可读名'}}

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
        print("没有匹配的邮件，无需备份。")
        conn.logout()
        return

    # 数量警告和限制
    if args.limit and args.limit < total:
        print("⚠️  匹配到 %d 封邮件，但设置了限制，将只备份前 %d 封" % (total, args.limit))
        total = args.limit
    elif total > 1000:
        print("⚠️  匹配到 %d 封邮件，数量较大，备份可能需要较长时间" % total)
        print("提示：可使用 --limit 参数限制备份数量，例如 --limit 100")
        # 给用户5秒时间取消
        try:
            import time
            for i in range(5, 0, -1):
                print(f"  {i} 秒后开始备份... (按 Ctrl+C 取消)", end='\r')
                time.sleep(1)
            print(" " * 50)  # 清除倒计时行
        except KeyboardInterrupt:
            print("\n\n已取消备份。")
            conn.logout()
            return

    print("开始备份到 %s ..." % args.output)

    global_saved = 0
    global_skipped = 0
    global_attach = 0
    global_processed = 0  # 已处理总数

    # 逐文件夹备份
    for folder_raw, info in folder_uid_map.items():
        uids = info['uids']
        folder_readable = info['readable']

        # 应用限制：按顺序处理，达到限制后停止
        if args.limit and global_processed >= args.limit:
            break

        # 按文件夹组织输出目录
        folder_dir = os.path.join(args.output, safe_filename(folder_readable))
        os.makedirs(folder_dir, exist_ok=True)
        attach_root = os.path.join(folder_dir, "attachments")

        # select 该文件夹
        conn.select('"%s"' % folder_raw, readonly=True)

        saved = 0
        skipped = 0
        attach_count = 0

        # 分批处理（每批最多100封，避免一次性加载太多到内存）
        batch_size = 100
        for batch_start in range(0, len(uids), batch_size):
            # 检查是否达到全局限制
            if args.limit and global_processed >= args.limit:
                break

            batch_end = min(batch_start + batch_size, len(uids))
            if args.limit:
                # 如果有限制，计算本批次实际应处理的数量
                remaining = args.limit - global_processed
                batch_end = min(batch_end, batch_start + remaining)

            batch_uids = uids[batch_start:batch_end]

            for i, uid in enumerate(batch_uids, 1):
                uid_str = uid.decode() if isinstance(uid, bytes) else str(uid)
                msg = fetch_message(conn, uid)
                if msg is None:
                    continue

                subject = decode_mime_header(msg.get("Subject"))
                date_raw = msg.get("Date", "")
                # 文件名：UID_主题，UID 保证唯一且支持断点续传
                base_name = "%s_%s" % (uid_str, safe_filename(subject, max_len=60))
                eml_path = os.path.join(folder_dir, base_name + ".eml")

                if os.path.exists(eml_path):
                    skipped += 1
                    global_processed += 1
                    continue

                # 保存 EML
                with open(eml_path, "wb") as f:
                    f.write(msg.as_bytes())
                saved += 1
                global_processed += 1

                # 保存附件
                attachments = get_attachments(msg)
                if attachments:
                    msg_attach_dir = os.path.join(attach_root, base_name)
                    os.makedirs(msg_attach_dir, exist_ok=True)
                    for fname, payload in attachments:
                        with open(os.path.join(msg_attach_dir, fname), "wb") as f:
                            f.write(payload)
                        attach_count += 1

                # 进度显示（每10封或批次结束时）
                current_in_folder = batch_start + i
                if (current_in_folder % 10 == 0 or current_in_folder == len(uids) or
                    (args.limit and global_processed >= args.limit)):
                    progress_total = len(uids) if not args.limit else min(len(uids), args.limit - (global_processed - current_in_folder))
                    print("  [%s] 进度 %d/%d（新增 %d，跳过 %d）" %
                          (folder_readable, current_in_folder, len(uids), saved, skipped))

                # 达到限制后停止
                if args.limit and global_processed >= args.limit:
                    break

        global_saved += saved
        global_skipped += skipped
        global_attach += attach_count

    conn.logout()
    print("\n备份完成：新增 %d 封，跳过 %d 封（已存在），保存附件 %d 个。"
          % (global_saved, global_skipped, global_attach))
    print("输出目录：%s" % os.path.abspath(args.output))


def main():
    p = argparse.ArgumentParser(description="备份邮件为 EML 文件")
    p.add_argument("--output", "-o", default="./email_backup", help="备份输出目录")
    p.add_argument("--folder", default="INBOX", help="邮箱文件夹（默认 INBOX）")
    p.add_argument("--since", help='起始时间，如 "2026-01-01" 或 "30 days ago"')
    p.add_argument("--before", help='结束时间，如 "2026-06-01" 或 "7 days ago"')
    p.add_argument("--sender", help="发件人邮箱或名称（IMAP 服务端子串搜索）")
    p.add_argument("--subject", help="主题关键词（IMAP 服务端子串搜索）")
    p.add_argument("--from-match", dest="from_match",
                   help="发件人正则（客户端扫描，更可靠，能匹配 noreply/no-reply 等变体）")
    p.add_argument("--subject-match", dest="subject_match",
                   help="主题正则（客户端扫描）")
    p.add_argument("--all-folders", action="store_true",
                   help="递归搜索所有文件夹（需配合 --from-match 或 --subject-match 使用）")
    p.add_argument("--seen", action="store_true", help="只备份已读邮件")
    p.add_argument("--unseen", action="store_true", help="只备份未读邮件")
    p.add_argument("--limit", type=int, help="限制备份邮件数量（例如 --limit 100 只备份前100封）")
    args = p.parse_args()
    backup(args)


if __name__ == "__main__":
    main()
