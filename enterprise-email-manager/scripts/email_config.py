"""共享配置与连接模块。

负责从 .env 加载邮箱凭证，并提供 IMAP / SMTP 连接的封装。
所有脚本都依赖此模块，避免重复实现连接逻辑。

设计要点：
- 密码只从环境/.env 读取，绝不打印到终端。
- 中文主题/发件人名的解码统一在这里处理（RFC 2047）。
- 时间表达式（如 "30 days ago"）统一解析为 IMAP 需要的格式。
"""

import os
import re
import sys
import email
import imaplib
import smtplib
from datetime import datetime, timedelta
from email.header import decode_header


def _split_csv(value):
    """将逗号分隔的字符串拆分为去空、去重后的列表。"""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_env(env_path=None):
    """加载 .env 文件中的配置。

    查找顺序：显式传入的路径 -> 当前目录 -> 逐级向上查找最多 5 层。
    这样无论脚本从哪个工作目录运行，都能找到项目根目录的 .env。
    """
    if env_path is None:
        # 从当前工作目录逐级向上找 .env
        cur = os.getcwd()
        for _ in range(6):
            candidate = os.path.join(cur, ".env")
            if os.path.exists(candidate):
                env_path = candidate
                break
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent

    if env_path and os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # 不覆盖已存在的真实环境变量
                os.environ.setdefault(key, value)

    config = {
        "email": os.environ.get("EMAIL_ADDRESS"),
        "password": os.environ.get("EMAIL_PASSWORD"),
        "imap_server": os.environ.get("IMAP_SERVER"),
        "imap_port": int(os.environ.get("IMAP_PORT", "993")),
        "smtp_server": os.environ.get("SMTP_SERVER"),
        "smtp_port": int(os.environ.get("SMTP_PORT", "465")),
        # 邮件签名信息
        "sender_name": os.environ.get("SENDER_NAME", ""),
        "sender_title": os.environ.get("SENDER_TITLE", ""),
        "sender_department": os.environ.get("SENDER_DEPARTMENT", ""),
        "sender_phone": os.environ.get("SENDER_PHONE", ""),
        "sender_address": os.environ.get("SENDER_ADDRESS", ""),
        # 公司信息
        "company_name": os.environ.get("COMPANY_NAME", ""),
        "company_website": os.environ.get("COMPANY_WEBSITE", ""),
        "company_address": os.environ.get("COMPANY_ADDRESS", ""),
        # 飞书推送配置（push_feishu.py 使用）
        "feishu_user_ids": _split_csv(os.environ.get("FEISHU_USER_IDS", "")),
        "feishu_chat_ids": _split_csv(os.environ.get("FEISHU_CHAT_IDS", "")),
        "feishu_send_as": os.environ.get("FEISHU_SEND_AS", "bot"),
        "feishu_vip_senders": _split_csv(os.environ.get("FEISHU_VIP_SENDERS", "")),
    }

    missing = [k for k in ("email", "password", "imap_server") if not config[k]]
    if missing:
        sys.stderr.write(
            "错误：.env 中缺少必要配置: %s\n"
            "请确保 .env 包含 EMAIL_ADDRESS / EMAIL_PASSWORD / IMAP_SERVER 等字段。\n"
            % ", ".join(m.upper() for m in missing)
        )
        sys.exit(1)

    return config


def connect_imap(config):
    """建立 IMAP SSL 连接并登录。返回已登录的连接对象。"""
    try:
        conn = imaplib.IMAP4_SSL(config["imap_server"], config["imap_port"])
        conn.login(config["email"], config["password"])
        return conn
    except imaplib.IMAP4.error as e:
        sys.stderr.write("IMAP 登录失败：%s\n" % e)
        sys.stderr.write("请检查邮箱地址、密码（或授权码）和服务器配置。\n")
        sys.exit(1)


def connect_smtp(config):
    """建立 SMTP SSL 连接并登录。返回已登录的连接对象。"""
    try:
        conn = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
        conn.login(config["email"], config["password"])
        return conn
    except smtplib.SMTPException as e:
        sys.stderr.write("SMTP 登录失败：%s\n" % e)
        sys.exit(1)


def decode_mime_header(raw):
    """解码 MIME 编码的邮件头（主题、发件人名等），正确处理中文。

    邮件头里的中文常被编码成 =?utf-8?B?...?= 或 =?gbk?Q?...?= 形式，
    需要按声明的字符集逐段解码再拼接。
    """
    if raw is None:
        return ""
    parts = decode_header(raw)
    result = []
    for text, charset in parts:
        if isinstance(text, bytes):
            try:
                result.append(text.decode(charset or "utf-8", errors="replace"))
            except (LookupError, TypeError):
                result.append(text.decode("utf-8", errors="replace"))
        else:
            result.append(text)
    return "".join(result)


def parse_date_expr(expr):
    """把人类可读的时间表达式解析为 IMAP 需要的 DD-Mon-YYYY 格式。

    支持：
    - "30 days ago" / "7 days ago"
    - "2026-01-01"
    - datetime / date 对象
    """
    if expr is None:
        return None
    if isinstance(expr, datetime):
        dt = expr
    else:
        expr = str(expr).strip()
        m = re.match(r"(\d+)\s+days?\s+ago", expr, re.IGNORECASE)
        if m:
            dt = datetime.now() - timedelta(days=int(m.group(1)))
        else:
            # 尝试常见日期格式
            dt = None
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
                try:
                    dt = datetime.strptime(expr, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                raise ValueError("无法解析时间表达式: %s" % expr)
    return dt.strftime("%d-%b-%Y")


def build_search_criteria(since=None, before=None, sender=None,
                          subject=None, seen=None, unseen=None):
    """根据筛选条件构造 IMAP SEARCH 命令的参数列表。

    IMAP 的 SEARCH 对非 ASCII（中文）需要配合 CHARSET UTF-8。
    返回 (charset, criteria_list)。criteria 为空时默认 ALL。
    """
    criteria = []
    charset = None

    if since:
        criteria += ["SINCE", parse_date_expr(since)]
    if before:
        criteria += ["BEFORE", parse_date_expr(before)]
    if sender:
        criteria += ["FROM", sender]
        if not sender.isascii():
            charset = "UTF-8"
    if subject:
        criteria += ["SUBJECT", subject]
        if not subject.isascii():
            charset = "UTF-8"
    if seen:
        criteria += ["SEEN"]
    if unseen:
        criteria += ["UNSEEN"]

    if not criteria:
        criteria = ["ALL"]

    return charset, criteria


def search_messages(conn, folder, charset, criteria):
    """选择文件夹并执行搜索，返回邮件 UID 列表（字符串）。"""
    # 文件夹名含中文时需要用引号包裹
    status, _ = conn.select('"%s"' % folder if folder != "INBOX" else folder)
    if status != "OK":
        # 退回到 INBOX
        conn.select("INBOX")

    if charset:
        # 中文搜索需要把条件编码为 bytes
        encoded = [c.encode("utf-8") if isinstance(c, str) and not c.isascii() else c
                   for c in criteria]
        status, data = conn.uid("SEARCH", "CHARSET", charset, *encoded)
    else:
        status, data = conn.uid("SEARCH", None, *criteria)

    if status != "OK" or not data or not data[0]:
        return []
    return data[0].split()


def fetch_message(conn, uid):
    """按 UID 拉取完整邮件，返回 email.message.Message 对象。"""
    status, data = conn.uid("FETCH", uid, "(RFC822)")
    if status != "OK" or not data or not data[0]:
        return None
    raw = data[0][1]
    return email.message_from_bytes(raw)


def fetch_headers(conn, uids, fields=("FROM", "SUBJECT", "DATE")):
    """批量只拉取邮件头（不下载正文/附件），返回 {uid: {field: value}}。

    只取头部比 FETCH RFC822 快几个数量级，适合"先扫描再筛选"的场景。
    解码后的中文头通过 decode_mime_header 处理。
    """
    result = {}
    if not uids:
        return result
    field_str = " ".join(f.upper() for f in fields)
    # 分批，避免一次性请求过多 UID 导致命令过长
    batch = 200
    for i in range(0, len(uids), batch):
        chunk = uids[i:i + batch]
        uid_set = b",".join(u if isinstance(u, bytes) else str(u).encode()
                            for u in chunk)
        status, data = conn.uid(
            "FETCH", uid_set,
            "(BODY.PEEK[HEADER.FIELDS (%s)])" % field_str)
        if status != "OK" or not data:
            continue
        # data 形如 [(b'1 (UID 5 BODY[...] {n}', b'headers...'), b')', ...]
        cur_uid = None
        for item in data:
            if isinstance(item, tuple) and len(item) == 2:
                meta = item[0].decode(errors="replace") if isinstance(item[0], bytes) else str(item[0])
                m = re.search(r"UID (\d+)", meta)
                cur_uid = m.group(1) if m else None
                hdr = email.message_from_bytes(item[1])
                if cur_uid is not None:
                    result[cur_uid] = {
                        f.lower(): decode_mime_header(hdr.get(f.title()))
                        for f in fields
                    }
    return result


def list_all_folders(conn):
    """列出邮箱所有文件夹，返回 (原始名, 可读名, 邮件数) 元组列表。

    原始名是 IMAP UTF-7 编码（如 &W5pl9k77UqE-），可读名是解码后的中文。
    """
    import base64

    def imap_utf7_decode(name):
        """IMAP modified UTF-7 解码为 Unicode"""
        out, i = [], 0
        while i < len(name):
            c = name[i]
            if c == '&':
                j = name.find('-', i)
                chunk = name[i+1:j]
                if chunk == '':
                    out.append('&')
                else:
                    chunk = chunk.replace(',', '/')
                    pad = '=' * (-len(chunk) % 4)
                    try:
                        decoded = base64.b64decode(chunk + pad).decode('utf-16-be')
                        out.append(decoded)
                    except Exception:
                        out.append(name[i:j+1])  # 解码失败保留原样
                i = j + 1
            else:
                out.append(c)
                i += 1
        return ''.join(out)

    status, folders = conn.list()
    if status != "OK" or not folders:
        return []

    result = []
    for f in folders:
        line = f.decode(errors='replace') if isinstance(f, bytes) else str(f)
        # 提取引号中的文件夹名
        if '"' in line:
            raw_name = line.split('"')[-2]
        else:
            raw_name = line.split()[-1]

        # 解码为可读名
        readable = imap_utf7_decode(raw_name) if '&' in raw_name else raw_name

        # 取邮件数
        try:
            st, cnt = conn.select('"%s"' % raw_name, readonly=True)
            n = int(cnt[0].decode()) if st == 'OK' and cnt and cnt[0] else 0
        except Exception:
            n = 0

        result.append((raw_name, readable, n))

    return result


def scan_by_header(conn, folder, from_regex=None, subject_regex=None, all_folders=False):
    """客户端正则扫描：先取全部邮件头，再按 From/Subject 正则匹配。

    比 IMAP 服务端 SEARCH 更可靠——服务端的子串搜索经常漏掉变体
    （如 'noreply' 搜不到 'no-reply'），而客户端正则可以精确控制。

    参数:
        all_folders: True 时递归搜索所有文件夹，False 时只搜指定文件夹。

    返回匹配的 UID 列表（字符串）或 (folder, uid) 元组列表（all_folders=True 时）。
    """
    if all_folders:
        # 递归搜索所有文件夹
        folders = list_all_folders(conn)
        all_matched = []
        for raw_name, readable, count in folders:
            if count == 0:
                continue
            matches = scan_by_header(conn, raw_name, from_regex, subject_regex, all_folders=False)
            for uid in matches:
                all_matched.append((raw_name, uid, readable))  # (文件夹原始名, UID, 可读名)
        return all_matched

    # 单文件夹搜索
    status, _ = conn.select('"%s"' % folder if folder != "INBOX" else folder, readonly=True)
    if status != "OK":
        return []

    status, data = conn.uid("SEARCH", None, "ALL")
    if status != "OK" or not data or not data[0]:
        return []
    all_uids = data[0].split()

    headers = fetch_headers(conn, all_uids, fields=("FROM", "SUBJECT"))

    from_re = re.compile(from_regex, re.IGNORECASE) if from_regex else None
    subj_re = re.compile(subject_regex, re.IGNORECASE) if subject_regex else None

    matched = []
    for uid in all_uids:
        uid_str = uid.decode() if isinstance(uid, bytes) else str(uid)
        h = headers.get(uid_str, {})
        if from_re and not from_re.search(h.get("from", "")):
            continue
        if subj_re and not subj_re.search(h.get("subject", "")):
            continue
        if from_re or subj_re:
            matched.append(uid)
    return matched


def safe_filename(text, max_len=100):
    """把主题等文本转换为安全的文件名，去除非法字符。"""
    text = decode_mime_header(text) if text else "no-subject"
    text = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", text)
    text = text.strip().strip(".")
    if len(text) > max_len:
        text = text[:max_len]
    return text or "no-subject"


def list_folders(conn):
    """列出邮箱中所有可用的文件夹。

    返回格式化的文件夹列表字符串，包括层级缩进显示。
    """
    status, folders = conn.list()
    if status != "OK":
        return "无法获取文件夹列表"

    folder_list = []
    for folder_bytes in folders:
        # IMAP LIST 返回格式: (flags) "delimiter" "folder_name"
        folder_str = folder_bytes.decode("utf-8")
        # 提取文件夹名（在最后一个引号对中）
        match = re.search(r'"([^"]+)"[^"]*$', folder_str)
        if match:
            folder_name = match.group(1)
            # 解码 IMAP modified UTF-7 编码
            try:
                decoded = folder_name.encode().decode('imap4-internal')
            except:
                decoded = folder_name
            folder_list.append(decoded)

    return folder_list


if __name__ == "__main__":
    """命令行工具：列出邮箱文件夹。"""
    import argparse

    parser = argparse.ArgumentParser(description="邮箱配置工具")
    parser.add_argument("--list-folders", action="store_true", help="列出邮箱中所有文件夹")
    args = parser.parse_args()

    if args.list_folders:
        load_env()
        try:
            conn = get_imap_connection()
            folders = list_folders(conn)
            print("\n📁 邮箱文件夹列表：\n")
            for i, folder in enumerate(folders, 1):
                # 根据层级添加缩进
                indent = "  " * folder.count("/")
                print(f"{i:2d}. {indent}{folder}")
            print(f"\n共 {len(folders)} 个文件夹")
            conn.logout()
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
