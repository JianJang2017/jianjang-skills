#!/bin/bash
# Rasterise an SVG at its true dimensions.
#
# Why not qlmanage: it renders into a square thumbnail canvas, so a 992×557
# drawing comes out 2000×2000 with the content squeezed into a band and the rest
# padding. Dimension text becomes unreadable, which defeats the purpose of a
# technical drawing. Headless Chrome honours the SVG's own width/height.
#
# Usage: svg2png.sh <in.svg> [out.png] [scale]
#   scale defaults to 2 (retina-sharp text)

set -euo pipefail

SVG="${1:?usage: svg2png.sh <in.svg> [out.png] [scale]}"
OUT="${2:-${SVG%.svg}.png}"
SCALE="${3:-2}"

[ -f "$SVG" ] || { echo "❌ not found: $SVG" >&2; exit 1; }

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$CHROME" ] || CHROME="$(command -v chromium || command -v google-chrome || true)"

# Read the SVG's declared pixel size so the capture matches it exactly.
read -r W H < <(python3 - "$SVG" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read(4000)
m = re.search(r'<svg[^>]*?width="([\d.]+)"[^>]*?height="([\d.]+)"', t)
if m:
    print(int(float(m.group(1))), int(float(m.group(2))))
else:
    v = re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', t)
    print(*(int(float(x)) for x in v.groups()) if v else (1200, 800))
PY
)

if [ -n "$CHROME" ] && [ -x "$CHROME" ]; then
    TMPDIR_C="$(mktemp -d)"
    trap 'rm -rf "$TMPDIR_C"' EXIT
    "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
        --force-device-scale-factor="$SCALE" \
        --user-data-dir="$TMPDIR_C" \
        --window-size="${W},${H}" \
        --default-background-color=FFFFFFFF \
        --screenshot="$OUT" "file://$(cd "$(dirname "$SVG")" && pwd)/$(basename "$SVG")" \
        >/dev/null 2>&1
    if [ -f "$OUT" ]; then
        DIMS=$(sips -g pixelWidth -g pixelHeight "$OUT" 2>/dev/null | awk '/pixel/{printf "%s ",$2}')
        echo "✅ $OUT  (${DIMS}from ${W}x${H} @${SCALE}x)"
        exit 0
    fi
fi

# Fallback: qlmanage. Aspect ratio will be wrong (square canvas) — warn loudly
# rather than silently hand back a distorted drawing.
echo "⚠️  Chrome unavailable; falling back to qlmanage (square canvas, aspect ratio not preserved)" >&2
PREV="$(mktemp -d)"
trap 'rm -rf "$PREV"' EXIT
LONG=$(( W > H ? W : H ))
qlmanage -t -s $(( LONG * SCALE )) -o "$PREV" "$SVG" >/dev/null 2>&1
SRC="$PREV/$(basename "$SVG").png"
[ -f "$SRC" ] || { echo "❌ conversion failed" >&2; exit 1; }
cp "$SRC" "$OUT"
echo "⚠️  $OUT (qlmanage fallback — 比例不准，仅供粗略预览)"
