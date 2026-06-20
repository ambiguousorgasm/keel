# KEEL Gate Simulator — CORE (Normative Design Truth)

> CORE overrides satellites; CORE is accountable to PRINCIPLES.md. Changes recorded
> in DECISIONS.md.

## 1. System purpose & boundaries
A deterministic, pure-Python simulator that measures how KEEL's gates respond to
synthetic agents with known biases. It validates mechanism, not agent realism
(P-1). No LLM calls, no network, no third-party deps in the core (P-4).

## 2. Architecture overview
Data flows one way: `substrate` (project + Diffs) → `profiles` (sample behavior)
→ `gate` (scope → scenario → review → outcome) → `runner` (orchestrate N seeded
trials) → `metrics` (count outcomes into rates) → `experiments` (sweeps → tables).
A single seeded RNG is threaded through each trial (P-2).

## 3. Per-subsystem normative rules
### substrate
- Authority: defines the synthetic project and Diff shape. Owns Diff/Project types.
- Must NOT import profiles/gate/runner/metrics. Upholds: INV-5.
### profiles
- Authority: Builder/Reviewer parameters and sampling diffs/verdicts from a passed RNG.
- Never decides outcomes. Upholds: INV-3 (reviewer is the only principle-catcher).
### gate
- Authority: the outcome classifier. Runs scope (deterministic) → scenario
  (deterministic) → review (judgment), in that order (P-5). Upholds INV-2, INV-3, FM-4.
### runner
- Authority: trial orchestration; owns the seeded RNG lifecycle (P-2). Upholds INV-1.
### metrics
- Authority: aggregation only. Every output is a counted ratio (P-3). Upholds INV-4.
### experiments
- Authority: named sweeps + text tables. Consumes only public outputs of runner/metrics.

## 4. System-wide invariants
- INV-1 determinism · INV-2 scope is deterministic · INV-3 reviewer is sole
  principle-catcher · INV-4 metrics are counted · INV-5 pure core.

## 5. Out-of-scope
Real LLM calls; parameter calibration; claims about real agents; persistence; web UI.
Adding any requires a DECISIONS entry citing the principles it impacts.

## 6. Glossary
trial · profile · scope violation · principle violation · escape · outcome
(see spec §10).
