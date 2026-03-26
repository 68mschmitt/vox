"""CLI entry point for Persona Forge.

POC scope: three commands — new, calibrate, export.
Uses argparse (stdlib, no dependency).

Schema reference: design/CLI-DESIGN.md
"""

from __future__ import annotations

import argparse
import sys

from persona_forge import __version__


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="persona-forge",
        description="Generate, calibrate, and export AI personas for AI coding assistants.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"persona-forge {__version__}",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai", "ollama"],
        default=None,
        help="LLM provider (default: anthropic)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Specific model override",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show LLM prompts and raw responses",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- new ---
    new_parser = subparsers.add_parser(
        "new",
        help="Create a new persona via structured interview",
    )
    new_parser.add_argument(
        "--name",
        help="Persona name (prompted interactively if not provided)",
    )

    # --- calibrate ---
    cal_parser = subparsers.add_parser(
        "calibrate",
        help="Run calibration loop on an existing persona",
    )
    cal_parser.add_argument(
        "persona_id",
        help="Persona ID (slug) to calibrate",
    )
    cal_parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Override max rounds (default: 4)",
    )
    cal_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume the most recent incomplete session",
    )

    # --- export ---
    exp_parser = subparsers.add_parser(
        "export",
        help="Render persona as a deployable system prompt",
    )
    exp_parser.add_argument(
        "persona_id",
        help="Persona ID (slug) to export",
    )
    exp_parser.add_argument(
        "--version",
        type=int,
        default=None,
        dest="persona_version",
        help="Specific version to export (default: current)",
    )
    exp_parser.add_argument(
        "--format",
        choices=["full", "compact", "oneliner"],
        default="full",
        help="Export format (default: full)",
    )

    return parser


def cmd_new(args: argparse.Namespace) -> int:
    """Handle the 'new' command — create a persona via seed interview."""
    print("persona-forge new: not yet implemented")
    print("This will run the structured interview and generate a first-draft persona.")
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    """Handle the 'calibrate' command — run calibration loop."""
    print(f"persona-forge calibrate {args.persona_id}: not yet implemented")
    print("This will run the calibration loop with Q&A evaluation.")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Handle the 'export' command — render persona as system prompt."""
    print(f"persona-forge export {args.persona_id}: not yet implemented")
    print("This will render the persona as a deployable system prompt.")
    return 0


_COMMANDS = {
    "new": cmd_new,
    "calibrate": cmd_calibrate,
    "export": cmd_export,
}


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
