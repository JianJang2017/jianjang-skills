#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书推送 - 将每日邮件汇总报告推送到飞书

支持多接收人（用户 + 群组），目标可从 .env 配置或命令行参数指定。

用法:
  # 使用 .env 中配置的接收人（FEISHU_USER_IDS / FEISHU_CHAT_IDS）
  python scripts/push_feishu.py --days 0

  # 命令行指定多个用户（覆盖配置文件）
  python scripts/push_feishu.py --days 0 --user-ids "ou_aaa,ou_bbb"

  # 命令行指定多个群聊
  python scripts/push_feishu.py --days 0 --chat-ids "oc_xxx,oc_yyy"

  # 同时推送用户和群聊
  python scripts/push_feishu.py --days 0 --user-ids "ou_aaa" --chat-ids "oc_xxx"

  # 最近7天 + VIP发件人 + 保存本地报告
  python scripts/push_feishu.py --days 7 --vip-senders "boss@company.com" --save reports/weekly
"""

import subprocess
import sys
import os
import argparse
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_config import load_env, connect_imap, _split_csv
from daily_report import fetch_emails_in_range, EmailPriority, generate_markdown_report


def format_feishu_markdown(emails, days):
    """格式化为飞书 Markdown 消息（简洁版，适合 IM 通知）"""
    grouped = defaultdict(list)
    for e in emails:
        grouped[e['priority']].append(e)

    total = len(emails)
    urgent = len(grouped[EmailPriority.URGENT])
    important = len(grouped[EmailPriority.IMPORTANT])
    normal = len(grouped[EmailPriority.NORMAL])
    low = len(grouped[EmailPriority.LOW])

    date_str = datetime.now().strftime('%Y-%m-%d')
    date_label = "今日" if days == 0 else f"最近 {days} 天"
    now_time = datetime.now().strftime('%H:%M')

    lines = [
        f"## 📧 邮件汇总报告 · {date_str}",
        f"",
        f"**时间范围**: {date_label}　**邮件总数**: {total} 封",
        f"",
        f"| 等级 | 数量 | 说明 |",
        f"|------|------|------|",
        f"| 🔴 紧急 | **{urgent}** 封 | 需立即处理 |",
        f"| 🟠 重要 | **{important}** 封 | 今日内处理 |",
        f"| 🟢 普通 | {normal} 封 | 常规处理 |",
        f"| ⚪ 低优先级 | {low} 封 | 可延后处理 |",
    ]

    # 紧急邮件明细（全部展示）
    if grouped[EmailPriority.URGENT]:
        lines += ["", "---", "### 🔴 紧急邮件"]
        for i, e in enumerate(grouped[EmailPriority.URGENT], 1):
            attach = " 📎" if e['has_attachment'] else ""
            cc = f"  *(抄送{e['cc_count']}人)*" if e['cc_count'] > 0 else ""
            lines.append(f"{i}. **{e['subject']}**{attach}{cc}")
            lines.append(f"   发件人: `{e['from_addr']}`")

    # 重要邮件明细（最多5条）
    if grouped[EmailPriority.IMPORTANT]:
        lines += ["", "---", "### 🟠 重要邮件"]
        for i, e in enumerate(grouped[EmailPriority.IMPORTANT][:5], 1):
            attach = " 📎" if e['has_attachment'] else ""
            lines.append(f"{i}. **{e['subject']}**{attach}")
            lines.append(f"   发件人: `{e['from_addr']}`")
        if len(grouped[EmailPriority.IMPORTANT]) > 5:
            lines.append(f"   *...还有 {len(grouped[EmailPriority.IMPORTANT]) - 5} 封，查看完整报告*")

    lines += ["", "---", f"*Enterprise Email Manager · {now_time} 自动生成*"]
    return "\n".join(lines)


def push_one(markdown_content, target_id, target_type, identity="bot", dry_run=False):
    """调用 lark-cli 推送消息给单个目标。返回 (ok, message)。"""
    cmd = ["lark-cli", "im", "+messages-send", "--as", identity, "--markdown", markdown_content]

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


def push_to_targets(markdown_content, user_ids, chat_ids, identity="bot", dry_run=False):
    """推送给多个目标（用户 + 群聊）。返回结果汇总列表。"""
    results = []

    targets = [(uid, "user") for uid in user_ids] + [(cid, "chat") for cid in chat_ids]

    for target_id, target_type in targets:
        label = f"{'👤 用户' if target_type == 'user' else '👥 群聊'} {target_id}"
        ok, msg = push_one(markdown_content, target_id, target_type, identity, dry_run)
        status = "✅" if ok else "❌"
        print(f"  {status} {label}")
        if not ok:
            print(f"      错误: {msg}")
        results.append({"target": target_id, "type": target_type, "ok": ok, "message": msg})

    return results


def main():
    parser = argparse.ArgumentParser(
        description="生成每日邮件汇总并推送到飞书（支持多接收人，目标可从 .env 读取）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--days", type=int, default=0,
                        help="时间范围（天数）。0=今天，1=昨天，7=最近7天。默认: 0")
    parser.add_argument("--folder", default="INBOX",
                        help="邮箱文件夹名称。默认: INBOX")
    parser.add_argument("--vip-senders",
                        help="VIP发件人（逗号分隔），自动标记为紧急。覆盖 .env 的 FEISHU_VIP_SENDERS")

    # 飞书目标：多个用户 / 多个群聊（可同时指定）。不传则用 .env 配置
    parser.add_argument("--user-ids",
                        help="推送给用户的 open_id，多个用逗号分隔（ou_aaa,ou_bbb）。覆盖 .env 的 FEISHU_USER_IDS")
    parser.add_argument("--chat-ids",
                        help="推送到群聊的 chat_id，多个用逗号分隔（oc_xxx,oc_yyy）。覆盖 .env 的 FEISHU_CHAT_IDS")

    parser.add_argument("--save",
                        help="同时保存本地报告（不含扩展名，如 reports/today）")
    parser.add_argument("--as", dest="identity", choices=["bot", "user", "auto"],
                        default=None,
                        help="发送身份：bot（机器人）| user（用户本人，需 im:message.send_as_user 权限）| auto。默认读 .env 的 FEISHU_SEND_AS（缺省 bot）")
    parser.add_argument("--dry-run", action="store_true",
                        help="预览推送内容，不实际发送")
    args = parser.parse_args()

    print("=" * 50)
    print("📧 邮件汇总报告 → 飞书推送")
    print("=" * 50)

    # 加载配置
    config = load_env()

    # 接收人：命令行参数优先，否则用 .env 配置
    user_ids = _split_csv(args.user_ids) if args.user_ids is not None else config.get("feishu_user_ids", [])
    chat_ids = _split_csv(args.chat_ids) if args.chat_ids is not None else config.get("feishu_chat_ids", [])

    if not user_ids and not chat_ids:
        print("\n❌ 未指定任何接收人。请通过 --user-ids/--chat-ids 指定，")
        print("   或在 .env 中配置 FEISHU_USER_IDS / FEISHU_CHAT_IDS。")
        sys.exit(1)

    # 发送身份
    identity = args.identity or config.get("feishu_send_as", "bot")

    # VIP发件人：命令行优先，否则用 .env
    if args.vip_senders is not None:
        config["vip_senders"] = _split_csv(args.vip_senders)
    else:
        config["vip_senders"] = config.get("feishu_vip_senders", [])

    # 获取邮件
    print(f"\n🔌 连接邮箱...")
    mail = connect_imap(config)

    print(f"📬 获取邮件（最近 {args.days} 天，文件夹: {args.folder}）...")
    emails = fetch_emails_in_range(mail, args.folder, args.days, config)
    mail.logout()

    if not emails:
        print("⚠️  未找到邮件，跳过推送")
        return

    # 格式化消息
    markdown = format_feishu_markdown(emails, args.days)

    # 保存本地报告（可选）
    if args.save:
        save_dir = os.path.dirname(args.save)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        generate_markdown_report(emails, args.days, f"{args.save}.md")
        print(f"✅ 本地报告已保存: {args.save}.md")

    # 推送到飞书（多目标）
    total = len(user_ids) + len(chat_ids)
    print(f"\n📤 推送到飞书 → {len(user_ids)} 个用户 + {len(chat_ids)} 个群聊 "
          f"（身份: {identity}）{'（预览模式）' if args.dry_run else ''}...")

    results = push_to_targets(markdown, user_ids, chat_ids,
                              identity=identity, dry_run=args.dry_run)

    # 汇总
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = total - ok_count
    print(f"\n{'─' * 50}")
    print(f"推送完成: {ok_count} 成功, {fail_count} 失败 (共 {total} 个目标)")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
