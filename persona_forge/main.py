"""CLI entry point for Persona Forge.

POC scope: three commands -- new, calibrate, export.
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
        choices=["anthropic", "bedrock", "openai", "ollama"],
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
        help="Override max rounds (default: 1 for POC)",
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
    """Handle the 'new' command -- create a persona via seed interview."""
    from persona_forge.llm import create_provider
    from persona_forge.persona.store import save_persona
    from persona_forge.seed.generator import generate_persona_from_seed
    from persona_forge.seed.interview import run_interview
    from persona_forge.ui.display import divider, error, info, success

    try:
        provider = create_provider(
            provider_name=args.provider,
            model=args.model,
        )
    except ValueError as e:
        error(str(e))
        return 1

    try:
        # Run the interactive interview
        seed_data = run_interview(
            provider=provider,
            name=args.name,
        )

        # Generate persona from seed
        persona = generate_persona_from_seed(seed_data, provider)

        # Save to disk
        state_path = save_persona(persona)

        divider()
        success(f'Persona "{persona.name}" created (v{persona.version})')
        info(f"Stored at: {state_path}")
        info("")
        info(f"Next step: Run `persona-forge calibrate {persona.id}` to refine.")
        divider()

    except KeyboardInterrupt:
        info("\n\nInterrupted. No persona saved.")
        return 1
    except Exception as e:
        error(f"Failed to create persona: {e}")
        return 1

    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    """Handle the 'calibrate' command -- run calibration loop."""
    from persona_forge.calibrate.loop import run_calibration
    from persona_forge.llm import create_provider
    from persona_forge.persona.store import load_persona
    from persona_forge.ui.display import error

    try:
        provider = create_provider(
            provider_name=args.provider,
            model=args.model,
        )
    except ValueError as e:
        error(str(e))
        return 1

    try:
        persona = load_persona(args.persona_id)
    except FileNotFoundError:
        error(f"Persona '{args.persona_id}' not found.")
        error(
            "Run `persona-forge list` to see available personas, or `persona-forge new` to create one."
        )
        return 1

    max_rounds = args.rounds or 1  # POC: single round

    try:
        run_calibration(
            persona=persona,
            provider=provider,
            max_rounds=max_rounds,
        )
    except KeyboardInterrupt:
        from persona_forge.ui.display import info

        info("\n\nCalibration interrupted. Progress from completed rounds is saved.")
        return 1
    except Exception as e:
        error(f"Calibration failed: {e}")
        return 1

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Handle the 'export' command -- render persona as system prompt."""
    from persona_forge.export.renderer import render_full
    from persona_forge.persona.store import load_persona
    from persona_forge.ui.display import divider, error, info, success

    try:
        persona = load_persona(args.persona_id)
    except FileNotFoundError:
        error(f"Persona '{args.persona_id}' not found.")
        return 1

    fmt = args.format

    if fmt != "full":
        error(f"Format '{fmt}' not yet implemented. POC supports 'full' only.")
        return 1

    # Render
    output = render_full(persona, exemplars=None)

    divider()
    info(f"Persona: {persona.name} (v{persona.version})")
    info(f"Format: {fmt}")
    divider()
    print()
    print(output)
    print()
    divider()

    # Token estimate (rough: ~4 chars per token)
    token_estimate = len(output) // 4
    success(f"Exported ({token_estimate} estimated tokens)")
    info(f"\nPaste this into your AI coding tool's system prompt configuration.")

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
