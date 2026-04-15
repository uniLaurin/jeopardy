"""
Einstiegspunkt für das Jeopardy-Spiel.

Flow:
    Startscreen → (optional) Settings → Game → Scores

Der User entscheidet im Startscreen mit der Tastatur:
    ENTER  → Spiel direkt starten (Default-Fragenset, aktuelle Teams)
    S      → Settings öffnen (Teams + Fragensets konfigurieren)
    ESCAPE → Anwendung beenden

Jedes Modul exportiert eine `run()`-Funktion, die ein eigenes `tk.Tk()`-Fenster
erstellt, `mainloop()` aufruft und nach `destroy()` zurückkehrt.
"""

import sys

import resources as r
# Theme laden BEVOR die GUI-Module importieren, damit deren lokale
# Farb-Aliase bereits mit der gewählten Palette gebunden werden.
r.apply_theme(r.load_current_theme())

import startscreen
import settings
import game
import scores


def main():
    # 1. Startscreen mit Animation (Typewriter-Titel, pulsierender Text)
    startscreen.run()

    # Escape im Startscreen → sofort beenden
    if startscreen.quit_app:
        sys.exit(0)

    # 2. Sicherstellen, dass mindestens das Default-Fragenset existiert
    r.ensure_default_questionset()

    # 3. Settings nur anzeigen, wenn der User im Startscreen 'S' gedrückt hat
    if startscreen.show_settings:
        settings.run()
    else:
        # Direkter Flow: Default-Fragenset laden (wie es Settings sonst tun würde)
        r.load_question_set("ergo_default.json")

    # 4. Team-Punkte und to_be_switched_int zurücksetzen (frisches Spiel)
    r.reset_game_state()

    # 5. Das eigentliche Jeopardy-Board anzeigen
    game.run()

    # 6. Ergebnisse anzeigen: animiertes Balkendiagramm mit Gewinner-Highlight
    scores.run()


if __name__ == "__main__":
    main()
