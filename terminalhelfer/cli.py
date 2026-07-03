"""Command-line entry point for terminalhelfer."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import __version__, config, direct, hook_installer, matcher, ollama_client, typo, ui
from .fallback import load_commands

# Exit codes for the single-shot mode, consumed by command_not_found_handle.sh:
#   0 = something actionable was shown (direct command or DB/AI suggestion)
#   1 = nothing relevant found at all
#   2 = looks like a single-word typo of a real installed command (e.g. "sl"
#       for "ls") rather than a natural-language request - our intent-based
#       database isn't the right tool for that, so the shell script should
#       let apt's own "did you mean" logic take over instead.
EXIT_GEFUNDEN = 0
EXIT_NICHTS_GEFUNDEN = 1
EXIT_VERMUTLICH_TIPPFEHLER = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="terminalhelfer",
        description=(
            "Ein deutschsprachiger Terminal-Assistent: beschreibe, was du tun "
            "moechtest, und terminalhelfer schlaegt passende Linux-Befehle vor."
        ),
    )
    parser.add_argument(
        "eingabe",
        nargs="?",
        default=None,
        help="Was du tun moechtest, z.B. 'rechner neu starten' (optional, sonst interaktiv)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Ollama-Modell ueberschreiben (Standard: qwen2.5:1.5b-instruct oder $TERMINALHELFER_MODEL)",
    )
    parser.add_argument("--no-ai", action="store_true", help="Erzwingt reinen Offline-Fallback-Modus, ohne Ollama")
    parser.add_argument(
        "--ki",
        action="store_true",
        help="Aktiviert die optionale KI-Verfeinerung (Ollama) fuer diesen einen Aufruf",
    )
    parser.add_argument(
        "--ki-aktivieren",
        action="store_true",
        help="Aktiviert die KI-Verfeinerung dauerhaft in den Einstellungen",
    )
    parser.add_argument(
        "--ki-deaktivieren",
        action="store_true",
        help="Deaktiviert die KI-Verfeinerung dauerhaft in den Einstellungen (Standard)",
    )
    parser.add_argument("--list", action="store_true", help="Zeigt die komplette Befehlsdatenbank kategorisiert an")
    parser.add_argument(
        "--install-hook",
        action="store_true",
        help="Richtet die command_not_found_handle-Integration in ~/.bashrc ein",
    )
    parser.add_argument("--debug", action="store_true", help="Zeigt zusaetzliche Diagnose-Ausgaben bei Fehlern")
    parser.add_argument("--version", action="version", version=f"terminalhelfer {__version__}")
    return parser


def _handle_single(
    query: str,
    commands: list[dict[str, Any]],
    use_ai: bool,
    model: str | None,
    debug: bool,
) -> int:
    """Process a single query end-to-end. Returns one of the EXIT_* codes
    above, so command_not_found_handle.sh can decide what to do next.
    """
    query = query.strip()
    if not query:
        return EXIT_NICHTS_GEFUNDEN

    if direct.ist_direkter_befehl(query):
        ui.confirm_and_execute(query)
        return EXIT_GEFUNDEN

    results, mode = matcher.match(query, commands=commands, use_ai=use_ai, model=model, debug=debug)
    if results:
        ui.show_mode_banner(mode)
        ui.handle_results(results)
        return EXIT_GEFUNDEN

    if typo.ist_wahrscheinlich_tippfehler(query):
        if debug:
            print(
                f"[debug] '{query}' sieht wie ein Tippfehler eines echten Befehls aus, verweise an apt.",
                file=sys.stderr,
            )
        return EXIT_VERMUTLICH_TIPPFEHLER

    return EXIT_NICHTS_GEFUNDEN


def interactive_loop(commands: list[dict[str, Any]], use_ai: bool, model: str | None, debug: bool) -> None:
    banner_mode = "ki" if (use_ai and ollama_client.is_available()) else "fallback"
    ui.show_mode_banner(banner_mode)

    while True:
        try:
            query = ui.ask_query()
        except KeyboardInterrupt:
            break

        if query is None:
            break

        query = query.strip()
        if not query:
            continue
        if query.lower() in ("exit", "quit"):
            break

        try:
            if direct.ist_direkter_befehl(query):
                ui.confirm_and_execute(query)
            else:
                results, _mode = matcher.match(query, commands=commands, use_ai=use_ai, model=model, debug=debug)
                ui.handle_results(results)
        except KeyboardInterrupt:
            ui.console.print("\n[dim]Abgebrochen.[/dim]")
            continue

    ui.console.print("[dim]Bis bald![/dim]")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.install_hook:
        return hook_installer.install()

    if args.ki_aktivieren:
        config.set_ki_enabled(True)
        ui.console.print("[green]KI-Verfeinerung (Ollama) wurde dauerhaft aktiviert.[/green]")
        return 0

    if args.ki_deaktivieren:
        config.set_ki_enabled(False)
        ui.console.print("[green]KI-Verfeinerung (Ollama) wurde dauerhaft deaktiviert.[/green]")
        return 0

    commands = load_commands()

    if args.list:
        ui.print_command_database(commands)
        return 0

    use_ai = False if args.no_ai else (args.ki or config.is_ki_enabled())

    try:
        if args.eingabe:
            return _handle_single(args.eingabe, commands, use_ai, args.model, args.debug)
        interactive_loop(commands, use_ai=use_ai, model=args.model, debug=args.debug)
    except KeyboardInterrupt:
        ui.console.print("\n[dim]Bis bald![/dim]")

    return EXIT_GEFUNDEN


if __name__ == "__main__":
    sys.exit(main())
