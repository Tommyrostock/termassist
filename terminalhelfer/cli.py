"""Command-line entry point for terminalhelfer."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import __version__, config, direct, hook_installer, matcher, ollama_client, ui
from .fallback import load_commands


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
) -> bool:
    """Process a single query end-to-end. Returns True if something actionable
    (a direct command or at least one suggestion) was shown to the user.
    """
    query = query.strip()
    if not query:
        return False

    if direct.ist_direkter_befehl(query):
        ui.confirm_and_execute(query)
        return True

    results, mode = matcher.match(query, commands=commands, use_ai=use_ai, model=model, debug=debug)
    ui.show_mode_banner(mode)
    ui.handle_results(results)
    return bool(results)


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
            gefunden = _handle_single(args.eingabe, commands, use_ai, args.model, args.debug)
            return 0 if gefunden else 1
        interactive_loop(commands, use_ai=use_ai, model=args.model, debug=args.debug)
    except KeyboardInterrupt:
        ui.console.print("\n[dim]Bis bald![/dim]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
