# URL Shortener — PRINCIPLES

> The founding, near-immutable commitments of this project. PRINCIPLES sit above
> CORE. A CORE statement, decision, or implementation that violates a principle
> is a defect to investigate, not a new fact.
>
> Every principle below is **falsifiable**: a future change can be checked
> against it and the answer is yes/no, not a matter of taste.
>
> Amendment process: see `_keel/templates/principle-amendment-task.template.md`.

---

## P-1 — Codes are immutable once issued

Once a `(code, target_url)` pair is committed to storage, the mapping is never
mutated. New codes may be issued; existing ones may expire; none are ever
edited. Any change to an existing row's `target_url` is a defect.

_Derived from INV-1 and "no custom aliases / no editing existing links" in
spec §8._

## P-2 — Collisions are impossible, not merely unlikely

The system never relies on probabilistic uniqueness. Code allocation goes
through an atomic insert that fails on conflict; the encoder retries with a
new candidate. There is no race window in which two distinct long URLs share
a code.

_Derived from INV-2 and FM-1._

## P-3 — Expired is gone, not redirected

A request for an expired code returns 410 Gone. The expiry check is performed
inside the same transaction as the redirect lookup; there is no "lookup, then
check expiry, then redirect" sequence where state can change in between.

_Derived from INV-4 and FM-3._

## P-4 — All answers come from storage

API responses are derivable from storage state alone. No subsystem caches
counters, target URLs, or expiry times in process memory in a way that could
diverge from storage. The same storage state always produces the same response.

_Derived from INV-5 and the broader "engine over text" principle: the truth
is in storage, not in any model or service's view of it._

## P-5 — Counters never go down

Click counts are monotonically non-decreasing. There is no operation in the
system — administrative, recovery, or otherwise — that decrements a counter.
Resetting a counter is achieved by deleting the row (a different operation
with different consequences); it is never silently zeroed.

_Derived from INV-3. This is foundational because once counters can be
silently rewritten, analytics becomes structurally untrustworthy._

---

## Superseded

_(empty at bootstrap)_
