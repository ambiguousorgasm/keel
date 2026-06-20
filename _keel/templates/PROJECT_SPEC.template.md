# <Project Name> — Design Spec

> This is the only free-form input to the bootstrap. The quality of the generated
> scaffold is bounded by the quality of this spec. Spend your effort here.
>
> Load-bearing sections: §4 Subsystems, §5 Invariants, §6 Failure modes. Get
> these right and the rest follows. Get them wrong and so will the bootstrap.

## 1. Purpose (one line)

<What this is, in a single sentence.>

**Project name:** <full name>
**Project prefix:** <2–6 caps letters used in task IDs, e.g. `ORDP` for "Order Pipeline">

## 2. Problem & users

<What problem it solves and who uses it. 2–4 sentences.>

## 3. Tech stack

- Language(s):
- Framework(s):
- Datastore:
- Runtime / deploy target:

## 4. Subsystems

> One block per major part of the system. Be concrete about ownership. The
> bootstrap will use `owns state` and `must NOT touch` to enforce module
> boundaries — write them as if you mean it.

### <Subsystem name>

- Responsibility:
- State it OWNS:
- State it must NOT touch:
- Talks to:
- Must NOT depend on:

### <Subsystem name>

- Responsibility:
- State it OWNS:
- State it must NOT touch:
- Talks to:
- Must NOT depend on:

<repeat for each subsystem>

## 5. Invariants

> Things that must ALWAYS be true. Phrase each as a falsifiable, checkable
> statement — something you could write a test for. Each becomes a scenario test.

- INV-1: ...
- INV-2: ...
- INV-3: ...

## 6. Failure modes / risks

> Known or anticipated ways this breaks. Each becomes an adversarial test. Be
> specific — "the orchestrator could send private narration to the public
> channel" is useful; "things might go wrong" is not.

- FM-1: ...
- FM-2: ...
- FM-3: ...

## 7. Phases

> Ordered. What must exist before what. The bootstrap uses these to order the
> seeded task backlog so deterministic-core work precedes orchestration/interface
> work.

- P0: <deterministic core / foundation>
- P1: ...
- P2: ...

## 8. Out of scope

> Explicit non-goals. These become PRINCIPLES candidates and protect the project
> from scope drift.

- ...
- ...

## 9. Decisions already made / assumptions

> Anything you've already decided that should be locked in from day one. Each
> becomes a seeded `DECISIONS.md` entry. Mark any of these you consider
> **foundational** — the bootstrap will weigh them when deriving PRINCIPLES.

- ...
- ...

## 10. Glossary

> Domain terms with definitions. Shared vocabulary for every agent that touches
> this project.

- <term>: <definition>
- <term>: <definition>
