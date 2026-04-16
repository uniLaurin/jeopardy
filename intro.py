"""
Cinematic Intro-Sequenz zwischen Settings und Gameboard.

Timeline (~18s aktive Animation, danach Hold-State bis Enter):
    0.0-2.0s  Fenster fadet ein, Sterne-Feld auf BLUE-Hintergrund
    2.0-4.5s  "JEOPARDY" — Buchstaben fallen einzeln mit Bounce
    4.5-5.5s  Gold-Linie wächst von Mitte nach außen unter dem Titel
    5.5-8.0s  Tagline "DAS QUIZ-SPIEL FÜR TEAMS" fadet ein
    8.0-10.0s Titel + Linie schrumpfen nach oben, Tagline fadet raus
    10.0-12s  Team-Karten erscheinen nacheinander
    13.0-15s  Stats-Strip (Kategorien / Fragen / Max-Punkte)
    16.0s+    "DRÜCKE ENTER ZUM START" pulsiert — wartet auf Enter

Audio läuft parallel: `audio/Jeopardy intro with host introduction.mp3` (~30s).
Die Musik überdauert die Animation, User drückt Enter wenn er bereit ist.

Enter / Escape kann jederzeit gedrückt werden → überspringt zum Gameboard.
"""

import math
import random
import tkinter as tk

import audio_player as audio
import resources as r


TITLE_TEXT = "JEOPARDY"
INTRO_AUDIO_FILE = "Jeopardy intro with host introduction.mp3"


# Lokale Farb-Aliase — werden in run() aus r.* neu gebunden (Theme-Support)
BLUE = r.BLUE
GOLD = r.GOLD
DARK_BLUE = r.DARK_BLUE
SHADOW = r.SHADOW


def _rebind_colors():
    global BLUE, GOLD, DARK_BLUE, SHADOW
    BLUE = r.BLUE
    GOLD = r.GOLD
    DARK_BLUE = r.DARK_BLUE
    SHADOW = r.SHADOW


# ---------------------------------------------------------------------------
# Farb-Utilities für Fade- und Pulse-Effekte
# ---------------------------------------------------------------------------

def _hex_to_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r_, g_, b_):
    return "#{:02X}{:02X}{:02X}".format(int(r_), int(g_), int(b_))


def _blend(c1, c2, t):
    """Interpoliere zwischen c1 (t=0) und c2 (t=1). Beide als Hex-String."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex(
        r1 + (r2 - r1) * t,
        g1 + (g2 - g1) * t,
        b1 + (b2 - b1) * t,
    )


# ---------------------------------------------------------------------------
# Modul-State
# ---------------------------------------------------------------------------

# True wenn User Escape gedrückt hat (derzeit genauso wie Enter — überspringt)
skipped = False


class IntroScreen:
    """Kapselt das komplette Intro — eine Instanz pro run()-Aufruf."""

    def __init__(self, root):
        self.root = root
        self.w = root.winfo_screenwidth()
        self.h = root.winfo_screenheight()
        self.cx = self.w // 2
        self.cy = self.h // 2

        self.root.configure(bg=BLUE)
        self.root.attributes("-fullscreen", True)

        # Sanfter Fenster-Fadein via -alpha (falls vom Fenstermanager unterstützt)
        self._alpha_supported = True
        try:
            self.root.attributes("-alpha", 0.0)
        except tk.TclError:
            self._alpha_supported = False

        self.canvas = tk.Canvas(
            root, bg=BLUE, highlightthickness=0,
            width=self.w, height=self.h
        )
        self.canvas.pack(fill="both", expand=True)

        # State für die einzelnen Phasen
        self.stars = []              # [{"id": canvas_id, "phase": float}]
        self.letter_items = []       # [{"id", "x_center", "y_center", "font_size"}]
        self.line_item = None        # Canvas-ID der Gold-Linie unter dem Titel
        self.tagline_item = None     # Canvas-ID der Tagline
        self.team_items = []         # Alle Canvas-IDs der Team-Karten
        self.stat_number_items = []  # Canvas-IDs der großen Zahlen (fade-in)
        self.stat_label_items = []   # Canvas-IDs der kleinen Labels
        self.prompt_rect = None
        self.prompt_text = None

        self._scheduled = []         # Ausstehende after()-Handles für Cleanup
        self._closed = False

        # Enter / Escape beenden das Intro jederzeit
        self.root.bind("<Return>", self._on_close_key)
        self.root.bind("<KP_Enter>", self._on_close_key)
        self.root.bind("<Escape>", self._on_escape)

        # Hintergrund + Sterne sofort zeichnen
        self._draw_vignette()
        self._draw_stars()

        # Musik starten
        audio.play_music(INTRO_AUDIO_FILE, loop=False)

        # Fenster einblenden (2s)
        if self._alpha_supported:
            self._fade_window_in(0, 20)

        # Phasen-Timeline planen
        self._after(0,     self._start_twinkle)
        self._after(2000,  self._phase_letter_drop)
        self._after(4500,  self._phase_underline)
        self._after(5500,  self._phase_tagline)
        self._after(8000,  self._phase_shrink)
        self._after(10000, self._phase_teams)
        self._after(13000, self._phase_stats)
        self._after(16000, self._phase_prompt)

    # ---------------------------------------------------------------- util
    def _after(self, ms, cb):
        """Wrapper um root.after() der das Handle zum Cancelen speichert."""
        try:
            h = self.root.after(ms, cb)
            self._scheduled.append(h)
            return h
        except tk.TclError:
            return None

    def _cancel_all(self):
        for h in self._scheduled:
            try:
                self.root.after_cancel(h)
            except tk.TclError:
                pass
        self._scheduled.clear()

    def _on_close_key(self, _e=None):
        self._close()

    def _on_escape(self, _e=None):
        global skipped
        skipped = True
        self._close()

    def _close(self):
        if self._closed:
            return
        self._closed = True
        self._cancel_all()
        audio.stop_music()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    # ----------------------------------------------------- Phase 0: Setup
    def _draw_vignette(self):
        """Dunkle Ränder — dieselbe Technik wie startscreen.py, reduziert."""
        strip_h = 30
        for i, stipple in enumerate(["gray50", "gray25", "gray12"]):
            self.canvas.create_rectangle(
                0, i * strip_h, self.w, (i + 1) * strip_h,
                fill=SHADOW, outline="", stipple=stipple
            )
            y_start = self.h - (i + 1) * strip_h
            self.canvas.create_rectangle(
                0, y_start, self.w, y_start + strip_h,
                fill=SHADOW, outline="", stipple=stipple
            )
        strip_w = 40
        for i, stipple in enumerate(["gray50", "gray25", "gray12"]):
            self.canvas.create_rectangle(
                i * strip_w, 0, (i + 1) * strip_w, self.h,
                fill=SHADOW, outline="", stipple=stipple
            )
            x_start = self.w - (i + 1) * strip_w
            self.canvas.create_rectangle(
                x_start, 0, x_start + strip_w, self.h,
                fill=SHADOW, outline="", stipple=stipple
            )

    def _draw_stars(self):
        rnd = random.Random(42)  # Deterministisch → immer gleiche Sternverteilung
        for _ in range(60):
            x = rnd.randint(0, self.w)
            y = rnd.randint(0, self.h)
            size = rnd.choice([1, 1, 1, 2, 2, 3])
            s_id = self.canvas.create_oval(
                x, y, x + size, y + size,
                fill=BLUE, outline=""   # Start unsichtbar (BLUE auf BLUE)
            )
            self.stars.append({"id": s_id, "phase": rnd.uniform(0, 1)})

    def _fade_window_in(self, step, total):
        try:
            alpha = min(1.0, step / total)
            self.root.attributes("-alpha", alpha)
            if step < total:
                self._after(100, lambda: self._fade_window_in(step + 1, total))
        except tk.TclError:
            pass

    def _start_twinkle(self):
        self._twinkle(0)

    def _twinkle(self, step):
        """Sterne pulsieren langsam zwischen BLUE (unsichtbar) und GOLD."""
        if self._closed:
            return
        try:
            for s in self.stars:
                phase = (step * 0.012 + s["phase"]) % 1.0
                brightness = 0.15 + 0.85 * abs(math.sin(phase * math.pi))
                color = _blend(BLUE, GOLD, brightness)
                self.canvas.itemconfig(s["id"], fill=color)
            self._after(100, lambda: self._twinkle(step + 1))
        except tk.TclError:
            pass

    # -------------------------------------------- Phase 2: Letter-Drop
    def _phase_letter_drop(self):
        """Buchstaben fallen einzeln von oben mit Bounce-Effekt."""
        font_size = max(72, int(self.h * 0.14))
        letter_w = int(font_size * 0.72)
        gap = int(font_size * 0.05)
        total_w = len(TITLE_TEXT) * letter_w + (len(TITLE_TEXT) - 1) * gap
        start_x = self.cx - total_w // 2 + letter_w // 2

        for i, ch in enumerate(TITLE_TEXT):
            x = start_x + i * (letter_w + gap)
            item = self.canvas.create_text(
                x, -120,
                text=ch, font=(r.FONT, font_size, "bold"),
                fill=GOLD, anchor="center"
            )
            self.letter_items.append({
                "id": item,
                "x_center": x,
                "y_center": self.cy,
                "font_size": font_size,
            })
            # Buchstaben zeitversetzt starten (0.3s Abstand)
            self._after(i * 300, lambda idx=i: self._drop_letter(idx, 0, 20))

    def _drop_letter(self, idx, step, total):
        if self._closed:
            return
        try:
            info = self.letter_items[idx]
            t = step / total
            if t >= 1.0:
                self.canvas.coords(info["id"], info["x_center"], info["y_center"])
                return
            # Einflugkurve: zuerst schnell runter, dann kleiner Overshoot
            if t < 0.6:
                progress = t / 0.6
                y = -120 + (info["y_center"] + 40 - (-120)) * _ease_out(progress)
            else:
                progress = (t - 0.6) / 0.4
                y = info["y_center"] + 40 - 40 * _ease_out(progress)
            self.canvas.coords(info["id"], info["x_center"], y)
            self._after(20, lambda: self._drop_letter(idx, step + 1, total))
        except tk.TclError:
            pass

    # -------------------------------------------- Phase 3: Underline
    def _phase_underline(self):
        y = self.cy + int(self.h * 0.11)
        self.line_item = self.canvas.create_line(
            self.cx, y, self.cx, y,
            fill=GOLD, width=4
        )
        self._grow_line(0, 400, y)

    def _grow_line(self, progress, max_w, y):
        if self._closed or self.line_item is None:
            return
        try:
            if progress <= max_w:
                self.canvas.coords(
                    self.line_item,
                    self.cx - progress, y, self.cx + progress, y
                )
                self._after(4, lambda: self._grow_line(progress + 5, max_w, y))
        except tk.TclError:
            pass

    # -------------------------------------------- Phase 4: Tagline
    def _phase_tagline(self):
        y = self.cy + int(self.h * 0.24)
        font_size = max(18, int(self.h * 0.026))
        self.tagline_item = self.canvas.create_text(
            self.cx, y,
            text="DAS QUIZ-SPIEL FÜR TEAMS",
            font=(r.FONT, font_size),
            fill=BLUE,  # unsichtbar — wird gleich in Weiß gefadet
            anchor="center"
        )
        self._fade_item_fill(self.tagline_item, BLUE, "#FFFFFF", 0, 20)

    def _fade_item_fill(self, item, from_c, to_c, step, total):
        if self._closed:
            return
        try:
            t = min(1.0, step / total)
            self.canvas.itemconfig(item, fill=_blend(from_c, to_c, t))
            if step < total:
                self._after(25, lambda: self._fade_item_fill(
                    item, from_c, to_c, step + 1, total))
        except tk.TclError:
            pass

    # -------------------------------------------- Phase 5: Shrink to top
    def _phase_shrink(self):
        """Titel rutscht + schrumpft nach oben, Linie folgt, Tagline fadet weg."""
        target_y = int(self.h * 0.14)
        target_line_y = int(self.h * 0.20)
        target_font = max(36, int(self.h * 0.07))
        start_line_y = self.cy + int(self.h * 0.11)

        self._shrink_step(0, 25, target_y, target_font,
                          start_line_y, target_line_y, 400, 250)

        if self.tagline_item is not None:
            self._fade_item_fill(self.tagline_item, "#FFFFFF", BLUE, 0, 18)

    def _shrink_step(self, step, total, target_y, target_font,
                     start_line_y, target_line_y, start_line_w, target_line_w):
        if self._closed:
            return
        try:
            t = step / total
            t = _ease_out(min(1.0, t))

            for info in self.letter_items:
                orig_font = info["font_size"]
                new_font = int(orig_font + (target_font - orig_font) * t)
                new_y = int(info["y_center"] + (target_y - info["y_center"]) * t)
                # x-Position zieht gleichmäßig in Richtung Mitte zusammen
                ratio = new_font / orig_font
                dx = (info["x_center"] - self.cx) * ratio
                new_x = int(self.cx + dx)
                self.canvas.itemconfig(
                    info["id"], font=(r.FONT, max(10, new_font), "bold"))
                self.canvas.coords(info["id"], new_x, new_y)

            if self.line_item is not None:
                new_y = int(start_line_y + (target_line_y - start_line_y) * t)
                new_w = int(start_line_w + (target_line_w - start_line_w) * t)
                self.canvas.coords(
                    self.line_item,
                    self.cx - new_w, new_y, self.cx + new_w, new_y
                )

            if step < total:
                self._after(40, lambda: self._shrink_step(
                    step + 1, total, target_y, target_font,
                    start_line_y, target_line_y, start_line_w, target_line_w))
        except tk.TclError:
            pass

    # -------------------------------------------- Phase 6: Team-Karten
    def _phase_teams(self):
        teams = list(r.teams)
        if not teams:
            return
        # Karten-Breite dynamisch — bei vielen Teams nicht übers Fenster rauswachsen
        gap = max(16, int(self.w * 0.012))
        max_total = int(self.w * 0.85)
        card_w = min(
            200,
            int(self.w * 0.13),
            (max_total - (len(teams) - 1) * gap) // len(teams)
        )
        card_w = max(100, card_w)  # Mindestbreite, damit Name lesbar bleibt
        card_h = int(self.h * 0.19)
        total_w = len(teams) * card_w + (len(teams) - 1) * gap
        start_x = self.cx - total_w // 2
        y = int(self.h * 0.38)

        for i, team in enumerate(teams):
            x = start_x + i * (card_w + gap)
            self._after(i * 350, lambda x=x, y=y, w=card_w, h=card_h, t=team:
                        self._build_team_card(x, y, w, h, t))

    def _build_team_card(self, x, y, w, h, team):
        if self._closed:
            return
        try:
            name = team.get("name", "Team")
            color = team.get("color", GOLD)

            # Karte: Rahmen + inner Fill + Team-Label + Name + Farb-Streifen
            rect = self.canvas.create_rectangle(
                x, y, x + w, y + h,
                fill=DARK_BLUE, outline=GOLD, width=2
            )
            label_font = max(10, int(h * 0.12))
            name_font = max(16, int(h * 0.20))

            label = self.canvas.create_text(
                x + w // 2, y + int(h * 0.18),
                text="TEAM",
                font=(r.FONT, label_font, "bold"),
                fill=GOLD, anchor="center"
            )
            name_item = self.canvas.create_text(
                x + w // 2, y + h // 2 + int(h * 0.02),
                text=name,
                font=(r.FONT, name_font, "bold"),
                fill="#FFFFFF", anchor="center"
            )
            stripe = self.canvas.create_rectangle(
                x + 14, y + h - 16, x + w - 14, y + h - 10,
                fill=color, outline=""
            )
            self.team_items.extend([rect, label, name_item, stripe])
        except tk.TclError:
            pass

    # -------------------------------------------- Phase 7: Stats
    def _phase_stats(self):
        num_cats = len(r.categories)
        num_qs = num_cats * len(r.values)
        max_pts = sum(r.values) * num_cats

        stats = [
            (str(num_cats), "KATEGORIEN"),
            (str(num_qs),   "FRAGEN"),
            (str(max_pts),  "MAX. PUNKTE"),
        ]

        group_w = int(self.w * 0.55)
        step_w = group_w // len(stats)
        start_x = self.cx - group_w // 2 + step_w // 2
        y = int(self.h * 0.65)

        num_font = max(36, int(self.h * 0.075))
        lbl_font = max(11, int(self.h * 0.018))

        for i, (num, lbl) in enumerate(stats):
            x = start_x + i * step_w
            num_item = self.canvas.create_text(
                x, y, text=num,
                font=(r.FONT, num_font, "bold"),
                fill=BLUE, anchor="center"
            )
            lbl_item = self.canvas.create_text(
                x, y + num_font // 2 + 20, text=lbl,
                font=(r.FONT, lbl_font, "bold"),
                fill=BLUE, anchor="center"
            )
            self.stat_number_items.append(num_item)
            self.stat_label_items.append(lbl_item)
            self._after(i * 350, lambda ni=num_item, li=lbl_item:
                        self._fade_stat_in(ni, li, 0, 15))

    def _fade_stat_in(self, num_item, lbl_item, step, total):
        if self._closed:
            return
        try:
            t = min(1.0, step / total)
            self.canvas.itemconfig(num_item, fill=_blend(BLUE, GOLD, t))
            self.canvas.itemconfig(lbl_item, fill=_blend(BLUE, "#FFFFFF", t))
            if step < total:
                self._after(30, lambda: self._fade_stat_in(
                    num_item, lbl_item, step + 1, total))
        except tk.TclError:
            pass

    # -------------------------------------------- Phase 8: Prompt + Pulse
    def _phase_prompt(self):
        y = int(self.h * 0.86)
        box_w = min(620, int(self.w * 0.42))
        box_h = 64
        font_size = max(16, int(self.h * 0.026))

        self.prompt_rect = self.canvas.create_rectangle(
            self.cx - box_w // 2, y - box_h // 2,
            self.cx + box_w // 2, y + box_h // 2,
            fill="", outline=GOLD, width=2
        )
        self.prompt_text = self.canvas.create_text(
            self.cx, y,
            text="DRÜCKE ENTER ZUM START",
            font=(r.FONT, font_size, "bold"),
            fill=GOLD, anchor="center"
        )
        self._pulse(0)

    def _pulse(self, step):
        if self._closed or self.prompt_text is None:
            return
        try:
            cycle = step % 30
            if cycle < 15:
                color = "#F0D76F"   # hell
            elif cycle < 24:
                color = GOLD         # normal
            else:
                color = _blend(GOLD, BLUE, 0.5)  # gedimmt
            self.canvas.itemconfig(self.prompt_rect, outline=color)
            self.canvas.itemconfig(self.prompt_text, fill=color)
            self._after(80, lambda: self._pulse(step + 1))
        except tk.TclError:
            pass


# ---------------------------------------------------------------------------
# Easing-Helper
# ---------------------------------------------------------------------------

def _ease_out(t):
    """Cubic ease-out — startet schnell, endet weich."""
    return 1 - (1 - t) ** 3


# ---------------------------------------------------------------------------
# Entry-Point
# ---------------------------------------------------------------------------

def run():
    """Läuft das Intro einmal. Blockiert bis User Enter oder Escape drückt."""
    global skipped
    skipped = False
    _rebind_colors()

    root = tk.Tk()
    r.detect_font()
    root.title("Jeopardy!")
    IntroScreen(root)
    root.mainloop()


if __name__ == "__main__":
    run()
