# KEEL Gate Simulator — Design Spec

## 1. Purpose (one line)

A deterministic, dependency-free simulator that validates KEEL's governance gates by running synthetic agents with known behavioral biases against an abstract project and measuring whether the gates behave as designed.

**Project name:** KEEL Gate Simulator
**Project prefix:** SIM

## 2. Problem & users

We make design claims about KEEL — "scope enforcement is mechanical," "an independent reviewer reading the raw diff catches principle drift," "reading the builder's explanation erodes that catch." Today those are arguments, not evidence. This simulator turns them into falsifiable measurements without needing real LLMs: it models agents as parameterized profiles and measures KEEL's *mechanism*, not agent realism. Users are KEEL maintainers validating or revising design decisions.

## 3. Tech stack

- Language(s): Python 3.11+
- Framework(s): none (standard library only — no LLM calls, no network)
- Datastore: none (in-memory; results printed/returned)
- Runtime / deploy target: a CLI / importable package

## 4. Subsystems

### substrate
- Responsibility: model an abstract project — subsystems that own files, a set of principles, and the notion of a synthetic diff that may carry scope or principle violations.
- State it OWNS: the synthetic project definition and Diff objects.
- State it must NOT touch: agent profiles, the gate logic, metrics.
- Talks to: nothing (it is the data layer).
- Must NOT depend on: profiles, gate, runner, metrics.

### profiles
- Responsibility: define synthetic agent behavioral profiles (Builder, Reviewer) as pure parameters, and the sampling that turns those parameters into concrete behaviors for a trial.
- State it OWNS: the profile dataclasses and a seeded RNG draw per trial.
- State it must NOT touch: the gate's verdict logic.
- Talks to: substrate (to produce Diffs).
- Must NOT depend on: gate, runner, metrics.

### gate
- Responsibility: model KEEL's gate exactly — deterministic scope check, deterministic scenario check, and judgment-based reviewer — and classify each trial's outcome.
- State it OWNS: the verdict/outcome classification.
- State it must NOT touch: profile internals beyond the sampled behavior.
- Talks to: substrate, profiles.
- Must NOT depend on: runner, metrics.

### runner
- Responsibility: execute trials — one task cycle and batches of N seeded trials — wiring substrate + profiles + gate together.
- State it OWNS: trial orchestration and the seeded RNG lifecycle.
- State it must NOT touch: metric aggregation math.
- Talks to: substrate, profiles, gate.
- Must NOT depend on: metrics' internal representation.

### metrics
- Responsibility: aggregate trial outcomes into reported rates (escape rate, catch rate, false-reject rate, cumulative drift).
- State it OWNS: the aggregation.
- State it must NOT touch: how trials are produced.
- Talks to: runner outputs (Outcome records).
- Must NOT depend on: substrate, profiles, gate internals.

### experiments
- Responsibility: the named experiments — parameter sweeps that produce falsifiable claims as tables.
- State it OWNS: experiment definitions and result formatting.
- Talks to: runner, metrics.
- Must NOT depend on: substrate/profiles/gate internals (only their public outputs).

## 5. Invariants

- INV-1: Determinism — running any experiment twice with the same seed produces byte-identical results.
- INV-2: Scope violations are caught deterministically when git/scope-enforcement is modeled as available; an in-scope-only diff never triggers a scope catch.
- INV-3: The reviewer's verdict is the ONLY mechanism that can catch a principle violation; if the reviewer is disabled, principle escape rate equals the builder's principle-drift rate.
- INV-4: Every reported metric is a ratio of counted outcomes — no metric is hand-set or derived from a profile parameter directly.
- INV-5: The core performs zero network calls and imports no third-party package.

## 6. Failure modes / risks

- FM-1: Circular validation — a metric that just echoes an input parameter would "prove" nothing. Metrics must be counted from outcomes.
- FM-2: Hidden nondeterminism — unseeded RNG, dict ordering, or wall-clock leaking into results would break INV-1.
- FM-3: Conflating mechanism with realism — presenting "synthetic builder drifts at 10%" as a claim about real agents. Outputs must be framed as mechanism validation only.
- FM-4: Gate bypass — a trial outcome computed without actually running the scope/scenario/review checks in the correct order.

## 7. Phases

- P0: substrate + profiles (the data and agents).
- P1: gate (the mechanism under test) + runner.
- P2: metrics.
- P3: experiments + CLI entry point.

## 8. Out of scope

- Any real LLM calls or API usage (that is a separate, much larger "LLM-in-the-loop" tool).
- Calibrating profile parameters against real agent run data.
- Claims about how real agents behave (only how KEEL's mechanism responds to given behaviors).
- Persistence, visualization beyond text tables, web UI.

## 9. Decisions already made / assumptions

- Mechanism-validation scope only; no LLM in the core. **Foundational.**
- Determinism via a single seeded RNG threaded through a trial. **Foundational.**
- Scope enforcement modeled as deterministic when git is available (mirrors verify_task). **Foundational.**
- Default trial counts: 10,000 per data point unless overridden. Not foundational; tunable.

## 10. Glossary

- **trial**: one simulated task cycle (builder produces a diff → gate runs → outcome).
- **profile**: a parameterized synthetic agent (Builder or Reviewer).
- **scope violation**: a diff touching files outside the task's allowed scope.
- **principle violation**: a diff that contradicts a project principle (not mechanically detectable; needs review).
- **escape**: a principle violation that reaches "merged" without being caught.
- **outcome**: the classified result of a trial (merged-clean, merged-with-violation, rework, false-reject).
