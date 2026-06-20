# COMPONENTS

## substrate
- **Path(s):** `sim/substrate.py`
- **Responsibility:** synthetic project, files, principles, Diff objects.
- **Owns state:** Project, Diff types.
- **May NOT mutate:** profiles/gate/runner/metrics.
- **Allowed dependencies:** (stdlib only)
- **Forbidden dependencies:** profiles, gate, runner, metrics
- **Upholds invariants:** INV-5

## profiles
- **Path(s):** `sim/profiles.py`
- **Responsibility:** Builder/Reviewer profiles + seeded sampling.
- **Allowed dependencies:** substrate
- **Forbidden dependencies:** gate, runner, metrics
- **Upholds invariants:** INV-3, INV-5

## gate
- **Path(s):** `sim/gate.py`
- **Responsibility:** scope → scenario → review → outcome classification.
- **Allowed dependencies:** substrate, profiles
- **Forbidden dependencies:** runner, metrics
- **Upholds invariants:** INV-2, INV-3, FM-4

## runner
- **Path(s):** `sim/runner.py`
- **Responsibility:** seeded trial orchestration (one + batch).
- **Allowed dependencies:** substrate, profiles, gate
- **Forbidden dependencies:** metrics
- **Upholds invariants:** INV-1

## metrics
- **Path(s):** `sim/metrics.py`
- **Responsibility:** count outcomes into rates.
- **Allowed dependencies:** (stdlib only)
- **Forbidden dependencies:** substrate, profiles, gate
- **Upholds invariants:** INV-4

## experiments
- **Path(s):** `sim/experiments.py`, `run_experiments.py`
- **Responsibility:** parameter sweeps → falsifiable tables.
- **Allowed dependencies:** runner, metrics
- **Upholds invariants:** INV-1
