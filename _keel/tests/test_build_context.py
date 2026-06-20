"""Tests for build_context — the verbatim-compaction script.

The risky paths: section extraction by heading, id lookup, ordering,
and the cache-stable-prefix-first rule.
"""

from __future__ import annotations

from pathlib import Path

from keel.operations import (  # type: ignore[import-not-found]
    _find_id_section,
    _looks_like_id,
    build_context,
    order_sources,
    parse_relevant_sources,
)
from keel.helpers import ProjectLayout  # type: ignore[import-not-found]


# ─── _looks_like_id ──────────────────────────────────────────────────────────


def test_looks_like_id_recognized():
    for s in ("P-1", "P-12", "D-001", "INV-3", "FM-9"):
        assert _looks_like_id(s), s


def test_looks_like_id_rejects_non_ids():
    for s in ("p-1", "P1", "D-", "INV", "Section Name", "1-P"):
        assert not _looks_like_id(s), s


# ─── _find_id_section ────────────────────────────────────────────────────────


def test_find_id_section_matches_titled_heading():
    md = """## D-001 — Some Decision
context here
- date: ...

## D-002 — Other
"""
    out = _find_id_section(md, "D-001")
    assert out is not None
    assert "context here" in out
    assert "D-002" not in out


def test_find_id_section_no_match():
    md = "## D-099\nbody\n"
    assert _find_id_section(md, "D-001") is None


# ─── parse_relevant_sources ──────────────────────────────────────────────────


def test_parse_relevant_sources_extracts_paths_and_subs():
    brief = """# T-001

## Relevant sources
- AGENTS.md
- PRINCIPLES.md: P-1, P-3
- CORE.md: Per-subsystem normative rules
- docs/module-cards/event-log.md

## Acceptance criteria
- ...
"""
    out = parse_relevant_sources(brief)
    assert out == [
        ("AGENTS.md", None),
        ("PRINCIPLES.md", "P-1, P-3"),
        ("CORE.md", "Per-subsystem normative rules"),
        ("docs/module-cards/event-log.md", None),
    ]


def test_parse_relevant_sources_strips_backticks():
    brief = """## Relevant sources
- `PRINCIPLES.md`: `P-1`
- `CORE.md`
"""
    out = parse_relevant_sources(brief)
    assert out == [("PRINCIPLES.md", "P-1"), ("CORE.md", None)]


def test_parse_relevant_sources_empty_when_section_missing():
    assert parse_relevant_sources("# T-001\nno relevant sources section\n") == []


# ─── order_sources ───────────────────────────────────────────────────────────


def test_order_sources_puts_stable_prefix_first():
    sources = [
        ("docs/module-cards/foo.md", None),
        ("COMPONENTS.md", None),
        ("CORE.md", "x"),
        ("AGENTS.md", None),
        ("PRINCIPLES.md", "P-1"),
        ("some/other.md", None),
    ]
    out = order_sources(sources)
    paths = [p for p, _ in out]
    assert paths == [
        "AGENTS.md",
        "PRINCIPLES.md",
        "CORE.md",
        "COMPONENTS.md",
        "docs/module-cards/foo.md",
        "some/other.md",
    ]


def test_order_sources_preserves_within_group_order():
    sources = [
        ("docs/module-cards/b.md", None),
        ("docs/module-cards/a.md", None),
        ("z/late.md", None),
        ("AGENTS.md", None),
    ]
    out = order_sources(sources)
    paths = [p for p, _ in out]
    # AGENTS first; module-cards keep their input order (b before a);
    # then the trailing "other" file.
    assert paths == [
        "AGENTS.md",
        "docs/module-cards/b.md",
        "docs/module-cards/a.md",
        "z/late.md",
    ]


# ─── build_context end-to-end ────────────────────────────────────────────────


def test_build_context_extracts_id_section_and_heading_section(project_layout: Path):
    layout = ProjectLayout.from_root(project_layout)
    # Set up a minimal task with a brief that references P-1 and a CORE heading
    task_dir = layout.tasks_active / "TEST-001-foo"
    task_dir.mkdir()
    (task_dir / "evidence").mkdir()
    (task_dir / "brief.md").write_text(
        "# TEST-001 — foo\n\n"
        "## Relevant sources\n"
        "- AGENTS.md\n"
        "- PRINCIPLES.md: P-1\n"
        "- CORE.md: Per-subsystem normative rules\n"
    )
    (task_dir / "acceptance.yml").write_text("task: TEST-001-foo\nchecks: []\n")

    result = build_context(layout, "TEST-001-foo")
    text = result.text

    # Verbatim presence
    assert "## P-1 — be honest" in text
    assert "No shortcuts." in text
    assert "Authority: full." in text

    # Stable prefix ordering: AGENTS appears before PRINCIPLES appears before CORE
    agents_pos = text.find("From `AGENTS.md`")
    principles_pos = text.find("From `PRINCIPLES.md`")
    core_pos = text.find("From `CORE.md`")
    assert 0 < agents_pos < principles_pos < core_pos


def test_build_context_warns_on_missing_heading(project_layout: Path):
    layout = ProjectLayout.from_root(project_layout)
    task_dir = layout.tasks_active / "TEST-002-bar"
    task_dir.mkdir()
    (task_dir / "evidence").mkdir()
    (task_dir / "brief.md").write_text(
        "# TEST-002\n\n## Relevant sources\n- CORE.md: NonexistentHeading\n"
    )
    (task_dir / "acceptance.yml").write_text("task: TEST-002-bar\n")

    result = build_context(layout, "TEST-002-bar")
    text = result.text
    assert "⚠ build_context" in text
    assert "NonexistentHeading" in text
