---
name: "Dev: Map Module"
id: dev-map-module
description: >
  Generate or refresh a subsystem's module card from the spec and source tree. Use when a module card is missing, stale, or a subsystem's boundaries have changed.
version: 1.0
keywords: [keel, workflow, builtin]
---

# /dev-map-module

**Role:** module-card author. Generate or refresh the card for one subsystem.

**prompt_version:** 1.0

**Usage:** `/dev-map-module <subsystem-name>`

---

You are writing or refreshing the module card for `$ARGUMENTS`.

## Read

1. `AGENTS.md`
2. `_keel/spec_model.yml` — find the subsystem definition by name
3. `COMPONENTS.md` — find the subsystem entry
4. `CORE.md` — relevant subsystem section
5. The existing card at `docs/module-cards/$ARGUMENTS.md` (if any)
6. The actual source files under the subsystem's paths (use the code map at
   `docs/code-map/$ARGUMENTS.md` if it exists)

## Produce `docs/module-cards/$ARGUMENTS.md`

Use `_keel/templates/module-card.template.md` as the structure. Fill every
field. Mark genuine unknowns as `TBD — needs design`. Do NOT invent invariants,
authorities, or interfaces that aren't grounded in the spec or the existing
source.

## Hard constraints

- **State derives from `spec_model.yml`.** If the module card disagrees with
  the spec, the spec wins — flag the disagreement to the human.
- **Don't paraphrase invariants.** Quote them verbatim from `PRINCIPLES.md` /
  `CORE.md` / `spec_model.yml`. Paraphrased invariants are how systems
  silently drift.

## Trace

```json
{"role": "mapper", "action": "module_card_written", "subsystem": "$ARGUMENTS", "prompt_version": "dev-map-module@1.0"}
```
