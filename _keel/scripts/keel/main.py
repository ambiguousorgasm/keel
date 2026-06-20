"""Unified `keel` command-line interface.

A single entry point with subcommand groups, replacing the separate keel-*
scripts:

    keel info                      orientation summary of this project
    keel doctor                    verify the environment is wired correctly
    keel task create <slug>        scaffold a task packet
    keel task list [--state ...]   list task packets
    keel task context <id>         build a task's context.md
    keel task verify <id>          run a task's gate
    keel skills list               list installed skills
    keel skills show <id>          print a skill's body
    keel skills search <query>     find skills
    keel skills new <id>           scaffold a new skill
    keel code-map                  refresh docs/code-map/
    keel mcp [--root ...]          run the MCP server

Every subcommand is a thin wrapper over keel.api.KeelRepo. KeelError is
translated into a clean stderr message + exit code 1.
"""

from __future__ import annotations

import argparse
import functools
import sys
from collections.abc import Callable
from pathlib import Path

from .api import KeelRepo
from .errors import KeelError
from .operations import TASK_TYPES
from . import scaffold


def _guard(fn: Callable[..., int]) -> Callable[..., int]:
    @functools.wraps(fn)
    def wrapper(*a, **k) -> int:
        try:
            return fn(*a, **k)
        except KeelError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

    return wrapper


# ─── orientation: info ───────────────────────────────────────────────────────


@_guard
def _cmd_info(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    model = repo.get_spec_model(validate=False)
    active = repo.list_tasks("active")
    skills = repo.list_skills()

    print(f"KEEL project: {model.get('project_name', '?')} "
          f"[{model.get('project_prefix', '?')}]")
    print(f"  root:    {repo.root}")
    print(f"  purpose: {model.get('purpose', '—')}")
    phases = model.get("phases", [])
    if phases:
        names = ", ".join(
            p.get("id", "?") + " " + p.get("name", "") if isinstance(p, dict) else str(p)
            for p in phases
        )
        print(f"  phases:  {names}")
    print(f"  governance: {', '.join(repo.list_governance()) or '(none)'}")
    print()
    print(f"Active tasks ({len(active)}):")
    for t in active:
        flags = "".join([
            "p" if t.has_plan else "-",
            "c" if t.has_context else "-",
            "r" if t.has_review else "-",
            "h" if t.has_handoff else "-",
        ])
        print(f"  {t.task_id}  [{flags}]")
    if not active:
        print("  (none)")
    print()
    print(f"Skills ({len(skills)}): {', '.join(s.id for s in skills) or '(none)'}")
    print()
    print("Next: `keel --help` for commands, or read AI_START_HERE.md.")
    return 0


# ─── orientation: doctor ─────────────────────────────────────────────────────


def _cmd_doctor(args: argparse.Namespace) -> int:
    """Diagnose the KEEL environment. Returns 1 if any hard check fails."""
    problems = 0
    ok = "✅"
    warn = "⚠️ "
    bad = "❌"

    # 1. Repo discoverable?
    try:
        repo = KeelRepo.discover()
        print(f"{ok} KEEL repo found: {repo.root}")
    except KeelError as e:
        print(f"{bad} {e}")
        print("   You are not inside a KEEL-managed repository.")
        return 1

    # 2. spec_model present & valid?
    try:
        repo.get_spec_model(validate=True)
        print(f"{ok} spec_model.yml present and schema-valid")
    except KeelError as e:
        print(f"{bad} spec_model.yml: {e}")
        problems += 1

    # 3. Governance docs present?
    present = set(repo.list_governance())
    expected = {"PRINCIPLES.md", "CORE.md", "AGENTS.md"}
    missing = expected - present
    if missing:
        print(f"{warn}missing governance docs: {', '.join(sorted(missing))}")
    else:
        print(f"{ok} core governance docs present")

    # 4. AI onboarding pointer present?
    if (repo.root / "AI_START_HERE.md").is_file():
        print(f"{ok} AI_START_HERE.md present")
    else:
        print(f"{warn}AI_START_HERE.md missing (agents have no onboarding pointer)")

    # 5. Skills loadable?
    try:
        skills = repo.list_skills()
        print(f"{ok} skills load: {len(skills)} found")
    except KeelError as e:
        print(f"{bad} skills failed to load: {e}")
        problems += 1

    # 6. Python deps
    for mod, label in [("yaml", "pyyaml"), ("jsonschema", "jsonschema")]:
        try:
            __import__(mod)
            print(f"{ok} dependency: {label}")
        except ImportError:
            print(f"{bad} missing dependency: {label} (pip install {label})")
            problems += 1

    # 7. MCP (optional)
    try:
        __import__("mcp")
        print(f"{ok} MCP available (keel mcp will run)")
    except ImportError:
        print(f"{warn}MCP not installed (optional). For MCP tools: "
              f"pip install -e '_keel[mcp]'")

    # 8. git (for scope enforcement)
    import shutil
    if shutil.which("git"):
        print(f"{ok} git available (scope enforcement active)")
    else:
        print(f"{warn}git not found — scope_allowlist checks will be skipped")

    print()
    if problems:
        print(f"{bad} {problems} problem(s) found.")
        return 1
    print(f"{ok} KEEL environment looks healthy.")
    return 0


# ─── task subcommands ────────────────────────────────────────────────────────


@_guard
def _cmd_task_create(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    t = repo.create_task(args.slug, task_type=args.type, prefix_override=args.prefix)
    rel = t.path.relative_to(repo.root)
    print(f"✅ created task packet: {rel}")
    print(f"   brief: {rel}/brief.md   acceptance: {rel}/acceptance.yml")
    print(f"Next: edit brief.md, then `keel task context {t.task_id}`")
    return 0


@_guard
def _cmd_task_list(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    tasks = repo.list_tasks(args.state)
    if not tasks:
        print("(no tasks)")
        return 0
    for t in tasks:
        print(f"{t.state:9}  {t.task_id}")
    return 0


@_guard
def _cmd_task_context(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    r = repo.build_context(args.task_id)
    print(f"✅ wrote {r.path.relative_to(repo.root)}")
    if r.warnings:
        print(f"⚠ {len(r.warnings)} warning(s):")
        for w in r.warnings:
            print(f"   - {w}")
    return 0


@_guard
def _cmd_task_verify(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    r = repo.verify_task(args.task_id)
    for c in r.results:
        mark = "✅" if c.passed else "❌"
        print(f"{mark} {c.name}" + ("" if c.passed else f" (exit {c.returncode})"))
    print(f"\nsummary: {r.summary_path.relative_to(repo.root)}")
    if r.passed:
        print("✅ all checks passed.")
        return 0
    print("❌ some checks failed.")
    return 1


# ─── skills subcommands ──────────────────────────────────────────────────────


@_guard
def _cmd_skills_list(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    infos = repo.list_skills()
    if not infos:
        print("No skills installed under _keel/skills/.")
        return 0
    width = max(len(i.id) for i in infos)
    for info in infos:
        desc = " ".join(info.description.split())
        if len(desc) > 80:
            desc = desc[:77] + "..."
        print(f"{info.id.ljust(width)}  {desc}")
    return 0


@_guard
def _cmd_skills_show(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    skill = repo.get_skill(args.skill_id)
    print(skill.body)
    if skill.bundled_files:
        print("\n--- bundled files ---")
        for f in skill.bundled_files:
            print(f"  {f}")
    return 0


@_guard
def _cmd_skills_search(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    hits = repo.search_skills(args.query)
    if not hits:
        print(f"No skills match {args.query!r}.")
        return 0
    for info in hits:
        print(f"{info.id}  —  {' '.join(info.description.split())}")
    return 0


@_guard
def _cmd_skills_new(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    skill = repo.create_skill(args.skill_id, name=args.name, description=args.description)
    print(f"✅ created skill: {skill.path.relative_to(repo.root)}/SKILL.md")
    print("   Edit the frontmatter description and body, then it's discoverable.")
    return 0


# ─── code-map ────────────────────────────────────────────────────────────────


@_guard
def _cmd_code_map(args: argparse.Namespace) -> int:
    repo = KeelRepo.discover()
    r = repo.update_code_map()
    print(f"✅ code map: {r.subsystems} subsystems, {r.total_files} files")
    print(f"   index: {r.index_path.relative_to(repo.root)}")
    return 0


# ─── mcp ─────────────────────────────────────────────────────────────────────


def _cmd_mcp(args: argparse.Namespace) -> int:
    try:
        from .mcp_server import build_server, resolve_root
    except ImportError:
        print(
            "ERROR: the MCP server needs the optional 'mcp' extra:\n"
            "    pip install -e '_keel[mcp]'",
            file=sys.stderr,
        )
        return 1
    root = resolve_root(args.root)
    build_server(root).run(transport=args.transport)
    return 0


# ─── parser ──────────────────────────────────────────────────────────────────


# ─── project creation: init ──────────────────────────────────────────────────

GUIDE_TEXT = """\
KEEL — repo-native agent development operating system
=====================================================

WHAT IT IS
  A project template + tooling that keeps AI coding agents on-task. The
  repository is the source of truth; agents are stateless specialists that take
  one bounded task at a time, prove it with a gate, and hand off.

SOURCE-OF-TRUTH HIERARCHY (higher overrides lower)
  PRINCIPLES.md → CORE.md → DECISIONS.md / COMPONENTS.md → STATUS.md → CHANGELOG.md
  A change that violates PRINCIPLES.md is a defect, not a new fact.

THE TASK LIFECYCLE
  plan → build context → implement (in an isolated worktree, in scope)
       → verify (the gate) → independent review (reads the diff, not your story)
       → handoff (updates STATUS / CHANGELOG)

GETTING STARTED
  keel init /path/to/project      create a new project (interactive)
  cd /path/to/project
  # edit PROJECT_SPEC.md, then open in an AI coding tool and say:
  #   "Read _keel/BOOTSTRAP.md and follow it."
  keel doctor                     check the environment is wired correctly
  keel info                       orientation summary of the project

EVERYDAY COMMANDS
  keel task create <slug>         scaffold a task packet
  keel task context <id>          build a task's context.md
  keel task verify <id>           run a task's gate
  keel skills list                list installed skills
  keel mcp                        run the MCP server (needs the [mcp] extra)

READ NEXT
  AI_START_HERE.md (after bootstrap) · _keel/BOOTSTRAP.md · _keel/scripts/keel/README.md
"""


def _derive_prefix(name: str) -> str:
    letters = [c for c in name.upper() if c.isalpha()]
    words = [w for w in name.upper().replace("-", " ").replace("_", " ").split() if w]
    if len(words) >= 2:
        cand = "".join(w[0] for w in words)[:6]
    else:
        cand = "".join(letters)[:4]
    cand = "".join(c for c in cand if c.isalpha())
    return (cand or "PROJ")[:6].ljust(2, "X")


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    try:
        ans = input(f"{label}{suffix}: ").strip()
    except EOFError:
        ans = ""
    return ans or (default or "")


def _prompt_yes(label: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    ans = _prompt(f"{label} ({d})", "").lower()
    if not ans:
        return default
    return ans.startswith("y")


def _interactive_init(args: argparse.Namespace) -> argparse.Namespace:
    """Fill missing init params by prompting. Mutates and returns args."""
    print("Create a new KEEL project\n" + "-" * 25)
    if not args.path:
        args.path = _prompt("Project path (a NEW directory to create)", "./my-project")
    # Offer to seed from an existing spec file (this is the --spec flow, interactive).
    if not getattr(args, "spec", None):
        spec_in = _prompt(
            "Seed from an existing PROJECT_SPEC file? (path, or blank to skip)", ""
        )
        if spec_in:
            args.spec = spec_in
    # If a spec was provided, read its identity to offer better defaults.
    parsed_name = parsed_prefix = None
    if getattr(args, "spec", None):
        try:
            text = Path(args.spec).expanduser().read_text()
            parsed_name, parsed_prefix = scaffold.parse_spec_identity(text)
        except Exception:
            print(f"  (couldn't read {args.spec} yet — will validate when creating)")
    default_name = (
        args.name or parsed_name
        or Path(args.path).expanduser().name.replace("-", " ").title()
    )
    args.name = args.name or _prompt("Project name", default_name)
    args.prefix = args.prefix or _prompt(
        "Task prefix (2-6 caps)", parsed_prefix or _derive_prefix(args.name)
    )
    if args.runner is None:
        args.runner = "just" if _prompt_yes("Use `just` as the command runner? (else make)", True) else "make"
    if args.git is None:
        args.git = _prompt_yes("Initialize a git repository?", True)
    if args.env is None:
        args.env = _prompt_yes("Write a .env.example?", False)
    return args


@_guard
def _cmd_init(args: argparse.Namespace) -> int:
    interactive = sys.stdin.isatty() and not args.yes
    if interactive:
        args = _interactive_init(args)

    # Resolve a spec file (from --spec or the interactive prompt) and read its
    # identity to fill any name/prefix the user didn't supply.
    spec = getattr(args, "spec", None)
    if spec:
        sp = Path(spec).expanduser()
        if not sp.is_file():
            print(f"ERROR: spec file not found: {sp}", file=sys.stderr)
            return 1
        spec = str(sp)
        parsed_name, parsed_prefix = scaffold.parse_spec_identity(sp.read_text())
        args.name = args.name or parsed_name
        args.prefix = args.prefix or parsed_prefix

    if not interactive:
        missing = [f for f in ("path", "name", "prefix") if not getattr(args, f)]
        if missing:
            print(
                f"ERROR: non-interactive init needs: {', '.join('--' + m for m in missing)} "
                f"(or run in a terminal for prompts). With --spec, name/prefix are read "
                f"from the spec if present.",
                file=sys.stderr,
            )
            return 1

    result = scaffold.init_project(
        args.path,
        name=args.name,
        prefix=args.prefix,
        runner=args.runner or "just",
        git=bool(args.git) if args.git is not None else True,
        write_env=bool(args.env),
        force=args.force,
        spec_file=spec,
    )

    print(f"\n✅ Created KEEL project at {result.root}")
    print(f"   template source: {result.template_source}")
    for item in result.created:
        print(f"   + {item}")
    if result.git_initialized:
        print("   + git repository initialized")
    print("\nNext steps:")
    print(f"  1. cd {result.root}")
    print("  2. Edit PROJECT_SPEC.md to describe your project.")
    print("  3. Open the project in an AI coding tool and say:")
    print('       "Read _keel/BOOTSTRAP.md and follow it."')
    print("     (a CLI can't write your PRINCIPLES/CORE — that needs a model reading your spec)")
    print("  4. keel doctor   # confirm the environment is healthy")
    return 0


def _cmd_guide(args: argparse.Namespace) -> int:
    print(GUIDE_TEXT)
    return 0


# ─── interactive top-level menu (bare `keel` in a terminal) ──────────────────


def _interactive_menu() -> int:
    print("KEEL — repo-native agent dev OS\n")
    print("  1) Create a new KEEL project")
    print("  2) Show rules & usage")
    print("  3) Quit")
    choice = _prompt("\nChoose", "1")
    if choice == "1":
        ns = argparse.Namespace(
            path=None, name=None, prefix=None, spec=None, runner=None,
            git=None, env=None, yes=False, force=False, func=_cmd_init,
        )
        return _cmd_init(ns)
    if choice == "2":
        return _cmd_guide(argparse.Namespace())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="keel", description="KEEL — repo-native agent dev OS.")
    from . import __version__
    p.add_argument("-V", "--version", action="version", version=f"keel {__version__}")
    sub = p.add_subparsers(dest="group", required=False)

    # init (project creation — interactive by default)
    i = sub.add_parser("init", help="create a new KEEL project (interactive)")
    i.add_argument("path", nargs="?", default=None, help="where to create the project")
    i.add_argument("--name", default=None)
    i.add_argument("--prefix", default=None, help="task ID prefix, 2-6 caps")
    i.add_argument("--spec", default=None,
                   help="seed PROJECT_SPEC.md from this file (name/prefix auto-read)")
    i.add_argument("--runner", default=None, choices=["just", "make"])
    i.add_argument("--git", dest="git", action="store_true", default=None)
    i.add_argument("--no-git", dest="git", action="store_false")
    i.add_argument("--env", action="store_true", default=None, help="write .env.example")
    i.add_argument("--yes", action="store_true", help="non-interactive; use args/defaults")
    i.add_argument("--force", action="store_true", help="scaffold into a non-empty dir")
    i.set_defaults(func=_cmd_init)

    sp = sub.add_parser("guide", help="show KEEL rules & usage")
    sp.set_defaults(func=_cmd_guide)

    sp = sub.add_parser("info", help="orientation summary of this project")
    sp.set_defaults(func=_cmd_info)

    sp = sub.add_parser("doctor", help="verify the environment is wired correctly")
    sp.set_defaults(func=_cmd_doctor)

    # task group
    t = sub.add_parser("task", help="task packet operations")
    tsub = t.add_subparsers(dest="cmd", required=True)
    c = tsub.add_parser("create", help="scaffold a task packet")
    c.add_argument("slug")
    c.add_argument("--type", default="implementation", choices=list(TASK_TYPES))
    c.add_argument("--prefix", default=None)
    c.set_defaults(func=_cmd_task_create)
    c = tsub.add_parser("list", help="list task packets")
    c.add_argument("--state", default=None, choices=["active", "completed", "blocked"])
    c.set_defaults(func=_cmd_task_list)
    c = tsub.add_parser("context", help="build a task's context.md")
    c.add_argument("task_id")
    c.set_defaults(func=_cmd_task_context)
    c = tsub.add_parser("verify", help="run a task's acceptance gate")
    c.add_argument("task_id")
    c.set_defaults(func=_cmd_task_verify)

    # skills group
    s = sub.add_parser("skills", help="skill registry operations")
    ssub = s.add_subparsers(dest="cmd", required=True)
    c = ssub.add_parser("list", help="list installed skills")
    c.set_defaults(func=_cmd_skills_list)
    c = ssub.add_parser("show", help="print a skill's full body")
    c.add_argument("skill_id")
    c.set_defaults(func=_cmd_skills_show)
    c = ssub.add_parser("search", help="find skills by query")
    c.add_argument("query")
    c.set_defaults(func=_cmd_skills_search)
    c = ssub.add_parser("new", help="scaffold a new skill")
    c.add_argument("skill_id")
    c.add_argument("--name", default=None)
    c.add_argument("--description", default=None)
    c.set_defaults(func=_cmd_skills_new)

    sp = sub.add_parser("code-map", help="refresh docs/code-map/")
    sp.set_defaults(func=_cmd_code_map)

    sp = sub.add_parser("mcp", help="run the MCP server")
    sp.add_argument("--root", default=None)
    sp.add_argument("--transport", default="stdio",
                    choices=["stdio", "sse", "streamable-http"])
    sp.set_defaults(func=_cmd_mcp)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if getattr(args, "func", None) is None:
            # No subcommand: interactive menu in a terminal, else help.
            if sys.stdin.isatty():
                return _interactive_menu()
            parser.print_help()
            return 0
        return args.func(args)
    except BrokenPipeError:
        # Downstream closed the pipe (e.g. `keel guide | head`). Exit quietly.
        try:
            sys.stdout.close()
        except Exception:
            pass
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
