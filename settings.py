import tkinter as tk
import resources as r

BLUE = "#060CE9"
GOLD = "#DBAB51"


class ColorPicker(tk.Toplevel):
    """Small popup to pick a team color from the palette."""

    def __init__(self, parent, current_color, callback):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=BLUE, highlightbackground=GOLD, highlightthickness=2)
        self.callback = callback

        # Position near the parent widget
        x = parent.winfo_rootx() + parent.winfo_width() + 5
        y = parent.winfo_rooty()
        self.geometry(f"+{x}+{y}")

        for i, color in enumerate(r.TEAM_PALETTE):
            swatch = tk.Frame(self, bg=color, width=40, height=40,
                              highlightbackground=GOLD, highlightthickness=1,
                              cursor="hand2")
            swatch.grid(row=i // 3, column=i % 3, padx=3, pady=3)
            swatch.bind("<Button-1>", lambda e, c=color: self._pick(c))

        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()
        self.grab_set()

    def _pick(self, color):
        self.callback(color)
        self.destroy()


class SettingsScreen:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg=BLUE)
        self.root.attributes("-fullscreen", True)

        self.sw = root.winfo_screenwidth()
        self.sh = root.winfo_screenheight()

        # Editor state
        self.editor_data = None       # {"name", "values", "categories"}
        self.editor_filename = None   # currently loaded filename
        self.current_cat_index = -1   # selected category index
        self.team_rows = []           # list of (name_entry, color_label, color_value)
        self.question_entries = []    # list of tk.Entry for current category

        self._build_header()
        self._build_team_panel()
        self._build_question_panel()
        self._build_start_button()

        # Load initial state
        self._refresh_set_listbox()
        self._update_key_info()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self):
        tk.Label(
            self.root, text="JEOPARDY! SETUP",
            font=(r.FONT, 48, "bold"), fg=GOLD, bg=BLUE
        ).place(x=self.sw // 2, y=30, anchor="n")

        canvas = tk.Canvas(self.root, bg=BLUE, highlightthickness=0, height=4)
        canvas.place(x=self.sw // 2 - 250, y=95, width=500, height=4)
        canvas.create_line(0, 2, 500, 2, fill=GOLD, width=3)

    # ------------------------------------------------------------------
    # Left panel: Teams
    # ------------------------------------------------------------------

    def _build_team_panel(self):
        lx = 40
        ly = 140
        panel_w = int(self.sw * 0.28)

        tk.Label(
            self.root, text="TEAMS", font=(r.FONT, 24, "bold"),
            fg=GOLD, bg=BLUE
        ).place(x=lx, y=ly)

        # Team count selector
        ly += 50
        tk.Label(
            self.root, text="Anzahl:", font=(r.FONT, 16),
            fg=GOLD, bg=BLUE
        ).place(x=lx, y=ly)

        self.team_count_label = tk.Label(
            self.root, text=str(len(r.teams)), font=(r.FONT, 20, "bold"),
            fg=GOLD, bg="#0A10A0", width=3
        )
        self.team_count_label.place(x=lx + 130, y=ly - 2)

        tk.Button(
            self.root, text="-", font=(r.FONT, 14, "bold"),
            fg=BLUE, bg=GOLD, width=2, command=self._remove_team,
            cursor="hand2"
        ).place(x=lx + 100, y=ly)

        tk.Button(
            self.root, text="+", font=(r.FONT, 14, "bold"),
            fg=BLUE, bg=GOLD, width=2, command=self._add_team,
            cursor="hand2"
        ).place(x=lx + 195, y=ly)

        # Team rows container
        self.team_frame_y = ly + 50
        self.team_frame_x = lx
        self.team_frame = tk.Frame(self.root, bg=BLUE)
        self.team_frame.place(x=lx, y=self.team_frame_y, width=panel_w, height=350)

        # Key info (must exist before _rebuild_team_rows calls _update_key_info)
        self.key_info_label = tk.Label(
            self.root, text="", font=(r.FONT, 13), fg=GOLD, bg=BLUE,
            justify="left", anchor="nw"
        )
        self.key_info_label.place(x=lx, y=self.team_frame_y + 360, width=panel_w, height=150)

        self._rebuild_team_rows()

    def _rebuild_team_rows(self):
        for widget in self.team_frame.winfo_children():
            widget.destroy()
        self.team_rows.clear()

        for i, team in enumerate(r.teams):
            row_y = i * 55

            # Name entry
            entry = tk.Entry(
                self.team_frame, font=(r.FONT, 14), width=15,
                bg="#0A10A0", fg=GOLD, insertbackground=GOLD
            )
            entry.place(x=0, y=row_y, height=40)
            entry.insert(0, team["name"])

            # Color swatch
            color_lbl = tk.Label(
                self.team_frame, bg=team["color"], width=4, height=2,
                relief="solid", borderwidth=2, cursor="hand2"
            )
            color_lbl.place(x=230, y=row_y, width=40, height=40)
            color_lbl.bind("<Button-1>", lambda e, idx=i: self._open_color_picker(idx))

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
        lines = ["Tasten:"]
        for i, team in enumerate(r.teams):
            lines.append(f"  {i + 1} = {team['name']}")
        lines.append(f"  {len(r.teams) + 1} = Niemand")
        self.key_info_label.config(text="\n".join(lines))

    def _read_teams_from_ui(self):
        """Sync team names from entry widgets back to r.teams."""
        for i, (entry, _, color) in enumerate(self.team_rows):
            name = entry.get().strip()
            if not name:
                name = f"Team {i + 1}"
            r.teams[i]["name"] = name
            r.teams[i]["color"] = color

    # ------------------------------------------------------------------
    # Right panel: Question sets
    # ------------------------------------------------------------------

    def _build_question_panel(self):
        rx = int(self.sw * 0.32)
        ry = 140
        panel_w = int(self.sw * 0.65)

        tk.Label(
            self.root, text="FRAGENSET", font=(r.FONT, 24, "bold"),
            fg=GOLD, bg=BLUE
        ).place(x=rx, y=ry)

        # Set selector listbox
        ry += 50
        self.set_listbox = tk.Listbox(
            self.root, font=(r.FONT, 13), bg="#0A10A0", fg=GOLD,
            selectbackground=GOLD, selectforeground=BLUE,
            height=4, width=30, exportselection=False
        )
        self.set_listbox.place(x=rx, y=ry)
        self.set_listbox.bind("<<ListboxSelect>>", self._on_set_select)

        btn_x = rx + 340
        tk.Button(
            self.root, text="Neu", font=(r.FONT, 12), fg=BLUE, bg=GOLD,
            command=self._new_set, cursor="hand2"
        ).place(x=btn_x, y=ry, width=80, height=35)

        tk.Button(
            self.root, text="Löschen", font=(r.FONT, 12), fg=BLUE, bg=GOLD,
            command=self._delete_set, cursor="hand2"
        ).place(x=btn_x, y=ry + 40, width=80, height=35)

        # Editor area
        ry += 110
        tk.Label(
            self.root, text="Name:", font=(r.FONT, 14), fg=GOLD, bg=BLUE
        ).place(x=rx, y=ry)

        self.set_name_entry = tk.Entry(
            self.root, font=(r.FONT, 14), width=30,
            bg="#0A10A0", fg=GOLD, insertbackground=GOLD
        )
        self.set_name_entry.place(x=rx + 70, y=ry, height=32)

        ry += 42
        tk.Label(
            self.root, text="Werte:", font=(r.FONT, 14), fg=GOLD, bg=BLUE
        ).place(x=rx, y=ry)

        self.values_entry = tk.Entry(
            self.root, font=(r.FONT, 14), width=30,
            bg="#0A10A0", fg=GOLD, insertbackground=GOLD
        )
        self.values_entry.place(x=rx + 70, y=ry, height=32)

        # Category list + question entries
        ry += 50
        cat_x = rx
        q_x = rx + 280

        tk.Label(
            self.root, text="Kategorien:", font=(r.FONT, 14), fg=GOLD, bg=BLUE
        ).place(x=cat_x, y=ry)

        tk.Label(
            self.root, text="Fragen:", font=(r.FONT, 14), fg=GOLD, bg=BLUE
        ).place(x=q_x, y=ry)

        ry += 30
        self.cat_listbox = tk.Listbox(
            self.root, font=(r.FONT, 12), bg="#0A10A0", fg=GOLD,
            selectbackground=GOLD, selectforeground=BLUE,
            height=10, width=22, exportselection=False
        )
        self.cat_listbox.place(x=cat_x, y=ry)
        self.cat_listbox.bind("<<ListboxSelect>>", self._on_cat_select)

        cat_btn_y = ry + 225
        tk.Button(
            self.root, text="+ Kat.", font=(r.FONT, 11), fg=BLUE, bg=GOLD,
            command=self._add_category, cursor="hand2"
        ).place(x=cat_x, y=cat_btn_y, width=80, height=30)

        tk.Button(
            self.root, text="- Kat.", font=(r.FONT, 11), fg=BLUE, bg=GOLD,
            command=self._remove_category, cursor="hand2"
        ).place(x=cat_x + 90, y=cat_btn_y, width=80, height=30)

        # Category name entry
        cat_name_y = cat_btn_y + 40
        tk.Label(
            self.root, text="Kat-Name:", font=(r.FONT, 13), fg=GOLD, bg=BLUE
        ).place(x=cat_x, y=cat_name_y)

        self.cat_name_entry = tk.Entry(
            self.root, font=(r.FONT, 13), width=20,
            bg="#0A10A0", fg=GOLD, insertbackground=GOLD
        )
        self.cat_name_entry.place(x=cat_x + 110, y=cat_name_y, height=30)
        self.cat_name_entry.bind("<FocusOut>", self._on_cat_name_change)
        self.cat_name_entry.bind("<Return>", self._on_cat_name_change)

        # Question entries frame (scrollable area)
        self.q_frame = tk.Frame(self.root, bg=BLUE)
        self.q_frame.place(x=q_x, y=ry, width=int(self.sw * 0.62) - q_x + rx, height=320)

        # Save button
        save_y = cat_name_y + 45
        tk.Button(
            self.root, text="Speichern", font=(r.FONT, 14, "bold"),
            fg=BLUE, bg=GOLD, command=self._save_set, cursor="hand2"
        ).place(x=rx, y=save_y, width=150, height=40)

        # Status label for feedback
        self.status_label = tk.Label(
            self.root, text="", font=(r.FONT, 12), fg="#FF6666", bg=BLUE
        )
        self.status_label.place(x=rx + 170, y=save_y + 8)

    def _refresh_set_listbox(self):
        self.set_listbox.delete(0, tk.END)
        self._sets = r.list_question_sets()
        for filename, display_name in self._sets:
            self.set_listbox.insert(tk.END, display_name)
        # Auto-select first set if available
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
            import json
            path = r.get_questionsets_dir()
            with open(f"{path}/{filename}", "r", encoding="utf-8") as f:
                self.editor_data = json.load(f)
        except (OSError, ValueError):
            self._set_status("Fehler beim Laden!")
            return

        self.editor_filename = filename
        self.current_cat_index = -1

        # Populate name + values
        self.set_name_entry.delete(0, tk.END)
        self.set_name_entry.insert(0, self.editor_data.get("name", ""))

        self.values_entry.delete(0, tk.END)
        vals_str = ", ".join(str(v) for v in self.editor_data.get("values", []))
        self.values_entry.insert(0, vals_str)

        # Populate category listbox
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

        # Update cat name entry
        self.cat_name_entry.delete(0, tk.END)
        self.cat_name_entry.insert(0, cat["name"])

        # Rebuild question entries
        for w in self.q_frame.winfo_children():
            w.destroy()
        self.question_entries.clear()

        vals = self._parse_values()
        questions = cat.get("questions", [])

        for i in range(len(vals)):
            # Value label
            val_text = str(vals[i]) if i < len(vals) else "?"
            tk.Label(
                self.q_frame, text=f"{val_text}:", font=(r.FONT, 12),
                fg=GOLD, bg=BLUE, width=6, anchor="e"
            ).place(x=0, y=i * 42, height=34)

            entry = tk.Entry(
                self.q_frame, font=(r.FONT, 11),
                bg="#0A10A0", fg=GOLD, insertbackground=GOLD
            )
            entry.place(x=70, y=i * 42, width=self.q_frame.winfo_width() - 80 if self.q_frame.winfo_width() > 100 else 400, height=34)

            q_text = questions[i] if i < len(questions) else ""
            entry.insert(0, q_text)
            self.question_entries.append(entry)

    def _save_current_questions(self):
        """Save question entries back into editor_data for the current category."""
        if not self.editor_data or self.current_cat_index < 0:
            return
        cats = self.editor_data.get("categories", [])
        if self.current_cat_index >= len(cats):
            return

        questions = []
        for entry in self.question_entries:
            questions.append(entry.get())
        cats[self.current_cat_index]["questions"] = questions

        # Also save cat name
        new_name = self.cat_name_entry.get()
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
        # Update listbox display
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
        # Select new category
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
        # Select adjacent
        if self.editor_data["categories"]:
            new_idx = min(idx, len(self.editor_data["categories"]) - 1)
            self.cat_listbox.selection_set(new_idx)
            self._show_category(new_idx)

    def _parse_values(self):
        """Parse the comma-separated values entry into a list of ints."""
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

        # Sync values into editor_data
        self.editor_data["name"] = name
        self.editor_data["values"] = vals

        # Pad/truncate questions to match values count
        for cat in self.editor_data["categories"]:
            qs = cat.get("questions", [])
            while len(qs) < len(vals):
                qs.append("")
            cat["questions"] = qs[:len(vals)]

        r.save_question_set(
            self.editor_filename, name, vals,
            self.editor_data["categories"]
        )
        self._set_status("Gespeichert!")
        self._refresh_set_listbox()
        # Re-select the saved set
        for i, (fn, _) in enumerate(self._sets):
            if fn == self.editor_filename:
                self.set_listbox.selection_set(i)
                break

    def _new_set(self):
        vals = [100, 200, 400, 600, 1000]
        cats = [{"name": "Neue Kategorie", "questions": [""] * len(vals)}]
        # Generate unique filename
        existing = {fn for fn, _ in r.list_question_sets()}
        idx = 1
        while f"custom_{idx}.json" in existing:
            idx += 1
        filename = f"custom_{idx}.json"
        r.save_question_set(filename, f"Neues Set {idx}", vals, cats)
        self._refresh_set_listbox()
        # Select the new set
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
        self.status_label.config(text=text)
        if text:
            self.root.after(3000, lambda: self.status_label.config(text=""))

    # ------------------------------------------------------------------
    # Start button
    # ------------------------------------------------------------------

    def _build_start_button(self):
        btn_y = self.sh - 90
        self.error_label = tk.Label(
            self.root, text="", font=(r.FONT, 14), fg="#FF6666", bg=BLUE
        )
        self.error_label.place(x=self.sw // 2, y=btn_y - 35, anchor="n")

        tk.Button(
            self.root, text=">>> SPIEL STARTEN <<<",
            font=(r.FONT, 22, "bold"), fg=BLUE, bg=GOLD,
            activebackground="#C89840", activeforeground=BLUE,
            command=self._start_game, cursor="hand2"
        ).place(x=self.sw // 2, y=btn_y, anchor="n", width=450, height=60)

    def _start_game(self):
        # Save current editor state
        self._save_current_questions()

        # Read team config from UI
        self._read_teams_from_ui()

        # Validate: a question set must be selected
        if not self.editor_data or not self.editor_filename:
            self.error_label.config(text="Bitte ein Fragenset auswählen!")
            return

        # Load the selected set into resources
        try:
            # First save any unsaved edits
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

        # Validate: at least 1 category
        if not r.categories:
            self.error_label.config(text="Mindestens 1 Kategorie nötig!")
            return

        # Validate: questions match values
        for i, cat_qs in enumerate(r.questions):
            if len(cat_qs) < len(r.values):
                self.error_label.config(
                    text=f"Kategorie '{r.categories[i]}' hat zu wenige Fragen!"
                )
                return

        self.root.destroy()


def run():
    root = tk.Tk()
    root.title("Jeopardy! Setup")
    SettingsScreen(root)
    root.mainloop()


if __name__ == "__main__":
    run()
