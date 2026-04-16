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

Dieses Projekt ist ein vollständig ausgearbeitetes **Jeopardy-Quizspiel**. Es führt Spieler durch einen kinoreifen Flow — von einer animierten Title-Sequence über ein flexibles Settings-Menü bis hin zum klassischen Jeopardy-Board mit Flip-Animationen und einem animierten Scoreboard.

<div align="center">

## Download

[![Download](https://img.shields.io/badge/%E2%AC%87%20Download%20hier-Jeopardy%20laden-gold?style=for-the-badge&labelColor=001f5b&color=d4af37)](https://github.com/uniLaurin/jeopardy/releases/latest/download/Jeopardy-macOS-arm64.zip)

</div>

### macOS: Gatekeeper-Hinweis

Da die App nicht mit einer Apple Developer ID signiert ist, blockiert macOS sie nach dem Download. Einmalig im Terminal ausführen, um die Quarantäne zu entfernen:

```bash
xattr -cr ~/Downloads/Jeopardy.app
```

Danach per Doppelklick starten.



## Steuerung

Das Spiel läuft durch mehrere Screens — hier die Tastenbelegung pro Bildschirm.

### Startscreen

| Taste | Funktion |
|---|---|
| `Enter` | Spiel starten (direkt ins Intro) |
| `S` | Einstellungen öffnen (Teams, Fragenset, Design) |
| `Esc` | App beenden |

### Einstellungen

| Taste / Eingabe | Funktion |
|---|---|
| `Esc` | Einstellungen schließen und App beenden |
| `!` *(im Fragentext)* | Absatz-Trennzeichen — trennt z. B. deutsche und englische Version einer Frage mit einem doppelten Zeilenumbruch |

Die Einstellungen haben vier Tabs: **TEAMS** (2–6 Teams, Name + Farbe), **FRAGENSET** (Editor für JSON-Fragensets), **DESIGN** (Farb-Theme auswählen) und **START** (Spiel starten).

### Intro-Sequenz

| Taste | Funktion |
|---|---|
| `Enter` | Intro überspringen, direkt zum Spiel |
| `Esc` | Intro überspringen |

### Spiel (Jeopardy-Board)

**Maus:**

| Aktion | Funktion |
|---|---|
| Klick auf Wert-Feld | Frage aufdecken (Flip-Animation) |

**Tastatur — nur während eine Frage offen ist:**

| Taste | Funktion |
|---|---|
| `Space` | 30-Sekunden-Timer-Audio stoppen — Frage bleibt offen und wartet auf eine Antwort |
| `1` … `N` | Team `1` bis `N` hat korrekt geantwortet → bekommt die Punkte der Frage |
| `N+1` | Niemand hat geantwortet → keine Punktevergabe (es werden **keine** Punkte abgezogen) |

Dabei ist `N` die Anzahl der konfigurierten Teams. Beispiel bei 3 Teams: `1`, `2`, `3` = Teams, `4` = Niemand.

### Scoreboard

| Taste | Funktion |
|---|---|
| `Enter` | Scoreboard schließen |
| `Esc` | Scoreboard schließen |
