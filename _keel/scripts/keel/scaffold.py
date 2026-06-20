"""scaffold — create new KEEL project instances.

This is the layer ABOVE the in-project CLI: it sets up a *new* project directory
from nothing, then hands off to the AI bootstrap. It deliberately does NOT write
PRINCIPLES/CORE/module-cards — those require a model reading your spec, and a
faked placeholder would be the unfalsifiable fluff KEEL warns against.

What `init` produces:

- `<root>/_keel/`            — the KEEL OS (templates, skills, scripts, bootstrap)
- `<root>/PROJECT_SPEC.md`   — pre-filled skeleton for YOU to complete
- `<root>/_keel/spec_model.yml` — a minimal *valid* placeholder so `keel doctor`
                               and `keel info` work immediately (honest stub, not
                               fake governance)
- justfile / Makefile, .gitignore, optional .env.example, optional git init

Then it prints the exact next step: open the project in an AI coding tool and say
"Read `_keel/BOOTSTRAP.md` and follow it."

Template resolution order (so it works in dev, editable, and pip-installed):
  1. $KEEL_TEMPLATE_ROOT  (a `_keel/` directory to copy from — escape hatch)
  2. bundled `keel/assets/keel_template.zip`  (pip-installed self-containment)
  3. walk up from this file to the enclosing `_keel/`  (dev / created projects)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .errors import KeelError, ValidationError

_ASSET_ZIP = Path(__file__).resolve().parent / "assets" / "keel_template.zip"

# Files/dirs never copied into a new project (dev junk + generated + the zip).
_EXCLUDE_NAMES = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "assets",            # avoid recursively shipping the template zip
    "tests",             # KEEL's own tests aren't part of a new project
    "BOOTSTRAP_REPORT.md", "spec_model.yml",  # generated, project-specific
}
_EXCLUDE_SUFFIXES = {".pyc", ".egg-info"}

_PREFIX_RE = __import__("re").compile(r"^[A-Z]{2,6}$")
_re = __import__("re")


def parse_spec_identity(text: str) -> tuple[str | None, str | None]:
    """Best-effort extraction of (project_name, project_prefix) from a spec file.

    Recognizes the KEEL PROJECT_SPEC format:
        # <Name> — Design Spec
        **Project name:** <Name>
        **Project prefix:** <PREFIX>
    Returns (None, None) for anything it can't find — callers fall back to
    explicit args or prompts.
    """
    name = None
    prefix = None
    m = _re.search(r"^\*\*Project name:\*\*\s*(.+?)\s*$", text, _re.MULTILINE)
    if m and "<" not in m.group(1):
        name = m.group(1).strip()
    if name is None:
        m = _re.search(r"^#\s+(.+?)\s+[—-]\s+Design Spec", text, _re.MULTILINE)
        if m and "<" not in m.group(1):
            name = m.group(1).strip()
    m = _re.search(r"^\*\*Project prefix:\*\*\s*`?([A-Z]{2,6})`?", text, _re.MULTILINE)
    if m:
        prefix = m.group(1)
    return name, prefix


# ─── template resolution & materialization ───────────────────────────────────


def _copytree_ignore(dirname: str, names: list[str]) -> set[str]:
    ignored = set()
    for n in names:
        if n in _EXCLUDE_NAMES or any(n.endswith(s) for s in _EXCLUDE_SUFFIXES):
            ignored.add(n)
    return ignored


def _walk_up_keel() -> Path | None:
    for p in Path(__file__).resolve().parents:
        if p.name == "_keel" and (p / "BOOTSTRAP.md").is_file():
            return p
    return None


def materialize_template(dest_keel: Path) -> str:
    """Create `dest_keel` (a new project's `_keel/`) from the best template source.

    Returns a short string naming which source was used (for the report).
    """
    if dest_keel.exists():
        raise KeelError(f"{dest_keel} already exists.")

    env = os.environ.get("KEEL_TEMPLATE_ROOT")
    if env:
        src = Path(env).resolve()
        if not (src / "BOOTSTRAP.md").is_file():
            raise KeelError(f"KEEL_TEMPLATE_ROOT={src} is not a KEEL template (_keel/).")
        shutil.copytree(src, dest_keel, ignore=_copytree_ignore)
        return f"env:{src}"

    if _ASSET_ZIP.is_file():
        dest_keel.mkdir(parents=True)
        with zipfile.ZipFile(_ASSET_ZIP) as z:
            z.extractall(dest_keel)
        return "bundled-zip"

    walk = _walk_up_keel()
    if walk:
        shutil.copytree(walk, dest_keel, ignore=_copytree_ignore)
        return f"walk-up:{walk}"

    raise KeelError(
        "Could not locate a KEEL template. Set KEEL_TEMPLATE_ROOT to a _keel/ "
        "directory, or reinstall the package so the bundled template is present."
    )


def build_template_archive(source_keel: Path, dest_zip: Path) -> int:
    """(Re)build the bundled template zip from a live `_keel/` tree.

    Returns the number of files written. Excludes the same junk/generated/assets
    that materialize_template would skip, so the zip is clean and non-recursive.
    """
    if not (source_keel / "BOOTSTRAP.md").is_file():
        raise KeelError(f"{source_keel} is not a KEEL template (_keel/).")
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(source_keel.rglob("*")):
            rel_parts = path.relative_to(source_keel).parts
            if any(part in _EXCLUDE_NAMES for part in rel_parts):
                continue
            if any(str(path).endswith(s) for s in _EXCLUDE_SUFFIXES):
                continue
            if path.is_file():
                z.write(path, Path(*rel_parts).as_posix())
                count += 1
    return count


# ─── project initialization ──────────────────────────────────────────────────


@dataclass
class InitResult:
    root: Path
    template_source: str
    created: list[str] = field(default_factory=list)
    git_initialized: bool = False


def _placeholder_spec_model(name: str, prefix: str) -> str:
    """A minimal, schema-VALID spec_model.yml so doctor/info work pre-bootstrap.

    This is an honest stub: one placeholder subsystem/invariant/phase, clearly
    marked TODO. It is NOT fake governance — there is no CORE or PRINCIPLES here.
    """
    model = {
        "project_name": name,
        "project_prefix": prefix,
        "purpose": "TODO — fill in PROJECT_SPEC.md, then run the AI bootstrap.",
        "tech_stack": {"language": "TODO"},
        "subsystems": [
            {
                "name": "placeholder",
                "responsibility": "TODO — replace via PROJECT_SPEC.md + bootstrap",
                "owns_state": [],
                "must_not_mutate": [],
                "allowed_deps": [],
                "forbidden_deps": [],
            }
        ],
        "invariants": [
            {"id": "INV-1", "statement": "TODO — define a real invariant"}
        ],
        "failure_modes": [],
        "phases": [{"id": "P0", "name": "TODO"}],
    }
    header = (
        "# PLACEHOLDER spec_model.yml — written by `keel init`.\n"
        "# This is a valid stub so `keel doctor` / `keel info` work immediately.\n"
        "# It is NOT your real project model. Fill in PROJECT_SPEC.md, then run the\n"
        "# AI bootstrap (see _keel/BOOTSTRAP.md), which regenerates this file.\n"
    )
    return header + yaml.safe_dump(model, sort_keys=False)


def _fill_project_spec(templates_dir: Path, name: str, prefix: str) -> str:
    tpl = templates_dir / "PROJECT_SPEC.template.md"
    text = tpl.read_text() if tpl.is_file() else "# <Project Name> — Design Spec\n"
    text = text.replace("# <Project Name> — Design Spec", f"# {name} — Design Spec")
    text = text.replace("**Project name:** <full name>", f"**Project name:** {name}")
    text = text.replace(
        '**Project prefix:** <2–6 caps letters used in task IDs, e.g. `ORDP` for "Order Pipeline">',
        f"**Project prefix:** {prefix}",
    )
    return text


_GITIGNORE = """\
.worktrees/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
*.egg-info/
"""

_ENV_EXAMPLE = """\
# Copy to .env and fill in. .env is gitignored.

# Bind the KEEL MCP server / CLI to this project (optional; CWD discovery also works).
KEEL_ROOT={root}

# If you drive KEEL with an AI coding tool that needs a key, set it here.
# ANTHROPIC_API_KEY=
"""


def init_project(
    path: str | Path,
    *,
    name: str,
    prefix: str,
    runner: str = "just",
    git: bool = True,
    write_env: bool = False,
    force: bool = False,
    spec_file: str | Path | None = None,
) -> InitResult:
    """Create a new KEEL project at `path`. Returns an InitResult.

    If `spec_file` is given, its contents become PROJECT_SPEC.md (instead of the
    blank skeleton) — so you can seed a project from a spec you've already written.
    """
    if not _PREFIX_RE.fullmatch(prefix):
        raise ValidationError(
            f"prefix {prefix!r} must be 2–6 uppercase letters (e.g. ORDP)."
        )
    if runner not in ("just", "make"):
        raise ValidationError("runner must be 'just' or 'make'.")

    spec_text: str | None = None
    if spec_file is not None:
        sp = Path(spec_file)
        if not sp.is_file():
            raise KeelError(f"--spec file not found: {sp}")
        spec_text = sp.read_text()

    root = Path(path).resolve()
    if root.exists() and any(root.iterdir()) and not force:
        raise KeelError(
            f"{root} exists and is not empty. Use force/--force to scaffold anyway."
        )
    root.mkdir(parents=True, exist_ok=True)

    result = InitResult(root=root, template_source="")

    # 1. the _keel/ OS
    result.template_source = materialize_template(root / "_keel")
    result.created.append("_keel/")

    templates_dir = root / "_keel" / "templates"

    # 2. placeholder spec_model.yml (valid stub)
    (root / "_keel" / "spec_model.yml").write_text(
        _placeholder_spec_model(name, prefix)
    )
    result.created.append("_keel/spec_model.yml (placeholder)")

    # 3. PROJECT_SPEC.md — from the provided spec file, or the filled skeleton
    if spec_text is not None:
        (root / "PROJECT_SPEC.md").write_text(spec_text)
        result.created.append("PROJECT_SPEC.md (from --spec)")
    else:
        (root / "PROJECT_SPEC.md").write_text(
            _fill_project_spec(templates_dir, name, prefix)
        )
        result.created.append("PROJECT_SPEC.md")

    # 4. command runner
    if runner == "just":
        src = templates_dir / "justfile.template"
        if src.is_file():
            (root / "justfile").write_text(
                src.read_text().replace("{{PROJECT_NAME}}", name)
            )
            result.created.append("justfile")
    else:
        src = templates_dir / "Makefile.template"
        if src.is_file():
            (root / "Makefile").write_text(
                src.read_text().replace("{{PROJECT_NAME}}", name)
            )
            result.created.append("Makefile")

    # 5. task dirs
    for sub in ("active", "completed", "blocked"):
        (root / "tasks" / sub).mkdir(parents=True, exist_ok=True)
    result.created.append("tasks/{active,completed,blocked}/")

    # 6. .gitignore
    (root / ".gitignore").write_text(_GITIGNORE)
    result.created.append(".gitignore")

    # 7. optional .env.example
    if write_env:
        (root / ".env.example").write_text(_ENV_EXAMPLE.format(root=root))
        result.created.append(".env.example")

    # 8. publish skills to .agents/skills/ for agent discovery (Zed/Claude Code/…)
    try:
        from . import skills as _skills
        from .helpers import ProjectLayout as _Layout

        layout = _Layout.from_root(root)
        _skills.export_agent_skills(layout.skills, layout.agents_skills)
        layout.agents_catalog.parent.mkdir(parents=True, exist_ok=True)
        layout.agents_catalog.write_text(_skills.render_catalog(layout.skills))
        result.created.append(".agents/skills/ (agent-discoverable skill mirrors)")
    except Exception:
        # Non-fatal: the project is still valid; `keel skills sync` can publish later.
        pass

    # 9. optional git init
    if git and shutil.which("git"):
        subprocess.run(["git", "init", "-q"], cwd=root, check=False)
        result.git_initialized = (root / ".git").is_dir()

    return result
