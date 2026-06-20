---
name: "Dev: Update Handoff"
id: dev-update-handoff
description: >
  Closer role: write handoff.md, append any DECISIONS entry with principles cited, update STATUS and CHANGELOG, and move the task to completed. Use after the reviewer approves and all checks pass.
version: 1.0
keywords: [keel, workflow, builtin]
---

# /dev-update-handoff

**Role:** packet closer. Write the handoff and update project state.

**prompt_version:** 1.0

**Usage:** `/dev-update-handoff <task_id>`

---

You are closing the packet for task `$ARGUMENTS`. Reviewer has APPROVED. All
checks are green. Now: produce the durable record.

## Preconditions (verify before doing anything)

- `tasks/active/$ARGUMENTS/review.md` exists and ends in `Verdict: APPROVE`.
- `just verify-task $ARGUMENTS` exits 0 (re-run it; do not trust prior runs).
- `tasks/active/$ARGUMENTS/evidence/verification.md` shows all checks pass.

If any precondition fails, STOP and surface to the human.

## Write `tasks/active/$ARGUMENTS/handoff.md`

Use `_keel/templates/handoff.template.md`. Fill every section. Cite specific
files and tests, not vague summaries.

## Append a `DECISIONS.md` entry IF the task made a non-trivial design choice

If during implementation a real choice was made — not just naming or
formatting — append to `DECISIONS.md`:

- The next available `D-NNN` id
- The decision with one-sentence context
- **`Principles checked:` must cite specific `P-n` ids** (or
  `none directly applicable`, never blank)
- Consequences

If no design choice was made, write `(no DECISIONS entry — implementation
followed CORE without ambiguity)` in handoff.md instead.

## Update `STATUS.md`

- Move this task from **In progress** to **Built & verified**.
- If the task closes a known gap, remove it from **Known gaps**.
- If the task advanced the phase, update **Current phase**.

## Update `CHANGELOG.md`

Append a new entry at the top:

```markdown
## <YYYY-MM-DD> — $ARGUMENTS: <one-line title>
- <user-visible or system-visible change>
- Files touched: see handoff.md
```

## Move the task folder

```bash
git mv tasks/active/$ARGUMENTS tasks/completed/$ARGUMENTS
```

## Trace

```json
{"role": "closer", "action": "handoff_written", "task_id": "$ARGUMENTS", "prompt_version": "dev-update-handoff@1.0", "decisions_added": ["D-NNN"]}
```

Then commit. Then merge from the worktree to main (or open a PR, depending on
the project's git policy). Then stop.
