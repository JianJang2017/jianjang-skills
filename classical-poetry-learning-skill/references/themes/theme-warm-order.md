# 主题：暖白秩序

视觉定位：暖白页面、低饱和橙色强调、稳重灰蓝文字和规则卡片。强调平静、可信和清楚推进的阅读体验，不绑定任何文章题材。

## 设计令牌

- 页面背景：`#f8fafc`
- 容器背景：`#ffffff`
- 正文文字：`#334155`
- 弱化文字：`#64748b`
- 标题：`#0f172a`
- 主强调色：`#c2410c`
- 次强调色：`#0f766e`
- 柔和表面：`#fff7ed`
- 中性表面：`#f8fafc`
- 深色表面：`#1e293b`
- 边框：`#e2e8f0`
- 字体栈：`-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif`
- 等宽字体栈：`'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace`

## 页面外壳

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{title}}</title>
</head>
<body style="margin:0;padding:0;background:#f8fafc;color:#334155;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif;line-height:1.88;">
  <section style="box-sizing:border-box;max-width:680px;margin:0 auto;padding:26px 16px 52px;background:#ffffff;">
    {{content}}
  </section>
</body>
</html>
```

## 组件

### 封面图

```html
<img src="{{image_src}}" alt="{{alt}}" style="display:block;width:100%;max-width:100%;height:auto;margin:0 0 28px;border-radius:8px;">
```

### 文内图片

```html
<img src="{{image_src}}" alt="{{alt}}" style="display:block;width:100%;max-width:100%;height:auto;margin:8px 0 10px;border-radius:8px;">
```

### 图片说明

```html
<p style="margin:0 0 22px;font-size:13px;line-height:1.7;color:#64748b;text-align:center;">{{caption}}</p>
```

### 标题和导语

```html
<h1 style="margin:0 0 14px;font-size:26px;line-height:1.38;font-weight:800;color:#0f172a;letter-spacing:0;word-break:break-word;">{{title}}</h1>
<p style="margin:0 0 24px;font-size:16px;color:#64748b;word-break:break-word;">{{deck}}</p>
```

### 章节标题

```html
<section style="margin:36px 0 18px;">
  <p style="margin:0 0 8px;font-size:13px;color:#c2410c;font-weight:800;letter-spacing:0;">{{number}}</p>
  <h2 style="margin:0 0 16px;font-size:22px;line-height:1.45;font-weight:800;color:#0f172a;">{{heading}}</h2>
</section>
```

### 段落

```html
<p style="margin:0 0 16px;font-size:16px;color:#334155;">{{text}}</p>
```

### 诗词原文（移动端优化：每句独立成行）

```html
<section style="margin:8px 0 28px;padding:24px 18px;background:#fff7ed;border-radius:8px;border:1px solid #fed7aa;text-align:center;">
  <p style="margin:0 0 4px;font-size:20px;font-weight:700;color:#0f172a;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;">{{poem_title}}</p>
  <p style="margin:0 0 16px;font-size:14px;color:#c2410c;">{{dynasty_author}}</p>
  <div style="font-size:18px;line-height:2.0;color:#334155;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;letter-spacing:0.5px;">
    {{poem_lines_each_line}}
  </div>
</section>
```

> **移动端优化**：`{{poem_lines_each_line}}` 应为每句诗独立生成一个 `<p>` 标签，确保在窄屏上不会句内换行。示例：
> ```html
> <p style="margin:0 0 6px;">床前明月光，</p>
> <p style="margin:0 0 6px;">疑是地上霜。</p>
> <p style="margin:0 0 6px;">举头望明月，</p>
> <p style="margin:0;">低头思故乡。</p>
> ```
> 注意最后一句 `margin:0`（无下边距）。长诗可适当减小字号至 17px。

### 暖色摘要

```html
<section style="margin:24px 0 30px;padding:18px 18px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;">
  <p style="margin:0 0 10px;font-size:16px;color:#9a3412;font-weight:800;">{{label}}</p>
  <p style="margin:0;font-size:16px;color:#7c2d12;">{{text}}</p>
</section>
```

### 稳态卡片

```html
<section style="margin:20px 0 24px;padding:18px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
  <p style="margin:0 0 8px;font-size:15px;color:#0f172a;font-weight:700;">{{title}}</p>
  <p style="margin:0;font-size:15px;color:#475569;">{{text}}</p>
</section>
```

### 多项列表

```html
<section style="margin:18px 0 24px;padding:18px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
  <p style="margin:0 0 10px;font-size:15px;line-height:1.8;color:#475569;">{{item1}}</p>
  <p style="margin:0 0 10px;font-size:15px;line-height:1.8;color:#475569;">{{item2}}</p>
  <p style="margin:0;font-size:15px;line-height:1.8;color:#475569;">{{item3}}</p>
</section>
```

### 有力收束

```html
<section style="margin:26px 0;padding:20px;background:#1e293b;border-radius:8px;">
  <p style="margin:0;font-size:18px;line-height:1.7;color:#ffffff;font-weight:800;">{{text}}</p>
</section>
```

### 代码块

```html
<p style="display:block;box-sizing:border-box;max-width:100%;margin:16px 0 22px;padding:16px;background:#1e293b;color:#e2e8f0;border-radius:8px;word-break:break-all;overflow-wrap:anywhere;font-size:14px;line-height:1.75;font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;">{{escaped_code_with_br_and_nbsp}}</p>
```

### 参考资料组

搭配文末唯一的“参考资料”章节标题使用。多个来源连续列出，不要为每条资料重复写“参考资料”或“参考文章”标签。按来源数量复制或删除条目段落，最后一条使用 `margin:0`。

```html
<section style="margin:18px 0 24px;padding:15px 16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
  <p style="margin:0 0 12px;font-size:15px;line-height:1.7;color:#0f172a;font-weight:700;">{{label1}}<br><span style="font-size:13px;line-height:1.65;color:#0f766e;font-weight:400;word-break:break-all;">{{url1}}</span></p>
  <p style="margin:0;font-size:15px;line-height:1.7;color:#0f172a;font-weight:700;">{{label2}}<br><span style="font-size:13px;line-height:1.65;color:#0f766e;font-weight:400;word-break:break-all;">{{url2}}</span></p>
</section>
```
