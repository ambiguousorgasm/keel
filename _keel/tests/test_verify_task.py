"""Tests for verify_task — scope enforcement and check execution."""

from __future__ import annotations

from pathlib import Path

from keel.operations import (  # type: ignore[import-not-found]
    check_scenarios,
    check_scope,
    run_check,
)
from keel.helpers import ProjectLayout  # type: ignore[import-not-found]


# ─── run_check ───────────────────────────────────────────────────────────────


def test_run_check_pass(tmp_path: Path):
    result = run_check("ok", "true", tmp_path)
    assert result.passed
    assert result.returncode == 0


def test_run_check_fail_captures_output(tmp_path: Path):
    result = run_check("nope", "echo errmsg && false", tmp_path)
    assert not result.passed
    assert result.returncode == 1
    assert "errmsg" in result.stdout


def test_run_check_captures_stderr(tmp_path: Path):
    result = run_check("err", "echo bad >&2 && exit 2", tmp_path)
    assert not result.passed
    assert result.returncode == 2
    assert "bad" in result.stderr


# ─── check_scope ─────────────────────────────────────────────────────────────


def test_check_scope_empty_allowlist_passes(project_layout: Path):
    layout = ProjectLayout.from_root(project_layout)
    result = check_scope(layout, [])
    assert result.passed


def test_check_scope_passes_when_not_a_git_repo(project_layout: Path):
    """In a non-git directory, git diff fails and scope check skips gracefully."""
    layout = ProjectLayout.from_root(project_layout)
    result = check_scope(layout, ["core/**"])
    # Without git diff, scope check should skip rather than crash
    assert result.passed


# ─── check_scenarios ─────────────────────────────────────────────────────────


def test_check_scenarios_empty_passes(project_layout: Path):
    result = check_scenarios(project_layout, [])
    assert result.passed
    assert "no scenarios_required" in result.stdout
