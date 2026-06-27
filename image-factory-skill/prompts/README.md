# Prompts 归档目录

本目录存放每次图片生成时使用的 prompt，便于后续统一分类、复用与整理。

## 命名规范

```
YYYYMMDD-NN.md
```

- `YYYYMMDD`：生成日期（如 `20260625`）
- `NN`：当天的序号，从 `01` 起递增（两位补零）

例如 `20260625-03.md` 表示 2026 年 6 月 25 日当天的第 3 个 prompt。

## 文件格式

每个归档文件含 frontmatter 元信息 + PROMPT 正文：

```markdown
---
aspect_ratio: "9:16"
provider: codex
timestamp: 2026-06-25T13:07:12.622098
---

PROMPT:
<完整的生成提示词>
```

## 自动归档

`scripts/send_feishu_image.py` 在每次成功生成图片后，会自动把 prompt 归档到此目录
（由 `archive_prompt()` 完成）。无需手动维护序号。

直接复用某个归档 prompt 重新生成/发送：

```bash
python scripts/send_feishu_image.py --prompt-file prompts/20260625-01.md
```
