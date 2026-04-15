#!/bin/bash
# =============================================
# Jeopardy – Build Script für Intel & Apple Silicon
# Benötigt nur: Python 3 von python.org
#
# Ausführen:
#   bash build.sh            → nur bauen (venv muss existieren)
#   bash build.sh --install  → installieren + bauen
# =============================================

set -e

# ── Farben ────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "========================================="
echo "  Jeopardy – Build Script"
echo "  Architektur: $(uname -m)"
echo "========================================="
echo ""

# ── Python prüfen ─────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}FEHLER: python3 nicht gefunden!${NC}"
  echo "Bitte Python 3 von https://python.org/downloads installieren."
  exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION gefunden${NC}"

# ── Virtuelle Umgebung ────────────────────────
VENV_DIR=".venv_build"

if [ -d "$VENV_DIR" ]; then
  echo -e "${YELLOW}→ Bestehende venv gefunden, wird wiederverwendet${NC}"
else
  echo "→ Erstelle virtuelle Umgebung..."
  python3 -m venv "$VENV_DIR"
  echo -e "${GREEN}✓ venv erstellt${NC}"
fi

# venv aktivieren
source "$VENV_DIR/bin/activate"

# ── Dependencies nur mit --install Flag ───────
if [ "$1" = "--install" ]; then
  echo "→ pip aktualisieren..."
  pip install --upgrade pip --quiet

  echo "→ Installiere PyInstaller..."
  pip install pyinstaller --quiet

  echo -e "${GREEN}✓ Alle Pakete installiert${NC}"
else
  echo -e "${YELLOW}→ Überspringe Installation (kein --install Flag)${NC}"
fi

# ── Quelldateien prüfen ──────────────────────
MISSING=0
for f in "main.py" "startscreen.py" "settings.py" "game.py" "scores.py" "resources.py"; do
  if [ ! -f "$f" ]; then
    echo -e "${RED}FEHLER: Datei nicht gefunden → \"$f\"${NC}"
    MISSING=1
  fi
done
if [ ! -d "questionsets" ]; then
  echo -e "${RED}FEHLER: Ordner 'questionsets/' nicht gefunden${NC}"
  MISSING=1
fi
if [ $MISSING -eq 1 ]; then
  echo ""
  echo "Bitte build.sh im Projektordner ausführen."
  deactivate
  exit 1
fi
echo -e "${GREEN}✓ Alle Quelldateien vorhanden${NC}"

# ── Alten Build löschen ───────────────────────
echo "→ Alten Build aufräumen..."
rm -rf dist build

# ── PyInstaller ───────────────────────────────
echo ""
echo "→ Starte PyInstaller..."
echo ""

pyinstaller jeopardy.spec --noconfirm

# ── venv deaktivieren ─────────────────────────
deactivate

# ── Ergebnis ──────────────────────────────────
echo ""
echo "========================================="
if [ "$(uname)" = "Darwin" ] && [ -d "dist/Jeopardy.app" ]; then
  echo -e "${GREEN}  ✓ Build erfolgreich! ($(uname -m))${NC}"
  echo "  App: dist/Jeopardy.app"

  # Ad-hoc signieren (entfernt "beschädigt"-Fehler auf Ziel-Macs)
  echo ""
  echo "→ Ad-hoc Signatur..."
  codesign --force --deep -s - dist/Jeopardy.app 2>/dev/null && \
    echo -e "${GREEN}✓ Signiert${NC}" || \
    echo -e "${YELLOW}⚠ codesign übersprungen${NC}"

  # ZIP mit ditto (behält .app-Struktur + macOS-Metadaten)
  echo "→ Erstelle ZIP mit ditto..."
  ZIP_NAME="Jeopardy-macOS-$(uname -m).zip"
  rm -f "dist/$ZIP_NAME"
  (cd dist && ditto -c -k --sequesterRsrc --keepParent Jeopardy.app "$ZIP_NAME")
  echo -e "${GREEN}✓ ZIP: dist/$ZIP_NAME${NC}"
elif [ -d "dist/Jeopardy" ]; then
  echo -e "${GREEN}  ✓ Build erfolgreich! ($(uname -m))${NC}"
  echo "  Ordner: dist/Jeopardy/"
  echo "  Executable: dist/Jeopardy/Jeopardy"
else
  echo -e "${RED}  ✗ Build fehlgeschlagen – Output nicht gefunden${NC}"
fi
echo "========================================="
echo ""
