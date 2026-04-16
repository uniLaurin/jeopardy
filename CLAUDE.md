# Jeopardy Game

## Projektübersicht

Jeopardy-Quizspiel für Firmenevents (ursprünglich ERGO). Komplett in **reinem tkinter** gebaut (kein PyQt5, kein tkmacosx), damit es cross-platform auf Mac und Windows als Executable läuft.

## Architektur

**Flow:** `main.py` → Startscreen (Animation) → Settings → Game → Scores

| Datei | Funktion |
|---|---|
| `main.py` | Einstiegspunkt, sequentieller Flow |
| `startscreen.py` | Tkinter Canvas Animation (Typewriter-Titel, Gold-Linie, pulsierender Text mit Farbwechsel, Vignette-Effekt) |
| `settings.py` | Settings Screen mit 4 Tabs (TEAMS / FRAGENSET / DESIGN / START): Team-Config (2-6 Teams), Fragenset-Editor (JSON CRUD), Theme-Auswahl, Hover/Focus-Effekte |
| `game.py` | Jeopardy-Board mit Flip-Animationen, Raised-Relief-Buttons, Hover-Effekte, dynamische Teams |
| `scores.py` | Animiertes Balkendiagramm mit Gewinner-Hervorhebung (Gold-Border), Titel + Footer |
| `resources.py` | Shared State, Font-Fallback, JSON Load/Save, **Design System** (Farben, Typografie, Spacing) |
| `build.sh` | Build-Script für macOS (venv + PyInstaller), analog zu Easter-Projekt |

**Shared State:** `resources.py` enthält module-level Variablen (`teams`, `team_points`, `categories`, `values`, `questions`, `to_be_switched_int`), die von allen Modulen gelesen/geschrieben werden.

**Design System:** `resources.py` definiert zentrale Konstanten, die alle Module importieren:
- **Farben:** `BLUE`, `GOLD`, `DARK_BLUE`, `CARD_BG`, `BORDER_BLUE`, `SHADOW`, `HOVER_GOLD`, `ACTIVE_GOLD`, `LABEL_GRAY`, `HINT_GRAY`, `ERROR_RED`, `SUCCESS_GREEN`
- **Typografie:** `FONT_TITLE` (48), `FONT_SECTION` (24), `FONT_BODY` (16), `FONT_SMALL` (13), `FONT_BUTTON` (14)
- **Spacing:** `SPACING_MAJOR` (40), `SPACING_SECTION` (20), `SPACING_ELEMENT` (10)

### Theme-System (Farb-Paletten)

Die Farbkonstanten (`BLUE`, `GOLD`, `DARK_BLUE`, `CARD_BG`, `BORDER_BLUE`, `SHADOW`, `HOVER_GOLD`, `ACTIVE_GOLD`, `LABEL_GRAY`, `HINT_GRAY`) sind **nicht mehr statisch**, sondern werden aus einem Theme-Dict gesetzt. `ERROR_RED` / `SUCCESS_GREEN` bleiben themeübergreifend konstant.

**Verfügbare Themes** (`r.THEMES` in `resources.py`):
| Key | Label | Look |
|---|---|---|
| `classic` | Classic Jeopardy | Blau (#060CE9) + Gold (#DBAB51) — Default |
| `modern_dark` | Modern Dark | Navy (#0A0A1A) + Neon-Cyan (#00D4FF) — aus `mockups/mockup_2_modern_dark.html` |
| `minimal_clean` | Minimal Clean | Dunkelblau (#1A1A2E) + Amber (#FFAA00) — aus `mockups/mockup_5_minimal_clean.html` |
| `emerald` | Emerald Luxury | Anthrazit (#0D1B14) + Smaragd (#10B981) |

Jedes Theme liefert alle Farb-Slots. Die historischen Namen (`BLUE`, `GOLD`) werden semantisch als "Primär" / "Akzent" interpretiert — sie können je nach Theme auch Cyan, Amber oder Grün enthalten.

**API in `resources.py`:**
- `apply_theme(name)` — setzt die Modul-Konstanten neu
- `load_current_theme()` / `save_current_theme(name)` — Persistenz in `theme.json` (neben `questionsets/`)
- `current_theme_name` — Name des aktuell aktiven Themes

**Startup-Reihenfolge in `main.py`:**
```python
import resources as r
r.apply_theme(r.load_current_theme())   # MUSS vor GUI-Imports stehen
import startscreen, settings, game, scores
```
Das ist wichtig, weil GUI-Module beim Import ihre lokalen Farb-Aliase (`BLUE = r.BLUE` etc.) einmalig aus `r` binden. Würde `apply_theme` erst *nach* den Imports laufen, hätten sie noch die Classic-Werte.

**Rebind bei Theme-Wechsel (Live-Refresh):** Jedes GUI-Modul hat eine `_rebind_colors()`-Funktion, die seine lokalen Farb-Aliase aus `r.*` neu setzt. Wird zu Beginn jeder `run()`-Funktion aufgerufen — und in `settings.py` zusätzlich im `__init__` des Screens.

**DESIGN-Tab in Settings:** Vierter Tab (zwischen FRAGENSET und START). 2×2-Grid aus Theme-Karten mit Name, Beschreibung, 4 Farb-Swatches (Primär/Akzent/Eingabe/Label) und Gold-Border + "AKTIV"-Badge für die aktuelle Wahl. Klick auf eine Karte:
1. Teams/Fragen aus UI in State sichern
2. `r.apply_theme(name)` + `r.save_current_theme(name)`
3. Flag `theme_changed = True`, `root.destroy()`
4. `run()` läuft in einer `while True`-Schleife und baut den Screen frisch auf, bis `theme_changed` False bleibt.

**Fragensets:** JSON-Dateien in `questionsets/`. Format:
```json
{"name": "...", "values": [100,200,...], "categories": [{"name": "...", "questions": ["...", ...]}]}
```

## Build

### Lokal (build.sh)

```bash
bash build.sh --install   # Erstmalig: venv + PyInstaller installieren + bauen
bash build.sh             # Danach: nur bauen (venv wird wiederverwendet)
# Mac: dist/Jeopardy.app | Windows: dist/Jeopardy/Jeopardy.exe
```

Das Script erstellt eine eigene `.venv_build/`, prüft alle Quelldateien + `questionsets/`, und nutzt die `jeopardy.spec`.

**macOS Release:** Nach dem Build wird die `.app` ad-hoc signiert (`codesign -s -`) und per `ditto -c -k --sequesterRsrc --keepParent` zu `dist/Jeopardy-macOS-<arch>.zip` gepackt. Dieses ZIP ist das GitHub-Release-Asset. Da die App unsigniert ist (keine Apple Developer ID), muss der Nutzer einmalig `xattr -cr ~/Downloads/Jeopardy.app` im Terminal ausführen — Anleitung steht im README.

PyInstaller kann NICHT cross-compilen. Mac-Build auf Mac, Windows-Build auf Windows.

### GitHub Actions

`.github/workflows/build.yml` baut automatisch für Mac + Windows.
**Trigger:** Nur bei Tag-Push (`v*`), z.B.: `git tag v1.0.0 && git push --tags`

**BEKANNTES PROBLEM:** Die GitHub Action wurde gepusht, aber noch nie ausgeführt. Es fehlt noch ein Tag-Push zum Testen. Mögliche Probleme:
- macOS Runner: `.app` Bundle-Struktur könnte ZIP-Probleme verursachen
- Windows Runner: tkinter ist bei `actions/setup-python` dabei, sollte funktionieren
- Release Job: `softprops/action-gh-release@v2` braucht `permissions: contents: write`

## Bekannte Probleme / TODOs

1. **GitHub Actions noch nicht getestet** -- Tag `v1.0.0` muss gepusht werden um den Build auszulösen. Actions löst das Gatekeeper-Problem nicht (Runner hat keine Developer ID) — echtes Signing bräuchte Apple Developer Account (99€/Jahr) + Notarization.
2. **Settings Screen Layout** -- Bei sehr kleinen/großen Bildschirmen könnte das .place()-Layout nicht optimal aussehen
3. **Font "Arial Rounded MT Bold"** -- Fallback auf "Arial" → "Helvetica" eingebaut, aber nicht auf einem System ohne den Font getestet
4. **Startscreen nach Settings** -- Wenn man im Settings Escape drückt, beendet sich die App komplett (kein Zurück zum Startscreen)
5. **Kein Zurück-Button im Game** -- Einmal gestartet gibt es keinen Abbruch

## Konventionen

- Alle GUI-Module exportieren `run()` -- erstellt eigenes `tk.Tk()`, läuft `mainloop()`, wird mit `destroy()` beendet
- Font immer über `r.FONT` referenzieren (nie hardcoded)
- **Farben immer über `resources.py`-Konstanten** (`r.BLUE`, `r.GOLD`, etc.) — nie `"blue"` oder hardcoded Hex
- Layout: `.place()` Geometry Manager durchgehend
- Tastenbelegung: `1`-`N` für Teams, `N+1` für Niemand (dynamisch)
- **Buttons:** Primär = Gold-Hintergrund, Sekundär = Grau mit Gold-Hover (via `_make_secondary_btn` / `_bind_hover`)
- **Eingabefelder:** Gold Focus-Border via `_bind_focus_border`
- **Card-Layout** in Settings: `CardFrame`-Klasse für visuelle Sektions-Trennung
- **Theme-Farben:** Alle GUI-Module dürfen lokale Aliase (`BLUE = r.BLUE`) haben, **müssen** aber eine `_rebind_colors()` bereitstellen und sie am Anfang ihrer `run()` aufrufen. Ohne Rebind sehen sie nach einem Theme-Wechsel die alten Classic-Werte.
- **Neue Themes hinzufügen:** Einfach einen Eintrag in `r.THEMES` ergänzen (muss alle Slots `BLUE`, `GOLD`, `DARK_BLUE`, `CARD_BG`, `BORDER_BLUE`, `SHADOW`, `HOVER_GOLD`, `ACTIVE_GOLD`, `LABEL_GRAY`, `HINT_GRAY` sowie `label` und `description` liefern). Der DESIGN-Tab erkennt neue Themes automatisch.

## Git

- Remote: `git@github.com:uniLaurin/jeopardy.git`
- Branch: `master`
- `.gitignore`: `build/`, `dist/`, `__pycache__/`, `.idea/`, `.venv/`, `.venv_build/`, `.DS_Store`
