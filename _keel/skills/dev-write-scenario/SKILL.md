---
name: "Dev: Write Scenario Test"
id: dev-write-scenario
description: >
  Convert a KEEL invariant (INV-n) or failure mode (FM-n) into an executable scenario test. Use whenever an invariant or failure mode still has an xfail stub instead of a real test.
version: 1.0
keywords: [keel, workflow, builtin]
---

# /dev-write-scenario

**Role:** test author. Convert an invariant or failure mode into an executable
scenario test.

**prompt_version:** 1.0

**Usage:** `/dev-write-scenario <INV-n or FM-n>`

---

You are writing the scenario test for `$ARGUMENTS`. KEEL's scenario tests are
the executable form of the architecture's invariants — what keeps the system
honest when nothing else is watching.

## Read

1. `AGENTS.md`
2. `_keel/spec_model.yml` — find the invariant/failure-mode by id
3. `CORE.md` — section relevant to the invariant
4. The matching module card under `docs/module-cards/`
5. The existing stub at `tests/scenarios/test_$ARGUMENTS.py` (if any)
6. `docs/test-scenarios/$ARGUMENTS-*.md` (the prose spec)

## Write the test

Replace the xfail stub with a real test. Requirements:

- The test must FAIL on a system that violates the invariant.
- The test must PASS on a system that upholds it.
- Use a stable fixture (deterministic, seedable).
- Name the test function `test_$ARGUMENTS_*` so `pytest -k $ARGUMENTS`
  selects it.
- For failure modes, the test should reproduce the failure mode and verify the
  system handles it correctly.

## Hard constraints

- **Do not** weaken the invariant to make it testable. If you cannot test
  it as stated, surface that as a clarifying question — the invariant may
  itself need amending via the DECISIONS process.
- **Do not** modify the production code in this skill. If the test reveals a
  bug, surface it as a follow-up task for the builder.

## Trace

```json
{"role": "test_author", "action": "scenario_written", "id": "$ARGUMENTS", "prompt_version": "dev-write-scenario@1.0"}
```
