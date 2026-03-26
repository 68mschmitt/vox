"""Tests for persona storage — save/load round-trips and listing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from persona_forge.persona.model import Persona
from persona_forge.persona.store import (
    delete_persona,
    list_personas,
    load_persona,
    persona_exists,
    save_persona,
)


class TestSaveLoad:
    def test_save_and_load(self, sample_persona: Persona, tmp_storage: Path):
        """Save a persona and load it back."""
        path = save_persona(sample_persona, base_dir=tmp_storage)
        assert path.exists()
        assert path.name == "state.json"

        loaded = load_persona(sample_persona.id, base_dir=tmp_storage)
        assert loaded.id == sample_persona.id
        assert loaded.name == sample_persona.name
        assert loaded.version == sample_persona.version
        assert loaded.traits.communication_tone.value == "direct and conversational"

    def test_save_creates_exports_dir(self, sample_persona: Persona, tmp_storage: Path):
        """Save should create the exports/ directory."""
        save_persona(sample_persona, base_dir=tmp_storage)
        exports_dir = tmp_storage / sample_persona.id / "exports"
        assert exports_dir.is_dir()

    def test_save_creates_backup(self, sample_persona: Persona, tmp_storage: Path):
        """Second save should create a .bak backup file."""
        save_persona(sample_persona, base_dir=tmp_storage)

        # Modify and save again
        sample_persona.version = 2
        save_persona(sample_persona, base_dir=tmp_storage)

        backup = tmp_storage / sample_persona.id / "state.json.bak"
        assert backup.exists()

        # Backup should have version 1
        with open(backup) as f:
            bak_data = json.load(f)
        assert bak_data["persona"]["version"] == 1

    def test_load_nonexistent_raises(self, tmp_storage: Path):
        """Loading a non-existent persona raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_persona("does-not-exist", base_dir=tmp_storage)

    def test_state_file_structure(self, sample_persona: Persona, tmp_storage: Path):
        """Verify the state file has expected top-level keys."""
        save_persona(sample_persona, base_dir=tmp_storage)
        state_path = tmp_storage / sample_persona.id / "state.json"

        with open(state_path) as f:
            state = json.load(f)

        assert "persona_id" in state
        assert "current_version" in state
        assert "persona" in state
        assert state["persona_id"] == sample_persona.id
        assert state["current_version"] == sample_persona.version


class TestPersonaExists:
    def test_exists_true(self, sample_persona: Persona, tmp_storage: Path):
        save_persona(sample_persona, base_dir=tmp_storage)
        assert persona_exists(sample_persona.id, base_dir=tmp_storage) is True

    def test_exists_false(self, tmp_storage: Path):
        assert persona_exists("nope", base_dir=tmp_storage) is False


class TestListPersonas:
    def test_empty_dir(self, tmp_storage: Path):
        assert list_personas(base_dir=tmp_storage) == []

    def test_lists_saved_personas(self, sample_persona: Persona, tmp_storage: Path):
        save_persona(sample_persona, base_dir=tmp_storage)

        results = list_personas(base_dir=tmp_storage)
        assert len(results) == 1
        assert results[0]["id"] == "eitan-katz"
        assert results[0]["name"] == "Eitan Katz"
        assert results[0]["version"] == 1

    def test_lists_multiple(self, sample_persona: Persona, tmp_storage: Path):
        save_persona(sample_persona, base_dir=tmp_storage)

        p2 = Persona.create("Other Person", "Engineer")
        save_persona(p2, base_dir=tmp_storage)

        results = list_personas(base_dir=tmp_storage)
        assert len(results) == 2


class TestDeletePersona:
    def test_delete(self, sample_persona: Persona, tmp_storage: Path):
        save_persona(sample_persona, base_dir=tmp_storage)
        assert persona_exists(sample_persona.id, base_dir=tmp_storage)

        delete_persona(sample_persona.id, base_dir=tmp_storage)
        assert not persona_exists(sample_persona.id, base_dir=tmp_storage)

    def test_delete_nonexistent_no_error(self, tmp_storage: Path):
        """Deleting a non-existent persona should not raise."""
        delete_persona("nope", base_dir=tmp_storage)
