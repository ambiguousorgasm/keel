# KEEL Bootstrap Protocol

You are bootstrapping a project's development operating system. Follow these steps
in order. Do not write any application code during bootstrap — you are generating
governance scaffolding only.

If at any step you find yourself reasoning past an ambiguity, STOP and apply the
Step 3 clarify-or-assume gate. Inventing domain facts silently is the failure mode
this protocol exists to prevent.

**Idempotency:** the bootstrap is a one-time act. Re-running it on a repository
that has already been bootstrapped is out of scope and will not be supported. If
`PROJECT_SPEC.md` changes after the initial bootstrap, propagate the change via
deliberate per-document edits recorded as `DECISIONS.md` entries — not by
re-running this protocol and overwriting generated work.

---

## Step 1 — Read inputs

1. Read this entire file.
2. Read `PROJECT_SPEC.md` at the repository root in full.
3. Read every file in `_keel/templates/`.
4. Read `_keel/spec_model.schema.json`.

Do not summarize or skim. The protocol assumes you have read each of these end to
end.

---

## Step 2 — Extract a structured model of the project

This step produces `_keel/spec_model.yml`. Do NOT hold the extraction loosely in
prose — write it as a YAML file that validates against `_keel/spec_model.schema.json`
before you proceed. If a required field is missing or empty, that is a Step 3
clarify-or-assume trigger, not something to skip.

The extracted object contains:

- `project_name` and one-line `purpose`
- `project_prefix` — a short, all-caps abbreviation used as the prefix for task
  IDs (e.g. `ORDP` for "Order Pipeline"). 2–6 characters, no digits, no spaces.
  The human MUST supply this in `PROJECT_SPEC.md` §1; if missing, that is a
  Step 3 trigger.
- `problem` and `users` (if present in spec)
- `tech_stack` (languages, frameworks, datastore, runtime)
- `subsystems[]` — for each: `name`, `responsibility`, `owns_state`,
  `must_not_mutate`, `allowed_deps`, `forbidden_deps`
- `invariants[]` — each with a stable id `INV-n` and a falsifiable `statement`
- `failure_modes[]` — each with a stable id `FM-n` and `description`
- `phases[]` — each with `id` (`P0`, `P1`, ...), `name`, and `depends_on`
- `out_of_scope[]`
- `decisions_or_assumptions[]`
- `glossary` (object)

Every downstream artifact (PRINCIPLES, CORE, module cards, scenarios, decisions)
references these ids. Generate them once here and reuse them — never re-derive
them per step. Treating extraction as schema-valid, constrained output is what
makes the rest of the bootstrap deterministic and auditable.

**Cross-check before continuing:** for every subsystem, its `must_not_mutate` list
must not contain any state that no other subsystem `owns_state` claims. If a
mismatch exists, that is a Step 3 trigger.

---

## Step 3 — Clarify-or-assume gate

For anything **blocking and genuinely ambiguous**, ask the human up to 5 crisp
questions, then STOP and wait. Do not generate anything until they answer.

For **non-blocking gaps**, proceed using a clearly labelled assumption.

Never invent domain facts silently. Every assumption is logged in
`_keel/BOOTSTRAP_REPORT.md` and, if it constrains design, as a `DECISIONS.md` entry
marked `assumed`.

---

## Step 4 — Generate the core governance documents

Fill the templates in `_keel/templates/`, substituting project specifics. Generate
in this exact order — PRINCIPLES must exist before CORE so CORE can be checked
against it.

1. `PRINCIPLES.md` — 5–9 numbered, falsifiable commitments. See derivation rules
   below.
2. `CORE.md` — normative design truth, organized by subsystem. CORE must visibly
   comply with every principle.
3. `COMPONENTS.md` — one entry per subsystem, with boundaries from
   `spec_model.yml`.
4. `DECISIONS.md` — seed `D-001+` with decisions the spec implies or assumes.
   Every seeded entry MUST cite which principles it was checked against. Write
   `none directly applicable` if so, but never leave the field blank.
5. `STATUS.md` — phase 0: "nothing built yet"; list phases and current target.
6. `CHANGELOG.md` — single entry: `OS bootstrapped on <date>`.
7. `AGENTS.md` — the operational contract. Keep under ~150 lines.
8. `AI_START_HERE.md` — the canonical AI onboarding pointer. Fill the generated
   header (`{{PROJECT_NAME}}`, `{{PROJECT_PREFIX}}`, `{{PURPOSE}}`,
   `{{SUBSYSTEM_LIST}}`) from `spec_model.yml`; leave the static body unchanged.
   This is the FIRST file an AI is pointed at when it joins the project.
9. `CLAUDE.md`, `GEMINI.md` — per-tool bridge files (one-liners that point
   at `AGENTS.md`, so Claude Code and Gemini CLI find their conventional names
   but defer to the canonical contract). Codex uses `AGENTS.md` natively and
   needs no bridge.

### Rules for deriving `PRINCIPLES.md`

Principles are the project's near-immutable founding commitments. Generating them
well is what gives this file teeth instead of fluff:

- Aim for 5–9. Fewer than 5 means you missed something; more than 9 means several
  belong in CORE instead.
- Each principle MUST be **falsifiable** — phrased so you could point at a future
  CORE change and say "that violates P-n." Aspirational values fail this test.
    - ✗ "We value fairness." → unfalsifiable.
    - ✓ "Resolution is dice-honest: no outcome is altered after the roll is
      shown."
- Each gets a stable id `P-1`, `P-2`, ... referenced elsewhere.
- Source them from `PROJECT_SPEC.md`'s purpose, invariants, out-of-scope, and any
  decisions/assumptions the human marked as foundational — not from your own
  taste.
- If you cannot derive at least 5 falsifiable principles from the spec, that is a
  Step 3 trigger, not a license to invent them.

---

## Step 5 — Generate module cards

For each subsystem in `spec_model.yml`, create
`docs/module-cards/<slug>.md` from `module-card.template.md`. Fill every field you
can from the spec; mark genuine unknowns as `TBD — needs design`.

A module card must explicitly state:

- what state the module MAY mutate (from `owns_state`)
- what state it MAY NOT mutate (from `must_not_mutate`)
- its allowed and forbidden dependencies
- the invariants it upholds (cross-referenced by `INV-n`)

---

## Step 6 — Derive the initial scenario suite

For each invariant and each failure mode, create:

1. A prose scenario spec under `docs/test-scenarios/<id>-<slug>.md` (where `<id>`
   is the `INV-n` or `FM-n`).
2. A corresponding empty/xfail test stub under `tests/scenarios/test_<id>.py`
   (or whatever the project's test convention is).

Do not implement these fully — stub them so they fail informatively until built.
The point is that the architecture's invariants are executable from day one, even
if every test is red.

---

## Step 7 — Seed the task backlog

Create the `tasks/` structure:

```
tasks/
├── active/
├── completed/
└── blocked/
```

From the phases and the gaps you found, seed 3–7 starter task packets in
`tasks/active/` using `task-brief.template.md`, ordered so that deterministic-core
work precedes orchestration/interface work. Each packet folder gets at minimum:

- `brief.md` (from template)
- `acceptance.yml` (from template)

Task ID format: `<PROJECT_PREFIX>-<NNN>-<slug>` — where `PROJECT_PREFIX` is a
short, all-caps abbreviation of the project name chosen by the human (e.g. a
project called "Order Pipeline" might use `ORDP-001-event-store-init`). The
prefix is set once during bootstrap and never changes.

---

## Step 8 — Wire the command runner

KEEL ships the agent scripts at `_keel/scripts/agent/`. Do NOT copy them into the
repo — they live in `_keel/` so upstream updates can be pulled cleanly.

Create the following at the repository root (templates provided in
`_keel/templates/`):

- `justfile` — entry-point command runner. The canonical command `just check`
  must chain: format → lint → type-check → unit tests → scenario tests.
- `Makefile` — thin wrapper delegating to `just` for environments without it.

The justfile is generated from `_keel/templates/justfile.template` with the
project's tool choices substituted (formatter, linter, type-checker). If the
project's tech stack isn't covered by the template defaults, leave the relevant
commands as `# TODO: set <toolname>` and surface this in the bootstrap report.

Do NOT generate `scripts/agent/` at the repo root — those scripts live under
`_keel/`. Generate `scripts/checks/` only if the project needs custom check
wrappers beyond what the justfile expresses directly.

---

## Step 9 — Verify, then write the bootstrap report

**Do not skip this step.** This is where a misread spec is caught cheapest.

Generate 5–8 verification questions targeting the highest-risk parts of your
extraction. Examples:

- "Does every subsystem's `must_not_mutate` list actually exclude state another
  subsystem owns?"
- "Does each invariant have at least one scenario stub?"
- "Is any phase ordered before a phase it depends on?"
- "Did I introduce any domain fact not present in `PROJECT_SPEC.md`?"
- "Is each principle in `PRINCIPLES.md` falsifiable, and does `CORE.md` visibly
  comply with all of them?"
- "Does each seeded `DECISIONS.md` entry cite the principles it was checked
  against?"

Answer each against the files you generated — NOT from memory. Open each file and
verify. Fix what fails before writing the report.

Then write `_keel/BOOTSTRAP_REPORT.md` containing:

1. A tree of every file you created.
2. The structured model from `_keel/spec_model.yml`, reproduced inline so the human
   can verify your read against their spec.
3. The verification questions and your answers (the CoVe trace).
4. Every assumption you made and where it now lives (in PRINCIPLES, CORE, or
   DECISIONS).
5. Every question still open.
6. The recommended first task to pick up.

Then STOP. Do not begin implementation. The human reviews the bootstrap report
before any work begins.
