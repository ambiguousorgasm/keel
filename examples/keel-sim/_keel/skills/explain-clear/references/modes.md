# explain-clear — Modes Reference

Worked shapes for each mode. These show the *form* a good answer takes and how
the implied dials play out. They are illustrative, not scripts — adapt to the
actual question and project. The two rules always hold: don't restart from
beginner basics, and find the missing link rather than paraphrasing.

---

## `why does this exist?` (deep, conceptual; tradeoffs + failure-modes)

The highest-value mode. The user is looking at something that looks unnecessary
and wants to know what would go wrong without it.

> **Q:** `/explain-clear why does this exist?` — the event queue between the API
> and the agent.
>
> **The problem it solves:** A web request should return in milliseconds, but
> running the agent can take seconds. If the API called the agent directly, the
> user's request would block the whole time, and a slow agent would pile up
> open connections until the server fell over.
>
> **The failure mode it prevents:** synchronous coupling — one slow downstream
> component (the agent) dragging down an unrelated upstream one (request
> latency, connection limits).
>
> **Alternatives & tradeoffs:** You could call directly and accept the latency
> (simpler, fine at low volume, fails under load). You could use a thread pool
> (no broker to run, but you lose durability — a crash drops in-flight work).
> The queue costs you a moving part and "eventual" instead of "immediate," and
> buys you durability + backpressure + independent scaling.
>
> **Without it:** every traffic spike becomes a latency spike; an agent crash
> loses the work mid-flight; you can't scale agents separately from the API.

---

## `trace the flow` (deep, concrete; data-flow + state-changes)

Walk the path in order, like a story.

> **Q:** `/explain-clear trace the flow` — what happens when a job is submitted?
>
> 1. **Entry:** `POST /jobs` hits `api/jobs.py:create`.
> 2. **Inputs:** JSON payload → validated against `JobSchema` (rejects with 422
>    on bad shape).
> 3. **Transform:** a `Job` row is written to SQLite with `status=queued`.
> 4. **State change:** the job id is pushed onto the `jobs` queue.
> 5. **External call:** the API returns `202 Accepted` + the job id immediately —
>    it does NOT wait for the work.
> 6. **Later:** a worker pops the id, sets `status=running`, runs the agent,
>    writes the result, sets `status=done`.
> 7. **Error path:** if the agent raises, the worker sets `status=failed` with
>    the error, and (if retries remain) re-queues with a backoff.

---

## `map the components` (moderate, balanced; files/modules + dependencies)

> **Q:** `/explain-clear concrete: map the components in campaign ingestion.`
>
> - **`ingest/reader.py`** — reads raw campaign files. Owns parsing; knows
>   nothing about storage.
> - **`ingest/normalize.py`** — turns raw rows into the canonical schema. Pure;
>   no I/O.
> - **`ingest/writer.py`** — persists normalized rows. Owns the DB connection.
> - **Boundary:** reader → normalize → writer is one-way; normalize never
>   touches the DB, writer never parses.
> - **Data passed:** `RawRow` → `CanonRow` → (side effect: DB write).
> - **Extension points:** add a source format by adding a reader; add a
>   destination by adding a writer. The normalize step stays untouched.

---

## `translate this code` (concrete, code-adjacent; optional line-by-line)

> **Q:** `/explain-clear translate this code` — the retry wrapper.
>
> **What it does, in sections:** (1) it tries the call; (2) on failure it waits a
> growing delay; (3) it gives up after N attempts and re-raises.
>
> **Why the order matters:** the delay happens *between* attempts, not before the
> first — so the happy path pays no penalty.
>
> **State:** `attempt` counts up; `delay` doubles each loop (exponential backoff).
>
> **Assumptions:** the wrapped call is idempotent — safe to run more than once.
> If it isn't, retrying could double-apply an effect. **Hazard flagged.**
>
> **Pseudocode:**
> ```
> attempt = 0
> loop:
>   try: return call()
>   except: 
>     attempt += 1
>     if attempt >= max: raise
>     wait(delay); delay *= 2
> ```

---

## `debug the mental model` (deep, balanced; misconceptions)

Not code debugging — surfacing the wrong assumption.

> **Q:** `/explain-clear debug the mental model` — I expected the cache to update
> when I changed the source row, but it didn't.
>
> **What you're probably assuming:** that the cache holds a *live reference* to
> the row, so changing the row changes the cache.
>
> **The correct model:** the cache holds a *copy* taken at read time. The source
> and the cached value are independent after that moment.
>
> **Why the wrong model is tempting:** in plenty of languages an object you pass
> around *is* a shared reference — so "I changed it, why didn't it update?" is a
> reasonable instinct. Caches deliberately break that link for speed.
>
> **Counterexample:** read X (cache stores 5) → set source X=9 → read X again →
> you still get 5 until the cache entry expires or is invalidated.
>
> **Rule of thumb:** a cache is a photo, not a window. To see the change, you
> have to take a new photo (invalidate/refresh).

---

## `compare options` (balanced; tradeoffs; project-specific recommendation)

> **Q:** `/explain-clear compare options` — SQLite vs Postgres for this.
>
> **Shared purpose:** durable relational storage with SQL.
> **Main difference:** SQLite is an in-process file; Postgres is a separate
> server with concurrency, network access, and richer types.
> **When each wins:** SQLite for single-writer, local, zero-ops (your case
> today). Postgres once you have concurrent writers, multiple app instances, or
> need network access.
> **Cost of choosing wrong:** start on Postgres you didn't need → ops overhead
> for nothing. Start on SQLite and outgrow it → a migration under load.
> **For this project:** you have one writer and value zero-ops — **SQLite now**,
> and since you're already behind a small data layer, the swap later is cheap if
> you ever need it.

---

## Notes on the dials in practice

- **Layered pacing (the default)** means: short answer first, then expansion. The
  user stops reading when satisfied. Don't bury the short answer below setup.
- **`light` expansion** is a real setting — honor it. "Clarify just the confusing
  clause" should produce two sentences, not a deep-dive.
- **`first-principles` abstraction** strips to the underlying problem: not "this
  uses a queue" but "slow work shouldn't block fast confirmation, so the system
  splits them." Reach for it when the user says the mechanism makes no sense.
- **`keep it concise after`** — give the depth once, then stop. Don't convert a
  single deep answer into an ongoing tutorial.
