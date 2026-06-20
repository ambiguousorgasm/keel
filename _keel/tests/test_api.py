"""Tests for the KeelRepo API surface — the Layer 1 integration interface."""

from __future__ import annotations

from pathlib import Path

import pytest

from keel.api import KeelRepo, TaskInfo  # type: ignore[import-not-found]
from keel.errors import (  # type: ignore[import-not-found]
    GovernanceNotFound,
    KeelError,
    TaskNotFound,
)


# ─── construction / discovery ────────────────────────────────────────────────


def test_repo_construct_from_root(project_layout: Path):
    repo = KeelRepo(project_layout)
    assert repo.root == project_layout


def test_repo_rejects_non_keel_dir(tmp_path: Path):
    with pytest.raises(KeelError):
        KeelRepo(tmp_path)


def test_repo_discover_walks_up(project_layout: Path, monkeypatch):
    deep = project_layout / "x" / "y"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    repo = KeelRepo.discover()
    assert repo.root == project_layout


# ─── write operations via the API ────────────────────────────────────────────


def test_repo_create_task_returns_created_task(repo: KeelRepo):
    task = repo.create_task("first-thing")
    assert task.task_id == "TEST-001-first-thing"
    assert task.path.is_dir()
    assert task.brief.is_file()


def test_repo_build_context_returns_result(repo: KeelRepo):
    task = repo.create_task("ctx-task")
    # Give the brief a relevant-sources section
    task.brief.write_text(
        "# t\n\n## Relevant sources\n- AGENTS.md\n- PRINCIPLES.md: P-1\n"
    )
    result = repo.build_context(task.task_id)
    assert result.path.is_file()
    assert "## P-1 — be honest" in result.text
    assert result.sources == 2
    assert result.warnings == []


def test_repo_verify_task_runs_checks(repo: KeelRepo):
    task = repo.create_task("verify-me")
    task.acceptance.write_text(
        "task: TEST-001-verify-me\n"
        "checks:\n"
        "  - name: ok\n    run: 'true'\n"
        "  - name: bad\n    run: 'false'\n"
        "scope_allowlist: []\n"
    )
    result = repo.verify_task(task.task_id)
    assert not result.passed
    names = {r.name for r in result.results}
    assert {"ok", "bad", "scope"} <= names
    assert result.summary_path.is_file()


# ─── read operations ─────────────────────────────────────────────────────────


def test_repo_get_spec_model(repo: KeelRepo):
    model = repo.get_spec_model()
    assert model["project_prefix"] == "TEST"


def test_repo_read_governance(repo: KeelRepo):
    text = repo.read_governance("PRINCIPLES.md")
    assert "P-1" in text


def test_repo_read_governance_missing(repo: KeelRepo):
    with pytest.raises(GovernanceNotFound):
        repo.read_governance("NONEXISTENT.md")


def test_repo_list_governance(repo: KeelRepo):
    docs = repo.list_governance()
    assert "PRINCIPLES.md" in docs
    assert "CORE.md" in docs
    # STATUS.md was not created by the fixture
    assert "STATUS.md" not in docs


def test_repo_list_tasks_empty(repo: KeelRepo):
    assert repo.list_tasks() == []


def test_repo_list_tasks_sorted(repo: KeelRepo):
    repo.create_task("alpha")
    repo.create_task("beta")
    tasks = repo.list_tasks()
    assert [t.task_id for t in tasks] == ["TEST-001-alpha", "TEST-002-beta"]
    assert all(isinstance(t, TaskInfo) for t in tasks)
    assert all(t.state == "active" for t in tasks)


def test_repo_list_tasks_filter_by_state(repo: KeelRepo):
    repo.create_task("active-one")
    # Move a fake completed task into place
    completed = repo.layout.tasks_completed / "TEST-009-done"
    completed.mkdir()
    assert {t.task_id for t in repo.list_tasks("active")} == {"TEST-001-active-one"}
    assert {t.task_id for t in repo.list_tasks("completed")} == {"TEST-009-done"}


def test_repo_list_tasks_bad_state(repo: KeelRepo):
    with pytest.raises(KeelError):
        repo.list_tasks("nonsense")


def test_repo_get_task(repo: KeelRepo):
    repo.create_task("findme")
    info = repo.get_task("TEST-001-findme")
    assert info.slug == "findme"
    assert info.state == "active"


def test_repo_get_task_missing(repo: KeelRepo):
    with pytest.raises(TaskNotFound):
        repo.get_task("TEST-404-ghost")


def test_repo_read_task_file(repo: KeelRepo):
    task = repo.create_task("readme-task")
    content = repo.read_task_file(task.task_id, "brief.md")
    assert "Relevant sources" in content or "Objective" in content


def test_repo_task_info_flags(repo: KeelRepo):
    task = repo.create_task("flags")
    info = repo.get_task(task.task_id)
    assert info.has_plan is False
    assert info.has_handoff is False
    (task.path / "plan.md").write_text("plan")
    assert repo.get_task(task.task_id).has_plan is True
