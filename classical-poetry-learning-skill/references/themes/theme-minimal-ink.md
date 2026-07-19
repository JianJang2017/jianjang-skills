# 主题：极简墨色

视觉定位：米白纸面、墨色正文、克制留白和低装饰结构。强调安静、慢读和稳定的文字节奏，不绑定任何文章题材。

## 设计令牌

- 页面背景：`#f7f5f0`
- 容器背景：`#fffdf8`
- 正文文字：`#2f2f2f`
- 弱化文字：`#6b6258`
- 标题：`#171717`
- 强调色：`#8b5e34`
- 柔和表面：`#f3efe6`
- 深色表面：`#27231f`
- 边框：`#e8dfd2`
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
<body style="margin:0;padding:0;background:#f7f5f0;color:#2f2f2f;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif;line-height:1.95;">
  <section style="box-sizing:border-box;max-width:660px;margin:0 auto;padding:30px 18px 54px;background:#fffdf8;">
    {{content}}
  </section>
</body>
</html>
```

## 组件

### 封面图

```html
<img src="{{image_src}}" alt="{{alt}}" style="display:block;width:100%;max-width:100%;height:auto;margin:0 0 30px;border-radius:4px;">
```

### 文内图片

```html
<img src="{{image_src}}" alt="{{alt}}" style="display:block;width:100%;max-width:100%;height:auto;margin:10px 0 10px;border-radius:4px;">
```

### 图片说明

```html
<p style="margin:0 0 24px;font-size:13px;line-height:1.75;color:#7c7167;text-align:center;">{{caption}}</p>
```

### 标题和导语

```html
<h1 style="margin:0 0 16px;font-size:26px;line-height:1.42;font-weight:800;color:#171717;letter-spacing:0;word-break:break-word;">{{title}}</h1>
<p style="margin:0 0 28px;font-size:16px;color:#6b6258;word-break:break-word;">{{deck}}</p>
```

### 章节标题

```html
<section style="margin:38px 0 20px;padding:0 0 10px;border-bottom:1px solid #e8dfd2;">
  <p style="margin:0 0 6px;font-size:13px;color:#8b5e34;font-weight:700;letter-spacing:0;">{{number}}</p>
  <h2 style="margin:0;font-size:21px;line-height:1.5;font-weight:800;color:#171717;">{{heading}}</h2>
</section>
```

### 段落

```html
<p style="margin:0 0 18px;font-size:16px;color:#2f2f2f;">{{text}}</p>
```

### 诗词原文（移动端优化：每句独立成行）

```html
<section style="margin:8px 0 28px;padding:24px 18px;background:#f3efe6;border-radius:6px;border:1px solid #e8dfd2;text-align:center;">
  <p style="margin:0 0 4px;font-size:20px;font-weight:700;color:#171717;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;">{{poem_title}}</p>
  <p style="margin:0 0 16px;font-size:14px;color:#8b5e34;">{{dynasty_author}}</p>
  <div style="font-size:18px;line-height:2.0;color:#2f2f2f;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;letter-spacing:0.5px;">
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

### 提炼引用

```html
<section style="margin:28px 0;padding:20px 20px;background:#f3efe6;border-radius:6px;">
  <p style="margin:0;font-size:18px;line-height:1.8;color:#171717;font-weight:700;">{{quote}}</p>
</section>
```

### 轻提示

```html
<section style="margin:22px 0 28px;padding:16px 18px;border-left:3px solid #8b5e34;background:#fbf8f1;">
  <p style="margin:0;font-size:15px;color:#4b4036;">{{text}}</p>
</section>
```

### 列表卡片

```html
<section style="margin:18px 0 24px;padding:16px 18px;background:#fbf8f1;border:1px solid #e8dfd2;border-radius:6px;">
  <p style="margin:0 0 8px;font-size:15px;color:#3f3a34;">{{item}}</p>
</section>
```

### 多项列表

```html
<section style="margin:18px 0 26px;padding:16px 18px;background:#fbf8f1;border:1px solid #e8dfd2;border-radius:6px;">
  <p style="margin:0 0 10px;font-size:15px;line-height:1.85;color:#3f3a34;">{{item1}}</p>
  <p style="margin:0 0 10px;font-size:15px;line-height:1.85;color:#3f3a34;">{{item2}}</p>
  <p style="margin:0;font-size:15px;line-height:1.85;color:#3f3a34;">{{item3}}</p>
</section>
```

### 代码块

```html
<p style="display:block;box-sizing:border-box;max-width:100%;margin:16px 0 24px;padding:16px;background:#27231f;color:#f5efe7;border-radius:6px;word-break:break-all;overflow-wrap:anywhere;font-size:14px;line-height:1.78;font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;">{{escaped_code_with_br_and_nbsp}}</p>
```

### 参考资料组

搭配文末唯一的“参考资料”章节标题使用。多个来源连续列出，不要为每条资料重复写“参考资料”或“参考文章”标签。按来源数量复制或删除条目段落，最后一条使用 `margin:0`。

```html
<section style="margin:20px 0 26px;padding:15px 18px;background:#fbf8f1;border:1px solid #e8dfd2;border-radius:6px;">
  <p style="margin:0 0 12px;font-size:15px;line-height:1.75;color:#171717;font-weight:700;">{{label1}}<br><span style="font-size:13px;line-height:1.7;color:#6b6258;font-weight:400;word-break:break-all;">{{url1}}</span></p>
  <p style="margin:0;font-size:15px;line-height:1.75;color:#171717;font-weight:700;">{{label2}}<br><span style="font-size:13px;line-height:1.7;color:#6b6258;font-weight:400;word-break:break-all;">{{url2}}</span></p>
</section>
```
