# 🔎 terminalhelfer

**terminalhelfer** ist ein deutschsprachiger Terminal-Assistent fuer Linux-Einsteiger. Du beschreibst in eigenen
Worten, was du tun moechtest – terminalhelfer findet den passenden Befehl dafuer.

## Warum gibt es das?

Wer neu mit Linux anfaengt (z.B. als Azubi in der IT-Ausbildung), kennt oft die *Absicht* ("ich will den Rechner
neu starten"), aber nicht den genauen Befehl ("`sudo reboot`"). Klassische Suchmaschinen oder Man-Pages setzen
voraus, dass man den Befehlsnamen schon kennt. terminalhelfer dreht das um: du tippst, was du erreichen willst,
und bekommst 3–5 passende Vorschlaege mit kurzer Erklaerung – zum Auswaehlen per Pfeiltasten, nicht zum Auswendiglernen.

Damit dabei nichts kaputt geht, schlaegt terminalhelfer **ausschliesslich Befehle aus einer kuratierten,
versionierten Datenbank** vor (siehe [Sicherheitsprinzip](#sicherheitsprinzip-kuratierte-datenbank)) und fuehrt
**niemals** etwas aus, ohne dass du es explizit bestaetigst.

<!-- TODO: Screenshot/GIF einfuegen -->

## Features

- 🗣️ Verstehen von Absicht statt nur Stichwoertern ("neustart" oder "ich will den rechner neu starten" finden
  beide `sudo reboot`)
- 🤖 Optionale KI-Unterstuetzung ueber ein lokales [Ollama](https://ollama.com)-Modell fuer besseres Verstehen
  natuerlicher Sprache
- 📴 Funktioniert komplett offline ueber eine Fuzzy-Suche, falls kein Ollama installiert ist
- 🛡️ Waehlt niemals frei erfundene Befehle – jeder KI-Vorschlag wird gegen die echte Datenbank geprueft
- ⌨️ Pfeiltasten-Auswahl, Bearbeiten, Ausfuehren oder in die Zwischenablage kopieren
- ⚠️ Deutliche Warnung bei potenziell gefaehrlichen Befehlen (`sudo`, `rm`, `dd`, `mkfs`, `shutdown`, `reboot`, ...)
- 📝 Fuellt Platzhalter wie `DATEI`, `ZIEL` oder `PID` interaktiv fuer dich aus

## Installation

Voraussetzung: Python 3.10 oder neuer.

```bash
git clone https://github.com/DEIN-NAME/terminalhelfer.git
cd terminalhelfer
pip install -e .
```

Danach steht der Befehl `terminalhelfer` direkt im Terminal zur Verfuegung.

### Optional: Ollama fuer KI-gestuetztes Matching

Ohne Ollama funktioniert terminalhelfer bereits vollstaendig ueber die eingebaute Fuzzy-Suche. Wer natuerliche
Sprache noch besser verstanden haben moechte, kann zusaetzlich ein kleines, lokales Sprachmodell installieren:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b-instruct
```

terminalhelfer erkennt automatisch, ob Ollama unter `http://localhost:11434` erreichbar ist, und nutzt es dann
automatisch. Ist Ollama nicht erreichbar (oder antwortet nicht rechtzeitig), greift automatisch der
Offline-Fallback – ohne dass du etwas tun musst.

## Nutzung

### Interaktiver Modus

```bash
terminalhelfer
```

Startet eine Endlosschleife, die dich immer wieder fragt, was du tun moechtest. Mit `exit`, `quit` oder
`Strg+C` beendest du die Sitzung sauber.

```
🔎 Was moechtest du tun? › rechner neu starten

Welcher Befehl passt?
❯ sudo reboot        —  Startet den Computer sofort neu
  sudo shutdown now   —  Faehrt den Computer sofort herunter
  ✏️  Selbst eingeben / bearbeiten
  ❌ Abbrechen
```

### Einmal-Modus

```bash
terminalhelfer "rechner neu starten"
```

Gibt direkt Vorschlaege fuer diese eine Eingabe aus und beendet sich danach. Praktisch z.B. fuer ein eigenes
Tastenkuerzel (Keybinding) in `bash` oder `zsh`.

### Weitere Flags

| Flag | Beschreibung |
|---|---|
| `--model NAME` | Ollama-Modell ueberschreiben (Standard: `qwen2.5:1.5b-instruct`, oder `$TERMINALHELFER_MODEL`) |
| `--no-ai` | Erzwingt reinen Offline-Fallback-Modus, auch wenn Ollama laeuft |
| `--list` | Zeigt die komplette Befehlsdatenbank kategorisiert an |
| `--debug` | Zeigt zusaetzliche Diagnose-Ausgaben (z.B. bei Ollama-Verbindungsproblemen) |
| `--version` | Zeigt die installierte Version an |
| `-h`, `--help` | Zeigt die Hilfe an |

## Sicherheitsprinzip: kuratierte Datenbank

terminalhelfer erfindet **keine** Befehle frei. Alle Vorschlaege stammen ausschliesslich aus
[`terminalhelfer/data/commands.json`](terminalhelfer/data/commands.json), einer versionierten, von Menschen
gepflegten Liste. Auch wenn KI-Unterstuetzung ueber Ollama aktiv ist, wird jeder von der KI zurueckgegebene
Befehl gegen diese Datenbank abgeglichen – Vorschlaege, die dort nicht woertlich vorkommen, werden verworfen.
So ist ausgeschlossen, dass ein halluzinierter, gefaehrlicher Befehl bei dir landet.

Zusaetzlich fuehrt terminalhelfer **nie automatisch** einen Befehl aus. Du bekommst den vollstaendigen Befehl
immer noch einmal deutlich angezeigt und musst mit `j` bestaetigen, bevor irgendetwas laeuft (Standard ist
`Nein`). Befehle mit `sudo`, `rm`, `dd`, `mkfs`, `shutdown` oder `reboot` werden zusaetzlich farblich hervorgehoben.

## Eigene Befehle zur Datenbank hinzufuegen

Jeder Eintrag in `terminalhelfer/data/commands.json` folgt diesem Schema:

```json
{
  "cmd": "sudo reboot",
  "kurz": "Startet den Computer sofort neu",
  "kategorie": "System",
  "keywords": ["neustart", "neu starten", "computer neustarten", "reboot"]
}
```

- **`cmd`**: der genaue Befehl, wie er im Terminal ausgefuehrt wird. Platzhalter in GROSSBUCHSTABEN
  (z.B. `DATEI`, `ZIEL`, `PAKETNAME`, `PID`, `DIENST`) werden von terminalhelfer automatisch erkannt und
  interaktiv abgefragt.
- **`kurz`**: eine kurze, verstaendliche deutsche Erklaerung, was der Befehl macht.
- **`kategorie`**: eine grobe Kategorie fuer die `--list`-Ansicht (z.B. `Dateisystem`, `Netzwerk`, `Git`).
- **`keywords`**: moeglichst viele deutsche Formulierungen, mit denen jemand nach diesem Befehl suchen koennte
  – auch Umgangssprache und ganze Saetze helfen der Fuzzy-Suche.

Einfach einen neuen Eintrag am Ende der Liste ergaenzen und einen Pull Request oeffnen (siehe unten).

## Contributing

Beitraege sind willkommen! Ob neue Befehle fuer die Datenbank, bessere Formulierungen bei den Keywords oder
Verbesserungen am Code – einfach forken, aendern, `pytest` laufen lassen und einen Pull Request stellen.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
