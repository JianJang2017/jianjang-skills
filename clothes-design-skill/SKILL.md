---
name: clothes-design-skill
description: 服装设计技能，能够根据尺寸样式要求生成对应的设计图稿（成衣效果图+裁片分解图），也能根据衣服图片逆向克隆出设计图稿和打版规格。输出包含：样衣效果图、裁片布局图、国际尺码表(XS-XXXL)、面料用量核算、成本明细。支持上衣/下装/连衣裙全品类，适配手绘/科技蓝图/水彩/3D渲染等风格。当用户提到"设计衣服"、"服装打版"、"制衣"、"裁片图"、"样衣"、"成本核算"、"面料用量"、"衣服设计图"、"克隆这件衣服"、"照着这个做一件"、"garment design"、"pattern making"，或需要完整的服装设计+生产规格书时使用。
version: 1.0.0
---

# Clothes Design Skill（服装设计工厂）

从设计到打版，一站式输出**可落地的服装生产规格书**：
- 样衣效果图（成衣穿着效果）
- 裁片分解图（1:N 比例示意，像地图那样标注尺寸）
- 国际尺码表（XS/S/M/L/XL/XXL/XXXL 全档）
- 面料用量计算（幅宽、总长度、裁片数）
- 成本明细（面料+辅料+人工+管理费）

## 核心理念

一张好看的服装图不等于能做出来。设计师画效果图，打版师拆裁片，采购算面料，财务核成本——这些环节通常各自为政。本技能把它们串联成一条流水线：**输入款式需求 → 输出生产规格书**，让设计直接对接制造。

参考文档 `docs/clothes-design-skill.md` 中的制衣六大阶段（设计打版→面料准备→裁剪→缝制→后整→检验包装），本技能覆盖**第一阶段（设计与打版）**，输出物可直接递交给面料采购和裁剪车间。

## 两种工作模式

### 模式 A：从需求到设计（正向设计）

用户提供款式描述、风格、尺寸要求 → 生成设计图稿 + 规格书

**输入示例：**
- "设计一件古风交领上衣，M码，用棉麻面料"
- "做一条高腰阔腿裤，黑色，全尺码"
- "连衣裙，法式复古风格，真丝面料，给我看效果图和成本"

### 模式 B：从图片到规格（逆向克隆）

用户提供一张衣服图片 → 反推设计要素 → 生成克隆版设计图稿 + 规格书

**输入示例：**
- "照着这张图做一件一样的" + 附图
- "克隆这件衣服，给我打版图和面料用量"
- "这个款式能做吗？成本多少？"

## 工作流程

### 第一步：理解需求

#### 正向设计（模式 A）

从用户描述中确定：

1. **款式类型**：上衣（t-shirt, shirt, blouse）、下装（pants, skirt）、连衣裙（dress）、外套（jacket, coat）
2. **风格定位**：古风、法式、韩系、街头、职业装、休闲、运动等
3. **面料选择**：棉、麻、丝、毛、涤纶、混纺、针织、牛仔（影响成本和用量）
4. **尺码需求**：单一尺码（如 M）还是全尺码（XS-XXXL）
5. **特殊要求**：颜色、图案、细节工艺（刺绣、印花、拼接）

需求不明确时，提供 2-3 个方向概念让用户选择，不要直接开始生成。

#### 逆向克隆（模式 B）

用户提供图片后：

1. 使用 `scripts/reverse-prompt.js` 反推图片的设计要素
2. 提取：款式类型、颜色、面料质感、关键细节（领型、袖型、下摆、装饰）
3. 向用户确认：是完全复刻还是调整细节（如换颜色、换面料）
4. 确认尺码需求和面料类型

### 第二步：生成样衣效果图

读取 `references/prompt-framework.md` 了解服装设计图的提示词结构。

**创建临时 prompt 文件：**

```bash
cat > /tmp/garment-design-prompt.md << 'EOF'
---
aspect_ratio: "3:4"
---

PROMPT:
[Style: 手绘风格 / 科技蓝图风 / 水彩风 / 3D 渲染风]
[Type: 服装设计效果图]
[Content: 款式描述]
一件[款式类型]，[风格特征]，[面料质感]，[颜色]，[关键细节]。
正面平铺展示，完整呈现衣身、袖子、领口、下摆，无模特穿着，白色背景。

[Key elements]
- 款式：[具体款式名称]
- 颜色：[主色调 + 配色]
- 面料：[面料类型及质感描述]
- 细节：[领型、袖型、扣子、装饰等]
EOF
```

**生成效果图：**

```bash
node scripts/generate-image.js \
  --prompt-file /tmp/garment-design-prompt.md \
  --output /tmp/garment-sample.png \
  --aspect-ratio 3:4 \
  --provider auto
```

### 第三步：生成裁片分解图（用 draw_pattern.py，不要用生图模型）

裁片图是打版师的工作图纸，尺寸标注必须精确、且必须能追溯回尺码表。
**这一步用 `scripts/draw_pattern.py` 出矢量图，不要用 `generate-image.js`。**

```bash
python3 scripts/draw_pattern.py \
  --type t-shirt \
  --size M \
  --fit regular \
  --fabric-width 140 \
  --title "基础圆领T恤" \
  --output /tmp/pattern.svg
```

**为什么裁片图不能用 AI 生图：**

扩散模型渲染数字文本不可靠，更要命的是它标出来的数字与尺码表**没有任何计算关系**——那是"看起来像尺寸的装饰"。打版师照着一个凭空生成的"袖长 20"下剪，裁出来的就是废料。而裁片几何本质上是确定性算术（比例分配法），属于该用代码算的东西。

`draw_pattern.py` 的每一个标注都由 `SIZE_CHART` 按公式推导，与规格书同源；出图前还会跑 `validate_pieces()` 逐条比对"标注数字"与"该标注所指线段的实际长度"，不一致就拒绝出图（exit 1）。这道检查在开发中真的抓到过两个 bug：袖长标注指向了袖底缝（标 20 实测 9.2），以及把横裆宽误标成臀宽。

**支持的款式**（`--type`）：

| type | 裁片数 | 说明 |
|------|-------|------|
| `t-shirt` / `shirt` / `blouse` | 4 种 / 5 片 | 前片、后片、袖子×2、领圈罗纹 |
| `crossover-blouse` | 6 种 / 7 片 | 古风交领：大襟、小襟、后片、宽袖×2、领子、腰带 |
| `pants` / `jeans` | 4 种 / 7 片 | 前片×2、后片×2、腰头、口袋布×2 |
| `dress` | 5 种 / 6 片 | 前后上身、前后裙片、泡泡袖×2 |

`--fit` 可选 `fitted` / `regular` / `loose`（放松量预设，见 `references/pattern-engineering.md`）。

**输出内容**（SVG 矢量图，可无损缩放、可 1:1 打印）：

- **净样线**（实线）+ **毛样线**（橙色虚线 = 净样 + 缝份）
- **对折线**（蓝色长短点线，标明不加缝份）
- **布纹方向箭头**（经向/纬向，裁反了衣服会扭）
- **每处关键尺寸的双箭头标注**（1/4胸围、袖窿深、立裆深、腰节长…）
- **每片的净样/毛样尺寸、缝份明细、裁剪注意事项**
- **图例 + 免责说明**

**SVG 转 PNG**（用 `scripts/svg2png.sh`，不要直接用 qlmanage）：

```bash
bash scripts/svg2png.sh /tmp/pattern.svg            # → /tmp/pattern.png，2 倍分辨率
bash scripts/svg2png.sh /tmp/pattern.svg out.png 3  # 指定输出和倍率
```

脚本走 headless Chrome，按 SVG 声明的宽高截图，比例与原图一致。

> **不要用 `qlmanage -t` 转裁片图**：它渲染的是缩略图，画布强制成正方形——1120×617 的图会输出成 2000×2000，内容被压在中间一条，四周全是留白，尺寸文字缩到看不清。这正是之前 PNG "缺失/不可用"的原因。`svg2png.sh` 在 Chrome 不可用时会退回 qlmanage，但会明确警告比例不准。

> 交付时**优先给 SVG**：矢量图放大不模糊，可按真实比例打印贴到裁床上。PNG 仅用于聊天窗口/文档内嵌预览。

**扩展新款式**：在 `scripts/pattern_drafting.py` 里加一个 `draft_xxx()` 函数返回 `List[Piece]`，然后注册进 `DRAFTERS`。每个 `Dim` 的 label 里必须写进它自己的数值，`validate_pieces()` 才能校验。

### 第四步：计算规格数据

使用 `scripts/calculate_garment.py` 生成尺码表、面料用量、成本明细。

**确定参数：**
- `--type`: 款式类型（t-shirt, shirt, blouse, dress, skirt, pants, jacket, coat）
- `--category`: 品类（tops, bottoms, dresses）
- `--fabric`: 面料类型（cotton, linen, silk, wool, polyester, blend, knit, denim）
- `--fabric-width`: 面料幅宽（默认 140cm，可选 110/140/150）
- `--sizes`: 尺码范围（默认全尺码 XS-XXXL，可指定子集如 `S M L`）

**生成规格书：**

```bash
python3 scripts/calculate_garment.py \
  --type shirt \
  --category tops \
  --fabric cotton \
  --fabric-width 140 \
  --output /tmp/garment-spec.md
```

输出包含：
- 完整尺码表（所请求尺码的胸围、腰围、臀围、肩宽、袖长、衣长）
- 面料用量（总米数、幅宽、裁片数量、排料效率）
- 成本明细（面料成本、辅料成本、人工成本、管理费用、总成本，每项附计算依据）

加 `--json` 输出结构化数据，便于程序消费。

**关于「参考尺码」：**

用量和成本是按**单一参考尺码**计算的，不是全尺码的总和。参考尺码的选取规则：
- 请求范围包含 M → 用 M（行业惯例，中间码最有代表性）
- 不包含 M → 取所请求范围的中间码

这一点很重要：如果用户只要 XXXL，脚本会按 XXXL 的实际用量报价，而不是拿 M 的数字充当 XXXL。参考尺码会写进 JSON 的 `reference_size` 字段，也会标在 markdown 的标题和尺码表里（`←参考`），所以交付时要明确告诉用户「这个用量和成本对应的是哪个码」。要全尺码的总用量，把各码分别跑一遍再累加。

**关于估算假设：**

如果面料或款式不在内置库里（比如用户说"竹纤维"、"汉服"），脚本不会报错，而是回退到中档默认值（¥30/米、辅料 ¥15、工时 4 小时），并把回退记录在 `cost_breakdown.assumptions` 里，markdown 中显示为「⚠️ 估算假设」区块。

**这些回退值必须转达给用户。** 一个查表得来的价格和一个默认猜测在输出里长得一样，用户没法分辨。看到 assumptions 非空时，主动说明哪几项是估的、建议用户提供实际报价，比让他们拿着一个来源不明的数字去下单要负责得多。

**关于无效尺码：**

尺码名写错（如 `--sizes BOGUS`）会直接报错退出（exit 1），不会静默跳过。原因是：静默跳过会产出一份尺码表缺行、但用量和成本看起来依然权威的规格书，这种输出比报错危险得多。

### 第五步：整合交付

将三部分内容整合成最终交付物：

```
📦 [款式名称] 设计规格书

1️⃣ 样衣效果图
   [内联显示 garment-sample.png]
   展示成衣穿着效果，用于客户确认和市场推广

2️⃣ 裁片分解图（SVG 矢量图，优先交付 .svg）
   [内联显示 pattern.svg / 预览 pattern.png]
   净样线 + 毛样线 + 对折线 + 布纹方向 + 逐处尺寸标注
   每处标注均由尺码表推导，与规格书同源

3️⃣ 尺码规格
   [插入 garment-spec.md 中的尺码表]

4️⃣ 面料用量（参考 [参考尺码] 码）
   [插入面料用量段落]
   - 总用量：X.XX 米
   - 幅宽：XXX cm
   - 裁片数：X 片
   - 排料效率：XX%

5️⃣ 成本核算（参考 [参考尺码] 码）
   [插入成本明细表]
   总成本：¥XXX.XX

---
💡 **下一步行动**
- ✅ 效果图已生成，可用于客户确认
- ✅ 裁片图已生成，可递交打版师制作纸样
- ✅ 面料用量已计算，可进行采购
- ✅ 成本已核算，可制定定价策略

📋 **制衣流程提示**（参考 docs/clothes-design-skill.md）
当前完成：✅ 设计与打版
待进行：⏸️ 面料采购 → ⏸️ 裁剪 → ⏸️ 缝制 → ⏸️ 后整 → ⏸️ 检验包装
```

## 模式 B：逆向克隆的特殊处理

### 使用反推脚本

当用户提供图片时，先用 `reverse-prompt.js` 提取设计要素：

```bash
node scripts/reverse-prompt.js \
  -i /path/to/reference-garment.jpg \
  --lang zh \
  --archive \
  --ar 3:4
```

脚本输出：
- 款式类型（shirt / dress / pants 等）
- 风格标签（vintage / korean / streetwear 等）
- 颜色方案
- 面料质感推测
- 关键细节描述

### 向用户确认

反推结果可能不完全准确，需要与用户确认：

1. 款式识别是否正确（有时连衣裙会被识别成上衣+裙子）
2. 面料类型（图片质感可能误导，需要用户明确：棉/麻/丝等）
3. 是否需要调整细节（如改颜色、简化装饰）
4. 尺码需求

### 生成克隆版设计

确认后，按照正向设计的流程生成：
- 效果图（基于反推的 prompt 重新生成）
- 裁片图（按标准款式的裁片结构）
- 规格数据（按用户确认的面料和尺码计算）

## 风格预设

设计图稿支持多种视觉风格，参考 `references/prompt-framework.md`：

### 效果图风格

1. **手绘风格**（推荐用于展示设计创意）
   - 温暖米白背景，黑色墨线，彩色色块
   - 适合：概念设计、客户提案

2. **水彩风格**（适合柔和款式）
   - 柔光、纸张质感、水墨晕染
   - 适合：女装、童装、家居服

3. **3D 渲染风格**（最接近实物）
   - 柔光、景深、真实材质
   - 适合：电商展示、样品确认

4. **摄影风格**（平铺拍摄效果）
   - 自然光、35mm 镜头感
   - 适合：产品目录、库存展示

### 裁片图不走风格预设

裁片图由 `draw_pattern.py` 出矢量图，样式固定为工程制图规范（净样实线、毛样橙虚线、对折蓝点线、布纹绿箭头），**不接受风格切换**。技术图纸的作用是让打版师读准尺寸，好看是次要的；换风格只会削弱可读性。

风格预设只作用于**效果图**。

## 面料与成本

### 面料数据库

内置常见面料的价格和特性，参考 `references/fabric-database.md`：

| 面料类型 | 单价(元/米) | 幅宽(cm) | 特性 |
|---------|-----------|---------|------|
| 纯棉 cotton | 25 | 140 | 透气、吸汗、易皱 |
| 亚麻 linen | 40 | 140 | 清爽、挺括、易皱 |
| 真丝 silk | 120 | 114 | 柔软、光泽、昂贵 |
| 羊毛 wool | 80 | 150 | 保暖、挺括、需专业护理 |
| 涤纶 polyester | 18 | 150 | 耐穿、不易皱、不透气 |
| 混纺 blend | 30 | 140 | 综合性能平衡 |
| 针织 knit | 22 | 160 | 弹性、舒适、易变形 |
| 牛仔 denim | 35 | 150 | 耐磨、厚实、适合裤装 |

### 成本构成

每件衣服的成本包括：

1. **面料成本** = 单价 × 用量（米）
2. **辅料成本** = 拉链、纽扣、松紧带、织唛、吊牌等（按款式固定值）
3. **人工成本** = 工时 × 单价（30元/小时）
   - T恤：2.5 小时
   - 衬衫：4.0 小时
   - 连衣裙：5.0 小时
   - 裤子：4.5 小时
   - 外套：8.0 小时
4. **管理费用** = 直接成本的 15%（打版、质检、包装）

**总成本公式：**
```
总成本 = (面料成本 + 辅料成本 + 人工成本) × 1.15
```

计算脚本会自动输出详细的成本明细表。

## 尺码标准

采用国际通用尺码（XS/S/M/L/XL/XXL/XXXL），每档递增规律：

**上衣类（tops）：**
- 胸围：每档 +4cm
- 腰围：每档 +4cm
- 肩宽：每档 +1cm
- 袖长：每档 +1cm
- 衣长：每档 +2cm

**下装类（bottoms）：**
- 腰围：每档 +4cm
- 臀围：每档 +4cm
- 裤长（内长）：每档 +2cm
- 大腿围：每档 +2cm

**连衣裙（dresses）：**
- 结合上衣和下装的测量点
- 总长度：每档 +2cm

完整尺码表由 `calculate_garment.py` 自动生成，无需手工计算。

## 工具依赖

### 必需工具

1. **Node.js** (>=18): 运行图片生成与反推脚本（脚本是 ESM，需要 Node 18+）
2. **Python 3** (>=3.6): 运行规格计算脚本
3. **图片生成后端**（至少一个）：
   - `bl`: 阿里云百炼 CLI（免费，推荐）
   - `codex-cli`: OpenAI Codex 图片生成
   - `agy`: Google Gemini 图片生成
   - `qwen`: 通义千问 API（需配置 DASHSCOPE_API_KEY）

### 本技能自带全部脚本，可独立运行

生图、反推、规格计算三个脚本都打包在 `scripts/` 下，不依赖其他技能目录：

| 脚本 | 用途 |
|------|------|
| `scripts/pattern_drafting.py` | 尺码表 → 裁片几何 + 标注（纯 Python，无第三方依赖） |
| `scripts/draw_pattern.py` | 裁片几何 → 带标注的 SVG 技术图纸（中英双语标注） |
| `scripts/svg2png.sh` | SVG → PNG，按原始宽高比光栅化（headless Chrome） |
| `scripts/calculate_garment.py` | 尺码表 / 面料用量 / 成本核算 |
| `scripts/generate-image.js` | 文生图（**仅效果图**；裁片图走 draw_pattern.py） |
| `scripts/reverse-prompt.js` | 图片 → prompt 反推（模式 B） |
| `scripts/bl-image-generator.js`、`scripts/qwen-image-generator.js` | 百炼 / 通义后端适配（由 generate-image.js 自动加载） |
| `scripts/styles.js` | 效果图风格预设库 |
| `models.json` | 各后端可用模型配置 |

**裁片图链路零外部依赖**：`pattern_drafting.py` + `draw_pattern.py` 只用 Python 标准库，不需要 Node、不需要生图后端、不需要联网。即使没装任何 AI 后端，裁片图和规格书也能正常出。

根目录的 `package.json` 声明了 `"type": "module"`，所以 ESM 导入在任何 Node 18+ 环境下都能跑，不依赖 Node 的语法自动探测。

### 验证安装

```bash
node --version          # 应显示 >=18
python3 --version       # 应显示 >=3.6
which bl || which codex || which agy  # 至少一个存在

# 脚本自检
python3 scripts/calculate_garment.py --help
python3 scripts/draw_pattern.py --help
node scripts/generate-image.js --help
node scripts/reverse-prompt.js --help

# 跑回归测试（尺码/用量/成本 + 打版标注自洽性）
python3 tests/test_calculate_garment.py
python3 tests/test_regressions.py
python3 tests/test_pattern_drafting.py

# SVG 转 PNG（headless Chrome，保持比例）
bash scripts/svg2png.sh pattern.svg
```

裁片图只需 Python 3；**没装 Node 或任何生图后端也能出裁片图和规格书**，只是出不了效果图。

## 实战示例

### 示例 1：设计一件古风上衣

**用户输入：**
"帮我设计一件古风交领上衣，白色底色配浅蓝色刺绣，用棉麻面料，M码"

**执行步骤：**

1. 确定参数：
   - 款式：blouse（古风上衣归入 blouse 类）
   - 风格：古风、交领、刺绣
   - 面料：linen（亚麻）
   - 尺码：M
   - 颜色：白色底+浅蓝色刺绣

2. 生成效果图 prompt：
```
[Style: 水彩风格]
[Type: 服装设计效果图]
一件古风交领上衣，白色底色，浅蓝色兰花刺绣点缀领口和袖口，
棉麻质感，交领设计，宽袖，腰部收腰带，下摆微微开叉。
正面平铺展示，白色背景。

[Key elements]
- 款式：古风交领上衣
- 颜色：白色+浅蓝色刺绣
- 面料：棉麻，自然褶皱质感
- 细节：交领、盘扣、宽袖口、腰带、兰花刺绣
```

3. 生成裁片图（交领结构用 `crossover-blouse`，它的大襟/小襟不对称）：
```bash
python3 scripts/draw_pattern.py \
  --type crossover-blouse --size M --fit loose \
  --fabric-width 140 --title "古风交领上衣" \
  --output gufeng-pattern.svg
# → 6 种裁片 / 共 7 片：大襟、小襟、后片、宽袖×2、领子、腰带
```

注意别用 `--type blouse`：那走的是 T恤版型，会把两片前襟裁成一样宽，交领就交不上了。

4. 计算规格：
```bash
python3 scripts/calculate_garment.py \
  --type blouse --category tops --fabric linen \
  --sizes M --output spec.md
```

5. 交付输出：
   - 效果图：水彩风格的古风上衣平铺图
   - 裁片图：6片裁片的分解示意图
   - 规格书：M码尺寸、面料2.8米、成本约¥175

### 示例 2：克隆一条牛仔裤

**用户输入：**
"照着这张图做一条一样的牛仔裤" + 上传图片

**执行步骤：**

1. 反推设计要素：
```bash
node scripts/reverse-prompt.js -i uploaded-image.jpg --archive
```

输出可能为：
```
[Style: 牛仔裤]
[Type: 裤装]
深蓝色修身牛仔裤，中腰设计，直筒裤型，膝盖处有轻微磨白处理，
五袋款式（前2后3），拉链+纽扣门襟，后腰有品牌皮标。
```

2. 向用户确认：
   - 款式：直筒牛仔裤，中腰，修身 ✓
   - 颜色：深蓝色 ✓
   - 面料：牛仔布（12oz 厚度） — 需确认
   - 尺码：全尺码还是单码？ — 需确认
   - 细节：磨白处理、品牌标是否保留？ — 需确认

3. 用户回复："面料用标准牛仔布就行，全尺码，不要品牌标，磨白保留"

4. 生成克隆版效果图（基于反推 prompt 调整）：
```
[Style: 摄影风格]
[Type: 服装设计效果图]
一条深蓝色直筒牛仔裤，中腰修身版型，膝盖处轻微磨白，
五袋款式，金属拉链+纽扣，后腰无品牌标。
正面平铺展示，白色背景。
```

5. 生成裁片图：
```bash
python3 scripts/draw_pattern.py \
  --type jeans --size M --fabric-width 150 \
  --title "直筒牛仔裤" --output jeans-pattern.svg
# → 4 种裁片 / 共 7 片：前片×2、后片×2、腰头、口袋布×2
# 前后片自动按 ±1cm 差值起版（后片包臀、后腰起翘 1.5cm）
```

6. 计算规格：
```bash
python3 scripts/calculate_garment.py \
  --type pants --category bottoms --fabric denim \
  --output clone-spec.md
```

7. 交付：全尺码规格书 + 效果图 + 裁片图

## 参考文档

- `docs/clothes-design-skill.md` - 制衣完整流程六大阶段
- `references/pattern-engineering.md` - **打版计算公式、放松量、缝份、标注校验机制、扩展新款式方法**（改动裁片图逻辑前必读）
- `references/garment-library.md` - 各款式的标准裁片构成
- `references/fabric-database.md` - 面料特性与价格数据库
- `references/prompt-framework.md` - 效果图提示词框架（裁片图不用 prompt）
- `references/cost-model.md` - 成本核算详细说明
- `scripts/pattern_drafting.py` - **打版引擎**：尺码表 → 裁片几何 + 尺寸标注（含 `validate_pieces` 自校验）
- `scripts/draw_pattern.py` - **裁片图渲染器**：裁片几何 → 带标注的 SVG 技术图纸（中英双语）
- `scripts/svg2png.sh` - SVG → PNG，保持原始比例（headless Chrome；**勿用 qlmanage**，它会输出正方形画布）
- `scripts/calculate_garment.py` - 规格计算脚本（全尺码表、用量、成本，deterministic）
- `scripts/generate-image.js` - 效果图生成（auto-detect 后端；**不用于裁片图**）
- `scripts/reverse-prompt.js` - 图片反推脚本（模式 B 的入口）
- `tests/test_pattern_drafting.py` - 打版引擎回归测试（7 款 × 7 码标注自洽 + 周长闭合 + SVG 校验）
- `tests/test_calculate_garment.py`、`tests/test_regressions.py` - 尺码/用量/成本计算回归测试

### 数据流

```
SIZE_CHART (calculate_garment.py)
    ├──→ calculate_garment.py  ──→ 尺码表 / 面料用量 / 成本明细
    └──→ pattern_drafting.py   ──→ 裁片几何 + 标注
              └──→ validate_pieces()  ← 标注与几何不符则拒绝出图
                        └──→ draw_pattern.py ──→ 带标注的 SVG 图纸
```

单一数据源意味着：规格书上的"1/4胸围 23.2cm"和裁片图上标的是同一个数，不可能对不上。

## 局限性

1. **面料用量是估算值**：基于标准版型和排料效率，实际生产中可能因为花型对位、特殊裁剪而有 ±10% 浮动
2. **成本仅供参考**：面料价格按市场平均值，实际采购价受数量、品牌、地域影响
3. **不涵盖复杂工艺**：如手工刺绣、钉珠、特殊染整等高定工艺未计入成本
4. **图片反推准确度有限**：依赖 AI 后端的视觉识别能力，复杂款式可能识别不准

### 裁片图的局限（务必如实告知用户）

裁片图上的**尺寸数字是准确的**（由尺码表推导 + 自动校验），但下列几点必须说明，详见 `references/pattern-engineering.md`：

5. **是 1:N 示意图，不是可裁剪纸样**：尺寸准确，但要落地必须由打版师出 1:1 实样。不导出 DXF/PLT。
6. **曲线是二次贝塞尔近似**：袖窿、裆弧的形状对但不够顺，真实打版要用曲线板逐点调顺。影响合体度，不影响尺寸核对。
7. **没有省道展开**：连衣裙腰省只给收量数值，未画出省道形状和省尖位置；不支持胸省转移、公主线分割。
8. **袖山与袖窿只做比例匹配**：未实测两条弧长，装袖前需打版师核对并调整吃势（通常袖山比袖窿长 1-2cm）。
9. **不含工艺细节**：扣位、袋位、明线、粘衬范围均未标注。
10. **毛样线是缩放近似**：橙色虚线用于表达"裁剪线在净样外侧"，精确缝份看每片下方的文字明细，不要去量图。

## 未来增强

潜在改进方向（暂未实现）：

- 导出 DXF/PLT 格式，直接对接 CAD 和自动裁床
- 输出 1:1 可拼接打印的 PDF（A4 分页 + 对齐标记），家用打印机也能出实样
- 省道展开：画出省道三角形与省尖位置，支持胸省转移
- 袖山/袖窿弧长实测校验 + 自动配吃势
- 排料图（marker）：把裁片在幅宽内套排，输出真实用量而非估算
- 更多廓形：插肩袖、连身袖、多片分割、斜裁
- 集成面料供应商 API，实时查询库存和价格
- 支持自定义面料价格和人工费率
- 增加儿童装和大码装（4XL-6XL）尺码表

---

**💡 提示：** 本技能输出的是**设计与打版阶段**的交付物。后续的面料采购、裁剪、缝制、后整、检验等环节需要实际生产车间完成。规格书可直接递交给制衣工厂使用。
