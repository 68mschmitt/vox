"""Terminal output formatting and display utilities.

POC scope: basic print formatting with ANSI colors.
No TUI framework — just print statements with ANSI escape codes.

Schema reference: design/ARCHITECTURE.md
"""

from __future__ import annotations

import sys


# ---------------------------------------------------------------------------
# ANSI color codes
# ---------------------------------------------------------------------------


class _Colors:
    """ANSI escape codes for terminal colors."""

    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"

    @classmethod
    def enabled(cls) -> bool:
        """Check if the terminal supports colors."""
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    """Wrap text in an ANSI color code if colors are enabled."""
    if _Colors.enabled():
        return f"{code}{text}{_Colors.RESET}"
    return text


# ---------------------------------------------------------------------------
# Public display functions
# ---------------------------------------------------------------------------


def header(text: str) -> None:
    """Print a section header."""
    print()
    print(_c(_Colors.BOLD, text))
    print(_c(_Colors.DIM, "\u2501" * len(text)))


def info(text: str) -> None:
    """Print an info message."""
    print(text)


def success(text: str) -> None:
    """Print a success message."""
    print(_c(_Colors.GREEN, text))


def warning(text: str) -> None:
    """Print a warning message."""
    print(_c(_Colors.YELLOW, f"WARNING: {text}"))


def error(text: str) -> None:
    """Print an error message."""
    print(_c(_Colors.RED, f"ERROR: {text}"), file=sys.stderr)


def dim(text: str) -> None:
    """Print dimmed/secondary text."""
    print(_c(_Colors.DIM, text))


def prompt(text: str) -> str:
    """Display a prompt and read user input."""
    return input(_c(_Colors.CYAN, f"{text} ")).strip()


def prompt_choice(text: str, options: list[str]) -> str:
    """Display a multiple choice prompt.

    Options are displayed as [a], [b], etc.
    Returns the selected option text.
    """
    print(_c(_Colors.BOLD, text))
    labels = "abcdefghijklmnopqrstuvwxyz"
    for i, option in enumerate(options):
        label = labels[i] if i < len(labels) else str(i)
        print(f"  [{label}] {option}")
    while True:
        choice = prompt(">")
        if not choice:
            continue
        # Accept label or index
        idx = labels.find(choice.lower())
        if 0 <= idx < len(options):
            return options[idx]
        # Try numeric
        try:
            idx = int(choice)
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print(
            _c(
                _Colors.DIM,
                f"  Please enter a letter ({labels[0]}-{labels[len(options) - 1]})",
            )
        )


def score_display(label: str, score: float, max_score: float = 10.0) -> None:
    """Display a score with a visual bar."""
    bar_width = 20
    filled = int((score / max_score) * bar_width)
    bar = "\u2588" * filled + "\u2591" * (bar_width - filled)

    if score >= 8.0:
        color = _Colors.GREEN
    elif score >= 5.0:
        color = _Colors.YELLOW
    else:
        color = _Colors.RED

    print(f"  {label:20s} {_c(color, bar)} {score:.1f}/{max_score:.0f}")


def divider() -> None:
    """Print a horizontal divider."""
    print(_c(_Colors.DIM, "\u2500" * 60))
