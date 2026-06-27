# 更新日志

## v2.0.0 (2026-06-27)

### 重大更新

- **新增 30 套 m2w 系列主题**：从 markdown2wechat 项目移植，前缀 `m2w-` 避免命名冲突
- 主题总数从 10 套扩展到 40 套
- 涵盖多种色系和风格：暗黑、紫色、蓝色、绿色、粉色、黄色、橙色、红色等

### 新增主题列表

#### 暗黑系列
- `m2w-geek-black` - 极客黑：暗黑、强代码感
- `m2w-obsidian` - 黑曜石：深色主题
- `m2w-minimal-black` - 极简黑

#### 紫色系列
- `m2w-night-purple` - 夜幕紫
- `m2w-brilliant-purple` - 荧光紫
- `m2w-rose-purple` - 玫瑰紫

#### 蓝色系列
- `m2w-vivid-blue` - 灵动蓝
- `m2w-luminous-blue` - 极光蓝
- `m2w-tech-blue` - 科技蓝
- `m2w-fullstack-blue` - 全栈蓝

#### 绿色系列
- `m2w-soft-green` - 柔和绿
- `m2w-greenery` - 新绿
- `m2w-prairie-green` - 草原绿

#### 青色系列
- `m2w-tender-cyan` - 嫩青
- `m2w-orchid-cyan` - 兰青

#### 粉色系列
- `m2w-cupid-busy` - 丘比特忙
- `m2w-soft-pink` - 柔粉

#### 黄色系列
- `m2w-lemon-yellow` - 柠檬黄
- `m2w-yamabuki` - 山吹黄
- `m2w-pornhub-yellow` - PH黄

#### 橙色/红色系列
- `m2w-orange-blue` - 橙蓝对撞
- `m2w-orange-heart` - 橙心
- `m2w-scarlet` - 绯红

#### 特色系列
- `m2w-simple` - 简：简洁白底
- `m2w-double-shadow` - 双重影
- `m2w-frontend-peak` - 前端之峰
- `m2w-weformat` - 微信式
- `m2w-smartisan-note-v2` - 锤子便签
- `m2w-singularity` - 奇点：科幻风格
- `m2w-yanqi-lake` - 雁栖湖：自然风格

### 文档更新

- 更新 README.md 和 README_EN.md，增加主题目录
- 更新 SKILL.md，优化主题选择逻辑
- 新增 CHANGELOG.md 记录版本历史

### 主题选择策略

更新后的主题选择优先级：
1. 用户点名主题直接使用
2. 题材型主题优先匹配（技术文章、笔记等）
3. 原创精品风格型主题根据气质匹配
4. m2w 系列作为补充选项，当用户需要特定色系时推荐

---

## v1.0.0 (2024-06-17)

### 初始版本

- 10 套原创精品主题
  - 题材型：native-blueprint、cyan-grid
  - 风格型：minimal-ink、vintage-magazine、noir-stage、notebook-sticky、warm-order、bluegray-brief、cool-blueprint、green-editorial
- 完整的 Markdown 到 HTML 转换功能
- 内联样式支持，兼容微信公众号和邮件客户端
- 代码块、表格、引用、列表等完整支持
- 辅助脚本：escape_code.py、validate_html.py

