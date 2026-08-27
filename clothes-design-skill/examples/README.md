# 服装设计技能示例 / Clothes Design Skill Examples

本目录包含 clothes-design-skill 的实际输出示例，展示从款式需求到打版师复核包的完整流程。

## 示例文件

每个示例包含两个确定性产出；交领上衣另含两个同源产出：

1. **裁片技术示意 SVG** —— 由 `scripts/draw_pattern.py` 计算生成的矢量图，带尺寸标注和缝份说明。**1:N 示意，不可直接裁剪**。
2. **规格书 Markdown** —— 由 `scripts/calculate_garment.py` 生成，包含尺码表、面料用量和成本估算。
3. **拼接示意 SVG（仅交领上衣）** —— 从真实 `Piece.path` 自动生成，不另画相似轮廓。
4. **1:1 A4 PDF（仅交领上衣）** —— 10mm 拼接重叠、50mm 校准框、真实缝份和对位刀口；只供白坯样衣。

**本目录不包含 AI 生成的效果图。** 效果图只用于外观确认，不作为结构或尺寸证据；且单个文件常超 1MB，不适合纳入代码库。

### 01 - 基础圆领T恤

- **款式**: t-shirt，M码，regular 版型
- **面料**: 纯棉 cotton，140cm 幅宽
- **裁片**: 4 种 / 共 5 片（前片、后片、袖子×2、领圈罗纹）
- **用量**: 2.55米（M码参考）
- **成本**: ¥165.31（面料 ¥63.75 + 辅料 ¥5 + 人工 ¥75 + 管理费 ¥21.56）

文件: `01-tshirt-pattern.svg`, `01-tshirt-spec.md`

### 02 - 古风交领上衣

- **款式**: crossover-blouse，M码，regular 版型
- **面料**: 亚麻 linen，110cm 幅宽（窄幅）
- **裁片**: 6 种 / 共 7 片，含不对称大襟/小襟（31.8cm vs 24.5cm）
- **用量**: 3.69米（M码参考）
- **成本**: ¥343.39（前期估算）
- **白坯输出**: 单尺码 1:1 A4 分页 PDF；先实测 50mm 校准框

文件: `02-crossover-blouse-pattern.svg`, `02-crossover-blouse-assembly-guide.svg`, `02-crossover-blouse-pattern-a4.pdf`, `02-crossover-blouse-spec.md`

### 03 - 直筒牛仔裤

- **款式**: jeans，M码，regular 版型
- **面料**: 牛仔布 denim，150cm 幅宽（宽幅）
- **裁片**: 4 种 / 共 7 片（前片×2、后片×2、腰头、口袋布×2）
- **用量**: 2.42米（M码参考）
- **成本**: ¥273.35（牛仔布 ¥84.70 + 辅料 ¥18 + 人工 ¥135 + 管理费 ¥35.65）
- **映射**: `jeans` 裁片引擎支持，成本按 `pants` 估算（裁片结构相同）

文件: `03-jeans-pattern.svg`, `03-jeans-spec.md`

### 04 - 收腰连衣裙

- **款式**: dress，M码，fitted 版型（修身）
- **面料**: 真丝 silk，140cm 幅宽
- **裁片**: 5 种 / 共 6 片（前/后上身、前/后裙片、泡泡袖×2）
- **用量**: 3.01米（M码参考）
- **成本**: ¥609.45（真丝 ¥361.20 + 辅料 ¥20 + 人工 ¥180 + 管理费 ¥48.25）

文件: `04-dress-pattern.svg`, `04-dress-spec.md`

### 05 - 幅宽门禁记录

记录 `--fabric-width` 校验的真实拒绝输出，证明无效输入被正确拦截，而不是产出格式正常、数字错误的交付物。

文件: `05-fabric-width-gate.md`

## 技术说明

### 款式词表映射

裁片引擎（`pattern_drafting.py`）支持的款式：

- `t-shirt`, `shirt`, `blouse`, `crossover-blouse`
- `pants`, `jeans`
- `dress`

成本估算表（`calculate_garment.py`）覆盖所有确定性裁片类型，并另覆盖：

- `t-shirt`, `shirt`, `blouse`, `crossover-blouse`, `pants`, `jeans`, `dress`
- `skirt`, `jacket`, `coat`

`skirt`, `jacket`, `coat` 只有成本数据，没有确定性裁片；不得反向宣称支持打版。

### 可复现性

所有产出由 `regenerate.sh` 从代码生成，**不可手工编辑**。两个脚本都是确定性的：相同输入总产生相同输出，因此可以用 diff 检测漂移。

运行 `tests/test_examples_current.py` 会重新生成到临时目录并与 `examples/` 比对；任何差异意味着示例过时或脚本被修改后未重新生成。

### 重新生成

```bash
bash examples/regenerate.sh
```

所需时间约 5 秒。无需网络、无需 Node.js、无需图像生成后端。

## 不包含的内容

根据 [industrial-delivery-contract.md](../references/industrial-delivery-contract.md)，一个完整的打版师复核包还包括：

- **效果图** —— 仅用于视觉确认，不作为结构证据。由 `scripts/generate-image.js` 调用扩散模型生成，单个文件 1–3MB，且需要 FLUX API 或 Qwen-VL 可用。已在代码库外管理，不纳入 `examples/`。
- **PNG 栅格预览** —— SVG 的光栅化版本，便于不支持 SVG 的环境查看。可用 `scripts/svg2png.sh` 转换（需 Chrome headless），但非必交件。
- **校验摘要、假设、风险和待确认项** —— 这些在实际交付时由 LLM 根据用户输入动态生成，不存在通用模板。

本目录只包含**纯代码产出、可复现**的技术文件。PDF 以二进制逐字节比较，SVG/Markdown 以文本 diff 比较。

## 引用

示例文件中的成本数据基于 `references/cost-model.md` 的市场均价，仅供前期估算。正式采购或报价前必须用实际纸样、排料图和供应商报价复核。

裁片由 `references/pattern-engineering.md` 定义的公式计算，符合成衣标准尺寸和常见版型规则，但**专业打版师仍需试坯修版**后才能投产。
