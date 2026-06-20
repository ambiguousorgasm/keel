"""substrate — the abstract project and synthetic diffs.

This is the data layer. It imports nothing from the rest of the simulator
(P-4, INV-5) and defines what a synthetic project and a synthetic Diff are.

A Diff is the unit a builder produces. It carries exactly the properties KEEL's
gate cares about:

- `touches_out_of_scope`: did it edit a file outside the task's allowed scope?
  (KEEL's scope_allowlist check is about precisely this.)
- `has_principle_violation`: does it contradict a project principle? This is the
  kind of thing no machine check catches — only review can.
- `is_functionally_wrong`: would a scenario test covering it fail?
- `covered_by_scenario`: does a scenario test actually cover the changed area?

The Diff does NOT carry its own verdict — classification is the gate's job (P-5).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Project:
    """An abstract project: how many subsystems, and the scenario coverage level.

    `scenario_coverage` is the probability that a functional bug lands in an area
    a scenario test covers (and is therefore caught deterministically). It models
    the maturity of the project's test suite, not anything about agents.
    """

    n_subsystems: int = 6
    scenario_coverage: float = 0.7

    def __post_init__(self) -> None:
        if self.n_subsystems < 1:
            raise ValueError("n_subsystems must be >= 1")
        if not 0.0 <= self.scenario_coverage <= 1.0:
            raise ValueError("scenario_coverage must be in [0, 1]")


@dataclass(frozen=True)
class Diff:
    """A synthetic change produced by a builder for one task.

    All fields are facts about the change itself, independent of any gate. The
    gate reads these to classify the outcome; it never sets them.
    """

    touches_out_of_scope: bool
    has_principle_violation: bool
    is_functionally_wrong: bool
    covered_by_scenario: bool
    # The builder's written explanation quality in [0, 1]. Only matters if a
    # reviewer (wrongly) reads the explanation instead of the diff.
    rationalization: float = 0.0
