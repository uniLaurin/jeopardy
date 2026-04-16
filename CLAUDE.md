# Jeopardy Game

## Projektübersicht

Jeopardy-Quizspiel für Firmenevents (ursprünglich ERGO). Komplett in **reinem tkinter** gebaut (kein PyQt5, kein tkmacosx), damit es cross-platform auf Mac und Windows als Executable läuft. **Audio** läuft über `pygame.mixer` — optional, das Spiel funktioniert auch ohne.

## Architektur

**Flow:** `main.py` → Startscreen → (optional) Settings → **Intro** → Game → Scores

| Datei | Funktion |
|---|---|
| `main.py` | Einstiegspunkt, sequentieller Flow |
| `startscreen.py` | Tkinter Canvas Animation (Typewriter-Titel, Gold-Linie, pulsierender Text mit Farbwechsel, Vignette-Effekt) |
| `settings.py` | Settings Screen mit 4 Tabs (TEAMS / FRAGENSET / DESIGN / START): Team-Config (2-6 Teams), Fragenset-Editor (JSON CRUD), Theme-Auswahl, Hover/Focus-Effekte |
| `intro.py` | Cinematic Intro-Sequenz zwischen Settings und Game: 9 Animations-Phasen (Letter-Drop, Tagline, Team-Cards, Stats, "DRÜCKE ENTER"-Pulse). Audio parallel via `audio_player`. Dauer ~18 s aktive Animation + Hold-State |
| `game.py` | Jeopardy-Board mit Flip-Animationen, Raised-Relief-Buttons, Hover-Effekte, dynamische Teams, 30-Sekunden-Timer-Audio pro Frage |
| `scores.py` | Animiertes Balkendiagramm mit Gewinner-Hervorhebung (Gold-Border), Titel + Footer |
| `resources.py` | Shared State, Font-Fallback, JSON Load/Save, **Design System** (Farben, Typografie, Spacing), Theme-Persistenz |
| `audio_player.py` | Wrapper um `pygame.mixer` — lazy init, graceful fallback wenn pygame fehlt. `play_music()`, `stop_music()`, `is_playing()`, `play_sound()` |
| `build.sh` | Build-Script für macOS/Windows (venv + PyInstaller) |
| `jeopardy.spec` | PyInstaller-Spec: bundelt `questionsets/` + `audio/` + pygame-Submodule/SDL-Binaries + plattform-abhängiges App-Icon |
| `assets/` | App-Icon-Dateien: `icon_source.png` (Master), `icon.icns` (macOS), `icon.ico` (Windows), `regenerate_icons.sh` (Helper) |

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
import startscreen, settings, intro, game, scores
```
Das ist wichtig, weil GUI-Module beim Import ihre lokalen Farb-Aliase (`BLUE = r.BLUE` etc.) einmalig aus `r` binden. Würde `apply_theme` erst *nach* den Imports laufen, hätten sie noch die Classic-Werte.

**Rebind bei Theme-Wechsel (Live-Refresh):** Jedes GUI-Modul hat eine `_rebind_colors()`-Funktion, die seine lokalen Farb-Aliase aus `r.*` neu setzt. Wird zu Beginn jeder `run()`-Funktion aufgerufen — und in `settings.py` zusätzlich im `__init__` des Screens.

**DESIGN-Tab in Settings:** Vierter Tab (zwischen FRAGENSET und START). 2×2-Grid aus Theme-Karten mit Name, Beschreibung, 4 Farb-Swatches (Primär/Akzent/Eingabe/Label) und Gold-Border + "AKTIV"-Badge für die aktuelle Wahl. Klick auf eine Karte:
1. Teams/Fragen aus UI in State sichern
2. `r.apply_theme(name)` + `r.save_current_theme(name)`
3. Flag `theme_changed = True`, `root.destroy()`
4. `run()` läuft in einer `while True`-Schleife und baut den Screen frisch auf, bis `theme_changed` False bleibt.

### Game-Board Farb-Logik

`game.py` leitet drei dynamische Farben pro Theme ab (in `_rebind_colors()`):
- **`HOVER_BG = r.CARD_BG`** — Hintergrund beim Hover auf einen Wert-Button
- **`ANSWERED_BG = _darken_hex(r.DARK_BLUE, 0.5)`** — Hintergrund beantworteter Buttons ("vergessen"-Look)
- **`DARK_BLUE`** — explizit beim Aufflippen einer Frage neu gesetzt, damit Hover-Reste nicht in die Fragenansicht überleben (`self.config(background=DARK_BLUE)` in `flip()` kurz vor `visible_text()`)

`_darken_hex(hex, factor)` ist ein Helper in `game.py` — multipliziert jeden RGB-Kanal mit `factor`.

### Audio-System

**Modul `audio_player.py`** (Import-Alias: `audio`):
- Lazy-Init: `pygame.mixer.init()` läuft erst beim ersten `play_*()`-Aufruf
- Wenn pygame fehlt oder Init scheitert: alle Calls werden zu No-Ops, das Spiel läuft weiter ohne Ton (Fallback-Fehler per `print` geloggt)
- Audio-Dateien liegen in `audio/` und werden via `r.resource_path("audio/<filename>")` aufgelöst — funktioniert sowohl in Dev als auch im PyInstaller-Bundle (`sys._MEIPASS`)
- API:
  - `play_music(filename, loop=False)` — Hintergrundmusik (ein Stream zur Zeit)
  - `stop_music()` — idempotent
  - `is_playing()` — True wenn Musik läuft
  - `play_sound(filename)` — Sound-Effekt auf separatem Channel, überlappt mit Musik
- `PYGAME_HIDE_SUPPORT_PROMPT=1` ist gesetzt, um die Banner-Ausgabe zu unterdrücken

**Aktuelle Audio-Dateien** in `audio/`:
| Datei | Verwendung |
|---|---|
| `Jeopardy intro with host introduction.mp3` | Intro-Sequenz (~30 s) — spielt parallel zur Canvas-Animation in `intro.py` |
| `30 Seconds To Answer Jeopardy Timer #challenge #timer #jeopardy.mp3` | Timer pro Frage in `game.py`, **startet wenn die Frage Fullscreen erreicht hat** (Ende von Phase 2 in `flip()`) |

**Timer-Stopp-Trigger in `game.py` (`keyboard_input`):**
- **Leertaste** (`event.keysym == "space"`) → `audio.stop_music()`, Frage bleibt offen
- **Team-Taste `1`–`N`** → Audio stoppt + Punkte vergeben
- **Niemand-Taste `N+1`** → Audio stoppt + keine Punkte
- Safety: `audio.stop_music()` auch nach `root.mainloop()` in `game.run()`, falls Fenster mit offener Frage geschlossen wird

### Intro-Sequenz

**Timeline (`intro.py`):**
| Zeit | Phase | Inhalt |
|---|---|---|
| 0.0 – 2.0 s | Fade-In | Fenster-Alpha 0→1 (via `-alpha`, falls WM unterstützt), Sterne-Feld pulsiert |
| 2.0 – 4.5 s | Letter-Drop | "JEOPARDY" — Buchstaben fallen einzeln (300 ms Offset) mit Bounce |
| 4.5 – 5.5 s | Underline | Gold-Linie wächst von Mitte nach außen unter dem Titel |
| 5.5 – 8.0 s | Tagline | "DAS QUIZ-SPIEL FÜR TEAMS" fadet ein (Color-Interpolation, da tkinter kein Alpha auf Canvas-Items hat) |
| 8.0 – 10.0 s | Shrink | Titel + Linie schrumpfen nach oben, Tagline fadet raus |
| 10.0 – 12.0 s | Team-Cards | Karten erscheinen nacheinander (350 ms Offset) mit Team-Name + Farb-Streifen |
| 13.0 – 15.0 s | Stats | 3 Zahlen fadet nacheinander ein: `KATEGORIEN` / `FRAGEN` / `MAX. PUNKTE` |
| 16.0 s + | Prompt + Hold | "DRÜCKE ENTER ZUM START" in Gold-Border pulsiert unendlich |

**Stats werden dynamisch berechnet** aus dem aktuell geladenen Fragenset:
- `KATEGORIEN = len(r.categories)`
- `FRAGEN = len(r.categories) * len(r.values)`
- `MAX. PUNKTE = sum(r.values) * len(r.categories)`

**Skip:** `Enter`, `KP_Enter` oder `Escape` schließt das Intro jederzeit (nicht nur während der Hold-Phase). Escape setzt zusätzlich `intro.skipped = True`.

**Team-Card-Layout ist responsive:** `card_w` wird dynamisch aus Fensterbreite berechnet (`card_w = min(200, 0.13*w, (0.85*w - gaps) // n_teams)`), damit 6 Teams auch auf 1024px-Screens passen.

**Color-Blending-Helper** (`_blend(c1, c2, t)`) simuliert Alpha-Fading durch RGB-Interpolation, da Canvas-Items kein `alpha` haben. Fade-in = Text startet in Hintergrund-Farbe (unsichtbar) und interpoliert zu Ziel-Farbe.

### Mockups

`mockups/intro_sequence.html` — animierter HTML-Prototyp der Intro-Sequenz (Phasen-Timeline-Overlay, Replay-Button). Dient als visuelle Referenz bei Änderungen an `intro.py`.

**Fragensets:** JSON-Dateien in `questionsets/`. Format:
```json
{"name": "...", "values": [100,200,...], "categories": [{"name": "...", "questions": ["...", ...]}]}
```

## Build

### Lokal (build.sh)

```bash
bash build.sh --install   # Erstmalig: venv + requirements.txt (pyinstaller + pygame) installieren + bauen
bash build.sh             # Danach: nur bauen (venv wird wiederverwendet)
# Mac: dist/Jeopardy.app | Windows: dist/Jeopardy/Jeopardy.exe
```

Das Script:
1. Erstellt/nutzt `.venv_build/`
2. Mit `--install`: installiert aus `requirements.txt` (oder Fallback: `pyinstaller pygame`)
3. Ohne `--install`: prüft ob pygame in venv vorhanden ist, installiert ggf. nach (Intro-Audio würde sonst fehlen)
4. Prüft alle Quelldateien (`main.py`, `startscreen.py`, `settings.py`, `game.py`, `scores.py`, `resources.py`, `intro.py`, `audio_player.py`) + Ordner `questionsets/` + `audio/`
5. Warnt wenn `audio/Jeopardy intro with host introduction.mp3` fehlt (Build läuft trotzdem weiter)
6. Ruft `pyinstaller jeopardy.spec --noconfirm` auf
7. macOS: ad-hoc signiert + ditto-ZIP

**`jeopardy.spec` bundelt:**
- `('questionsets', 'questionsets')` und `('audio', 'audio')` als Data-Ordner
- `collect_submodules('pygame')` → hiddenimports (damit PyInstaller alle pygame-Subpackages findet)
- `collect_dynamic_libs('pygame')` → binaries (SDL-Libs — sonst `silent fail` auf Ziel-Systemen)
- `try/except` um die Collect-Calls, damit der Spec auch ohne pygame im venv parsebar bleibt
- **App-Icon:** `assets/icon.ico` → `EXE(icon=...)` für Windows, `assets/icon.icns` → `BUNDLE(icon=...)` für macOS. Fehlt eine Datei, wird `None` verwendet (Default-Icon, Build läuft weiter).

### App-Icon (`assets/`)

- **`icon_source.png`** — Master-Bild, quadratisch, mind. 1024×1024, transparent. Single Source of Truth.
- **`icon.icns`** — macOS-Bundle mit allen Retina-Größen (16–1024). Wird via `iconutil -c icns` aus einem `iconset/`-Ordner mit 10 sips-Resizes gebaut.
- **`icon.ico`** — Windows-Multi-Res-Icon (16/24/32/48/64/128/256), gebaut via Pillow `Image.save(format="ICO", sizes=[...])`.
- **`regenerate_icons.sh`** — regeneriert beide Dateien aus `icon_source.png`. Braucht macOS-Bordmittel (`iconutil`, `sips`) für `.icns` und Pillow (`pip install Pillow`) für `.ico`. Aufruf: `bash assets/regenerate_icons.sh`.

Um das Icon zu ändern: einfach `icon_source.png` ersetzen und `bash assets/regenerate_icons.sh` laufen lassen, dann neu bauen.

**macOS Release:** Nach dem Build wird die `.app` ad-hoc signiert (`codesign -s -`) und per `ditto -c -k --sequesterRsrc --keepParent` zu `dist/Jeopardy-macOS-<arch>.zip` gepackt. Dieses ZIP ist das GitHub-Release-Asset. Da die App unsigniert ist (keine Apple Developer ID), muss der Nutzer einmalig `xattr -cr ~/Downloads/Jeopardy.app` im Terminal ausführen — Anleitung steht im README.

PyInstaller kann NICHT cross-compilen. Mac-Build auf Mac, Windows-Build auf Windows.

### GitHub Actions

`.github/workflows/build.yml` baut automatisch für Mac + Windows.
**Trigger:** Nur bei Tag-Push (`v*`), z.B.: `git tag v1.0.0 && git push --tags`

**BEKANNTES PROBLEM:** Die GitHub Action wurde gepusht, aber noch nie ausgeführt. Es fehlt noch ein Tag-Push zum Testen. Mögliche Probleme:
- macOS Runner: `.app` Bundle-Struktur könnte ZIP-Probleme verursachen
- Windows Runner: tkinter ist bei `actions/setup-python` dabei, sollte funktionieren
- Release Job: `softprops/action-gh-release@v2` braucht `permissions: contents: write`
- **pygame-Installation im Workflow** muss ggf. mit `pip install -r requirements.txt` ergänzt werden, falls der Workflow noch hardcoded `pip install pyinstaller` nutzt

## Bekannte Probleme / TODOs

1. **GitHub Actions noch nicht getestet** — Tag `v1.0.0` muss gepusht werden um den Build auszulösen. Actions löst das Gatekeeper-Problem nicht (Runner hat keine Developer ID) — echtes Signing bräuchte Apple Developer Account (99€/Jahr) + Notarization.
2. **Settings Screen Layout** — Bei sehr kleinen/großen Bildschirmen könnte das .place()-Layout nicht optimal aussehen
3. **Font "Arial Rounded MT Bold"** — Fallback auf "Arial" → "Helvetica" eingebaut, aber nicht auf einem System ohne den Font getestet
4. **Startscreen nach Settings** — Wenn man im Settings Escape drückt, beendet sich die App komplett (kein Zurück zum Startscreen)
5. **Kein Zurück-Button im Game** — Einmal gestartet gibt es keinen Abbruch
6. **Keine UI-Lautstärke-Steuerung** — System-Lautstärke wird vertraut (bewusste Design-Entscheidung)
7. **Audio-Drift** — Intro-Audio (pygame) und Canvas-Animation (tkinter `after()`) laufen auf getrennten Pfaden — bei 30 s Clip nicht hörbar, aber kein garantierter Sync
8. **`tkinter -alpha` + Fullscreen** — auf Linux-WMs ggf. ignoriert; `intro.py` fängt `TclError` ab und zeigt das Fenster dann einfach voll opak

## Konventionen

- Alle GUI-Module exportieren `run()` — erstellt eigenes `tk.Tk()`, läuft `mainloop()`, wird mit `destroy()` beendet
- Font immer über `r.FONT` referenzieren (nie hardcoded)
- **Farben immer über `resources.py`-Konstanten** (`r.BLUE`, `r.GOLD`, etc.) — nie `"blue"` oder hardcoded Hex. Ausnahmen: pure Grautöne (`#404040` für Borders), die theme-neutral sind.
- Layout: `.place()` Geometry Manager durchgehend
- Tastenbelegung: `1`-`N` für Teams, `N+1` für Niemand (dynamisch), `Space` stoppt Frage-Timer-Audio
- **Buttons:** Primär = Gold-Hintergrund, Sekundär = Grau mit Gold-Hover (via `_make_secondary_btn` / `_bind_hover`)
- **Eingabefelder:** Gold Focus-Border via `_bind_focus_border`
- **Card-Layout** in Settings: `CardFrame`-Klasse für visuelle Sektions-Trennung
- **Theme-Farben:** Alle GUI-Module dürfen lokale Aliase (`BLUE = r.BLUE`) haben, **müssen** aber eine `_rebind_colors()` bereitstellen und sie am Anfang ihrer `run()` aufrufen. Ohne Rebind sehen sie nach einem Theme-Wechsel die alten Classic-Werte.
- **Neue Themes hinzufügen:** Einfach einen Eintrag in `r.THEMES` ergänzen (muss alle Slots `BLUE`, `GOLD`, `DARK_BLUE`, `CARD_BG`, `BORDER_BLUE`, `SHADOW`, `HOVER_GOLD`, `ACTIVE_GOLD`, `LABEL_GRAY`, `HINT_GRAY` sowie `label` und `description` liefern). Der DESIGN-Tab erkennt neue Themes automatisch.
- **Neue Audio-Assets:** Datei in `audio/` ablegen, über `audio.play_music("filename.mp3")` abspielen. PyInstaller bundelt den Ordner automatisch (via `jeopardy.spec`).
- **Canvas-Animations:** Kein echtes Alpha möglich — für Fade-Effekte `_blend(c1, c2, t)` in `intro.py` nutzen (RGB-Interpolation). Pattern: Start-Item in Hintergrundfarbe erzeugen (unsichtbar), dann zu Ziel-Farbe interpolieren.

## Git

- Remote: `git@github.com:uniLaurin/jeopardy.git`
- Branch: `master`
- `.gitignore`: `build/`, `dist/`, `__pycache__/`, `.idea/`, `.venv/`, `.venv_build/`, `.DS_Store`
