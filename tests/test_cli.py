"""Tests for the CLI entry point."""

from __future__ import annotations

from persona_forge.main import _build_parser, main


class TestParser:
    def test_no_command_returns_1(self):
        """No command shows help and returns 1."""
        result = main([])
        assert result == 1

    def test_version_flag(self, capsys):
        """--version prints version and exits."""
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_new_parser(self):
        """'new' subcommand parses correctly."""
        parser = _build_parser()
        args = parser.parse_args(["new", "--name", "Test User"])
        assert args.command == "new"
        assert args.name == "Test User"

    def test_calibrate_parser(self):
        """'calibrate' subcommand parses correctly."""
        parser = _build_parser()
        args = parser.parse_args(["calibrate", "test-user", "--rounds", "2"])
        assert args.command == "calibrate"
        assert args.persona_id == "test-user"
        assert args.rounds == 2

    def test_export_parser(self):
        """'export' subcommand parses correctly."""
        parser = _build_parser()
        args = parser.parse_args(["export", "test-user", "--format", "full"])
        assert args.command == "export"
        assert args.persona_id == "test-user"
        assert args.format == "full"

    def test_global_options(self):
        """Global options (provider, model, verbose) are parsed."""
        parser = _build_parser()
        args = parser.parse_args(
            ["--provider", "anthropic", "--model", "claude-3-opus", "--verbose", "new"]
        )
        assert args.provider == "anthropic"
        assert args.model == "claude-3-opus"
        assert args.verbose is True


class TestCmdExport:
    def test_export_nonexistent_persona(self, tmp_path, monkeypatch):
        """Exporting a non-existent persona returns error."""
        monkeypatch.setattr("persona_forge.persona.store.PERSONAS_DIR", tmp_path)
        result = main(["export", "nonexistent"])
        assert result == 1

    def test_export_existing_persona(
        self, sample_persona, tmp_storage, capsys, monkeypatch
    ):
        """Exporting an existing persona prints the system prompt."""
        from persona_forge.persona.store import save_persona

        save_persona(sample_persona, base_dir=tmp_storage)

        # Monkeypatch PERSONAS_DIR in the store module where it's actually used
        monkeypatch.setattr("persona_forge.persona.store.PERSONAS_DIR", tmp_storage)

        result = main(["export", "eitan-katz"])
        assert result == 0

        captured = capsys.readouterr()
        assert "Eitan Katz" in captured.out
        assert "Senior Software Engineer" in captured.out
