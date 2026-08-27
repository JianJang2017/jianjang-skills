---
name: clothes-design-skill
description: Use when a user needs garment concept design, pattern-making reference, size specifications, fabric consumption or cost estimates, a validated 1:1 crossover-blouse muslin PDF, or garment-photo analysis for a pattern-maker handoff. Not for production-ready patterns, DXF/PLT, grading, markers, or bulk cutting.
version: 2.1.0
---

# Clothes Design Skill

生成供专业打版师复核的技术资料包。效果图用于视觉确认；裁片 SVG 是 1:N 技术示意，**不可直接裁剪、采购签约或投产**。`crossover-blouse` 可额外生成经过比例、拓扑、缝份和缝合关系校验的 1:1 A4 分页 PDF，仅用于制作白坯样衣。

## 开始前

必须读取 [references/industrial-delivery-contract.md](references/industrial-delivery-contract.md)。它定义输入预检、能力边界、交付状态和最终输出结构。

按任务需要再读取：

- 调整版型或检查公式：[references/pattern-engineering.md](references/pattern-engineering.md)
- 选择面料或解释特性：[references/fabric-database.md](references/fabric-database.md)
- 解释用量、价格或费率：[references/cost-model.md](references/cost-model.md)
- 生成效果图：[references/prompt-framework.md](references/prompt-framework.md)
- 核对款式裁片构成：[references/garment-library.md](references/garment-library.md)

## 模式

### 正向设计

从描述中确认款式、目标尺码/人体净尺寸、版型、面料与幅宽、关键结构和交付范围。会改变版型的关键项缺失时先询问；可安全默认的项目必须进入“假设与待确认项”。

### 图片逆向分析

先检查图片是否已提供，并先判断用户是否要求“完全复刻”或直接生产；此类单图请求先标记 `BLOCKED`，不要先生成效果图。仅在目标调整为外观分析或打版师复核、且必要信息可补充时运行：

```bash
node scripts/reverse-prompt.js -i /absolute/path/garment.jpg --lang zh --archive
```

图片只能证明可见外观。面料成分、内部结构、背面细节、尺寸和工艺不得从单张图片断言；未获用户确认时标为推测，并将状态设为 `CONDITIONAL` 或 `BLOCKED`。
复刻第三方款式时，提醒用户核查商标、版权、外观设计及授权范围；不要复制品牌标识。

## 确定性工作流

1. 形成设计简报并完成输入预检。
2. 检查款式是否受裁片引擎支持。
3. 效果图仅用于外观确认，可按 prompt framework 生成；生图失败不允许伪造成功。
4. 裁片图必须由代码生成，不得用扩散模型生成带尺寸的技术图：

```bash
python3 scripts/draw_pattern.py \
  --type t-shirt --size M --fit regular \
  --fabric-width 140 --title "基础圆领T恤" \
  --output /tmp/t-shirt-pattern.svg
```

支持的确定性裁片类型：`t-shirt`、`shirt`、`blouse`、`crossover-blouse`、`pants`、`jeans`、`dress`。其他款式不能套用近似款后宣称已完成打版；提供概念方案时状态为 `BLOCKED`，等待专业打版。

5. 生成尺码、用量和成本数据：

```bash
python3 scripts/calculate_garment.py \
  --type t-shirt --category tops --fabric cotton \
  --fabric-width 140 --sizes M \
  --output /tmp/t-shirt-spec.md
```

用量和成本只对应输出所标识的参考尺码。任何 `assumptions` 都必须原样进入交付物，并使状态至少为 `CONDITIONAL`。无效尺码、几何校验失败或关键输入缺失必须停止，状态为 `BLOCKED`。

6. 用户需要交领上衣白坯样板时，生成单尺码 1:1 PDF；不要用 SVG 打印替代：

```bash
python3 scripts/draw_pattern.py \
  --type crossover-blouse --size M --fit regular \
  --fabric-width 110 \
  --output /tmp/crossover-reference.svg \
  --pdf /tmp/crossover-muslin-a4.pdf
```

PDF 必须先量取每页 `50 × 50mm` 校准框，并按“实际大小 / 100%”打印，禁止适合页面。当前只有 `crossover-blouse` 定义了逐边缝份与对位刀口；其他款式的 `--pdf` 校验会拒绝输出。

7. 按合同组装打版师复核包，运行交付门禁：

```bash
python3 scripts/validate_skill.py
```

## 交付状态

- `PASS`：所有必交件存在，确定性校验通过，无未确认的关键假设。
- `CONDITIONAL`：可供打版师复核，但包含已披露的估算、默认值或非关键降级。
- `BLOCKED`：关键输入缺失、款式不受支持或校验失败；不得包装成完整规格书。

最终答复开头必须显示一个状态，并在结尾明确：1:1 PDF 只可制作白坯；由专业打版师试穿修版、复核面料缩率和工艺后，才能进入面料采购、裁剪与生产。

## 不可突破的边界

- 不把效果图当作结构证据。
- 不把 1:N SVG 描述为 1:1 纸样，即使 SVG 可无损缩放。
- 不把白坯样衣 PDF 描述为生产纸样、放码文件或排料图。
- 不用估算用量直接下采购单，不用估算成本直接签报价合同。
- 不声称支持 DXF/PLT、工业放码、真实排料、完整工艺单、生产 BOM、公差表或批量质检。
- 不手工修饰失败输出；修正输入或代码后重新运行校验。
