# Clothes Design Skill

面向服装概念设计与打版师交接的技能。它把款式需求或参考图片整理为“打版师复核包”：

- 用于外观确认的效果图；
- 由确定性代码生成的 1:N 裁片技术示意；
- 基准尺码与测量点；
- 面料用量和成本估算；
- 校验摘要、假设、风险和待确认项。

## 工业定位

本技能达到的目标是：让专业打版师能够核对设计意图和尺寸依据，并继续制作、试穿修正 1:1 工业纸样。

裁片 SVG **不可直接裁剪**，也不能替代 DXF/PLT、工业放码、真实排料、完整工艺单、生产 BOM、公差表或批量质检。用量和成本属于前期估算，正式采购或报价前必须用实际纸样、排料和供应商报价复核。

## 支持范围

确定性裁片引擎支持：

- `t-shirt`、`shirt`、`blouse`
- `crossover-blouse`
- `pants`、`jeans`
- `dress`

其他款式可以做概念设计，但不能宣称已经完成可复核裁片。

## 快速验证

只需 Python 标准库即可验证打版、规格和工业边界：

```bash
python3 scripts/validate_skill.py
```

单独生成裁片和规格：

```bash
python3 scripts/draw_pattern.py \
  --type t-shirt --size M --fit regular \
  --fabric-width 140 --title "基础圆领T恤" \
  --output /tmp/t-shirt-pattern.svg

python3 scripts/calculate_garment.py \
  --type t-shirt --category tops --fabric cotton \
  --fabric-width 140 --sizes M \
  --output /tmp/t-shirt-spec.md
```

效果图和图片逆向分析额外需要 Node.js 18+ 及可用的图像后端；它们失败时不影响确定性技术资料的验证，但交付状态必须披露降级。

## 交付状态

- `PASS`：必交件齐全，校验通过，无未确认的关键假设。
- `CONDITIONAL`：资料可供打版师复核，但包含已披露的估算、默认值或非关键降级。
- `BLOCKED`：关键输入缺失、款式不受支持或校验失败。

完整输入、边界和交付门禁见 [industrial-delivery-contract.md](references/industrial-delivery-contract.md)。
