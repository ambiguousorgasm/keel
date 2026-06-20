# Worked example — URL shortener

This folder shows what a complete KEEL bootstrap produces for a small but
non-trivial project: a URL shortener API with storage, encoding, an HTTP
layer, and analytics.

It exists for two reasons:

1. **Calibration.** When you run the bootstrap on your own project, compare
   the output against this example. If your generated CORE.md is half the
   size and missing per-subsystem rules, the bootstrap didn't go deep
   enough — push back, or improve your `PROJECT_SPEC.md`.
2. **Smoke test.** This was used during KEEL's own development to verify the
   bootstrap protocol could produce coherent output across all the
   templates. The files here are hand-crafted approximations of what an
   agent would generate, not literal script output.

## What's here

| File | Role | What to look at |
|---|---|---|
| `PROJECT_SPEC.md` | The single human-authored input | The shape of subsystems, invariants, failure modes |
| `spec_model.yml` | Step 2 structured extraction (validates against schema) | The 1-to-1 mapping from spec → ids |
| `PRINCIPLES.md` | Step 4 founding commitments | All 5 falsifiable; each derivable from spec §1/§5/§8 |
| `CORE.md` | Step 4 normative design truth | Per-subsystem authority blocks; INV ids preserved |
| `COMPONENTS.md` | Step 4 component registry | Boundary discipline (owns / must-not-mutate) |
| `docs/module-cards/storage.md` | Step 5 sample module card | What "TBD — needs design" markers look like in practice |
| `tasks/active/URLS-001-storage-bootstrap/brief.md` | Step 7 sample task | Scope allowlist; non-goals; complexity hint |
| `BOOTSTRAP_REPORT.md` | Step 9 generated report | The CoVe verification trace that closes the bootstrap |

## What's NOT here

To keep the example focused, I omitted:

- `DECISIONS.md` (seeded with just D-001 in this example)
- `STATUS.md` and `CHANGELOG.md` (templates fill in trivially)
- Test stubs under `tests/scenarios/` (each `INV-n` and `FM-n` gets one)
- All seven task packets the bootstrap would seed; only one is shown

## How to read this for your own bootstrap

Read in the order listed above (`PROJECT_SPEC.md` first). For each file,
ask: "Could I trace this content back to the spec?" If yes, the bootstrap
worked. If a generated file contains something *not* derivable from the
spec, that's an assumption — it should appear in `BOOTSTRAP_REPORT.md` and
likely also as a `D-NNN` marked `assumed`.
