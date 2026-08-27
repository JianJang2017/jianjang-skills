#!/bin/bash
# Regenerate every file in examples/ from the current scripts.
#
# The examples exist to show what the skill actually emits, so they are only
# useful while they match the code. Both generators are deterministic, so this
# script is the single source of truth: never hand-edit a generated file, and
# run tests/test_examples_current.py to catch drift.
#
# Usage: examples/regenerate.sh

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/examples"
cd "$ROOT"

DRAW="scripts/draw_pattern.py"
CALC="scripts/calculate_garment.py"
ASSEMBLY="scripts/pattern_assembly.py"

# idx|slug|type|size|fit|category|fabric|width|sizes|title
#
# The same --type goes to both scripts. Any style the cutting engine drafts must
# also have real cost data; if a style here starts emitting `assumptions`, that
# is a missing table entry to fill in, not something to route around by quoting
# a lookalike style.
while IFS='|' read -r idx slug type size fit cat fabric width sizes title; do
    [ -z "${idx:-}" ] && continue
    python3 "$DRAW" --type "$type" --size "$size" --fit "$fit" \
        --fabric-width "$width" --title "$title" \
        --output "$OUT/$idx-$slug-pattern.svg" >/dev/null || exit 1
    python3 "$CALC" --type "$type" --category "$cat" --fabric "$fabric" \
        --fabric-width "$width" --sizes $sizes \
        --output "$OUT/$idx-$slug-spec.md" >/dev/null || exit 1
    echo "  $idx-$slug  ($type/$size/$fit, ${width}cm $fabric)"
done <<'TABLE'
01|tshirt|t-shirt|M|regular|tops|cotton|140|XS S M L XL XXL XXXL|基础圆领T恤
02|crossover-blouse|crossover-blouse|M|regular|tops|linen|110|M L XL|古风交领上衣
03|jeans|jeans|M|regular|bottoms|denim|150|XS S M L XL XXL XXXL|直筒牛仔裤
04|dress|dress|M|fitted|dresses|silk|140|S M L|收腰连衣裙
TABLE

# These three views must share the exact M-size crossover draft. The assembly
# guide is generated (never hand-drawn), and the PDF is the only cuttable view.
python3 "$ASSEMBLY" --type crossover-blouse --size M --fit regular \
    --output "$OUT/02-crossover-blouse-assembly-guide.svg" || exit 1
python3 "$DRAW" --type crossover-blouse --size M --fit regular \
    --fabric-width 110 --pdf "$OUT/02-crossover-blouse-pattern-a4.pdf" || exit 1
echo "  02-crossover-blouse assembly + 1:1 A4 PDF"

# ── Rejection transcript ────────────────────────────────────────────────────
# The examples above are all successes. A reader who only sees those will
# assume any input produces a deliverable, which is the opposite of what the
# delivery contract requires. Record the refusals verbatim.
GATE="$OUT/05-fabric-width-gate.md"

{
    cat <<'HEADER'
# 幅宽门禁记录 / Fabric width gate

`--fabric-width` 是用量计算的除数,也会原样印在图纸标题栏。无效值必须让脚本
停止,而不是产出一份格式正常、数字错误的交付物。依据
[industrial-delivery-contract.md](../references/industrial-delivery-contract.md)
"无效尺码或参数:停止并要求更正,不得静默跳过"。

本文件由 `examples/regenerate.sh` 记录真实命令输出,非手写。

HEADER

    emit() {
        local desc="$1"; shift
        local out rc
        # Capture first, then report: piping straight into sed would make $?
        # the exit code of sed, so every transcript would claim exit=0 —
        # including the rejections whose whole point is a non-zero exit.
        out="$("$@" 2>&1)"
        rc=$?
        echo "### $desc"
        echo
        echo '```'
        echo "\$ $*"
        printf '%s\n' "$out" | sed "s|$ROOT|.|g"
        echo "exit=$rc"
        echo '```'
        echo
    }

    echo "## 被拒绝的输入 / Rejected"
    echo
    emit "幅宽为零 —— 曾抛出 ZeroDivisionError" \
        python3 "$CALC" --type t-shirt --category tops --fabric cotton \
        --fabric-width 0 --sizes M
    emit "幅宽为负 —— 曾静默产出负数用量与负数成本" \
        python3 "$CALC" --type t-shirt --category tops --fabric cotton \
        --fabric-width -50 --sizes M
    emit "幅宽小于最窄可用门幅 60cm" \
        python3 "$DRAW" --type t-shirt --size M --fit regular \
        --fabric-width 5 --title 示例 --output /tmp/cds-gate-reject.svg
    emit "对折裁片展开后超过幅宽" \
        python3 "$DRAW" --type dress --size XXXL --fit loose \
        --fabric-width 60 --title 示例 --output /tmp/cds-gate-reject.svg

    echo "## 通过的输入 / Accepted"
    echo
    emit "标准幅宽 140cm" \
        python3 "$DRAW" --type t-shirt --size M --fit regular \
        --fabric-width 140 --title 示例 --output /tmp/cds-gate-accept.svg

    cat <<'FOOTER'
拒绝时不写出任何文件:交付物要么完整可复核,要么不存在。
FOOTER
} > "$GATE"

rm -f /tmp/cds-gate-reject.svg /tmp/cds-gate-accept.svg
echo "  05-fabric-width-gate.md"
