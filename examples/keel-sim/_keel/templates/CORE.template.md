# <Project Name> — CORE (Normative Design Truth)

> CORE overrides all satellite documents in any contradiction. CORE is itself
> accountable to `PRINCIPLES.md` — a CORE statement that violates a principle is
> a defect, not a new fact. Changes to CORE are recorded in `DECISIONS.md`, and
> each decision entry cites which principles it was checked against.

---

## 1. System purpose & boundaries

<From spec §1–2. What this is, who it's for, what it isn't.>

## 2. Architecture overview

<The subsystems and how state flows between them. Diagram-as-prose is fine; a
mermaid block is fine; what matters is that an agent can derive the boundaries
from this section without reading every module card.>

## 3. Per-subsystem normative rules

> One block per subsystem from `_keel/spec_model.yml`. The module card in
> `docs/module-cards/` is the detail view; this is the canonical summary.

### <Subsystem name>

- **Authority:** what this subsystem is allowed to decide / mutate.
- **State it owns:**
- **State it must NOT mutate:**
- **Invariants it upholds:** INV-n, INV-m
- **Public interfaces:**

(repeat per subsystem)

## 4. System-wide invariants

> From spec §5, with stable ids preserved.

- **INV-1:** <statement>
- **INV-2:** <statement>

## 5. Out-of-scope

> Carried over from spec §8. Anything here is a CORE-level non-goal, not just a
> roadmap deferral. Adding to scope requires a DECISIONS entry.

- ...

## 6. Glossary

> Shared vocabulary. Every agent reads this before touching code.

- **<term>:** <definition>
