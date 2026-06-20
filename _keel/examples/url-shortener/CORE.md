# URL Shortener — CORE (Normative Design Truth)

> CORE overrides all satellite documents in any contradiction. CORE is itself
> accountable to `PRINCIPLES.md` — a CORE statement that violates a principle
> is a defect, not a new fact. Changes to CORE are recorded in `DECISIONS.md`,
> and each decision entry cites which principles it was checked against.

---

## 1. System purpose & boundaries

A small HTTP service that maps long URLs to short codes and redirects them, with
TTLs and per-code click analytics. The system is deliberately small and stateful:
all truth lives in PostgreSQL; the application layers above storage are stateless
and derivable.

In scope: link creation, redirect with expiry, click counting, stats.
Out of scope: user accounts, authentication, rate limiting, custom aliases,
editing existing links, multi-region replication.

## 2. Architecture overview

Four subsystems, layered:

```
api  ───┬──> encoder ──> storage <── analytics
        └─────────────────┘
```

`storage` is the only subsystem that mutates persistent state. `encoder` is pure
plus a collision-retry loop against storage. `api` orchestrates without owning
state. `analytics` only ever increments counters; it never reads or writes link
rows.

Codes are 7-character base62 strings (see D-001). Default TTL is 90 days (D-002).

## 3. Per-subsystem normative rules

### storage

- **Authority:** the sole mutator of the `links` table and `clicks` counter rows.
- **State it owns:** `links(code, target_url, created_at, expires_at)`,
  `clicks(code, count)`.
- **State it must NOT mutate:** N/A — it is the bottom layer.
- **Invariants it upholds:** INV-1 (immutability of `target_url`), INV-2
  (atomic insert with conflict detection), INV-3 (counter monotonicity:
  no UPDATE that lowers `count`), INV-5 (deterministic reads).
- **Public interfaces:**
    - `insert_link(code, target_url, expires_at) -> InsertResult` —
      conflict-aware; returns `OK` or `CONFLICT`.
    - `get_link(code) -> LinkOrExpired | None` — atomic read that joins
      the expiry check.
    - `increment_click(code) -> int` — atomic increment; returns new value.

### encoder

- **Authority:** decides which candidate code to attempt; decides retry policy
  on conflict.
- **State it owns:** none persistent. Retry budget is configured, not stored.
- **State it must NOT mutate:** `links` directly, `clicks` ever.
- **Invariants it upholds:** INV-2 (via collision-retry against storage's
  atomic insert).
- **Public interfaces:**
    - `allocate_code(target_url, ttl) -> AllocatedCode | RetriesExhausted` —
      generates and inserts; loops on `CONFLICT` up to the budget.

### api

- **Authority:** translates HTTP requests to subsystem calls; shapes responses.
- **State it owns:** none.
- **State it must NOT mutate:** all persistent state.
- **Invariants it upholds:** INV-4 (returns 410 for expired codes — never
  inferring expiry separately from storage), INV-5 (every response derives
  from a storage call).
- **Public interfaces:** `POST /shorten`, `GET /{code}`, `GET /stats/{code}`.

### analytics

- **Authority:** issues counter increments on successful redirects.
- **State it owns:** the *event* of incrementing (the increment call itself);
  storage owns the counter row.
- **State it must NOT mutate:** `links` table.
- **Invariants it upholds:** INV-3 (only calls `increment_click`, never an
  arbitrary update).
- **Public interfaces:** internal — `record_click(code) -> None`.

## 4. System-wide invariants

- **INV-1:** A given short code always resolves to the same target URL throughout
  its lifetime — codes are immutable once issued.
- **INV-2:** No two distinct long URLs are ever assigned the same code at the
  same time.
- **INV-3:** Click counts are monotonically non-decreasing for the lifetime of
  a code.
- **INV-4:** A GET for an expired code returns HTTP 410 Gone, not 302 Found.
- **INV-5:** All API responses are derivable from storage state alone.

## 5. Out-of-scope

- User accounts, authentication, rate limiting.
- Custom code aliases.
- Editing or deleting existing short links.
- Multi-region replication.

Adding any of the above requires a `DECISIONS.md` entry that explicitly cites
the principle(s) it impacts. Several are not just feature deferrals but
*foundational scope decisions* that PRINCIPLES would block.

## 6. Glossary

- **code:** the 7-character short identifier (e.g. `aB3xK9q`).
- **target URL:** the original long URL the code redirects to.
- **TTL:** time-to-live; the code expires after this duration.
- **base62:** alphabet of `[0-9a-zA-Z]`, used for code generation.
