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

*macOS `.app` & Windows `.exe` — keine Installation, einfach starten.*

</div>

### macOS: Gatekeeper-Hinweis

Da die App nicht mit einer Apple Developer ID signiert ist, blockiert macOS sie nach dem Download. Einmalig im Terminal ausführen, um die Quarantäne zu entfernen:

```bash
xattr -cr ~/Downloads/Jeopardy.app
```

Danach per Doppelklick starten.



## Steuerung im Spiel

| Taste | Funktion |
|---|---|
| `1` … `N` | Team, das die Frage korrekt beantwortet hat |
| `N+1` | Niemand — Punkte werden abgezogen |
| `Esc` | Schließt den aktuellen Screen |
|!| Absatz beim beschreiben der Fragen in den settings|
