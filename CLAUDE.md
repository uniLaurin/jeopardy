# Jeopardy Game

## Projektübersicht

Jeopardy-Quizspiel für Firmenevents (ursprünglich ERGO). Komplett in **reinem tkinter** gebaut (kein PyQt5, kein tkmacosx), damit es cross-platform auf Mac und Windows als Executable läuft.

## Architektur

**Flow:** `main.py` → Startscreen (Animation) → Settings → Game → Scores

| Datei | Funktion |
|---|---|
| `main.py` | Einstiegspunkt, sequentieller Flow |
| `startscreen.py` | Tkinter Canvas Animation (Typewriter-Titel, Gold-Linie, pulsierender Text mit Farbwechsel, Vignette-Effekt) |
| `settings.py` | Settings Screen: Card-basiertes Layout, Team-Config (2-6 Teams) + Fragenset-Editor (JSON CRUD), Hover/Focus-Effekte |
| `game.py` | Jeopardy-Board mit Flip-Animationen, Raised-Relief-Buttons, Hover-Effekte, dynamische Teams |
| `scores.py` | Animiertes Balkendiagramm mit Gewinner-Hervorhebung (Gold-Border), Titel + Footer |
| `resources.py` | Shared State, Font-Fallback, JSON Load/Save, **Design System** (Farben, Typografie, Spacing) |
| `build.sh` | Build-Script für macOS (venv + PyInstaller), analog zu Easter-Projekt |

**Shared State:** `resources.py` enthält module-level Variablen (`teams`, `team_points`, `categories`, `values`, `questions`, `to_be_switched_int`), die von allen Modulen gelesen/geschrieben werden.

**Design System:** `resources.py` definiert zentrale Konstanten, die alle Module importieren:
- **Farben:** `BLUE`, `GOLD`, `DARK_BLUE`, `CARD_BG`, `BORDER_BLUE`, `SHADOW`, `HOVER_GOLD`, `ACTIVE_GOLD`, `LABEL_GRAY`, `HINT_GRAY`, `ERROR_RED`, `SUCCESS_GREEN`
- **Typografie:** `FONT_TITLE` (48), `FONT_SECTION` (24), `FONT_BODY` (16), `FONT_SMALL` (13), `FONT_BUTTON` (14)
- **Spacing:** `SPACING_MAJOR` (40), `SPACING_SECTION` (20), `SPACING_ELEMENT` (10)

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

PyInstaller kann NICHT cross-compilen. Mac-Build auf Mac, Windows-Build auf Windows.

### GitHub Actions

`.github/workflows/build.yml` baut automatisch für Mac + Windows.
**Trigger:** Nur bei Tag-Push (`v*`), z.B.: `git tag v1.0.0 && git push --tags`

**BEKANNTES PROBLEM:** Die GitHub Action wurde gepusht, aber noch nie ausgeführt. Es fehlt noch ein Tag-Push zum Testen. Mögliche Probleme:
- macOS Runner: `.app` Bundle-Struktur könnte ZIP-Probleme verursachen
- Windows Runner: tkinter ist bei `actions/setup-python` dabei, sollte funktionieren
- Release Job: `softprops/action-gh-release@v2` braucht `permissions: contents: write`

## Bekannte Probleme / TODOs

1. **GitHub Actions noch nicht getestet** -- Tag `v1.0.0` muss gepusht werden um den Build auszulösen
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

## Git

- Remote: `git@github.com:uniLaurin/jeopardy.git`
- Branch: `master`
- `.gitignore`: `build/`, `dist/`, `__pycache__/`, `.idea/`, `.venv/`, `.venv_build/`, `.DS_Store`
