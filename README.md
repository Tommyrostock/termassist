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

Das Besondere: Nach der Einrichtung musst du terminalhelfer gar nicht mehr bewusst aufrufen. Du arbeitest ganz
normal im Terminal (`cd`, `ls`, `wget`, ...) und nur wenn du einen Befehl eintippst, den die Shell nicht kennt,
schaltet sich terminalhelfer automatisch im Hintergrund ein und zeigt passende Vorschlaege direkt an Ort und
Stelle an.

<!-- TODO: Screenshot/GIF einfuegen -->

## Features

- 👻 **Unsichtbare Integration**: haengt sich in bashs `command_not_found_handle` ein und erscheint nur, wenn ein
  Befehl nicht gefunden wird – kein separates Programm, das man erst aufrufen muss
- 🗣️ Verstehen von Absicht statt nur Stichwoertern ("neustart" oder "ich will den rechner neu starten" finden
  beide `sudo reboot`)
- 📴 Funktioniert komplett offline ueber eine kuratierte Datenbank mit Fuzzy-Suche – das ist die Standard-Loesung
  fuer alle Nutzer, unabhaengig von der Hardware
- 🤖 Optionale KI-Verfeinerung ueber ein lokales [Ollama](https://ollama.com)-Modell fuer Nutzer mit staerkerer
  Hardware, die noch freiere Satzformulierungen abdecken wollen (siehe [Fuer Fortgeschrittene](#fuer-fortgeschrittene-optionale-ki-verfeinerung-mit-ollama))
- ⚡ Erkennt bereits gueltige Befehle (z.B. `df -h`) sofort und springt ohne Umweg zur Ausfuehrungs-Bestaetigung
- 🛡️ Waehlt niemals frei erfundene Befehle – jeder KI-Vorschlag wird gegen die echte Datenbank geprueft
- ⌨️ Pfeiltasten-Auswahl, Bearbeiten, Ausfuehren oder in die Zwischenablage kopieren
- ⚠️ Deutliche Warnung bei potenziell gefaehrlichen Befehlen (`sudo`, `rm`, `dd`, `mkfs`, `shutdown`, `reboot`, ...)
- 📝 Fuellt Platzhalter wie `DATEI`, `ZIEL` oder `PID` interaktiv fuer dich aus

## Installation

Voraussetzung: Python 3.10 oder neuer und `bash`.

```bash
git clone https://github.com/DEIN-NAME/terminalhelfer.git
cd terminalhelfer
pip install -e .
terminalhelfer --install-hook
```

`--install-hook` richtet die Hintergrund-Integration ein (siehe unten) und traegt dafuer einen klar
gekennzeichneten Block in deine `~/.bashrc` ein. Am Ende einmal `source ~/.bashrc` ausfuehren oder das Terminal
neu starten – danach arbeitet terminalhelfer automatisch im Hintergrund.

### Wie die Hintergrund-Integration funktioniert

Bash bietet die eingebaute Funktion `command_not_found_handle`, die automatisch aufgerufen wird, sobald ein
eingetippter Befehl nicht gefunden wird (derselbe Mechanismus, ueber den Ubuntu normalerweise "Command 'xyz'
not found, but can be installed with: ..." anzeigt). `--install-hook` erweitert genau diese Funktion:

1. **terminalhelfer wird immer zuerst befragt**, egal ob die Eingabe aus einem oder mehreren Woertern besteht.
   Findet es einen Datenbanktreffer oder erkennt es einen bereits gueltigen Befehl, siehst du direkt die
   gewohnte Pfeiltasten-Auswahl bzw. Sicherheitsabfrage – fertig.
2. Nur bei einem **einzelnen Wort ohne Datenbanktreffer** prueft terminalhelfer zusaetzlich, ob das eher wie ein
   simpler Tippfehler eines echten Programms aussieht (z.B. `sl` statt `ls`). In diesem Fall zeigt terminalhelfer
   selbst nichts an, sondern ueberlaesst das dem gewohnten apt-Hinweis (`sudo apt install ...`) – dafuer ist apts
   eigene Rechtschreibkorrektur besser geeignet als die intent-basierte Datenbank von terminalhelfer.
3. Nur wenn weder terminalhelfer noch apt etwas Sinnvolles finden, siehst du die normale "Befehl nicht
   gefunden"-Meldung.

Mehrwortige Eingaben wie `firewall ausschalten` gehen also **nie** an apt (das haette frueher fast immer eine
falsche Paketvermutung geliefert), sondern werden ausschliesslich von terminalhelfers eigener Datenbank
beantwortet.

**Deinstallieren:** Oeffne `~/.bashrc` und entferne den Block zwischen den Kommentaren
`# >>> terminalhelfer >>>` und `# <<< terminalhelfer <<<`, dann `source ~/.bashrc` erneut ausfuehren.

### Manueller Modus (ohne Hook)

Der klassische, eigenstaendige Modus bleibt vollstaendig erhalten – praktisch, wenn du die Hook-Integration nicht
einrichten willst oder eine andere Shell als bash nutzt:

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

Oder im Einmal-Modus fuer eine einzelne Eingabe (das nutzt auch der Hook intern):

```bash
terminalhelfer "rechner neu starten"
```

### Fuer Fortgeschrittene: optionale KI-Verfeinerung mit Ollama

Die lokale Datenbank ist die Standard-Loesung und reicht fuer die meisten Anfragen voellig aus – auch auf
aelterer oder schwaecherer Hardware, wie sie viele Linux-Einsteiger nutzen. Ein lokales KI-Modell kostet dagegen
spuerbar CPU-Zeit: auf einer VM ohne GPU dauerte eine einzelne Anfrage in unseren Tests mehrere Sekunden. Wer
staerkere Hardware hat und noch freiere, ganze Satzformulierungen abdecken moechte, kann optional
[Ollama](https://ollama.com) dazuschalten:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b-instruct
```

Standardmaessig wird Ollama **nie** automatisch angesprochen, selbst wenn es laeuft – das spart unnoetige
Rechenlast fuer alle, die es nicht aktiv nutzen wollen. Du aktivierst die KI-Verfeinerung explizit:

```bash
terminalhelfer --ki "irgendwas kompliziertes in ganzen saetzen formuliert"   # nur fuer diesen einen Aufruf
terminalhelfer --ki-aktivieren                                              # dauerhaft in den Einstellungen
terminalhelfer --ki-deaktivieren                                            # dauerhaft wieder abschalten (Standard)
```

Ist die KI aktiviert, fragt terminalhelfer zuerst weiterhin die lokale Datenbank ab und nutzt Ollama danach nur
noch zur Verfeinerung dieses Ergebnisses. Jeder von der KI zurueckgegebene Befehl wird gegen die echte Datenbank
geprueft; ist Ollama nicht erreichbar oder liefert es nichts Brauchbares, greift automatisch wieder die lokale
Datenbank.

### Weitere Flags

| Flag | Beschreibung |
|---|---|
| `--install-hook` | Richtet die `command_not_found_handle`-Integration in `~/.bashrc` ein |
| `--ki` | Aktiviert die optionale KI-Verfeinerung (Ollama) fuer diesen einen Aufruf |
| `--ki-aktivieren` / `--ki-deaktivieren` | Aktiviert/deaktiviert die KI-Verfeinerung dauerhaft in den Einstellungen |
| `--model NAME` | Ollama-Modell ueberschreiben (Standard: `qwen2.5:1.5b-instruct`, oder `$TERMINALHELFER_MODEL`) |
| `--no-ai` | Erzwingt reinen Offline-Modus, auch wenn KI aktiviert und Ollama erreichbar ist |
| `--list` | Zeigt die komplette Befehlsdatenbank kategorisiert an |
| `--debug` | Zeigt zusaetzliche Diagnose-Ausgaben (z.B. bei Ollama-Verbindungsproblemen) |
| `--version` | Zeigt die installierte Version an |
| `-h`, `--help` | Zeigt die Hilfe an |

## Sicherheitsprinzip: kuratierte Datenbank

terminalhelfer erfindet **keine** Befehle frei. Alle Vorschlaege stammen ausschliesslich aus
[`terminalhelfer/data/commands.json`](terminalhelfer/data/commands.json), einer versionierten, von Menschen
gepflegten Liste mit ueber 150 Befehlen. Diese lokale Datenbank wird fuer jede Anfrage zuerst befragt. Nur wenn
du die optionale KI-Verfeinerung aktiviert hast, wird Ollama zusaetzlich zurate gezogen – und jeder von der KI
zurueckgegebene Befehl wird gegen die Datenbank abgeglichen, bevor er dir angezeigt wird. Vorschlaege, die dort
nicht woertlich vorkommen, werden verworfen. So ist ausgeschlossen, dass ein halluzinierter, gefaehrlicher Befehl
bei dir landet.

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
- **`keywords`**: moeglichst viele (idealerweise 6-10) deutsche Formulierungen, mit denen jemand nach diesem
  Befehl suchen koennte – einzelne Stichwoerter, Umgangssprache und ganze Saetze helfen der Fuzzy-Suche alle
  gleichermassen.

Einfach einen neuen Eintrag am Ende der Liste ergaenzen und einen Pull Request oeffnen (siehe unten).

## Contributing

Beitraege sind willkommen! Ob neue Befehle fuer die Datenbank, bessere Formulierungen bei den Keywords oder
Verbesserungen am Code – einfach forken, aendern, `pytest` laufen lassen und einen Pull Request stellen.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
