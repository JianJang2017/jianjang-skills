#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书图片推送 - 根据 prompt 生成图片并发送到飞书用户或群组

工作流：
  1. （可选）根据 prompt 调用 generate-image.js 生成图片
  2. 通过 lark-cli 将图片发送给指定的用户/群聊
  3. （可选）发送一条配文（markdown）

用法:
  # 生成图片并发送（接收人从 .env 读取）
  python scripts/send_feishu_image.py --prompt "一张科技感的系统架构图"

  # 生成并发送给指定用户和群聊
  python scripts/send_feishu_image.py \
      --prompt "手绘风格的部署流程图" \
      --user-ids "ou_aaa,ou_bbb" \
      --chat-ids "oc_xxx" \
      --caption "Q2 部署架构草图"

  # 发送已有图片（跳过生成）
  python scripts/send_feishu_image.py --image output/diagram.png --user-ids "ou_aaa"

  # 预览模式（不实际发送）
  python scripts/send_feishu_image.py --prompt "测试图" --dry-run

设计要点（避坑）:
  - lark-cli 的 --image 拒绝绝对路径与 .. ，所以发送时切到图片所在目录、只传文件名。
  - 单个目标失败不中断，最后汇总成功/失败数。
  - 接收人、发送身份优先用命令行参数，缺省读 .env。
"""

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime

# 复用同目录下的脚本路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)  # 技能包根目录
PROMPTS_DIR = os.path.join(SKILL_DIR, "prompts")  # prompt 归档目录
GENERATE_IMAGE_JS = os.path.join(SCRIPT_DIR, "generate-image.js")

# codex 把生成的图片写在这里（即使后续复制失败，原图仍在）
CODEX_GENERATED_DIR = os.path.join(os.path.expanduser("~"), ".codex", "generated_images")


def split_csv(value):
    """将逗号分隔的字符串拆分为去空后的列表。"""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def read_prompt_file(path):
    """从 prompt markdown 文件读取正文，剥离 frontmatter 与 PROMPT: 标记。

    与 generate-image.js 的解析保持一致：优先取 `PROMPT:` 段（修正版 regex），
    否则退而取去掉 --- frontmatter 后的全文。返回纯 prompt 文本（失败返回 None）。
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None

    import re
    # Fix: 用 \Z 匹配真正的字符串末尾，不是行末
    m = re.search(r"^PROMPT:\s*\n([\s\S]+?)(?=\n---|^\n##|\Z)", content, re.MULTILINE)
    if m:
        return m.group(1).strip()

    # 没有 PROMPT: 标记则剥离 frontmatter 后取全文
    lines = content.splitlines()
    in_fm = False
    body = []
    for line in lines:
        if line.strip() == "---":
            in_fm = not in_fm
            continue
        if not in_fm:
            body.append(line)
    text = "\n".join(body).strip()
    return text or None


def archive_prompt(prompt_text, aspect_ratio, provider):
    """将 prompt 归档到技能包的 prompts/ 目录，文件名格式：YYYYMMDD-NN.md。

    返回归档后的文件路径（成功）或 None（失败）。
    """
    if not prompt_text:
        return None

    os.makedirs(PROMPTS_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")

    # 找出今天已有的最大序号
    existing = [f for f in os.listdir(PROMPTS_DIR) if f.startswith(today + "-") and f.endswith(".md")]
    max_seq = 0
    for fname in existing:
        try:
            seq_str = fname[len(today) + 1 : -3]  # extract NN from YYYYMMDD-NN.md
            max_seq = max(max_seq, int(seq_str))
        except ValueError:
            pass
    next_seq = max_seq + 1
    filename = f"{today}-{next_seq:02d}.md"
    filepath = os.path.join(PROMPTS_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\naspect_ratio: \"{aspect_ratio}\"\n")
            f.write(f"provider: {provider}\n")
            f.write(f"timestamp: {datetime.now().isoformat()}\n")
            f.write("---\n\n")
            f.write(f"PROMPT:\n{prompt_text}\n")
        return filepath
    except OSError:
        return None


def archive_images(image_paths, prompt_md_path):
    """把刚生成的图片归档到 prompts/images/，命名与 prompt 文件一一对应。

    命名规则（按前缀检索友好）：
      - 单图（len==1）→ prompts/images/YYYYMMDD-NN.png
      - 多图（len>=2）→ prompts/images/YYYYMMDD-NN-1.png ... -N.png
    与对应的 prompt 文件 prompts/YYYYMMDD-NN.md 共享前缀，方便后期按规则规整。

    image_paths: 生成图片的本地路径列表（来自 generate-image.js 的临时输出）。
    prompt_md_path: archive_prompt() 返回的归档 md 路径；为空则放弃归档。
    返回归档后的路径列表（可能比输入短，因为单张复制失败不阻断其它图）。
    失败仅警告，不抛错——归档是辅助能力，绝不该影响主发送流程。
    """
    if not prompt_md_path or not image_paths:
        return []
    archive_dir = os.path.join(PROMPTS_DIR, "images")
    try:
        os.makedirs(archive_dir, exist_ok=True)
    except OSError:
        return []

    base = os.path.splitext(os.path.basename(prompt_md_path))[0]  # YYYYMMDD-NN
    multi = len(image_paths) > 1
    archived = []
    for i, src in enumerate(image_paths, 1):
        if not src or not os.path.exists(src):
            continue
        ext = os.path.splitext(src)[1] or ".png"
        name = f"{base}-{i}{ext}" if multi else f"{base}{ext}"
        dst = os.path.join(archive_dir, name)
        try:
            shutil.copyfile(src, dst)
            archived.append(dst)
        except OSError:
            # 单张失败不影响其它；只在 verbose 下提示，但不阻塞
            pass
    return archived




def load_env():
    """从就近的 .env 加载飞书配置（逐级向上查找最多 6 层）。

    返回 dict，包含 feishu_user_ids / feishu_chat_ids / feishu_send_as。
    不覆盖已存在的真实环境变量。
    """
    cur = os.getcwd()
    env_path = None
    for _ in range(6):
        candidate = os.path.join(cur, ".env")
        if os.path.exists(candidate):
            env_path = candidate
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    if env_path:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    return {
        "feishu_user_ids": split_csv(os.environ.get("FEISHU_USER_IDS", "")),
        "feishu_chat_ids": split_csv(os.environ.get("FEISHU_CHAT_IDS", "")),
        "feishu_send_as": os.environ.get("FEISHU_SEND_AS", "bot") or "bot",
    }


def _recover_codex_image(output, since_ts):
    """兜底：当 generate-image.js 失败/超时，但 codex 其实已经把图写进了
    ~/.codex/generated_images/ 时，扫描该目录找出 since_ts 之后最新的图，
    复制到 output。

    为什么需要：codex 在沙箱/只读目录下"自己复制到 output"会失败，
    或生成耗时触发超时——但原图通常已经落盘。直接捞原图即可救回本次结果。

    返回 output 路径（成功）或 None（没找到）。
    """
    if not os.path.isdir(CODEX_GENERATED_DIR):
        return None

    newest = None
    for root, _dirs, files in os.walk(CODEX_GENERATED_DIR):
        for name in files:
            if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue
            full = os.path.join(root, name)
            try:
                st = os.stat(full)
            except OSError:
                continue
            # 只认本次生成开始之后产生、且体积合理的图
            if st.st_mtime < since_ts or st.st_size < 1024:
                continue
            if newest is None or st.st_mtime > newest[1]:
                newest = (full, st.st_mtime)

    if not newest:
        return None

    try:
        os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
        shutil.copyfile(newest[0], output)
        if os.path.getsize(output) > 0:
            return output
    except OSError:
        # output 目录也不可写时，退而用源图原地路径（仍可发送）
        return newest[0]
    return None


def read_prompt_file(path):
    """从 prompt markdown 文件读取正文，剥离 frontmatter 与 PROMPT: 标记。

    与 generate-image.js 的解析保持一致：优先取 `PROMPT:` 段（修正版 regex），
    否则退而取去掉 --- frontmatter 后的全文。返回纯 prompt 文本（失败返回 None）。
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None

    import re
    # Fix: 用 \Z 匹配真正的字符串末尾，不是行末 $
    m = re.search(r"^PROMPT:\s*\n([\s\S]+?)(?=\n---|^\n##|\Z)", content, re.MULTILINE)
    if m:
        return m.group(1).strip()

    # 没有 PROMPT: 标记则剥离 frontmatter 后取全文
    lines = content.splitlines()
    in_fm = False
    body = []
    for line in lines:
        if line.strip() == "---":
            in_fm = not in_fm
            continue
        if not in_fm:
            body.append(line)
    text = "\n".join(body).strip()
    return text or None


def generate_image(prompt, output, aspect_ratio="16:9", provider="auto", verbose=True):
    """调用 generate-image.js 生成图片。返回 (ok, message)。

    若脚本失败/超时，会尝试从 codex 生成目录兜底捞回本次刚生成的图。
    message 在成功时是最终可用的图片路径（可能与 output 不同）。
    """
    if not os.path.exists(GENERATE_IMAGE_JS):
        return False, f"找不到图片生成脚本: {GENERATE_IMAGE_JS}"

    since_ts = time.time() - 5  # 容忍少量时钟/启动延迟

    # 把 prompt 写入临时 markdown，generate-image.js 会解析 PROMPT: 段
    prompt_fd, prompt_file = tempfile.mkstemp(suffix=".md", prefix="feishu-prompt-")
    try:
        with os.fdopen(prompt_fd, "w", encoding="utf-8") as f:
            f.write(f'---\naspect_ratio: "{aspect_ratio}"\n---\n\nPROMPT:\n{prompt}\n')

        cmd = [
            "node", GENERATE_IMAGE_JS,
            "--prompt-file", prompt_file,
            "--output", output,
            "--aspect-ratio", aspect_ratio,
            "--provider", provider,
        ]
        if verbose:
            print(f"🎨 生成图片中... (provider={provider}, ar={aspect_ratio})")

        result = subprocess.run(cmd, capture_output=True, text=True)

        # 正常成功路径
        if result.returncode == 0 and os.path.exists(output) and os.path.getsize(output) > 0:
            # 归档 prompt 到技能包 prompts/ 目录
            archived = archive_prompt(prompt, aspect_ratio, provider)
            if archived and verbose:
                print(f"📝 Prompt 已归档: {os.path.basename(archived)}")
            # 归档图片到 prompts/images/，命名与 prompt 文件一一对应
            img_archived = archive_images([output], archived)
            if img_archived and verbose:
                print(f"🖼️  图片已归档: {os.path.basename(img_archived[0])}")
            return True, output

        # 兜底：脚本失败/超时，但 codex 可能已经把图落盘了
        tail = (result.stderr or result.stdout).strip()[-300:]
        recovered = _recover_codex_image(output, since_ts)
        if recovered:
            if verbose:
                print(f"⚠️  生成脚本报错/超时，但已从 codex 目录兜底捞回图片：{recovered}")
            # 兜底成功时也归档 prompt
            archived = archive_prompt(prompt, aspect_ratio, provider)
            if archived and verbose:
                print(f"📝 Prompt 已归档: {os.path.basename(archived)}")
            # 兜底成功时也归档图片
            img_archived = archive_images([recovered], archived)
            if img_archived and verbose:
                print(f"🖼️  图片已归档: {os.path.basename(img_archived[0])}")
            return True, recovered

        if result.returncode != 0:
            return False, f"图片生成失败: {tail}"
        return False, f"脚本返回成功但输出文件无效: {output}"
    finally:
        try:
            os.remove(prompt_file)
        except OSError:
            pass


def _parse_last_json(text):
    """从一段输出里取最后一个 JSON 对象行（generate-image.js 末行是机器可读 JSON）。"""
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def generate_images(prompt, output, count, aspect_ratio="16:9", provider="auto", verbose=True):
    """生成 N 张图（同一个 prompt，-n 张不同的图）。返回 (ok, paths_or_msg)。

    count<=1 时退回单图 generate_image（保留 codex 兜底）。count>1 时调
    generate-image.js --count N，解析末行 JSON 的 outputs 拿到全部产物路径。
    只要至少有一张成功即视为成功，paths 为成功列表。
    """
    if count <= 1:
        ok, res = generate_image(prompt, output, aspect_ratio, provider, verbose)
        return (ok, [res] if ok else res)

    if not os.path.exists(GENERATE_IMAGE_JS):
        return False, f"找不到图片生成脚本: {GENERATE_IMAGE_JS}"

    prompt_fd, prompt_file = tempfile.mkstemp(suffix=".md", prefix="feishu-prompt-")
    try:
        with os.fdopen(prompt_fd, "w", encoding="utf-8") as f:
            f.write(f'---\naspect_ratio: "{aspect_ratio}"\n---\n\nPROMPT:\n{prompt}\n')

        cmd = [
            "node", GENERATE_IMAGE_JS,
            "--prompt-file", prompt_file,
            "--output", output,
            "--aspect-ratio", aspect_ratio,
            "--provider", provider,
            "--count", str(count),
        ]
        if verbose:
            print(f"🎨 生成 {count} 张图片中... (provider={provider}, ar={aspect_ratio})")

        result = subprocess.run(cmd, capture_output=True, text=True)
        data = _parse_last_json(result.stdout)
        outputs = [p for p in (data.get("outputs") if data else []) if p and os.path.exists(p)]

        if outputs:
            # 归档一次 prompt（N 张共用同一 prompt）
            archived = archive_prompt(prompt, aspect_ratio, provider)
            if archived and verbose:
                print(f"📝 Prompt 已归档: {os.path.basename(archived)}")
            # 归档 N 张图：YYYYMMDD-NN-1.png ... -N.png（与 prompt md 同前缀）
            img_archived = archive_images(outputs, archived)
            if img_archived and verbose:
                print(f"🖼️  图片已归档: {len(img_archived)} 张 → prompts/images/")
            if len(outputs) < count and verbose:
                print(f"⚠️  请求 {count} 张，实际成功 {len(outputs)} 张，继续用已成功的图发送。")
            return True, outputs

        tail = (result.stderr or result.stdout).strip()[-300:]
        return False, f"图片生成失败（{count} 张均未产出）: {tail}"
    finally:
        try:
            os.remove(prompt_file)
        except OSError:
            pass


def upload_image(image_path, identity="bot", dry_run=False):
    """把本地图片上传一次，拿到可复用的 image_key（img_xxx）。返回 (ok, key_or_msg)。

    为什么：原先每个目标都重新上传同一张图（N 个目标 = N 次上传），
    现在上传一次、把 image_key 复用到所有目标，省掉 N-1 次上传。
    注意：图片上传是 bot-only 接口。
    """
    if dry_run:
        return True, "img_dryrun_placeholder"

    image_dir = os.path.dirname(os.path.abspath(image_path))
    image_name = os.path.basename(image_path)
    cmd = [
        "lark-cli", "im", "images", "create", "--as", "bot",
        "--data", '{"image_type":"message"}',
        "--file", f"image={image_name}",
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=image_dir)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip()
    try:
        data = json.loads(result.stdout)
        key = data.get("data", {}).get("image_key")
    except (ValueError, AttributeError):
        key = None
    if not key:
        return False, f"上传成功但未解析到 image_key: {result.stdout.strip()[:200]}"
    return True, key


def _build_post_content(image_keys, caption=None, prompt=None, copywriting=None, tags=None):
    """构造 post 富文本：一条消息里同时含 N 张图片 + 可复制的文案/标签/prompt。

    Feishu post 文本默认就是可选中复制的——飞书没有"一键复制按钮"的原生能力，
    所以这里把要复制的内容各自做成独立连续段落，用户长按某段即可整段全选复制。
    content 是「段落数组」，每段是「元素数组」。
    image_keys 可以是单个字符串或字符串列表；多图时每张图各占一段，依次排列。

    段落顺序（自媒体发布友好）：
      [N 张图] → [📋 文案+标签合并段（最易整体复制）] → [📝 Prompt 段]
    文案与标签放在 prompt 上方，且合并成一个连续段落，方便长按一次性复制去发帖。
    """
    title = caption if caption else "🎨 AI 生成图片"
    if isinstance(image_keys, str):
        image_keys = [image_keys]
    content = [[{"tag": "img", "image_key": k}] for k in image_keys]

    # 自媒体文案 + 标签：合并成一个独立段落，放在 prompt 上方。
    # 标签统一加 # 前缀，多个空格分隔，拼到文案末尾，让"文案+话题"成为一个
    # 可长按整体复制的连续文本块（飞书无复制按钮，连续段落是最接近一键复制的体验）。
    if copywriting or tags:
        parts = []
        if copywriting:
            parts.append(copywriting.strip())
        if tags:
            tag_line = " ".join(
                t if t.startswith("#") else f"#{t}"
                for t in (tags if isinstance(tags, list) else split_csv(tags))
            )
            if tag_line:
                parts.append(tag_line)
        merged = "\n".join(parts)
        if merged:
            content.append([{"tag": "text", "text": f"📋 文案（长按复制）:\n{merged}"}])

    if prompt:
        content.append([{"tag": "text", "text": f"📝 Prompt: {prompt}"}])
    return {"zh_cn": {"title": title, "content": content}}


def send_post(content, target_id, target_type, identity="bot", dry_run=False):
    """把构造好的 post 富文本发给单个目标。返回 (ok, message)。"""
    cmd = [
        "lark-cli", "im", "+messages-send", "--as", identity,
        "--msg-type", "post", "--content", json.dumps(content, ensure_ascii=False),
    ]
    if target_type == "chat":
        cmd += ["--chat-id", target_id]
    else:
        cmd += ["--user-id", target_id]
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip()

    # dry-run 模式下返回消息预览而不是空的 stdout
    if dry_run:
        return True, f"[DRY-RUN] 消息内容: {json.dumps(content, ensure_ascii=False, indent=2)}"

    return True, result.stdout.strip()


def hint_for_error(msg):
    """对常见错误给出可操作的排查建议。"""
    low = (msg or "").lower()
    if "230002" in msg or "out of the chat" in low:
        return "机器人不在目标群里。请在群设置 → 群机器人 → 添加机器人后重试。"
    if "im:resource" in low or "uploading image" in low:
        # 用户身份发图需要 im:resource:upload，比发文本多一层权限。
        # 实测最稳的做法是改用 bot 身份发图。
        return ("用户身份缺少图片上传权限（im:resource:upload）。发图最稳的做法是改用 --as bot；"
                "若必须用 user，请执行 lark-cli auth login --scope \"im:resource:upload im:resource\" 重新授权。")
    if "send_as_user" in low or "scope" in low:
        return "缺少用户发送权限。改用 --as bot，或为应用开通 im:message.send_as_user 后重新登录。"
    if "open_id" in low or "chat_id" in low or "receive_id" in low:
        return "ID 格式可能有误：用户用 ou_xxx，群聊用 oc_xxx。"
    return None


def send_to_targets(image_paths, user_ids, chat_ids, caption=None, prompt=None,
                    copywriting=None, tags=None, identity="bot", dry_run=False):
    """发送图片（N 张图 + 文案/标签 + 可复制 prompt 合一）给多个目标。返回结果列表。

    image_paths 可以是单个路径或路径列表。多图时合成一条 post 消息（一条多图）。

    优化点：
      1. 每张图只上传一次，image_key 复用到所有目标（省 N_target-1 次上传/张）。
      2. N 张图 + 配文/prompt 合成一条 post 消息（省一半发送请求）。
      3. 多目标并发发送（用线程池，网络 IO 型，吃满并发）。
    """
    if isinstance(image_paths, str):
        image_paths = [image_paths]

    targets = [(uid, "user") for uid in user_ids] + [(cid, "chat") for cid in chat_ids]
    if not targets:
        return []

    # 1) 每张图各上传一次拿 key（图片接口 bot-only，与发送身份无关）
    image_keys = []
    for img in image_paths:
        up_ok, key_or_err = upload_image(img, identity=identity, dry_run=dry_run)
        if not up_ok:
            print(f"  ❌ 图片上传失败 ({os.path.basename(img)}): {key_or_err}")
            hint = hint_for_error(key_or_err)
            if hint:
                print(f"      💡 {hint}")
            return [{"target": t, "type": ty, "ok": False, "message": key_or_err}
                    for t, ty in targets]
        image_keys.append(key_or_err)

    content = _build_post_content(image_keys, caption=caption, prompt=prompt,
                                  copywriting=copywriting, tags=tags)

    # 2) 并发发送同一条 post 到所有目标
    def _one(target):
        target_id, target_type = target
        ok, msg = send_post(content, target_id, target_type, identity, dry_run)
        return {"target": target_id, "type": target_type, "ok": ok, "message": msg}

    max_workers = min(len(targets), 8)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(_one, targets))

    for r in results:
        label = f"{'👤 用户' if r['type'] == 'user' else '👥 群聊'} {r['target']}"
        status = "✅" if r["ok"] else "❌"
        print(f"  {status} {label}")
        if not r["ok"]:
            print(f"      错误: {r['message']}")
            hint = hint_for_error(r["message"])
            if hint:
                print(f"      💡 {hint}")
        elif dry_run and "DRY-RUN" in r["message"]:
            # 在 dry-run 模式下，只显示第一个目标的完整消息内容（避免重复）
            if r == results[0]:
                print(f"\n📋 消息内容预览（首个目标）:")
                # 提取并格式化显示 JSON 内容
                try:
                    import re
                    match = re.search(r'\{.*\}', r["message"], re.DOTALL)
                    if match:
                        content_obj = json.loads(match.group(0))
                        print(json.dumps(content_obj, ensure_ascii=False, indent=2))
                except:
                    pass

    return results


def main():
    parser = argparse.ArgumentParser(
        description="根据 prompt 生成图片并发送到飞书用户/群组（接收人可从 .env 读取）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--prompt", help="图片生成提示词（与 --image 二选一）")
    parser.add_argument("--prompt-file", dest="prompt_file",
                        help="prompt markdown 文件；用于生成图片，或在 --image 模式下附为可复制文本")
    parser.add_argument("--image", help="已有图片路径（提供则跳过生成）；多张用逗号分隔，合成一条多图消息")
    parser.add_argument("--user-ids", help="接收用户 open_id，逗号分隔（覆盖 .env）")
    parser.add_argument("--chat-ids", help="接收群聊 chat_id，逗号分隔（覆盖 .env）")
    parser.add_argument("--caption", help="随图发送的配文（作为 post 标题）")
    parser.add_argument("--copywriting", "--copy", dest="copywriting",
                        help="自媒体平台文案正文，随图附在 prompt 上方（独立段落，方便长按整体复制去发帖）")
    parser.add_argument("--tags", help="自媒体标签，逗号分隔（自动加 #），拼到文案末尾一起发")
    parser.add_argument("--no-prompt-caption", action="store_true",
                        help="不要把生成 prompt 作为可复制文本附在图片消息里")
    parser.add_argument("--aspect-ratio", default="16:9", help="图片宽高比，默认 16:9")
    parser.add_argument("--count", "-n", type=int, default=1,
                        help="同一个 prompt 生成 N 张不同的图，合成一条多图消息发送（默认 1）")
    parser.add_argument("--provider", default="auto", choices=["auto", "codex", "gemini"],
                        help="图片生成后端，默认 auto")
    parser.add_argument("--output", help="生成图片的保存路径（默认临时文件）")
    parser.add_argument("--as", dest="identity", choices=["bot", "user", "auto"],
                        default=None, help="发送身份，默认读 .env 的 FEISHU_SEND_AS（缺省 bot）")
    parser.add_argument("--dry-run", action="store_true", help="预览，不实际发送")
    args = parser.parse_args()

    print("=" * 50)
    print("🖼️  图片生成 → 飞书推送")
    print("=" * 50)

    if not args.prompt and not args.prompt_file and not args.image:
        print("\n❌ 必须提供 --prompt / --prompt-file（生成图片）或 --image（发送已有图片）")
        sys.exit(1)

    # prompt 文本：命令行 --prompt 优先，否则从 --prompt-file 读取。
    # 这样无论是生成图片还是 --image 直发，都能拿到可复制的 prompt 文本。
    prompt_text = args.prompt
    if not prompt_text and args.prompt_file:
        prompt_text = read_prompt_file(args.prompt_file)
        if not prompt_text:
            print(f"\n❌ 无法从 prompt 文件读取内容: {args.prompt_file}")
            sys.exit(1)

    config = load_env()

    # 接收人：命令行优先，否则用 .env
    user_ids = split_csv(args.user_ids) if args.user_ids is not None else config["feishu_user_ids"]
    chat_ids = split_csv(args.chat_ids) if args.chat_ids is not None else config["feishu_chat_ids"]

    if not user_ids and not chat_ids:
        print("\n❌ 未指定任何接收人。请用 --user-ids/--chat-ids 指定，")
        print("   或在 .env 中配置 FEISHU_USER_IDS / FEISHU_CHAT_IDS。")
        sys.exit(1)

    identity = args.identity or config["feishu_send_as"]

    # 1) 获取图片（image_paths 始终是列表）
    if args.image:
        image_paths = split_csv(args.image)
        missing = [p for p in image_paths if not os.path.exists(p)]
        if missing:
            print(f"\n❌ 图片不存在: {', '.join(missing)}")
            sys.exit(1)
        print(f"\n📁 使用已有图片: {len(image_paths)} 张")
    else:
        count = max(1, args.count or 1)
        output = args.output or os.path.join(
            tempfile.gettempdir(),
            f"feishu-image-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png",
        )
        print()
        ok, result = generate_images(prompt_text, output, count, args.aspect_ratio, args.provider)
        if not ok:
            print(f"\n❌ {result}")
            sys.exit(1)
        image_paths = result
        total_kb = sum(os.path.getsize(p) for p in image_paths) // 1024
        print(f"✅ 已生成 {len(image_paths)} 张图片 (共 {total_kb} KB)")
        for p in image_paths:
            print(f"   - {p}")

    # 2) 发送
    total = len(user_ids) + len(chat_ids)
    print(f"\n📤 推送到 → {len(user_ids)} 个用户 + {len(chat_ids)} 个群聊 "
          f"（身份: {identity}，{len(image_paths)} 张图）{'（预览模式）' if args.dry_run else ''}")
    if args.caption:
        print(f"   配文: {args.caption}")
    if args.copywriting:
        print(f"   文案: {args.copywriting[:50] + '…' if len(args.copywriting) > 50 else args.copywriting}")
    if args.tags:
        print(f"   标签: {' '.join('#' + t for t in split_csv(args.tags))}")

    # 把生成 prompt 作为可复制文本附在图片消息里（除非显式 --no-prompt-caption）。
    # prompt_text 来自 --prompt 或 --prompt-file，因此 --image 直发也能附带 prompt。
    attach_prompt = prompt_text if (prompt_text and not args.no_prompt_caption) else None

    if args.dry_run:
        print(f"\n🔍 调试信息:")
        print(f"   图片路径({len(image_paths)}): {', '.join(image_paths)}")
        print(f"   配文: {args.caption or '(无)'}")
        print(f"   文案: {args.copywriting or '(无)'}")
        print(f"   标签: {' '.join('#' + t for t in split_csv(args.tags)) if args.tags else '(无)'}")
        print(f"   Prompt文本: {attach_prompt[:100] + '...' if attach_prompt and len(attach_prompt) > 100 else attach_prompt or '(无)'}")
        print(f"   --prompt-file: {args.prompt_file or '(未提供)'}")
        print(f"   --no-prompt-caption: {args.no_prompt_caption}")
    print()

    results = send_to_targets(image_paths, user_ids, chat_ids,
                              caption=args.caption, prompt=attach_prompt,
                              copywriting=args.copywriting, tags=args.tags,
                              identity=identity, dry_run=args.dry_run)

    # 3) 汇总
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = total - ok_count
    print(f"\n{'─' * 50}")
    print(f"推送完成: {ok_count} 成功, {fail_count} 失败 (共 {total} 个目标)")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
