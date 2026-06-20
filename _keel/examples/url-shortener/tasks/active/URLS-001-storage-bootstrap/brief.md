# URLS-001 — Storage schema and atomic insert

> **Complexity hint:** `moderate`
> (Optional metadata. Used by orchestrators to route to an appropriately-sized
> model. KEEL does not enforce a model choice — this is a signal, not a command.)

## Objective

Stand up the `storage` subsystem with the `links` table, the `clicks` table,
and the three public methods documented in the module card:
`insert_link`, `get_link`, `increment_click`. The atomic-insert behavior is
the load-bearing piece — it's what gives P-2 ("collisions are impossible") its
teeth.

This is the first task because P0 of the roadmap requires storage before
anything else can be built on top.

## Allowed scope

- `backend/storage/**`
- `tests/unit/test_storage_*.py`
- `tests/scenarios/test_INV-1_immutability.py`
- `tests/scenarios/test_INV-2_no_collision.py`
- `tests/scenarios/test_INV-3_monotonic_counters.py`
- `tests/scenarios/test_FM-1_concurrent_creation.py`
- `migrations/**`

## Non-goals

- Do not implement the encoder. Stub a fake code in tests; don't generate one.
- Do not add the HTTP API.
- Do not add caching, read-replica routing, or any "performance" optimization.
- Do not add a `delete_link` or `update_link` operation. Per P-1, codes are
  immutable; the absence of these operations is itself the enforcement.

## Relevant sources

- `PRINCIPLES.md`: P-1, P-2, P-3, P-5
- `CORE.md`: Per-subsystem normative rules
- `COMPONENTS.md`: storage
- `docs/module-cards/storage.md`
- `STATUS.md`: P0

## Acceptance criteria

- `links` and `clicks` tables exist with the schema documented in the module
  card, with appropriate primary keys and the `clicks.count` default of 0.
- `insert_link` uses `INSERT ... ON CONFLICT (code) DO NOTHING` and returns a
  typed `InsertResult` indicating OK or CONFLICT.
- `get_link` returns a result that distinguishes (no such code) /
  (code exists but expired) / (active code) in a single round-trip — the
  expiry check is in the SQL, not the Python.
- `increment_click` is implemented as an atomic `UPDATE` and returns the new
  count.
- No `update_link` or `delete_link` operation exists. (The absence is itself
  the enforcement of P-1.)
- Scenario tests for INV-1, INV-2, INV-3, and FM-1 all pass against the
  implementation.
- No unrelated behavior changes (lint + scope check passes).

## Risk notes

- FM-1 is the headline failure mode for this task. The scenario test should
  spawn N concurrent inserts of distinct URLs all targeting the same candidate
  code, and assert exactly one wins and the others receive CONFLICT — not "in
  most runs" but "every run, on a seeded fixture."
- Postgres-level enforcement of P-5 (no UPDATE that lowers count) is worth
  considering at the database role / GRANT level, not just in application
  code. Surface in handoff if you have an opinion.
