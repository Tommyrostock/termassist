# 🔎 TermAssist

**TermAssist** ist ein deutschsprachiger Terminal-Assistent für Linux-Einsteiger, der natürliche Sprache in
Terminal-Befehle übersetzt. Du beschreibst in eigenen Worten, was du tun möchtest – TermAssist findet den
passenden Befehl dafür und führt **nie automatisch** etwas aus, ohne dass du es explizit bestätigst.

## Wie ist das entstanden?

Dieses Projekt ist in Zusammenarbeit mit KI entstanden: Konzept und Testing stammen von
[DEIN NAME/GITHUB-USERNAME], die Implementierung wurde gemeinsam mit Claude (Anthropic) über Claude Code
umgesetzt. Der Code wurde manuell getestet und iterativ verbessert, unter anderem in einer echten Ubuntu-VM.

<!-- TODO: Screenshot/GIF einfuegen -->

## Voraussetzungen

- **Linux** (getestet unter Ubuntu; sollte auf den meisten Debian-basierten Distributionen laufen)
- **Python 3.10 oder neuer** – [offizielle Download-/Infoseite](https://www.python.org/downloads/). Unter Ubuntu
  meist schon vorinstalliert, prüfbar mit `python3 --version`
- **pip** (Python-Paketmanager) – meist automatisch mit Python dabei; falls nicht vorhanden:
  `sudo apt install python3-pip`. [Offizielle Installationsanleitung](https://pip.pypa.io/en/stable/installation/)
- **git** – zum Herunterladen des Projekts; falls nicht vorhanden: `sudo apt install git`.
  [Offizielle Seite](https://git-scm.com/)
- **Bash** als Shell (Standard unter Ubuntu) – für die automatische Hintergrund-Integration nötig
- Optional, für den erweiterten KI-Modus: **[Ollama](https://ollama.com)**

## Installation

```bash
git clone https://github.com/DEINNAME/termassist.git
cd termassist
pip install -e . --break-system-packages
termassist --install-hook
source ~/.bashrc
```

Danach arbeitet TermAssist unsichtbar im Hintergrund: Du benutzt das Terminal ganz normal weiter, und sobald du
einen Befehl eintippst, den die Shell nicht kennt, schlägt TermAssist automatisch passende Alternativen direkt
an Ort und Stelle vor – inklusive Sicherheitsabfrage, bevor irgendetwas ausgeführt wird.

> `--break-system-packages` wird auf neueren Debian/Ubuntu-Versionen benötigt, da `pip` dort standardmäßig keine
> Pakete außerhalb einer virtuellen Umgebung installiert. Wer lieber eine virtuelle Umgebung nutzt
> (`python3 -m venv .venv && source .venv/bin/activate`), kann das Flag weglassen.

## Optional: KI-Modus aktivieren

Die lokale Befehlsdatenbank ist die Standard-Lösung und reicht für die meisten Anfragen völlig aus – auch auf
älterer oder schwächerer Hardware, wie sie viele Linux-Einsteiger nutzen. Ein lokales KI-Modell kostet dagegen
spürbar CPU-Zeit. Der KI-Modus ist deshalb **optional** und nur für bessere Erkennung bei komplexeren, frei
formulierten Sätzen gedacht – für die Grundfunktion ist er nicht notwendig:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b-instruct
```

Standardmäßig wird Ollama **nie** automatisch angesprochen, selbst wenn es läuft:

```bash
termassist --ki "irgendwas kompliziertes in ganzen saetzen formuliert"   # nur fuer diesen einen Aufruf
termassist --ki-aktivieren                                              # dauerhaft in den Einstellungen
termassist --ki-deaktivieren                                            # dauerhaft wieder abschalten (Standard)
```

Ist die KI aktiviert, fragt TermAssist zuerst weiterhin die lokale Datenbank ab und nutzt Ollama danach nur noch
zur Verfeinerung dieses Ergebnisses. Jeder von der KI zurückgegebene Befehl wird gegen die echte Datenbank
geprüft und verworfen, falls er dort nicht wörtlich vorkommt – TermAssist erfindet nie eigene Befehle. Ist Ollama
nicht erreichbar oder liefert nichts Brauchbares, greift automatisch wieder die lokale Datenbank.

## Nutzung / Beispiele

Einfach normal im Terminal tippen:

```
$ neustart
bash: neustart: command not found

Welcher Befehl passt?
❯ sudo reboot        —  Startet den Computer sofort neu
  sudo shutdown now   —  Faehrt den Computer sofort herunter
  ✏️  Selbst eingeben / bearbeiten
  ❌ Abbrechen
```

Auch mehrwortige, umgangssprachliche Eingaben funktionieren:

```
$ firewall ausschalten
❯ sudo ufw disable   —  Deaktiviert die Firewall
```

```
$ mach mal platz frei
❯ sudo apt autoremove   —  Entfernt nicht mehr benoetigte Pakete automatisch
  sudo apt clean        —  Loescht heruntergeladene Paketdateien aus dem apt-Cache
  ...
```

Wer TermAssist lieber manuell aufruft (z.B. ohne die Hook-Integration einzurichten), kann das jederzeit direkt
tun:

```bash
termassist                          # interaktive Dauerschleife, fragt immer wieder "Was moechtest du tun?"
termassist "rechner neu starten"    # Einmal-Modus fuer eine einzelne Eingabe
```

### Weitere Flags

| Flag | Beschreibung |
|---|---|
| `--install-hook` | Richtet die `command_not_found_handle`-Integration in `~/.bashrc` ein |
| `--ki` | Aktiviert die optionale KI-Verfeinerung (Ollama) für diesen einen Aufruf |
| `--ki-aktivieren` / `--ki-deaktivieren` | Aktiviert/deaktiviert die KI-Verfeinerung dauerhaft in den Einstellungen |
| `--model NAME` | Ollama-Modell überschreiben (Standard: `qwen2.5:1.5b-instruct`, oder `$TERMASSIST_MODEL`) |
| `--no-ai` | Erzwingt reinen Offline-Modus, auch wenn KI aktiviert und Ollama erreichbar ist |
| `--list` | Zeigt die komplette Befehlsdatenbank kategorisiert an |
| `--debug` | Zeigt zusätzliche Diagnose-Ausgaben (z.B. bei Ollama-Verbindungsproblemen) |
| `--version` | Zeigt die installierte Version an |
| `-h`, `--help` | Zeigt die Hilfe an |

## Eigene Befehle zur Datenbank hinzufügen

TermAssist schlägt ausschließlich Befehle aus einer kuratierten, versionierten Datenbank vor – nie frei
erfundene. Jeder Eintrag in [`termassist/data/commands.json`](termassist/data/commands.json) folgt diesem
Schema:

```json
{
  "cmd": "sudo reboot",
  "kurz": "Startet den Computer sofort neu",
  "kategorie": "System",
  "keywords": ["neustart", "neu starten", "computer neustarten", "reboot"]
}
```

- **`cmd`**: der genaue Befehl, wie er im Terminal ausgeführt wird. Platzhalter in GROSSBUCHSTABEN (z.B.
  `DATEI`, `ZIEL`, `PAKETNAME`, `PID`, `DIENST`) werden von TermAssist automatisch erkannt und interaktiv
  abgefragt.
- **`kurz`**: eine kurze, verständliche deutsche Erklärung, was der Befehl macht.
- **`kategorie`**: eine grobe Kategorie für die `--list`-Ansicht (z.B. `Dateisystem`, `Netzwerk`, `Git`).
- **`keywords`**: möglichst viele (idealerweise 6-10) deutsche Formulierungen, mit denen jemand nach diesem
  Befehl suchen könnte – einzelne Stichwörter, Umgangssprache und ganze Sätze helfen der Fuzzy-Suche alle
  gleichermaßen.

Einfach einen neuen Eintrag am Ende der Liste ergänzen, `pytest` laufen lassen und einen Pull Request öffnen.

## Deinstallation

Öffne `~/.bashrc` und entferne den Block zwischen den Kommentaren `# >>> termassist >>>` und
`# <<< termassist <<<`, dann `source ~/.bashrc` erneut ausführen.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
