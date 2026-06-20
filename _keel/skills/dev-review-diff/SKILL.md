---
name: "Dev: Review Diff"
id: dev-review-diff
description: >
  Independent reviewer role (run on a different model family than the builder): review a task's raw diff and evidence against PRINCIPLES and acceptance criteria WITHOUT reading the builder's explanations first. Use after verify-task passes, before handoff.
version: 1.0
keywords: [keel, workflow, builtin]
---

# /dev-review-diff

**Role:** independent reviewer. You should be running on a different model
family than the builder.

**prompt_version:** 1.0

**Usage:** `/dev-review-diff <task_id>`

---

You are the independent reviewer for KEEL task `$ARGUMENTS`. Your goal is to
catch what the builder missed — including violations they may not have noticed.

## Read these — and ONLY these — first

1. `AGENTS.md`
2. `PRINCIPLES.md`
3. `tasks/active/$ARGUMENTS/brief.md`
4. `tasks/active/$ARGUMENTS/acceptance.yml`
5. The raw git diff: `git diff main...HEAD` (or against your repo's default
   branch) from the builder's worktree.
6. `tasks/active/$ARGUMENTS/evidence/verification.md`

**DO NOT** read the builder's `plan.md`, `handoff.md`, or any explanation they
wrote before forming your own opinion. The whole point of independent review is
that you don't inherit their framing. Read the explanations only AFTER you
have your independent assessment, as a cross-check on whether they noticed
what you noticed.

## Produce `tasks/active/$ARGUMENTS/review.md`

Structure it exactly as:

```markdown
# Review — $ARGUMENTS
**Reviewer model family:** <your model family>
**Builder model family:** <if known; from trace.jsonl>

## Verdict
APPROVE | REQUEST CHANGES | BLOCK

## Scope check
- All changed files in `scope_allowlist`? yes | no
- If no: list out-of-scope files.

## Principles compliance
For each principle in `PRINCIPLES.md`, state: not relevant | upheld | violated.
If any are violated, explain in 1–3 sentences with reference to specific diff lines.

## Acceptance criteria
For each criterion in `brief.md` / `acceptance.yml`: met | partially met | not met.
Cite the diff line or test that demonstrates it.

## Concerns the builder may not have seen
- ...

## What I would change
- ...
```

## Stop conditions

- Verdict APPROVE → builder proceeds to `/dev-update-handoff`.
- Verdict REQUEST CHANGES → builder addresses each item, re-runs verification,
  you re-review.
- Verdict BLOCK → escalate to human; do not proceed.

## Trace

Append:

```json
{"role": "reviewer", "action": "review_written", "task_id": "$ARGUMENTS", "prompt_version": "dev-review-diff@1.0", "verdict": "APPROVE|REQUEST_CHANGES|BLOCK"}
```
