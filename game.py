"""
Jeopardy Game Board — das Kern-Spielbrett mit Kategorien und Wert-Buttons.

Struktur:
    - Kategorie-Header oben (eine Zeile)
    - Darunter ein Raster aus LButton-Instanzen (eine pro Frage)
    - Team-Score-Bar ganz unten

Haupt-Interaktion:
    1. User klickt einen Wert-Button → `button_click()`
    2. Button "flippt" auf Vollbild und zeigt die Frage (`flip()`)
    3. Moderator drückt Team-Nummer (1-N) oder Niemand-Taste (N+1)
    4. Button schrumpft weg, Punkte werden zugewiesen (`keyboard_input()` + `set_org()`)
    5. Bei 0 verbleibenden Fragen → Fenster schließt automatisch

Bug-Fixes:
    - `_answered` Flag verhindert Mehrfach-Registrierung bei schnellem Tastendruck
    - `_flip_in_progress` Flag verhindert Klicks während eine Frage offen ist
"""

import tkinter as tk
import tkinter.font
import resources as r
import audio_player as audio
import math

# Timer-Audio: wird beim Aufruf einer Frage gestartet und bei Antwort/Leertaste gestoppt
TIMER_AUDIO = "30 Seconds To Answer Jeopardy Timer #challenge #timer #jeopardy.mp3"

# Lokale Aliase — werden in run() aus r.* neu gebunden, damit Theme-Wechsel greift
BLUE = r.BLUE
GOLD = r.GOLD
DARK_BLUE = r.DARK_BLUE
HOVER_BG = r.CARD_BG      # Hintergrund beim Hovern (themed)
ANSWERED_BG = r.SHADOW    # Hintergrund beantworteter Buttons (themed, dunkel)
ANSWERED_FG = "#404040"   # Border-Farbe beantworteter Buttons (theme-neutrales Grau)


def _darken_hex(h, factor=0.5):
    """Macht einen Hex-Farbwert dunkler (Multiplikation pro Kanal)."""
    h = h.lstrip('#')
    return "#{:02X}{:02X}{:02X}".format(
        int(int(h[0:2], 16) * factor),
        int(int(h[2:4], 16) * factor),
        int(int(h[4:6], 16) * factor),
    )


def _rebind_colors():
    """Aktualisiert alle Farb-Aliase aus r.* (nach Theme-Wechsel)."""
    global BLUE, GOLD, DARK_BLUE, HOVER_BG, ANSWERED_BG
    BLUE = r.BLUE
    GOLD = r.GOLD
    DARK_BLUE = r.DARK_BLUE
    HOVER_BG = r.CARD_BG
    # ANSWERED_BG: deutlich dunkler als DARK_BLUE — "vergessen"-Look
    ANSWERED_BG = _darken_hex(r.DARK_BLUE, 0.5)

# Modul-Level State
grid = []                   # 2D-Liste aller Buttons: grid[kategorie][zeile]
_flip_in_progress = False   # Global: verhindert Klick auf weiteren Button während Flip aktiv


class LButton(tk.Label):
    """Ein einzelner Wert-Button auf dem Jeopardy-Board.

    Erbt von tk.Label (nicht tk.Button) um Flip-Animationen frei zu positionieren.
    Verhält sich aber wie ein Button via <Button-1> Binding.
    """

    def __init__(self, master, p_width, p_height, **kwargs):
        self._text = ""           # Der umgebrochene Fragentext (set_text befüllt ihn)
        self.wertigkeit = 0       # Punktwert dieses Buttons (100, 200, ...)
        self.gedreht = False      # Wurde der Button bereits aktiviert?
        self._answered = False    # Wurde die Frage bereits beantwortet? (Race-Condition Fix)
        super().__init__(master, **kwargs)
        self.place(width=p_width, height=p_height)

        # Hover-Effekt: beim Überfahren heller Hintergrund + leuchtender Gold-Border
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._default_bg = kwargs.get("background", DARK_BLUE)

    def _on_enter(self, event):
        """Maus betritt den Button → Hover-Style anwenden (nur wenn nicht gedreht)."""
        if not self.gedreht:
            self.config(background=HOVER_BG,
                        highlightbackground=r.HOVER_GOLD, highlightthickness=3)

    def _on_leave(self, event):
        """Maus verlässt den Button → Normal-Style wiederherstellen."""
        if not self.gedreht:
            self.config(background=self._default_bg,
                        highlightbackground=GOLD, highlightthickness=2)

    def set_org(self, org, richtung, schnelligkeit):
        """Shrink-Animation: Lässt den aufgeklappten Button wieder verschwinden.

        Wird nach der Beantwortung einer Frage aufgerufen. Der Button schrumpft
        von Vollbild horizontal zur ursprünglichen Position und bleibt dort
        unsichtbar (width=0) liegen.

        Ablauf:
            richtung=True: Breite schrittweise reduzieren
            richtung=False: Platzieren auf Original-Position mit width=0 (endgültig)
                → Wenn alle Fragen beantwortet: Fenster nach 1s zerstören
        """
        tmp_x = self.winfo_x()
        if richtung:
            if self.winfo_width() > 3:
                # Weiter schrumpfen (Breite -, x-Position + um zentriert zu bleiben)
                self.place(width=self.winfo_width() - (schnelligkeit * 20),
                           x=tmp_x + schnelligkeit * 10)
                self.master.after(10, lambda: self.set_org(org, True, schnelligkeit))
            else:
                # Vollständig geschrumpft → unsichtbar auf Original-Position parken
                self.lower()
                self.place(x=org[2], y=org[3], width=0, height=org[1])
                self.master.after(10, lambda: self.set_org(org, False, schnelligkeit))
        else:
            # Keine weitere Animation — aber prüfen ob das Spiel vorbei ist
            if r.to_be_switched_int == 0:
                self.master.after(1000, self.master.destroy)

    def keyboard_input(self, event, org, schnelligkeit):
        """Verarbeitet den Tastendruck nach dem Aufklappen einer Frage.

        Tasten:
            LEERTASTE:                Timer-Audio stoppen (Frage bleibt offen)
            '1' bis str(num_teams):   Punkte an entsprechendes Team + Audio stoppen
            str(num_teams + 1):       "Niemand" — keine Punkte + Audio stoppen

        Bug-Fix: `_answered` Flag wird SOFORT gesetzt und unbind SOFORT
        ausgeführt. Früher passierte unbind via `after(10, ...)`, sodass
        in diesen 10ms weitere Key-Events durchkommen konnten.
        """
        global _flip_in_progress
        if self._answered:
            return  # Bereits verarbeitet — Mehrfach-Key-Events ignorieren

        # Leertaste: Nur den Timer stoppen — Frage bleibt offen, wartet auf Antwort
        if event.keysym == "space":
            audio.stop_music()
            return

        num_teams = len(r.teams)

        # Team-Tasten: 1 bis num_teams
        for i in range(num_teams):
            if event.char == str(i + 1):
                self._answered = True
                audio.stop_music()  # Timer stoppen — Antwort gegeben
                self.master.unbind("<KeyPress>")
                # Button in der Team-Farbe einfärben (visuelles Feedback für den Moderator)
                self.config(foreground=r.teams[i]["color"])
                self.update()
                r.team_points[i] += self.wertigkeit
                self.set_org(org, True, schnelligkeit)
                _flip_in_progress = False
                _update_team_scores()  # Team-Score-Bar unten aktualisieren
                return

        # Niemand-Taste: num_teams + 1 (z.B. '4' bei 3 Teams)
        if event.char == str(num_teams + 1):
            self._answered = True
            audio.stop_music()  # Timer stoppen — Antwort (Niemand)
            self.master.unbind("<KeyPress>")
            self.config(foreground="black")
            self.update()
            self.set_org(org, True, schnelligkeit)
            _flip_in_progress = False

    def set_text(self, text):
        """Bricht den Fragentext auf Bildschirmbreite um und speichert ihn in `_text`.

        Das '!' Zeichen wirkt als Trennzeichen zwischen deutscher und englischer
        Version (→ doppelter Zeilenumbruch). Wörter werden sonst nach der
        tatsächlichen Pixel-Breite umbrochen.
        """
        font = tk.font.Font(font=self.cget("font"))

        def split_string(s):
            return s.split()

        def join_string(str1, str2):
            return str1 + " " + str2

        def get_text_width(text):
            return self.master.winfo_fpixels(f"{font.measure(text)}p")

        split_list = split_string(text)
        erg_string = ""
        tmp_ergebnis = ""
        for i in split_list:
            if i == "!":
                # Spezial-Separator: doppelter Umbruch (DE/EN-Trennung)
                erg_string += tmp_ergebnis + "\n" + "\n"
                tmp_ergebnis = ""
            else:
                tmp = join_string(tmp_ergebnis, i)
                # Wenn Zeile zu breit wird → umbrechen
                if get_text_width(tmp) + 100 > self.master.winfo_screenwidth():
                    erg_string += tmp_ergebnis + "\n"
                    tmp_ergebnis = i
                else:
                    tmp_ergebnis = tmp

        erg_string += tmp_ergebnis
        self._text = erg_string

    def get_text(self):
        return self._text

    def visible_text(self):
        """Setzt den umgebrochenen Fragentext als Label-Text (für Display)."""
        self.config(text=self._text)

    def flip(self, org, richtung, schnelligkeit):
        """Flip-Animation: Zentriert den Button und vergrößert ihn auf Vollbild.

        Zweiphasig:
            richtung=True:  Button auf width=0 schrumpfen (an aktueller Stelle)
                            dann in die Mitte springen
            richtung=False: Von der Mitte auf Vollbild expandieren

        Bug-Fix: `_answered` Check stoppt die Expand-Animation wenn der User
        bereits eine Taste gedrückt hat (sonst liefen Expand und Shrink parallel).
        """
        if self._answered:
            return  # Frühzeitiger Abbruch wenn schon beantwortet
        tmp_x = self.winfo_x()
        if richtung:
            # Phase 1: schrumpfen an aktueller Position
            if self.winfo_width() > 3:
                self.place(width=self.winfo_width() - (schnelligkeit * 2),
                           x=tmp_x + schnelligkeit)
                self.master.after(10, lambda: self.flip(org, True, schnelligkeit))
            else:
                # Vollständig geschrumpft → Text anzeigen und in die Mitte springen
                # Background explizit auf Theme-Farbe setzen, damit Hover-Reste
                # (HOVER_BG) nicht in die Fragenansicht überleben.
                self.config(background=DARK_BLUE)
                self.visible_text()
                self.lift()  # In den Vordergrund bringen
                self.place(
                    x=self.master.winfo_screenwidth() / 2,
                    y=self.master.winfo_screenheight() / 2,
                    width=0, height=0
                )
                self.master.after(10, lambda: self.flip(org, False, schnelligkeit))
        else:
            # Phase 2: von der Mitte auf Vollbild expandieren
            if self._answered:
                return
            if self.winfo_width() < self.master.winfo_screenwidth():
                self.place(width=self.winfo_width() + (schnelligkeit * 20),
                           x=tmp_x - schnelligkeit * 10)
                if self.winfo_height() < self.master.winfo_screenheight():
                    self.place(height=self.winfo_height() + (schnelligkeit * 20),
                               y=self.winfo_y() - schnelligkeit * 10)
                self.master.after(10, lambda: self.flip(org, False, schnelligkeit))
            else:
                # Fullscreen erreicht — jetzt erst das 30-Sekunden-Timer-Audio starten.
                # (No-Op wenn pygame nicht verfügbar ist.)
                audio.play_music(TIMER_AUDIO, loop=False)

    def start_flip(self):
        """Startet die Flip-Animation beim Klick auf den Button.

        Setzt das globale `_flip_in_progress` Flag (damit andere Buttons nicht
        klickbar sind) und bindet die Tastenerkennung an das Root-Fenster.
        Das Timer-Audio startet erst, wenn die Frage Fullscreen erreicht hat
        (siehe flip() Phase 2).
        """
        global _flip_in_progress
        if not self.gedreht:
            _flip_in_progress = True
            # Original-Geometrie merken (Width, Height, X, Y) — wird nach Antwort wiederhergestellt
            org = [self.winfo_width(), self.winfo_height(),
                   self.winfo_x(), self.winfo_y()]
            schnelligkeit = int(math.ceil(self.winfo_width() / 100))
            self.flip(org, True, schnelligkeit)
            self.gedreht = True
            # Globales KeyPress-Binding — wird in keyboard_input() wieder entfernt
            self.master.bind("<KeyPress>",
                             lambda event: self.keyboard_input(event, org, schnelligkeit))


# ---------------------------------------------------------------------------
# Team-Score-Anzeige am unteren Bildschirmrand
# ---------------------------------------------------------------------------

_team_score_labels = []  # Referenzen auf die Points-Labels für Live-Update


def _update_team_scores():
    """Aktualisiert die Punkteanzeige der Team-Bar (wird nach jeder Antwort aufgerufen)."""
    for i, lbl in enumerate(_team_score_labels):
        lbl.config(text=str(r.team_points[i]))


def _create_team_bar(root, sw, sh):
    """Erstellt die Team-Score-Bar am unteren Bildschirmrand.

    Zeigt für jedes Team: Name (in Teamfarbe) + Punkte (in Weiß)
    Über der Bar eine goldene Trennlinie zum Haupt-Board.
    """
    _team_score_labels.clear()

    bar_y = sh - 100
    num_teams = len(r.teams)

    # Goldene Trennlinie über der Team-Bar
    sep = tk.Canvas(root, bg=BLUE, highlightthickness=0, height=3)
    sep.place(x=40, y=bar_y - 10, width=sw - 80, height=3)
    sep.create_line(0, 1, sw - 80, 1, fill=GOLD, width=2)

    # Team-Einträge gleichmäßig verteilen
    section_w = sw // num_teams
    for i, team in enumerate(r.teams):
        cx = section_w * i + section_w // 2  # Zentrum des Abschnitts

        # Team-Name in der Teamfarbe
        tk.Label(
            root, text=team["name"],
            font=(r.FONT, 16, "bold"),
            fg=team["color"], bg=BLUE
        ).place(x=cx, y=bar_y + 2, anchor="n")

        # Punktestand in Weiß (wird live aktualisiert)
        pts_lbl = tk.Label(
            root, text=str(r.team_points[i]),
            font=(r.FONT, 20, "bold"),
            fg="white", bg=BLUE
        )
        pts_lbl.place(x=cx, y=bar_y + 28, anchor="n")
        _team_score_labels.append(pts_lbl)


def create_grid(root):
    """Erstellt das komplette Jeopardy-Spielbrett.

    Layout:
        - Kategorie-Header in Zeile 0 (eine pro Kategorie)
        - Frage-Buttons in Zeilen 1 bis len(values)
        - Team-Score-Bar ganz unten

    Die Zeilenhöhe wird dynamisch aus der verbleibenden Bildschirmhöhe berechnet,
    sodass das Board sich an unterschiedliche Bildschirmgrößen anpasst.
    """
    grid.clear()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    col_width = sw // len(r.categories)
    gap = 8  # Abstand zwischen Zellen (Classic Jeopardy Look)

    # Platz am unteren Rand für die Team-Bar reservieren
    board_height = sh - 140

    num_rows = len(r.values) + 1  # +1 für die Kategorien-Header-Zeile
    header_h = 140
    row_h = (board_height - header_h - gap * (num_rows + 1)) // len(r.values)

    for i in range(len(r.categories)):
        grid.append([])
        for j in range(len(r.values) + 1):
            if j == 0:
                # --- Kategorie-Header (dunkelblauer BG, goldener Border) ---
                # Schatten-Layer für 3D-Tiefeneffekt
                shadow = tk.Label(
                    root, text="",
                    background=r.SHADOW
                )
                shadow.place(
                    y=gap + 3,
                    x=col_width * i + gap + 3,
                    width=col_width - gap * 2,
                    height=header_h
                )
                # Haupt-Header
                tmp = tk.Label(
                    root, text=r.categories[i],
                    font=(r.FONT, 28, "bold"),
                    background=DARK_BLUE, foreground=GOLD,
                    highlightbackground=GOLD, highlightthickness=2,
                    relief="flat", borderwidth=0
                )
                tmp.place(
                    y=gap,
                    x=col_width * i + gap,
                    width=col_width - gap * 2,
                    height=header_h
                )
                grid[i].append(tmp)
            else:
                # --- Wert-Button (LButton Instanz) ---
                cell_y = (header_h + gap + (row_h + gap) * (j - 1)) + 15
                tmp_b = LButton(
                    root,
                    font=(r.FONT, 48, "bold"),
                    background=DARK_BLUE, foreground=GOLD,
                    p_width=col_width - gap * 2, p_height=row_h,
                    cursor="hand2",
                    highlightbackground=GOLD, highlightthickness=2,
                    relief="flat", borderwidth=0
                )
                tmp_b.place(y=cell_y, x=col_width * i + gap)
                tmp_b.bind("<Button-1>", button_click)
                # Fragentext für später umbrechen (wird erst bei flip() angezeigt)
                tmp_b.set_text(r.questions[i][j - 1])
                # Vor dem Flip zeigt der Button nur den Punktwert
                tmp_b.config(text=f"{r.values[j - 1]}")
                tmp_b.wertigkeit = r.values[j - 1]
                grid[i].append(tmp_b)

    _create_team_bar(root, sw, sh)


def button_click(event):
    """Handler für Klick auf einen Wert-Button. Startet die Flip-Animation.

    Bug-Fix: Wenn bereits ein anderer Button im Flip ist (`_flip_in_progress`),
    wird der Klick ignoriert — sonst könnten zwei Fragen gleichzeitig offen sein.
    """
    if _flip_in_progress:
        return
    r.to_be_switched_int -= 1  # Verbleibende Fragen -1
    event.widget.unbind("<Button-1>")  # Kein weiterer Klick auf diesen Button
    event.widget.config(cursor="")
    # Visuell als "beantwortet" markieren (grauer Border)
    event.widget._default_bg = ANSWERED_BG
    event.widget.config(highlightbackground=ANSWERED_FG, highlightthickness=2)
    event.widget.start_flip()


def run():
    """Entry-Point für das Game-Modul. Wird von main.py aufgerufen."""
    # Modul-State zurücksetzen, damit aufeinanderfolgende Spiele keine
    # alten Referenzen oder Flags wiederverwenden
    global _flip_in_progress
    _flip_in_progress = False
    grid.clear()
    _team_score_labels.clear()
    _rebind_colors()

    root = tk.Tk()
    root.title("Jeopardy!")
    root.attributes("-fullscreen", True)
    root.configure(bg=BLUE)
    create_grid(root)
    root.mainloop()
    # Safety: Timer stoppen falls das Fenster geschlossen wird während eine Frage offen ist
    audio.stop_music()


if __name__ == "__main__":
    run()
