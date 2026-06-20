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


# ─── Agent Skills bridge: manual_only / export / sync / lint ─────────────────

from keel.skills import (  # noqa: E402
    export_agent_skills,
    lint_skills,
    render_agent_skill,
    render_catalog,
)


def _make_skill_full(skills_dir, sid, *, name=None, desc="does a thing", body="B",
                     manual_only=None, export=None):
    folder = skills_dir / sid
    folder.mkdir(parents=True)
    fm = [f"name: {name or sid}", f"description: {desc}", "version: 1.0"]
    if manual_only is not None:
        fm.append(f"manual_only: {str(manual_only).lower()}")
    if export is not None:
        fm.append(f"export: {str(export).lower()}")
    (folder / "SKILL.md").write_text("---\n" + "\n".join(fm) + "\n---\n\n" + body + "\n")
    return folder


def test_manual_only_and_export_parsed(tmp_path):
    skills = tmp_path / "skills"
    _make_skill_full(skills, "dev-release", manual_only=True)
    _make_skill_full(skills, "dev-demo", export=False)
    infos = {i.id: i for i in list_skills(skills)}
    assert infos["dev-release"].manual_only is True
    assert infos["dev-release"].export is True
    assert infos["dev-demo"].export is False
    assert infos["dev-demo"].manual_only is False


def test_non_bool_flag_rejected(tmp_path):
    skills = tmp_path / "skills"
    folder = skills / "dev-x"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        "---\nname: dev-x\ndescription: d\nmanual_only: yes-please\n---\n\nb\n"
    )
    with pytest.raises(SkillValidationError):
        list_skills(skills)


def test_render_agent_skill_uses_portable_frontmatter(tmp_path):
    skills = tmp_path / "skills"
    _make_skill_full(skills, "dev-release", desc="ship it", manual_only=True, body="RUN")
    mirror = render_agent_skill(load_skill(skills, "dev-release"))
    assert "name: dev-release" in mirror          # folder-name == name (Agent Skills convention)
    assert "description: >" in mirror
    assert "ship it" in mirror
    assert "disable-model-invocation: true" in mirror  # manual-only safeguard
    assert "GENERATED from _keel/skills/" in mirror     # do-not-edit banner
    assert mirror.rstrip().endswith("RUN")              # body carried through


def test_export_excludes_non_exported_and_copies_bundled(tmp_path):
    skills = tmp_path / "skills"
    a = _make_skill_full(skills, "dev-a")
    (a / "references").mkdir()
    (a / "references" / "notes.md").write_text("ref")
    _make_skill_full(skills, "dev-demo", export=False)
    agents = tmp_path / ".agents" / "skills"
    result = export_agent_skills(skills, agents)
    assert result["written"] == ["dev-a"]
    assert (agents / "dev-a" / "SKILL.md").is_file()
    assert (agents / "dev-a" / "references" / "notes.md").read_text() == "ref"
    assert not (agents / "dev-demo").exists()


def test_sync_removes_only_managed_stale_mirrors(tmp_path):
    skills = tmp_path / "skills"
    _make_skill_full(skills, "dev-a")
    agents = tmp_path / ".agents" / "skills"
    export_agent_skills(skills, agents)
    # a hand-authored, non-KEEL skill the user added directly
    hand = agents / "user-own"
    hand.mkdir(parents=True)
    (hand / "SKILL.md").write_text("---\nname: user-own\ndescription: mine\n---\n\nx\n")
    # delete the canonical dev-a, re-sync
    import shutil
    shutil.rmtree(skills / "dev-a")
    result = export_agent_skills(skills, agents)
    assert "dev-a" in result["removed"]          # KEEL-managed stale mirror removed
    assert (agents / "user-own").exists()        # hand-authored skill preserved


def test_lint_clean_and_drift(tmp_path):
    skills = tmp_path / "skills"
    _make_skill_full(skills, "dev-a")
    agents = tmp_path / ".agents" / "skills"
    # before sync: missing mirror is a problem
    assert any("sync" in p for p in lint_skills(skills, agents))
    export_agent_skills(skills, agents)
    assert lint_skills(skills, agents) == []      # clean after sync
    # edit canonical body → mirror now drifted
    (skills / "dev-a" / "SKILL.md").write_text(
        "---\nname: dev-a\ndescription: changed\n---\n\nNEW\n"
    )
    assert any("out of date" in p for p in lint_skills(skills, agents))


def test_lint_flags_manual_only_missing_safeguard(tmp_path):
    skills = tmp_path / "skills"
    _make_skill_full(skills, "dev-release", manual_only=True)
    agents = tmp_path / ".agents" / "skills"
    export_agent_skills(skills, agents)
    # tamper: strip the safeguard out of the mirror
    mp = agents / "dev-release" / "SKILL.md"
    mp.write_text(mp.read_text().replace("disable-model-invocation: true", ""))
    problems = lint_skills(skills, agents)
    assert any("safeguard" in p or "out of date" in p for p in problems)


def test_repo_sync_and_lint_end_to_end(repo: KeelRepo):
    result = repo.sync_agent_skills()
    assert "dev-release" in result["written"]
    assert "example-csv-clean" not in result["written"]   # export:false demo
    assert repo.layout.agents_catalog.is_file()
    rel = repo.layout.agents_skills / "dev-release" / "SKILL.md"
    assert "disable-model-invocation: true" in rel.read_text()
    assert repo.lint_skills() == []


def test_catalog_marks_manual_only(repo: KeelRepo):
    repo.sync_agent_skills()
    cat = repo.layout.agents_catalog.read_text()
    assert "dev-release" in cat and "manual-only" in cat
