# Antworten-Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optionales Anzeigen der Antwort nach Beantwortung einer Frage — manuell per `A`-Taste oder automatisch nach Punktevergabe, mit Karten-Flip-Animation zur Gold-Antwort-Seite.

**Architecture:** Drei Ebenen: (1) Datenmodell in `resources.py` erweitern (Fragen werden zu `{"q":..., "a":...}`-Dicts, neuer `show_answers`-Flag pro Set), (2) `settings.py` bekommt zweites Eingabefeld pro Frage und Set-Toggle, (3) `game.py` State-Maschine mit Flip zur Antwort-Seite plus `A`-Taste.

**Tech Stack:** Python 3, tkinter (kein PyQt5), pygame.mixer (optional für Audio), unittest für Tests.

**Spec:** `docs/superpowers/specs/2026-04-28-antworten-feature-design.md`

---

## File Structure

| Datei | Verantwortung |
|---|---|
| `resources.py` | Question/Answer Normalisierung beim Laden/Speichern, Modul-State `r.answers`, `r.show_answers` |
| `settings.py` | UI: zweites Eingabefeld pro Frage, Toggle pro Set, Persistenz dict-basiert |
| `game.py` | State-Maschine pro LButton, `A`-Taste, Flip-zur-Antwort-Seite, Audio-Stop bei Flip |
| `test_jeopardy_extended.py` | Unit-Tests für Normalisierung + Roundtrip + Backward-Compat |
| `CLAUDE.md` | Doku: Datenmodell-Erweiterung, neue Tasten, State-Maschine |

---

## Task 1: Datenmodell — Question-Normalisierung in resources.py

**Files:**
- Modify: `resources.py:323-449` (Game Data + Fragenset-Verwaltung Sektionen)
- Test: `test_jeopardy_extended.py` (am Ende neue TestCase ergänzen)

### Steps

- [ ] **Step 1: Test schreiben — Normalisierung String → Dict-Tupel**

Neue Datei oder am Ende von `test_jeopardy_extended.py` ergänzen:

```python
class TestQuestionNormalization(unittest.TestCase):
    """Tests für die _normalize_question Hilfsfunktion."""

    def test_string_input_returns_q_and_empty_a(self):
        q, a = r._normalize_question("Was ist 2+2?")
        self.assertEqual(q, "Was ist 2+2?")
        self.assertEqual(a, "")

    def test_dict_with_q_and_a_returns_both(self):
        q, a = r._normalize_question({"q": "Hauptstadt?", "a": "Berlin"})
        self.assertEqual(q, "Hauptstadt?")
        self.assertEqual(a, "Berlin")

    def test_dict_without_a_returns_empty_a(self):
        q, a = r._normalize_question({"q": "Hauptstadt?"})
        self.assertEqual(q, "Hauptstadt?")
        self.assertEqual(a, "")

    def test_empty_string_returns_empty_q(self):
        q, a = r._normalize_question("")
        self.assertEqual(q, "")
        self.assertEqual(a, "")
```

- [ ] **Step 2: Tests laufen lassen — sollten fehlschlagen**

```bash
cd /Users/laurinokon/PycharmProjects/Jepoardy
python -m unittest test_jeopardy_extended.TestQuestionNormalization -v
```

Erwartet: FAIL mit `AttributeError: module 'resources' has no attribute '_normalize_question'`.

- [ ] **Step 3: `_normalize_question` und `_serialize_question` in resources.py implementieren**

In `resources.py` direkt vor `def get_questionsets_dir()` (also ca. Zeile 391) einfügen:

```python
def _normalize_question(q):
    """Normalisiert eine Frage zu einem (q_text, a_text) Tupel.

    Akzeptiert sowohl alte String-Formate als auch neue Dict-Formate
    {"q": str, "a": str}. Fehlende Felder werden zu "".
    """
    if isinstance(q, dict):
        return q.get("q", ""), q.get("a", "")
    return str(q), ""


def _serialize_question(q_text, a_text):
    """Konvertiert (Frage, Antwort) zu Dict-Form für JSON-Speicherung."""
    return {"q": q_text, "a": a_text}
```

- [ ] **Step 4: Tests erneut laufen lassen — sollten passen**

```bash
python -m unittest test_jeopardy_extended.TestQuestionNormalization -v
```

Erwartet: 4 Tests PASS.

- [ ] **Step 5: Commit**

```bash
git add resources.py test_jeopardy_extended.py
git commit -m "$(cat <<'EOF'
feat: add question normalization helpers in resources

Bereitet Datenmodell für Antworten-Feature vor: Fragen können nun
optional als Dict {"q":..., "a":...} statt nur String hinterlegt werden.
_normalize_question akzeptiert beide Formate, _serialize_question
konvertiert für JSON-Speicherung.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Modul-State `r.answers` und `r.show_answers` + Lade-Logik

**Files:**
- Modify: `resources.py:326-430` (Game Data Sektion + load_question_set)
- Test: `test_jeopardy_extended.py`

### Steps

- [ ] **Step 1: Test schreiben — Laden eines Sets mit Antworten und Toggle**

Am Ende von `test_jeopardy_extended.py`:

```python
class TestLoadQuestionSetWithAnswers(unittest.TestCase):
    """Tests für load_question_set mit dem erweiterten Format."""

    def setUp(self):
        # Temporäres questionsets-Verzeichnis nutzen
        self.tmp = tempfile.mkdtemp()
        self._orig_data_path = r.data_path
        r.data_path = lambda relative_path="": (
            os.path.join(self.tmp, relative_path) if relative_path else self.tmp
        )

    def tearDown(self):
        r.data_path = self._orig_data_path
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_set(self, filename, payload):
        d = r.get_questionsets_dir()
        with open(os.path.join(d, filename), "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def test_load_dict_questions_populates_answers(self):
        self._write_set("t.json", {
            "name": "T",
            "values": [100, 200],
            "show_answers": True,
            "categories": [
                {"name": "C1", "questions": [
                    {"q": "Frage A?", "a": "Antwort A"},
                    {"q": "Frage B?", "a": "Antwort B"},
                ]}
            ]
        })
        r.load_question_set("t.json")
        self.assertEqual(r.questions, [["Frage A?", "Frage B?"]])
        self.assertEqual(r.answers, [["Antwort A", "Antwort B"]])
        self.assertTrue(r.show_answers)

    def test_load_legacy_string_questions_works(self):
        """Alte Sets mit String-Fragen müssen weiter funktionieren."""
        self._write_set("legacy.json", {
            "name": "Legacy",
            "values": [100],
            "categories": [
                {"name": "C1", "questions": ["Alte Frage?"]}
            ]
        })
        r.load_question_set("legacy.json")
        self.assertEqual(r.questions, [["Alte Frage?"]])
        self.assertEqual(r.answers, [[""]])
        self.assertFalse(r.show_answers)

    def test_load_mixed_questions_normalizes_all(self):
        self._write_set("mix.json", {
            "name": "Mix",
            "values": [100, 200],
            "categories": [
                {"name": "C", "questions": [
                    "Plain String",
                    {"q": "Dict mit a", "a": "antwort"},
                ]}
            ]
        })
        r.load_question_set("mix.json")
        self.assertEqual(r.questions, [["Plain String", "Dict mit a"]])
        self.assertEqual(r.answers, [["", "antwort"]])
```

- [ ] **Step 2: Tests laufen — sollten fehlschlagen**

```bash
python -m unittest test_jeopardy_extended.TestLoadQuestionSetWithAnswers -v
```

Erwartet: FAIL (entweder `AttributeError: module 'resources' has no attribute 'answers'` oder Vergleichsfehler).

- [ ] **Step 3: `r.answers` und `r.show_answers` als Modul-State ergänzen**

In `resources.py` direkt nach der `questions = [...]` Definition (also nach Zeile 384, vor dem Kommentar-Block "Fragenset-Verwaltung") einfügen:

```python
# Antworten parallel zu questions — gleiche Indizierung: answers[kat_idx][frage_idx]
# Default leer; wird beim Laden eines Sets gefüllt.
answers = [["" for _ in row] for row in questions]

# Globaler Toggle: zeigt das Spiel nach Beantwortung die Antwort an?
# Wird pro geladenem Set aus dem JSON-Feld "show_answers" gesetzt.
show_answers = False
```

- [ ] **Step 4: `load_question_set` anpassen**

Ersetze in `resources.py` die Funktion `load_question_set` (Zeile 418-430) durch:

```python
def load_question_set(filename):
    """Lädt ein Fragenset aus JSON und befüllt den Modul-State.

    Akzeptiert sowohl alte (String-Fragen) als auch neue (Dict-Fragen)
    JSON-Formate. Bei alten Sets bleibt `answers` leer und
    `show_answers=False`.
    """
    global categories, values, questions, answers, show_answers, to_be_switched_int
    path = os.path.join(get_questionsets_dir(), filename)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    values = data["values"]
    categories = [cat["name"] for cat in data["categories"]]
    questions = []
    answers = []
    for cat in data["categories"]:
        q_list = []
        a_list = []
        for raw in cat.get("questions", []):
            q_text, a_text = _normalize_question(raw)
            q_list.append(q_text)
            a_list.append(a_text)
        questions.append(q_list)
        answers.append(a_list)
    show_answers = bool(data.get("show_answers", False))
    to_be_switched_int = len(categories) * len(values)
```

- [ ] **Step 5: Tests laufen — sollten passen**

```bash
python -m unittest test_jeopardy_extended.TestLoadQuestionSetWithAnswers -v
```

Erwartet: 3 Tests PASS.

- [ ] **Step 6: Bestehende Tests laufen — keine Regressionen**

```bash
python -m unittest test_jeopardy test_jeopardy_extended -v
```

Erwartet: alle bestehenden Tests grün.

- [ ] **Step 7: Commit**

```bash
git add resources.py test_jeopardy_extended.py
git commit -m "$(cat <<'EOF'
feat: r.answers + r.show_answers state, load supports dict questions

load_question_set normalisiert sowohl alte String- als auch neue
Dict-Fragen und füllt r.answers parallel zu r.questions. show_answers
kommt aus dem optionalen JSON-Feld (Default: False).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `save_question_set` schreibt Dict-Format

**Files:**
- Modify: `resources.py:433-441` (save_question_set)
- Test: `test_jeopardy_extended.py`

### Steps

- [ ] **Step 1: Test schreiben — Save-Roundtrip mit Antworten**

Am Ende von `test_jeopardy_extended.py`:

```python
class TestSaveQuestionSetRoundtrip(unittest.TestCase):
    """Save/Load Roundtrip: Antworten und show_answers bleiben erhalten."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._orig_data_path = r.data_path
        r.data_path = lambda relative_path="": (
            os.path.join(self.tmp, relative_path) if relative_path else self.tmp
        )

    def tearDown(self):
        r.data_path = self._orig_data_path
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_roundtrip_with_answers_and_toggle(self):
        cats = [
            {"name": "Geo", "questions": [
                {"q": "Hauptstadt von Frankreich?", "a": "Paris"},
                {"q": "Längster Fluss?", "a": ""},
            ]}
        ]
        r.save_question_set("rt.json", "Roundtrip", [100, 200], cats,
                            show_answers=True)
        r.load_question_set("rt.json")
        self.assertEqual(r.questions, [["Hauptstadt von Frankreich?",
                                         "Längster Fluss?"]])
        self.assertEqual(r.answers, [["Paris", ""]])
        self.assertTrue(r.show_answers)

    def test_roundtrip_legacy_strings_get_migrated_to_dicts(self):
        cats = [{"name": "C", "questions": ["Alte Frage 1", "Alte Frage 2"]}]
        r.save_question_set("legacy_rt.json", "Legacy", [100, 200], cats)
        # Auf Disk müssen es Dicts sein
        with open(os.path.join(r.get_questionsets_dir(), "legacy_rt.json")) as f:
            data = json.load(f)
        self.assertEqual(data["categories"][0]["questions"][0],
                         {"q": "Alte Frage 1", "a": ""})
        self.assertEqual(data.get("show_answers"), False)
```

- [ ] **Step 2: Tests laufen — sollten fehlschlagen**

```bash
python -m unittest test_jeopardy_extended.TestSaveQuestionSetRoundtrip -v
```

Erwartet: FAIL (Signatur kennt `show_answers` Parameter nicht oder Strings statt Dicts auf Disk).

- [ ] **Step 3: `save_question_set` erweitern**

Ersetze in `resources.py` die Funktion `save_question_set` (Zeile 433-441):

```python
def save_question_set(filename, name, values_list, cats, show_answers=False):
    """Speichert ein Fragenset als JSON-Datei.

    cats: Liste von {"name": str, "questions": [...]}.
        Fragen können Strings (Legacy) oder Dicts {"q":..., "a":...} sein —
        werden beim Speichern alle zu Dicts konvertiert.
    show_answers: bool — wird auf Top-Level des JSON gespeichert.
    """
    path = os.path.join(get_questionsets_dir(), filename)
    serialized_cats = []
    for cat in cats:
        new_qs = []
        for raw in cat.get("questions", []):
            q_text, a_text = _normalize_question(raw)
            new_qs.append(_serialize_question(q_text, a_text))
        serialized_cats.append({"name": cat["name"], "questions": new_qs})
    data = {
        "name": name,
        "values": values_list,
        "show_answers": bool(show_answers),
        "categories": serialized_cats,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: Tests laufen — sollten passen**

```bash
python -m unittest test_jeopardy_extended.TestSaveQuestionSetRoundtrip -v
```

Erwartet: 2 Tests PASS.

- [ ] **Step 5: Alle Tests laufen — keine Regressionen**

```bash
python -m unittest test_jeopardy test_jeopardy_extended -v
```

Erwartet: alle grün. Achtung: Falls `ensure_default_questionset()` oder `_new_set` in settings noch ohne `show_answers` aufrufen — Default-Wert `False` greift, kein Bruch.

- [ ] **Step 6: Commit**

```bash
git add resources.py test_jeopardy_extended.py
git commit -m "$(cat <<'EOF'
feat: save_question_set writes dict-format with show_answers flag

Migrationsweg: Beim ersten Speichern eines Legacy-Sets werden
String-Fragen automatisch zu {"q": str, "a": ""} Dicts. show_answers
ist optional (Default False) und wird auf Top-Level gespeichert.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Settings UI — Antwort-Feld pro Frage + Set-Toggle

**Files:**
- Modify: `settings.py:581-664` (Lade/Anzeige der Kategorie), `settings.py:741-769` (Save), `settings.py:424-563` (Tab-Aufbau)

### Steps

- [ ] **Step 1: Editor-State auf Dict-Form umstellen — `_load_set_into_editor`**

In `settings.py` die Methode `_load_set_into_editor` (Zeile 581) anpassen. Direkt **nach** dem `try/except`-Block, der `self.editor_data` befüllt (also nach `return` der except-Klausel — d.h. vor `self.editor_filename = filename`), folgenden Block einfügen:

```python
        # Migriere String-Fragen → Dict {"q":..., "a":""} im Editor-State
        for cat in self.editor_data.get("categories", []):
            migrated = []
            for raw in cat.get("questions", []):
                q_text, a_text = r._normalize_question(raw)
                migrated.append({"q": q_text, "a": a_text})
            cat["questions"] = migrated
        # show_answers default = False
        self.editor_data.setdefault("show_answers", False)
```

- [ ] **Step 2: Toggle-Variable im `__init__` ergänzen**

In `settings.py:116` `def __init__(self, root):`, im Block nach `self.theme_changed = False` (etwa Zeile 132) ergänzen:

```python
        # Tk-Variable für den "Antworten anzeigen"-Toggle pro Set
        self.show_answers_var = tk.BooleanVar(value=False)
```

- [ ] **Step 3: Toggle in den FRAGENSET-Tab einbauen**

In `settings.py` in `_build_fragenset_tab` direkt nach dem Name-Eingabefeld (nach Zeile 492, vor `ed_y += 50`) einfügen:

```python
        # Antworten-Toggle (Checkbutton) — eigene Zeile unter "Name"
        ed_y += 40
        chk = tk.Checkbutton(
            tab, text="Antworten nach Beantwortung anzeigen",
            variable=self.show_answers_var,
            font=(r.FONT, r.FONT_SMALL),
            fg=LABEL_GRAY, bg=CARD_BG,
            activeforeground=GOLD, activebackground=CARD_BG,
            selectcolor=DARK_BLUE,
        )
        chk.place(x=ed_x, y=ed_y - 4)
```

- [ ] **Step 4: Toggle-Wert beim Set-Wechsel synchronisieren**

In `_load_set_into_editor` am Ende (vor `self._set_status("")`) einfügen:

```python
        self.show_answers_var.set(bool(self.editor_data.get("show_answers", False)))
```

- [ ] **Step 5: `_show_category` — Antwort-Feld pro Zeile ergänzen**

Ersetze in `settings.py` den For-Loop in `_show_category` (Zeile 648-664) durch:

```python
        for i in range(len(vals)):
            val_text = str(vals[i]) if i < len(vals) else "?"
            row_y = i * 80  # mehr vertikaler Platz für Q + A pro Reihe
            tk.Label(
                self.q_frame, text=f"{val_text}:", font=(r.FONT, r.FONT_BODY, "bold"),
                fg=GOLD, bg=CARD_BG, width=6, anchor="e"
            ).place(x=0, y=row_y, height=36)

            # Frage-Feld
            q_entry = tk.Entry(
                self.q_frame, font=(r.FONT, 11),
                bg=DARK_BLUE, fg=GOLD, insertbackground=GOLD, relief="flat"
            )
            q_entry.place(x=75, y=row_y, width=frame_w - 85, height=32)
            _bind_focus_border(q_entry)

            # Antwort-Feld direkt darunter
            a_entry = tk.Entry(
                self.q_frame, font=(r.FONT, 11),
                bg=DARK_BLUE, fg=LABEL_GRAY, insertbackground=GOLD, relief="flat"
            )
            a_entry.place(x=75, y=row_y + 36, width=frame_w - 85, height=32)
            _bind_focus_border(a_entry)

            # Aktuellen Wert einsetzen — questions[i] ist jetzt Dict (nach Migration in _load_set_into_editor)
            q_dict = questions[i] if i < len(questions) else {"q": "", "a": ""}
            if isinstance(q_dict, dict):
                q_entry.insert(0, q_dict.get("q", ""))
                a_entry.insert(0, q_dict.get("a", ""))
            else:
                q_entry.insert(0, str(q_dict))

            self.question_entries.append((q_entry, a_entry))
```

**Wichtig:** `self.question_entries` enthält jetzt Tupel `(q_entry, a_entry)` statt einzelner Entries. Die nächsten Steps passen alle Leser an.

- [ ] **Step 6: `_save_current_questions` an Tupel-Form anpassen**

Ersetze in `settings.py` den Block in `_save_current_questions` (Zeile 666-687) durch:

```python
    def _save_current_questions(self):
        if not self.editor_data or self.current_cat_index < 0:
            return
        cats = self.editor_data.get("categories", [])
        if self.current_cat_index >= len(cats):
            return

        questions = []
        for q_entry, a_entry in self.question_entries:
            try:
                q_text = q_entry.get()
                a_text = a_entry.get()
            except tk.TclError:
                return
            questions.append({"q": q_text, "a": a_text})
        cats[self.current_cat_index]["questions"] = questions

        try:
            new_name = self.cat_name_entry.get()
        except tk.TclError:
            return
        if new_name:
            cats[self.current_cat_index]["name"] = new_name
```

- [ ] **Step 7: `_save_set` — Toggle mitspeichern**

Ersetze in `settings.py` den `r.save_question_set(...)`-Aufruf in `_save_set` (Zeile 759-762) durch:

```python
        r.save_question_set(
            self.editor_filename, name, vals,
            self.editor_data["categories"],
            show_answers=self.show_answers_var.get(),
        )
        # State im Editor-Dict aktualisieren, damit beim nächsten Tab-Wechsel kein Drift
        self.editor_data["show_answers"] = self.show_answers_var.get()
```

- [ ] **Step 8: `_start_game` — Toggle ebenfalls mitspeichern**

Im `_start_game` in `settings.py` den `r.save_question_set(...)`-Aufruf (Zeile 1065-1068) ersetzen durch:

```python
                r.save_question_set(
                    self.editor_filename, name, vals,
                    self.editor_data["categories"],
                    show_answers=self.show_answers_var.get(),
                )
```

- [ ] **Step 9: `_new_set` — neue Sets bekommen `show_answers=False`**

In `_new_set` (Zeile 779) den Aufruf:

```python
        r.save_question_set(filename, f"Neues Set {idx}", vals, cats)
```

bleibt unverändert (Default-Parameter `show_answers=False` greift).

- [ ] **Step 10: `_add_category` — Default-Frage als Dict statt String**

In `_add_category` (Zeile 706) den Block:

```python
        new_cat = {"name": "Neue Kategorie", "questions": [""] * len(vals)}
```

ersetzen durch:

```python
        new_cat = {"name": "Neue Kategorie",
                   "questions": [{"q": "", "a": ""} for _ in range(len(vals))]}
```

- [ ] **Step 11: `_save_set` — Padding mit Dicts statt Strings**

In `_save_set` (Zeile 753-757) den Block:

```python
        for cat in self.editor_data["categories"]:
            qs = cat.get("questions", [])
            while len(qs) < len(vals):
                qs.append("")
            cat["questions"] = qs[:len(vals)]
```

ersetzen durch:

```python
        for cat in self.editor_data["categories"]:
            qs = cat.get("questions", [])
            while len(qs) < len(vals):
                qs.append({"q": "", "a": ""})
            cat["questions"] = qs[:len(vals)]
```

Gleiche Stelle nochmal in `_start_game` (Zeile 1060-1064) anpassen:

```python
                for cat in self.editor_data["categories"]:
                    qs = cat.get("questions", [])
                    while len(qs) < len(vals):
                        qs.append({"q": "", "a": ""})
                    cat["questions"] = qs[:len(vals)]
```

- [ ] **Step 12: Manuell verifizieren — App starten und testen**

```bash
cd /Users/laurinokon/PycharmProjects/Jepoardy
python main.py
```

Verifizieren:
1. Settings öffnet sich, FRAGENSET-Tab zeigt Toggle "Antworten nach Beantwortung anzeigen"
2. Ein bestehendes Set auswählen → unter jeder Frage erscheint ein zweites Feld (graue Schrift)
3. Eine Antwort eintippen, Toggle aktivieren, "Speichern" klicken → Erfolgsmeldung
4. App neu starten → Toggle und Antwort sind persistent
5. JSON-Datei prüfen:

```bash
cat questionsets/ergo_default.json | head -30
```

Erwartet: `"show_answers": false/true` auf Top-Level, Fragen als Objekte `{"q": "...", "a": "..."}`.

- [ ] **Step 13: Bestehende Tests laufen lassen**

```bash
python -m unittest test_jeopardy test_jeopardy_extended -v
```

Erwartet: alle grün.

- [ ] **Step 14: Commit**

```bash
git add settings.py
git commit -m "$(cat <<'EOF'
feat: settings UI for answers — entry per question + per-set toggle

FRAGENSET-Tab erweitert: pro Frage gibt es jetzt ein zweites Eingabefeld
für die Antwort (optional). Pro Set kann via Checkbox eingestellt werden,
ob die Antworten im Spiel angezeigt werden sollen. Editor-State arbeitet
intern mit Dicts {"q":..., "a":...}, alte String-Sets werden beim Laden
migriert.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Game — State-Maschine + Antwort-Side-Flip + A-Taste

**Files:**
- Modify: `game.py:64-287` (LButton-Klasse + Helpers), `game.py:340-417` (create_grid)

### Steps

- [ ] **Step 1: LButton um State + Antwort-Text erweitern**

In `game.py` in `LButton.__init__` (Zeile 71-83) nach `self._answered = False` (Zeile 75) folgende Felder ergänzen:

```python
        # Antwort-Feature State:
        # "question" = Frage sichtbar
        # "answer_manual" = Antwort-Side via A-Taste (Punkte noch nicht vergeben)
        # "answer_post_score" = Antwort-Side nach Punktevergabe
        self._answer_state = "question"
        self._answer_text = ""  # wird in create_grid gesetzt
        self._cat_idx = 0       # für Lookup in r.answers
        self._row_idx = 0
        self._answered_post_close = False  # Re-entry-Schutz für State-3 Close
```

- [ ] **Step 2: `create_grid` — Antwort-Text und Indizes pro Button mitsetzen**

In `game.py` in `create_grid`, im Block der LButton-Erstellung (Zeile 396-414), direkt nach `tmp_b.wertigkeit = r.values[j - 1]` einfügen:

```python
                tmp_b._cat_idx = i
                tmp_b._row_idx = j - 1
                # Antwort aus r.answers (parallel zu r.questions)
                if i < len(r.answers) and (j - 1) < len(r.answers[i]):
                    tmp_b._answer_text = r.answers[i][j - 1]
                else:
                    tmp_b._answer_text = ""
```

- [ ] **Step 3: Helper für Antwort-Side-Flip implementieren**

In `game.py` in der `LButton`-Klasse nach der `flip()`-Methode (Zeile 218-265) eine neue Methode `flip_to_answer_side` einfügen:

```python
    def flip_to_answer_side(self, post_score):
        """Flippt von der Frage- zur Antwort-Seite (Gold-BG, dunkler Text).

        Animation: erst horizontal zur Mitte zusammendrücken (width → 0),
        dann zur Antwort-Seite umbauen und wieder auf Vollbild expandieren.

        post_score=True markiert, dass die Punktevergabe schon erfolgt ist
        (State 3) — beliebige Taste schließt die Karte dann zum Board.
        Sonst (State 2) führt eine beliebige andere Taste zurück zur Frage.
        """
        self._answer_state = "answer_post_score" if post_score else "answer_manual"
        # Audio in jedem Fall stoppen
        audio.stop_music()

        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        schnelligkeit = max(1, int(math.ceil(sw / 100)))

        def shrink():
            if self.winfo_width() > 3:
                cur_x = self.winfo_x()
                self.place(width=self.winfo_width() - schnelligkeit * 20,
                           x=cur_x + schnelligkeit * 10)
                self.master.after(10, shrink)
            else:
                # Antwort-Seite vorbereiten
                self.config(background=GOLD, foreground=DARK_BLUE)
                self.config(text=self._answer_text_display())
                self.place(x=sw / 2, y=sh / 2, width=0, height=0)
                self.master.after(10, expand)

        def expand():
            if self.winfo_width() < sw:
                cur_x = self.winfo_x()
                self.place(width=self.winfo_width() + schnelligkeit * 20,
                           x=cur_x - schnelligkeit * 10)
                if self.winfo_height() < sh:
                    self.place(height=self.winfo_height() + schnelligkeit * 20,
                               y=self.winfo_y() - schnelligkeit * 10)
                self.master.after(10, expand)

        shrink()

    def _answer_text_display(self):
        """Formatierter Antwort-Text mit Header und Footer-Hinweis."""
        header = "ANTWORT\n\n"
        footer = ""
        if self._answer_state == "answer_manual":
            footer = "\n\nBeliebige Taste: zurück"
        return header + self._answer_text + footer
```

- [ ] **Step 4: Helper für State-3 → Board (close_to_board) implementieren**

In `LButton`-Klasse direkt nach `flip_to_answer_side` einfügen:

```python
    def close_to_board(self, org, schnelligkeit):
        """Schrumpft die Antwort-Seite zurück zum Board (wie set_org)."""
        self.master.unbind("<KeyPress>")
        global _flip_in_progress
        # Foreground/Background auf Original-Look zurücksetzen, damit der
        # geschlossene Button als "answered" aussieht (Grau-Border bleibt).
        self.config(background=self._default_bg, foreground=GOLD)
        self.set_org(org, True, schnelligkeit)
        _flip_in_progress = False
```

- [ ] **Step 5: Helper für State 2 → State 1 (zurück zur Frage)**

In `LButton`-Klasse nach `close_to_board` einfügen:

```python
    def flip_back_to_question(self):
        """Flippt von der manuell aufgedeckten Antwort zurück zur Frage (State 2 → 1)."""
        self._answer_state = "question"
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        schnelligkeit = max(1, int(math.ceil(sw / 100)))

        def shrink():
            if self.winfo_width() > 3:
                cur_x = self.winfo_x()
                self.place(width=self.winfo_width() - schnelligkeit * 20,
                           x=cur_x + schnelligkeit * 10)
                self.master.after(10, shrink)
            else:
                self.config(background=DARK_BLUE, foreground=GOLD)
                self.visible_text()  # ursprünglicher Frage-Text
                self.place(x=sw / 2, y=sh / 2, width=0, height=0)
                self.master.after(10, expand)

        def expand():
            if self.winfo_width() < sw:
                cur_x = self.winfo_x()
                self.place(width=self.winfo_width() + schnelligkeit * 20,
                           x=cur_x - schnelligkeit * 10)
                if self.winfo_height() < sh:
                    self.place(height=self.winfo_height() + schnelligkeit * 20,
                               y=self.winfo_y() - schnelligkeit * 10)
                self.master.after(10, expand)

        shrink()
```

- [ ] **Step 6: `keyboard_input` State-Maschine umstellen**

Ersetze die gesamte `keyboard_input`-Methode (Zeile 125-171) durch:

```python
    def keyboard_input(self, event, org, schnelligkeit):
        """Verarbeitet Tastendrücke gemäß aktuellem _answer_state.

        State "question":
            SPACE       → Audio stop (Frage bleibt)
            'a'/'A'     → Wenn Antwort verfügbar + show_answers: Flip zur Antwort
            '1'..'N'    → Punkte + Audio stop. Wenn Antwort verfügbar +
                           show_answers: Flip zu State 3 statt direkt zu Board.
            'N+1'       → Niemand. Genauso State 3 wenn Antwort verfügbar.

        State "answer_manual":
            '1'..'N'    → Punkte. Karte bleibt auf Antwort-Seite (State 3),
                           jede weitere Taste schließt zum Board.
            'N+1'       → Niemand → State 3.
            sonstige    → Zurück zur Frage (State 1).

        State "answer_post_score":
            beliebige Taste → close_to_board.
        """
        global _flip_in_progress

        num_teams = len(r.teams)
        team_keys = {str(i + 1) for i in range(num_teams)}
        nobody_key = str(num_teams + 1)
        has_answer = bool(self._answer_text) and bool(getattr(r, "show_answers", False))

        # --- State: answer_post_score ---
        if self._answer_state == "answer_post_score":
            if self._answered_post_close:
                return
            self._answered_post_close = True
            self.close_to_board(org, schnelligkeit)
            _update_team_scores()
            return

        # --- State: answer_manual ---
        if self._answer_state == "answer_manual":
            # Punkte-Tasten: Punkte vergeben + State 3
            if event.char in team_keys:
                idx = int(event.char) - 1
                self._answered = True
                r.team_points[idx] += self.wertigkeit
                self.config(foreground=r.teams[idx]["color"])
                # Bleibt auf Antwort-Seite, aber Footer-Hinweis weg
                self._answer_state = "answer_post_score"
                self.config(text=self._answer_text_display())
                _update_team_scores()
                return
            if event.char == nobody_key:
                self._answered = True
                self._answer_state = "answer_post_score"
                self.config(text=self._answer_text_display())
                return
            # Sonst: zurück zur Frage
            self.flip_back_to_question()
            return

        # --- State: question (default) ---
        if self._answered:
            return

        if event.keysym == "space":
            audio.stop_music()
            return

        # 'A' = Antwort manuell aufdecken
        if event.keysym in ("a", "A") and has_answer:
            self.flip_to_answer_side(post_score=False)
            return

        # Team-Tasten
        if event.char in team_keys:
            idx = int(event.char) - 1
            self._answered = True
            audio.stop_music()
            self.config(foreground=r.teams[idx]["color"])
            self.update()
            r.team_points[idx] += self.wertigkeit

            if has_answer:
                # State 3: Antwort zeigen, beliebige Taste schließt zum Board
                self.flip_to_answer_side(post_score=True)
                _update_team_scores()
            else:
                self.master.unbind("<KeyPress>")
                self.set_org(org, True, schnelligkeit)
                _flip_in_progress = False
                _update_team_scores()
            return

        # Niemand-Taste
        if event.char == nobody_key:
            self._answered = True
            audio.stop_music()
            self.config(foreground="black")
            self.update()
            if has_answer:
                self.flip_to_answer_side(post_score=True)
            else:
                self.master.unbind("<KeyPress>")
                self.set_org(org, True, schnelligkeit)
                _flip_in_progress = False
            return
```

- [ ] **Step 7: Manuell verifizieren — Spielablauf**

```bash
cd /Users/laurinokon/PycharmProjects/Jepoardy
python main.py
```

Test-Cases manuell durchgehen:

1. **Toggle aus, keine Antwort hinterlegt:** Spiel verhält sich exakt wie vorher. Frage öffnet, Punkte-Taste → zurück zum Board. (Regression-Check)
2. **Toggle an, Antwort vorhanden:** Frage öffnet → Punkte-Taste drücken → Karte flippt zur Gold-Antwort-Seite (zeigt "ANTWORT" + Antwort-Text) → beliebige Taste schließt zum Board.
3. **Toggle an, `A`-Taste während Frage:** Karte flippt zur Antwort-Seite (Gold) mit Footer "Beliebige Taste: zurück" → Audio ist gestoppt → beliebige nicht-Punkte-Taste → zurück zur Frage.
4. **Toggle an, `A` dann Punkte-Taste:** Karte zeigt Antwort, dann Punkte-Taste → Footer-Hinweis verschwindet → beliebige Taste → zurück zum Board, Punkte sichtbar in Team-Bar.
5. **Toggle an, Antwort leer:** `A`-Taste tut nichts. Punkte-Vergabe schließt die Karte direkt zum Board (kein Auto-Flip ohne Inhalt).

- [ ] **Step 8: Bestehende Tests laufen lassen**

```bash
python -m unittest test_jeopardy test_jeopardy_extended -v
```

Erwartet: alle grün (game.py wird nicht in Tests abgedeckt, aber resources/settings müssen weiter funktionieren).

- [ ] **Step 9: Commit**

```bash
git add game.py
git commit -m "$(cat <<'EOF'
feat: game state machine for answer flip + A key

LButton State-Maschine: question / answer_manual / answer_post_score.
- 'A' im Frage-State flippt zur Gold-Antwort-Seite (Audio stop).
- Punkte-Taste mit Antwort + Toggle aktiv: Auto-Flip zur Antwort,
  beliebige Taste schließt zum Board.
- Manuelle Antwort-Ansicht: nicht-Punkte-Taste flippt zurück zur Frage.
- Wenn keine Antwort hinterlegt oder Toggle aus: altes Verhalten.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: CLAUDE.md Doku-Update

**Files:**
- Modify: `CLAUDE.md` (mehrere Stellen)

### Steps

- [ ] **Step 1: Datenmodell-Dokumentation aktualisieren**

In `CLAUDE.md` den Abschnitt "**Fragensets:**" (mit dem JSON-Beispiel) finden und ersetzen durch:

```markdown
**Fragensets:** JSON-Dateien in `questionsets/`. Format:
\`\`\`json
{
  "name": "...",
  "values": [100,200,...],
  "show_answers": false,
  "categories": [
    {
      "name": "...",
      "questions": [
        {"q": "Frage?", "a": "Antwort"},
        {"q": "Frage ohne Antwort?", "a": ""},
        "Legacy-String wird beim ersten Speichern migriert"
      ]
    }
  ]
}
\`\`\`

`show_answers` (optional, Default `false`) steuert, ob im Spiel die Antwort
nach Beantwortung gezeigt wird. Antworten sind pro Frage optional.
```

(Achtung: Backslashes vor den Code-Block-Markern beim Eingeben weglassen — sie sind nur für die Markdown-Quote in dieser Anleitung.)

- [ ] **Step 2: Tastenbelegung um `A` ergänzen**

Im Abschnitt "Tastenbelegung" (unter "Konventionen") die Zeile:

```
- Tastenbelegung: `1`-`N` für Teams, `N+1` für Niemand (dynamisch), `Space` stoppt Frage-Timer-Audio
```

ersetzen durch:

```
- Tastenbelegung: `1`-`N` für Teams, `N+1` für Niemand (dynamisch), `Space` stoppt Frage-Timer-Audio, `A` deckt Antwort auf (wenn `show_answers=true` und Antwort hinterlegt)
```

- [ ] **Step 3: Neuen Abschnitt "Antworten-Feature" unter "Architektur" ergänzen**

Direkt nach dem Abschnitt "Audio-System" (vor "Intro-Sequenz") einen neuen Abschnitt einfügen:

```markdown
### Antworten-Feature

Optionales Anzeigen der Antwort nach Beantwortung einer Frage. Aktiv nur
wenn `show_answers=true` im Set UND die Frage ein nicht-leeres `a`-Feld hat.

**State-Maschine pro `LButton`:**
| State | Beschreibung |
|---|---|
| `question` | Frage sichtbar (Standard) |
| `answer_manual` | Spielleiter hat `A` gedrückt — Antwort sichtbar, Punkte noch offen |
| `answer_post_score` | Punkte vergeben, Antwort wird gezeigt bis beliebige Taste die Karte schließt |

**Tasten:**
- `A` (in `question`): Audio stop, Flip zur Gold-Antwort-Seite
- `1`-`N` / `N+1` (in `question`): Punkte vergeben → bei aktivem Toggle Auto-Flip zu `answer_post_score`, sonst direkt zu Board
- `1`-`N` / `N+1` (in `answer_manual`): Punkte vergeben → State `answer_post_score`
- Sonstige Taste (in `answer_manual`): zurück zur Frage
- Beliebige Taste (in `answer_post_score`): Karte zum Board

**Antwort-Seite Visuals:** `r.GOLD` als Background, `r.DARK_BLUE` als Foreground.
Header `ANTWORT`, darunter Antwort-Text. In `answer_manual` zusätzlicher Footer
`Beliebige Taste: zurück`.

**Datenmodell:** `r.questions[i][j]` ist String (Frage), `r.answers[i][j]` ist String
(Antwort, ggf. leer). `r.show_answers` ist bool. Beim Laden eines Sets wird ein
String-Format (`"Frage"`) zu `{"q": "Frage", "a": ""}` normalisiert.
```

- [ ] **Step 4: "Bekannte Probleme / TODOs" um Editor-Layout-Punkt erweitern**

Im Abschnitt "Bekannte Probleme / TODOs" einen neuen nummerierten Punkt am Ende ergänzen:

```markdown
9. **FRAGENSET-Editor wird durch Antwort-Felder doppelt so hoch** — pro Frage gibt es jetzt 2 Eingabefelder (Frage + Antwort) übereinander. Bei vielen Fragen pro Kategorie könnte das Layout unhandlich werden. Mögliche Lösung: Antwort-Feld collapsible (per `+`-Button) oder nur sichtbar wenn der Set-Toggle aktiv ist. Aktuell YAGNI bis es konkret stört.
```

- [ ] **Step 5: Verifizieren — Markdown-Render**

```bash
cat CLAUDE.md | head -100
```

Visuell prüfen, dass die Tabellen und Code-Blöcke korrekt aussehen.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs: CLAUDE.md update for answers feature

Datenmodell, State-Maschine, Tastenbelegung und das offene
Editor-Layout-Problem dokumentiert.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: End-to-End Manual Verification

**Files:** keine — nur App-Test

### Steps

- [ ] **Step 1: Komplett-Durchlauf mit aktiviertem Feature**

```bash
python main.py
```

Vorgehen:
1. Settings → FRAGENSET-Tab → ein Set auswählen
2. Toggle "Antworten anzeigen" aktivieren
3. In ≥ 2 Fragen Antworten eintragen, in einer leer lassen
4. Speichern
5. → Intro → Spiel
6. Frage mit Antwort öffnen → `A` drücken → Antwort sichtbar (Gold) mit "Beliebige Taste: zurück"
7. Beliebige Taste (z. B. `q`) → zurück zur Frage
8. Punkte-Taste (`1`) → Antwort sichtbar ohne Footer → beliebige Taste → Board, Punkte +
9. Frage ohne Antwort öffnen → `A` ignoriert → Punkte-Taste schließt direkt zum Board (kein Antwort-Flip)
10. Frage mit Antwort öffnen → `Niemand`-Taste → Antwort sichtbar → beliebige Taste → Board

- [ ] **Step 2: Komplett-Durchlauf mit deaktiviertem Feature (Regression)**

Settings → Toggle aus → Speichern → Spiel starten.

Verifizieren:
- `A`-Taste tut nichts während offener Frage
- Punkte-Vergabe schließt direkt zum Board (wie früher)
- Audio-Verhalten unverändert

- [ ] **Step 3: Legacy-Set laden (vor dem Feature gespeichert)**

Falls Backup eines alten JSON ohne `show_answers`-Feld vorhanden, in `questionsets/` ablegen, App starten, Set laden. Erwartet: lädt sauber, Toggle ist aus, Antworten leer.

- [ ] **Step 4: Theme-Wechsel-Regression**

Settings → DESIGN → anderes Theme → Settings baut neu auf → FRAGENSET-Tab → Toggle und Antwort-Felder funktionieren weiter wie vorher.

- [ ] **Step 5: Tests gesamt**

```bash
python -m unittest test_jeopardy test_jeopardy_extended -v
```

Erwartet: alle grün.

- [ ] **Step 6: Final Commit (falls Änderungen aus Manual-Test)**

Falls beim manuellen Test Bugs gefunden + gefixt werden, jeweils einzeln committen mit `fix:`-Prefix. Sonst diesen Step überspringen.

---

## Definition of Done

- [ ] Alle Unit-Tests grün
- [ ] Manuelle Spielablauf-Verifikation durchlaufen (Task 7 Steps 1-4)
- [ ] CLAUDE.md aktualisiert
- [ ] Backward-Compat verifiziert: alte String-Sets laden ohne Fehler
- [ ] Audio stoppt sowohl bei manuellem `A` als auch bei Punktevergabe
- [ ] Theme-Wechsel funktioniert weiterhin
