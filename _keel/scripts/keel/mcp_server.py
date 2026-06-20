"""KEEL MCP server — exposes the KeelRepo API as MCP tools.

Built on the official MCP SDK's bundled FastMCP (`mcp.server.fastmcp`), pinned
`mcp>=1.27,<2`. This is Layer 2: a thin, stateless wrapper over Layer 1
(`keel.api.KeelRepo`). It adds no state and no orchestration — every tool call
is a repo operation, and the repository remains the single source of truth.

The server is bound to ONE project (one `_keel/` repo), resolved at startup
from `--root`, then `KEEL_ROOT`, then discovery upward from CWD. This matches how
MCP servers are normally scoped: one server per project.

Write tools (create_task, build_context, verify_task, create_skill,
update_code_map) perform real writes immediately — per the project's chosen
"trust the gates" policy, there is no preview/staging step. The gates
(scope_allowlist, scenarios, principle review) are enforced by `verify_task`
exactly as they are from the CLI.

Run:
    keel-mcp --root /path/to/repo            # stdio (for Claude Desktop / Code)
    keel-mcp --transport streamable-http     # remote
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from .api import KeelRepo
from .helpers import find_project_root

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "The MCP server requires the 'mcp' package. Install the optional extra:\n"
        "    pip install -e '_keel[mcp]'\n"
        "or: pip install 'mcp>=1.27,<2'"
    ) from e


_TRUNC = 4000  # cap large stdout/stderr blobs in tool output


def _trunc(s: str, limit: int = _TRUNC) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n…[truncated {len(s) - limit} chars]"


# ─── serializers (dataclass → JSON-safe dict) ───────────────────────────────


def _task_info(t: Any) -> dict[str, Any]:
    return {
        "task_id": t.task_id,
        "state": t.state,
        "prefix": t.prefix,
        "number": t.number,
        "slug": t.slug,
        "path": str(t.path),
        "has_plan": t.has_plan,
        "has_context": t.has_context,
        "has_review": t.has_review,
        "has_handoff": t.has_handoff,
    }


def _skill_info(s: Any) -> dict[str, Any]:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "version": s.version,
        "keywords": s.keywords,
        "bundled_files": s.bundled_files,
        "path": str(s.path),
    }


def resolve_root(explicit: str | None = None) -> Path:
    """Resolve which repo to bind to: explicit arg → KEEL_ROOT env → CWD discovery."""
    if explicit:
        root = Path(explicit).resolve()
        if not (root / "_keel").is_dir():
            raise SystemExit(f"{root} is not a KEEL repo (no _keel/).")
        return root
    env = os.environ.get("KEEL_ROOT")
    if env:
        root = Path(env).resolve()
        if not (root / "_keel").is_dir():
            raise SystemExit(f"KEEL_ROOT={root} is not a KEEL repo (no _keel/).")
        return root
    return find_project_root()


def build_server(root: Path | str) -> FastMCP:
    """Construct a FastMCP server bound to the KEEL repo at `root`.

    Tools close over a single KeelRepo (which holds only the location; every
    call re-reads files). Returned server is testable in-process via
    `await server.call_tool(name, args)`.
    """
    repo = KeelRepo(root)
    mcp = FastMCP("keel")

    # ── orientation ──────────────────────────────────────────────────────────

    @mcp.tool()
    def keel_project_info() -> dict[str, Any]:
        """Summarize this KEEL project: name, prefix, phases, and which
        governance documents exist. Call this first to orient yourself."""
        model = repo.get_spec_model(validate=False)
        return {
            "project_name": model.get("project_name"),
            "project_prefix": model.get("project_prefix"),
            "purpose": model.get("purpose"),
            "phases": model.get("phases", []),
            "governance_docs": repo.list_governance(),
            "root": str(repo.root),
        }

    # ── tasks ────────────────────────────────────────────────────────────────

    @mcp.tool()
    def keel_list_tasks(state: str | None = None) -> list[dict[str, Any]]:
        """List task packets. `state` is optional: 'active', 'completed', or
        'blocked'; omit for all. Returns lightweight task metadata (no file
        bodies)."""
        return [_task_info(t) for t in repo.list_tasks(state)]

    @mcp.tool()
    def keel_get_task(task_id: str) -> dict[str, Any]:
        """Get metadata for one task packet by ID (which packet files exist,
        what state it's in)."""
        return _task_info(repo.get_task(task_id))

    @mcp.tool()
    def keel_read_task_file(task_id: str, filename: str) -> str:
        """Read a file inside a task packet, e.g. filename='brief.md',
        'plan.md', 'context.md', 'review.md', or 'handoff.md'."""
        return repo.read_task_file(task_id, filename)

    @mcp.tool()
    def keel_create_task(
        slug: str,
        task_type: str = "implementation",
        prefix_override: str | None = None,
    ) -> dict[str, Any]:
        """Scaffold a new task packet under tasks/active/. `slug` is kebab-case.
        `task_type` is 'implementation' (default) or 'principle-amendment'.
        Writes the packet immediately and returns its paths."""
        t = repo.create_task(
            slug, task_type=task_type, prefix_override=prefix_override
        )
        return {
            "task_id": t.task_id,
            "path": str(t.path),
            "brief": str(t.brief),
            "acceptance": str(t.acceptance),
            "task_type": t.task_type,
        }

    @mcp.tool()
    def keel_build_context(task_id: str) -> dict[str, Any]:
        """Generate a task's context.md from its brief's Relevant-sources section
        (verbatim excerpts, cache-stable ordering). Writes the file and returns
        metadata + any warnings. Read the result with keel_read_task_file(task_id,
        'context.md')."""
        r = repo.build_context(task_id)
        return {
            "task_id": r.task_id,
            "path": str(r.path),
            "sources": r.sources,
            "warnings": r.warnings,
        }

    @mcp.tool()
    def keel_verify_task(task_id: str) -> dict[str, Any]:
        """Run a task's acceptance checks (the SAME gates as the CLI: shell
        checks, required scenarios, and scope_allowlist enforcement). Writes
        evidence and returns a structured pass/fail breakdown. This is the gate;
        do not treat a task as done until it passes."""
        r = repo.verify_task(task_id)
        return {
            "task_id": r.task_id,
            "passed": r.passed,
            "summary_path": str(r.summary_path),
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "returncode": c.returncode,
                    "stdout": _trunc(c.stdout),
                    "stderr": _trunc(c.stderr),
                }
                for c in r.results
            ],
        }

    # ── governance ───────────────────────────────────────────────────────────

    @mcp.tool()
    def keel_read_governance(name: str) -> str:
        """Read a governance document verbatim by filename, e.g. 'PRINCIPLES.md',
        'CORE.md', 'COMPONENTS.md', 'DECISIONS.md', 'STATUS.md', 'AGENTS.md'.
        PRINCIPLES overrides CORE; CORE overrides the other satellites."""
        return repo.read_governance(name)

    @mcp.tool()
    def keel_list_governance() -> list[str]:
        """List which canonical governance documents currently exist in the repo."""
        return repo.list_governance()

    @mcp.tool()
    def keel_get_spec_model() -> dict[str, Any]:
        """Return the structured, schema-validated project model from
        _keel/spec_model.yml (subsystems, invariants, failure modes, phases)."""
        return repo.get_spec_model()

    @mcp.tool()
    def keel_update_code_map() -> dict[str, Any]:
        """Refresh docs/code-map/ from COMPONENTS.md and the source tree.
        Returns subsystem and file counts."""
        r = repo.update_code_map()
        return {
            "subsystems": r.subsystems,
            "total_files": r.total_files,
            "index_path": str(r.index_path),
        }

    # ── skills ───────────────────────────────────────────────────────────────

    @mcp.tool()
    def keel_skills_index() -> str:
        """Return a compact markdown index (id + description) of all installed
        skills. Call this FIRST when looking for a skill — it's cheap. Then load
        only the relevant one with keel_get_skill (progressive disclosure)."""
        return repo.skills_index()

    @mcp.tool()
    def keel_list_skills() -> list[dict[str, Any]]:
        """List installed skills with their metadata (frontmatter only)."""
        return [_skill_info(s) for s in repo.list_skills()]

    @mcp.tool()
    def keel_get_skill(skill_id: str) -> dict[str, Any]:
        """Fully load one skill by id: its metadata plus the full instruction
        body. Call after surveying keel_skills_index. The 'body' is the
        instructions to follow."""
        s = repo.get_skill(skill_id)
        return {**_skill_info(s), "body": s.body}

    @mcp.tool()
    def keel_search_skills(query: str) -> list[dict[str, Any]]:
        """Find skills whose id, name, description, or keywords match `query`."""
        return [_skill_info(s) for s in repo.search_skills(query)]

    @mcp.tool()
    def keel_load_skill_file(skill_id: str, relpath: str) -> str:
        """Read a bundled file inside a skill folder, e.g.
        relpath='scripts/helper.py' or 'references/notes.md'. Path-traversal is
        blocked. KEEL exposes the file; deciding whether to run a script is yours."""
        return repo.load_skill_file(skill_id, relpath)

    @mcp.tool()
    def keel_create_skill(
        skill_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Scaffold a new skill folder under _keel/skills/ from the template.
        `skill_id` is kebab-case (becomes the folder name). Writes immediately
        and returns the new skill's metadata."""
        s = repo.create_skill(skill_id, name=name, description=description)
        return _skill_info(s)

    @mcp.tool()
    def keel_skills_sync() -> dict[str, Any]:
        """Publish the canonical skills to .agents/skills/ (the portable Agent
        Skills layout that Zed, Claude Code, Codex, and Gemini discover) and
        regenerate the .agents/SKILLS.md catalog. Returns the written and
        removed skill ids. Idempotent."""
        return repo.sync_agent_skills()

    @mcp.tool()
    def keel_skills_lint() -> dict[str, Any]:
        """Validate the skill library: frontmatter, duplicate names, manual-only
        safeguards, and .agents mirror/catalog drift. Returns {ok, problems}."""
        problems = repo.lint_skills()
        return {"ok": not problems, "problems": problems}

    return mcp


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="keel-mcp", description="Run the KEEL MCP server."
    )
    parser.add_argument(
        "--root", default=None,
        help="project root (defaults to $KEEL_ROOT, then upward discovery from CWD)",
    )
    parser.add_argument(
        "--transport", default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="MCP transport (default stdio, for Claude Desktop / Code)",
    )
    args = parser.parse_args()

    root = resolve_root(args.root)
    server = build_server(root)
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
