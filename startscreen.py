"""
Startbildschirm mit animiertem Jeopardy-Titel.

Animationskette (sequentiell):
    1. Typewriter-Animation: "JEOPARDY!" wird Buchstabe für Buchstabe geschrieben
    2. Gold-Linie wächst von der Mitte nach außen unter dem Titel
    3. "ENTER = Start    ·    S = Settings" pulsiert in zwei Gold-Tönen

Der User kann wählen:
    ENTER / Numpad-Enter  →  Spiel direkt starten (Settings überspringen)
    S                     →  Settings öffnen
    ESCAPE                →  Anwendung beenden

Das Modul exportiert `show_settings` als globale Variable, die nach `run()`
angibt, ob die Settings geöffnet werden sollen.
"""

import tkinter as tk
import resources as r


# Lokale Aliase für bessere Lesbarkeit
JEOPARDY_BLUE = r.BLUE
JEOPARDY_GOLD = r.GOLD

# Modul-globales Flag, das nach run() ausgewertet wird.
# True  → User hat 'S' gedrückt → Settings anzeigen
# False → User hat Enter gedrückt → Settings überspringen, direkt ins Spiel
show_settings = False
# True wenn User Escape gedrückt hat → Anwendung beenden
quit_app = False


class StartScreen:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg=JEOPARDY_BLUE)
        self.root.attributes("-fullscreen", True)  # Vollbildmodus

        # Bildschirmabmessungen für alle Koordinaten-Berechnungen merken
        self.w = root.winfo_screenwidth()
        self.h = root.winfo_screenheight()

        # Canvas füllt den gesamten Bildschirm — alles wird darauf gezeichnet
        self.canvas = tk.Canvas(
            root, bg=JEOPARDY_BLUE, highlightthickness=0,
            width=self.w, height=self.h
        )
        self.canvas.pack(fill="both", expand=True)

        # Vignette-Effekt: dunkle Ränder und Ecken für Tiefenwirkung
        self._draw_vignette()

        # Titel-Text (wird von animate_title() Buchstabe für Buchstabe befüllt)
        self.title_text = self.canvas.create_text(
            self.w // 2, self.h // 2 - 60,
            text="", font=(r.FONT, 100, "bold"),
            fill=JEOPARDY_GOLD
        )

        # Dekorative Gold-Linie unter dem Titel (wächst animiert von Mitte nach außen)
        cy = self.h // 2 + 40
        self.line = self.canvas.create_line(
            self.w // 2, cy, self.w // 2, cy,  # Startet als Punkt in der Mitte
            fill=JEOPARDY_GOLD, width=4
        )

        # "ENTER = Start    ·    S = Settings" Text — wird pulsiert via pulse_enter()
        self.enter_text = self.canvas.create_text(
            self.w // 2, self.h // 2 + 120,
            text="", font=(r.FONT, 28),
            fill=JEOPARDY_GOLD
        )

        # Unterstrich unter dem pulsierenden Text (gleicher Pulseffekt)
        uy = self.h // 2 + 145
        self.enter_underline = self.canvas.create_line(
            self.w // 2 - 280, uy, self.w // 2 + 280, uy,
            fill="", width=2
        )

        # Tastenbindings:
        #   Enter → Spiel direkt starten (Settings überspringen)
        #   S     → Settings öffnen
        #   Esc   → Anwendung beenden
        self.root.bind("<Return>", lambda e: self._choose(settings=False))
        self.root.bind("<KP_Enter>", lambda e: self._choose(settings=False))
        self.root.bind("<s>", lambda e: self._choose(settings=True))
        self.root.bind("<S>", lambda e: self._choose(settings=True))
        self.root.bind("<Escape>", lambda e: self._quit())

        # Animation-Chain starten (→ animate_line → pulse_enter)
        self.animate_title("JEOPARDY!", 0)

    def _choose(self, settings):
        """Setzt das globale Flag und schließt den Startscreen."""
        global show_settings
        show_settings = settings
        self.root.destroy()

    def _quit(self):
        """Escape: Anwendung komplett beenden."""
        global quit_app
        quit_app = True
        self.root.destroy()

    def _draw_vignette(self):
        """Zeichnet eine mehrschichtige Vignette (Rand-Abdunklung) für Tiefenwirkung.

        Da tkinter keine echten Gradienten unterstützt, werden Rechtecke mit
        abnehmender Stipple-Dichte (gray50 → gray25 → gray12) übereinander
        gelegt, was einen weichen Übergang simuliert.
        """
        strip_h = 30
        stipples = ["gray50", "gray25", "gray12"]  # Von dicht nach leicht

        # Oberer Rand
        for i, stipple in enumerate(stipples):
            self.canvas.create_rectangle(
                0, i * strip_h, self.w, (i + 1) * strip_h,
                fill=r.SHADOW, outline="", stipple=stipple
            )

        # Unterer Rand (gespiegelt)
        for i, stipple in enumerate(stipples):
            y_start = self.h - (i + 1) * strip_h
            self.canvas.create_rectangle(
                0, y_start, self.w, y_start + strip_h,
                fill=r.SHADOW, outline="", stipple=stipple
            )

        # Linker Rand
        strip_w = 40
        for i, stipple in enumerate(stipples):
            self.canvas.create_rectangle(
                i * strip_w, 0, (i + 1) * strip_w, self.h,
                fill=r.SHADOW, outline="", stipple=stipple
            )

        # Rechter Rand (gespiegelt)
        for i, stipple in enumerate(stipples):
            x_start = self.w - (i + 1) * strip_w
            self.canvas.create_rectangle(
                x_start, 0, x_start + strip_w, self.h,
                fill=r.SHADOW, outline="", stipple=stipple
            )

        # Zusätzliche Eckenverdunkelung über Ovale
        corner_size = 200
        for cx, cy in [(0, 0), (self.w, 0), (0, self.h), (self.w, self.h)]:
            self.canvas.create_oval(
                cx - corner_size, cy - corner_size,
                cx + corner_size, cy + corner_size,
                fill=r.SHADOW, outline="", stipple="gray25"
            )

    def animate_title(self, full_text, idx):
        """Typewriter-Effekt: fügt alle 120ms einen Buchstaben hinzu.

        Nach Abschluss startet die nächste Animation (animate_line).
        try/except TclError fängt den Fall ab, dass das Fenster bereits
        zerstört wurde während noch ein after()-Callback geplant war.
        """
        try:
            if idx <= len(full_text):
                self.canvas.itemconfig(self.title_text, text=full_text[:idx])
                self.root.after(120, lambda: self.animate_title(full_text, idx + 1))
            else:
                self.animate_line(0)
        except tk.TclError:
            pass

    def animate_line(self, progress):
        """Lässt die Gold-Linie unter dem Titel von der Mitte nach außen wachsen.

        Die Linie wächst alle 3ms um 4 Pixel in beide Richtungen bis max_width.
        Danach startet der Pulseffekt für den "Press ENTER" Text.
        """
        try:
            cx = self.w // 2
            cy = self.h // 2 + 40
            max_width = 350
            if progress <= max_width:
                self.canvas.coords(self.line, cx - progress, cy, cx + progress, cy)
                self.root.after(3, lambda: self.animate_line(progress + 4))
            else:
                self.pulse_enter(0)
        except tk.TclError:
            pass

    def pulse_enter(self, step):
        """Pulsiert den 'Press ENTER' Text mit einem dreiteiligen Zyklus.

        Zyklus (40 Steps à 80ms = 3.2s):
            0-14:  helles Gold   (sichtbar, bright)
            15-24: normales Gold (sichtbar, normal)
            25-39: unsichtbar    (komplett ausgeblendet)

        Das ergibt ein Blink/Pulse-Effekt der die Aufmerksamkeit auf den Text lenkt.
        """
        try:
            cycle = step % 40
            if cycle < 15:
                # Phase 1: helles Gold (maximale Sichtbarkeit)
                self.canvas.itemconfig(self.enter_text,
                                       text="ENTER = Start    ·    S = Settings",
                                       fill="#F0D76F")
                self.canvas.itemconfig(self.enter_underline, fill="#F0D76F")
            elif cycle < 25:
                # Phase 2: normales Gold (leichte Abdunklung)
                self.canvas.itemconfig(self.enter_text,
                                       text="ENTER = Start    ·    S = Settings",
                                       fill=JEOPARDY_GOLD)
                self.canvas.itemconfig(self.enter_underline, fill=JEOPARDY_GOLD)
            else:
                # Phase 3: unsichtbar
                self.canvas.itemconfig(self.enter_text, text="")
                self.canvas.itemconfig(self.enter_underline, fill="")

            self.root.after(80, lambda: self.pulse_enter(step + 1))
        except tk.TclError:
            pass


def run():
    """Entry-Point für das Startscreen-Modul. Wird von main.py aufgerufen."""
    # Modul-Flags zurücksetzen, falls run() mehrfach aufgerufen wird
    global show_settings, quit_app
    show_settings = False
    quit_app = False

    root = tk.Tk()
    r.detect_font()  # Font-Fallback erst hier aufrufen (braucht aktiven Tcl-Interpreter)
    root.title("Jeopardy!")
    StartScreen(root)
    root.mainloop()


if __name__ == "__main__":
    run()
