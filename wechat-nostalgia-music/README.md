# 怀旧音乐公众号创作技能

为怀旧音乐微信公众号策划和创作可发布内容，包括单曲故事、歌手专题、歌单、标题优化、改写润色、版权检查，**以及自动配图和一键发布功能**。

## 功能概览

### 核心功能

1. **内容创作**
   - 单曲故事文章（900-1400 字）
   - 歌手/词曲作者专题
   - 年代歌单（70/80/90/00 年代）
   - 影视 OST 专题
   - 节日选题策划

2. **内容优化**
   - 标题生成（5 个差异化方案）
   - 文章改写润色
   - 局部段落优化
   - 版权风险检查

3. **🆕 配图功能**
   - 自动分析文章结构
   - 推荐配图位置和数量
   - 生成符合年代氛围的插图
   - 支持多种怀旧风格（70s/80s/90s/00s）
   - 严格的版权安全控制

4. **🆕 发布功能**（新增）
   - Markdown → HTML 转换
   - 微信公众号样式适配
   - 图片素材自动上传
   - 封面图设置
   - 一键发布到草稿箱
   - 支持评论、作者、摘要等设置

## 配图功能特色

### 年代精准匹配

根据歌曲和文章的年代背景，自动选择合适的视觉符号：

| 年代 | 视觉符号 | 推荐风格 |
|------|---------|---------|
| **70年代** | 收音机、黑胶唱片、绿皮火车 | vintage-scene（复古场景） |
| **80年代** | 磁带、录音机、音像店 | storytelling（叙事场景） |
| **90年代** | 随身听、校园广播、CD | watercolor-scene（水彩场景） |
| **00年代** | MP3、翻盖手机、QQ空间 | warm-scene（温暖场景） |

### 版权安全

配图功能内置版权保护机制：

✅ **允许生成**：
- 抽象的年代场景（教室、街道、音像店）
- 象征性物件（收音机、磁带、随身听）
- 情感氛围图（黄昏、校园、火车站）
- 时间线和信息图

❌ **禁止生成**：
- 真实歌手的肖像或面容
- 专辑封面的复制或模仿
- MV 截图或场景重现
- 受版权保护的 logo、字体、品牌标识

### 风格预设

专为怀旧音乐设计的风格预设：

- **storytelling**：叙事场景，适合单曲故事
- **vintage-scene**：复古场景，适合 70/80 年代
- **watercolor-scene**：水彩场景，适合 90 年代青春主题
- **history/evolution**：时间线图，适合年代专题
- **hand-drawn-edu**：手绘信息图，适合歌单

## 使用示例

### 示例 1：创作单曲文章并配图

```
用户："写一篇关于罗大佑《童年》的文章，然后配图"

技能执行流程：
1. 生成文章（分析歌曲背景、创作角度、组织正文）
2. 识别年代（90年代校园传播期）
3. 推荐配图方案（2张图：开场场景 + 结尾呼应）
4. 询问风格（推荐 watercolor-scene）
5. 生成配图提示词（包含校园、随身听、阳光等元素）
6. 调用 scripts/generate-image.js 生成图片
7. 插入图片到文章
8. 输出带图的完整文章
```

### 示例 2：为已有文章添加配图

```
用户："给这篇文章配图：./articles/童年.md"

技能执行流程：
1. 读取文章内容
2. 分析文章结构和主题
3. 推荐配图位置
4. 询问风格偏好
5. 生成并插入图片
6. 创建备份并更新原文件
```

### 示例 3：年代歌单配图

```
用户："做一个80年代经典歌曲歌单，配上时代感的图片"

技能执行流程：
1. 生成歌单内容
2. 推荐配图类型（时间线或信息图）
3. 生成展示 80 年代音乐符号的插图
4. 插入到歌单文章
```

## 技术架构

### 目录结构

```
wechat-nostalgia-music/
├── SKILL.md                          # 主技能文档
├── references/
│   ├── compliance.md                 # 版权合规指南
│   └── illustration-guide.md         # 🆕 配图详细指南
├── scripts/
│   └── generate-image.js             # 🆕 图片生成脚本
└── evals/
    ├── evals.json                    # 测试用例
    └── test-article.md               # 🆕 测试文章
```

### 配图工作流程

```
文章分析
    ↓
推荐配图方案 → 用户确认
    ↓
确定视觉风格 → 用户选择
    ↓
生成 outline.md（配图大纲）
    ↓
生成 prompt 文件（每张图的详细提示词）
    ↓
调用 generate-image.js 批量生成
    ↓
插入图片到文章
    ↓
输出完整结果
```

## 依赖要求

### 基础功能（内容创作）
- 无需额外依赖
- 纯文本创作和编辑

### 配图功能
**必需**：
- Node.js >= 14.0.0

**图片生成后端（至少一个）**：
- **codex-cli**（推荐）：OpenAI Codex
  - 安装：访问 https://openai.com/zh-Hans-CN/codex
  - 验证：`codex --version`
  
- **agy**（Antigravity CLI）：Google Gemini
  - 安装：访问 https://antigravity.google/docs/cli-getting-started
  - 验证：`agy --version`

脚本会自动检测可用的后端并选择最佳选项。

### 安装验证

```bash
# 检查 Node.js
node --version

# 检查图片生成工具（任选其一）
codex --version
# 或
agy --version
```

## 配图输出示例

配图完成后会生成以下文件：

```
[文章目录]/
├── article.md                        # 原文
├── article.backup.md                 # 备份
└── imgs/
    ├── outline.md                    # 配图大纲
    ├── batch.json                    # 批量生成配置
    ├── prompts/                      # 提示词文件
    │   ├── 01-campus-afternoon.md
    │   └── 02-growing-echoes.md
    ├── 01-campus-afternoon.png       # 生成的图片
    └── 02-growing-echoes.png
```

## 完整示例

查看 `evals/test-article.md` 了解一篇典型的怀旧音乐文章结构。

运行配图功能：

```bash
# 方式 1：在技能使用时直接要求
"给 evals/test-article.md 这篇文章配图"

# 方式 2：写完文章后添加
"帮我写一篇关于《童年》的文章"
"需要为这篇文章配图吗？" # 技能会主动询问
```

## 最佳实践

### 内容创作
1. **事实优先**：所有幕后故事、数据必须有来源
2. **克制表达**：避免夸大传播度或杜撰记忆
3. **版权意识**：歌词引用最少必要，不提供未授权资源
4. **年代准确**：视觉符号与歌曲实际传播时期匹配

### 配图使用
1. **风格一致**：同一篇文章使用统一的艺术风格
2. **适度原则**：900-1400 字文章建议 1-2 张图
3. **位置合理**：在自然的段落间隙插入，不打断阅读
4. **检查版权**：生成后检查是否包含侵权元素

## 更新日志

### v1.1.0 (2026-07-10)
- ✨ 新增配图功能
- ✨ 新增年代视觉符号库
- ✨ 新增怀旧音乐专用风格预设
- 📚 新增 `references/illustration-guide.md` 详细配图指南
- 🔧 集成 `scripts/generate-image.js` 图片生成工具

### v1.0.0
- 🎉 初始版本
- 📝 单曲文章、歌单、专题创作
- ✍️ 标题生成、改写润色
- ⚖️ 版权风险检查

## 参考文档

- **SKILL.md**：完整技能说明，包含所有创作规则和配图流程
- **references/compliance.md**：版权合规详细指南
- **references/illustration-guide.md**：配图视觉风格和提示词模板
- **evals/test-article.md**：示例文章

## 支持

使用本技能创作内容时：

- 内容创作功能可独立使用（无需配图依赖）
- 配图功能可选，需要时再安装相关工具
- 所有功能都优先保证内容质量和版权安全

---

**版本**: 1.1.0  
**最后更新**: 2026-07-10  
**许可**: 遵守微信公众平台规则和相关版权法律

## 发布功能特色

### 自动化发布流程

一键将 Markdown 文章转换为微信公众号格式并发布到草稿箱：

1. **Markdown → HTML 转换**
   - 自动转换为微信友好的 HTML
   - 添加适配样式（字体、间距、对齐）
   - 保持手机阅读体验

2. **图片素材上传**
   - 自动上传封面图
   - 批量上传正文图片
   - 获取微信 media_id
   - 替换图片路径

3. **草稿创建**
   - 设置标题、作者、摘要
   - 配置封面显示
   - 设置评论权限
   - 一键提交到草稿箱

### 微信公众号 API 集成

使用微信官方服务端 API：

- ✅ Access Token 自动获取
- ✅ 素材上传（图片、封面）
- ✅ 草稿箱管理
- ✅ 错误处理和重试
- ✅ 安全凭证管理

### 灵活的发布选项

```bash
# 基础发布
node scripts/publish-to-wechat.js --article article.md --cover cover.jpg

# 自动使用第一张图作为封面
node scripts/publish-to-wechat.js --article article.md --auto-cover

# 自定义作者和摘要
node scripts/publish-to-wechat.js \
  --article article.md \
  --cover cover.jpg \
  --author "怀旧音乐编辑部" \
  --digest "回忆那些年，我们一起听过的歌"

# 打开评论（仅粉丝可评）
node scripts/publish-to-wechat.js \
  --article article.md \
  --auto-cover \
  --open-comment \
  --fans-only-comment

# 仅转换 HTML 预览，不发布
node scripts/publish-to-wechat.js \
  --article article.md \
  --dry-run \
  --output preview.html
```

## 使用示例（完整流程）

### 示例 4：创作、配图、发布一体化

```
用户："写一篇关于《童年》的文章，配图，然后发布到公众号"

技能执行流程：
1. 创作文章
   - 分析歌曲背景
   - 生成完整文章
   - 保存为 article.md

2. 配图
   - 识别 90 年代背景
   - 推荐 2 张图
   - 生成校园和成长主题插图
   - 插入到文章中

3. 发布准备
   - 询问封面选择（使用第一张图）
   - 询问作者署名（怀旧音乐）
   - 确认评论设置（关闭）

4. 执行发布
   - 转换 Markdown → HTML
   - 上传封面图和正文图片
   - 创建草稿

5. 输出结果
   ✅ 发布完成！
   草稿 ID: abc123xyz
   请登录微信公众号后台查看草稿箱
```

### 示例 5：批量发布歌单

```bash
# 为多篇文章批量发布
for article in 80s-songs/*.md; do
  echo "发布: $article"
  node scripts/publish-to-wechat.js \
    --article "$article" \
    --auto-cover \
    --author "怀旧音乐"
  sleep 2  # 避免频繁调用 API
done
```

## 技术架构

### 目录结构

```
wechat-nostalgia-music/
├── SKILL.md                          # 主技能文档
├── README.md                         # 说明文档
├── package.json                      # Node.js 依赖配置
├── .env.example                      # 🆕 配置文件示例
├── .gitignore                        # 🆕 Git 忽略规则
├── references/
│   ├── compliance.md                 # 版权合规指南
│   └── illustration-guide.md         # 配图详细指南
├── scripts/
│   ├── generate-image.js             # 图片生成脚本
│   └── publish-to-wechat.js          # 🆕 发布脚本
└── evals/
    ├── evals.json                    # 测试用例
    └── test-article.md               # 测试文章
```

### 发布工作流程

```
完成文章创作
    ↓
配图（可选）
    ↓
询问是否发布到公众号
    ↓
用户确认 → 收集发布参数
    ↓
检查微信凭证
    ↓
Markdown → HTML 转换
    ↓
上传封面图（获取 media_id）
    ↓
上传正文图片（获取 media_id）
    ↓
替换图片路径为 media_id
    ↓
创建草稿
    ↓
返回草稿 ID
```

## 依赖要求

### 基础功能（内容创作）
- 无需额外依赖
- 纯文本创作和编辑

### 配图功能
**必需**：
- Node.js >= 14.0.0

**图片生成后端（至少一个）**：
- **codex-cli**（推荐）：OpenAI Codex
  - 安装：访问 https://openai.com/zh-Hans-CN/codex
  - 验证：`codex --version`
  
- **agy**（Antigravity CLI）：Google Gemini
  - 安装：访问 https://antigravity.google/docs/cli-getting-started
  - 验证：`agy --version`

### 发布功能（新增）
**必需**：
- Node.js >= 14.0.0
- npm packages: `marked`, `form-data`（已包含在 package.json）

**微信公众号**：
- 已认证的服务号或订阅号
- 开启服务端 API 权限
- AppID 和 AppSecret

### 安装验证

```bash
# 检查 Node.js
node --version

# 安装依赖
npm install

# 检查图片生成工具（任选其一）
codex --version
# 或
agy --version

# 验证配图功能
node scripts/generate-image.js --help

# 验证发布功能
node scripts/publish-to-wechat.js --help
```

## 配置说明

### 1. 安装依赖

```bash
cd wechat-nostalgia-music
npm install
```

### 2. 配置微信公众号凭证

**方式 1：使用配置文件（推荐）**

```bash
# 创建配置目录
mkdir -p ~/.config/wechat-mp

# 复制配置示例
cp .env.example ~/.config/wechat-mp/.env

# 编辑配置文件，填入真实凭证
vi ~/.config/wechat-mp/.env
```

**方式 2：使用环境变量**

```bash
export WECHAT_APP_ID="your_app_id"
export WECHAT_APP_SECRET="your_app_secret"
```

**获取凭证步骤**：
1. 登录微信公众平台 (https://mp.weixin.qq.com)
2. 进入"设置与开发" → "基本配置"
3. 查看"开发者 ID(AppID)"
4. 重置或查看"开发者密码(AppSecret)"
5. 填入配置文件

### 3. 验证安装

```bash
# 运行配图功能验证
bash scriptbash scripts/verify-integration.sh

# 运行发布功能验证
bash scriptbash scripts/verify-publish.sh
```

## 配图输出示例

配图完成后会生成以下文件：

```
[文章目录]/
├── article.md                        # 原文
├── article.backup.md                 # 备份
└── imgs/
    ├── outline.md                    # 配图大纲
    ├── batch.json                    # 批量生成配置
    ├── prompts/                      # 提示词文件
    │   ├── 01-campus-afternoon.md
    │   └── 02-growing-echoes.md
    ├── 01-campus-afternoon.png       # 生成的图片
    └── 02-growing-echoes.png
```

## 发布输出示例

```
✅ 文章已发布到草稿箱

📋 草稿详情：
  标题：《那盘反复倒带的〈童年〉》
  作者：怀旧音乐
  封面：已设置
  图片：2 张已上传
  评论：已开启（仅粉丝可评论）
  草稿 ID：abc123xyz

📱 下一步操作：
1. 登录微信公众平台: https://mp.weixin.qq.com
2. 进入"内容与互动" → "草稿箱"
3. 找到标题为《那盘反复倒带的〈童年〉》的草稿
4. 预览效果，确认无误后点击"发表"
```

## 最佳实践

### 内容创作
1. **事实优先**：所有幕后故事、数据必须有来源
2. **克制表达**：避免夸大传播度或杜撰记忆
3. **版权意识**：歌词引用最少必要，不提供未授权资源
4. **年代准确**：视觉符号与歌曲实际传播时期匹配

### 配图使用
1. **风格一致**：同一篇文章使用统一的艺术风格
2. **适度原则**：900-1400 字文章建议 1-2 张图
3. **位置合理**：在自然的段落间隙插入，不打断阅读
4. **检查版权**：生成后检查是否包含侵权元素

### 发布流程
1. **预览验证**：使用 `--dry-run` 先预览 HTML
2. **凭证安全**：不要将 AppID 和 AppSecret 提交到代码仓库
3. **草稿审核**：发布后在后台预览，确认排版无误
4. **定时发布**：避免在半夜或敏感时间发布
5. **数据跟踪**：发布后关注阅读量和互动数据

## 常见问题

### Q: 如何获取微信公众号 AppID 和 AppSecret？

**A**: 
1. 登录微信公众平台 (mp.weixin.qq.com)
2. 进入"设置与开发" → "基本配置"
3. 查看 AppID 和重置/查看 AppSecret
4. 注意：AppSecret 仅显示一次，请妥善保管

### Q: 封面图尺寸要求是什么？

**A**: 
- 推荐比例：2.35:1（宽封面）
- 推荐尺寸：900x383 像素
- 格式：JPG、PNG
- 大小：< 1MB

### Q: 可以批量发布多篇文章吗？

**A**: 
可以编写脚本循环调用，但建议添加延迟避免频繁调用 API：
```bash
for article in *.md; do
  node scripts/publish-to-wechat.js --article "$article" --auto-cover
  sleep 2  # 延迟 2 秒
done
```

### Q: 发布失败如何排查？

**A**: 
按以下顺序检查：
1. 检查网络连接
2. 验证 AppID 和 AppSecret
3. 确认公众号类型（需要认证服务号或订阅号）
4. 检查图片路径和格式
5. 查看完整错误信息

## 更新日志

### v1.2.0 (2026-07-10)
- ✨ 新增发布功能
- ✨ Markdown → HTML 转换
- ✨ 微信公众号 API 集成
- ✨ 图片素材自动上传
- ✨ 草稿箱管理
- 🔧 添加 .env.example 配置示例
- 🔧 添加 .gitignore 文件
- 📝 新增 verify-publish.sh 验证脚本

### v1.1.0 (2026-07-10)
- ✨ 新增配图功能
- ✨ 新增年代视觉符号库
- ✨ 新增怀旧音乐专用风格预设
- 📚 新增 `references/illustration-guide.md` 详细配图指南
- 🔧 集成 `scripts/generate-image.js` 图片生成工具

### v1.0.0
- 🎉 初始版本
- 📝 单曲文章、歌单、专题创作
- ✍️ 标题生成、改写润色
- ⚖️ 版权风险检查

## 参考文档

- **SKILL.md**：完整技能说明，包含所有创作规则、配图流程和发布流程
- **references/compliance.md**：版权合规详细指南
- **references/illustration-guide.md**：配图视觉风格和提示词模板
- **evals/test-article.md**：示例文章
- **.env.example**：微信公众号凭证配置示例

## 支持

使用本技能创作内容时：

- 内容创作功能可独立使用（无需配图或发布依赖）
- 配图功能可选，需要时再安装相关工具
- 发布功能可选，需要配置微信公众号凭证
- 所有功能都优先保证内容质量和版权安全

---

**版本**: 1.2.0  
**最后更新**: 2026-07-10  
**许可**: 遵守微信公众平台规则和相关版权法律
