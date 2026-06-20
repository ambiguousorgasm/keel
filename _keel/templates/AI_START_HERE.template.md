<!--
  KEEL fills the {{...}} placeholders during bootstrap (Step 4). Everything below
  the "How you connect" line is static and never needs regenerating.
-->
# AI: Start Here

You are working inside a **KEEL** repository — a repo-native development operating
system. This file is your single orientation point. Read it first, then follow
the pointers. The goal is that you never have to reconstruct how this project
works by reading around: the repo tells you.

## This project (generated)

- **Name:** {{PROJECT_NAME}}
- **Task prefix:** {{PROJECT_PREFIX}}  (task IDs look like `{{PROJECT_PREFIX}}-001-slug`)
- **Purpose:** {{PURPOSE}}
- **Current phase:** see `STATUS.md`
- **Subsystems:** {{SUBSYSTEM_LIST}}

## The one rule that matters most

The **repository is the source of truth**, not you. You are a stateless
specialist. You never "continue building the project" — you take a bounded task
packet, work inside its scope, prove it with the gate, and hand off. All durable
truth lives in files, in this order of authority:

`PRINCIPLES.md` → `CORE.md` → `DECISIONS.md` / `COMPONENTS.md` → `STATUS.md` → `CHANGELOG.md`

A change that violates `PRINCIPLES.md` is a defect, not a new fact.

---

## How you connect (static)

Pick the interface that matches how you're running. All three drive the **same**
underlying engine; none is a shortcut around the gates.

### If you have MCP tools

This repo ships an MCP server. If your client is connected to it, you already
have `keel_*` tools. Call **`keel_project_info`** first to orient, then
**`keel_skills_index`** to see available skills. Full tool catalog and wiring:
`_keel/scripts/keel/MCP.md`. If you're *not* connected yet, that file shows how.

### If you have a shell

The `keel` command is your interface (after `pip install -e _keel`, or via
`python _keel/scripts/agent/<cmd>.py` with no install). Start with:

```bash
keel info          # what this project is, phase, tasks, skills, health
keel doctor        # verify your environment is wired correctly
keel --help        # the full command surface
```

### If you can run Python

```python
from keel import KeelRepo
repo = KeelRepo.discover()
repo.skills_index()          # survey skills cheaply
repo.list_tasks("active")    # what's in flight
```

API reference: `_keel/scripts/keel/README.md`.

---

## Your workflow (static)

Every nontrivial change is a **task packet**. The lifecycle, and the skill that
drives each step:

1. **Plan** — `dev-plan-task` (read-only; produces `plan.md`).
2. **Build context** — `dev-build-context` (deterministic `context.md`).
3. **Implement** — `dev-implement-task` (one isolated worktree, in scope).
4. **Verify** — run the gate; it must pass.
5. **Review** — `dev-review-diff` (a *different* model, reads the diff not your story).
6. **Hand off** — `dev-update-handoff` (writes handoff, updates STATUS/CHANGELOG).

Survey skills with `keel skills list` / `keel_skills_index`; load one only when
relevant (progressive disclosure).

## Where to go next (static)

| You want to… | Read |
|---|---|
| Know the operating rules for task work | `AGENTS.md` |
| Understand the design truth | `CORE.md` (and `PRINCIPLES.md` above it) |
| See the bootstrap protocol | `_keel/BOOTSTRAP.md` |
| Use the Python API | `_keel/scripts/keel/README.md` |
| Connect / use MCP tools | `_keel/scripts/keel/MCP.md` |
| Author or use a skill | `_keel/skills/README.md` |

## Hard "don't"s (static)

- Don't change files outside a task's `scope_allowlist`.
- Don't weaken `acceptance.yml` or mute checks to get a green gate.
- Don't edit `PRINCIPLES.md` via an ordinary task — that needs a
  `principle-amendment` packet.
- Don't act as if you remember prior sessions. Read the repo.
