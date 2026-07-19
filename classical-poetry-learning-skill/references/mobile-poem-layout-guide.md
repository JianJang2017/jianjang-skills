# 古诗词原文移动端排版方案

## 问题分析

古诗词原文在手机上显示时存在的问题：
1. 一行两句（如"床前明月光，疑是地上霜。"）在窄屏上会换行
2. 超长诗句（如"飞流直下三千尺"）可能溢出
3. 标点符号可能被截断

## 解决方案

### 方案A：每句独立成行（推荐）

**适用场景**：所有诗词，尤其是长诗

**优势**：
- 在任何屏幕宽度下都不会换行
- 诗句结构清晰
- 易读性好

**HTML 结构**：
```html
<section style="margin:8px 0 28px;padding:26px 20px;background:#f0e9d8;border-radius:6px;border:1px solid #e0d5c0;text-align:center;">
  <p style="margin:0 0 4px;font-size:20px;font-weight:700;color:#1a1712;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;">{{poem_title}}</p>
  <p style="margin:0 0 18px;font-size:14px;color:#9c5a3c;">{{dynasty_author}}</p>
  <div style="margin:0;font-size:19px;line-height:2.2;color:#2f2b26;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;letter-spacing:1px;">
    <p style="margin:0 0 8px;">床前明月光，</p>
    <p style="margin:0 0 8px;">疑是地上霜。</p>
    <p style="margin:0 0 8px;">举头望明月，</p>
    <p style="margin:0;">低头思故乡。</p>
  </div>
</section>
```

### 方案B：智能两句一行（适用于短句）

**适用场景**：五言、七言短诗，诗句较短

**优势**：
- 保持传统排版美感
- 节省垂直空间

**响应式 HTML**：
```html
<section style="margin:8px 0 28px;padding:26px 20px;background:#f0e9d8;border-radius:6px;border:1px solid #e0d5c0;text-align:center;">
  <p style="margin:0 0 4px;font-size:20px;font-weight:700;color:#1a1712;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;">{{poem_title}}</p>
  <p style="margin:0 0 18px;font-size:14px;color:#9c5a3c;">{{dynasty_author}}</p>
  <div style="margin:0;font-size:19px;line-height:2.2;color:#2f2b26;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;letter-spacing:1px;">
    <!-- 方式1: 使用 word-break 防止断行 -->
    <p style="margin:0 0 8px;word-break:keep-all;white-space:nowrap;overflow-wrap:normal;">床前明月光，疑是地上霜。</p>
    <p style="margin:0;word-break:keep-all;white-space:nowrap;overflow-wrap:normal;">举头望明月，低头思故乡。</p>
  </div>
</section>
```

**注意**：`white-space:nowrap` 可能导致超长句子溢出，需要配合容器 `overflow-x:auto`

### 方案C：响应式布局（最佳方案）

**适用场景**：需要同时适配桌面和移动端

**特点**：
- 宽屏（>500px）：两句一行
- 窄屏（≤500px）：每句一行

```html
<section style="margin:8px 0 28px;padding:26px 20px;background:#f0e9d8;border-radius:6px;border:1px solid #e0d5c0;text-align:center;">
  <p style="margin:0 0 4px;font-size:20px;font-weight:700;color:#1a1712;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;">{{poem_title}}</p>
  <p style="margin:0 0 18px;font-size:14px;color:#9c5a3c;">{{dynasty_author}}</p>
  <div style="margin:0;font-size:19px;line-height:2.2;color:#2f2b26;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;letter-spacing:1px;">
    <!-- 每句诗独立成段，确保不会在句内换行 -->
    <p style="margin:0 0 6px;display:inline-block;width:100%;max-width:100%;">床前明月光，</p>
    <p style="margin:0 0 12px;display:inline-block;width:100%;max-width:100%;">疑是地上霜。</p>
    <p style="margin:0 0 6px;display:inline-block;width:100%;max-width:100%;">举头望明月，</p>
    <p style="margin:0;display:inline-block;width:100%;max-width:100%;">低头思故乡。</p>
  </div>
</section>
```

## 推荐实现（移动端优先）

考虑到微信公众号主要在手机上阅读，推荐使用**方案A（每句独立成行）**：

```html
<section style="margin:8px 0 28px;padding:24px 18px;background:#f0e9d8;border-radius:6px;border:1px solid #e0d5c0;text-align:center;">
  <p style="margin:0 0 4px;font-size:20px;font-weight:700;color:#1a1712;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;">静夜思</p>
  <p style="margin:0 0 16px;font-size:14px;color:#9c5a3c;">唐·李白</p>
  <div style="font-size:18px;line-height:2.0;color:#2f2b26;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;letter-spacing:0.5px;">
    <p style="margin:0 0 6px;">床前明月光，</p>
    <p style="margin:0 0 6px;">疑是地上霜。</p>
    <p style="margin:0 0 6px;">举头望明月，</p>
    <p style="margin:0;">低头思故乡。</p>
  </div>
</section>
```

### 关键优化点

1. **每句独立 `<p>` 标签**：确保每句在单独一行
2. **合理的行间距**：`margin:0 0 6px` 句间有呼吸感
3. **字号和行高**：
   - 字号：18-19px（移动端合适）
   - 行高：2.0-2.2（古诗词舒展感）
4. **字间距**：`letter-spacing:0.5-1px`（增加气质）
5. **容器内边距**：`padding:24px 18px`（移动端适配）

## 长诗处理

对于超长诗句（如《琵琶行》），使用相同方案但调整字号：

```html
<div style="font-size:17px;line-height:2.0;...">
  <p style="margin:0 0 6px;">浔阳江头夜送客，</p>
  <p style="margin:0 0 6px;">枫叶荻花秋瑟瑟。</p>
  <!-- 更多诗句 -->
</div>
```

## 实施建议

1. **更新所有主题模板**：统一使用"每句独立成行"方案
2. **生成逻辑**：从 `poem-meta.json` 读取诗句数组，每句生成一个 `<p>` 标签
3. **测试验证**：在不同屏幕宽度（320px, 375px, 414px）测试
4. **视觉检查**：确保最后一句不带多余的 `margin-bottom`

## 生成代码示例

```javascript
// 从 poem-meta.json 读取诗句
const lines = poemMeta.lines; // ["床前明月光，", "疑是地上霜。", ...]

// 生成 HTML
const linesHTML = lines.map((line, index) => {
  const isLast = index === lines.length - 1;
  const margin = isLast ? '0' : '0 0 6px';
  return `<p style="margin:${margin};">${escapeHTML(line)}</p>`;
}).join('\n    ');

// 完整诗词原文 HTML
const poemHTML = `
<section style="margin:8px 0 28px;padding:24px 18px;background:#f0e9d8;border-radius:6px;border:1px solid #e0d5c0;text-align:center;">
  <p style="margin:0 0 4px;font-size:20px;font-weight:700;color:#1a1712;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;">${poemMeta.title}</p>
  <p style="margin:0 0 16px;font-size:14px;color:#9c5a3c;">${poemMeta.dynasty}·${poemMeta.author}</p>
  <div style="font-size:18px;line-height:2.0;color:#2f2b26;font-family:'STKaiti','KaiTi','Kaiti SC','Songti SC',serif;letter-spacing:0.5px;">
    ${linesHTML}
  </div>
</section>`;
```
