"""Low-level KEEL helpers: path discovery, spec loading, markdown extraction.

Moved from the former lib/keel.py. The behavioral change vs. that module: these
raise KeelError subclasses instead of SystemExit, so API callers can handle
failures. The CLIs translate KeelError into exit codes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
import jsonschema

from .errors import ProjectNotFound, SpecModelError, TaskNotFound


# ─── project layout ──────────────────────────────────────────────────────────

KEEL_DIRNAME = "_keel"


@dataclass(frozen=True)
class ProjectLayout:
    """Resolved project paths. All absolute. Holds no project *content* — just
    locations — so it is safe to construct once and reuse."""

    root: Path
    keel: Path
    spec_model: Path
    schema: Path
    templates: Path
    skills: Path
    tasks_active: Path
    tasks_completed: Path
    tasks_blocked: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectLayout":
        keel = root / KEEL_DIRNAME
        return cls(
            root=root,
            keel=keel,
            spec_model=keel / "spec_model.yml",
            schema=keel / "spec_model.schema.json",
            templates=keel / "templates",
            skills=keel / "skills",
            tasks_active=root / "tasks" / "active",
            tasks_completed=root / "tasks" / "completed",
            tasks_blocked=root / "tasks" / "blocked",
        )


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from `start` (default CWD) until a directory containing _keel/
    is found. Raises ProjectNotFound if none found.
    """
    start = (start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / KEEL_DIRNAME).is_dir():
            return candidate
    raise ProjectNotFound(
        f"could not find a {KEEL_DIRNAME}/ directory walking up from {start}. "
        f"Run from inside a KEEL-managed repository."
    )


def get_layout() -> ProjectLayout:
    """Convenience: discover project root and return layout."""
    return ProjectLayout.from_root(find_project_root())


# ─── spec_model loading ──────────────────────────────────────────────────────


def load_spec_model(layout: ProjectLayout, validate: bool = True) -> dict[str, Any]:
    """Load _keel/spec_model.yml and (optionally) validate against the schema.

    Raises SpecModelError on any failure.
    """
    if not layout.spec_model.is_file():
        raise SpecModelError(
            f"{layout.spec_model} not found. Has the bootstrap been run?"
        )
    with layout.spec_model.open() as f:
        model = yaml.safe_load(f)
    if not isinstance(model, dict):
        raise SpecModelError(
            f"{layout.spec_model} did not parse to a dict (got {type(model).__name__})."
        )
    if validate:
        with layout.schema.open() as f:
            schema = json.load(f)
        try:
            jsonschema.validate(instance=model, schema=schema)
        except jsonschema.ValidationError as e:
            path = "/".join(str(p) for p in e.absolute_path) or "<root>"
            raise SpecModelError(
                f"{layout.spec_model} failed schema validation:\n  {e.message}\n"
                f"  at path: {path}"
            ) from e
    return model


# ─── markdown section extraction (VERBATIM) ──────────────────────────────────

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def extract_markdown_section(
    markdown: str, heading: str, *, fuzzy: bool = True
) -> str | None:
    """Return the verbatim text of the section under the given heading.

    A "section" extends from the matched heading to the next heading at the
    same or higher level (or end of file). The matched heading is included.

    DO NOT modify, summarize, or paraphrase the returned text — KEEL's
    compaction rule is verbatim-only.
    """
    target = _normalize(heading) if fuzzy else heading
    matches = list(_HEADING_RE.finditer(markdown))
    for i, m in enumerate(matches):
        level = len(m.group(1))
        text = m.group(2)
        candidate = _normalize(text) if fuzzy else text
        if candidate != target:
            continue
        start = m.start()
        end = len(markdown)
        for j in range(i + 1, len(matches)):
            next_level = len(matches[j].group(1))
            if next_level <= level:
                end = matches[j].start()
                break
        return markdown[start:end].rstrip() + "\n"
    return None


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


# ─── task ID helpers ─────────────────────────────────────────────────────────

_TASK_ID_RE = re.compile(r"^([A-Z]{2,6})-(\d{3,})-(.+)$")


def parse_task_id(task_id: str) -> tuple[str, int, str] | None:
    """Parse PREFIX-NNN-slug. Returns (prefix, number, slug) or None."""
    m = _TASK_ID_RE.match(task_id)
    if not m:
        return None
    return m.group(1), int(m.group(2)), m.group(3)


def find_task_dir(layout: ProjectLayout, task_id: str) -> Path:
    """Locate a task folder by ID across active/completed/blocked.
    Raises TaskNotFound if absent.
    """
    for base in (layout.tasks_active, layout.tasks_completed, layout.tasks_blocked):
        candidate = base / task_id
        if candidate.is_dir():
            return candidate
    raise TaskNotFound(
        f"task {task_id!r} not found under tasks/{{active,completed,blocked}}/"
    )


def task_state(layout: ProjectLayout, task_id: str) -> str:
    """Return 'active' | 'completed' | 'blocked' for a task. Raises TaskNotFound."""
    mapping = {
        layout.tasks_active: "active",
        layout.tasks_completed: "completed",
        layout.tasks_blocked: "blocked",
    }
    for base, name in mapping.items():
        if (base / task_id).is_dir():
            return name
    raise TaskNotFound(f"task {task_id!r} not found.")


def next_task_number(layout: ProjectLayout, prefix: str) -> int:
    """Find the next available task number for the given prefix.

    Scans all three task directories so completed/blocked tasks aren't
    accidentally re-numbered.
    """
    used: set[int] = set()
    for base in (layout.tasks_active, layout.tasks_completed, layout.tasks_blocked):
        if not base.is_dir():
            continue
        for entry in base.iterdir():
            if not entry.is_dir():
                continue
            parsed = parse_task_id(entry.name)
            if parsed and parsed[0] == prefix:
                used.add(parsed[1])
    return (max(used) + 1) if used else 1


# ─── trace logging ───────────────────────────────────────────────────────────


def append_trace(task_dir: Path, **fields: Any) -> None:
    """Append a JSON line to evidence/trace.jsonl. Creates the file if missing."""
    import datetime as _dt

    evidence_dir = task_dir / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    trace = evidence_dir / "trace.jsonl"
    record = {"ts": _dt.datetime.now(_dt.timezone.utc).isoformat(), **fields}
    with trace.open("a") as f:
        f.write(json.dumps(record) + "\n")
