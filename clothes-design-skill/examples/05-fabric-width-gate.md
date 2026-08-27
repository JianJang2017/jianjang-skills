# 幅宽门禁记录 / Fabric width gate

`--fabric-width` 是用量计算的除数,也会原样印在图纸标题栏。无效值必须让脚本
停止,而不是产出一份格式正常、数字错误的交付物。依据
[industrial-delivery-contract.md](../references/industrial-delivery-contract.md)
"无效尺码或参数:停止并要求更正,不得静默跳过"。

本文件由 `examples/regenerate.sh` 记录真实命令输出,非手写。

## 被拒绝的输入 / Rejected

### 幅宽为零 —— 曾抛出 ZeroDivisionError

```
$ python3 scripts/calculate_garment.py --type t-shirt --category tops --fabric cotton --fabric-width 0 --sizes M
❌ 幅宽必须为正数，收到 0cm
exit=1
```

### 幅宽为负 —— 曾静默产出负数用量与负数成本

```
$ python3 scripts/calculate_garment.py --type t-shirt --category tops --fabric cotton --fabric-width -50 --sizes M
❌ 幅宽必须为正数，收到 -50cm
exit=1
```

### 幅宽小于最窄可用门幅 60cm

```
$ python3 scripts/draw_pattern.py --type t-shirt --size M --fit regular --fabric-width 5 --title 示例 --output /tmp/cds-gate-reject.svg
❌ 幅宽无效，拒绝出图：
   - 幅宽 5cm 小于最窄可用门幅 60cm，无法排料；请确认输入
exit=1
```

### 对折裁片展开后超过幅宽

```
$ python3 scripts/draw_pattern.py --type dress --size XXXL --fit loose --fabric-width 60 --title 示例 --output /tmp/cds-gate-reject.svg
❌ 幅宽无效，拒绝出图：
   - 前上身: 对折展开需 62.0cm 宽，超过幅宽 60cm
   - 后上身: 对折展开需 62.0cm 宽，超过幅宽 60cm
   - 前裙片: 对折展开需 79.0cm 宽，超过幅宽 60cm
   - 后裙片: 对折展开需 79.0cm 宽，超过幅宽 60cm
exit=1
```

## 通过的输入 / Accepted

### 标准幅宽 140cm

```
$ python3 scripts/draw_pattern.py --type t-shirt --size M --fit regular --fabric-width 140 --title 示例 --output /tmp/cds-gate-accept.svg
✅ /tmp/cds-gate-accept.svg  (4 种裁片 / 共 5 片, 36KB)
   前片     ×1  净样 23.2×64cm  (5 处标注)
   后片     ×1  净样 23.2×64cm  (4 处标注)
   袖子     ×2  净样 17.0×20.0cm  (5 处标注)
   领圈罗纹   ×1  净样 31.0×4.0cm  (2 处标注)
exit=0
```

拒绝时不写出任何文件:交付物要么完整可复核,要么不存在。
