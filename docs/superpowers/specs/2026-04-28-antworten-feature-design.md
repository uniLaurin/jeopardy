# Antworten-Feature — Design-Spec

**Datum:** 2026-04-28
**Status:** Brainstorming abgeschlossen, Plan-Erstellung folgt

## Ziel

Spielleiter und Teams sollen nach Beantwortung einer Frage optional die korrekte Antwort sehen können. Die Antworten werden pro Fragenset hinterlegt und können pro Set ein-/ausgeschaltet werden. Während des Spiels gibt es zusätzlich eine Taste zum manuellen Aufdecken sowie automatisches Aufdecken nach Punktevergabe.

## Datenmodell

JSON-Format der Fragensets in `questionsets/*.json` wird rückwärtskompatibel erweitert:

```json
{
  "name": "Beispiel-Set",
  "values": [100, 200, 300, 400, 500],
  "show_answers": false,
  "categories": [
    {
      "name": "Geographie",
      "questions": [
        {"q": "Hauptstadt von Frankreich?", "a": "Paris"},
        {"q": "Längster Fluss Europas?"},
        "Alte String-Frage ohne Antwort"
      ]
    }
  ]
}
```

**Lade-Logik (`resources.py`):**
- Beim Einlesen wird jede Frage normalisiert:
  - String `"Frage?"` → `{"q": "Frage?", "a": ""}`
  - Dict ohne `a` → `a` wird als `""` ergänzt
- Damit arbeitet der Rest des Codes immer mit Dicts.
- Modul-Variable `r.show_answers` (bool) wird beim Laden eines Sets gesetzt. Default `False`.

**Speicher-Logik:** Alle Fragen werden als Dicts geschrieben (ehemalige Strings werden migriert). `show_answers` wird auf Top-Level des Sets gespeichert.

## Settings-Erweiterung (FRAGENSET-Tab)

**Pro Frage:** zweites Eingabefeld unter dem Frage-Feld:
- Label: `Antwort:`
- Stil: gleicher Look wie Frage-Feld, Gold Focus-Border via `_bind_focus_border`
- Placeholder: "(optional)"

**Pro Set:** Checkbox/Toggle oben im Set-Editor neben dem Set-Namen:
> ☐ Antworten nach Beantwortung anzeigen

State wird beim Set-Speichern persistiert.

## Spielablauf (`game.py`)

Antwort-Logik ist **nur aktiv**, wenn:
- `r.show_answers == True` UND
- die aktuelle Frage ein nicht-leeres `a`-Feld hat.

Sonst gilt das bisherige Verhalten unverändert.

### State-Maschine

| State | Beschreibung | Erlaubte Aktionen |
|---|---|---|
| **1: Frage offen** | Karte zeigt die Frage (wie heute) | `Space` (Audio-Stop), `1`–`N` (Punkte), `N+1` (Niemand), `A` (→ State 2) |
| **2: Antwort offen (manuell)** | Spielleiter hat `A` gedrückt, Antwort-Seite ist sichtbar | `1`–`N` (Punkte → State 3 oder Board), `N+1`, beliebige andere Taste (→ zurück zu State 1) |
| **3: Antwort nach Punktevergabe** | Punkte sind bereits vergeben, Antwort wird automatisch angezeigt | beliebige Taste → zurück zum Board |

### Tasten-Verhalten

- **`A`** (in State 1): Stoppt Timer-Audio, flippt zur Antwort-Seite (State 2).
- **Team-Taste `1`–`N`** / **Niemand `N+1`** (in State 1 oder 2): Vergibt Punkte (State 1) bzw. nutzt bereits vergebene (State 2). Wenn Antwort-Logik aktiv → wechselt zu State 3 (Antwort sichtbar). Sonst direkt zurück zu Board wie heute.
- **Beliebige Taste in State 3**: Flippt Karte zurück ins Board.
- **Beliebige Taste in State 2** (außer Punkte-Tasten): Flippt zurück zur Frage (State 1).

### Audio

- `audio.stop_music()` wird gerufen sobald von State 1 in State 2 oder 3 gewechselt wird (egal ob via `A` oder Punkte-Taste).
- Verhalten konsistent mit aktuellem `Space`/Punkte-Stop.

### Flip-Animation

Wiederverwendung der bestehenden `flip()`-Mechanik in `game.py`:
1. Karte horizontal zusammendrücken (Breite → 0)
2. Hintergrundfarbe und Text austauschen
3. Karte expandieren

Antwort-Seite hat eigene Farbgebung (siehe unten).

## Visuelle Gestaltung der Antwort-Seite

- **Hintergrund:** `r.GOLD` (Akzentfarbe) — klarer Kontrast zur Frage-Seite (`r.DARK_BLUE`).
- **Text-Farbe:** `r.DARK_BLUE` auf Gold (gute Lesbarkeit).
- **Layout:**
  - Oben klein: Label `ANTWORT` in `r.FONT_SECTION`
  - Zentriert groß: Antwort-Text in Größe analog zur aktuellen Frage-Darstellung (ggf. dynamisch je nach Länge)
  - Unten klein (nur in State 2): Hinweis `Beliebige Taste: zurück` in `r.FONT_SMALL`, gedimmte Farbe
- **Theme-Integration:** automatisch über `_rebind_colors()` — passt zu jedem Theme.

## Edge Cases

| Fall | Verhalten |
|---|---|
| Toggle an, aber Antwort fehlt | `A`-Taste = No-Op. Punktevergabe ohne Auto-Flip. |
| Toggle aus | Komplett altes Verhalten, `A` wird ignoriert. |
| Altes Set ohne `show_answers` | Default `False`, beim Speichern wird Feld ergänzt. |
| Alte String-Fragen | Beim Laden zu `{"q": str, "a": ""}` migriert. |
| `A` in State 2 erneut gedrückt | Ignorieren (gleicher State). |

## Zusammenfassung der Änderungen

| Datei | Änderung |
|---|---|
| `resources.py` | Question-Normalisierung beim Laden/Speichern, `show_answers` Feld, Modul-Variable `r.show_answers` |
| `settings.py` | FRAGENSET-Tab: Antwort-Feld pro Frage, Set-Toggle "Antworten anzeigen" |
| `game.py` | State-Maschine erweitert, `A`-Taste, Flip zur Antwort-Seite (Gold), Audio-Stop bei manuellem Flip, Auto-Flip nach Punktevergabe, Rückkehr per beliebiger Taste |
| `CLAUDE.md` | Doku-Update: Datenmodell, State-Maschine, Tastenbelegung |

## Bekannte offene Probleme

1. **Editor-Layout:** Durch das zusätzliche Antwort-Feld pro Frage wird der FRAGENSET-Editor ~doppelt so hoch. Bei vielen Fragen pro Kategorie könnte das Layout unhandlich werden. Mögliche spätere Lösung: Antwort-Feld collapsible (per `+`-Button aufklappen) oder nur sichtbar wenn der Set-Toggle aktiv ist. **Erstmal nicht angehen — YAGNI bis es konkret stört.**
