"""Core KEEL operations: create_task, build_context, verify, code_map.

These are the single implementation of each operation. The CLIs in
scripts/agent/ and the KeelRepo API surface both call these. They return typed
results and raise KeelError subclasses — they never print or call SystemExit.
"""

from __future__ import annotations

import fnmatch
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .errors import TaskExists, TemplateError, ValidationError
from .helpers import (
    ProjectLayout,
    append_trace,
    extract_markdown_section,
    find_task_dir,
    load_spec_model,
    next_task_number,
)


# ═══════════════════════════════════════════════════════════════════════════
# create_task
# ═══════════════════════════════════════════════════════════════════════════

TASK_TYPES = {
    "implementation": "task-brief.template.md",
    "principle-amendment": "principle-amendment-task.template.md",
}

_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def validate_slug(slug: str) -> str:
    """Slug must be kebab-case. Raises ValidationError otherwise."""
    if not _SLUG_RE.fullmatch(slug):
        raise ValidationError(
            f"slug {slug!r} must be kebab-case "
            f"(lowercase letters/digits, hyphen-separated, no leading/trailing hyphen)."
        )
    return slug


@dataclass
class CreatedTask:
    task_id: str
    path: Path
    brief: Path
    acceptance: Path
    task_type: str


def create_task(
    layout: ProjectLayout,
    slug: str,
    *,
    task_type: str = "implementation",
    prefix_override: str | None = None,
) -> CreatedTask:
    """Create a task packet under tasks/active/. Returns CreatedTask."""
    validate_slug(slug)
    if task_type not in TASK_TYPES:
        raise ValidationError(
            f"unknown task type {task_type!r}. Valid types: {', '.join(TASK_TYPES)}"
        )

    if prefix_override:
        prefix = prefix_override
    else:
        model = load_spec_model(layout)
        prefix = model["project_prefix"]

    number = next_task_number(layout, prefix)
    task_id = f"{prefix}-{number:03d}-{slug}"
    task_dir = layout.tasks_active / task_id

    if task_dir.exists():
        raise TaskExists(f"{task_dir} already exists.")

    task_dir.mkdir(parents=True)
    (task_dir / "evidence").mkdir()

    brief_template = layout.templates / TASK_TYPES[task_type]
    if not brief_template.is_file():
        raise TemplateError(f"template not found: {brief_template}")
    shutil.copy(brief_template, task_dir / "brief.md")

    acceptance_template = layout.templates / "acceptance.template.yml"
    if not acceptance_template.is_file():
        raise TemplateError(f"template not found: {acceptance_template}")
    text = acceptance_template.read_text().replace("<ID>", task_id, 1)
    (task_dir / "acceptance.yml").write_text(text)

    (task_dir / "evidence" / "trace.jsonl").touch()
    append_trace(
        task_dir,
        role="system",
        action="task_created",
        task_id=task_id,
        task_type=task_type,
    )

    return CreatedTask(
        task_id=task_id,
        path=task_dir,
        brief=task_dir / "brief.md",
        acceptance=task_dir / "acceptance.yml",
        task_type=task_type,
    )


# ═══════════════════════════════════════════════════════════════════════════
# build_context
# ═══════════════════════════════════════════════════════════════════════════

STABLE_PREFIX_ORDER = ("AGENTS.md", "PRINCIPLES.md", "CORE.md", "COMPONENTS.md")


def parse_relevant_sources(brief_text: str) -> list[tuple[str, str | None]]:
    """Extract the 'Relevant sources' section and return (path, section?) tuples."""
    section = extract_markdown_section(brief_text, "Relevant sources")
    if section is None:
        return []
    sources: list[tuple[str, str | None]] = []
    for raw_line in section.splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if not line or line.startswith("#") or line.startswith(">"):
            continue
        line = line.replace("`", "")
        if ":" in line:
            path, _, sub = line.partition(":")
            sources.append((path.strip(), sub.strip() or None))
        else:
            sources.append((line.strip(), None))
    return sources


def _looks_like_id(s: str) -> bool:
    return bool(re.fullmatch(r"(P|D|INV|FM)-\d+", s))


def _find_id_section(text: str, ref: str) -> str | None:
    """Find a heading line that STARTS with the id ref, even with a title."""
    pattern = re.compile(rf"^(#{{1,6}})\s+{re.escape(ref)}\b.*$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        return None
    heading_level = len(m.group(1))
    start = m.start()
    end = len(text)
    next_pattern = re.compile(r"^(#{1,6})\s+", re.MULTILINE)
    for nxt in next_pattern.finditer(text, m.end()):
        if len(nxt.group(1)) <= heading_level:
            end = nxt.start()
            break
    return text[start:end].rstrip() + "\n"


def read_excerpt(path: Path, sub: str | None) -> tuple[str, list[str]]:
    """Return (verbatim_excerpt, warnings) for one source line."""
    warnings: list[str] = []
    if not path.is_file():
        warnings.append(f"{path} does not exist")
        return f"\n> ⚠ build_context: {path} does not exist; included as-is.\n", warnings

    text = path.read_text()
    if sub is None:
        return text, warnings

    ids = [s.strip() for s in sub.split(",") if s.strip()]
    if ids and all(_looks_like_id(i) for i in ids):
        parts: list[str] = []
        for ref in ids:
            section = extract_markdown_section(text, ref) or _find_id_section(text, ref)
            if section is None:
                warnings.append(f"id {ref!r} not found in {path.name}")
                parts.append(f"> ⚠ build_context: id {ref!r} not found in {path.name}.\n")
            else:
                parts.append(section)
        return "\n".join(parts), warnings

    section = extract_markdown_section(text, sub)
    if section is None:
        warnings.append(f"heading {sub!r} not found in {path.name}")
        return (
            f"> ⚠ build_context: heading {sub!r} not found in {path.name}; "
            f"included full file as fallback.\n\n{text}",
            warnings,
        )
    return section, warnings


def order_sources(
    sources: list[tuple[str, str | None]]
) -> list[tuple[str, str | None]]:
    """Sort sources so the cache-stable prefix files come first, then module
    cards, then everything else. Within each group, preserve input order."""

    def rank(item: tuple[str, str | None]) -> tuple[int, int]:
        path, _ = item
        try:
            return (0, STABLE_PREFIX_ORDER.index(Path(path).name))
        except ValueError:
            pass
        if path.startswith("docs/module-cards/"):
            return (1, 0)
        if path.startswith("docs/"):
            return (2, 0)
        return (3, 0)

    return [
        s for _, s in sorted(enumerate(sources), key=lambda iv: (rank(iv[1]), iv[0]))
    ]


def current_git_revision(layout: ProjectLayout) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=layout.root,
            capture_output=True,
            text=True,
            check=False,
        )
        return out.stdout.strip() if out.returncode == 0 else "<not a git repository>"
    except FileNotFoundError:
        return "<git not installed>"


@dataclass
class ContextResult:
    task_id: str
    path: Path
    text: str
    sources: int
    warnings: list[str] = field(default_factory=list)


def build_context(layout: ProjectLayout, task_id: str) -> ContextResult:
    """Assemble a task's context.md. Writes the file and returns ContextResult."""
    task_dir = find_task_dir(layout, task_id)
    brief_path = task_dir / "brief.md"
    if not brief_path.is_file():
        raise TemplateError(f"{brief_path} not found.")

    brief_text = brief_path.read_text()
    sources = order_sources(parse_relevant_sources(brief_text))

    revision = current_git_revision(layout)
    risk_notes = extract_markdown_section(brief_text, "Risk notes (optional)")
    acceptance_path = task_dir / "acceptance.yml"
    acceptance_text = (
        acceptance_path.read_text() if acceptance_path.is_file() else "(missing)"
    )

    all_warnings: list[str] = []
    parts: list[str] = []
    parts.append(f"# Context for {task_id}\n")
    parts.append(
        "> Generated by KEEL build_context. Do not edit by hand; re-run to refresh. \n"
        "> Excerpts are verbatim — KEEL's compaction rule is cut-don't-summarize.\n"
    )
    parts.append("\n---\n\n## Stable governance prefix\n")
    parts.append(
        "_These sections come first in every task's context so prompt-caching \n"
        "providers can reuse them across sessions._\n\n"
    )
    for path, sub in sources:
        excerpt, warnings = read_excerpt(layout.root / path, sub)
        all_warnings.extend(warnings)
        anchor = f"`{path}`" + (f" → `{sub}`" if sub else "")
        parts.append(f"\n### From {anchor}\n\n{excerpt}\n")

    parts.append("\n---\n\n## Task-specific material\n\n")
    parts.append(f"**Task ID:** `{task_id}`  \n")
    parts.append(f"**Git revision at context build:** `{revision}`\n\n")
    parts.append("### Brief\n\n")
    parts.append(brief_text)
    parts.append("\n\n### Acceptance criteria (executable)\n\n```yaml\n")
    parts.append(acceptance_text.rstrip() + "\n```\n")
    if risk_notes:
        parts.append("\n### Risk notes\n\n")
        parts.append(risk_notes)
    parts.append(
        "\n### Required verification commands\n\n"
        "Before writing the handoff, run:\n\n"
        f"```bash\njust verify-task {task_id}\n```\n"
    )

    context_path = task_dir / "context.md"
    text = "".join(parts)
    context_path.write_text(text)

    append_trace(
        task_dir,
        role="system",
        action="context_built",
        sources=len(sources),
        revision=revision,
        warnings=all_warnings,
    )

    return ContextResult(
        task_id=task_id,
        path=context_path,
        text=text,
        sources=len(sources),
        warnings=all_warnings,
    )


# ═══════════════════════════════════════════════════════════════════════════
# verify_task
# ═══════════════════════════════════════════════════════════════════════════

import yaml  # noqa: E402  (kept local-ish; used only here)


@dataclass
class CheckResult:
    name: str
    passed: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


@dataclass
class VerificationResult:
    task_id: str
    results: list[CheckResult]
    summary_path: Path

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)


def run_check(name: str, cmd: str, cwd: Path) -> CheckResult:
    proc = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=False
    )
    return CheckResult(
        name=name,
        passed=(proc.returncode == 0),
        stdout=proc.stdout,
        stderr=proc.stderr,
        returncode=proc.returncode,
    )


def detect_default_branch(cwd: Path) -> str:
    for candidate in ("main", "master", "trunk"):
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            return candidate
    return "main"


def changed_files(cwd: Path, base_ref: str) -> list[str] | None:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return [f for f in proc.stdout.splitlines() if f.strip()]


def check_scope(layout: ProjectLayout, scope_allowlist: list[str]) -> CheckResult:
    if not scope_allowlist:
        return CheckResult("scope", True, "scope_allowlist empty; not enforced.")
    base = detect_default_branch(layout.root)
    changed = changed_files(layout.root, base)
    if changed is None:
        return CheckResult("scope", True, "git diff unavailable; scope check skipped.")
    out_of_scope = [
        f for f in changed
        if not any(fnmatch.fnmatch(f, glob) for glob in scope_allowlist)
    ]
    if out_of_scope:
        return CheckResult(
            "scope",
            False,
            f"changed in scope: {len(changed) - len(out_of_scope)}",
            "files changed outside scope_allowlist:\n  " + "\n  ".join(out_of_scope),
            1,
        )
    return CheckResult("scope", True, f"all {len(changed)} changed files in scope.")


def check_scenarios(cwd: Path, required: list[str]) -> CheckResult:
    if not required:
        return CheckResult("scenarios_required", True, "no scenarios_required listed.")
    expr = " or ".join(required)
    proc = subprocess.run(
        ["pytest", "tests/scenarios", "-q", "-k", expr],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return CheckResult(
        "scenarios_required",
        proc.returncode == 0,
        proc.stdout,
        proc.stderr,
        proc.returncode,
    )


def _format_summary(task_id: str, results: list[CheckResult]) -> str:
    lines = [f"# Verification — {task_id}\n", "| Check | Result |", "|---|---|"]
    for r in results:
        marker = "✅ pass" if r.passed else f"❌ fail (exit {r.returncode})"
        lines.append(f"| `{r.name}` | {marker} |")
    lines.append("")
    for r in results:
        if not r.passed:
            lines.append(f"\n## ❌ {r.name}\n")
            if r.stdout.strip():
                lines.append("**stdout:**\n```\n" + r.stdout.rstrip() + "\n```")
            if r.stderr.strip():
                lines.append("\n**stderr:**\n```\n" + r.stderr.rstrip() + "\n```")
    return "\n".join(lines) + "\n"


def verify_task(layout: ProjectLayout, task_id: str) -> VerificationResult:
    """Run a task's acceptance checks, write evidence, return structured result."""
    task_dir = find_task_dir(layout, task_id)
    acceptance_path = task_dir / "acceptance.yml"
    if not acceptance_path.is_file():
        raise TemplateError(f"{acceptance_path} not found.")

    with acceptance_path.open() as f:
        acceptance = yaml.safe_load(f) or {}

    results: list[CheckResult] = []

    for check in acceptance.get("checks") or []:
        name = check.get("name", "<unnamed>")
        cmd = check.get("run", "")
        if not cmd:
            continue
        result = run_check(name, cmd, layout.root)
        results.append(result)
        append_trace(
            task_dir, role="verifier", action="check_run",
            name=name, command=cmd, passed=result.passed, returncode=result.returncode,
        )

    scenarios_required = acceptance.get("scenarios_required") or []
    if scenarios_required:
        result = check_scenarios(layout.root, scenarios_required)
        results.append(result)
        append_trace(
            task_dir, role="verifier", action="scenarios_required",
            scenarios=scenarios_required, passed=result.passed,
        )

    scope_allowlist = acceptance.get("scope_allowlist") or []
    result = check_scope(layout, scope_allowlist)
    results.append(result)
    append_trace(
        task_dir, role="verifier", action="scope_check",
        allowlist=scope_allowlist, passed=result.passed,
    )

    summary = _format_summary(task_id, results)
    summary_path = task_dir / "evidence" / "verification.md"
    summary_path.write_text(summary)

    return VerificationResult(task_id=task_id, results=results, summary_path=summary_path)


# ═══════════════════════════════════════════════════════════════════════════
# update_code_map
# ═══════════════════════════════════════════════════════════════════════════

_SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "node_modules", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".worktrees", "dist", "build",
}
_SKIP_SUFFIXES = {".pyc", ".pyo", ".so", ".o"}


def parse_components(components_text: str) -> list[tuple[str, list[str]]]:
    """Return [(subsystem_name, [path_globs])] from COMPONENTS.md."""
    out: list[tuple[str, list[str]]] = []
    current_name: str | None = None
    current_paths: list[str] = []
    for line in components_text.splitlines():
        if line.startswith("## "):
            if current_name is not None:
                out.append((current_name, current_paths))
            current_name = line[3:].strip()
            current_paths = []
        elif current_name is not None:
            m = re.match(r"\s*-\s*\*\*Path\(s\):\*\*\s*(.+)$", line)
            if m:
                for p in m.group(1).split(","):
                    p = p.strip().strip("`").strip()
                    if p:
                        current_paths.append(p)
    if current_name is not None:
        out.append((current_name, current_paths))
    return out


def walk_paths(root: Path, globs: list[str]) -> list[Path]:
    matched: set[Path] = set()
    for raw_glob in globs:
        glob = raw_glob.rstrip("/")
        if "*" not in glob:
            glob = glob + "/**/*"
        elif glob.endswith("**"):
            glob = glob + "/*"
        try:
            for p in root.glob(glob):
                if not p.is_file():
                    continue
                if any(part in _SKIP_DIRS for part in p.parts):
                    continue
                if p.suffix in _SKIP_SUFFIXES:
                    continue
                matched.add(p)
        except Exception:
            continue
    return sorted(matched)


def render_subsystem_map(name: str, files: list[Path], root: Path) -> str:
    rel = [f.relative_to(root).as_posix() for f in files]
    lines = [f"# Code Map — {name}\n"]
    if not rel:
        lines.append("_No files matched the component paths. Either the subsystem\n")
        lines.append("hasn't been implemented yet, or COMPONENTS.md paths need updating._\n")
        return "\n".join(lines)
    groups: dict[str, list[str]] = {}
    for f in rel:
        groups.setdefault(f.split("/")[0], []).append(f)
    for top in sorted(groups):
        lines.append(f"\n## `{top}/`\n")
        for f in groups[top]:
            lines.append(f"- `{f}`")
    lines.append("")
    return "\n".join(lines)


def _render_index(subsystems: list[tuple[str, list[Path]]]) -> str:
    import datetime as _dt

    stamp = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# Code Map — Index\n",
        f"_Generated by KEEL update_code_map at {stamp}._\n",
        "\n_For each subsystem, see the linked per-subsystem map._\n",
    ]
    for name, files in subsystems:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        lines.append(f"\n## {name}")
        lines.append(f"- {len(files)} files — [`docs/code-map/{slug}.md`](./{slug}.md)")
    return "\n".join(lines) + "\n"


@dataclass
class CodeMapResult:
    subsystems: int
    total_files: int
    index_path: Path


def update_code_map(layout: ProjectLayout) -> CodeMapResult:
    """Refresh docs/code-map/ from COMPONENTS.md and the source tree."""
    components_path = layout.root / "COMPONENTS.md"
    if not components_path.is_file():
        raise TemplateError("COMPONENTS.md not found. Has the bootstrap been run?")
    subsystems_decl = parse_components(components_path.read_text())

    out_dir = layout.root / "docs" / "code-map"
    out_dir.mkdir(parents=True, exist_ok=True)

    resolved: list[tuple[str, list[Path]]] = []
    for name, paths in subsystems_decl:
        files = walk_paths(layout.root, paths) if paths else []
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        (out_dir / f"{slug}.md").write_text(render_subsystem_map(name, files, layout.root))
        resolved.append((name, files))

    index_path = out_dir / "INDEX.md"
    index_path.write_text(_render_index(resolved))
    total = sum(len(f) for _, f in resolved)
    return CodeMapResult(subsystems=len(resolved), total_files=total, index_path=index_path)
