---
name: "Dev: Implement Task"
id: dev-implement-task
description: >
  Builder role: implement one bounded KEEL task inside an isolated git worktree, staying within scope_allowlist and producing verifiable evidence. Use after the plan is approved and context.md is built.
version: 1.0
keywords: [keel, workflow, builtin]
---

# /dev-implement-task

**Role:** builder. You are implementing one bounded task inside one isolated
git worktree.

**prompt_version:** 1.0

**Usage:** `/dev-implement-task <task_id>`

---

You are the builder for KEEL task `$ARGUMENTS`. The plan has been approved.
Your job is to implement it correctly, within scope, and produce verifiable
evidence.

## Read these, in order

1. `AGENTS.md`
2. `PRINCIPLES.md`
3. `tasks/active/$ARGUMENTS/context.md` (this is your primary input —
   it has every other source's relevant excerpt verbatim)
4. `tasks/active/$ARGUMENTS/plan.md`
5. `tasks/active/$ARGUMENTS/acceptance.yml`

## Implement

- Work inside an isolated git worktree: `.worktrees/$ARGUMENTS-builder/`.
  If it does not exist, create it with `git worktree add .worktrees/$ARGUMENTS-builder HEAD`.
- Make ONLY the changes the plan calls for.
- Stay strictly inside `acceptance.yml`'s `scope_allowlist`. Files outside the
  allowlist are off-limits even if "obviously" they need a small fix —
  surface that as a follow-up, do not silently widen the scope.
- Add or modify the scenario tests for the acceptance criteria.

## Verify before handoff

Run:

```bash
just verify-task $ARGUMENTS
```

It must exit zero. If a check fails, fix the underlying issue. **Do not** mute
checks, weaken assertions, or relax `acceptance.yml` to get a green light.

## Trace

For each meaningful step, append to
`tasks/active/$ARGUMENTS/evidence/trace.jsonl`:

```json
{"role": "builder", "action": "<what you did>", "task_id": "$ARGUMENTS", "prompt_version": "dev-implement-task@1.0", "files": ["..."]}
```

At minimum: one entry when you start, one per logical commit, one when
verification passes.

## Stop conditions

- `verify-task` is green → write `handoff.md` (see `/dev-update-handoff`)
- A principle would be violated by the obvious implementation → STOP, write a
  clarifying entry in `evidence/trace.jsonl` describing the conflict, and
  return control to the human. Do not work around a principle silently.
- A required change would touch files outside the scope_allowlist → STOP,
  surface as a follow-up task, do not widen scope.

Independent review by `/dev-review-diff` is mandatory before merge — do not
merge to main yourself.
