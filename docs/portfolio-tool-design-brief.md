# Design Brief: A Portfolio Manager for KEEL Projects

> **How to use this document:** Paste it as the opening prompt to an AI you want
> to design (not yet implement) a multi-project portfolio/status tool. It
> contains everything the AI needs to know about KEEL's integration surface so it
> can design against a stable, accurate target. Your job after pasting: answer the
> "Open questions" at the end, which the AI should raise before designing.

---

## Your role

You are designing a **portfolio manager**: a tool that sits *above* a set of
software projects, periodically reviews each one, and maintains a minimal log per
project plus a cross-project overview — what projects exist, what stage of
development each is in, what's active, what's stalled or blocked. This is for
*higher-level organization and tracking*, deliberately much lighter than the
detailed tracking that happens inside any single project.

Many (not necessarily all) of the projects it watches are **KEEL projects**. KEEL
is a repo-native development operating system; this brief tells you exactly how a
KEEL project exposes its status so your tool can read it. Design the tool to read
KEEL projects richly and to degrade gracefully on non-KEEL projects.

Do **not** start coding. First produce the design artifacts listed at the end,
and raise the open questions. Then wait for direction.

---

## The single most important integration principle

**KEEL's core invariant is: the repository is the source of truth.** Everything
about a project's state lives in files inside that project's repo — there is no
database, no daemon, no central server holding project state. This is what makes
your tool easy and safe to build:

- **You integrate by reading repos, not by hooking a runtime.** There is nothing
  to subscribe to and no process to keep alive. You scan project directories and
  read files. That is the entire integration model.
- **Your tool is strictly read-only with respect to projects.** It must NEVER
  write into a project repo. A portfolio tool that can't corrupt a project is a
  portfolio tool you can run unattended. All of your tool's own state (its logs,
  its index) lives in the tool's own storage, never inside the watched projects.
- **Cross-project state belongs to your tool, not to KEEL.** KEEL governs one
  project, repo-locally. The notion of "all my projects" is inherently *not*
  repo-local — it's about relationships between repos. That's your tool's domain.
  Do not try to push portfolio state back into individual repos.

---

## How to detect a KEEL project

Given a candidate directory, it is a KEEL project if it contains a `_keel/`
subdirectory with a `_keel/BOOTSTRAP.md` file. (The `_keel/` directory is the OS;
`BOOTSTRAP.md` confirms it's a real KEEL install, not a coincidental folder name.)

A project that has been *initialized* but not yet *bootstrapped by an AI* will
have `_keel/` and a placeholder `_keel/spec_model.yml` but will be missing the
governance docs (PRINCIPLES.md, CORE.md, AGENTS.md). Your tool should treat this
as a valid but "not yet bootstrapped" state, not an error — it's a real lifecycle
stage worth surfacing in the portfolio.

---

## The integration contract: what a KEEL project exposes

There are two ways to read a KEEL project's status. **Prefer Path A; fall back to
Path B.**

### Path A (preferred): `keel status --json`

The clean machine-readable seam is a single command that emits a project's status
as one JSON object. Run it with the project root as the working directory (or
pass `--root <path>`):

```
keel status --json
```

> **Build status of this command:** This is the *recommended* integration seam and
> is small and in-scope for KEEL, but it may not exist in the installed KEEL
> version yet. Design your tool to consume this JSON as the primary path, and
> implement Path B (direct file reads) as a fallback that produces the same
> internal model. If the command is absent, the KEEL maintainer can add it
> cheaply; your tool should not depend on its presence to function.

**Target JSON shape** (design against this; treat fields as optional-tolerant):

```json
{
  "schema_version": "1.0",
  "is_keel_project": true,
  "keel_version": "0.1.0",
  "project": {
    "name": "KEEL Gate Simulator",
    "prefix": "SIM",
    "purpose": "One-line purpose from the spec.",
    "root": "/abs/path/to/project"
  },
  "phase": {
    "current": "P2",
    "current_name": "metrics",
    "all": [
      {"id": "P0", "name": "substrate and profiles", "done": true},
      {"id": "P1", "name": "gate and runner", "done": true},
      {"id": "P2", "name": "metrics", "done": false}
    ],
    "completed_count": 2,
    "total_count": 4
  },
  "tasks": {
    "active": 3,
    "blocked": 1,
    "completed": 12,
    "active_ids": ["SIM-007-foo", "SIM-008-bar"],
    "blocked_ids": ["SIM-005-baz"]
  },
  "governance_present": ["PRINCIPLES.md", "CORE.md", "COMPONENTS.md",
                          "DECISIONS.md", "STATUS.md", "CHANGELOG.md", "AGENTS.md"],
  "health": {
    "bootstrapped": true,
    "spec_model_valid": true,
    "warnings": []
  },
  "activity": {
    "last_changelog_date": "2026-06-19",
    "last_modified_utc": "2026-06-19T19:44:00Z"
  }
}
```

### Path B (fallback / available today): read the canonical files

Every KEEL project exposes its state through files at predictable locations. Your
tool can read these directly (in any language) or via KEEL's Python API (below).

**Structured project model — `_keel/spec_model.yml`** (YAML; the richest source):
top-level keys include `project_name`, `project_prefix`, `purpose`, `tech_stack`,
`subsystems` (list), `invariants` (list), `failure_modes` (list), and `phases`
(list of `{id, name, depends_on?}`). This is schema-validated, so it's reliable to
parse. **Use this for project identity and the phase list.**

**Human status — `STATUS.md`** (repo root; semi-structured markdown). Sections:
`## Current phase`, `## Roadmap` (a checkbox list of phases — `- [x]` done,
`- [ ]` pending), `## Built & verified`, `## Known gaps & defects`. Scrapeable but
prose-y — this is exactly why Path A's JSON is preferred. Use the `## Roadmap`
checkboxes to compute phase progress if Path A isn't available.

**Work queue — `tasks/{active,completed,blocked}/`** (repo root). Each task is a
directory named `PREFIX-NNN-slug/`. **Counting the subdirectories in each state
gives you the task counts directly** — no parsing needed. A non-empty
`tasks/blocked/` is a portfolio red flag worth surfacing.

**Recent activity — `CHANGELOG.md`** (repo root): dated entries, newest first.
The top entry's date is a good "last meaningful activity" signal. (Git log or file
mtimes are a secondary signal.)

**Other governance (read only if you need detail):** `PRINCIPLES.md`, `CORE.md`,
`COMPONENTS.md`, `DECISIONS.md`, `AGENTS.md` at the repo root. The *presence* of
these is itself signal: their absence means the project is initialized but not yet
bootstrapped.

### Path B via the KEEL Python API (if your tool is in Python)

KEEL ships a `keel` package with a stateless, read-only `KeelRepo` surface. If
your tool is Python, this is cleaner than hand-parsing:

```python
from keel import KeelRepo

repo = KeelRepo(project_root)            # raises if not a KEEL repo
model   = repo.get_spec_model()          # dict: name, prefix, phases, subsystems, ...
status  = repo.read_governance("STATUS.md")   # str (verbatim)
present = repo.list_governance()         # list[str] of governance docs that exist
active   = repo.list_tasks("active")     # list[TaskInfo]
blocked  = repo.list_tasks("blocked")
done     = repo.list_tasks("completed")
```

`list_tasks(state)` returns `TaskInfo` objects with: `task_id`, `state`, `prefix`,
`number`, `slug`, `path`, and booleans `has_plan`, `has_context`, `has_review`,
`has_handoff` (useful for showing how far each active task has progressed). All
methods re-read files on each call (stateless), and none write.

> If your tool is NOT Python, use Path A (the JSON command) or parse the files in
> Path B directly — `spec_model.yml` is YAML, `tasks/*/` are countable directories,
> `STATUS.md`/`CHANGELOG.md` are markdown. You do not need KEEL installed to read a
> KEEL project's files; you only need it for the `keel status --json` command and
> the Python API.

---

## Graceful degradation: non-KEEL projects

Your tool should still report on projects that aren't KEEL-managed, just with less
structure. When `_keel/` is absent, fall back to generic signals:

- **Identity:** directory name; `README.md` first heading if present.
- **Activity:** last git commit date (`git log -1 --format=%cI`) if it's a git
  repo, else newest-file mtime.
- **Status:** unavailable — mark as "unmanaged / no structured status."

Surface these as a distinct category ("unmanaged projects") so the overview is
honest about which projects have real status data and which are just being noticed.
This fallback is a feature: it means your tool watches a whole directory of work,
not only the KEEL ones.

---

## What the tool must produce (functional requirements)

**Per-project log (minimal, much lighter than in-project tracking).** For each
KEEL project, a short maintained record answering: what is this project (name,
one-line purpose), what phase is it in, how far through its phases, how many tasks
are active / blocked / done, when did it last show activity, and any blocked tasks
or known gaps. This log is *append-light* — it tracks change over time (e.g. "moved
P1 → P2 on 2026-06-19"), not every internal event.

**Portfolio overview (cross-project).** A single view answering: what projects
exist, what development stage each is in, which are actively progressing, which are
stalled (no recent activity) or blocked (non-empty `tasks/blocked/`), and which are
initialized-but-not-bootstrapped. This is the "what's going on across everything"
surface.

**Review cadence.** The tool reviews projects automatically (you choose the
mechanism with the user — scheduled scan, on-demand, or watch). Each review reads
the current state and updates the per-project log + overview.

Keep the output *minimal by design*. The detailed truth lives in each project; your
tool's value is the bird's-eye view, not a re-implementation of in-project tracking.

---

## Hard constraints (design principles — do not violate)

1. **Read-only on projects.** Never write into a watched repo. All tool state lives
   in the tool's own storage.
2. **Repo is truth; your index is a cache.** Treat your stored data as a derived
   cache that can always be rebuilt by re-scanning. Never let it become a second
   source of truth that can drift from the repos.
3. **Degrade, don't fail.** A malformed, half-bootstrapped, or non-KEEL project
   must produce a reduced report, never crash the scan.
4. **Don't duplicate in-project tracking.** If a detail belongs inside a project's
   own STATUS/tasks, link to it; don't mirror it.
5. **Stable contract only.** Depend on the documented surface above (the canonical
   files, `keel status --json`, `KeelRepo` read methods). Do not reach into KEEL
   internals or undocumented files.

---

## Explicitly out of scope

- Writing to, modifying, or governing any individual project (that's KEEL's job).
- Running or orchestrating project work, triggering tasks, or driving agents.
- Re-implementing per-task detail (briefs, diffs, reviews) — link, don't mirror.
- Requiring a long-running daemon inside any project repo.

---

## What to deliver (this design phase)

1. **A one-paragraph product definition** in your own words, confirming you've
   understood the boundary (portfolio-above-projects, read-only, repo-is-truth).
2. **A proposed architecture**: how the tool discovers projects, reads status
   (Path A with Path B fallback), stores its own logs/index, and renders the two
   outputs (per-project log + portfolio overview).
3. **A data model** for the tool's own storage (the per-project log entry shape and
   the portfolio index), explicitly marked as a rebuildable cache.
4. **The review/cadence mechanism** options with a recommendation.
5. **The degradation behavior** for non-KEEL and half-bootstrapped projects.
6. **Answers/assumptions** for the open questions below, flagged as assumptions.

---

## Open questions to resolve with the user before designing

- **Scope of "projects":** one parent directory scanned for children, an explicit
  list of paths, or both?
- **Output medium:** CLI report, a written file (e.g. a portfolio `OVERVIEW.md`), a
  small local web/TUI dashboard, or several?
- **Cadence:** on-demand command, scheduled (cron-like), or a filesystem watch?
- **"Stalled" definition:** after how long with no activity is a project flagged
  stalled? (Suggest a default, e.g. 14 days, and make it configurable.)
- **Language/stack:** if Python, you can use the `KeelRepo` API directly; if not,
  you'll read files / the JSON command. Which is preferred?
- **History depth:** does the per-project log keep full phase-transition history, or
  just the current snapshot plus a short recent trail?
```
