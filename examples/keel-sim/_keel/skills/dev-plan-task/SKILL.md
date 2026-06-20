---
name: "Dev: Plan Task"
id: dev-plan-task
description: >
  Read-only planning pass for a KEEL task: produces plan.md from the brief without writing any code. Use after a task packet is created and before implementation begins.
version: 1.0
keywords: [keel, workflow, builtin]
---

# /dev-plan-task

**Role:** read-only planner. You will NOT write code or edit project files.

**prompt_version:** 1.0

**Usage (Claude Code):** copy this file to `.claude/commands/dev-plan-task.md`
and invoke as `/dev-plan-task <task_id>`. For other agents, paste the prompt
verbatim and provide the task ID.

---

You are the planner for KEEL task `$ARGUMENTS`. Your job is to produce a
disciplined plan — not to write code.

## Read these, in order

1. `AGENTS.md` (operational contract)
2. `PRINCIPLES.md` (the founding commitments your plan must respect)
3. `tasks/active/$ARGUMENTS/brief.md`
4. Every source listed in the brief's **Relevant sources** section
5. `STATUS.md` (current phase)

## Produce `tasks/active/$ARGUMENTS/plan.md`

Structure it exactly as:

```markdown
# Plan — $ARGUMENTS

## Approach
<2–5 sentences. What changes, at what layer, in what order.>

## Files to create or modify
| Path | Action | Reason |
|---|---|---|
| ... | create | ... |

## Tests to add or modify
- `tests/scenarios/test_INV-n.py` — covers acceptance criterion 1
- ...

## Order of operations
1. ...
2. ...

## Risks and unknowns
- ...

## Questions blocking implementation
- (none) — or list specific, blocking questions
```

## Hard constraints

- **Do not write any application code.** Your output is the plan file only.
- **Do not edit files outside `tasks/active/$ARGUMENTS/`.**
- **Do not invent acceptance criteria.** They live in `brief.md` and
  `acceptance.yml`; you may only refine *how* they will be satisfied.
- **Cite every principle and decision your plan depends on.** If your plan
  could plausibly violate a principle, surface it as a question rather than
  silently designing around it.

## Trace

Before you finish, append to `tasks/active/$ARGUMENTS/evidence/trace.jsonl`:

```json
{"role": "planner", "action": "plan_written", "task_id": "$ARGUMENTS", "prompt_version": "dev-plan-task@1.0"}
```

Then stop. The human reviews `plan.md` and approves before any code is written.
