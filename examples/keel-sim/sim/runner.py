"""runner — seeded trial orchestration (INV-1).

Owns the RNG lifecycle. A batch creates ONE random.Random(seed) and threads it
through every draw, so a (seed, builder, reviewer, project, n) tuple fully
determines the outcome sequence. Nothing here touches the global RNG (P-2).
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass

from .gate import Outcome, classify
from .profiles import Builder, Reviewer
from .substrate import Project


def run_trial(
    rng: random.Random,
    builder: Builder,
    reviewer: Reviewer,
    project: Project,
    *,
    scope_enforcement: bool = True,
) -> Outcome:
    """One task cycle: builder produces a diff, the gate classifies it."""
    diff = builder.sample_diff(rng, project)
    return classify(rng, diff, reviewer, scope_enforcement=scope_enforcement)


@dataclass
class BatchResult:
    """Outcome tally for a batch of trials. Pure counts — metrics are derived
    from these (P-3), never set here."""

    n: int
    counts: Counter
    # the number of trials in which a principle violation was actually introduced
    # (needed to compute escape RATE without echoing the input parameter).
    principle_violations_introduced: int

    def __getitem__(self, outcome: Outcome) -> int:
        return self.counts.get(outcome, 0)


def run_batch(
    builder: Builder,
    reviewer: Reviewer,
    project: Project | None = None,
    *,
    n: int = 10_000,
    seed: int = 0,
    scope_enforcement: bool = True,
) -> BatchResult:
    """Run `n` seeded trials and return the outcome tally.

    The builder's sampling and the reviewer's draws all pull from a single
    RNG seeded with `seed`, so the result is byte-reproducible (INV-1).
    """
    project = project or Project()
    rng = random.Random(seed)
    counts: Counter = Counter()
    violations_introduced = 0

    for _ in range(n):
        diff = builder.sample_diff(rng, project)
        if diff.has_principle_violation:
            violations_introduced += 1
        outcome = classify(rng, diff, reviewer, scope_enforcement=scope_enforcement)
        counts[outcome] += 1

    return BatchResult(
        n=n,
        counts=counts,
        principle_violations_introduced=violations_introduced,
    )
