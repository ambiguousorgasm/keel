# BOOTSTRAP_REPORT — KEEL Gate Simulator

## 1. Files created
PRINCIPLES.md (P-1..P-5), CORE.md, COMPONENTS.md, DECISIONS.md (D-001, D-002),
STATUS.md, CHANGELOG.md, AGENTS.md, AI_START_HERE.md, _keel/spec_model.yml.
sim/ package (substrate, profiles, gate, runner, metrics, experiments).
tests/unit/test_sim.py. tasks/active/SIM-001..004. RESULTS.md.

## 2. Extracted model
6 subsystems (substrate, profiles, gate, runner, metrics, experiments);
5 invariants (INV-1 determinism, INV-2 deterministic scope, INV-3 reviewer is
sole principle-catcher, INV-4 counted metrics, INV-5 pure core);
4 failure modes (FM-1 circular validation, FM-2 hidden nondeterminism,
FM-3 mechanism≠realism, FM-4 gate bypass); 4 phases P0→P3.

## 3. Verification (CoVe)
| Question | Result |
|---|---|
| Does every subsystem's must_not_mutate exclude state another owns? | ✅ one-way data flow; only gate classifies outcomes. |
| Each invariant has a test? | ✅ INV-1..INV-5 each have ≥1 test in test_sim.py. |
| Any phase before its dependency? | ✅ P0→P1→P2→P3 in order. |
| Domain fact not in spec introduced? | ✅ none; gate ordering mirrors KEEL's real gate. |
| Each principle falsifiable + CORE complies? | ✅ e.g. P-3 ("metrics counted") is enforced by test_escape_rate_is_not_one_minus_catch_param. |
| DECISIONS cite principles? | ✅ D-001 cites P-1,P-4; D-002 cites P-2. |

## 4. Assumptions
- Default 10,000 trials / data point (D-001-adjacent; tunable, non-foundational).
- scenario_coverage=0.7 as a project-maturity default (substrate).

## 5. Open questions
- None blocking. A future LLM-in-the-loop harness (out of scope here) would let
  us calibrate the synthetic profiles against real run data.

## 6. Recommended first task
SIM-001-substrate-and-profiles (P0; everything else depends on it).
