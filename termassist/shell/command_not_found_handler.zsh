# termassist command_not_found_handler (Zsh-Variante)
#
# Zsh-Gegenstueck zu command_not_found_handle.sh (Bash). Wird von Zsh
# automatisch aufgerufen, wenn ein eingetippter Befehl nicht gefunden wurde -
# z.B. standardmaessig unter aktuellem Kali Linux, das Zsh statt Bash nutzt.
#
# Die Logik ist inhaltlich 1:1 identisch zur Bash-Version (siehe dortige
# ausfuehrliche Begruendung zur Reihenfolge termassist-zuerst-dann-apt).
# Nur zwei Zsh-Besonderheiten sind zu beachten:
#
#   1. Der Funktionsname heisst in Zsh "command_not_found_handler" (mit "er"
#      am Ende), nicht "command_not_found_handle" wie in Bash.
#   2. Zum Aufteilen der Eingabe in einzelne Woerter wird `${=eingabe}`
#      verwendet statt Bashs `read -ra`: das ist Zsh's eingebauter Mechanismus
#      fuer erzwungenes Word-Splitting einer Variable. Anders als unquoted
#      Word-Splitting in Bash (z.B. in `set -- $eingabe`) expandiert Zsh dabei
#      standardmaessig KEINE Glob-Muster (z.B. "*") in der Variable - das
#      Verhalten ist also von Haus aus sicher, ganz ohne Sonderbehandlung.
#
# Ansonsten verhaelt sich alles gleich, da if/local/printf/command -v in Zsh
# genauso funktionieren wie in Bash.
command_not_found_handler () {
    local befehl="$1"
    local eingabe="$*"

    local -a woerter
    woerter=(${=eingabe})
    local wortanzahl=${#woerter[@]}

    local thf_exit=1
    if command -v termassist >/dev/null 2>&1; then
        termassist "$eingabe"
        thf_exit=$?
    fi

    # Fall 1: termassist hat selbst eine passende Antwort gezeigt
    # (Datenbanktreffer, KI-Verfeinerung oder ein direkt erkannter gueltiger
    # Befehl) - hier ist nichts weiter zu tun.
    if [ "$thf_exit" -eq 0 ]; then
        return 0
    fi

    # Fall 2: mehrwortige Eingabe ohne Treffer. Das ist praktisch nie ein
    # einzelner Tippfehler eines Binaernamens, also lohnt sich der
    # (vergleichsweise langsame) apt-Aufruf hier nicht.
    if [ "$wortanzahl" -gt 1 ]; then
        printf '%s: Befehl nicht gefunden\n' "$befehl" >&2
        return 127
    fi

    # Fall 3: einzelnes Wort, termassist hat entweder Exit-Code 2 ("sieht nach
    # Tippfehler eines echten Programms aus") oder 1 ("nichts gefunden")
    # signalisiert. In beiden Faellen ist der klassische apt-Hinweis noch
    # einen Versuch wert, bevor wir endgueltig aufgeben.
    # TERMASSIST_APT_TOOL_UEBERSCHREIBEN erlaubt Tests, das apt-Tool durch
    # ein Fake zu ersetzen, ohne echte Dateien unter /usr/lib anzulegen. Im
    # normalen Betrieb ist diese Variable nie gesetzt.
    local apt_tool="${TERMASSIST_APT_TOOL_UEBERSCHREIBEN:-}"
    if [ -z "$apt_tool" ]; then
        if [ -x /usr/lib/command-not-found ]; then
            apt_tool="/usr/lib/command-not-found"
        elif [ -x /usr/share/command-not-found/command-not-found ]; then
            apt_tool="/usr/share/command-not-found/command-not-found"
        fi
    fi

    if [ -n "$apt_tool" ]; then
        local apt_ausgabe
        apt_ausgabe="$("$apt_tool" -- "$befehl" 2>&1)"
        # command-not-found gibt bei einem echten Paketvorschlag immer einen
        # "apt install"-Hinweis aus; ohne Treffer bleibt nur eine generische
        # Fehlermeldung. Der Exit-Code allein unterscheidet das leider nicht.
        if printf '%s' "$apt_ausgabe" | grep -qi "install"; then
            printf '%s\n' "$apt_ausgabe" >&2
            return 127
        fi
    fi

    printf '%s: Befehl nicht gefunden\n' "$befehl" >&2
    return 127
}
