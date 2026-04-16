#!/bin/bash
# =============================================
# Icon-Regenerator
#
# Baut aus assets/icon_source.png die Plattform-Icons:
#   - icon.icns  (macOS, via iconutil — macOS-only)
#   - icon.ico   (Windows, via Pillow — cross-platform)
#
# Ausführen:
#   bash assets/regenerate_icons.sh
# =============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/icon_source.png"

if [ ! -f "$SRC" ]; then
  echo "FEHLER: $SRC nicht gefunden"
  echo "Lege ein quadratisches PNG (>=1024x1024, transparent) unter diesem Namen ab."
  exit 1
fi

# --- macOS: .icns via iconutil + sips ---
if command -v iconutil >/dev/null 2>&1 && command -v sips >/dev/null 2>&1; then
  ICONSET="$SCRIPT_DIR/icon.iconset"
  rm -rf "$ICONSET"
  mkdir -p "$ICONSET"

  # 10 Standard-Größen für macOS iconset
  for size in 16 32 64 128 256 512 1024; do
    sips -z $size $size "$SRC" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null 2>&1
  done
  sips -z 32   32   "$SRC" --out "$ICONSET/icon_16x16@2x.png"   >/dev/null 2>&1
  sips -z 64   64   "$SRC" --out "$ICONSET/icon_32x32@2x.png"   >/dev/null 2>&1
  sips -z 256  256  "$SRC" --out "$ICONSET/icon_128x128@2x.png" >/dev/null 2>&1
  sips -z 512  512  "$SRC" --out "$ICONSET/icon_256x256@2x.png" >/dev/null 2>&1
  sips -z 1024 1024 "$SRC" --out "$ICONSET/icon_512x512@2x.png" >/dev/null 2>&1

  iconutil -c icns "$ICONSET" -o "$SCRIPT_DIR/icon.icns"
  rm -rf "$ICONSET"
  echo "✓ icon.icns erstellt"
else
  echo "⚠ iconutil/sips nicht gefunden — .icns wird übersprungen (nur auf macOS möglich)"
fi

# --- Windows: .ico via Pillow ---
if python3 -c "from PIL import Image" 2>/dev/null; then
  python3 - <<PY
from PIL import Image
img = Image.open("$SRC").convert("RGBA")
img.save("$SCRIPT_DIR/icon.ico", format="ICO",
         sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
PY
  echo "✓ icon.ico erstellt"
else
  echo "⚠ Pillow nicht installiert — installiere mit: pip install Pillow"
fi
