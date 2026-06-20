"""Tests for the KEEL skills system."""

from __future__ import annotations

from pathlib import Path

import pytest

from keel.api import KeelRepo  # type: ignore[import-not-found]
from keel.errors import (  # type: ignore[import-not-found]
    SkillExists,
    SkillNotFound,
    SkillValidationError,
)
from keel.skills import (  # type: ignore[import-not-found]
    list_skills,
    load_skill,
    parse_frontmatter,
)


# ─── frontmatter parsing ─────────────────────────────────────────────────────


def test_parse_frontmatter_basic():
    text = "---\nname: X\ndescription: does a thing\n---\n\nbody here\n"
    meta, body = parse_frontmatter(text)
    assert meta["name"] == "X"
    assert meta["description"] == "does a thing"
    assert body.strip() == "body here"


def test_parse_frontmatter_missing_block():
    with pytest.raises(SkillValidationError):
        parse_frontmatter("# no frontmatter\nbody\n")


def test_parse_frontmatter_bad_yaml():
    with pytest.raises(SkillValidationError):
        parse_frontmatter("---\nname: [unclosed\n---\nbody\n")


def test_parse_frontmatter_non_mapping():
    with pytest.raises(SkillValidationError):
        parse_frontmatter("---\n- just\n- a\n- list\n---\nbody\n")


# ─── discovery & loading via helpers ─────────────────────────────────────────


def _make_skill(skills_dir: Path, sid: str, *, name="N", desc="d", body="b"):
    folder = skills_dir / sid
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {desc}\nversion: 1.2\n---\n\n{body}\n"
    )
    return folder


def test_list_skills_empty(tmp_path: Path):
    assert list_skills(tmp_path / "nope") == []


def test_list_skills_finds_folders(tmp_path: Path):
    skills = tmp_path / "skills"
    skills.mkdir()
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    # A loose file and a non-skill folder should be ignored.
    (skills / "README.md").write_text("not a skill")
    (skills / "notaskill").mkdir()
    infos = list_skills(skills)
    assert [i.id for i in infos] == ["alpha", "beta"]
    assert infos[0].version == "1.2"


def test_load_skill_returns_body(tmp_path: Path):
    skills = tmp_path / "skills"
    skills.mkdir()
    _make_skill(skills, "alpha", body="real instructions")
    skill = load_skill(skills, "alpha")
    assert "real instructions" in skill.body
    assert skill.render() == skill.body


def test_load_skill_missing(tmp_path: Path):
    skills = tmp_path / "skills"
    skills.mkdir()
    with pytest.raises(SkillNotFound):
        load_skill(skills, "ghost")


def test_validation_requires_description(tmp_path: Path):
    skills = tmp_path / "skills"
    folder = skills / "bad"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text("---\nname: X\n---\nbody\n")
    with pytest.raises(SkillValidationError):
        load_skill(skills, "bad")


def test_validation_id_mismatch(tmp_path: Path):
    skills = tmp_path / "skills"
    folder = skills / "alpha"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        "---\nname: X\ndescription: d\nid: beta\n---\nbody\n"
    )
    with pytest.raises(SkillValidationError):
        load_skill(skills, "alpha")


def test_bundled_files_enumerated(tmp_path: Path):
    skills = tmp_path / "skills"
    folder = _make_skill(skills, "withfiles")
    (folder / "scripts").mkdir()
    (folder / "scripts" / "h.py").write_text("x = 1")
    (folder / "ref.md").write_text("ref")
    skill = load_skill(skills, "withfiles")
    assert "ref.md" in skill.bundled_files
    assert "scripts/h.py" in skill.bundled_files
    assert "SKILL.md" not in skill.bundled_files


# ─── KeelRepo skills API ─────────────────────────────────────────────────────


def test_repo_list_skills(repo: KeelRepo):
    # The fixture copies the real _keel/, so the builtin dev-* skills are present.
    infos = repo.list_skills()
    ids = {i.id for i in infos}
    assert "dev-plan-task" in ids
    assert "dev-review-diff" in ids


def test_repo_get_skill(repo: KeelRepo):
    skill = repo.get_skill("dev-plan-task")
    assert skill.name
    assert skill.description
    assert "plan" in skill.body.lower()


def test_repo_skills_index(repo: KeelRepo):
    index = repo.skills_index()
    assert "dev-plan-task" in index
    assert index.startswith("# Available skills")


def test_repo_search_skills(repo: KeelRepo):
    hits = repo.search_skills("reviewer")
    assert any(i.id == "dev-review-diff" for i in hits)


def test_repo_load_skill_file(repo: KeelRepo):
    # The example skill ships bundled files.
    text = repo.load_skill_file("example-csv-clean", "references/rules.md")
    assert "cleaning conventions" in text.lower()


def test_repo_load_skill_file_traversal_blocked(repo: KeelRepo):
    with pytest.raises(SkillNotFound):
        repo.load_skill_file("example-csv-clean", "../../../etc/passwd")


def test_repo_create_skill(repo: KeelRepo):
    skill = repo.create_skill(
        "my-new-skill", name="My New", description="Does a thing. Use when needed."
    )
    assert skill.id == "my-new-skill"
    assert (skill.path / "SKILL.md").is_file()
    # And it's now discoverable
    assert any(i.id == "my-new-skill" for i in repo.list_skills())


def test_repo_create_skill_rejects_bad_id(repo: KeelRepo):
    with pytest.raises(SkillValidationError):
        repo.create_skill("Bad Id")


def test_repo_create_skill_refuses_overwrite(repo: KeelRepo):
    repo.create_skill("dup", description="x")
    with pytest.raises(SkillExists):
        repo.create_skill("dup", description="x")


def test_repo_create_skill_with_colon_name(repo: KeelRepo):
    # A name with a colon must not break the generated YAML frontmatter.
    skill = repo.create_skill(
        "colon-name", name="Thing: A Demo", description="x. Use when y."
    )
    reloaded = repo.get_skill("colon-name")
    assert reloaded.name == "Thing: A Demo"


def test_explain_clear_is_a_builtin_skill(repo: KeelRepo):
    ids = {i.id for i in repo.list_skills()}
    assert "explain-clear" in ids


def test_explain_clear_loads_with_reference(repo: KeelRepo):
    skill = repo.get_skill("explain-clear")
    assert "comprehension modifier" in skill.body.lower()
    assert "references/modes.md" in skill.bundled_files
    # the two load-bearing rules must be present
    assert "don't restart from beginner" in skill.body.lower() or \
           "do not restart from beginner" in skill.body.lower()
    assert "missing link" in skill.body.lower()
    # and the bundled reference is readable
    ref = repo.load_skill_file("explain-clear", "references/modes.md")
    assert "why does this exist" in ref.lower()
