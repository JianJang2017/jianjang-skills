# prompts/ — 生成归档库

每次成功生图都会自动把 **prompt（含 frontmatter）+ 生成出来的图片** 落盘到这里，
方便后期检索、复用、规整。归档是**辅助能力**：复制失败只警告、不阻塞发送/发布主流程。

## 目录结构

```
prompts/
├── YYYYMMDD-NN.md                 ← prompt 正文 + frontmatter
└── images/
    ├── YYYYMMDD-NN.png            ← 单图（--count 1）
    ├── YYYYMMDD-NN-1.png          ← 多图（--count >=2），第 1 张
    ├── YYYYMMDD-NN-2.png          ← 多图，第 2 张
    └── YYYYMMDD-NN-N.png          ← ...
```

## 命名规则

- `YYYYMMDD` — 生成当天的日期，例如 `20260630`
- `NN` — 当天的序号，从 `01` 起，零填充两位
- prompt md 和它的图片**共享 `YYYYMMDD-NN` 前缀**，是显式的"一一配对"关系
- 多图（`--count N`）才会带 `-1..-N` 后缀；单图就用裸文件名（更易辨认是哪条 prompt 的图）

序号是按当天 `prompts/*.md` 已有最大值 +1 推出来的，无需手动管理。

## prompt 文件长什么样

```yaml
---
aspect_ratio: "3:4"
provider: codex
timestamp: 2026-06-30T18:07:52.123456
---

PROMPT:
<完整 prompt 正文，可多段；技能用 \Z（字符串末尾）而非 $（行末）解析，多段不会被截断>
```

frontmatter 里的 `aspect_ratio` / `provider` 是生图当时的参数，回放时可以照原样复刻。

## 复用归档过的 prompt

直接把归档文件路径丢给三个发布入口任一个即可：

```bash
# 重新发飞书（同一条 prompt，新一轮生图）
python scripts/send_feishu_image.py --prompt-file prompts/20260630-04.md --count 3

# 重新发小红书
node scripts/publish_xiaohongshu.js --prompt-file prompts/20260630-04.md

# 重新发抖音
node scripts/publish_douyin.js --prompt-file prompts/20260630-04.md
```

也可以喂给 `optimize-prompt.js` 改写风格、再生新图；详见 SKILL.md 的"Common pipelines"段。

## 常用查询

```bash
# 看某天的所有 prompt
ls prompts/20260630-*.md

# 看某条 prompt 对应的所有图
ls prompts/images/20260630-04-*.*    # 多图
ls prompts/images/20260630-04.*      # 单图

# 一条 prompt 的所有产出（md + 图）
ls prompts/20260630-04.* prompts/images/20260630-04*

# 统计：今天生成了多少张图
ls prompts/images/$(date +%Y%m%d)*.png 2>/dev/null | wc -l
```

## 哪些入口会自动归档

| 入口 | prompt md | 图片 |
|------|-----------|------|
| `send_feishu_image.py`（生成模式）| ✅ | ✅ |
| `publish_xiaohongshu.js --prompt`/`--prompt-file` | ✅ | ✅ |
| `publish_douyin.js --prompt`/`--prompt-file` | ✅ | ✅ |
| `reverse-prompt.js --archive` | ✅（source: reverse）| —（反推只产出 prompt）|
| `optimize-prompt.js --archive` | ✅（source: optimize）| —（优化只产出 prompt）|
| `generate-portrait-prompt.js --archive` | ✅（source: portrait）| —（仅产出 prompt）|
| `--image` 模式发送已有图 | ❌（没有新 prompt）| ❌（不是本次生成的）|

> 反推 / 优化 / 人物 prompt 这三类脚本的 frontmatter 会带 `source: reverse|optimize|portrait`
> 标记，方便后期区分"原始生成 prompt"和"派生 prompt"。

## 边界情况

- **codex 兜底捞图**：生图脚本失败/超时但 codex 已落盘时，兜底捞回的图也会被归档（同套命名）
- **N 张图部分失败**：比如请求 3 张实际 2 张成功，只会归档成功那 2 张（`-1`/`-2`），不留空位
- **归档目录写不进去**：仅警告，主流程（发送/发布）正常继续 — 归档绝不阻塞业务路径
- **重名冲突**：当天序号是按 `prompts/*.md` 最大值递推的，正常使用下不会冲突；
  手动改名时注意保持 `YYYYMMDD-NN` 前缀对齐 md 文件，否则后期检索就乱了
