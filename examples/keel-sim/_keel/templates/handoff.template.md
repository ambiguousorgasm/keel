# Handoff — <ID>

> Written by the builder after all `acceptance.yml` checks pass AND the reviewer
> has signed off in `review.md`. This is the canonical record of what changed
> and why.

## What was done

<2–5 sentences. The user-visible or system-visible change, not a code summary.>

## Files changed

| File | Why |
|---|---|
| `path/to/file` | <one line> |

## How it was verified

```bash
just check         # → all green
just verify-task <ID>  # → all checks passed
```

Scenario evidence: `evidence/`

## Decisions made

> Any decisions made during the work. Each must already be appended to
> `DECISIONS.md` with its principles cited.

- D-<NNN>: <one line>

## Principles compliance

- Checked against: P-n, P-m
- Reviewer confirmed no PRINCIPLES violation in `review.md`.

## Follow-ups discovered

> Things that came up but were out-of-scope for this task. Each becomes a new
> task packet.

- <follow-up> → <new task ID>

## State updated

- `STATUS.md` ✅
- `CHANGELOG.md` ✅
- `evidence/trace.jsonl` ✅
