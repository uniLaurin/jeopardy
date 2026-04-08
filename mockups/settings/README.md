# Jeopardy Settings Screen - Konzeptmockups

Fünf verschiedene Layout-Konzepte für den Settings-Screen, die alle im **Classic Jeopardy Look** (königsblau #060CE9, gold #DBAB51) gestaltet sind.

## Übersicht der Konzepte

### 1. Sidebar Classic (`settings_1_sidebar.html`)
**Ansatz:** 2-Spalten-Layout mit schmaler Sidebar

- **Links (25%):** Kompakte Team-Verwaltung in einer Sidebar
- **Rechts (75%):** Großes Fragenset-Editor-Panel
- **Vorteile:**
  - Sehr klare visuelle Trennung durch Gold-Linie
  - Kompakte Teams benötigen weniger Platz
  - Großer Platz für umfangreiche Fragenset-Bearbeitung
  - Traditionelles Admin-Panel-Layout
- **Nachteil:**
  - Teams-Panel könnte bei vielen Teams eng werden

---

### 2. Stacked Sections (`settings_2_stacked.html`)
**Ansatz:** Vertikale Stapelung mit großen Cards

- **Oben:** Teams-Karte (volle Breite, 3er Grid)
- **Unten:** Fragenset-Karte (volle Breite)
- **Vorteile:**
  - Sehr viel Whitespace, nicht überwältigend
  - Teams als große, gut lesbare Cards
  - Fokus auf einen Bereich zur Zeit
  - Responsive kann funktionieren
  - Intuitive Top-to-Bottom Reihenfolge
- **Nachteil:**
  - Braucht mehr vertikale Höhe
  - Weniger Übersicht auf einen Blick

---

### 3. Tabbed Interface (`settings_3_tabs.html`)
**Ansatz:** Tab-Navigation mit exklusiven Inhalten

- **Tabs:** TEAMS | FRAGENSET | START
- **Verhalten:** Nur ein Bereich ist gleichzeitig sichtbar
- **Vorteile:**
  - Maximal clean und fokussiert
  - Keine Überladung, großer Platz pro Tab
  - START-Tab zeigt Zusammenfassung
  - Sehr moderner Look
- **Nachteil:**
  - Weniger Übersicht (muss zwischen Tabs wechseln)
  - Könnte weniger kontextbewusst wirken

---

### 4. Wizard Steps (`settings_4_wizard.html`)
**Ansatz:** Schritt-für-Schritt-Anleitung mit visuellen Progress-Indikatoren

- **Top:** Step-Indikatoren (1, 2, 3) mit Verbindungslinien und Gold-Highlight
- **Mitte:** Großer Step-Content mit Beschreibung
- **Bottom:** Vor/Weiter/Start-Buttons
- **Vorteile:**
  - Onboarding-Gefühl, führt Nutzer leicht
  - Visuelle Progress-Anzeige (erledigt, aktuell, kommend)
  - Step-Beschreibungen helfen neuen Usern
  - Sehr zeitgemäß und modern
- **Nachteil:**
  - Könnte für erfahrene User zu langsam sein
  - Mehr Clicks nötig (3 Steps statt 1 Screen)

---

### 5. Dashboard Grid (`settings_5_dashboard.html`)
**Ansatz:** Admin-Dashboard mit flexiblem Grid-Layout

- **Oben-Links:** Teams-Card (kompakt)
- **Oben-Rechts:** Fragensets-Card (Selector)
- **Unten:** Großer Editor (volle Breite)
- **Vorteile:**
  - Maximum Übersicht (alle Teile sichtbar)
  - Modern, Admin-Dashboard-Gefühl
  - Asymmetrisches Layout wirkt professionell
  - Teams und Sets auf einen Blick einsehbar
  - Balancierte Raumnutzung
- **Nachteil:**
  - Kann bei sehr kleinen Screens eng werden

---

## Design System (konsistent über alle Mockups)

Alle Mockups verwenden das etablierte Classic Jeopardy Design System:

- **Hintergrund:** `#060CE9` (Königsblau)
- **Cards:** `#0A15B8` / `#0A10A0` (Dunkles Blau)
- **Borders:** `#000A80` (sehr dunkles Blau)
- **Akzent (Gold):** `#DBAB51` (kräftiges Gold für Highlights, Text, Borders)
- **Hover Gold:** `#E8C76B`
- **Labels:** `#C0C0D5` (helles Grau)
- **Placeholder:** `#9999CC` (Grau-Blau)

### Typografie
- **Titel:** 42px, bold, Gold
- **Sektionen:** 20-24px, bold, Gold
- **Body:** 12-14px, Weiß/Grau
- **Small:** 11-13px, Grau-Blau
- **Font:** Arial (wie im Code)

### Komponenten
- **Primary Button:** Gold Hintergrund, dunkelblauen Text, Hover-Effekt
- **Secondary Button:** Grau, Hover zu Gold
- **Input Fields:** Dunkelblaues Feld, Gold Border bei Focus
- **Cards:** Dunkelblaue Karte mit Gold-Linie links (2-4px), inset Shadow
- **Listbox:** Dunkelblaues Feld mit Scrolling, Gold Selection

---

## Elemente in allen Mockups

### Teams-Bereich (in allen)
- 3 Beispiel-Teams: Grün, Rot, Lila
- Team-Name Input
- Farb-Swatch zum Klicken
- +/- Buttons für Teamanzahl (2-6)
- Tasten-Info: "1=Team 1, 2=Team 2, 3=Team 3, 4=Niemand"

### Fragenset-Bereich (in allen)
- Listbox mit 3 Beispiel-Sets:
  - "ERGO Team Event 2025" (selected)
  - "Allgemeinwissen Quiz"
  - "Fußball Spezial"
- Name-Input: "ERGO Team Event 2025"
- Werte-Input: "100, 200, 400, 600, 1000"
- Kategorien-Listbox mit 4 Beispiel-Kategorien
- +/- Buttons für Kategorien
- Kategorie-Name Input: "World of Ergo"
- 5 Frage-Inputs für die Werte (100, 200, 400, 600, 1000)
- Speichern-Button

### Footer (in allen)
- Großer ">>> SPIEL STARTEN <<<" Button (Gold, prominent)
- Hover-Effekt mit Skalierung

---

## Wie öffnen?

Einfach die gewünschte HTML-Datei im Browser öffnen:
- `settings_1_sidebar.html`
- `settings_2_stacked.html`
- `settings_3_tabs.html`
- `settings_4_wizard.html`
- `settings_5_dashboard.html`

Die Mockups sind statische HTML-Seiten mit inline CSS und einem Konzept-Header mit Beschreibung.

---

## Empfehlung für die Umsetzung im Code

Basierend auf der Jeopardy Game-Architektur:

- **Sidebar Classic (1):** Sehr einfach zu implementieren mit `.place()` (zwei Frames nebeneinander)
- **Stacked Sections (2):** Auch einfach, zwei große Panels übereinander
- **Tabbed Interface (3):** Mittel (braucht Tab-Switching, aber clean Code möglich)
- **Wizard Steps (4):** Komplex (viel State-Management für Steps)
- **Dashboard Grid (5):** Mittel (`.place()` mit mehreren Karten, flexibles Layout)

Meine Empfehlung: **Sidebar Classic (1)** oder **Dashboard Grid (5)** — beide sind elegant, bieten gute Übersicht und sind in reinem tkinter gut umsetzbar.
