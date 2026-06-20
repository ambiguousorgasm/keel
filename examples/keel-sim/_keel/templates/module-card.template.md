# Module Card — <Subsystem>

> The detail view for a subsystem listed in `COMPONENTS.md`. Read this before
> editing any file under this module's paths.

## Purpose

<One paragraph: what this module exists to do.>

## Authority

<What this module is allowed to decide and mutate. Be explicit.>

## Inputs

- <input>: <where it comes from, what shape it has>

## Outputs

- <output>: <where it goes, what shape>

## State it MAY mutate

- <state element>

## State it may NOT mutate

- <state element owned by another subsystem>

## Allowed dependencies

- <module / package>

## Forbidden dependencies

- <module / package> — <why forbidden>

## Public interfaces

- `<function or endpoint signature>` — <purpose>

## Invariants upheld

- **INV-n:** <statement> — how this module enforces it

## Relevant tests

- `tests/unit/<...>`
- `tests/scenarios/test_INV-n.py`

## Known gaps

- <gap or TBD>
