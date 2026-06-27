#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_with_images.py — 导入本地 Markdown 到飞书知识库(Wiki)，并把图片放到正确位置。

实现「方案一」的等价能力（基于 lark-cli 原生命令编排，已端到端验证）：
  1. 解析 MD 内所有图片（本地相对/绝对路径 + 外网 http/https）。
  2. 把每张图片替换成唯一文本占位符（marker），外网图片先下载到本地临时目录。
  3. 在目标知识库新建 Wiki 节点（空 docx），或写入已有文档。
  4. 以 markdown 形式 append 带 marker 的正文。
  5. 逐张图片执行 `docs +media-insert --file <本地图> --selection-with-ellipsis "<marker>" --before`，
     该命令内部完成「建空 image block → 上传素材 → 绑定 token」三步并自动回滚。
  6. 删除所有 marker 占位段落。
  7. 输出文档 URL。

为什么用 marker 占位法而不是「导入后替换空 image block」：
  飞书原生 markdown 导入只会自动下载**网络 URL** 图片，本地路径图片会被直接丢弃，
  不会生成空 image block。marker 占位 + media-insert 定位是经验证 100% 命中的方案。

依赖：已 `lark-cli auth login` 完成认证（user 身份）。本脚本不读取 app secret，全程走 lark-cli。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
import urllib.request

# 复用同目录下的配置加载（.env -> space_id / as_identity 等）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import feishu_config
except Exception:
    feishu_config = None

IMG_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def run_lark(args, retries=3, timeout=120):
    """运行 lark-cli 命令，返回 (ok, parsed_json_or_text)。带网络瞬时错误重试。"""
    last = None
    for attempt in range(1, retries + 1):
        try:
            proc = subprocess.run(
                ["lark-cli"] + args,
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            last = {"ok": False, "error": {"type": "network", "subtype": "timeout"}}
            log(f"  ⏱  超时，重试 {attempt}/{retries} ...")
            time.sleep(3)
            continue
        out = proc.stdout.strip()
        # lark-cli 把进度打到 stderr，JSON 结果在 stdout；取最后一个 JSON 对象
        parsed = _extract_json(out)
        if parsed is None:
            parsed = _extract_json(proc.stderr.strip())
        if parsed is not None:
            ok = bool(parsed.get("ok", proc.returncode == 0))
            if ok:
                return True, parsed
            err = parsed.get("error", {})
            if err.get("type") == "network" or err.get("subtype") == "timeout":
                last = parsed
                log(f"  ⏱  网络瞬时错误，重试 {attempt}/{retries} ...")
                time.sleep(3)
                continue
            return False, parsed
        # 无 JSON：按 returncode 判定
        if proc.returncode == 0:
            return True, {"ok": True, "_raw": out}
        last = {"ok": False, "_raw": (proc.stderr or out)}
        time.sleep(2)
    return False, last or {"ok": False, "error": {"type": "unknown"}}


def _extract_json(text):
    """从混合输出里抽取最后一个完整的顶层 JSON 对象。"""
    if not text:
        return None
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        chunk = text[start:i + 1]
                        try:
                            return json.loads(chunk)
                        except json.JSONDecodeError:
                            break
        start = text.find("{", start + 1)
    return None


def parse_and_markerize(md_text, base_dir, temp_dir):
    """把 MD 里每张图片替换成唯一 marker，返回 (new_md, images)。

    images: [{marker, alt, original_src, local_path, is_remote, ok}]
    外网图片在此处下载到 temp_dir；下载失败的图片保留原 markdown（不丢内容）。
    """
    images = []
    counter = {"n": 0}

    def repl(m):
        alt = m.group(1)
        src = m.group(2).strip()
        idx = counter["n"]
        counter["n"] += 1
        is_remote = src.startswith("http://") or src.startswith("https://")
        local_path = None
        ok = True
        if is_remote:
            local_path = _download(src, temp_dir, idx)
            if not local_path:
                ok = False
        else:
            local_path = src if os.path.isabs(src) else os.path.normpath(os.path.join(base_dir, src))
            if not os.path.exists(local_path):
                log(f"  ⚠️  本地图片不存在，保留原引用: {local_path}")
                ok = False
        if not ok:
            # 保留原始 markdown 图片语法，避免丢失内容
            return m.group(0)
        marker = f"FEISHU-IMG-{idx}-{uuid.uuid4().hex[:8]}"
        images.append({
            "marker": marker, "alt": alt, "original_src": src,
            "local_path": local_path, "is_remote": is_remote, "ok": True,
        })
        # 占位段落需独占一行，便于后续按文本唯一定位
        return marker

    new_md = IMG_PATTERN.sub(repl, md_text)
    return new_md, images


def _download(url, temp_dir, idx):
    try:
        ext = os.path.splitext(url.split("?")[0])[1] or ".png"
        if len(ext) > 5:
            ext = ".png"
        dest = os.path.join(temp_dir, f"remote_{idx}{ext}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        log(f"  ⬇️  已下载外网图片: {url[:60]}... -> {os.path.basename(dest)}")
        return dest
    except Exception as e:
        log(f"  ⚠️  外网图片下载失败({e})，保留原引用: {url[:60]}...")
        return None


def create_wiki_node(space_id, title, parent_node_token, as_identity):
    args = ["wiki", "+node-create", "--space-id", space_id,
            "--title", title, "--obj-type", "docx", "--as", as_identity, "--json"]
    if parent_node_token:
        args += ["--parent-node-token", parent_node_token]
    ok, data = run_lark(args)
    if not ok:
        return None
    d = data.get("data", {})
    return {"node_token": d.get("node_token"), "doc_id": d.get("obj_token"),
            "url": d.get("url"), "title": d.get("title")}


def append_markdown(doc_id, md_text, temp_dir, as_identity):
    """以 markdown append 正文。--content @file 仅接受 cwd 下相对路径，故写到 cwd 临时文件。"""
    tmp_name = f"._feishu_md_{uuid.uuid4().hex[:8]}.md"
    tmp_path = os.path.join(os.getcwd(), tmp_name)
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        ok, data = run_lark([
            "docs", "+update", "--api-version", "v2", "--doc", doc_id,
            "--command", "append", "--doc-format", "markdown",
            "--content", f"@{tmp_name}", "--as", as_identity, "--json",
        ])
        return ok, data
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def insert_image_at_marker(doc_id, image, as_identity):
    # lark-cli 的 --file 要求「cwd 下的相对路径」，绝对路径/外部路径会报 unsafe file path。
    # 因此把图片暂存到 cwd 根目录下的唯一相对文件，插入后再删。
    import shutil
    ext = os.path.splitext(image["local_path"])[1] or ".png"
    rel_name = f"._feishu_img_{uuid.uuid4().hex[:8]}{ext}"
    staged = os.path.join(os.getcwd(), rel_name)
    try:
        shutil.copyfile(image["local_path"], staged)
        ok, data = run_lark([
            "docs", "+media-insert", "--doc", doc_id,
            "--file", rel_name,
            "--selection-with-ellipsis", image["marker"],
            "--before", "--align", "center", "--as", as_identity, "--json",
        ] + (["--caption", image["alt"]] if image["alt"] else []))
        return ok, data
    finally:
        try:
            os.remove(staged)
        except OSError:
            pass


def fetch_block_ids_for_markers(doc_id, markers, as_identity):
    """fetch with-ids(XML)，找出每个 marker 所在段落 block_id。"""
    proc = subprocess.run(
        ["lark-cli", "docs", "+fetch", "--api-version", "v2", "--doc", doc_id,
         "--detail", "with-ids", "--as", as_identity, "--json"],
        capture_output=True, text=True, timeout=120,
    )
    # 必须解析 JSON 取出未转义的 content，否则原始 stdout 里引号是 \" ，正则匹配不到
    parsed = _extract_json(proc.stdout) or _extract_json(proc.stderr)
    xml = _find_content(parsed) if parsed else ""
    if not xml:
        xml = proc.stdout + proc.stderr
    found = {}
    for marker in markers:
        m = re.search(r'<p id="([^"]+)">' + re.escape(marker) + r'</p>', xml)
        if m:
            found[marker] = m.group(1)
    return found


def _find_content(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get("content"), str):
            return obj["content"]
        for v in obj.values():
            r = _find_content(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_content(v)
            if r:
                return r
    return None


def delete_blocks(doc_id, block_ids, as_identity):
    if not block_ids:
        return True, {"ok": True}
    return run_lark([
        "docs", "+update", "--api-version", "v2", "--doc", doc_id,
        "--command", "block_delete", "--block-id", ",".join(block_ids),
        "--as", as_identity, "--json",
    ])


def main():
    ap = argparse.ArgumentParser(
        description="导入本地 Markdown 到飞书知识库(Wiki)，自动上传并定位图片（方案一等价实现）。")
    ap.add_argument("md", help="本地 Markdown 文件路径")
    ap.add_argument("--space-id", help="目标知识库 space_id（缺省读 .env）")
    ap.add_argument("--title", help="Wiki 节点标题（缺省取 MD 文件名）")
    ap.add_argument("--parent-node-token", help="父节点 token（可选）")
    ap.add_argument("--doc-id", help="写入已有 docx 文档（提供则不新建节点）")
    ap.add_argument("--as", dest="as_identity", help="身份 user|bot（缺省读 .env，默认 user）")
    ap.add_argument("--keep-markers", action="store_true", help="调试用：不删除占位 marker")
    args = ap.parse_args()

    cfg = feishu_config.get_config() if feishu_config else {}
    space_id = args.space_id or cfg.get("space_id")
    as_identity = args.as_identity or cfg.get("as_identity") or "user"
    parent = args.parent_node_token or cfg.get("parent_node_token") or ""

    md_path = os.path.abspath(args.md)
    if not os.path.exists(md_path):
        log(f"❌ MD 文件不存在: {md_path}")
        sys.exit(1)
    base_dir = os.path.dirname(md_path)
    title = args.title or os.path.splitext(os.path.basename(md_path))[0]

    if not args.doc_id and not space_id:
        log("❌ 未指定 --space-id 且 .env 中没有 space_id")
        sys.exit(1)

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    temp_dir = tempfile.mkdtemp(prefix="feishu_img_")
    try:
        log(f"📄 解析 Markdown 与图片: {md_path}")
        new_md, images = parse_and_markerize(md_text, base_dir, temp_dir)
        log(f"   共发现可定位图片 {len(images)} 张")

        # 1) 目标文档
        if args.doc_id:
            doc_id = args.doc_id
            doc_url = f"https://feishu.cn/docx/{doc_id}"
            log(f"📝 写入已有文档: {doc_id}")
        else:
            log(f"🆕 在知识库 {space_id} 新建节点: {title}")
            node = create_wiki_node(space_id, title, parent, as_identity)
            if not node or not node.get("doc_id"):
                log("❌ 新建 Wiki 节点失败")
                sys.exit(1)
            doc_id = node["doc_id"]
            doc_url = node["url"]

        # 2) 写正文（含 marker）
        log("✍️  写入正文（带图片占位符）...")
        ok, data = append_markdown(doc_id, new_md, temp_dir, as_identity)
        if not ok:
            log(f"❌ 写入正文失败: {json.dumps(data, ensure_ascii=False)[:300]}")
            sys.exit(1)

        # 3) 逐张插入图片到 marker 位置
        inserted = 0
        for i, img in enumerate(images, 1):
            log(f"🖼️  [{i}/{len(images)}] 插入图片到位: {os.path.basename(img['local_path'])}")
            ok, data = insert_image_at_marker(doc_id, img, as_identity)
            if ok:
                inserted += 1
            else:
                log(f"   ⚠️  插入失败，保留 marker: {json.dumps(data, ensure_ascii=False)[:200]}")
                img["ok"] = False

        # 4) 删除成功插入的 marker 段落
        if not args.keep_markers:
            markers_to_clear = [im["marker"] for im in images if im.get("ok")]
            if markers_to_clear:
                log("🧹 清理占位符...")
                id_map = fetch_block_ids_for_markers(doc_id, markers_to_clear, as_identity)
                ok, data = delete_blocks(doc_id, list(id_map.values()), as_identity)
                if not ok:
                    log(f"   ⚠️  marker 清理失败: {json.dumps(data, ensure_ascii=False)[:200]}")

        log(f"✅ 完成：图片 {inserted}/{len(images)} 已就位")
        print(json.dumps({
            "ok": True,
            "doc_id": doc_id,
            "url": doc_url,
            "images_total": len(images),
            "images_inserted": inserted,
        }, ensure_ascii=False, indent=2))
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
