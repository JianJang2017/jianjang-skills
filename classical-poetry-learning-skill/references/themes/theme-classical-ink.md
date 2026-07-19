# 古诗词公众号 HTML 主题（古典水墨风）

专为古诗词学习推文设计的公众号可粘贴 HTML 主题，米白纸面、墨色正文、古典雅致，契合古诗词的文化气质，同时保证手机端清晰易读。

## 设计令牌

- 页面背景：`#f5f1e8`（宣纸米黄）
- 容器背景：`#fbf8f1`（暖白纸面）
- 正文文字：`#2f2b26`（墨色）
- 弱化文字：`#6b6258`（淡墨）
- 标题：`#1a1712`（浓墨）
- 强调色：`#9c5a3c`（赭石/印章红棕）
- 诗句底色：`#f0e9d8`（浅米，突出诗词原文）
- 边框：`#e0d5c0`
- 字体栈（正文）：`-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',serif`
- 诗句字体栈：`'STKaiti','KaiTi','Kaiti SC','Songti SC',serif`（楷体/宋体，古典气质）

## 使用说明

1. 把推文的 Markdown 内容按模块映射到下面的 HTML 组件。
2. 所有样式必须**内联**（`style="..."`），公众号不支持外部 CSS。
3. 图片使用全宽、`height:auto`；发布稿正文不重复放封面图（封面通过草稿的 `thumb_media_id` 展示）。
4. 生成两份 HTML：
   - `outputs/公众号预览稿.html`：顶部含封面图，供本地预览
   - `outputs/公众号发布稿.html`：正文不含封面副本、不含主标题 `<h1>`，供创建草稿

## 页面外壳

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{title}}</title>
</head>
<body style="margin:0;padding:0;background:#f5f1e8;color:#2f2b26;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',serif;line-height:1.9;">
  <section style="box-sizing:border-box;max-width:660px;margin:0 auto;padding:28px 18px 50px;background:#fbf8f1;">
    {{content}}
  </section>
</body>
</html>
```

## 组件

### 主标题（仅预览稿；发布稿由草稿 title 字段承载，正文不放 h1）

```html
<h1 style="margin:0 0 20px;font-size:25px;line-height:1.5;font-weight:800;color:#1a1712;text-align:center;">{{title}}</h1>
```

### 诗词原文（视觉重点，古典底色 + 楷体，移动端优化）

```html
<section style="margin:8px 0 28px;padding:24px 18px;background:#f0e9d8;border-radius:6px;border:1px solid #e0d5c0;text-align:center;">
  <p style="margin:0 0 4px;font-size:20px;font-weight:700;color:#1a1712;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;">{{poem_title}}</p>
  <p style="margin:0 0 16px;font-size:14px;color:#9c5a3c;">{{dynasty_author}}</p>
  <div style="font-size:18px;line-height:2.0;color:#2f2b26;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;letter-spacing:0.5px;">
    {{poem_lines_each_line}}
  </div>
</section>
```

> **移动端优化**：`{{poem_lines_each_line}}` 应为每句诗独立生成一个 `<p>` 标签，确保在窄屏上不会句内换行：
> ```html
> <p style="margin:0 0 6px;">床前明月光，</p>
> <p style="margin:0 0 6px;">疑是地上霜。</p>
> <p style="margin:0 0 6px;">举头望明月，</p>
> <p style="margin:0;">低头思故乡。</p>
> ```
> 注意最后一句 `margin:0`（无下边距）。

### 章节标题（如"二、诗人小档案"）

```html
<section style="margin:34px 0 16px;padding:0 0 8px;border-bottom:2px solid #9c5a3c;">
  <h2 style="margin:0;font-size:20px;line-height:1.5;font-weight:800;color:#1a1712;">{{heading}}</h2>
</section>
```

### 正文段落

```html
<p style="margin:0 0 16px;font-size:16px;color:#2f2b26;">{{text}}</p>
```

### 易错字提醒 / 考点提示（卡片强调）

```html
<section style="margin:16px 0 22px;padding:16px 18px;background:#f0e9d8;border-left:4px solid #9c5a3c;border-radius:4px;">
  <p style="margin:0 0 8px;font-size:15px;font-weight:700;color:#9c5a3c;">{{label}}</p>
  <p style="margin:0;font-size:15px;line-height:1.85;color:#2f2b26;">{{content}}</p>
</section>
```

### 列表（考点、易错字等）

```html
<ul style="margin:0 0 18px;padding-left:22px;color:#2f2b26;">
  <li style="margin:0 0 8px;font-size:15px;line-height:1.8;">{{item}}</li>
</ul>
```

### 文内配图

```html
<img src="{{image_src}}" alt="{{alt}}" style="display:block;width:100%;max-width:100%;height:auto;margin:18px 0 8px;border-radius:6px;">
```

### 图片说明

```html
<p style="margin:0 0 22px;font-size:13px;line-height:1.7;color:#7c7167;text-align:center;">{{caption}}</p>
```

### 白话译文（区分于原文，稍作强调）

```html
<section style="margin:12px 0 20px;padding:18px;background:#fbf8f1;border:1px dashed #d9cbb0;border-radius:6px;">
  <p style="margin:0 0 10px;font-size:15px;color:#9c5a3c;font-weight:700;">白话译文</p>
  <p style="margin:0;font-size:16px;line-height:1.95;color:#2f2b26;">{{translation}}</p>
</section>
```

### 亲子小结 / 文末寄语

```html
<section style="margin:30px 0 0;padding:20px;background:#f0e9d8;border-radius:8px;">
  <p style="margin:0;font-size:15px;line-height:1.9;color:#2f2b26;">{{summary}}</p>
</section>
```

### 关注引导（文末）

```html
<p style="margin:20px 0 0;font-size:15px;line-height:1.85;color:#9c5a3c;text-align:center;font-weight:700;">{{cta}}</p>
```

## 双语版排版补充

双语版每个模块中文在前、英文在后。英文用弱化色和稍小字号，与中文形成层次：

```html
<p style="margin:0 0 4px;font-size:16px;color:#2f2b26;">{{chinese_text}}</p>
<p style="margin:0 0 16px;font-size:14px;color:#6b6258;font-style:italic;">{{english_text}}</p>
```

## 公众号兼容注意

- 不使用外部 CSS、`<script>`、`<iframe>`、表单、事件处理器、远程字体。
- 不依赖 `<pre>`/`<code>`/`white-space`；本主题古诗词场景一般无代码块。
- 正文默认不放 `<a>` 超链接。
- 图片用可发布的 HTTPS 地址；本地相对路径仅用于预览稿。发布时由发布脚本上传本地图片并改写为微信 URL。
- 楷体字体栈在部分设备可能回退到系统衬线体，属正常现象，不影响阅读。
