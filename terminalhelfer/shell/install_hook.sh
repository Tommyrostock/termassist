#!/usr/bin/env bash
# Installiert die terminalhelfer command_not_found_handle-Integration in
# ~/.bashrc, damit unbekannte Befehle automatisch von terminalhelfer
# beantwortet werden - ganz ohne das Tool extra aufzurufen.
set -euo pipefail

SKRIPT_VERZEICHNIS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HANDLE_DATEI="$SKRIPT_VERZEICHNIS/command_not_found_handle.sh"
BASHRC="${HOME}/.bashrc"
MARKER_START="# >>> terminalhelfer >>>"
MARKER_ENDE="# <<< terminalhelfer <<<"

if [ ! -f "$HANDLE_DATEI" ]; then
    echo "Fehler: $HANDLE_DATEI wurde nicht gefunden." >&2
    exit 1
fi

if [ -f "$BASHRC" ] && grep -qF "$MARKER_START" "$BASHRC"; then
    echo "Der terminalhelfer-Hook ist bereits in $BASHRC eingerichtet. Nichts zu tun."
    echo "Zum Neu-Einrichten zuerst den Block zwischen '$MARKER_START' und '$MARKER_ENDE' entfernen."
    exit 0
fi

{
    echo ""
    echo "$MARKER_START"
    echo "# Bindet terminalhelfer in command_not_found_handle ein - siehe README."
    cat "$HANDLE_DATEI"
    echo "$MARKER_ENDE"
} >> "$BASHRC"

echo "terminalhelfer-Hook wurde zu $BASHRC hinzugefuegt."
echo "Bitte 'source ~/.bashrc' ausfuehren oder das Terminal neu starten, damit die Aenderung wirksam wird."
