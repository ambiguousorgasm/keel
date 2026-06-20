# <ID> — <short title>

> **Complexity hint:** `trivial` | `moderate` | `complex`
> (Optional metadata. Used by orchestrators to route to an appropriately-sized
> model. KEEL does not enforce a model choice — this is a signal, not a command.)

## Objective

<One paragraph: what changes and why. State the user-visible or system-visible
outcome, not the implementation approach.>

## Allowed scope

> Glob list. The reviewer enforces this — changes outside scope require a new
> task or an explicit decision.

- `path/glob/**`
- `path/glob/**`

## Non-goals

> Things to deliberately NOT do in this task. Protects against scope creep.

- Do not <X>.
- Do not <Y>.

## Relevant sources

> The agent's `context.md` will pull these in verbatim. List the smallest set
> that's actually needed.

- `PRINCIPLES.md`: <relevant P-n>
- `CORE.md`: <section>
- `COMPONENTS.md`: <subsystem>
- `DECISIONS.md`: <entries>
- `STATUS.md`: <current phase>
- Module cards: `docs/module-cards/<slug>.md`

## Acceptance criteria

> Observable, testable. Each criterion maps to a check in `acceptance.yml`.

- <observable behavior 1>
- <observable behavior 2>
- A scenario test demonstrates the failure before and the fix after.
- No unrelated behavior changes (lint + scope check passes).

## Risk notes (optional)

> Anything the builder should be aware of that isn't obvious from the brief.

- ...
