#!/bin/bash
cd "$(dirname "$0")"
echo ""
echo "Entferne Quarantäne-Flag von Jeopardy.app..."
xattr -cr Jeopardy.app
echo ""
echo "✓ Fertig! Jeopardy.app kann jetzt per Doppelklick gestartet werden."
echo ""
read -p "Drücke Enter zum Schließen..."
