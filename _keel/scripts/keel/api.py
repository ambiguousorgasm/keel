"""KeelRepo — the stateless Python API surface for KEEL.

This is the integration layer other tools (AI APIs, an MCP server, custom
orchestrators) import. Design constraints, enforced throughout:

- STATELESS. A KeelRepo holds only the resolved project *location*, never
  project *content*. Every method re-reads files. If the object is discarded,
  nothing is lost because nothing was cached.
- THE REPO IS CANONICAL. Every method reads or writes files under the project
  root. There is no separate database, daemon, or in-memory model of truth.
- SAME GATES AS THE CLI. verify_task() runs the identical scope/scenario checks
  the CLI does. There is no convenience path that bypasses verification.

Example:

    from keel.api import KeelRepo

    repo = KeelRepo.discover()                 # finds _keel/ from CWD
    task = repo.create_task("storage-init")    # CreatedTask
    ctx  = repo.build_context(task.task_id)    # ContextResult (also writes file)
    res  = repo.verify_task(task.task_id)       # VerificationResult
    if not res.passed:
        for c in res.results:
            if not c.passed:
                print(c.name, c.stderr)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import operations as ops
from . import skills as skills_mod
from .errors import GovernanceNotFound, KeelError, TaskNotFound
from .helpers import (
    ProjectLayout,
    find_project_root,
    find_task_dir,
    load_spec_model,
    parse_task_id,
    task_state,
)

# Re-export the result types so callers can import everything from keel.api.
from .operations import (  # noqa: F401
    CheckResult,
    CodeMapResult,
    ContextResult,
    CreatedTask,
    VerificationResult,
)
from .skills import Skill, SkillInfo  # noqa: F401


# Canonical governance documents the API will read by name.
GOVERNANCE_DOCS = (
    "PRINCIPLES.md",
    "CORE.md",
    "COMPONENTS.md",
    "DECISIONS.md",
    "STATUS.md",
    "CHANGELOG.md",
    "AGENTS.md",
)


@dataclass
class TaskInfo:
    """Lightweight summary of a task packet (no file contents loaded)."""

    task_id: str
    state: str          # active | completed | blocked
    prefix: str
    number: int
    slug: str
    path: Path
    has_plan: bool
    has_context: bool
    has_review: bool
    has_handoff: bool


class KeelRepo:
    """Stateless handle to a KEEL-managed repository.

    Construct via `KeelRepo.discover()` (walks up from CWD) or
    `KeelRepo(root)` with an explicit project root.
    """

    def __init__(self, root: Path | str) -> None:
        root = Path(root).resolve()
        if not (root / "_keel").is_dir():
            raise KeelError(f"{root} is not a KEEL-managed repository (no _keel/).")
        self.layout = ProjectLayout.from_root(root)

    @classmethod
    def discover(cls, start: Path | str | None = None) -> "KeelRepo":
        """Find the project root by walking up from `start` (default CWD)."""
        root = find_project_root(Path(start) if start else None)
        return cls(root)

    @property
    def root(self) -> Path:
        return self.layout.root

    # ── write operations ────────────────────────────────────────────────────

    def create_task(
        self,
        slug: str,
        *,
        task_type: str = "implementation",
        prefix_override: str | None = None,
    ) -> CreatedTask:
        """Scaffold a new task packet. Returns CreatedTask. Raises KeelError."""
        return ops.create_task(
            self.layout, slug, task_type=task_type, prefix_override=prefix_override
        )

    def build_context(self, task_id: str) -> ContextResult:
        """Generate context.md for a task. Writes the file, returns ContextResult."""
        return ops.build_context(self.layout, task_id)

    def verify_task(self, task_id: str) -> VerificationResult:
        """Run the task's acceptance checks (same gates as the CLI)."""
        return ops.verify_task(self.layout, task_id)

    def update_code_map(self) -> CodeMapResult:
        """Refresh docs/code-map/ from COMPONENTS.md and the source tree."""
        return ops.update_code_map(self.layout)

    # ── read operations ─────────────────────────────────────────────────────

    def get_spec_model(self, validate: bool = True) -> dict[str, Any]:
        """Load and (by default) schema-validate _keel/spec_model.yml."""
        return load_spec_model(self.layout, validate=validate)

    def read_governance(self, name: str) -> str:
        """Return the verbatim text of a governance document by filename.

        e.g. read_governance("PRINCIPLES.md"). Raises GovernanceNotFound.
        """
        path = self.root / name
        if not path.is_file():
            raise GovernanceNotFound(f"{name} not found at {path}.")
        return path.read_text()

    def list_governance(self) -> list[str]:
        """Return the canonical governance docs that currently exist."""
        return [d for d in GOVERNANCE_DOCS if (self.root / d).is_file()]

    def list_tasks(self, state: str | None = None) -> list[TaskInfo]:
        """List task packets, optionally filtered by state.

        state: None (all) | 'active' | 'completed' | 'blocked'.
        Sorted by (prefix, number).
        """
        bases = {
            "active": self.layout.tasks_active,
            "completed": self.layout.tasks_completed,
            "blocked": self.layout.tasks_blocked,
        }
        if state is not None and state not in bases:
            raise KeelError(
                f"unknown state {state!r}; expected one of {', '.join(bases)}."
            )
        chosen = {state: bases[state]} if state else bases

        infos: list[TaskInfo] = []
        for st, base in chosen.items():
            if not base.is_dir():
                continue
            for entry in sorted(base.iterdir()):
                if not entry.is_dir():
                    continue
                parsed = parse_task_id(entry.name)
                if parsed is None:
                    continue
                prefix, number, slug = parsed
                infos.append(
                    TaskInfo(
                        task_id=entry.name,
                        state=st,
                        prefix=prefix,
                        number=number,
                        slug=slug,
                        path=entry,
                        has_plan=(entry / "plan.md").is_file(),
                        has_context=(entry / "context.md").is_file(),
                        has_review=(entry / "review.md").is_file(),
                        has_handoff=(entry / "handoff.md").is_file(),
                    )
                )
        infos.sort(key=lambda t: (t.prefix, t.number))
        return infos

    def get_task(self, task_id: str) -> TaskInfo:
        """Return the TaskInfo for a single task. Raises TaskNotFound."""
        find_task_dir(self.layout, task_id)  # raises TaskNotFound if absent
        for info in self.list_tasks():
            if info.task_id == task_id:
                return info
        raise TaskNotFound(f"task {task_id!r} not found.")

    def read_task_file(self, task_id: str, filename: str) -> str:
        """Read a file inside a task packet (e.g. 'brief.md', 'context.md')."""
        task_dir = find_task_dir(self.layout, task_id)
        path = task_dir / filename
        if not path.is_file():
            raise TaskNotFound(f"{filename} not found in task {task_id!r}.")
        return path.read_text()

    # ── skills ──────────────────────────────────────────────────────────────

    def list_skills(self) -> list[SkillInfo]:
        """List installed skills (frontmatter only — progressive disclosure)."""
        return skills_mod.list_skills(self.layout.skills)

    def get_skill(self, skill_id: str) -> Skill:
        """Fully load a skill (frontmatter + body). Raises SkillNotFound."""
        return skills_mod.load_skill(self.layout.skills, skill_id)

    def load_skill_file(self, skill_id: str, relpath: str) -> str:
        """Read a bundled file inside a skill folder."""
        return skills_mod.load_skill_file(self.layout.skills, skill_id, relpath)

    def search_skills(self, query: str) -> list[SkillInfo]:
        """Find skills whose id/name/description/keywords match `query`."""
        return skills_mod.search_skills(self.layout.skills, query)

    def skills_index(self) -> str:
        """Compact markdown index (id + description) to inject into a prompt.

        Hand an agent THIS, not every skill body; it pulls full skills on demand.
        """
        return skills_mod.skills_index(self.layout.skills)

    def sync_agent_skills(self) -> dict[str, list[str]]:
        """Generate the `.agents/skills/` mirrors + catalog from canonical skills.

        Single source of truth stays `_keel/skills/`; this projects it into the
        portable Agent Skills layout that Zed, Claude Code, Codex, etc. discover.
        Returns {"written": [...], "removed": [...]}.
        """
        result = skills_mod.export_agent_skills(
            self.layout.skills, self.layout.agents_skills
        )
        self.layout.agents_catalog.parent.mkdir(parents=True, exist_ok=True)
        self.layout.agents_catalog.write_text(
            skills_mod.render_catalog(self.layout.skills)
        )
        return result

    def lint_skills(self) -> list[str]:
        """Validate the skill library (frontmatter, dupes, manual-only safeguard,
        and `.agents` mirror/catalog drift). Returns a list of problems."""
        return skills_mod.lint_skills(
            self.layout.skills,
            agents_skills_dir=self.layout.agents_skills,
            catalog_path=self.layout.agents_catalog,
        )

    def create_skill(
        self,
        skill_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Skill:
        """Scaffold a new skill folder from the SKILL template. Returns the Skill."""
        template = self.layout.templates / "SKILL.template.md"
        return skills_mod.create_skill(
            self.layout.skills,
            skill_id,
            name=name,
            description=description,
            template=template if template.is_file() else None,
        )
