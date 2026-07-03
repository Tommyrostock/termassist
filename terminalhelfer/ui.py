"""Terminal UI: colored suggestion list, arrow-key selection, and the
execute/copy/edit flow. Uses questionary for interaction and rich for colored
output, as requested.
"""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from typing import Any

import questionary
from questionary import Choice
from rich.console import Console

try:
    import pyperclip
except ImportError:  # pragma: no cover - pyperclip is a declared dependency
    pyperclip = None

console = Console()

EDIT_CHOICE = "__EDIT__"
CANCEL_CHOICE = "__CANCEL__"

# Commands containing any of these words get an extra warning before execution.
DANGER_WORDS = ["sudo", "rm", "dd", "mkfs", "shutdown", "reboot", "poweroff"]

PLACEHOLDER_LABELS = {
    "DATEI": "Dateiname",
    "ZIEL": "Ziel (Pfad, Adresse o.ae.)",
    "PAKETNAME": "Paketname",
    "PID": "Prozess-ID",
    "DIENST": "Dienst-/Programmname",
    "BENUTZER": "Benutzername",
    "GRUPPE": "Gruppenname",
    "NACHRICHT": "Nachricht",
    "MUSTER": "Suchmuster",
    "BEFEHL": "Befehl",
    "VARIABLE": "Variablenname",
    "WERT": "Wert",
}
PLACEHOLDER_PATTERN = re.compile(r"\b(" + "|".join(PLACEHOLDER_LABELS) + r")\b")

_CHOICE_STYLE = questionary.Style(
    [
        ("cmd", "bold fg:#00d7af"),
        ("desc", "fg:#d0d0d0"),
        ("special", "fg:#888888 italic"),
    ]
)


def show_mode_banner(mode: str) -> None:
    """Print a one-time hint about whether AI or offline fallback mode is active."""
    if mode == "ki":
        console.print("[bold green]🤖 KI-Modus aktiv[/bold green] (lokales Ollama-Modell erkannt)\n")
    else:
        console.print(
            "[bold yellow]📴 Offline-Modus aktiv[/bold yellow] "
            "(kein Ollama gefunden, nutze Fuzzy-Suche)\n"
        )


def ask_query() -> str | None:
    """Prompt the user for their next request in the interactive loop."""
    return questionary.text("Was moechtest du tun?", qmark="🔎").ask()


def choose_command(results: list[dict[str, Any]]) -> dict[str, Any] | str | None:
    """Show an arrow-key list of suggestions plus edit/cancel options.

    Returns the chosen ``{"cmd", "kurz"}`` dict, the ``EDIT_CHOICE`` /
    ``CANCEL_CHOICE`` sentinel, or ``None`` if the user aborted (Strg+C).
    """
    choices = []
    for entry in results:
        title = [
            ("class:cmd", entry["cmd"]),
            ("", "  —  "),
            ("class:desc", entry["kurz"]),
        ]
        choices.append(Choice(title=title, value=entry))

    choices.append(Choice(title=[("class:special", "✏️  Selbst eingeben / bearbeiten")], value=EDIT_CHOICE))
    choices.append(Choice(title=[("class:special", "❌ Abbrechen")], value=CANCEL_CHOICE))

    return questionary.select(
        "Welcher Befehl passt?",
        choices=choices,
        style=_CHOICE_STYLE,
    ).ask()


def edit_command(initial: str = "") -> str | None:
    """Let the user type or edit a raw command string."""
    return questionary.text("Befehl eingeben:", default=initial).ask()


def resolve_placeholders(cmd: str) -> str:
    """Ask the user for a value for every placeholder token in the command
    (e.g. DATEI, ZIEL, PID) and substitute it into the command string.
    """
    tokens = list(dict.fromkeys(PLACEHOLDER_PATTERN.findall(cmd)))  # unique, order-preserving
    resolved = cmd
    for token in tokens:
        label = PLACEHOLDER_LABELS.get(token, token)
        answer = questionary.text(f"Wert fuer {label} ({token}):").ask()
        resolved = re.sub(rf"\b{token}\b", answer or "", resolved)
    return resolved


def _is_dangerous(cmd: str) -> bool:
    return any(re.search(rf"\b{re.escape(word)}\b", cmd) for word in DANGER_WORDS)


def _copy_to_clipboard(cmd: str) -> None:
    if pyperclip is None:
        console.print(
            "[bold red]⚠️ Zwischenablage nicht verfuegbar[/bold red] "
            "(pyperclip ist nicht installiert)."
        )
        return
    try:
        pyperclip.copy(cmd)
        console.print("[green]✅ In die Zwischenablage kopiert.[/green]")
    except Exception:  # pragma: no cover - depends on OS clipboard backend
        console.print(
            "[bold red]⚠️ Konnte nicht in die Zwischenablage kopieren.[/bold red] "
            "Das kann z.B. in einer reinen SSH-Sitzung ohne X11/Wayland vorkommen."
        )


def _run(cmd: str) -> None:
    console.print(f"[dim]$ {cmd}[/dim]")
    try:
        subprocess.run(cmd, shell=True, check=False)
    except OSError as exc:
        console.print(f"[bold red]Fehler beim Ausfuehren:[/bold red] {exc}")


def _wants_yes(answer: str | None) -> bool:
    return (answer or "").strip().lower() in ("j", "ja", "y", "yes")


def confirm_and_execute(cmd: str) -> None:
    """Show the final command, warn if dangerous, and ask before running or
    copying it. Never executes anything without an explicit confirmation.
    """
    console.print()
    console.print(f"[bold]Vollstaendiger Befehl:[/bold] [bold cyan]{cmd}[/bold cyan]")

    if _is_dangerous(cmd):
        console.print(
            "[bold white on red] ⚠️  Dieser Befehl kann Daten loeschen oder das System neu starten. [/bold white on red]"
        )

    run_answer = questionary.text("Befehl ausfuehren? [j/N]").ask()
    if _wants_yes(run_answer):
        _run(cmd)
        return

    copy_answer = questionary.text("Stattdessen in die Zwischenablage kopieren? [j/N]").ask()
    if _wants_yes(copy_answer):
        _copy_to_clipboard(cmd)
        return

    console.print("[dim]Nichts ausgefuehrt.[/dim]")


def handle_results(results: list[dict[str, Any]]) -> None:
    """Show the suggestion list, handle selection/edit/cancel, and act on it."""
    if not results:
        console.print("[yellow]Keine passenden Befehle gefunden.[/yellow]")
        cmd = edit_command()
        if cmd:
            confirm_and_execute(resolve_placeholders(cmd))
        else:
            console.print("[dim]Abgebrochen.[/dim]")
        return

    selected = choose_command(results)
    if selected is None or selected == CANCEL_CHOICE:
        console.print("[dim]Abgebrochen.[/dim]")
        return

    if selected == EDIT_CHOICE:
        cmd = edit_command()
        if not cmd:
            console.print("[dim]Abgebrochen.[/dim]")
            return
    else:
        cmd = selected["cmd"]

    confirm_and_execute(resolve_placeholders(cmd))


def print_command_database(commands: list[dict[str, Any]]) -> None:
    """Print the full command database grouped by category (for --list)."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in commands:
        grouped[entry.get("kategorie", "Sonstiges")].append(entry)

    for kategorie in sorted(grouped):
        console.print(f"\n[bold underline]{kategorie}[/bold underline]")
        for entry in grouped[kategorie]:
            console.print(f"  [bold cyan]{entry['cmd']}[/bold cyan]  —  {entry['kurz']}")
