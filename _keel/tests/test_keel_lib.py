"""Tests for _keel/scripts/lib/keel.py — the load-bearing helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from keel.errors import (  # type: ignore[import-not-found]
    ProjectNotFound,
    SpecModelError,
)
from keel.helpers import (  # type: ignore[import-not-found]
    ProjectLayout,
    extract_markdown_section,
    find_project_root,
    load_spec_model,
    next_task_number,
    parse_task_id,
)


# ─── find_project_root ───────────────────────────────────────────────────────


def test_find_project_root_walks_up(project_layout: Path, monkeypatch):
    deep = project_layout / "a" / "b" / "c"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    assert find_project_root() == project_layout


def test_find_project_root_fails_cleanly(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ProjectNotFound) as excinfo:
        find_project_root()
    assert "_keel" in str(excinfo.value)


# ─── parse_task_id ───────────────────────────────────────────────────────────


def test_parse_task_id_valid():
    assert parse_task_id("TEST-001-foo-bar") == ("TEST", 1, "foo-bar")
    assert parse_task_id("AB-999-x") == ("AB", 999, "x")
    assert parse_task_id("ORDP-042-event-log-init") == ("ORDP", 42, "event-log-init")


def test_parse_task_id_invalid_returns_none():
    assert parse_task_id("lowercase-001-foo") is None
    assert parse_task_id("TEST-1-foo") is None  # number must be 3+ digits
    assert parse_task_id("TEST-001") is None  # missing slug
    assert parse_task_id("TEST_001_foo") is None  # underscores


# ─── extract_markdown_section ────────────────────────────────────────────────


def test_extract_markdown_section_simple():
    md = """# Top
## Section A
Content A.

## Section B
Content B.
"""
    out = extract_markdown_section(md, "Section A")
    assert out is not None
    assert "Content A." in out
    assert "Content B." not in out
    assert "## Section A" in out


def test_extract_markdown_section_respects_levels():
    md = """## Outer
Body 1
### Inner
Body 2
## Sibling
Body 3
"""
    out = extract_markdown_section(md, "Outer")
    assert out is not None
    # Inner is a subsection of Outer, so should be included.
    assert "Body 2" in out
    # Sibling is at the same level, so should NOT be included.
    assert "Body 3" not in out


def test_extract_markdown_section_fuzzy():
    md = "## D-001 — Some Decision\nbody\n"
    # Fuzzy matching should normalize whitespace/case
    assert extract_markdown_section(md, "D-001 — Some Decision") is not None
    assert extract_markdown_section(md, "  D-001 —  Some Decision  ") is not None


def test_extract_markdown_section_missing():
    md = "## Other\nhi\n"
    assert extract_markdown_section(md, "Missing") is None


# ─── next_task_number ────────────────────────────────────────────────────────


def test_next_task_number_empty(project_layout: Path):
    layout = ProjectLayout.from_root(project_layout)
    assert next_task_number(layout, "TEST") == 1


def test_next_task_number_with_existing(project_layout: Path):
    layout = ProjectLayout.from_root(project_layout)
    (layout.tasks_active / "TEST-001-foo").mkdir()
    (layout.tasks_completed / "TEST-003-bar").mkdir()
    (layout.tasks_blocked / "TEST-007-baz").mkdir()
    # Other prefixes don't affect the count
    (layout.tasks_active / "OTHER-099-x").mkdir()
    assert next_task_number(layout, "TEST") == 8


def test_next_task_number_isolates_by_prefix(project_layout: Path):
    layout = ProjectLayout.from_root(project_layout)
    (layout.tasks_active / "AAA-005-x").mkdir()
    assert next_task_number(layout, "BBB") == 1
    assert next_task_number(layout, "AAA") == 6


# ─── load_spec_model ────────────────────────────────────────────────────────


def test_load_spec_model_validates(project_layout: Path):
    layout = ProjectLayout.from_root(project_layout)
    model = load_spec_model(layout)
    assert model["project_prefix"] == "TEST"


def test_load_spec_model_rejects_missing_field(project_layout: Path):
    import yaml

    layout = ProjectLayout.from_root(project_layout)
    bad = {"project_name": "x"}  # missing required fields
    layout.spec_model.write_text(yaml.safe_dump(bad))
    with pytest.raises(SpecModelError) as excinfo:
        load_spec_model(layout)
    assert "schema validation" in str(excinfo.value)


def test_load_spec_model_rejects_bad_prefix(project_layout: Path):
    import yaml

    layout = ProjectLayout.from_root(project_layout)
    model = load_spec_model(layout)
    model["project_prefix"] = "lowercase"  # violates ^[A-Z]{2,6}$
    layout.spec_model.write_text(yaml.safe_dump(model))
    with pytest.raises(SpecModelError):
        load_spec_model(layout)


def test_load_spec_model_missing_file(tmp_path: Path):
    keel = tmp_path / "_keel"
    keel.mkdir()
    layout = ProjectLayout.from_root(tmp_path)
    with pytest.raises(SpecModelError) as excinfo:
        load_spec_model(layout)
    assert "not found" in str(excinfo.value).lower()
