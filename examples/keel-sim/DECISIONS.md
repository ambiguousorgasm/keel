# DECISIONS

## D-001 — Mechanism-validation scope, no LLM in core
- Date: 2026-06-19
- Status: accepted
- Principles checked: P-1, P-4
- Context: Validating KEEL's gates could be done with real models, but that needs
  calibration data we don't have and conflates mechanism with realism.
- Decision: The core uses synthetic parameterized profiles only; no LLM calls.
- Consequences: Results are claims about KEEL's mechanism, not real agents. An
  LLM-in-the-loop harness is a separate future project.

## D-002 — Single seeded RNG threaded per trial
- Date: 2026-06-19
- Status: accepted
- Principles checked: P-2
- Context: Determinism (INV-1) requires controlling every random draw.
- Decision: One random.Random(seed) is created per batch and passed explicitly
  into sampling; nothing else may call the global RNG.
- Consequences: Reproducible runs; sampling functions must accept an rng argument.
