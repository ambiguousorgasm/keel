# AGENTS — Operational Contract

> Canonical agent instructions for this repository. Tool-specific bridge files
> (`CLAUDE.md`, `GEMINI.md`, etc.) should be one line pointing here. Keep this
> file under ~150 lines so every session can hold it in active context.

## 1. Read order (every task, every time)

`AGENTS.md` → `PRINCIPLES.md` → `STATUS.md` → relevant module card → relevant
`COMPONENTS.md` section → relevant `DECISIONS.md` entries → current task packet
(`brief.md` + `context.md`) → then source & tests.

## 2. Source-of-truth hierarchy

- **PRINCIPLES overrides CORE.** A CORE statement that violates a principle is a
  defect.
- **CORE overrides all other satellites** in a contradiction.
- **DECISIONS** records accepted interpretations and changes; every entry cites
  the principles it was checked against.
- **STATUS** is implementation truth, not design truth.
- **CHANGELOG** is historical, never normative.
- A mismatch between code/tests and CORE is a **defect to investigate**, not a
  new fact.
- A principle is amended only via a `principle-amendment` task packet — never
  inside an ordinary decision.

## 3. Hard rules

- Never begin implementation without a task packet (`tasks/active/<ID>/`).
- Do not make broad refactors while completing a bounded task.
- Do not change files outside the task's `scope_allowlist` in `acceptance.yml`.
- Run `just check` (or `just verify-task <ID>`) before writing the handoff.
- Update `handoff.md`, `STATUS.md`, and `CHANGELOG.md` only after implementation
  AND verification are complete.
- Append every meaningful step to `evidence/trace.jsonl` (role, model, action,
  command, result). When running a skill/slash-command, include the
  `prompt_version` field so we can later attribute outcomes to specific prompt
  revisions.

## 4. Commands

- Check everything: `just check` (format, lint, type, unit, scenario)
- Verify a task:    `just verify-task <ID>`
- Build a task's context.md: `just build-context <ID>`
- Create a new task packet:  `just new-task <slug>`

## 5. Role tiers (when running multi-agent)

- **Planner / mapper** (read-only): cheap/fast model.
- **Builder:** frontier coding model, one isolated worktree per task.
- **Test adversary:** cheap/fast model — adversarial breadth matters more than
  depth.
- **Reviewer:** frontier model from a **different family** than the builder.
  Reviews raw diff + evidence — NOT the builder's explanation. Also checks
  PRINCIPLES compliance and that any DECISIONS entry cites the right `P-n`.

## 6. For agents that don't auto-load project guidance

First line of the task prompt must be:

> "Read `AGENTS.md` and the task `context.md` before doing anything else."
