#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日邮件汇总报告生成器

分析指定时间范围内的邮件，按重要等级分类并生成汇总报告。

重要等级分类规则：
1. 🔴 紧急 (Urgent): 标题包含"紧急"/"urgent"/"ASAP"，或来自VIP发件人
2. 🟠 重要 (Important): 有附件、抄送多人(>3)、标记为重要
3. 🟢 普通 (Normal): 常规工作邮件
4. ⚪ 低优先级 (Low): 通知类、营销类邮件

输出格式：
- Markdown 文本报告
- HTML 可视化报告（可选）
- JSON 结构化数据（可选）
"""

import imaplib
import email
import os
import sys
import re
from datetime import datetime, timedelta
from email.header import decode_header
from collections import defaultdict
import json

# 导入配置模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_config import load_env, connect_imap


class EmailPriority:
    """邮件优先级分类"""
    URGENT = "urgent"       # 🔴 紧急
    IMPORTANT = "important"  # 🟠 重要
    NORMAL = "normal"        # 🟢 普通
    LOW = "low"              # ⚪ 低优先级


def decode_email_header(header_value):
    """解码邮件头（处理中文等编码）"""
    if not header_value:
        return ""

    decoded_parts = decode_header(header_value)
    result = []
    for content, charset in decoded_parts:
        if isinstance(content, bytes):
            try:
                result.append(content.decode(charset or 'utf-8', errors='ignore'))
            except:
                result.append(content.decode('utf-8', errors='ignore'))
        else:
            result.append(str(content))
    return ''.join(result)


def extract_email_address(address_str):
    """从地址字符串中提取邮箱地址"""
    if not address_str:
        return ""

    # 匹配 <email@domain.com> 或 email@domain.com
    match = re.search(r'<([^>]+)>|([^\s<>]+@[^\s<>]+)', address_str)
    if match:
        return match.group(1) or match.group(2)
    return address_str


def classify_priority(msg, config):
    """
    对邮件进行优先级分类

    Args:
        msg: email.message.Message 对象
        config: 配置字典（包含VIP列表等）

    Returns:
        str: 优先级等级 (urgent/important/normal/low)
    """
    subject = decode_email_header(msg.get('Subject', ''))
    from_addr = extract_email_address(decode_email_header(msg.get('From', '')))
    importance = msg.get('Importance', '').lower()
    priority = msg.get('Priority', '').lower()

    # VIP 发件人列表（从配置或环境变量读取）
    vip_senders = config.get('vip_senders', [])

    # 紧急关键词
    urgent_keywords = ['紧急', 'urgent', 'asap', '立即', '马上', '紧急通知', 'critical']

    # 低优先级关键词
    low_keywords = ['通知', 'notification', '订阅', 'newsletter', '广告', 'promotion',
                    '营销', 'marketing', 'unsubscribe', '退订']

    # 🔴 紧急：VIP发件人 或 标题包含紧急关键词
    for keyword in urgent_keywords:
        if keyword in subject.lower():
            return EmailPriority.URGENT

    for vip in vip_senders:
        if vip.lower() in from_addr.lower():
            return EmailPriority.URGENT

    if importance == 'high' or priority == 'urgent':
        return EmailPriority.URGENT

    # ⚪ 低优先级：通知类、营销类
    for keyword in low_keywords:
        if keyword in subject.lower():
            return EmailPriority.LOW

    # 🟠 重要：有附件、抄送多人
    has_attachment = False
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            has_attachment = True
            break

    if has_attachment:
        return EmailPriority.IMPORTANT

    # 检查抄送人数
    cc = msg.get('Cc', '')
    if cc:
        cc_count = len([addr for addr in cc.split(',') if '@' in addr])
        if cc_count > 3:
            return EmailPriority.IMPORTANT

    # 🟢 普通
    return EmailPriority.NORMAL


def fetch_emails_in_range(mail, folder, days, config):
    """
    获取指定时间范围内的邮件

    Args:
        mail: IMAP连接对象
        folder: 文件夹名称
        days: 天数（0=今天，1=昨天，7=最近7天）
        config: 配置字典

    Returns:
        list: 邮件列表，每个元素为 (priority, email_data) 元组
    """
    # 选择文件夹
    status, _ = mail.select(folder, readonly=True)
    if status != 'OK':
        print(f"❌ 无法选择文件夹: {folder}")
        return []

    # 计算日期范围
    if days == 0:
        # 今天
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = datetime.now() - timedelta(days=days)

    date_str = start_date.strftime("%d-%b-%Y")

    # IMAP搜索（SINCE查找指定日期之后的邮件）
    search_criteria = f'(SINCE "{date_str}")'

    status, messages = mail.search(None, search_criteria)
    if status != 'OK':
        print(f"❌ 搜索失败")
        return []

    email_ids = messages[0].split()
    print(f"📬 找到 {len(email_ids)} 封邮件（从 {date_str} 开始）")

    emails = []

    for email_id in email_ids:
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # 分类
            priority = classify_priority(msg, config)

            # 提取关键信息
            email_info = {
                'id': email_id.decode(),
                'priority': priority,
                'subject': decode_email_header(msg.get('Subject', '无主题')),
                'from': decode_email_header(msg.get('From', '')),
                'from_addr': extract_email_address(decode_email_header(msg.get('From', ''))),
                'date': msg.get('Date', ''),
                'has_attachment': any(part.get_content_disposition() == 'attachment'
                                     for part in msg.walk()),
                'cc_count': len([a for a in msg.get('Cc', '').split(',') if '@' in a]),
            }

            emails.append(email_info)

        except Exception as e:
            print(f"⚠️  处理邮件 {email_id} 时出错: {e}")
            continue

    return emails


def generate_markdown_report(emails, days, output_file):
    """生成Markdown格式报告"""

    # 按优先级分组
    grouped = defaultdict(list)
    for email_info in emails:
        grouped[email_info['priority']].append(email_info)

    # 统计
    total = len(emails)
    stats = {
        EmailPriority.URGENT: len(grouped[EmailPriority.URGENT]),
        EmailPriority.IMPORTANT: len(grouped[EmailPriority.IMPORTANT]),
        EmailPriority.NORMAL: len(grouped[EmailPriority.NORMAL]),
        EmailPriority.LOW: len(grouped[EmailPriority.LOW]),
    }

    # 生成报告
    report_lines = []
    report_lines.append(f"# 📧 邮件汇总报告")
    report_lines.append(f"")

    if days == 0:
        report_lines.append(f"**报告日期**: {datetime.now().strftime('%Y年%m月%d日')} (今日)")
    else:
        report_lines.append(f"**报告日期**: 最近 {days} 天")

    report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**邮件总数**: {total} 封")
    report_lines.append(f"")
    report_lines.append(f"---")
    report_lines.append(f"")

    # 统计概览
    report_lines.append(f"## 📊 统计概览")
    report_lines.append(f"")
    report_lines.append(f"| 优先级 | 数量 | 占比 |")
    report_lines.append(f"|--------|------|------|")
    report_lines.append(f"| 🔴 紧急 | {stats[EmailPriority.URGENT]} | {stats[EmailPriority.URGENT]/total*100:.1f}% |")
    report_lines.append(f"| 🟠 重要 | {stats[EmailPriority.IMPORTANT]} | {stats[EmailPriority.IMPORTANT]/total*100:.1f}% |")
    report_lines.append(f"| 🟢 普通 | {stats[EmailPriority.NORMAL]} | {stats[EmailPriority.NORMAL]/total*100:.1f}% |")
    report_lines.append(f"| ⚪ 低优先级 | {stats[EmailPriority.LOW]} | {stats[EmailPriority.LOW]/total*100:.1f}% |")
    report_lines.append(f"")
    report_lines.append(f"---")
    report_lines.append(f"")

    # 按优先级输出详细列表
    priority_order = [
        (EmailPriority.URGENT, "🔴 紧急邮件", "需立即处理"),
        (EmailPriority.IMPORTANT, "🟠 重要邮件", "今日内处理"),
        (EmailPriority.NORMAL, "🟢 普通邮件", "常规处理"),
        (EmailPriority.LOW, "⚪ 低优先级邮件", "可延后处理"),
    ]

    for priority, title, desc in priority_order:
        emails_in_category = grouped[priority]
        if not emails_in_category:
            continue

        report_lines.append(f"## {title} ({len(emails_in_category)} 封)")
        report_lines.append(f"")
        report_lines.append(f"*{desc}*")
        report_lines.append(f"")

        for idx, email_info in enumerate(emails_in_category, 1):
            attachment_icon = "📎" if email_info['has_attachment'] else ""
            cc_info = f" (抄送{email_info['cc_count']}人)" if email_info['cc_count'] > 0 else ""

            report_lines.append(f"### {idx}. {email_info['subject']} {attachment_icon}")
            report_lines.append(f"")
            report_lines.append(f"- **发件人**: {email_info['from_addr']}")
            report_lines.append(f"- **时间**: {email_info['date']}{cc_info}")
            report_lines.append(f"")

        report_lines.append(f"---")
        report_lines.append(f"")

    # 写入文件
    report_content = '\n'.join(report_lines)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return report_content, stats


def generate_html_report(emails, days, output_file):
    """生成HTML格式报告（可视化）"""

    # 按优先级分组
    grouped = defaultdict(list)
    for email_info in emails:
        grouped[email_info['priority']].append(email_info)

    total = len(emails)
    stats = {
        EmailPriority.URGENT: len(grouped[EmailPriority.URGENT]),
        EmailPriority.IMPORTANT: len(grouped[EmailPriority.IMPORTANT]),
        EmailPriority.NORMAL: len(grouped[EmailPriority.NORMAL]),
        EmailPriority.LOW: len(grouped[EmailPriority.LOW]),
    }

    # HTML模板
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>邮件汇总报告 - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2em;
        }}
        .header .meta {{
            opacity: 0.9;
            font-size: 0.9em;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid;
        }}
        .stat-card.urgent {{ border-color: #e53e3e; }}
        .stat-card.important {{ border-color: #ed8936; }}
        .stat-card.normal {{ border-color: #48bb78; }}
        .stat-card.low {{ border-color: #cbd5e0; }}
        .stat-card .icon {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-card .label {{
            color: #718096;
            font-size: 0.9em;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }}
        .email-item {{
            padding: 15px;
            border-left: 3px solid #e2e8f0;
            margin-bottom: 15px;
            background: #f7fafc;
            border-radius: 5px;
        }}
        .email-item .subject {{
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 8px;
            color: #2d3748;
        }}
        .email-item .meta {{
            color: #718096;
            font-size: 0.9em;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            margin-left: 5px;
        }}
        .badge.attachment {{
            background: #bee3f8;
            color: #2c5282;
        }}
        .badge.cc {{
            background: #fed7d7;
            color: #742a2a;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📧 邮件汇总报告</h1>
        <div class="meta">
            <div>报告日期: {datetime.now().strftime('%Y年%m月%d日')} {"(今日)" if days == 0 else f"(最近{days}天)"}</div>
            <div>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div>邮件总数: {total} 封</div>
        </div>
    </div>

    <div class="stats">
        <div class="stat-card urgent">
            <div class="icon">🔴</div>
            <div class="number">{stats[EmailPriority.URGENT]}</div>
            <div class="label">紧急邮件 ({stats[EmailPriority.URGENT]/total*100:.1f}%)</div>
        </div>
        <div class="stat-card important">
            <div class="icon">🟠</div>
            <div class="number">{stats[EmailPriority.IMPORTANT]}</div>
            <div class="label">重要邮件 ({stats[EmailPriority.IMPORTANT]/total*100:.1f}%)</div>
        </div>
        <div class="stat-card normal">
            <div class="icon">🟢</div>
            <div class="number">{stats[EmailPriority.NORMAL]}</div>
            <div class="label">普通邮件 ({stats[EmailPriority.NORMAL]/total*100:.1f}%)</div>
        </div>
        <div class="stat-card low">
            <div class="icon">⚪</div>
            <div class="number">{stats[EmailPriority.LOW]}</div>
            <div class="label">低优先级邮件 ({stats[EmailPriority.LOW]/total*100:.1f}%)</div>
        </div>
    </div>
"""

    # 按优先级输出详细列表
    priority_configs = [
        (EmailPriority.URGENT, "🔴 紧急邮件", "需立即处理"),
        (EmailPriority.IMPORTANT, "🟠 重要邮件", "今日内处理"),
        (EmailPriority.NORMAL, "🟢 普通邮件", "常规处理"),
        (EmailPriority.LOW, "⚪ 低优先级邮件", "可延后处理"),
    ]

    for priority, title, desc in priority_configs:
        emails_in_category = grouped[priority]
        if not emails_in_category:
            continue

        html += f"""
    <div class="section">
        <h2>{title} ({len(emails_in_category)} 封)</h2>
        <p style="color: #718096; font-style: italic;">{desc}</p>
"""

        for email_info in emails_in_category:
            attachment_badge = '<span class="badge attachment">📎 附件</span>' if email_info['has_attachment'] else ''
            cc_badge = f'<span class="badge cc">抄送{email_info["cc_count"]}人</span>' if email_info['cc_count'] > 0 else ''

            html += f"""
        <div class="email-item">
            <div class="subject">{email_info['subject']} {attachment_badge} {cc_badge}</div>
            <div class="meta">
                <div>发件人: {email_info['from_addr']}</div>
                <div>时间: {email_info['date']}</div>
            </div>
        </div>
"""

        html += """
    </div>
"""

    html += """
</body>
</html>
"""

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    return html


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='生成邮件汇总报告，按重要等级分类',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成今日邮件汇总
  python daily_report.py --days 0 --output reports/today

  # 生成最近7天的汇总
  python daily_report.py --days 7 --output reports/weekly

  # 生成HTML可视化报告
  python daily_report.py --days 0 --format both --output reports/today

  # 指定文件夹和VIP发件人
  python daily_report.py --days 0 --folder INBOX --vip-senders "boss@company.com,ceo@company.com"
        """
    )

    parser.add_argument('--days', type=int, default=0,
                       help='时间范围（天数）。0=今天，1=昨天，7=最近7天。默认: 0')
    parser.add_argument('--folder', default='INBOX',
                       help='邮箱文件夹名称。默认: INBOX')
    parser.add_argument('--output', required=True,
                       help='输出文件路径（不含扩展名）')
    parser.add_argument('--format', choices=['markdown', 'html', 'both'], default='both',
                       help='输出格式。默认: both')
    parser.add_argument('--vip-senders',
                       help='VIP发件人列表（逗号分隔），这些发件人的邮件自动标记为紧急')
    parser.add_argument('--json', action='store_true',
                       help='同时输出JSON格式的结构化数据')

    args = parser.parse_args()

    print("="*60)
    print("📧 邮件汇总报告生成器")
    print("="*60)

    # 加载配置
    config = load_env()

    # VIP发件人列表
    vip_senders = []
    if args.vip_senders:
        vip_senders = [s.strip() for s in args.vip_senders.split(',')]
    config['vip_senders'] = vip_senders

    # 连接IMAP
    print(f"\n🔌 连接邮箱服务器...")
    mail = connect_imap(config)

    # 获取邮件
    print(f"📬 获取邮件（最近 {args.days} 天，文件夹: {args.folder}）...")
    emails = fetch_emails_in_range(mail, args.folder, args.days, config)

    if not emails:
        print("⚠️  未找到邮件")
        mail.logout()
        return

    # 生成报告
    print(f"\n📝 生成报告...")

    if args.format in ['markdown', 'both']:
        md_file = f"{args.output}.md"
        content, stats = generate_markdown_report(emails, args.days, md_file)
        print(f"✅ Markdown报告已生成: {md_file}")

    if args.format in ['html', 'both']:
        html_file = f"{args.output}.html"
        generate_html_report(emails, args.days, html_file)
        print(f"✅ HTML报告已生成: {html_file}")

    if args.json:
        json_file = f"{args.output}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(emails, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON数据已生成: {json_file}")

    # 打印统计
    print(f"\n" + "="*60)
    print(f"📊 统计汇总")
    print("="*60)
    print(f"  总计: {len(emails)} 封")

    # 按优先级统计
    grouped = defaultdict(list)
    for email_info in emails:
        grouped[email_info['priority']].append(email_info)

    print(f"  🔴 紧急: {len(grouped[EmailPriority.URGENT])} 封")
    print(f"  🟠 重要: {len(grouped[EmailPriority.IMPORTANT])} 封")
    print(f"  🟢 普通: {len(grouped[EmailPriority.NORMAL])} 封")
    print(f"  ⚪ 低优先级: {len(grouped[EmailPriority.LOW])} 封")

    # 关闭连接
    mail.logout()
    print(f"\n✅ 完成！")


if __name__ == '__main__':
    main()
