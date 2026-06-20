"""Tests for the KEEL gate simulator, organized around the spec's invariants.

These are unit tests (tests/unit). Scenario-level invariant tests live in
tests/scenarios.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

# make the sim package importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sim.experiments import run_all  # noqa: E402
from sim.gate import Outcome, classify  # noqa: E402
from sim.metrics import summarize  # noqa: E402
from sim.profiles import Builder, Reviewer, ReviewerMode  # noqa: E402
from sim.runner import run_batch  # noqa: E402
from sim.substrate import Diff, Project  # noqa: E402


# ─── INV-1: determinism ──────────────────────────────────────────────────────


def test_same_seed_same_batch():
    b = Builder(scope_creep_rate=0.2, principle_drift_rate=0.2)
    r = Reviewer(catch_rate=0.7)
    a = run_batch(b, r, n=2000, seed=42)
    c = run_batch(b, r, n=2000, seed=42)
    assert a.counts == c.counts
    assert a.principle_violations_introduced == c.principle_violations_introduced


def test_different_seed_different_batch():
    b = Builder(scope_creep_rate=0.2, principle_drift_rate=0.2)
    r = Reviewer(catch_rate=0.7)
    a = run_batch(b, r, n=2000, seed=1)
    c = run_batch(b, r, n=2000, seed=2)
    assert a.counts != c.counts


def test_run_all_is_byte_identical():
    assert run_all() == run_all()


# ─── INV-2: scope is deterministic ───────────────────────────────────────────


def test_out_of_scope_always_caught_when_enforced():
    rng = random.Random(0)
    diff = Diff(
        touches_out_of_scope=True, has_principle_violation=False,
        is_functionally_wrong=False, covered_by_scenario=False,
    )
    # Try many rng states; scope catch is deterministic regardless.
    for _ in range(100):
        assert classify(rng, diff, Reviewer(), scope_enforcement=True) == Outcome.REWORK_SCOPE


def test_in_scope_never_triggers_scope_rework():
    b = Builder(scope_creep_rate=0.0, principle_drift_rate=0.0, competence=1.0)
    batch = run_batch(b, Reviewer(false_positive_rate=0.0), n=5000, seed=7)
    assert batch[Outcome.REWORK_SCOPE] == 0


def test_scope_off_lets_creep_through():
    b = Builder(scope_creep_rate=0.3, principle_drift_rate=0.0, competence=1.0)
    off = run_batch(b, Reviewer(false_positive_rate=0.0), n=5000, seed=7,
                    scope_enforcement=False)
    assert off[Outcome.REWORK_SCOPE] == 0  # not enforced → never caught here


# ─── INV-3: reviewer is the sole principle-catcher ───────────────────────────


def test_disabled_reviewer_escape_equals_drift():
    # catch_rate 0 → every introduced violation escapes → escape_rate == 1.0
    b = Builder(scope_creep_rate=0.0, principle_drift_rate=0.25, competence=1.0)
    r = Reviewer(catch_rate=0.0, false_positive_rate=0.0)
    m = summarize(run_batch(b, r, n=10000, seed=3))
    assert m.principle_escape_rate == 1.0


def test_perfect_reviewer_catches_all():
    b = Builder(scope_creep_rate=0.0, principle_drift_rate=0.25, competence=1.0)
    r = Reviewer(catch_rate=1.0, false_positive_rate=0.0)
    m = summarize(run_batch(b, r, n=10000, seed=3))
    assert m.principle_escape_rate == 0.0
    assert m.violation_merge_rate == 0.0


# ─── INV-4 / FM-1: metrics are counted, not echoed ───────────────────────────


def test_escape_rate_is_not_one_minus_catch_param():
    # The escape rate is close to (1-catch) but NOT computed from it; with a
    # finite sample it must differ from the parameter at least sometimes.
    b = Builder(scope_creep_rate=0.0, principle_drift_rate=0.2, competence=1.0)
    diffs = []
    for catch in (0.3, 0.55, 0.82):
        m = summarize(run_batch(b, Reviewer(catch_rate=catch, false_positive_rate=0.0),
                                n=3000, seed=99))
        diffs.append(abs(m.principle_escape_rate - (1 - catch)))
    # If escape_rate were literally (1-catch), every diff would be exactly 0.
    assert any(d > 0 for d in diffs), "escape_rate appears to echo the parameter"


def test_metrics_are_ratios_in_range():
    b = Builder(scope_creep_rate=0.15, principle_drift_rate=0.15)
    m = summarize(run_batch(b, Reviewer(), n=3000, seed=5))
    for val in (m.principle_escape_rate, m.violation_merge_rate, m.false_reject_rate,
                m.rework_rate, m.clean_merge_rate):
        assert 0.0 <= val <= 1.0


# ─── INV-5: pure core ────────────────────────────────────────────────────────


def test_core_imports_no_third_party():
    import sim.substrate, sim.profiles, sim.gate, sim.runner, sim.metrics
    import sys as _sys
    # No common third-party libs should be pulled in by importing the core.
    for forbidden in ("numpy", "pandas", "requests", "scipy"):
        assert forbidden not in _sys.modules, f"core pulled in {forbidden}"


# ─── E3 mechanism: diff mode is immune to rationalization ────────────────────


def test_diff_mode_immune_to_rationalization():
    project = Project()
    high = Builder(principle_drift_rate=0.3, competence=1.0, rationalization=0.9)
    low = Builder(principle_drift_rate=0.3, competence=1.0, rationalization=0.0)
    r = Reviewer(catch_rate=0.8, false_positive_rate=0.0, mode=ReviewerMode.DIFF)
    m_high = summarize(run_batch(high, r, project, n=8000, seed=11))
    m_low = summarize(run_batch(low, r, project, n=8000, seed=11))
    # In DIFF mode, rationalization has no effect on escape rate (within noise).
    assert abs(m_high.principle_escape_rate - m_low.principle_escape_rate) < 0.03


def test_story_mode_eroded_by_rationalization():
    project = Project()
    high = Builder(principle_drift_rate=0.3, competence=1.0, rationalization=0.9)
    low = Builder(principle_drift_rate=0.3, competence=1.0, rationalization=0.0)
    r = Reviewer(catch_rate=0.8, false_positive_rate=0.0,
                 framing_susceptibility=0.7, mode=ReviewerMode.STORY)
    m_high = summarize(run_batch(high, r, project, n=8000, seed=11))
    m_low = summarize(run_batch(low, r, project, n=8000, seed=11))
    # In STORY mode, high rationalization meaningfully raises the escape rate.
    assert m_high.principle_escape_rate > m_low.principle_escape_rate + 0.1
