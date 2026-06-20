# COMPONENTS

> One entry per subsystem. The registry of what exists and where its edges are.
> Each entry points to a detailed module card under `docs/module-cards/`.

---

## storage

- **Path(s):** `backend/storage/**`
- **Responsibility:** persist link rows and click counters; sole mutator of persistent state.
- **Owns state:**
  - `links(code, target_url, created_at, expires_at)`
  - `clicks(code, count)`
- **May mutate:**
  - both tables above, via documented interfaces only
- **May NOT mutate:**
  - N/A (bottom layer)
- **Allowed dependencies:** PostgreSQL driver
- **Forbidden dependencies:** `api`, `encoder`, `analytics`
- **Module card:** `docs/module-cards/storage.md`
- **Upholds invariants:** INV-1, INV-2, INV-3, INV-5

---

## encoder

- **Path(s):** `backend/encoder/**`
- **Responsibility:** generate short codes; collision-retry against storage.
- **Owns state:** none persistent
- **May mutate:** nothing directly
- **May NOT mutate:** `links` (direct), `clicks` (ever)
- **Allowed dependencies:** `storage`
- **Forbidden dependencies:** `api`, `analytics`
- **Module card:** `docs/module-cards/encoder.md`
- **Upholds invariants:** INV-2

---

## api

- **Path(s):** `backend/api/**`
- **Responsibility:** HTTP surface; orchestrates encoder + storage + analytics.
- **Owns state:** none
- **May mutate:** nothing directly
- **May NOT mutate:** all persistent state (use the storage interface)
- **Allowed dependencies:** `encoder`, `storage`, `analytics`, FastAPI
- **Forbidden dependencies:** none
- **Module card:** `docs/module-cards/api.md`
- **Upholds invariants:** INV-4, INV-5

---

## analytics

- **Path(s):** `backend/analytics/**`
- **Responsibility:** increment click counters; expose stats.
- **Owns state:** the *event* of incrementing
- **May mutate:** `clicks.count` via `storage.increment_click` only
- **May NOT mutate:** `links` table
- **Allowed dependencies:** `storage`
- **Forbidden dependencies:** `api`, `encoder`
- **Module card:** `docs/module-cards/analytics.md`
- **Upholds invariants:** INV-3
