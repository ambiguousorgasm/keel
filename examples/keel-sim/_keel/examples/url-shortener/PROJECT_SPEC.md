# URL Shortener — Design Spec

## 1. Purpose (one line)

A small HTTP service that maps long URLs to short codes and redirects them, with TTLs and per-code click analytics.

**Project name:** URL Shortener
**Project prefix:** URLS

## 2. Problem & users

Users need shareable short links for long URLs and basic visibility into how often each link is clicked. Operators need confidence that codes are unique, that expired links stop working, and that the system can be reasoned about under concurrency.

## 3. Tech stack

- Language(s): Python 3.11+
- Framework(s): FastAPI
- Datastore: PostgreSQL (with optimistic locking on code allocation)
- Runtime / deploy target: containerized; single-region

## 4. Subsystems

### storage
- Responsibility: persist `(code → target_url, created_at, expires_at)` and per-code click counters.
- State it OWNS: the `links` table and the `clicks` counter rows.
- State it must NOT touch: nothing else exists yet.
- Talks to: PostgreSQL.
- Must NOT depend on: api, encoder, analytics (it is the bottom layer).

### encoder
- Responsibility: generate a short code for a given long URL, deterministically check candidates against storage for collisions, retry on conflict.
- State it OWNS: nothing persistent — pure functions plus collision-retry policy.
- State it must NOT touch: the `clicks` counter; the `links` table directly (it asks storage to insert).
- Talks to: storage (for collision check + atomic insert).
- Must NOT depend on: api, analytics.

### api
- Responsibility: HTTP surface. Two endpoints: `POST /shorten` (long URL → short code) and `GET /{code}` (redirect, or 404, or 410 if expired).
- State it OWNS: no state.
- State it must NOT touch: any storage row directly — it calls into encoder and storage.
- Talks to: encoder, storage, analytics.
- Must NOT depend on: implementation details of storage (uses the storage interface).

### analytics
- Responsibility: increment per-code click counters on successful redirects; expose `GET /stats/{code}`.
- State it OWNS: counter increments (storage owns the actual counter rows; analytics owns the *event* of incrementing).
- State it must NOT touch: the `links` table directly.
- Talks to: storage (atomic counter increment).
- Must NOT depend on: api, encoder.

## 5. Invariants

- INV-1: A given short code always resolves to the same target URL throughout its lifetime — codes are immutable once issued.
- INV-2: No two distinct long URLs are ever assigned the same code at the same time (concurrent collision is impossible, not just unlikely).
- INV-3: Click counts are monotonically non-decreasing for the lifetime of a code; a counter never goes down.
- INV-4: A `GET /{code}` for an expired code returns HTTP 410 Gone, not 302 Found.
- INV-5: All API responses are derivable from storage state alone; the same storage state always produces the same API response.

## 6. Failure modes / risks

- FM-1: Two concurrent `POST /shorten` requests for different URLs race for the same candidate code, and one silently overwrites the other.
- FM-2: A click happens, the counter increment fails partway, the redirect succeeds, and the count silently desyncs from reality.
- FM-3: A code expires between the lookup and the redirect; the redirect proceeds anyway, violating INV-4.
- FM-4: Storage returns stale data from a read replica and the API serves a code that has been deleted upstream.

## 7. Phases

- P0: storage — schema, atomic insert, atomic counter increment, basic CRUD interface.
- P1: encoder — code generation + collision-retry against storage.
- P2: api — HTTP layer wiring encoder + storage; redirect with expiry check.
- P3: analytics — click counting + stats endpoint.

## 8. Out of scope

- User accounts, authentication, rate limiting.
- Custom code aliases (codes are always generated, never chosen).
- Editing or deleting existing short links.
- Multi-region replication.

## 9. Decisions already made / assumptions

- Codes are 7 characters, base62. **Foundational.**
- Default TTL is 90 days unless specified at creation. **Foundational.**
- Collision-retry budget is 5 attempts; exhausting it returns 503. Not foundational; subject to tuning.

## 10. Glossary

- **code**: the 7-character short identifier (e.g. `aB3xK9q`).
- **target URL**: the original long URL the code redirects to.
- **TTL**: time-to-live; the code expires after this duration.
- **base62**: alphabet of `[0-9a-zA-Z]`, used for code generation.
