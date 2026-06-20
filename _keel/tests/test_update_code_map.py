"""Tests for update_code_map — including the glob bug fix from Round 2 smoke test.

Regression target: `core/**` (the form `COMPONENTS.md` produces) must match files
not just directories. We learned this the hard way.
"""

from __future__ import annotations

from pathlib import Path

from keel.operations import (  # type: ignore[import-not-found]
    parse_components,
    render_subsystem_map,
    walk_paths,
)


# ─── parse_components ────────────────────────────────────────────────────────


def test_parse_components_extracts_paths():
    components = """# COMPONENTS

## event_log
- **Path(s):** `backend/event_log/**`
- **Responsibility:** append-only events

## world_state
- **Path(s):** `backend/world_state/**`, `backend/snapshots/**`
- **Owns state:**
"""
    out = parse_components(components)
    assert out == [
        ("event_log", ["backend/event_log/**"]),
        ("world_state", ["backend/world_state/**", "backend/snapshots/**"]),
    ]


def test_parse_components_empty_when_no_paths():
    components = "# COMPONENTS\n\n## thing\n- **Responsibility:** something\n"
    out = parse_components(components)
    assert out == [("thing", [])]


# ─── walk_paths (the glob-normalization fix) ─────────────────────────────────


def test_walk_paths_handles_double_star(tmp_path: Path):
    """Regression: `core/**` should match files at any depth, not just dirs."""
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "a.py").touch()
    (tmp_path / "core" / "sub").mkdir()
    (tmp_path / "core" / "sub" / "b.py").touch()
    (tmp_path / "other.py").touch()

    files = walk_paths(tmp_path, ["core/**"])
    names = sorted(f.name for f in files)
    assert names == ["a.py", "b.py"]


def test_walk_paths_handles_bare_directory(tmp_path: Path):
    """A path without any glob char (e.g. just `core`) should also recurse."""
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "x.py").touch()
    files = walk_paths(tmp_path, ["core"])
    assert len(files) == 1
    assert files[0].name == "x.py"


def test_walk_paths_skips_pycache(tmp_path: Path):
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "real.py").touch()
    (tmp_path / "core" / "__pycache__").mkdir()
    (tmp_path / "core" / "__pycache__" / "real.cpython-311.pyc").touch()

    files = walk_paths(tmp_path, ["core/**"])
    names = [f.name for f in files]
    assert "real.py" in names
    assert all(not n.endswith(".pyc") for n in names)


def test_walk_paths_explicit_glob_unchanged(tmp_path: Path):
    """A specific glob like `core/*.py` should stay as-is and not recurse."""
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "a.py").touch()
    (tmp_path / "core" / "sub").mkdir()
    (tmp_path / "core" / "sub" / "b.py").touch()

    files = walk_paths(tmp_path, ["core/*.py"])
    names = [f.name for f in files]
    assert names == ["a.py"]


# ─── render_subsystem_map ────────────────────────────────────────────────────


def test_render_subsystem_map_empty(tmp_path: Path):
    out = render_subsystem_map("core", [], tmp_path)
    assert "No files matched" in out


def test_render_subsystem_map_groups_by_top(tmp_path: Path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.py").touch()
    files = [tmp_path / "a" / "x.py"]
    out = render_subsystem_map("test", files, tmp_path)
    assert "## `a/`" in out
    assert "`a/x.py`" in out
