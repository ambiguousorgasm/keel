# Module Card — storage

> The detail view for a subsystem listed in `COMPONENTS.md`. Read this before
> editing any file under this module's paths.

## Purpose

`storage` is the only subsystem that mutates persistent state. Everything above
it must go through its documented interfaces. The contract is narrow on purpose:
three operations, all atomic, no leakage of SQL or transaction details.

## Authority

- Decides the row-level schema of `links` and `clicks`.
- Decides what "atomic" means in this codebase: every public method either
  succeeds completely or fails with a typed result; partial state changes are
  defects.
- Does NOT decide: code length (encoder), TTL semantics beyond storing
  `expires_at` (CORE), HTTP status mapping (api).

## Inputs

- `(code, target_url, expires_at)` for `insert_link`
- `code` for `get_link` and `increment_click`

## Outputs

- `InsertResult = OK | CONFLICT` from `insert_link` — never raises on
  collision; returns a typed result so encoder's retry loop can reason about it.
- `LinkOrExpired | None` from `get_link` — distinguishes "no such code,"
  "code exists but expired" (returns sentinel + the link), and "active code."
- `int` (new counter value) from `increment_click`.

## State it MAY mutate

- `links` (insert only; no update of `target_url` per P-1)
- `clicks.count` (increment only; never decrement per P-5)

## State it may NOT mutate

- None within the system — but TBD: any future cache layer must NOT be writable
  from above `storage`.

## Allowed dependencies

- PostgreSQL driver (`psycopg`)

## Forbidden dependencies

- `api`, `encoder`, `analytics` — `storage` is the bottom of the dependency
  graph. Any inbound import from above is a layer violation.

## Public interfaces

- `insert_link(code: str, target_url: str, expires_at: datetime) -> InsertResult`
- `get_link(code: str) -> LinkOrExpired | None`
- `increment_click(code: str) -> int`

## Invariants upheld

- **INV-1:** No public method updates `target_url`. Enforced by the absence of
  an `update_link` operation; database role lacks UPDATE on `target_url`.
- **INV-2:** `insert_link` uses `INSERT ... ON CONFLICT (code) DO NOTHING`
  and returns CONFLICT if zero rows were inserted.
- **INV-3:** `increment_click` uses `UPDATE clicks SET count = count + 1`;
  no other UPDATE exists.
- **INV-5:** Each public method is a single round-trip; no in-process cache.

## Relevant tests

- `tests/unit/test_storage_schema.py`
- `tests/scenarios/test_INV-1_immutability.py`
- `tests/scenarios/test_INV-2_no_collision.py`
- `tests/scenarios/test_INV-3_monotonic_counters.py`
- `tests/scenarios/test_FM-1_concurrent_creation.py`

## Known gaps

- TBD — needs design: the read-replica strategy for FM-4. Currently `get_link`
  always reads from primary; this is correct for INV-5 but limits throughput.
  Any future read-replica routing must preserve INV-5 (no stale-read window
  visible to the API).
