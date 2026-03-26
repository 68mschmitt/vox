"""Persona persistence — save/load JSON files.

POC scope: single JSON file per persona, no versioning.
Atomic writes (write to temp, rename). Backup before overwrite.

Directory structure:
    personas/
    +-- eitan-katz/
    |   +-- state.json
    |   +-- exports/
    +-- another-persona/
        +-- state.json
        +-- exports/

Schema reference: design/DATA-MODEL.md
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from persona_forge.config import PERSONAS_DIR
from persona_forge.persona.model import Persona


def _persona_dir(persona_id: str, base_dir: Path | None = None) -> Path:
    """Return the directory for a given persona."""
    base = base_dir or PERSONAS_DIR
    return base / persona_id


def _state_path(persona_id: str, base_dir: Path | None = None) -> Path:
    """Return the state.json path for a given persona."""
    return _persona_dir(persona_id, base_dir) / "state.json"


def _exports_dir(persona_id: str, base_dir: Path | None = None) -> Path:
    """Return the exports/ directory for a given persona."""
    return _persona_dir(persona_id, base_dir) / "exports"


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically: write to temp file, then rename.

    Creates a backup of the existing file before overwriting.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing file
    if path.exists():
        backup = path.with_suffix(".json.bak")
        shutil.copy2(path, backup)

    # Write to temp file in the same directory, then rename
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp", prefix=".state-")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        Path(tmp_path).replace(path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def save_persona(persona: Persona, base_dir: Path | None = None) -> Path:
    """Save a persona to disk as JSON.

    POC scope: stores the persona directly as a flat JSON file.
    No versioning, sessions, or golden exemplars yet.

    Returns the path to the state file.
    """
    state_path = _state_path(persona.id, base_dir)

    # Ensure exports dir exists too
    _exports_dir(persona.id, base_dir).mkdir(parents=True, exist_ok=True)

    state = {
        "persona_id": persona.id,
        "current_version": persona.version,
        "persona": persona.to_dict(),
    }

    _atomic_write(state_path, state)
    return state_path


def load_persona(persona_id: str, base_dir: Path | None = None) -> Persona:
    """Load a persona from disk.

    Raises FileNotFoundError if the persona doesn't exist.
    """
    state_path = _state_path(persona_id, base_dir)

    if not state_path.exists():
        raise FileNotFoundError(f"Persona '{persona_id}' not found at {state_path}")

    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    return Persona.from_dict(state["persona"])


def persona_exists(persona_id: str, base_dir: Path | None = None) -> bool:
    """Check if a persona exists on disk."""
    return _state_path(persona_id, base_dir).exists()


def list_personas(base_dir: Path | None = None) -> list[dict[str, Any]]:
    """List all personas in the storage directory.

    Returns a list of dicts with basic info:
    [{"id": "...", "name": "...", "version": N, "updated_at": "..."}]
    """
    base = base_dir or PERSONAS_DIR
    if not base.exists():
        return []

    results = []
    for persona_dir in sorted(base.iterdir()):
        state_path = persona_dir / "state.json"
        if not state_path.is_file():
            continue

        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            p = state["persona"]
            results.append(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "version": p.get("version", 1),
                    "updated_at": p.get("updated_at", ""),
                }
            )
        except (json.JSONDecodeError, KeyError):
            continue

    return results


def delete_persona(persona_id: str, base_dir: Path | None = None) -> None:
    """Delete a persona and all its data from disk."""
    pdir = _persona_dir(persona_id, base_dir)
    if pdir.exists():
        shutil.rmtree(pdir)
