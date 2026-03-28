import os
import sys
import json


def resource_path(relative_path):
    """Get absolute path to bundled resource (read-only in frozen mode)."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def data_path(relative_path=""):
    """Get absolute path to writable data directory (next to executable)."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


# ---------------------------------------------------------------------------
# Team configuration
# ---------------------------------------------------------------------------

TEAM_PALETTE = ["green", "red", "purple", "orange", "#2196F3", "#FF69B4"]

teams = [
    {"name": "Team 1", "color": "green"},
    {"name": "Team 2", "color": "red"},
    {"name": "Team 3", "color": "purple"},
]

team_points = [0, 0, 0]

# ---------------------------------------------------------------------------
# Game data (populated by load_question_set or used as defaults)
# ---------------------------------------------------------------------------

categories = [
    "World \n of \n Ergo", "Indian", "German",
    "Products \n of \n Vorsorge", "Useless \n Knowledge",
    "Alpha", "IT"
]

values = [100, 200, 400, 600, 1000]

to_be_switched_int = len(categories) * len(values)

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
# Question set management
# ---------------------------------------------------------------------------

def get_questionsets_dir():
    """Return path to questionsets/ directory, creating it if needed."""
    d = data_path("questionsets")
    os.makedirs(d, exist_ok=True)
    return d


def list_question_sets():
    """Return list of (filename, display_name) tuples."""
    d = get_questionsets_dir()
    result = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            try:
                with open(os.path.join(d, f), "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                result.append((f, data.get("name", f)))
            except (json.JSONDecodeError, KeyError, OSError):
                result.append((f, f))
    return result


def load_question_set(filename):
    """Load a question set JSON and populate module-level state."""
    global categories, values, questions, to_be_switched_int
    path = os.path.join(get_questionsets_dir(), filename)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    values = data["values"]
    categories = [cat["name"] for cat in data["categories"]]
    questions = [cat["questions"] for cat in data["categories"]]
    to_be_switched_int = len(categories) * len(values)


def save_question_set(filename, name, values_list, cats):
    """Save a question set to JSON.

    cats: list of {"name": str, "questions": [str, ...]}
    """
    path = os.path.join(get_questionsets_dir(), filename)
    data = {"name": name, "values": values_list, "categories": cats}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def delete_question_set(filename):
    path = os.path.join(get_questionsets_dir(), filename)
    if os.path.exists(path):
        os.remove(path)


def ensure_default_questionset():
    """Create the default question set JSON if it doesn't exist."""
    d = get_questionsets_dir()
    default_path = os.path.join(d, "ergo_default.json")
    if os.path.exists(default_path):
        return
    # Also check if bundled version exists (PyInstaller)
    bundled = resource_path(os.path.join("questionsets", "ergo_default.json"))
    if os.path.exists(bundled) and bundled != default_path:
        import shutil
        shutil.copy2(bundled, default_path)
        return
    # Generate from hardcoded defaults
    cats = []
    for i, cat_name in enumerate(categories):
        cats.append({"name": cat_name, "questions": questions[i]})
    save_question_set("ergo_default.json", "ERGO Team Event 2025", values, cats)


def reset_game_state():
    """Initialize team_points and to_be_switched_int before game starts."""
    global team_points, to_be_switched_int
    team_points = [0] * len(teams)
    to_be_switched_int = len(categories) * len(values)
