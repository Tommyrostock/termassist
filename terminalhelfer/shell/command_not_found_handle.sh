# terminalhelfer command_not_found_handle
#
# Ersetzt/erweitert die von Ubuntu vorinstallierte command_not_found_handle-
# Funktion, die bash automatisch aufruft, wenn ein eingetippter Befehl nicht
# gefunden wurde:
#
#   1. Zuerst wird weiterhin versucht, den gewohnten apt-Hinweis zu zeigen
#      (z.B. "sudo apt install xyz"), falls ein passendes Paket bekannt ist.
#   2. Wird kein passendes Paket gefunden, fragt terminalhelfer im
#      Einmal-Modus nach, ob einer der bekannten Befehle gemeint sein koennte.
#   3. Nur wenn auch terminalhelfer nichts findet, wird die normale
#      "Befehl nicht gefunden"-Meldung angezeigt.
command_not_found_handle () {
    local befehl="$1"
    local apt_tool=""
    local apt_ausgabe=""

    if [ -x /usr/lib/command-not-found ]; then
        apt_tool="/usr/lib/command-not-found"
    elif [ -x /usr/share/command-not-found/command-not-found ]; then
        apt_tool="/usr/share/command-not-found/command-not-found"
    fi

    if [ -n "$apt_tool" ]; then
        apt_ausgabe="$("$apt_tool" -- "$befehl" 2>&1)"
        # command-not-found gibt bei einem echten Paketvorschlag immer einen
        # "apt install"-Hinweis aus; ohne Treffer bleibt nur eine generische
        # Fehlermeldung. Der Exit-Code allein unterscheidet das leider nicht.
        if printf '%s' "$apt_ausgabe" | grep -qi "install"; then
            printf '%s\n' "$apt_ausgabe" >&2
            return 127
        fi
    fi

    if command -v terminalhelfer >/dev/null 2>&1; then
        if terminalhelfer "$*"; then
            return 0
        fi
    fi

    printf '%s: Befehl nicht gefunden\n' "$befehl" >&2
    return 127
}
