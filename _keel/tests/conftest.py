"""Shared fixtures and path setup for KEEL's own tests.

Run KEEL's tests from the repo containing _keel/ with:

    pytest _keel/tests/
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

# Make the `keel` package importable.
KEEL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = KEEL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def minimal_spec_model() -> dict:
    """A spec_model that passes schema validation."""
    return {
        "project_name": "Test Project",
        "project_prefix": "TEST",
        "purpose": "A minimal project for testing.",
        "tech_stack": {"language": "python"},
        "subsystems": [
            {
                "name": "core",
                "responsibility": "do the thing",
                "owns_state": ["core.state"],
                "must_not_mutate": [],
                "allowed_deps": [],
                "forbidden_deps": [],
            }
        ],
        "invariants": [{"id": "INV-1", "statement": "things work"}],
        "failure_modes": [],
        "phases": [{"id": "P0", "name": "foundation"}],
    }


@pytest.fixture
def project_layout(tmp_path: Path, minimal_spec_model: dict) -> Path:
    """Build a minimal project rooted at tmp_path with a usable _keel/."""
    import yaml

    keel_dst = tmp_path / "_keel"
    shutil.copytree(KEEL_DIR, keel_dst)
    (keel_dst / "spec_model.yml").write_text(yaml.safe_dump(minimal_spec_model))

    (tmp_path / "AGENTS.md").write_text("# AGENTS\nbase contract.\n")
    (tmp_path / "PRINCIPLES.md").write_text(
        "# PRINCIPLES\n\n## P-1 — be honest\nNo shortcuts.\n"
    )
    (tmp_path / "CORE.md").write_text(
        "# CORE\n\n## Per-subsystem normative rules\n### core\nAuthority: full.\n"
    )
    (tmp_path / "COMPONENTS.md").write_text(
        "# COMPONENTS\n\n## core\n- **Path(s):** `core/**`\n"
    )

    for sub in ("active", "completed", "blocked"):
        (tmp_path / "tasks" / sub).mkdir(parents=True)

    return tmp_path


@pytest.fixture
def repo(project_layout: Path):
    """A KeelRepo bound to the minimal project."""
    from keel.api import KeelRepo

    return KeelRepo(project_layout)
