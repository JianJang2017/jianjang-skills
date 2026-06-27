#!/usr/bin/env python3
"""飞书/Lark 配置加载模块。

从 .env 读取本 skill 需要的飞书信息，避免每次调用都让用户重复指定：
目标知识库、默认身份（user/bot）、品牌，以及可选的应用凭证（App ID/Secret）。

设计要点（与 enterprise-email-manager/email_config.py 保持一致）：
- 凭证只从环境 / .env 读取，绝不把 APP_SECRET / token 明文打印到终端。
- 输出 JSON 时对密钥做掩码（****），方便 skill 工作流直接读取而不泄密。
- .env 已被仓库根 .gitignore 忽略，不会提交。

用法：
    python3 feishu_config.py            # 打印当前配置（密钥掩码）
    python3 feishu_config.py --check    # 仅校验，缺关键项时非零退出
"""

from __future__ import annotations

import json
import os
import sys


def _mask(value):
    """对密钥类字段掩码：只保留判断"是否已配置"所需信息，不泄露明文。"""
    if not value:
        return ""
    return "****"


def load_env(env_path=None):
    """加载 .env 中的配置到 os.environ。

    查找顺序：
    1. 显式传入路径
    2. skill 根目录（此脚本所在目录的上一级）
    3. 当前工作目录 -> 逐级向上查找最多 6 层

    优先从 skill 根目录找 .env（因为配置文件通常放在那里），
    这样无论从哪个工作目录运行都能找到。
    不覆盖已存在的真实环境变量（环境变量优先级高于 .env）。
    """
    if env_path is None:
        # 1. 优先查找 skill 根目录（此脚本所在的上一级目录）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        skill_root = os.path.dirname(script_dir)
        skill_env = os.path.join(skill_root, ".env")
        if os.path.exists(skill_env):
            env_path = skill_env
        else:
            # 2. 回退到从当前工作目录向上查找
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
                os.environ.setdefault(key, value)
    return env_path


def get_config(env_path=None):
    """读取配置并返回 dict。"""
    loaded_from = load_env(env_path)

    as_identity = (os.environ.get("FEISHU_AS", "user") or "user").strip().lower()
    if as_identity not in ("user", "bot"):
        as_identity = "user"
    brand = (os.environ.get("FEISHU_BRAND", "feishu") or "feishu").strip().lower()
    if brand not in ("feishu", "lark"):
        brand = "feishu"

    config = {
        # 应用凭证（可选）：缺省时沿用 lark-cli 已有的 ~/.lark-cli/config.json
        "app_id": os.environ.get("FEISHU_APP_ID", ""),
        "app_secret": os.environ.get("FEISHU_APP_SECRET", ""),
        "brand": brand,
        # 默认身份：知识库/文档是个人资源，默认 user
        "as_identity": as_identity,
        # 默认目标知识库：三选一（优先级 space_id > wiki_url > space_name）
        "space_id": os.environ.get("FEISHU_SPACE_ID", "").strip(),
        "wiki_url": os.environ.get("FEISHU_WIKI_URL", "").strip(),
        "space_name": os.environ.get("FEISHU_SPACE_NAME", "").strip(),
        # 可选：迁入时挂到的父节点
        "parent_node_token": os.environ.get("FEISHU_PARENT_NODE_TOKEN", "").strip(),
    }
    config["_env_path"] = loaded_from
    config["_has_app_credentials"] = bool(config["app_id"] and config["app_secret"])
    # 用户是否在 .env 里预设了目标知识库（否则走"自动新建"流程）
    config["_has_target_space"] = bool(
        config["space_id"] or config["wiki_url"] or config["space_name"]
    )
    return config


def safe_config(config):
    """返回掩码后的副本，可安全打印到终端 / 日志。"""
    out = dict(config)
    out["app_secret"] = _mask(config.get("app_secret"))
    return out


def main(argv):
    check_only = "--check" in argv
    config = get_config()

    if check_only:
        # 本 skill 不强制要求 .env 里有任何字段（凭证可走 lark-cli 既有配置，
        # 目标库可在对话里临时指定）。这里只在"配了应用凭证但不完整"时报错。
        if config["app_id"] and not config["app_secret"]:
            sys.stderr.write(
                "错误：.env 配置了 FEISHU_APP_ID 但缺少 FEISHU_APP_SECRET。\n"
            )
            sys.exit(1)
        if config["app_secret"] and not config["app_id"]:
            sys.stderr.write(
                "错误：.env 配置了 FEISHU_APP_SECRET 但缺少 FEISHU_APP_ID。\n"
            )
            sys.exit(1)
        sys.exit(0)

    print(json.dumps(safe_config(config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
