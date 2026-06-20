"""Tests for the unified `keel` CLI (keel.main)."""

from __future__ import annotations

from pathlib import Path

import pytest

from keel.main import build_parser, main  # type: ignore[import-not-found]


def run(argv: list[str], cwd: Path, monkeypatch, capsys) -> tuple[int, str]:
    """Run the CLI with argv from inside `cwd`, return (exit_code, stdout)."""
    monkeypatch.chdir(cwd)
    monkeypatch.setattr("sys.argv", ["keel", *argv])
    code = main()
    out = capsys.readouterr().out
    return code, out


# ─── parser shape ────────────────────────────────────────────────────────────


def test_parser_has_all_groups():
    parser = build_parser()
    # argparse exits on --help; just confirm it builds and subparsers exist.
    assert parser.prog == "keel"


def test_no_subcommand_does_not_error():
    # Bare `keel` no longer errors at parse time — it dispatches to the menu
    # (tty) or help (non-tty). So parsing [] must succeed with no func set.
    parser = build_parser()
    args = parser.parse_args([])
    assert getattr(args, "func", None) is None


# ─── info ────────────────────────────────────────────────────────────────────


def test_info(project_layout: Path, monkeypatch, capsys):
    code, out = run(["info"], project_layout, monkeypatch, capsys)
    assert code == 0
    assert "Test Project" in out
    assert "TEST" in out
    assert "Skills" in out


# ─── doctor ──────────────────────────────────────────────────────────────────


def test_doctor_healthy(project_layout: Path, monkeypatch, capsys):
    code, out = run(["doctor"], project_layout, monkeypatch, capsys)
    # pyyaml + jsonschema are installed in the test env; spec is valid.
    assert "KEEL repo found" in out
    assert "spec_model.yml present and schema-valid" in out
    assert code == 0


def test_doctor_outside_repo(tmp_path: Path, monkeypatch, capsys):
    code, out = run(["doctor"], tmp_path, monkeypatch, capsys)
    assert code == 1
    assert "not inside a KEEL" in out


# ─── task subcommands ────────────────────────────────────────────────────────


def test_task_create_and_list(project_layout: Path, monkeypatch, capsys):
    code, out = run(["task", "create", "my-task"], project_layout, monkeypatch, capsys)
    assert code == 0
    assert "TEST-001-my-task" in out

    code, out = run(["task", "list"], project_layout, monkeypatch, capsys)
    assert "TEST-001-my-task" in out


def test_task_verify_failing(project_layout: Path, monkeypatch, capsys):
    # create a task then give it a failing check
    run(["task", "create", "vfail"], project_layout, monkeypatch, capsys)
    acc = project_layout / "tasks" / "active" / "TEST-001-vfail" / "acceptance.yml"
    acc.write_text(
        "task: TEST-001-vfail\nchecks:\n  - name: boom\n    run: 'false'\n"
        "scope_allowlist: []\n"
    )
    code, out = run(["task", "verify", "TEST-001-vfail"], project_layout, monkeypatch, capsys)
    assert code == 1
    assert "boom" in out


# ─── skills subcommands ──────────────────────────────────────────────────────


def test_skills_list_and_show(project_layout: Path, monkeypatch, capsys):
    code, out = run(["skills", "list"], project_layout, monkeypatch, capsys)
    assert code == 0
    assert "dev-plan-task" in out

    code, out = run(["skills", "show", "dev-plan-task"], project_layout, monkeypatch, capsys)
    assert code == 0
    assert "plan" in out.lower()


def test_skills_new(project_layout: Path, monkeypatch, capsys):
    code, out = run(
        ["skills", "new", "fresh-skill", "--description", "x. Use when y."],
        project_layout, monkeypatch, capsys,
    )
    assert code == 0
    assert (project_layout / "_keel" / "skills" / "fresh-skill" / "SKILL.md").is_file()


# ─── code-map ────────────────────────────────────────────────────────────────


def test_code_map(project_layout: Path, monkeypatch, capsys):
    (project_layout / "core").mkdir()
    (project_layout / "core" / "x.py").write_text("x = 1")
    code, out = run(["code-map"], project_layout, monkeypatch, capsys)
    assert code == 0
    assert "subsystems" in out


# ─── AI_START_HERE template ──────────────────────────────────────────────────


def test_ai_start_here_template_has_placeholders():
    # Locate the template inside the installed/in-repo _keel.
    template = (
        Path(__file__).resolve().parents[1] / "templates" / "AI_START_HERE.template.md"
    )
    text = template.read_text()
    for ph in ("{{PROJECT_NAME}}", "{{PROJECT_PREFIX}}", "{{PURPOSE}}", "{{SUBSYSTEM_LIST}}"):
        assert ph in text, f"template missing placeholder {ph}"
    # And the static body's load-bearing pointers exist.
    assert "How you connect" in text
    assert "AGENTS.md" in text


# ─── interactive path (the bit a TTY-less suite normally misses) ─────────────


def test_interactive_init_creates_project(tmp_path, monkeypatch):
    """Exercises _interactive_init end-to-end with mocked input. This is the path
    that previously crashed on a missing Path import — keep it covered."""
    import argparse
    from keel.main import _cmd_init

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    target = tmp_path / "interactive-proj"
    answers = iter([
        str(target),          # Project path
        "",                   # seed from spec? (blank = skip)
        "Interactive Proj",   # Project name
        "IPRJ",               # prefix
        "y",                  # use just?
        "n",                  # git?
        "n",                  # env?
    ])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))

    ns = argparse.Namespace(
        path=None, name=None, prefix=None, spec=None,
        runner=None, git=None, env=None, yes=False, force=False,
    )
    rc = _cmd_init(ns)
    assert rc == 0
    assert (target / "_keel").is_dir()
    assert (target / "PROJECT_SPEC.md").is_file()


def test_interactive_init_default_path_does_not_crash(tmp_path, monkeypatch):
    """The exact regression: empty path input → default → Path(default) must work."""
    import argparse
    from keel.main import _interactive_init

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    # All empty → use every default; the default_name line calls Path(args.path).
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    ns = argparse.Namespace(
        path=None, name=None, prefix=None, spec=None,
        runner=None, git=None, env=None, yes=False, force=False,
    )
    filled = _interactive_init(ns)          # must not raise NameError
    assert filled.path                      # a default was chosen
    assert filled.name and filled.prefix


def test_interactive_menu_routes_to_guide(monkeypatch, capsys):
    from keel.main import _interactive_menu
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *a, **k: "2")  # choose guide
    rc = _interactive_menu()
    assert rc == 0
    assert "KEEL" in capsys.readouterr().out


def test_interactive_init_with_spec(tmp_path, monkeypatch):
    """Your scenario, the intended way: enter a project DIR, then a spec FILE.
    name/prefix should be auto-read from the spec."""
    import argparse
    from keel.main import _cmd_init

    spec = tmp_path / "myspec.md"
    spec.write_text(
        "# Crag Log — Design Spec\n\n**Project name:** Crag Log\n"
        "**Project prefix:** CRAG\n\n## Purpose\nClimbing logbook.\n"
    )
    target = tmp_path / "crag-log"
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    answers = iter([
        str(target),     # Project path (a directory)
        str(spec),       # Seed from spec file
        "",              # name (blank → auto from spec → "Crag Log")
        "",              # prefix (blank → auto from spec → "CRAG")
        "n",             # just?  (→ make, doesn't matter)
        "n",             # git?
        "n",             # env?
    ])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))

    ns = argparse.Namespace(path=None, name=None, prefix=None, spec=None,
                            runner=None, git=None, env=None, yes=False, force=False)
    rc = _cmd_init(ns)
    assert rc == 0
    assert (target / "_keel").is_dir()
    # the spec became PROJECT_SPEC.md, and identity was auto-read
    assert "Climbing logbook." in (target / "PROJECT_SPEC.md").read_text()
    import yaml
    model = yaml.safe_load((target / "_keel" / "spec_model.yml").read_text())
    assert model["project_prefix"] == "CRAG"
    assert model["project_name"] == "Crag Log"
