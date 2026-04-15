"""
Settings-Screen mit Tab-Navigation (Mockup 3: Tabbed Interface).

Drei Tabs:
    TEAMS      — Teamanzahl, Namen und Farben konfigurieren
    FRAGENSET  — Fragensets auswählen, erstellen, bearbeiten, löschen
    START      — Zusammenfassung + großer "SPIEL STARTEN" Button

Nur ein Tab ist gleichzeitig sichtbar. Umschalten per Klick auf die Tab-Buttons.
Eingaben werden beim Tab-Wechsel automatisch übernommen (Teams aus UI gelesen,
Fragen gespeichert) damit der Start-Tab immer aktuelle Infos anzeigt.
"""

import tkinter as tk
import resources as r

# Farbkonstanten aus dem zentralen Ressourcen-Modul laden
# Werden in run() per _rebind_colors() aus r.* aktualisiert (Theme-Support)
BLUE = r.BLUE
GOLD = r.GOLD
DARK_BLUE = r.DARK_BLUE
CARD_BG = r.CARD_BG
BORDER_BLUE = r.BORDER_BLUE
HOVER_GOLD = r.HOVER_GOLD
ACTIVE_GOLD = r.ACTIVE_GOLD
LABEL_GRAY = r.LABEL_GRAY

# Inaktive Tab-Farbe (wird in _rebind_colors aus dem Theme abgeleitet)
TAB_INACTIVE_BG = r.DARK_BLUE
TAB_HOVER_BG = r.CARD_BG


def _rebind_colors():
    """Aktualisiert alle lokalen Farb-Aliase aus r.* (nach Theme-Wechsel)."""
    global BLUE, GOLD, DARK_BLUE, CARD_BG, BORDER_BLUE
    global HOVER_GOLD, ACTIVE_GOLD, LABEL_GRAY, TAB_INACTIVE_BG, TAB_HOVER_BG
    BLUE = r.BLUE
    GOLD = r.GOLD
    DARK_BLUE = r.DARK_BLUE
    CARD_BG = r.CARD_BG
    BORDER_BLUE = r.BORDER_BLUE
    HOVER_GOLD = r.HOVER_GOLD
    ACTIVE_GOLD = r.ACTIVE_GOLD
    LABEL_GRAY = r.LABEL_GRAY
    TAB_INACTIVE_BG = r.DARK_BLUE
    TAB_HOVER_BG = r.CARD_BG


# ---------------------------------------------------------------------------
# Hover / Focus helpers
# ---------------------------------------------------------------------------

def _bind_focus_border(entry, normal_bg=DARK_BLUE, focus_highlight=GOLD):
    """Zeigt einen goldenen Rahmen an, wenn ein Eingabefeld den Fokus hat."""
    entry.config(highlightbackground=BORDER_BLUE, highlightcolor=focus_highlight,
                 highlightthickness=2)


def _make_secondary_btn(parent, text, command, width=80, height=35, font_size=12):
    """Erstellt einen sekundären Button (grau), der bei Hover gold wird.

    Nutzt FlatButton aus resources.py, damit das Rendering auf Mac und
    Windows identisch ist (tk.Button ignoriert auf macOS die bg-Option).
    """
    return r.FlatButton(
        parent, text=text, command=command,
        bg="#555555", fg="white",
        hover_bg=GOLD, hover_fg=BLUE,
        active_bg=ACTIVE_GOLD,
        font=(r.FONT, font_size, "bold"),
    )


# ---------------------------------------------------------------------------
# Color Picker
# ---------------------------------------------------------------------------

class ColorPicker(tk.Toplevel):
    """Kleines Popup-Fenster zur Auswahl einer Teamfarbe aus einer Farbpalette."""

    def __init__(self, parent, current_color, callback):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=CARD_BG, highlightbackground=GOLD, highlightthickness=2)
        self.callback = callback

        x = parent.winfo_rootx() + parent.winfo_width() + 5
        y = parent.winfo_rooty()
        self.geometry(f"+{x}+{y}")

        for i, color in enumerate(r.TEAM_PALETTE):
            swatch = tk.Frame(self, bg=color, width=50, height=50,
                              highlightbackground=GOLD, highlightthickness=1,
                              cursor="hand2")
            swatch.grid(row=i // 3, column=i % 3, padx=4, pady=4)
            swatch.bind("<Button-1>", lambda e, c=color: self._pick(c))
            swatch.bind("<Enter>", lambda e, s=swatch: s.config(highlightthickness=3))
            swatch.bind("<Leave>", lambda e, s=swatch: s.config(highlightthickness=1))

        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()
        self.grab_set()

    def _pick(self, color):
        self.callback(color)
        self.destroy()


# ---------------------------------------------------------------------------
# Settings Screen (Tabbed)
# ---------------------------------------------------------------------------

class SettingsScreen:
    """Tabbed Settings-Screen mit drei Tabs: TEAMS, FRAGENSET, START."""

    def __init__(self, root):
        _rebind_colors()
        self.root = root
        self.root.configure(bg=BLUE)
        self.root.attributes("-fullscreen", True)

        self.sw = root.winfo_screenwidth()
        self.sh = root.winfo_screenheight()

        # Editor-Zustand
        self.editor_data = None
        self.editor_filename = None
        self.current_cat_index = -1
        self.team_rows = []
        self.question_entries = []
        self.game_started = False
        self.theme_changed = False

        # Tab-State
        self.current_tab = "teams"
        self.tab_buttons = {}   # name → Button
        self.tab_frames = {}    # name → Frame

        # Header + Tab Navigation
        self._build_header()
        self._build_tab_navigation()

        # Content-Bereich für die Tabs
        self.content_x = 40
        self.content_y = 210
        self.content_w = self.sw - 80
        self.content_h = self.sh - self.content_y - 40

        # Tabs aufbauen
        self._build_teams_tab()
        self._build_fragenset_tab()
        self._build_design_tab()
        self._build_start_tab()

        # Initiale Daten laden
        self._refresh_set_listbox()
        self._update_key_info()

        # Startzustand: TEAMS-Tab zeigen
        self._switch_tab("teams")

        # Escape beendet die Anwendung
        self.root.bind("<Escape>", lambda e: self._quit_app())
        self.root.protocol("WM_DELETE_WINDOW", self._quit_app)

    # ------------------------------------------------------------------
    # Header + Tab Navigation
    # ------------------------------------------------------------------

    def _build_header(self):
        """Überschrift 'JEOPARDY! SETUP' mit goldener Trennlinie."""
        tk.Label(
            self.root, text="JEOPARDY! SETUP",
            font=(r.FONT, r.FONT_TITLE, "bold"), fg=GOLD, bg=BLUE
        ).place(x=self.sw // 2, y=20, anchor="n")

        canvas = tk.Canvas(self.root, bg=BLUE, highlightthickness=0, height=4)
        canvas.place(x=self.sw // 2 - 300, y=95, width=600, height=4)
        canvas.create_line(0, 2, 600, 2, fill=GOLD, width=3)

    def _build_tab_navigation(self):
        """Baut die drei Tab-Buttons unter dem Header auf."""
        nav_y = 130
        nav_h = 60
        total_w = self.sw - 80
        tab_w = total_w // 4

        # Tab-Geometrie merken, damit wir die Unterstreichung ohne winfo_x()
        # positionieren können (winfo_x liefert 0 bevor das Fenster gemapped ist).
        self._tab_geom = {}  # key → (x, y, w, h)
        self._tab_nav_y = nav_y
        self._tab_nav_h = nav_h

        tabs = [("teams", "TEAMS"), ("fragenset", "FRAGENSET"),
                ("design", "DESIGN"), ("start", "START")]
        for i, (key, label) in enumerate(tabs):
            btn = r.FlatButton(
                self.root, text=label,
                command=lambda k=key: self._switch_tab(k),
                bg=TAB_INACTIVE_BG, fg=LABEL_GRAY,
                hover_bg=TAB_HOVER_BG, hover_fg=GOLD,
                active_bg=TAB_HOVER_BG,
                font=(r.FONT, 18, "bold"),
            )
            bx = 40 + i * tab_w
            bw = tab_w - 4
            btn.place(x=bx, y=nav_y, width=bw, height=nav_h)
            self._tab_geom[key] = (bx, nav_y, bw, nav_h)
            self.tab_buttons[key] = btn

        # Goldene Unterstreichung für aktiven Tab (wird dynamisch repositioniert)
        self.tab_underline = tk.Frame(self.root, bg=GOLD)
        # Position wird in _switch_tab gesetzt

    def _switch_tab(self, tab_name):
        """Wechselt zum angegebenen Tab. Blendet alle anderen aus."""
        # Beim Verlassen von TEAMS/FRAGENSET: Zustand übernehmen
        if self.current_tab == "teams":
            self._read_teams_from_ui()
        elif self.current_tab == "fragenset":
            self._save_current_questions()

        self.current_tab = tab_name

        # Tab-Button-Farben aktualisieren. Der aktive Tab wird "gelockt",
        # damit Hover-Events ihn nicht mehr zurückfärben.
        for key, btn in self.tab_buttons.items():
            if key == tab_name:
                btn.set_state(CARD_BG, GOLD, locked=True)
            else:
                btn.set_state(TAB_INACTIVE_BG, LABEL_GRAY, locked=False)

        # Goldene Unterstreichung unter aktiven Tab schieben
        # Verwendet die gespeicherte Geometrie statt winfo_x() (das vor dem
        # ersten Mapping 0 zurückgeben würde).
        bx, by, bw, bh = self._tab_geom[tab_name]
        self.tab_underline.place(x=bx, y=by + bh - 4, width=bw, height=4)

        # Frames umschalten
        for key, frame in self.tab_frames.items():
            if key == tab_name:
                frame.place(x=self.content_x, y=self.content_y,
                            width=self.content_w, height=self.content_h)
            else:
                frame.place_forget()

        # START-Tab: Zusammenfassung aktualisieren
        if tab_name == "start":
            self._refresh_start_summary()

    # ------------------------------------------------------------------
    # TEAMS Tab
    # ------------------------------------------------------------------

    def _build_teams_tab(self):
        """Baut den TEAMS-Tab auf: Steuerzeile + Grid mit Team-Karten."""
        tab = tk.Frame(self.root, bg=CARD_BG,
                       highlightbackground=GOLD, highlightthickness=0)
        # Goldene Akzentlinie links (wie in Mockup)
        accent = tk.Frame(tab, bg=GOLD)
        accent.place(x=0, y=0, width=4, relheight=1)

        self.tab_frames["teams"] = tab

        # Titel
        tk.Label(
            tab, text="TEAMS KONFIGURIEREN",
            font=(r.FONT, r.FONT_SECTION, "bold"), fg=GOLD, bg=CARD_BG
        ).place(x=30, y=20)

        # --- Steuerzeile: Anzahl + Key-Info ---
        ctrl_y = 75

        tk.Label(
            tab, text="Anzahl:", font=(r.FONT, r.FONT_BODY),
            fg=LABEL_GRAY, bg=CARD_BG
        ).place(x=30, y=ctrl_y + 8)

        minus_btn = r.FlatButton(
            tab, text="-", command=self._remove_team,
            font=(r.FONT, 20, "bold"),
        )
        minus_btn.place(x=125, y=ctrl_y, width=40, height=40)

        self.team_count_label = tk.Label(
            tab, text=str(len(r.teams)), font=(r.FONT, 20, "bold"),
            fg=GOLD, bg=DARK_BLUE, width=3
        )
        self.team_count_label.place(x=170, y=ctrl_y, width=50, height=40)

        plus_btn = r.FlatButton(
            tab, text="+", command=self._add_team,
            font=(r.FONT, 20, "bold"),
        )
        plus_btn.place(x=225, y=ctrl_y, width=40, height=40)

        # Key-Info-Box rechts neben der Anzahl-Steuerung
        self.key_info_label = tk.Label(
            tab, text="", font=(r.FONT, r.FONT_SMALL),
            fg=LABEL_GRAY, bg=DARK_BLUE, justify="left", anchor="w",
            padx=15, pady=8
        )
        self.key_info_label.place(x=300, y=ctrl_y, width=self.content_w - 340, height=40)

        # --- Team-Karten-Grid ---
        self.team_grid = tk.Frame(tab, bg=CARD_BG)
        self.team_grid.place(x=30, y=150, width=self.content_w - 60,
                             height=self.content_h - 180)

        self._rebuild_team_rows()

    def _rebuild_team_rows(self):
        """Erstellt die Team-Karten neu (3 Karten pro Zeile)."""
        for widget in self.team_grid.winfo_children():
            widget.destroy()
        self.team_rows.clear()

        # Bewusst NICHT winfo_width() — das liefert vor dem ersten Mapping 1
        # (truthy), wodurch ein `or`-Fallback nicht greift und card_w negativ
        # wird. Die geplante Grid-Breite steht fest aus der place-Geometrie.
        grid_w = self.content_w - 60
        card_w = (grid_w - 40) // 3  # 3 Karten pro Zeile, 20px Abstand
        card_h = 150

        for i, team in enumerate(r.teams):
            col = i % 3
            row = i // 3
            cx = col * (card_w + 20)
            cy = row * (card_h + 20)

            # Team-Karte mit dunklem Hintergrund
            card = tk.Frame(
                self.team_grid, bg=DARK_BLUE,
                highlightbackground=BORDER_BLUE, highlightthickness=2
            )
            card.place(x=cx, y=cy, width=card_w, height=card_h)

            # "Team N" Label
            tk.Label(
                card, text=f"Team {i + 1}", font=(r.FONT, r.FONT_SMALL, "bold"),
                fg=LABEL_GRAY, bg=DARK_BLUE
            ).place(x=15, y=12)

            # Name-Eingabefeld
            entry = tk.Entry(
                card, font=(r.FONT, r.FONT_BODY, "bold"),
                bg=CARD_BG, fg=GOLD, insertbackground=GOLD, relief="flat"
            )
            entry.place(x=15, y=40, width=card_w - 30, height=38)
            entry.insert(0, team["name"])
            _bind_focus_border(entry)

            # Farbwahl-Label + Swatch
            tk.Label(
                card, text="Farbe:", font=(r.FONT, r.FONT_SMALL),
                fg=LABEL_GRAY, bg=DARK_BLUE
            ).place(x=15, y=95)

            color_lbl = tk.Label(
                card, bg=team["color"], relief="solid", borderwidth=2,
                cursor="hand2"
            )
            color_lbl.place(x=75, y=92, width=50, height=32)
            color_lbl.bind("<Button-1>", lambda e, idx=i: self._open_color_picker(idx))
            color_lbl.bind("<Enter>", lambda e, lbl=color_lbl: lbl.config(
                highlightbackground=GOLD, highlightthickness=3))
            color_lbl.bind("<Leave>", lambda e, lbl=color_lbl: lbl.config(
                highlightbackground="", highlightthickness=0))

            self.team_rows.append((entry, color_lbl, team["color"]))

        self.team_count_label.config(text=str(len(r.teams)))
        self._update_key_info()

    def _add_team(self):
        if len(r.teams) >= 6:
            return
        palette_idx = len(r.teams) % len(r.TEAM_PALETTE)
        r.teams.append({
            "name": f"Team {len(r.teams) + 1}",
            "color": r.TEAM_PALETTE[palette_idx]
        })
        self._rebuild_team_rows()

    def _remove_team(self):
        if len(r.teams) <= 2:
            return
        r.teams.pop()
        self._rebuild_team_rows()

    def _open_color_picker(self, team_idx):
        swatch = self.team_rows[team_idx][1]
        ColorPicker(swatch, r.teams[team_idx]["color"],
                    lambda c: self._set_team_color(team_idx, c))

    def _set_team_color(self, team_idx, color):
        r.teams[team_idx]["color"] = color
        entry, color_lbl, _ = self.team_rows[team_idx]
        color_lbl.config(bg=color)
        self.team_rows[team_idx] = (entry, color_lbl, color)

    def _update_key_info(self):
        parts = ["Tasten im Spiel:"]
        for i, team in enumerate(r.teams):
            parts.append(f"  {i + 1}={team['name']}")
        parts.append(f"  {len(r.teams) + 1}=Niemand")
        self.key_info_label.config(text="   ".join(parts))

    def _read_teams_from_ui(self):
        for i, (entry, _, color) in enumerate(self.team_rows):
            try:
                name = entry.get().strip()
            except tk.TclError:
                return
            if not name:
                name = f"Team {i + 1}"
            r.teams[i]["name"] = name
            r.teams[i]["color"] = color

    # ------------------------------------------------------------------
    # FRAGENSET Tab
    # ------------------------------------------------------------------

    def _build_fragenset_tab(self):
        """Baut den FRAGENSET-Tab auf: links Selector, rechts Editor."""
        tab = tk.Frame(self.root, bg=CARD_BG)
        accent = tk.Frame(tab, bg=GOLD)
        accent.place(x=0, y=0, width=4, relheight=1)

        self.tab_frames["fragenset"] = tab

        # Titel
        tk.Label(
            tab, text="FRAGENSET BEARBEITEN",
            font=(r.FONT, r.FONT_SECTION, "bold"), fg=GOLD, bg=CARD_BG
        ).place(x=30, y=20)

        # --- Linke Spalte: Set-Selector ---
        sel_x = 30
        sel_y = 75
        sel_w = 300

        tk.Label(
            tab, text="Fragensets:", font=(r.FONT, r.FONT_BUTTON, "bold"),
            fg=LABEL_GRAY, bg=CARD_BG
        ).place(x=sel_x, y=sel_y)

        self.set_listbox = tk.Listbox(
            tab, font=(r.FONT, r.FONT_SMALL), bg=DARK_BLUE, fg=GOLD,
            selectbackground=GOLD, selectforeground=BLUE,
            exportselection=False, relief="flat",
            highlightbackground=BORDER_BLUE, highlightthickness=2
        )
        self.set_listbox.place(x=sel_x, y=sel_y + 30, width=sel_w, height=280)
        self.set_listbox.bind("<<ListboxSelect>>", self._on_set_select)

        # Neu / Löschen Buttons unter der Listbox
        new_btn = _make_secondary_btn(tab, "Neu", self._new_set)
        new_btn.place(x=sel_x, y=sel_y + 320, width=140, height=36)

        del_btn = _make_secondary_btn(tab, "Löschen", self._delete_set)
        del_btn.place(x=sel_x + 160, y=sel_y + 320, width=140, height=36)

        # Speichern-Button (prominent, gold)
        save_btn = r.FlatButton(
            tab, text="Speichern", command=self._save_set,
            font=(r.FONT, r.FONT_BUTTON, "bold"),
        )
        save_btn.place(x=sel_x, y=sel_y + 370, width=sel_w, height=42)

        # Status-Label unter dem Save-Button
        self.status_label = tk.Label(
            tab, text="", font=(r.FONT, r.FONT_SMALL), fg=r.ERROR_RED, bg=CARD_BG
        )
        self.status_label.place(x=sel_x, y=sel_y + 420, width=sel_w)

        # --- Rechte Spalte: Editor ---
        ed_x = sel_x + sel_w + 40
        ed_y = 75
        ed_w = self.content_w - ed_x - 30

        tk.Label(
            tab, text="Name:", font=(r.FONT, r.FONT_BUTTON),
            fg=LABEL_GRAY, bg=CARD_BG
        ).place(x=ed_x, y=ed_y)

        self.set_name_entry = tk.Entry(
            tab, font=(r.FONT, r.FONT_BUTTON),
            bg=DARK_BLUE, fg=GOLD, insertbackground=GOLD, relief="flat"
        )
        self.set_name_entry.place(x=ed_x + 80, y=ed_y - 4, width=ed_w - 100, height=36)
        _bind_focus_border(self.set_name_entry)

        ed_y += 50
        tk.Label(
            tab, text="Werte:", font=(r.FONT, r.FONT_BUTTON),
            fg=LABEL_GRAY, bg=CARD_BG
        ).place(x=ed_x, y=ed_y)

        self.values_entry = tk.Entry(
            tab, font=(r.FONT, r.FONT_BUTTON),
            bg=DARK_BLUE, fg=GOLD, insertbackground=GOLD, relief="flat"
        )
        self.values_entry.place(x=ed_x + 80, y=ed_y - 4, width=ed_w - 100, height=36)
        _bind_focus_border(self.values_entry)

        # Kategorien-Bereich
        ed_y += 55
        cat_col_w = 260
        cat_x = ed_x
        q_x = ed_x + cat_col_w + 30

        tk.Label(
            tab, text="Kategorien:", font=(r.FONT, r.FONT_BUTTON, "bold"),
            fg=LABEL_GRAY, bg=CARD_BG
        ).place(x=cat_x, y=ed_y)

        tk.Label(
            tab, text="Fragen:", font=(r.FONT, r.FONT_BUTTON, "bold"),
            fg=LABEL_GRAY, bg=CARD_BG
        ).place(x=q_x, y=ed_y)

        ed_y += 28

        self.cat_listbox = tk.Listbox(
            tab, font=(r.FONT, 12), bg=DARK_BLUE, fg=GOLD,
            selectbackground=GOLD, selectforeground=BLUE,
            exportselection=False, relief="flat",
            highlightbackground=BORDER_BLUE, highlightthickness=2
        )
        self.cat_listbox.place(x=cat_x, y=ed_y, width=cat_col_w, height=200)
        self.cat_listbox.bind("<<ListboxSelect>>", self._on_cat_select)

        cat_btn_y = ed_y + 210
        add_cat_btn = _make_secondary_btn(tab, "+ Kat.", self._add_category, font_size=11)
        add_cat_btn.place(x=cat_x, y=cat_btn_y, width=120, height=32)

        rm_cat_btn = _make_secondary_btn(tab, "- Kat.", self._remove_category, font_size=11)
        rm_cat_btn.place(x=cat_x + 140, y=cat_btn_y, width=120, height=32)

        # Kategorie-Name
        cat_name_y = cat_btn_y + 45
        tk.Label(
            tab, text="Kat-Name:", font=(r.FONT, r.FONT_SMALL),
            fg=LABEL_GRAY, bg=CARD_BG
        ).place(x=cat_x, y=cat_name_y)

        self.cat_name_entry = tk.Entry(
            tab, font=(r.FONT, r.FONT_SMALL),
            bg=DARK_BLUE, fg=GOLD, insertbackground=GOLD, relief="flat"
        )
        self.cat_name_entry.place(x=cat_x + 90, y=cat_name_y - 4, width=cat_col_w - 90, height=30)
        _bind_focus_border(self.cat_name_entry)
        self.cat_name_entry.bind("<FocusOut>", self._on_cat_name_change)
        self.cat_name_entry.bind("<Return>", self._on_cat_name_change)

        # Fragen-Frame rechts
        # Breite auch als Attribut speichern, damit _show_category nicht auf
        # winfo_width() angewiesen ist (liefert vor dem ersten Mapping 1).
        self._q_frame_w = ed_w - cat_col_w - 30
        self.q_frame = tk.Frame(tab, bg=CARD_BG)
        self.q_frame.place(x=q_x, y=ed_y,
                           width=self._q_frame_w, height=290)

    def _refresh_set_listbox(self):
        self.set_listbox.delete(0, tk.END)
        self._sets = r.list_question_sets()
        for filename, display_name in self._sets:
            self.set_listbox.insert(tk.END, display_name)
        if self._sets:
            self.set_listbox.selection_set(0)
            self._load_set_into_editor(self._sets[0][0])

    def _on_set_select(self, event):
        sel = self.set_listbox.curselection()
        if not sel:
            return
        filename = self._sets[sel[0]][0]
        self._load_set_into_editor(filename)

    def _load_set_into_editor(self, filename):
        self._save_current_questions()
        try:
            import json, os
            path = os.path.join(r.get_questionsets_dir(), filename)
            with open(path, "r", encoding="utf-8") as f:
                self.editor_data = json.load(f)
        except (OSError, ValueError):
            self._set_status("Fehler beim Laden!")
            return

        self.editor_filename = filename
        self.current_cat_index = -1

        self.set_name_entry.delete(0, tk.END)
        self.set_name_entry.insert(0, self.editor_data.get("name", ""))

        self.values_entry.delete(0, tk.END)
        vals_str = ", ".join(str(v) for v in self.editor_data.get("values", []))
        self.values_entry.insert(0, vals_str)

        self._refresh_cat_listbox()
        if self.editor_data.get("categories"):
            self.cat_listbox.selection_set(0)
            self._show_category(0)

        self._set_status("")

    def _refresh_cat_listbox(self):
        self.cat_listbox.delete(0, tk.END)
        if not self.editor_data:
            return
        for cat in self.editor_data.get("categories", []):
            display = cat["name"].replace("\n", " ").strip()
            self.cat_listbox.insert(tk.END, display)

    def _on_cat_select(self, event):
        sel = self.cat_listbox.curselection()
        if not sel:
            return
        self._save_current_questions()
        self._show_category(sel[0])

    def _show_category(self, idx):
        if not self.editor_data or idx < 0:
            return
        cats = self.editor_data.get("categories", [])
        if idx >= len(cats):
            return

        self.current_cat_index = idx
        cat = cats[idx]

        self.cat_name_entry.delete(0, tk.END)
        self.cat_name_entry.insert(0, cat["name"])

        for w in self.q_frame.winfo_children():
            w.destroy()
        self.question_entries.clear()

        vals = self._parse_values()
        questions = cat.get("questions", [])

        # Feste Breite aus _build_fragenset_tab — winfo_width() wäre vor dem
        # ersten Mapping 1, was die Eingabefelder kaputtrendern würde.
        frame_w = self._q_frame_w

        for i in range(len(vals)):
            val_text = str(vals[i]) if i < len(vals) else "?"
            tk.Label(
                self.q_frame, text=f"{val_text}:", font=(r.FONT, r.FONT_BODY, "bold"),
                fg=GOLD, bg=CARD_BG, width=6, anchor="e"
            ).place(x=0, y=i * 48, height=36)

            entry = tk.Entry(
                self.q_frame, font=(r.FONT, 11),
                bg=DARK_BLUE, fg=GOLD, insertbackground=GOLD, relief="flat"
            )
            entry.place(x=75, y=i * 48, width=frame_w - 85, height=36)
            _bind_focus_border(entry)

            q_text = questions[i] if i < len(questions) else ""
            entry.insert(0, q_text)
            self.question_entries.append(entry)

    def _save_current_questions(self):
        if not self.editor_data or self.current_cat_index < 0:
            return
        cats = self.editor_data.get("categories", [])
        if self.current_cat_index >= len(cats):
            return

        questions = []
        for entry in self.question_entries:
            try:
                questions.append(entry.get())
            except tk.TclError:
                return
        cats[self.current_cat_index]["questions"] = questions

        try:
            new_name = self.cat_name_entry.get()
        except tk.TclError:
            return
        if new_name:
            cats[self.current_cat_index]["name"] = new_name

    def _on_cat_name_change(self, event):
        if not self.editor_data or self.current_cat_index < 0:
            return
        cats = self.editor_data.get("categories", [])
        if self.current_cat_index >= len(cats):
            return
        new_name = self.cat_name_entry.get()
        cats[self.current_cat_index]["name"] = new_name
        display = new_name.replace("\n", " ").strip()
        self.cat_listbox.delete(self.current_cat_index)
        self.cat_listbox.insert(self.current_cat_index, display)
        self.cat_listbox.selection_set(self.current_cat_index)

    def _add_category(self):
        if not self.editor_data:
            return
        self._save_current_questions()
        vals = self._parse_values()
        new_cat = {"name": "Neue Kategorie", "questions": [""] * len(vals)}
        self.editor_data["categories"].append(new_cat)
        self._refresh_cat_listbox()
        idx = len(self.editor_data["categories"]) - 1
        self.cat_listbox.selection_set(idx)
        self._show_category(idx)

    def _remove_category(self):
        if not self.editor_data:
            return
        sel = self.cat_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.editor_data["categories"].pop(idx)
        self.current_cat_index = -1
        self.question_entries.clear()
        for w in self.q_frame.winfo_children():
            w.destroy()
        self.cat_name_entry.delete(0, tk.END)
        self._refresh_cat_listbox()
        if self.editor_data["categories"]:
            new_idx = min(idx, len(self.editor_data["categories"]) - 1)
            self.cat_listbox.selection_set(new_idx)
            self._show_category(new_idx)

    def _parse_values(self):
        raw = self.values_entry.get()
        result = []
        for part in raw.split(","):
            part = part.strip()
            if part.isdigit():
                result.append(int(part))
        return result if result else [100, 200, 400, 600, 1000]

    def _save_set(self):
        if not self.editor_data or not self.editor_filename:
            self._set_status("Kein Set ausgewählt!")
            return
        self._save_current_questions()

        name = self.set_name_entry.get().strip() or "Unnamed"
        vals = self._parse_values()

        self.editor_data["name"] = name
        self.editor_data["values"] = vals

        for cat in self.editor_data["categories"]:
            qs = cat.get("questions", [])
            while len(qs) < len(vals):
                qs.append("")
            cat["questions"] = qs[:len(vals)]

        r.save_question_set(
            self.editor_filename, name, vals,
            self.editor_data["categories"]
        )
        self.status_label.config(text="Gespeichert!", fg=r.SUCCESS_GREEN)
        self.root.after(3000, lambda: self.status_label.config(text=""))
        self._refresh_set_listbox()
        for i, (fn, _) in enumerate(self._sets):
            if fn == self.editor_filename:
                self.set_listbox.selection_set(i)
                break

    def _new_set(self):
        vals = [100, 200, 400, 600, 1000]
        cats = [{"name": "Neue Kategorie", "questions": [""] * len(vals)}]
        existing = {fn for fn, _ in r.list_question_sets()}
        idx = 1
        while f"custom_{idx}.json" in existing:
            idx += 1
        filename = f"custom_{idx}.json"
        r.save_question_set(filename, f"Neues Set {idx}", vals, cats)
        self._refresh_set_listbox()
        for i, (fn, _) in enumerate(self._sets):
            if fn == filename:
                self.set_listbox.selection_set(i)
                self._load_set_into_editor(fn)
                break

    def _delete_set(self):
        sel = self.set_listbox.curselection()
        if not sel:
            return
        filename = self._sets[sel[0]][0]
        r.delete_question_set(filename)
        self.editor_data = None
        self.editor_filename = None
        self.current_cat_index = -1
        for w in self.q_frame.winfo_children():
            w.destroy()
        self.question_entries.clear()
        self.set_name_entry.delete(0, tk.END)
        self.values_entry.delete(0, tk.END)
        self.cat_listbox.delete(0, tk.END)
        self.cat_name_entry.delete(0, tk.END)
        self._refresh_set_listbox()

    def _set_status(self, text):
        self.status_label.config(text=text, fg=r.ERROR_RED)
        if text:
            self.root.after(3000, lambda: self.status_label.config(text=""))

    # ------------------------------------------------------------------
    # DESIGN Tab (Theme-Auswahl)
    # ------------------------------------------------------------------

    def _build_design_tab(self):
        """Baut den DESIGN-Tab: 4 Theme-Karten mit Farbvorschau + Auswahl."""
        tab = tk.Frame(self.root, bg=CARD_BG)
        accent = tk.Frame(tab, bg=GOLD)
        accent.place(x=0, y=0, width=4, relheight=1)
        self.tab_frames["design"] = tab

        tk.Label(
            tab, text="FARB-DESIGN", font=(r.FONT, r.FONT_SECTION, "bold"),
            fg=GOLD, bg=CARD_BG
        ).place(x=30, y=20)

        tk.Label(
            tab,
            text="Wähle ein Farbschema. Die Änderung wird sofort übernommen.",
            font=(r.FONT, r.FONT_SMALL), fg=LABEL_GRAY, bg=CARD_BG
        ).place(x=30, y=60)

        # Karten-Grid (2x2)
        grid = tk.Frame(tab, bg=CARD_BG)
        grid_y = 100
        grid_h = self.content_h - grid_y - 30
        grid.place(x=30, y=grid_y, width=self.content_w - 60, height=grid_h)

        self._theme_cards = {}
        theme_keys = list(r.THEMES.keys())
        card_w = (self.content_w - 60 - 30) // 2
        card_h = (grid_h - 30) // 2

        for i, key in enumerate(theme_keys):
            col = i % 2
            row = i // 2
            cx = col * (card_w + 30)
            cy = row * (card_h + 30)
            self._build_theme_card(grid, key, cx, cy, card_w, card_h)

    def _build_theme_card(self, parent, key, x, y, w, h):
        """Baut eine einzelne Theme-Karte mit Farbvorschau und Klick-Handler."""
        theme = r.THEMES[key]
        is_active = (key == r.current_theme_name)

        border_color = GOLD if is_active else BORDER_BLUE
        border_thick = 3 if is_active else 2

        card = tk.Frame(
            parent, bg=theme["CARD_BG"],
            highlightbackground=border_color, highlightthickness=border_thick,
            cursor="hand2"
        )
        card.place(x=x, y=y, width=w, height=h)

        # Theme-Name
        tk.Label(
            card, text=theme["label"], font=(r.FONT, 20, "bold"),
            fg=theme["GOLD"], bg=theme["CARD_BG"]
        ).place(x=20, y=20)

        # Beschreibung
        tk.Label(
            card, text=theme["description"], font=(r.FONT, r.FONT_SMALL),
            fg=theme["LABEL_GRAY"], bg=theme["CARD_BG"]
        ).place(x=20, y=55)

        # Farb-Swatches: Primär / Akzent / Hintergrund
        swatch_y = 100
        swatch_w = 60
        swatch_h = 60
        swatches = [
            (theme["BLUE"], "Primär"),
            (theme["GOLD"], "Akzent"),
            (theme["DARK_BLUE"], "Eingabe"),
            (theme["LABEL_GRAY"], "Label"),
        ]
        for j, (color, label) in enumerate(swatches):
            sx = 20 + j * (swatch_w + 12)
            sw = tk.Frame(card, bg=color,
                          highlightbackground=theme["GOLD"], highlightthickness=1)
            sw.place(x=sx, y=swatch_y, width=swatch_w, height=swatch_h)
            tk.Label(
                card, text=label, font=(r.FONT, 10),
                fg=theme["LABEL_GRAY"], bg=theme["CARD_BG"]
            ).place(x=sx, y=swatch_y + swatch_h + 4, width=swatch_w, anchor="nw")

        # Aktiv-Marker
        if is_active:
            tk.Label(
                card, text="AKTIV", font=(r.FONT, 12, "bold"),
                fg=theme["CARD_BG"], bg=theme["GOLD"], padx=10, pady=3
            ).place(relx=1.0, y=20, x=-20, anchor="ne")

        # Klick-Handler (auf Card + allen Kindern, damit man überall klicken kann)
        def on_click(_e, k=key):
            self._select_theme(k)
        card.bind("<Button-1>", on_click)
        for child in card.winfo_children():
            child.bind("<Button-1>", on_click)

        self._theme_cards[key] = card

    def _select_theme(self, name):
        """Wendet ein Theme an, speichert es und baut den Settings-Screen neu auf."""
        if name == r.current_theme_name:
            return
        r.apply_theme(name)
        r.save_current_theme(name)
        self.theme_changed = True
        # Settings-State in r persistieren, damit Restart die Teams/Set behält
        self._read_teams_from_ui()
        self._save_current_questions()
        self.root.destroy()

    # ------------------------------------------------------------------
    # START Tab
    # ------------------------------------------------------------------

    def _build_start_tab(self):
        """Baut den START-Tab auf: Zusammenfassung + großer Start-Button."""
        tab = tk.Frame(self.root, bg=CARD_BG)
        accent = tk.Frame(tab, bg=GOLD)
        accent.place(x=0, y=0, width=4, relheight=1)

        self.tab_frames["start"] = tab

        # Titel
        tk.Label(
            tab, text="BEREIT ZUM START?",
            font=(r.FONT, r.FONT_SECTION, "bold"), fg=GOLD, bg=CARD_BG
        ).place(x=30, y=20)

        # Zusammenfassungs-Box
        box_x = 60
        box_y = 90
        box_w = self.content_w - 120
        box_h = self.content_h - 280

        summary_box = tk.Frame(
            tab, bg=DARK_BLUE,
            highlightbackground=BORDER_BLUE, highlightthickness=2
        )
        summary_box.place(x=box_x, y=box_y, width=box_w, height=box_h)

        # Inhalt der Box — wird bei Tab-Wechsel aktualisiert
        self.summary_content = tk.Frame(summary_box, bg=DARK_BLUE)
        self.summary_content.place(x=30, y=25,
                                   width=box_w - 60, height=box_h - 50)

        # Fehler-Label über dem Start-Button
        self.error_label = tk.Label(
            tab, text="", font=(r.FONT, r.FONT_BUTTON),
            fg=r.ERROR_RED, bg=CARD_BG
        )
        self.error_label.place(x=self.content_w // 2,
                               y=box_y + box_h + 30, anchor="n")

        # Großer "SPIEL STARTEN" Button
        start_btn = r.FlatButton(
            tab, text=">>> SPIEL STARTEN <<<",
            command=self._start_game,
            font=(r.FONT, 24, "bold"),
        )
        start_btn.place(x=self.content_w // 2,
                        y=box_y + box_h + 70, anchor="n",
                        width=500, height=70)

    def _refresh_start_summary(self):
        """Aktualisiert die Zusammenfassung im START-Tab."""
        for w in self.summary_content.winfo_children():
            w.destroy()

        # Teams-Sektion
        y = 0
        tk.Label(
            self.summary_content, text="Teams:", font=(r.FONT, r.FONT_BUTTON, "bold"),
            fg=GOLD, bg=DARK_BLUE, anchor="w"
        ).place(x=0, y=y, width=200, height=28)

        teams_text = f"{len(r.teams)} Teams"
        tk.Label(
            self.summary_content, text=teams_text, font=(r.FONT, r.FONT_BUTTON),
            fg="white", bg=DARK_BLUE, anchor="w"
        ).place(x=220, y=y, width=400, height=28)

        # Team-Namen zeigen
        y += 34
        for i, team in enumerate(r.teams):
            swatch = tk.Frame(self.summary_content, bg=team["color"],
                              highlightbackground=GOLD, highlightthickness=1)
            swatch.place(x=20, y=y, width=24, height=24)
            tk.Label(
                self.summary_content, text=team["name"],
                font=(r.FONT, r.FONT_SMALL), fg="white", bg=DARK_BLUE, anchor="w"
            ).place(x=55, y=y, width=400, height=24)
            y += 30

        y += 15

        # Fragenset-Sektion
        tk.Label(
            self.summary_content, text="Fragenset:", font=(r.FONT, r.FONT_BUTTON, "bold"),
            fg=GOLD, bg=DARK_BLUE, anchor="w"
        ).place(x=0, y=y, width=200, height=28)

        if self.editor_data:
            try:
                set_name = self.set_name_entry.get().strip() or "Unnamed"
            except tk.TclError:
                set_name = self.editor_data.get("name", "Unnamed")
            num_cats = len(self.editor_data.get("categories", []))
            try:
                vals = self._parse_values()
            except tk.TclError:
                vals = self.editor_data.get("values", [])
            info = f'"{set_name}" — {num_cats} Kategorien, Werte: {", ".join(str(v) for v in vals)}'
        else:
            info = "Kein Set ausgewählt!"

        tk.Label(
            self.summary_content, text=info, font=(r.FONT, r.FONT_SMALL),
            fg="white", bg=DARK_BLUE, anchor="w", wraplength=self.content_w - 300,
            justify="left"
        ).place(x=220, y=y, width=self.content_w - 360, height=60)

    # ------------------------------------------------------------------
    # App-Steuerung
    # ------------------------------------------------------------------

    def _quit_app(self):
        """Beendet die gesamte Anwendung ohne das Spiel zu starten."""
        self.root.destroy()
        import sys
        sys.exit(0)

    def _start_game(self):
        self._save_current_questions()
        self._read_teams_from_ui()

        if not self.editor_data or not self.editor_filename:
            self.error_label.config(text="Bitte ein Fragenset auswählen!")
            return

        try:
            if self.editor_data:
                name = self.set_name_entry.get().strip() or "Unnamed"
                vals = self._parse_values()
                self.editor_data["name"] = name
                self.editor_data["values"] = vals
                for cat in self.editor_data["categories"]:
                    qs = cat.get("questions", [])
                    while len(qs) < len(vals):
                        qs.append("")
                    cat["questions"] = qs[:len(vals)]
                r.save_question_set(
                    self.editor_filename, name, vals,
                    self.editor_data["categories"]
                )

            r.load_question_set(self.editor_filename)
        except Exception as e:
            self.error_label.config(text=f"Fehler: {e}")
            return

        if not r.categories:
            self.error_label.config(text="Mindestens 1 Kategorie nötig!")
            return

        for i, cat_qs in enumerate(r.questions):
            if len(cat_qs) < len(r.values):
                self.error_label.config(
                    text=f"Kategorie '{r.categories[i]}' hat zu wenige Fragen!"
                )
                return

        self.game_started = True
        self.root.destroy()


def run():
    # Restart-Schleife: bei Theme-Wechsel wird destroy() aufgerufen und wir
    # bauen den Screen mit den neuen Farben frisch auf.
    while True:
        root = tk.Tk()
        root.title("Jeopardy! Setup")
        screen = SettingsScreen(root)
        root.mainloop()
        if not screen.theme_changed:
            break
        # Flag zurücksetzen + nächste Iteration
        screen.theme_changed = False

    # game_started-Flag nach außen propagieren wird nicht benötigt — main.py
    # ruft game.run() ohnehin im Anschluss auf.


if __name__ == "__main__":
    run()
