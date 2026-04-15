"""
Scores-Screen — animiertes Balkendiagramm mit den Endpunktzahlen.

Zeigt für jedes Team einen goldenen Balken, dessen Höhe zu den erreichten
Punkten proportional ist (in Prozent der maximal möglichen Punkte).
Der Gewinner (höchste Punktzahl) bekommt einen dickeren Gold-Border und
ein "GEWINNER!" Label über seinem Balken.

Animation: Die Balken wachsen von 6px Starthöhe schrittweise auf ihre
finale Höhe. Mit jedem Animationsschritt bewegt sich auch das darüber
liegende Winner-Label und der Schatten mit.
"""

import tkinter as tk
import resources as r
import math

# Lokale Aliase — werden in run() aus r.* neu gebunden (Theme-Support)
BLUE = r.BLUE
GOLD = r.GOLD


def _rebind_colors():
    global BLUE, GOLD
    BLUE = r.BLUE
    GOLD = r.GOLD


class BLabel(tk.Label):
    """Ein einzelner Punktebalken für ein Team im Scores-Diagramm.

    Enthält selbst den Balken, einen Schatten dahinter, Team-Namen, Punktzahl
    und (beim Gewinner) ein 'GEWINNER!' Label darüber.
    """

    def __init__(self, master, team_name, team_color, points, is_winner,
                 p_width, p_height, p_y, p_x, **kwargs):
        self.y = p_y          # Y-Position (wird während Animation aktualisiert)
        self.x = p_x          # X-Position (statisch)
        self.is_winner = is_winner
        super().__init__(master, **kwargs)
        self.place(width=p_width, height=p_height, x=self.x, y=self.y)

        # --- Gewinner-Spezial-Styling ---
        if is_winner:
            # Prominenter Gold-Rahmen (6px statt Standard)
            self.config(highlightbackground=GOLD, highlightthickness=6)

            # "GEWINNER!" Label über dem Balken
            self.winner_label = tk.Label(
                master, text="GEWINNER!",
                font=(r.FONT, 14, "bold"),
                fg=GOLD, bg=BLUE
            )
            self.winner_label.place(x=self.x + p_width // 2, y=self.y - 30, anchor="s")

        # --- Schatten hinter dem Balken für 3D-Tiefe ---
        self.shadow = tk.Label(master, text="", background=r.SHADOW)
        self.shadow.place(width=p_width + 6, height=p_height + 6,
                          x=self.x + 3, y=self.y + 3)
        self.shadow.lower()  # Hinter den Balken schieben

        # --- Team-Name unter dem Balken (in Teamfarbe) ---
        name_font_size = 22 if is_winner else 18  # Gewinner etwas größer
        self.name_label = tk.Label(
            master, text=team_name,
            font=(r.FONT, name_font_size, "bold"),
            fg=team_color,
            bg=BLUE
        )
        self.name_label.place(x=self.x + p_width // 2,
                              y=self.y + p_height + 12, anchor="n")

        # --- Punktzahl in Weiß unter dem Team-Namen ---
        self.points_label = tk.Label(
            master, text=f"{points} Punkte",
            font=(r.FONT, 16, "bold"),
            fg="white", bg=BLUE
        )
        self.points_label.place(x=self.x + p_width // 2,
                                y=self.y + p_height + 42, anchor="n")

    def animation(self, n):
        """Lässt den Balken schrittweise nach oben wachsen.

        n: Anzahl der Animationsschritte (proportional zu den Punkten)
           Jeder Schritt: +3px Höhe, -3px Y-Position, alle 40ms.

        Winner-Label und Schatten werden synchron mitgezogen.
        """
        def go(n):
            y = self.y
            self.y = self.y - 3
            if n > 0:
                self.place(height=self.winfo_height() + 3, y=y - 3)
                # Winner-Label mit nach oben ziehen
                if self.is_winner and hasattr(self, 'winner_label'):
                    self.winner_label.place(y=y - 33)
                # Schatten wächst mit
                self.shadow.place(height=self.winfo_height() + 9, y=y)
                self.master.after(40, lambda: go(n - 1))

        go(n * 2)  # *2 damit die Animation etwas länger/dramatischer wirkt


def run():
    """Entry-Point für das Scores-Modul. Wird von main.py aufgerufen."""
    _rebind_colors()
    root = tk.Tk()
    root.title("Jeopardy! - Scores")
    root.attributes("-fullscreen", True)
    root.configure(bg=BLUE)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    # --- Titel: "ERGEBNISSE" ---
    tk.Label(
        root, text="ERGEBNISSE",
        font=(r.FONT, r.FONT_TITLE, "bold"),
        fg=GOLD, bg=BLUE
    ).place(x=screen_w // 2, y=30, anchor="n")

    # Goldene Dekorationslinie unter dem Titel
    canvas = tk.Canvas(root, bg=BLUE, highlightthickness=0, height=4)
    canvas.place(x=screen_w // 2 - 200, y=95, width=400, height=4)
    canvas.create_line(0, 2, 400, 2, fill=GOLD, width=3)

    # --- Layout-Berechnung für die Balken ---
    num_teams = len(r.teams)
    block_width = min(200, (screen_w - 100) // max(num_teams, 1))
    block_height = 6  # Starthöhe der Balken (wachsen dann durch Animation)
    allpoints = sum(r.values) * len(r.categories)  # Max. erreichbare Punkte

    # Balken horizontal zentrieren (50px Abstand zwischen Balken)
    total_width = block_width * num_teams + (num_teams - 1) * 50
    start_x = (screen_w - total_width) / 2
    base_y = (screen_h / 2) + 180  # Basislinie aller Balken

    # Gewinner ermitteln (kann mehrere bei Gleichstand geben)
    max_points = max(r.team_points) if r.team_points else 0

    # --- Balken erstellen ---
    labels = []
    for i, team in enumerate(r.teams):
        # Nur "echter" Gewinner wenn max_points > 0 (verhindert dass bei 0:0:0 alle gewinnen)
        is_winner = r.team_points[i] == max_points and max_points > 0
        lbl = BLabel(
            root, team["name"], team["color"], r.team_points[i], is_winner,
            p_width=block_width, p_height=block_height,
            p_x=start_x + (block_width + 50) * i, p_y=base_y - block_height,
            background=GOLD, borderwidth=2, relief="solid",
            highlightbackground=GOLD, highlightthickness=2,
            font=(r.FONT, 20, "bold")
        )
        labels.append(lbl)

    # --- Animation starten ---
    for i, lbl in enumerate(labels):
        if allpoints > 0:
            # Prozentualer Anteil der erreichten Punkte → Anzahl der Animationsschritte
            points_pct = math.ceil(100 * (r.team_points[i] / allpoints))
        else:
            points_pct = 0
        lbl.animation(points_pct)

    # --- Footer-Hinweis ---
    tk.Label(
        root, text="ENTER zum Beenden",
        font=(r.FONT, 14), fg=r.LABEL_GRAY, bg=BLUE
    ).place(x=screen_w // 2, y=screen_h - 50, anchor="n")

    # Enter oder Escape beendet den Scores-Screen (und damit das Spiel)
    root.bind("<Return>", lambda event: root.destroy())
    root.bind("<Escape>", lambda event: root.destroy())

    root.mainloop()


if __name__ == '__main__':
    run()
