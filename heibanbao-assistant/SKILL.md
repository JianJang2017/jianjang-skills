---
name: heibanbao-assistant
description: 根据主题制作中小学黑板报方案，交付可直接誊写的 Markdown 排版稿和真实生成的黑板效果图。适用于班级活动、节日、校园文化与安全教育等黑板报需求。
---

# 黑板报助手

把用户的主题和附加要求做成一套能落地的黑板报。每套方案交付 `.md` 排版稿和 **3840 × 2160、16:9 的高清 `.png` 效果图**；效果图必须由本技能脚本实际生成，并在回复中给出文件链接。所有产物保存在本技能目录的 `release/<主题>/` 中，按主题分包；用户要求多套时，在该主题目录下以方案名分包。

## 输入与取舍

- 主题必需；未给主题时询问。其余信息可推断：默认小学高年级、4 个板块、简约卡通、文字图画均衡、黑板 3.6 × 1.2 米。已给出的年级、尺寸、风格、板块数、字数、配色、禁用元素和侧重点优先。
- 模糊的非关键参数用默认值完成，不因缺少年级或色彩而停下。只有相互冲突的硬性要求会导致不可执行时才询问。
- 小学低年级少字多图，初高中可适当增加内容深度。安全知识须准确；有现实风险的具体建议要核实，不编造法规或名言来源。
- 文字以粉笔手写可容纳为限。先分配画面空间，再定字数；宁可精简文案，不缩到难以辨认。

## 制作与交付

1. 先确定本技能 `SKILL.md` 所在的真实目录，创建 `release/<主题>/`；主题目录名使用简短、可辨认的主题文字，去掉路径分隔符等非法字符。调用技能时无论当前工作目录在哪里、是否经软连接调用，产物都写入这个 `release`。同一主题有多套方案时用 `release/<主题>/<方案名>/`。编写 `方案.md`，标题与模块依次为：**黑板报标题**、**整体版面排版规划**、**各板块文字内容**、**绘画 & 插图方案**、**配色方案**、**制作小贴士**。排版规划要写各区域位置、尺寸或占比、用途与边框；文字板块提供可直接誊写的完整正文。
2. 用同一份最终文案制作 `layout.json`，字段见下方。板块的标题、正文、顺序必须与 Markdown 一致。默认网格版块可加 `illustration` 字段，支持 `book`、`torch`、`footprints`、`sprout`、`camera`、`microphone`、`pen`、`newspaper` 简笔画；空间不足时脚本会省略插图。用户不想要四宫格时，可设 `layout: "story"`，使用左侧主画面、右侧两段知识和底部观察条，需恰好四段文案。运行本地 `scripts/render-board.py` 产出 `效果图.png`。该脚本把确切文案排到 16:9 的 4K 画布上，并在内容溢出时报错；遇到溢出先压缩文案或调整板块，再同步更新两份文件并重新生成。版面规划可写实物黑板尺寸，效果图统一使用 16:9 展示比例。
3. 如果环境已有生图后端且用户希望画面更丰富，可用本技能自带的 `scripts/generate-image.js` 生成**无字粉笔装饰背景**，并把其绝对或相对路径写进 `layout.json` 的 `backgroundImage`，再重新运行排版脚本。生图提示词须要求纯黑板材质、边角简笔画装饰、中央留白、没有任何字母数字或文字。最终标题和正文仍由排版脚本绘制，不能让图像模型自行书写正文。
4. 查看生成的图片，核对主标题、板块顺序、文字没有裁切、颜色在黑板上可读，以及画面与 Markdown 一致。完成后回复两个文件链接和一句方案说明。不得把提示词或尚未生成的路径当作效果图。

`layout.json` 最小结构：

```json
{
  "title": "主标题",
  "subtitle": "可选副标题",
  "style": "简约卡通",
  "colors": { "main": "#86d7ee", "accent": "#ffd878", "text": "#f4f1e8" },
  "sections": [
    { "title": "板块一", "body": "可直接誊写的正文。" },
    { "title": "板块二", "body": "可直接誊写的正文。" }
  ]
}
```

运行示例：

```bash
python3 heibanbao-assistant/scripts/render-board.py --input heibanbao-assistant/release/消防安全/layout.json --output heibanbao-assistant/release/消防安全/效果图.png
node heibanbao-assistant/scripts/generate-image.js --prompt-file heibanbao-assistant/release/消防安全/背景提示词.md --output heibanbao-assistant/release/消防安全/粉笔背景.png --aspect-ratio 16:9 --provider qwen --retries 0
```

生图脚本与所需 Qwen、百炼后端代码已复制在本技能的 `scripts/` 中，运行不依赖另一个技能目录。`--provider` 可选 `qwen`、`bl`、`codex`、`gemini`；仅在相应凭据或命令可用时使用。Qwen 读取 `DASHSCOPE_API_KEY` 环境变量或本技能目录的 `.env`；不要把密钥写进排版稿、提示词或提交文件。PNG 排版脚本需要 Python 3 和 Pillow；没有可用生图后端时，直接交付由排版脚本生成的真实 PNG 效果图。
