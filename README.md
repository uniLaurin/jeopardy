<div align="center">

# Jeopardy

### Ein elegantes Jeopardy-Quizspiel für Firmenevents & Team-Spieleabende

*Gebaut in reinem Python & tkinter — cross-platform, ohne Dependencies, als Executable verteilbar.*

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-lightgrey?style=flat-square)](#build)
[![Build](https://img.shields.io/badge/Build-PyInstaller-orange?style=flat-square)](https://pyinstaller.org/)
[![License](https://img.shields.io/badge/License-MIT-gold?style=flat-square)](#lizenz)

---

</div>

## Überblick

Dieses Projekt ist ein vollständig ausgearbeitetes **Jeopardy-Quizspiel**, ursprünglich für ein ERGO-Firmenevent entwickelt. Es führt Spieler durch einen kinoreifen Flow — von einer animierten Title-Sequence über ein flexibles Settings-Menü bis hin zum klassischen Jeopardy-Board mit Flip-Animationen und einem animierten Scoreboard.

Das Besondere: **kein PyQt, kein tkmacosx, keine exotischen Dependencies** — alles läuft mit reinem `tkinter` aus der Standardbibliothek. Dadurch ist der Build winzig, startet sofort und lässt sich als einzelne Executable für Mac (`.app`) und Windows (`.exe`) ausliefern.

## Features

| | |
|---|---|
| **Animierter Startscreen** | Typewriter-Titel, pulsierender Gold-Text, Vignette-Effekt, Farbwechsel |
| **Dynamische Teams** | 2–6 Teams konfigurierbar, eigene Namen, Tastenbelegung `1`…`N` |
| **Fragenset-Editor** | JSON-basierte CRUD-Oberfläche zum Erstellen, Bearbeiten & Löschen |
| **Jeopardy-Board** | Flip-Animationen, Raised-Relief-Buttons, Hover-Effekte |
| **Live-Scoreboard** | Animiertes Balkendiagramm mit Gold-Border für den Gewinner |
| **Design-System** | Zentrale Farben, Typografie & Spacing über `resources.py` |
| **Cross-Platform Build** | `build.sh` + GitHub Actions für Mac- und Windows-Releases |

## Screenshots & Mockups

Im Ordner [`mockups/`](./mockups) liegen mehrere HTML-Design-Varianten, die während der Entwicklung entstanden sind:

- `mockup_1_classic.html` — Klassischer Jeopardy-Look
- `mockup_2_modern_dark.html` — Moderne Dark-UI
- `mockup_3_elegant_premium.html` — **Gewählter Stil** (elegant, premium)
- `mockup_4_vibrant_playful.html` — Verspielt & bunt
- `mockup_5_minimal_clean.html` — Minimalistisch

Einfach im Browser öffnen, um die Designs zu vergleichen.

## Projektstruktur

```
Jepoardy/
├── main.py              Einstiegspunkt — sequentieller Flow
├── startscreen.py       Canvas-Animation (Titel, Gold-Linie, Vignette)
├── settings.py          Team-Setup + Fragenset-Editor (Card-Layout)
├── game.py              Jeopardy-Board mit Flip-Animationen
├── scores.py            Animiertes Balkendiagramm
├── resources.py         Shared State + Design System (Farben, Fonts)
│
├── questionsets/        JSON-Fragensets
│   └── ergo_default.json
├── mockups/             HTML-Design-Mockups
│
├── build.sh             Build-Skript (venv + PyInstaller)
├── jeopardy.spec        PyInstaller-Konfiguration
└── .github/workflows/   CI für automatisierte Mac/Windows-Builds
```

**Flow:**
```
main.py  →  Startscreen  →  Settings  →  Game  →  Scores
```

## Installation & Start

### Aus dem Quellcode ausführen

```bash
git clone git@github.com:uniLaurin/jeopardy.git
cd jeopardy
python3 main.py
```

> **Hinweis:** Es werden keine externen Pakete benötigt — nur Python 3.10+ mit dem mitgelieferten `tkinter`-Modul.

### Als Executable bauen

```bash
# Erstmalig: venv einrichten + PyInstaller installieren + bauen
bash build.sh --install

# Folge-Builds (venv wird wiederverwendet)
bash build.sh
```

Das Resultat landet in `dist/`:

- **macOS:** `dist/Jeopardy.app`
- **Windows:** `dist/Jeopardy/Jeopardy.exe`

> PyInstaller kann **nicht** cross-compilen — Mac-Builds müssen auf Mac, Windows-Builds auf Windows erzeugt werden.

### Automatisierte Releases via GitHub Actions

Ein Push eines Git-Tags triggert den CI-Build für beide Plattformen gleichzeitig:

```bash
git tag v1.0.0
git push --tags
```

Die fertigen Artefakte werden automatisch als GitHub Release hochgeladen.

## Fragensets

Fragensets sind schlichte JSON-Dateien im Ordner `questionsets/`:

```json
{
  "name": "ERGO Default",
  "values": [100, 200, 300, 400, 500],
  "categories": [
    {
      "name": "Versicherungen",
      "questions": [
        "Frage für 100",
        "Frage für 200",
        "Frage für 300",
        "Frage für 400",
        "Frage für 500"
      ]
    }
  ]
}
```

Neue Sets können direkt im **Settings-Screen** über den eingebauten Editor erstellt werden — keine manuelle JSON-Bearbeitung nötig.

## Design-System

Alle Farben, Fonts und Spacings sind zentral in `resources.py` definiert und werden von allen Modulen importiert. Dadurch bleibt das Look & Feel konsistent und lässt sich an einer einzigen Stelle anpassen.

| Rolle | Konstante |
|---|---|
| Primärfarbe | `BLUE`, `DARK_BLUE` |
| Akzentfarbe | `GOLD`, `HOVER_GOLD`, `ACTIVE_GOLD` |
| Cards & Rahmen | `CARD_BG`, `BORDER_BLUE`, `SHADOW` |
| Text & Hints | `LABEL_GRAY`, `HINT_GRAY` |
| Status | `ERROR_RED`, `SUCCESS_GREEN` |
| Typografie | `FONT_TITLE` (48), `FONT_SECTION` (24), `FONT_BODY` (16), `FONT_SMALL` (13), `FONT_BUTTON` (14) |
| Spacing | `SPACING_MAJOR` (40), `SPACING_SECTION` (20), `SPACING_ELEMENT` (10) |

## Steuerung im Spiel

| Taste | Funktion |
|---|---|
| `1` … `N` | Team, das die Frage korrekt beantwortet hat |
| `N+1` | Niemand — Punkte werden abgezogen |
| `Esc` | Schließt den aktuellen Screen |

## Bekannte Einschränkungen

- Kein „Zurück"-Button im Game — einmal gestartet, keine Abbruchmöglichkeit
- `Esc` im Settings-Screen beendet die App komplett (kein Rücksprung zum Startscreen)
- Layout mit `.place()` kann bei extrem kleinen/großen Displays suboptimal wirken
- Font `Arial Rounded MT Bold` mit Fallback auf `Arial` → `Helvetica`

## Contributing

Pull Requests und Issues sind willkommen. Bitte beachte die Konventionen:

- **Farben & Fonts** ausschließlich über `resources.py`-Konstanten (`r.GOLD`, `r.FONT`, …)
- **Layout** durchgehend mit `.place()`
- GUI-Module exportieren ein `run()`, das `tk.Tk()` erstellt und mit `destroy()` beendet
- Buttons: Primär = Gold-Hintergrund, Sekundär = Grau mit Gold-Hover

## Lizenz

MIT — frei nutzbar für private und kommerzielle Events.

---

<div align="center">

*Gebaut mit Python & tkinter — schlicht, schnell, schön.*

</div>
