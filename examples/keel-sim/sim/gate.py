"""gate — the KEEL gate mechanism under test.

This is the heart of the simulator: it mirrors KEEL's real gate ordering and
classifies a trial's outcome. The ordering (P-5) is exactly KEEL's:

    1. scope check     — deterministic. A diff touching files outside the
                         allowed scope is caught with certainty WHEN scope
                         enforcement is available (KEEL: git diff vs allowlist).
    2. scenario check  — deterministic. A functionally-wrong diff is caught IFF
                         a scenario test covers it.
    3. review          — judgment. Only the reviewer can catch a principle
                         violation (INV-3). May also false-positive on clean work.

The first stage that catches the diff decides the outcome (rework). A principle
violation only "escapes" if it survives scope + scenario (which don't see it) and
the reviewer misses it.
"""

from __future__ import annotations

import random
from enum import Enum

from .profiles import Reviewer
from .substrate import Diff


class Outcome(Enum):
    MERGED_CLEAN = "merged_clean"
    MERGED_WITH_VIOLATION = "merged_with_violation"  # a principle violation escaped
    REWORK_SCOPE = "rework_scope"                     # caught by scope check
    REWORK_SCENARIO = "rework_scenario"               # caught by scenario test
    REWORK_REVIEW = "rework_review"                   # caught by the reviewer
    FALSE_REJECT = "false_reject"                      # clean work wrongly rejected


def classify(
    rng: random.Random,
    diff: Diff,
    reviewer: Reviewer,
    *,
    scope_enforcement: bool = True,
) -> Outcome:
    """Run the gate in order and return the outcome for one trial.

    `scope_enforcement` models whether KEEL's deterministic scope check is active
    (in KEEL: whether git is available so verify_task can diff against the
    allowlist). Turning it off lets scope violations through — used to show the
    value of the mechanical check.
    """
    # 1. scope — deterministic
    if diff.touches_out_of_scope and scope_enforcement:
        return Outcome.REWORK_SCOPE

    # 2. scenario — deterministic
    if diff.is_functionally_wrong and diff.covered_by_scenario:
        return Outcome.REWORK_SCENARIO

    # 3. review — judgment
    if diff.has_principle_violation:
        if reviewer.catches_violation(rng, diff):
            return Outcome.REWORK_REVIEW
        return Outcome.MERGED_WITH_VIOLATION  # escaped

    # clean diff (no principle violation surviving to review): reviewer may still
    # wrongly reject it.
    if reviewer.false_positive(rng):
        return Outcome.FALSE_REJECT

    return Outcome.MERGED_CLEAN
