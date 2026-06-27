#!/usr/bin/env python3
"""发送模版邮件，支持纯文本/HTML、变量替换、批量发送、附件。

模版放在 assets/templates/，用 {{变量名}} 作为占位符。
收件人可以是单个（命令行）或批量（CSV/JSON 文件）。

用法见 --help。
"""

import os
import re
import sys
import csv
import json
import time
import argparse
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from email.header import Header
from email.utils import formataddr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_config import load_env, connect_smtp  # noqa: E402

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "templates")
ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets")


def render(text, variables):
    """用变量替换模版中的 {{key}} 占位符。

    未提供的变量保持原样并警告，避免静默发出含 {{xxx}} 的邮件。
    """
    missing = set()

    def repl(m):
        key = m.group(1).strip()
        if key in variables:
            return str(variables[key])
        missing.add(key)
        return m.group(0)

    result = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", repl, text)
    if missing:
        sys.stderr.write("警告：模版中以下变量未提供值：%s\n" % ", ".join(missing))
    return result


def get_signature_vars(config):
    """从配置中提取签名信息。"""
    return {
        'sender_name': config.get('sender_name', ''),
        'sender_title': config.get('sender_title', ''),
        'sender_department': config.get('sender_department', ''),
        'sender_email': config.get('email', ''),
        'sender_phone': config.get('sender_phone', ''),
        'sender_address': config.get('sender_address', ''),
        'company_name': config.get('company_name', ''),
        'company_website': config.get('company_website', ''),
        'company_address': config.get('company_address', ''),
    }


def load_template(name):
    """加载模版内容，根据扩展名判断是 HTML 还是纯文本。"""
    # 允许传入完整路径或仅文件名
    path = name if os.path.isabs(name) or os.path.exists(name) \
        else os.path.join(TEMPLATE_DIR, name)
    if not os.path.exists(path):
        sys.stderr.write("找不到模版文件：%s\n" % path)
        sys.stderr.write("模版应放在 %s 目录下。\n" % TEMPLATE_DIR)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    is_html = path.lower().endswith((".html", ".htm"))
    return content, is_html


def attach_file(msg, filepath):
    """把文件作为附件加到邮件上。"""
    if not os.path.exists(filepath):
        sys.stderr.write("警告：附件不存在，已跳过：%s\n" % filepath)
        return
    ctype, encoding = mimetypes.guess_type(filepath)
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"
    maintype, subtype = ctype.split("/", 1)
    with open(filepath, "rb") as f:
        part = MIMEBase(maintype, subtype)
        part.set_payload(f.read())
    encoders.encode_base64(part)
    filename = os.path.basename(filepath)
    # 用 Header 编码文件名以支持中文
    part.add_header("Content-Disposition", "attachment",
                    filename=("utf-8", "", filename))
    msg.attach(part)


def build_message(from_addr, to_addr, subject, body, is_html, attachments, embed_logo=False):
    """构造一封邮件。

    embed_logo: 是否嵌入公司logo（用于HTML模板中的cid:company_logo）
    """
    # 如果是HTML且需要嵌入logo，使用 MIMEMultipart('related')
    if is_html and embed_logo:
        msg = MIMEMultipart('related')
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(body, "html", "utf-8"))

        # 嵌入logo图片
        logo_path = os.path.join(ASSETS_DIR, "images", "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_img = MIMEImage(f.read())
                logo_img.add_header('Content-ID', '<company_logo>')
                logo_img.add_header('Content-Disposition', 'inline', filename='logo.png')
                msg.attach(logo_img)

        # 添加附件
        if attachments:
            for a in attachments:
                attach_file(msg, a)
    elif attachments:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, "html" if is_html else "plain", "utf-8"))
        for a in attachments:
            attach_file(msg, a)
    else:
        msg = MIMEText(body, "html" if is_html else "plain", "utf-8")

    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = Header(subject, "utf-8")
    return msg


def load_recipients(path):
    """从 CSV 或 JSON 加载批量收件人。

    CSV：第一行表头，必须含 email 列，其余列作为变量。
    JSON：[{"email": "...", "name": "...", ...}, ...]
    """
    recipients = []
    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            recipients = json.load(f)
    else:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            recipients = list(reader)

    for r in recipients:
        if "email" not in r or not r["email"]:
            sys.stderr.write("错误：收件人数据缺少 email 字段：%s\n" % r)
            sys.exit(1)
    return recipients


def send(args):
    config = load_env()

    template_body, is_html = load_template(args.template)

    # 解析命令行变量 --var key=value
    cli_vars = {}
    for v in (args.var or []):
        if "=" not in v:
            sys.stderr.write("忽略格式错误的变量（应为 key=value）：%s\n" % v)
            continue
        k, _, val = v.partition("=")
        cli_vars[k.strip()] = val

    # 添加签名信息到变量中（从.env读取）
    signature_vars = get_signature_vars(config)
    cli_vars.update(signature_vars)

    # 确定收件人列表
    if args.recipients:
        recipients = load_recipients(args.recipients)
    elif args.to:
        recipients = [dict(cli_vars, email=args.to)]
    else:
        sys.stderr.write("错误：必须指定 --to 或 --recipients。\n")
        sys.exit(1)

    from_addr = formataddr((str(Header(args.from_name or "", "utf-8")), config["email"])) \
        if args.from_name else config["email"]

    # 检查模板是否使用了logo（包含 cid:company_logo）
    embed_logo = is_html and 'cid:company_logo' in template_body

    # Dry-run 模式：只预览不发送
    if args.dry_run:
        print("=" * 70)
        print("📧 预览模式（不会实际发送邮件）")
        print("=" * 70)
        print(f"\n发件人: {from_addr}")
        print(f"收件人数量: {len(recipients)}")
        print(f"模板类型: {'HTML' if is_html else '纯文本'}")
        if embed_logo:
            print("包含嵌入Logo: 是")
        if args.attach:
            print(f"附件: {', '.join(args.attach)}")
        print("\n" + "-" * 70)

        # 预览前3封邮件
        preview_count = min(3, len(recipients))
        for i, r in enumerate(recipients[:preview_count], 1):
            variables = dict(cli_vars)
            variables.update({k: v for k, v in r.items() if k != "email"})

            body = render(template_body, variables)
            subject = render(args.subject, variables)
            to_addr = r["email"]

            print(f"\n【邮件 {i}/{len(recipients)}】")
            print(f"收件人: {to_addr}")
            print(f"主题: {subject}")
            print(f"变量: {variables}")
            print(f"\n正文预览（前200字符）:")
            print("-" * 70)
            preview_body = body[:200].replace('\n', '\n  ')
            print(f"  {preview_body}{'...' if len(body) > 200 else ''}")
            print("-" * 70)

        if len(recipients) > preview_count:
            print(f"\n...还有 {len(recipients) - preview_count} 封邮件未显示")

        print("\n" + "=" * 70)
        print("✅ 预览完成。移除 --dry-run 参数以实际发送。")
        print("=" * 70)
        return

    # 实际发送模式
    smtp = connect_smtp(config)
    sent = 0
    failed = 0

    for r in recipients:
        # 合并变量：命令行变量为基础，收件人行数据覆盖
        variables = dict(cli_vars)
        variables.update({k: v for k, v in r.items() if k != "email"})

        body = render(template_body, variables)
        subject = render(args.subject, variables)
        to_addr = r["email"]

        msg = build_message(from_addr, to_addr, subject, body, is_html, args.attach, embed_logo)

        try:
            smtp.sendmail(config["email"], [to_addr], msg.as_string())
            sent += 1
            print("已发送 -> %s（主题：%s）" % (to_addr, subject))
        except Exception as e:  # noqa: BLE001
            failed += 1
            sys.stderr.write("发送失败 -> %s：%s\n" % (to_addr, e))

        # 批量发送时加短延时，避免触发服务器频率限制
        if len(recipients) > 1:
            time.sleep(args.delay)

    smtp.quit()
    print("\n发送完成：成功 %d 封，失败 %d 封。" % (sent, failed))


def main():
    p = argparse.ArgumentParser(description="发送模版邮件")
    p.add_argument("--to", help="单个收件人邮箱")
    p.add_argument("--recipients", help="批量收件人文件（CSV 或 JSON）")
    p.add_argument("--subject", required=True, help="邮件主题（支持 {{变量}}）")
    p.add_argument("--template", required=True, help="模版文件名或路径")
    p.add_argument("--var", action="append", help="模版变量，格式 key=value，可多次")
    p.add_argument("--attach", action="append", help="附件路径，可多次")
    p.add_argument("--from-name", help="发件人显示名称")
    p.add_argument("--delay", type=float, default=1.0,
                   help="批量发送时每封之间的延时秒数（默认 1.0）")
    p.add_argument("--dry-run", action="store_true",
                   help="预览模式：渲染邮件但不实际发送")
    args = p.parse_args()
    send(args)


if __name__ == "__main__":
    main()
