# Markdown 转 HTML 排版

[English](./README_EN.md)

把一篇 Markdown 文档转换成**排版精美、可直接粘贴到微信公众号编辑器或邮件客户端**的 HTML。

核心约束：所有样式全部内联在 `style="..."` 属性里，不依赖 `<style>` 块、外部样式表或 `class` 选择器——因为公众号编辑器和多数邮件客户端会把这些统统丢掉，只保留内联样式。产出全内联、680px 移动端容器的完整 HTML。

## 它能做什么

- 读一篇 Markdown（文件路径或直接给文本），逐元素映射成主题组件，拼成成品 HTML
- 内置 **40 套主题**（包含原创精品主题 + markdown2wechat 移植主题），可由用户点名套用，也能根据正文内容和气质自动推荐
- 代码块用 `&nbsp;`/`<br>` 渲染（不用 `<pre>`，避免公众号折叠空白）
- 表格、引用、列表、图片、语义化卡片等都按主题样式渲染
- 自带校验脚本，交付前检查有没有会"掉样式"的写法

## 快速上手

技能会在你提出排版需求时自动触发，典型说法：

```
把 ~/notes/读书笔记.md 排版成公众号文章
这段 markdown 帮我转成好看的 HTML，用「青格笔记」主题
把这篇技术文章美化成网页，能直接贴进公众号编辑器
换个主题风格重新排一下这篇 md
```

输出默认写到源文件同目录的同名 `.html`，并在回复里说明用了哪套主题、为什么。

## 主题一览

主题分两类。**题材型**为特定文体设计，**风格型**对题材中立、靠"气质"匹配。没点名主题时，技能优先按题材匹配，落不进去就从风格型里挑最贴气质的一套。

### 题材型

| 主题 | 名称 | 适用 |
| --- | --- | --- |
| `native-blueprint` | 原生蓝图 | AI-Native、软件工程范式、技术战略、架构方法论、长篇技术分析。黑白正文 + 浅蓝荧光标题 + 深色代码框 |
| `cyan-grid` | 青格笔记 | 备考计划、学习复盘、资料清单、知识整理、教程笔记。浅青网格纸背景 + 青色标题 + 清爽表格 |

### 风格型（不绑定题材）

#### 原创精品主题

| 主题 | 名称 | 气质 |
| --- | --- | --- |
| `minimal-ink` | 极简墨色 | 米白纸面、墨色正文、克制留白，适合安静慢读的长文 |
| `vintage-magazine` | 复古杂志 | 复古纸张、强标题、期刊眉标，纸媒质感与叙事节奏 |
| `noir-stage` | 黑金舞台 | 深色页面、金色高光、聚光灯式重点，仪式感与强停顿 |
| `notebook-sticky` | 手账便签 | 暖纸、虚线边框、便签高亮，亲近轻松的手账质感 |
| `warm-order` | 暖白秩序 | 暖白页面、低饱和橙色强调、规则卡片，平静可信 |
| `bluegray-brief` | 蓝灰简报 | 蓝灰页面、严谨边框、大号关键数字，紧凑冷静的摘要感 |
| `cool-blueprint` | 冷感蓝图 | 冷白页面、蓝色信号色、工程感信息块，秩序与可扫描性 |
| `green-editorial` | 森绿编辑 | 浅绿页面、编辑部式标题、侧边强调线，清新有组织 |

#### markdown2wechat 移植主题（m2w-系列）

新增 30 套从 markdown2wechat 项目移植的主题，前缀 `m2w-` 避免命名冲突。涵盖多种色系和风格：

| 主题 | 名称 | 色系/风格 |
| --- | --- | --- |
| `m2w-simple` | 简 | 简洁白底、轻装饰 |
| `m2w-geek-black` | 极客黑 | 暗黑、强代码感 |
| `m2w-obsidian` | 黑曜石 | 深色主题 |
| `m2w-minimal-black` | 极简黑 | 黑色主题 |
| `m2w-night-purple` | 夜幕紫 | 紫色夜色系 |
| `m2w-brilliant-purple` | 荧光紫 | 明亮紫色 |
| `m2w-rose-purple` | 玫瑰紫 | 玫瑰紫色 |
| `m2w-vivid-blue` | 灵动蓝 | 轻快蓝色 |
| `m2w-luminous-blue` | 极光蓝 | 蓝色主题 |
| `m2w-tech-blue` | 科技蓝 | 科技感蓝色 |
| `m2w-fullstack-blue` | 全栈蓝 | 蓝色技术风 |
| `m2w-orange-blue` | 橙蓝对撞 | 橙蓝对比 |
| `m2w-soft-green` | 柔和绿 | 柔和绿色 |
| `m2w-greenery` | 新绿 | 清新绿色 |
| `m2w-prairie-green` | 草原绿 | 草原绿色 |
| `m2w-tender-cyan` | 嫩青 | 青色主题 |
| `m2w-orchid-cyan` | 兰青 | 兰青色 |
| `m2w-cupid-busy` | 丘比特忙 | 粉色主题 |
| `m2w-soft-pink` | 柔粉 | 柔和粉色 |
| `m2w-lemon-yellow` | 柠檬黄 | 黄色主题 |
| `m2w-yamabuki` | 山吹黄 | 日式黄色 |
| `m2w-pornhub-yellow` | PH黄 | 黄黑对比 |
| `m2w-orange-heart` | 橙心 | 橙色主题 |
| `m2w-scarlet` | 绯红 | 红色主题 |
| `m2w-double-shadow` | 双重影 | 双色影子 |
| `m2w-frontend-peak` | 前端之峰 | 前端风格 |
| `m2w-weformat` | 微信式 | 微信风格 |
| `m2w-smartisan-note-v2` | 锤子便签 | 便签风格 |
| `m2w-singularity` | 奇点 | 科幻风格 |
| `m2w-yanqi-lake` | 雁栖湖 | 自然风格 |

使用示例：`把这篇文章用 m2w-geek-black 主题排版` 或 `换成 m2w-rose-purple 风格`



## 目录结构

```
markdown-to-html/
├── SKILL.md                      # 技能核心指令
├── README.md                     # 本文档
├── scripts/
│   ├── escape_code.py            # 代码块转义为 &nbsp;/<br> 内联片段
│   └── validate_html.py          # 校验有无会掉样式的写法（<style>/class/缺 charset）
├── references/themes/
│   ├── theme-<名字>.md           # 每套主题的组件库（页面外壳 + 各组件 HTML 片段）
│   └── examples/<名字>.html      # 每套主题的完整范例文章
└── evals/
    ├── evals.json                # 测试用例
    └── inputs/                   # 测试输入 markdown
```

## 辅助脚本

```bash
# 代码块/流程图转成内联 HTML 片段（HTML 转义 + 空格转 &nbsp; + 换行转 <br>）
python3 scripts/escape_code.py --in snippet.txt
cat snippet.txt | python3 scripts/escape_code.py

# 校验生成的 HTML 能否直接粘贴（报出 <style>/class/缺 charset 等问题）
python3 scripts/validate_html.py output.html
python3 scripts/validate_html.py output.html --strict   # 有告警也判失败
```

## 扩展主题

新增一套主题，无需改 `SKILL.md`：

1. 在 `references/themes/` 加一份 `theme-<名字>.md`，沿用现有结构——首行一句话写明适用场景或视觉定位（题材型写"适用于……"，风格型写"视觉定位：……，不绑定任何文章题材"），再给设计令牌、页面外壳、各组件 HTML 片段。
2. 在 `references/themes/examples/` 放一篇同名 `<名字>.html` 范例。

技能会自动扫描并支持新主题。
