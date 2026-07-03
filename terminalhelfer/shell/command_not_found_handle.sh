# terminalhelfer command_not_found_handle
#
# Ersetzt/erweitert die von Ubuntu vorinstallierte command_not_found_handle-
# Funktion, die bash automatisch aufruft, wenn ein eingetippter Befehl nicht
# gefunden wurde.
#
# WARUM DIESE REIHENFOLGE? (v0.3)
# --------------------------------
# In einer frueheren Version wurde zuerst das apt-basierte command-not-found
# befragt und terminalhelfer nur als Rueckfall genutzt. Das Problem dabei:
# apt/command-not-found liefert fast IMMER irgendeine aehnlich klingende
# Paketvermutung, auch wenn die Eingabe gar kein Tippfehler eines Binaernamens
# war, sondern eine mehrwortige, natuersprachliche Anfrage wie
# "alle dateien loeschen" oder "firewall ausschalten". Dadurch gewann apt in
# der Praxis fast immer, sobald mehr als ein Wort eingegeben wurde, und
# terminalhelfer kam nie zum Zug.
#
# Die Reihenfolge ist deshalb jetzt umgekehrt:
#
#   1. IMMER zuerst terminalhelfer befragen, unabhaengig von der Wortanzahl.
#      terminalhelfer entscheidet selbst (siehe terminalhelfer/typo.py), ob
#      die Eingabe wie ein simpler Tippfehler eines einzelnen echten Befehls
#      aussieht (z.B. "sl" statt "ls") oder wie eine natuersprachliche
#      Absicht - und liefert einen von drei Exit-Codes:
#        0 = etwas gefunden/behandelt (Datenbanktreffer oder direkter Befehl)
#        1 = nichts Passendes gefunden
#        2 = sieht nach einem Tippfehler eines echten Programms aus, das ist
#            eher ein Fall fuer apts eigene Rechtschreibkorrektur
#   2. Exit-Code 0 -> fertig, nichts weiter noetig.
#   3. Mehrwortige Eingaben sind so gut wie nie ein einzelner Tippfehler eines
#      Binaernamens. Deshalb wird bei mehr als einem Wort der (langsamere)
#      apt-Aufruf gar nicht erst gestartet, wenn terminalhelfer nichts fand -
#      dann kommt direkt die normale Fehlermeldung.
#   4. Bei einzelnen Woertern (Exit-Code 1 oder 2) lohnt sich apt noch als
#      letzter Versuch, bevor endgueltig aufgegeben wird.
#   5. Nur wenn weder terminalhelfer noch apt etwas Sinnvolles liefern, wird
#      die normale "Befehl nicht gefunden"-Meldung angezeigt.
command_not_found_handle () {
    local befehl="$1"
    local eingabe="$*"

    # Wortanzahl ueber `read -ra` ermitteln statt ueber unquoted `$eingabe`
    # (z.B. in `set -- $eingabe`) - so wird die Eingabe nur in Woerter
    # zerlegt, aber nicht als Glob-Muster (z.B. "*") expandiert.
    local -a woerter
    read -ra woerter <<< "$eingabe"
    local wortanzahl=${#woerter[@]}

    local thf_exit=1
    if command -v terminalhelfer >/dev/null 2>&1; then
        terminalhelfer "$eingabe"
        thf_exit=$?
    fi

    # Fall 1: terminalhelfer hat selbst eine passende Antwort gezeigt
    # (Datenbanktreffer, KI-Verfeinerung oder ein direkt erkannter gueltiger
    # Befehl) - hier ist nichts weiter zu tun.
    if [ "$thf_exit" -eq 0 ]; then
        return 0
    fi

    # Fall 2: mehrwortige Eingabe ohne Treffer. Das ist praktisch nie ein
    # einzelner Tippfehler eines Binaernamens, also lohnt sich der
    # (vergleichsweise langsame) apt-Aufruf hier nicht - terminalhelfer haette
    # bei einem Datenbanktreffer bereits Exit-Code 0 geliefert, und fuer
    # mehrwortige Eingaben liefert terminalhelfer ohnehin nie Exit-Code 2.
    if [ "$wortanzahl" -gt 1 ]; then
        printf '%s: Befehl nicht gefunden\n' "$befehl" >&2
        return 127
    fi

    # Fall 3: einzelnes Wort, terminalhelfer hat entweder
    #   Exit-Code 2 = "sieht nach Tippfehler eines echten Programms aus" oder
    #   Exit-Code 1 = "nichts Passendes in der Datenbank gefunden"
    # signalisiert. In beiden Faellen ist der klassische apt-Hinweis noch
    # einen Versuch wert, bevor wir endgueltig aufgeben.
    # TERMINALHELFER_APT_TOOL_UEBERSCHREIBEN erlaubt Tests, das apt-Tool durch
    # ein Fake zu ersetzen, ohne echte Dateien unter /usr/lib anzulegen. Im
    # normalen Betrieb ist diese Variable nie gesetzt.
    local apt_tool="${TERMINALHELFER_APT_TOOL_UEBERSCHREIBEN:-}"
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
