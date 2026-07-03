"""Command-line entry point for terminalhelfer."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import __version__, matcher, ollama_client, ui
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
    parser.add_argument("--list", action="store_true", help="Zeigt die komplette Befehlsdatenbank kategorisiert an")
    parser.add_argument("--debug", action="store_true", help="Zeigt zusaetzliche Diagnose-Ausgaben bei Fehlern")
    parser.add_argument("--version", action="version", version=f"terminalhelfer {__version__}")
    return parser


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
            results, _mode = matcher.match(query, commands=commands, use_ai=use_ai, model=model, debug=debug)
            ui.handle_results(results)
        except KeyboardInterrupt:
            ui.console.print("\n[dim]Abgebrochen.[/dim]")
            continue

    ui.console.print("[dim]Bis bald![/dim]")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    commands = load_commands()

    if args.list:
        ui.print_command_database(commands)
        return 0

    use_ai = not args.no_ai

    try:
        if args.eingabe:
            results, mode = matcher.match(
                args.eingabe, commands=commands, use_ai=use_ai, model=args.model, debug=args.debug
            )
            ui.show_mode_banner(mode)
            ui.handle_results(results)
        else:
            interactive_loop(commands, use_ai=use_ai, model=args.model, debug=args.debug)
    except KeyboardInterrupt:
        ui.console.print("\n[dim]Bis bald![/dim]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
