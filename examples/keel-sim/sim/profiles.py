"""profiles — synthetic agent behavioral profiles.

A profile is pure parameters. Sampling functions take an explicit `rng`
(random.Random) so that determinism (P-2, INV-1) is total — nothing here touches
the global RNG.

Honesty note (P-1): these parameters are *inputs we choose to test the gate's
response*. They are NOT measurements of real agents. "Builder drifts at 10%" is a
question we pose to the mechanism, never a claim about reality.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from .substrate import Diff, Project


class ReviewerMode(Enum):
    """How the reviewer forms its opinion.

    DIFF  — reads the raw diff (KEEL's design rule: independence in the weights).
    STORY — reads the builder's explanation first (the anti-pattern KEEL warns
            against; lets the builder's rationalization erode the catch).
    """

    DIFF = "diff"
    STORY = "story"


@dataclass(frozen=True)
class Builder:
    """A synthetic builder.

    competence            P(diff is functionally correct)
    scope_creep_rate      P(diff touches a file outside the allowed scope)
    principle_drift_rate  P(diff contains a principle violation)
    rationalization       quality of the builder's written explanation [0,1]
    """

    competence: float = 0.9
    scope_creep_rate: float = 0.1
    principle_drift_rate: float = 0.1
    rationalization: float = 0.0

    def sample_diff(self, rng: random.Random, project: Project) -> Diff:
        functionally_wrong = rng.random() >= self.competence
        covered = rng.random() < project.scenario_coverage
        return Diff(
            touches_out_of_scope=rng.random() < self.scope_creep_rate,
            has_principle_violation=rng.random() < self.principle_drift_rate,
            is_functionally_wrong=functionally_wrong,
            covered_by_scenario=covered,
            rationalization=self.rationalization,
        )


@dataclass(frozen=True)
class Reviewer:
    """A synthetic reviewer.

    catch_rate             base P(spotting a real principle violation)
    false_positive_rate    P(flagging a clean diff as a violation)
    framing_susceptibility how much the builder's story sways the reviewer [0,1];
                           only takes effect in STORY mode.
    mode                   DIFF (read the diff) or STORY (read the explanation).

    `effective_catch_rate(diff)` is what actually catches a violation. In DIFF
    mode it's just `catch_rate`. In STORY mode a skilled rationalizer erodes it:
        catch_rate * (1 - rationalization * framing_susceptibility)
    """

    catch_rate: float = 0.8
    false_positive_rate: float = 0.05
    framing_susceptibility: float = 0.6
    mode: ReviewerMode = ReviewerMode.DIFF

    def effective_catch_rate(self, diff: Diff) -> float:
        if self.mode is ReviewerMode.DIFF:
            return self.catch_rate
        erosion = 1.0 - (diff.rationalization * self.framing_susceptibility)
        return self.catch_rate * erosion

    def catches_violation(self, rng: random.Random, diff: Diff) -> bool:
        return rng.random() < self.effective_catch_rate(diff)

    def false_positive(self, rng: random.Random) -> bool:
        return rng.random() < self.false_positive_rate
