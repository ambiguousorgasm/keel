# KEEL — Project-Local Skill System (Agent Skills Bridge)

## Implementation report

This adds a project-local, agent-discoverable skill layer to KEEL. It was built
to honor the colleague brief's *intent* — Zed-native automatic skill selection
with a reliable fallback for other agents — while integrating with KEEL's
existing architecture instead of forking it. The brief's own closing instruction
("integrate cleanly rather than forcing the proposed layout where it conflicts")
governed every decision below.

The central choice: **one source of truth, two surfaces.** Skills stay canonical
in `_keel/skills/` (so they travel with the OS and update cleanly), and are
*generated* into `.agents/skills/` — the portable Agent Skills layout. We did not
build a second, independently-authored skill library, a parallel `docs/` tree, or
duplicate lifecycle skills that already exist as KEEL's `dev-*` skills.

A web check confirmed `.agents/skills/<name>/SKILL.md` is not Zed-specific: it is
the cross-tool Agent Skills open format that Zed, Claude Code, Codex, Cursor, and
Gemini all read. So this single bridge serves every agent and also closes KEEL's
previously-pending model-agnosticism gap.

---

## Files added

| Path | Role |
|---|---|
| `_keel/skills/dev-intake/SKILL.md` | Repository-orientation skill (the brief's `repository-intake`). Read-only; finds source-of-truth docs, separates designed-vs-built, reports current state and next task. The skill an agent auto-selects on cold open. |
| `_keel/skills/dev-update-docs/SKILL.md` | Documentation-drift skill (the brief's `documentation`). Brings prose in line with the code as built; refuses to smuggle design changes into docs. |
| `_keel/skills/dev-release/SKILL.md` | Release skill (the brief's `release`). **Manual-only** — exported with `disable-model-invocation: true`; gates each irreversible action behind explicit human go-ahead. |
| `/mnt/user-data/outputs/keel-skills-bridge-report.md` | This report. |

## Files modified

| Path | Change |
|---|---|
| `_keel/scripts/keel/skills.py` | Added `manual_only` + `export` frontmatter fields (validated as booleans); added `render_agent_skill`, `export_agent_skills`, `render_catalog`, `lint_skills`. |
| `_keel/scripts/keel/helpers.py` | `ProjectLayout` gained `agents_skills` (`.agents/skills/`) and `agents_catalog` (`.agents/SKILLS.md`) paths. |
| `_keel/scripts/keel/api.py` | `KeelRepo.sync_agent_skills()` and `KeelRepo.lint_skills()`. |
| `_keel/scripts/keel/main.py` | `keel skills sync` and `keel skills lint` subcommands; `keel doctor` now reports `.agents` drift (non-fatal); help text updated. |
| `_keel/scripts/keel/mcp_server.py` | `keel_skills_sync` and `keel_skills_lint` MCP tools (19 tools total, was 17). |
| `_keel/scripts/keel/scaffold.py` | `keel init` now publishes `.agents/skills/` + catalog automatically. |
| `_keel/templates/AGENTS.template.md` | New **Skills** section: select-by-task, load-on-demand, manual-only rule, "don't edit the library mid-task," `keel skills sync`/`lint`. |
| `_keel/templates/SKILL.template.md` | Documents the optional `manual_only` and `export` flags. |
| `_keel/skills/example-csv-clean/SKILL.md` | Marked `export: false` (demo stays out of project catalogs — proves the opt-out path). |
| `_keel/BOOTSTRAP.md` | Step 8 now instructs the bootstrapping agent to run `keel skills sync` + `keel skills lint`. |
| `_keel/README.md` | New "Skills & agent discovery (Zed, Claude Code, Codex, Gemini)" section. |
| `_keel/tests/test_skills.py` | +13 tests covering parsing, export/exclusion, bundled-file copy, stale-mirror safety, drift, manual-only safeguard, and the repo/catalog end-to-end. |

---

## The skill set and each skill's role

KEEL's pre-existing `dev-*` skills already cover most of the brief's proposed
taxonomy, so those were reused rather than duplicated:

| Brief's proposed skill | KEEL skill | Status |
|---|---|---|
| `repository-intake` | **`dev-intake`** | New |
| `design-to-plan` | `dev-plan-task` | Already existed — reused |
| `implementation` | `dev-implement-task` | Already existed — reused |
| `verification` | `dev-review-diff` + the `verify-task` gate | Already existed — reused |
| `documentation` | **`dev-update-docs`** | New |
| `release` | **`dev-release`** (manual-only) | New |

Supporting helpers already present: `dev-build-context`, `dev-update-handoff`,
`dev-map-module`, `dev-write-scenario`, `explain-clear`.

---

## How automatic selection works (Zed and other agents)

1. `keel init` (or `keel skills sync`) writes `.agents/skills/<id>/SKILL.md` for
   every exported skill, plus `.agents/SKILLS.md` (a human catalog).
2. Each mirror's frontmatter carries the two portable fields agents route on:
   `name` (the skill id, matching the folder per the Agent Skills convention) and
   `description` (the routing metadata — what it does AND when to use it).
3. When the repo is open in Zed, the agent sees the catalog of name+description
   for all installed skills and loads the body of the one whose description
   matches the task (progressive disclosure — it does not ingest the whole
   library). `AGENTS.md` reinforces: orient first, load only the relevant skill.

## How manual invocation works

`dev-release` sets `manual_only: true`. On export this becomes the cross-tool
`disable-model-invocation: true` flag, so an agent will **not** auto-select or run
it. A human invokes it deliberately (e.g. Zed's slash-command, or by pointing an
agent at it explicitly). The skill body itself further requires explicit,
per-action human go-ahead for anything irreversible. `keel skills lint` fails if a
manual-only skill's safeguard is ever missing from its mirror.

## How external agents use the fallback

The same `.agents/skills/` tree is read natively by Claude Code, Codex, Cursor,
and Gemini. For agents that don't auto-load it, `AGENTS.md` is the canonical,
always-on contract (with `CLAUDE.md`/`GEMINI.md` as one-line bridges pointing to
it), and the skills remain reachable three other ways that all hit the same
engine: the `keel skills` CLI, the Python API (`KeelRepo`), and the MCP server
(`keel_skills_index` → `keel_get_skill`, plus `keel_skills_sync`/`keel_skills_lint`).

## Validation tooling

`keel skills lint` (and MCP `keel_skills_lint`) checks: required frontmatter,
duplicate skill names, empty descriptions, manual-only safeguard present in the
mirror, and `.agents` mirror/catalog drift against the canonical source. It
collects all problems rather than failing on the first. `keel doctor` surfaces
drift as a non-fatal warning.

---

## Limitations & assumptions

- **The `.agents/` tree is a generated build artifact.** Each mirror carries a
  DO-NOT-EDIT banner; edits belong in `_keel/skills/`, then `keel skills sync`.
  `keel skills lint` and `keel doctor` flag drift, but nothing *enforces* re-sync
  on commit — that would be a git hook the user opts into.
- **Stale-mirror cleanup is banner-scoped.** Sync only removes mirrors it
  generated (identified by the banner); hand-authored skills a user drops into
  `.agents/skills/` are preserved and never touched.
- **Agent Skills format taken from current Zed/agentskills.io docs.** The spec
  deliberately leaves some things unspecified (collision handling, activation
  UI); verify against your installed Zed version. KEEL emits the portable subset
  (`name`, `description`, `disable-model-invocation`).
- **The frozen `examples/keel-sim/` project was not regenerated** with a fresh
  `.agents/` tree; it predates this feature and is a fixture, not a live project.
- **Bundled files are copied, not linked.** A skill with large `scripts/` or
  `references/` is duplicated into its mirror; fine at current sizes.

## Recommended next improvements (not done)

- An optional git pre-commit hook (or a `just` target) that runs `keel skills
  sync && keel skills lint`, so the mirror can't silently drift in a shared repo.
- Fold `keel skills lint` into the `just check` gate so drift fails CI like any
  other check.
- A `keel skills sync --check` mode (exit non-zero on drift, write nothing) for
  use in CI without mutating the tree.
- Carry through the two still-queued dogfood fixes that are adjacent to this work:
  BOOTSTRAP Step 9 explicitly running `keel doctor`, and the fail-closed
  `fmt`/`lint`/`types` gate recipes (so `just check` can't report green while
  stages no-op).
