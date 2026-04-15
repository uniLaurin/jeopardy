"""
Zentrales Ressourcen- und Konfigurations-Modul.

Enthält:
- Design System (Farben, Fonts, Spacing) — wird von ALLEN GUI-Modulen importiert
- Shared State (teams, team_points, categories, questions, values, ...)
- Pfad-Helpers für Read-Only (bundled) und Writable (Daten) Dateien
- Laden/Speichern/Verwalten von Fragensets als JSON

Wichtig: Die Variablen `teams`, `team_points`, `categories`, `values`,
`questions` und `to_be_switched_int` sind Modul-Level State. Alle Module
lesen und schreiben direkt über `r.teams`, `r.team_points` etc.
"""

import os
import sys
import json
import tkinter as tk


def resource_path(relative_path):
    """Gibt den absoluten Pfad zu einer gebündelten Read-Only Ressource zurück.

    Im Frozen-Modus (PyInstaller) wird das temporäre Extraktionsverzeichnis
    `sys._MEIPASS` genutzt. Im Dev-Modus das Verzeichnis dieser Datei.
    """
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def data_path(relative_path=""):
    """Gibt den Pfad zu einem beschreibbaren Datenverzeichnis zurück.

    Im Frozen-Modus: neben der Executable (damit der User dort Fragensets
    speichern kann). Im Dev-Modus: neben dieser Datei.
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


# ---------------------------------------------------------------------------
# Font-Konfiguration (mit Fallback für Systeme ohne "Arial Rounded MT Bold")
# ---------------------------------------------------------------------------

FONT = "Arial Rounded MT Bold"  # Default — wird bei Bedarf von detect_font() ersetzt

# ---------------------------------------------------------------------------
# Design System — einheitliche Farben, Spacing, Typografie
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Theme-Paletten — jedes Theme liefert die gleichen Slots (Primär/Akzent/...)
# ---------------------------------------------------------------------------
#
# Die Namen BLUE/GOLD sind historisch (Classic Jeopardy) und werden als
# "Primär" / "Akzent" interpretiert — andere Themes dürfen dort auch
# Grün, Cyan, etc. einsetzen.

THEMES = {
    "classic": {
        "label": "Classic Jeopardy",
        "description": "Das klassische Blau & Gold",
        "BLUE":         "#060CE9",
        "GOLD":         "#DBAB51",
        "DARK_BLUE":    "#0A10A0",
        "CARD_BG":      "#0A15B8",
        "BORDER_BLUE":  "#000A80",
        "SHADOW":       "#1A1A2E",
        "HOVER_GOLD":   "#E8C76B",
        "ACTIVE_GOLD":  "#C89840",
        "LABEL_GRAY":   "#C0C0D5",
        "HINT_GRAY":    "#9999CC",
    },
    "modern_dark": {
        "label": "Modern Dark",
        "description": "Tiefes Navy mit Neon-Cyan",
        "BLUE":         "#0A0A1A",
        "GOLD":         "#00D4FF",
        "DARK_BLUE":    "#0F0F2E",
        "CARD_BG":      "#121238",
        "BORDER_BLUE":  "#1A1A4A",
        "SHADOW":       "#050510",
        "HOVER_GOLD":   "#55E6FF",
        "ACTIVE_GOLD":  "#00A3C4",
        "LABEL_GRAY":   "#8888AA",
        "HINT_GRAY":    "#505080",
    },
    "minimal_clean": {
        "label": "Minimal Clean",
        "description": "Dunkelblau mit warmem Amber",
        "BLUE":         "#1A1A2E",
        "GOLD":         "#FFAA00",
        "DARK_BLUE":    "#22223A",
        "CARD_BG":      "#1E1E32",
        "BORDER_BLUE":  "#404050",
        "SHADOW":       "#10101A",
        "HOVER_GOLD":   "#FFC44D",
        "ACTIVE_GOLD":  "#CC8800",
        "LABEL_GRAY":   "#9090A0",
        "HINT_GRAY":    "#606070",
    },
    "emerald": {
        "label": "Emerald Luxury",
        "description": "Anthrazit mit Smaragd-Akzent",
        "BLUE":         "#0D1B14",
        "GOLD":         "#10B981",
        "DARK_BLUE":    "#142820",
        "CARD_BG":      "#18322A",
        "BORDER_BLUE":  "#0A140F",
        "SHADOW":       "#050A07",
        "HOVER_GOLD":   "#34D399",
        "ACTIVE_GOLD":  "#059669",
        "LABEL_GRAY":   "#9CA3A8",
        "HINT_GRAY":    "#6B7280",
    },
}

# Farb-Slots — werden bei Import mit Classic befüllt und bei apply_theme()
# überschrieben. Alle GUI-Module lesen diese über `r.BLUE` etc.
BLUE = THEMES["classic"]["BLUE"]
GOLD = THEMES["classic"]["GOLD"]
DARK_BLUE = THEMES["classic"]["DARK_BLUE"]
CARD_BG = THEMES["classic"]["CARD_BG"]
BORDER_BLUE = THEMES["classic"]["BORDER_BLUE"]
SHADOW = THEMES["classic"]["SHADOW"]
HOVER_GOLD = THEMES["classic"]["HOVER_GOLD"]
ACTIVE_GOLD = THEMES["classic"]["ACTIVE_GOLD"]
LABEL_GRAY = THEMES["classic"]["LABEL_GRAY"]
HINT_GRAY = THEMES["classic"]["HINT_GRAY"]
ERROR_RED = "#FF6666"       # themeübergreifend konstant
SUCCESS_GREEN = "#66FF66"   # themeübergreifend konstant

current_theme_name = "classic"


def apply_theme(name):
    """Setzt die aktuelle Farbpalette. Updatet Modul-Konstanten BLUE, GOLD, …"""
    global BLUE, GOLD, DARK_BLUE, CARD_BG, BORDER_BLUE, SHADOW
    global HOVER_GOLD, ACTIVE_GOLD, LABEL_GRAY, HINT_GRAY, current_theme_name
    if name not in THEMES:
        name = "classic"
    t = THEMES[name]
    BLUE = t["BLUE"]
    GOLD = t["GOLD"]
    DARK_BLUE = t["DARK_BLUE"]
    CARD_BG = t["CARD_BG"]
    BORDER_BLUE = t["BORDER_BLUE"]
    SHADOW = t["SHADOW"]
    HOVER_GOLD = t["HOVER_GOLD"]
    ACTIVE_GOLD = t["ACTIVE_GOLD"]
    LABEL_GRAY = t["LABEL_GRAY"]
    HINT_GRAY = t["HINT_GRAY"]
    current_theme_name = name


def _theme_config_path():
    return os.path.join(data_path(), "theme.json")


def load_current_theme():
    """Liest den gespeicherten Theme-Namen. Default: 'classic'."""
    try:
        with open(_theme_config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        name = data.get("theme", "classic")
        return name if name in THEMES else "classic"
    except (OSError, ValueError):
        return "classic"


def save_current_theme(name):
    """Persistiert den Theme-Namen in theme.json."""
    if name not in THEMES:
        return
    try:
        with open(_theme_config_path(), "w", encoding="utf-8") as f:
            json.dump({"theme": name}, f)
    except OSError:
        pass

# Typografie-Größen (in Punkten)
FONT_TITLE = 48             # Hauptüberschriften (z.B. "JEOPARDY! SETUP")
FONT_SECTION = 24           # Sektions-Header (z.B. "TEAMS", "FRAGENSET")
FONT_BODY = 16              # Fließtext, Labels, Team-Namen
FONT_SMALL = 13             # Kleine Hinweise, Placeholder
FONT_BUTTON = 14            # Button-Beschriftungen

# Spacing (Abstände in Pixel)
SPACING_MAJOR = 40          # Zwischen Haupt-Sektionen
SPACING_SECTION = 20        # Zwischen Sub-Sektionen
SPACING_ELEMENT = 10        # Zwischen einzelnen Elementen


def detect_font():
    """Erkennt den besten verfügbaren Font und setzt `FONT` entsprechend.

    Muss AUFGERUFEN werden nachdem das erste `tk.Tk()` erstellt wurde,
    weil `tk.font.families()` einen aktiven Tcl-Interpreter braucht.

    Fallback-Reihenfolge: Arial Rounded MT Bold → Arial → Helvetica → Arial
    """
    global FONT
    try:
        import tkinter as tk
        import tkinter.font
        available = set(tk.font.families())
        for candidate in ["Arial Rounded MT Bold", "Arial", "Helvetica"]:
            if candidate in available:
                FONT = candidate
                return
    except Exception:
        pass
    FONT = "Arial"


# ---------------------------------------------------------------------------
# FlatButton — plattform-unabhängiger Button
# ---------------------------------------------------------------------------

class FlatButton(tk.Frame):
    """Button aus Frame + Label, der auf Mac und Windows identisch aussieht.

    Hintergrund: tk.Button ignoriert auf macOS die `bg`-Option weil Tk dort
    native Cocoa-Buttons verwendet. Diese Klasse umgeht das Problem, indem
    sie einen Frame als Klickfläche und ein Label als Beschriftung verwendet
    und Hover-/Press-Effekte selbst über Event-Bindings steuert.

    Für Tab-Navigation oder andere "aktive" Zustände kann der Button via
    `set_state(bg, fg, locked=True)` gesperrt werden — Hover-Events werden
    dann ignoriert bis der Lock wieder aufgehoben wird.
    """

    def __init__(self, parent, text, command, *, bg=None, fg=None,
                 hover_bg=None, hover_fg=None, active_bg=None, font=None):
        bg = bg if bg is not None else GOLD
        fg = fg if fg is not None else BLUE
        hover_bg = hover_bg if hover_bg is not None else HOVER_GOLD
        hover_fg = hover_fg if hover_fg is not None else fg
        active_bg = active_bg if active_bg is not None else ACTIVE_GOLD
        if font is None:
            font = (FONT, FONT_BUTTON, "bold")

        super().__init__(parent, bg=bg, highlightthickness=0, bd=0)
        self._normal_bg = bg
        self._normal_fg = fg
        self._hover_bg = hover_bg
        self._hover_fg = hover_fg
        self._active_bg = active_bg
        self._command = command
        self._locked = False

        self._label = tk.Label(
            self, text=text, font=font, bg=bg, fg=fg, cursor="hand2"
        )
        self._label.place(relx=0.5, rely=0.5, anchor="center")

        for w in (self, self._label):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_press)
            w.bind("<ButtonRelease-1>", self._on_release)

    def _apply(self, bg, fg):
        self.config(bg=bg)
        self._label.config(bg=bg, fg=fg)

    def _on_enter(self, _e):
        if self._locked:
            return
        self._apply(self._hover_bg, self._hover_fg)

    def _on_leave(self, _e):
        if self._locked:
            return
        self._apply(self._normal_bg, self._normal_fg)

    def _on_press(self, _e):
        if self._locked:
            return
        self._apply(self._active_bg, self._hover_fg)

    def _on_release(self, _e):
        if self._locked:
            return
        self._apply(self._hover_bg, self._hover_fg)
        if self._command:
            self._command()

    def set_state(self, bg, fg, locked=False):
        """Setzt Basis-Farben und Lock-Status (z.B. für aktiven Tab-Button)."""
        self._normal_bg = bg
        self._normal_fg = fg
        self._locked = locked
        self._apply(bg, fg)

    def set_text(self, text):
        self._label.config(text=text)


# ---------------------------------------------------------------------------
# Team-Konfiguration
# ---------------------------------------------------------------------------

# Verfügbare Teamfarben (im Settings Color-Picker anwählbar)
TEAM_PALETTE = ["green", "red", "purple", "orange", "#2196F3", "#FF69B4"]

# Default-Teams (werden in settings.py überschrieben)
teams = [
    {"name": "Team 1", "color": "green"},
    {"name": "Team 2", "color": "red"},
    {"name": "Team 3", "color": "purple"},
]

# Punktestand pro Team — wird in reset_game_state() auf [0, 0, ...] gesetzt
team_points = [0, 0, 0]

# ---------------------------------------------------------------------------
# Game Data (wird von load_question_set() aus einer JSON-Datei befüllt)
# ---------------------------------------------------------------------------

# Fallback-Kategorien falls kein Set geladen wird
categories = [
    "World \n of \n Ergo", "Indian", "German",
    "Products \n of \n Vorsorge", "Useless \n Knowledge",
    "Alpha", "IT"
]

# Werte pro Reihe (Punkte für leichte bis schwere Fragen)
values = [100, 200, 400, 600, 1000]

# Zähler für noch nicht beantwortete Fragen — bei 0 endet das Spiel automatisch
to_be_switched_int = len(categories) * len(values)

# Fallback-Fragen — dieselbe Struktur wie in JSON-Fragensets:
# questions[kategorie_idx][frage_idx]
questions = [
    ["Wieviele Zeichen muss ein ERGO Passwort mindestens haben? ! What is the minimum number of characters a ERGO password must have?",
     "Wofür steht ET&S? ! What do ET&S stand for?",
     "Was konnte man heute in der Kantine bei G&G essen? ! What was available today as a meal in the canteen at G&G?",
     "Wieviele Meter hat der ERGO Turm? ! How many meters high is the ERGO Tower?",
     "Was ist das in Wikipedia angegebene Gründungsjahr der ERGO? ! What is the year of ERGO's foundation according to Wikipedia?"],

    ["Wie heißt der längste Fluss Indiens? ! What is the name of the longest river in India?",
     "Nenne ein indisches Fest ! Name an Indian festival",
     "Wann wurde das Taj Mahal gebaut? ! When was the Taj Mahal built?",
     "Nenne ein deutsches Wort, welches genauso in Hindi verwendet wird ! Name a German word that is used exactly the same way in Hindi",
     "Was ist ein Bindi? ! What is a bindi?"],

    ["Wie heißt der längste Fluß Deutschlands? ! What is the name of the longest river in Germany?",
     "Nenne das größte Volksfest der Welt in München? ! Name the largest folk festival in the world, which takes place in Munich",
     "Wann wurde das Brandenburger Tor gebaut? ! When was the Brandenburg Gate built?",
     "Nenne ein Hindi-Wort, welches genauso in Deutsch verwendet wird? ! Name a Hindi word that is used in the same way in German.",
     "Was bedeuten die roten Bommeln an dem Bollenhut im Schwarzwald? ! What do the red bobbles on the Bollenhut hat mean in the Black Forest?"],

    ["Wie heißt der vollständige Marketingname von ERD? ! What is the full marketing name of ERD?",
     "Welches Produkt hat die längsten Versicherungsbedingungen? ! Which product has the longest insurance terms and conditions?",
     "Welches Produkt wurde in 2024 am wenigsten verkauft? ! Which product was sold the least in 2024?",
     "Wieviel kostet aktuell ein Ersatzversicherungsschein? ! How much does a replacement insurance certificate currently cost?",
     "Was regelt Teil E in den Versicherungsbedingungen? ! What does Part E of the insurance terms and conditions regulate?"],

    ["Nenne eine Planning-Poker Zahl größer 10? ! Name a Planning Poker number greater than 10.",
     'Wieviele Ziffern enthält ein HP-Alm Ticket nach dem Wort "ERGO"? ! How many digits does an HP-Alm ticket contain after the word "ERGO"?',
     "Welche Sprintnummer hat der Weihnachtssprint in diesem Jahr? ! Which sprint number does the Christmas sprint have this year?",
     "Welches Getränk gibt der Kaffeeautomat in der Kaffeeküche bei der Auswahltaste unten rechts? ! Which drink does the coffee machine in the kitchenette dispense when the selection button is pressed down on the bottom right?",
     "Wieviele Büros befinden sich auf dem NPL Flur im Bauteil 11 in der ersten Etage? ! How many offices are there on the NPL corridor in section 11 on the first floor?"],

    ["Wieviele Mitglieder hat das Team aktuell? ! How many members does the team currently have?",
     "Aus welchen Teams ist das aktuelle Team Alpha entstanden? ! Which teams did the current Team Alpha emerge from?",
     "Wieviele Features wird Team Alpha im Release 25.10 nach Produktion bringen? ! How many features will Team Alpha bring to production in Release 25.10?",
     "Wieviele Scrum Master hatte Alpha seit Gründung des Teams? ! How many Scrum Masters has Alpha had since the team was formed?",
     "Wie heißt die Alpha Gruppen Email exakt? ! What is the exact name of the Alpha group email?"],

    ["Wie heißt das September Release in 2030 nach der aktuellen Konvention für Relasenamen? ! What is the September 2030 release named according to the current release naming convention?",
     "Wofür steht die Abkürzung SOM/BOM? ! What do the abbreviations SOM/BOM stand for?",
     'Welche Schritt ID hat der GeVo "Tod" in der Life Factory? ! Which step ID does the GeVo "Tod" have in the Life Factory?',
     "Worin unterscheiden sich die 7 a und 7 b Methoden? ! What is the difference between the 7 a and 7 b methods?",
     "Welches LF Standardprodukt verwenden wir für das Invita Garantie Produkt? ! Which LF standard product do we use for the Invita Garantie product?"]
]


# ---------------------------------------------------------------------------
# Fragenset-Verwaltung (CRUD auf JSON-Dateien in questionsets/)
# ---------------------------------------------------------------------------

def get_questionsets_dir():
    """Gibt den Pfad zum questionsets/ Verzeichnis zurück und erstellt es falls nötig."""
    d = data_path("questionsets")
    os.makedirs(d, exist_ok=True)
    return d


def list_question_sets():
    """Gibt eine Liste aller verfügbaren Fragensets als (filename, display_name) Tupel zurück.

    Liest den `name` aus jeder JSON-Datei. Bei korrupten oder unlesbaren
    Dateien wird der Dateiname selbst als Display-Name verwendet.
    """
    d = get_questionsets_dir()
    result = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            try:
                with open(os.path.join(d, f), "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                result.append((f, data.get("name", f)))
            except (json.JSONDecodeError, KeyError, OSError):
                # Korrupte Datei — trotzdem in der Liste zeigen (damit löschbar)
                result.append((f, f))
    return result


def load_question_set(filename):
    """Lädt ein Fragenset aus JSON und befüllt den Modul-State (categories, values, questions).

    Wird von settings.py vor dem Spielstart aufgerufen.
    """
    global categories, values, questions, to_be_switched_int
    path = os.path.join(get_questionsets_dir(), filename)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    values = data["values"]
    categories = [cat["name"] for cat in data["categories"]]
    questions = [cat["questions"] for cat in data["categories"]]
    to_be_switched_int = len(categories) * len(values)


def save_question_set(filename, name, values_list, cats):
    """Speichert ein Fragenset als JSON-Datei.

    cats: Liste von {"name": str, "questions": [str, ...]}
    """
    path = os.path.join(get_questionsets_dir(), filename)
    data = {"name": name, "values": values_list, "categories": cats}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def delete_question_set(filename):
    """Löscht ein Fragenset. Kein Fehler wenn die Datei nicht existiert."""
    path = os.path.join(get_questionsets_dir(), filename)
    if os.path.exists(path):
        os.remove(path)


def ensure_default_questionset():
    """Stellt sicher, dass mindestens das Default-Fragenset (ergo_default.json) existiert.

    Strategie:
    1. Existiert die Datei bereits im Datenverzeichnis → nichts tun
    2. Existiert eine gebündelte Version (PyInstaller) → ins Datenverzeichnis kopieren
    3. Ansonsten: aus den Fallback-Daten am Anfang der Datei neu erstellen
    """
    d = get_questionsets_dir()
    default_path = os.path.join(d, "ergo_default.json")
    if os.path.exists(default_path):
        return
    # Prüfen ob eine gebündelte Version existiert (bei PyInstaller-Build)
    bundled = resource_path(os.path.join("questionsets", "ergo_default.json"))
    if os.path.exists(bundled) and bundled != default_path:
        import shutil
        shutil.copy2(bundled, default_path)
        return
    # Aus den hardcodierten Defaults neu generieren
    cats = []
    for i, cat_name in enumerate(categories):
        cats.append({"name": cat_name, "questions": questions[i]})
    save_question_set("ergo_default.json", "ERGO Team Event 2025", values, cats)


def reset_game_state():
    """Setzt team_points und to_be_switched_int vor jedem Spielstart zurück."""
    global team_points, to_be_switched_int
    team_points = [0] * len(teams)
    to_be_switched_int = len(categories) * len(values)
