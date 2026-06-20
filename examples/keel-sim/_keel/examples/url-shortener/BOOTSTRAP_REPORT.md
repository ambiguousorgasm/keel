# BOOTSTRAP_REPORT — URL Shortener

> Generated at the close of Step 9. The human reviews this before any
> implementation work begins.

## 1. Files created

```
PRINCIPLES.md
CORE.md
COMPONENTS.md
DECISIONS.md (seeded D-001, D-002)
STATUS.md
CHANGELOG.md
AGENTS.md
CLAUDE.md       (one-liner pointing at AGENTS.md)
GEMINI.md       (one-liner pointing at AGENTS.md)
justfile
Makefile
docs/module-cards/storage.md
docs/module-cards/encoder.md
docs/module-cards/api.md
docs/module-cards/analytics.md
docs/test-scenarios/INV-1-immutability.md
docs/test-scenarios/INV-2-no-collision.md
docs/test-scenarios/INV-3-monotonic-counters.md
docs/test-scenarios/INV-4-expired-is-410.md
docs/test-scenarios/INV-5-storage-derivable.md
docs/test-scenarios/FM-1-concurrent-creation.md
docs/test-scenarios/FM-2-counter-desync.md
docs/test-scenarios/FM-3-expiry-race.md
docs/test-scenarios/FM-4-stale-replica.md
tests/scenarios/test_INV-1_immutability.py   (xfail stub)
tests/scenarios/test_INV-2_no_collision.py   (xfail stub)
tests/scenarios/test_INV-3_monotonic_counters.py (xfail stub)
tests/scenarios/test_INV-4_expired_is_410.py (xfail stub)
tests/scenarios/test_INV-5_storage_derivable.py (xfail stub)
tests/scenarios/test_FM-1_concurrent_creation.py (xfail stub)
tests/scenarios/test_FM-2_counter_desync.py  (xfail stub)
tests/scenarios/test_FM-3_expiry_race.py     (xfail stub)
tests/scenarios/test_FM-4_stale_replica.py   (xfail stub)
tasks/active/URLS-001-storage-bootstrap/{brief.md, acceptance.yml, evidence/}
tasks/active/URLS-002-encoder-collision-retry/{brief.md, acceptance.yml, evidence/}
tasks/active/URLS-003-api-shorten-and-redirect/{brief.md, acceptance.yml, evidence/}
tasks/active/URLS-004-api-expiry-410/{brief.md, acceptance.yml, evidence/}
tasks/active/URLS-005-analytics-increment/{brief.md, acceptance.yml, evidence/}
_keel/spec_model.yml
```

## 2. Extracted structured model

See `_keel/spec_model.yml` for the full validated extraction (passes
`spec_model.schema.json`). Summary:

- **Project:** URL Shortener (`URLS`)
- **Subsystems (4):** storage, encoder, api, analytics
- **Invariants (5):** INV-1 through INV-5
- **Failure modes (4):** FM-1 through FM-4
- **Phases (4):** P0 storage → P1 encoder → P2 api → P3 analytics
- **Foundational decisions:** 7-char base62 codes, 90-day default TTL

## 3. Verification (CoVe pass)

| Question | Result |
|---|---|
| Does every subsystem's `must_not_mutate` exclude state another subsystem owns? | ✅ — encoder, api, analytics all forbid mutation of `links`; only storage owns it. |
| Does each invariant have at least one scenario stub? | ✅ — all 5 stubs present, all xfail. |
| Does each failure mode have a scenario stub? | ✅ — all 4 stubs present. |
| Is any phase ordered before a phase it depends on? | ✅ — P0 first; api depends on P0+P1; analytics depends on P0+P2. |
| Did I introduce any domain fact not present in `PROJECT_SPEC.md`? | ✅ — checked. The phrase "INSERT ... ON CONFLICT DO NOTHING" is implementation detail derived from INV-2 + the PostgreSQL choice in tech_stack, but is not a new domain fact. |
| Is each principle in `PRINCIPLES.md` falsifiable? | ✅ — each can be tested against a future change. P-5 ("counters never go down") is especially tight; a single `UPDATE clicks SET count = count - 1` anywhere violates it. |
| Does `CORE.md` visibly comply with all principles? | ✅ — storage's lack of `update_link` enforces P-1; `INSERT ... ON CONFLICT` enforces P-2; the joined expiry check enforces P-3; the no-cache rule enforces P-4; absence of decrement enforces P-5. |
| Does each seeded DECISIONS entry cite the principles it was checked against? | ✅ — D-001 (code length) cites "none directly applicable"; D-002 (TTL default) cites P-3. |

## 4. Assumptions

| Assumption | Where it lives | Rationale |
|---|---|---|
| Single-region deployment is acceptable. | CORE §1 (out-of-scope) | Spec §8 listed multi-region as out-of-scope. |
| PostgreSQL is the datastore; no abstraction for swapping to a different DB. | `storage` module card | Spec §3 explicitly chose PostgreSQL. |
| Counter increments are PostgreSQL UPDATEs, not Redis or a separate counter service. | CORE §3 storage; D-001 | Direct read of spec; no separate counter service mentioned. |
| Codes are `[0-9a-zA-Z]` with no excluded ambiguous characters (e.g., `0`/`O`, `1`/`l`). | Not yet recorded | Spec §10 said base62 unconditionally. This MAY warrant a follow-up decision if UX matters. |

## 5. Questions still open

1. Should there be an admin endpoint to expire a code early? Spec §8 says
   "no editing or deleting" but doesn't address early expiry. Flagging for
   human input before implementing api in P2.
2. The collision-retry budget (5 attempts → 503) is explicitly NOT
   foundational. Should it be configurable per environment? Probably yes,
   but not a foundation question. Defer to encoder task.

## 6. Recommended first task

**`URLS-001-storage-bootstrap`** — see
`tasks/active/URLS-001-storage-bootstrap/brief.md`.

Reasoning: every other subsystem depends on storage. The atomic-insert
behavior is the load-bearing piece — it's what gives P-2 ("collisions are
impossible") its teeth, and FM-1 is the headline failure mode for this task.

The four follow-on tasks are seeded in `tasks/active/` in the order
P0 → P1 → P2 → P3.
