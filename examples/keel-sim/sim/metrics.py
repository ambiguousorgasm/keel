"""metrics — aggregate trial outcomes into reported rates.

Every value here is a ratio of counted outcomes (P-3, INV-4). No metric reads a
profile parameter. If a metric could be computed without the BatchResult, it
does not belong here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .gate import Outcome
from .runner import BatchResult


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


@dataclass(frozen=True)
class Metrics:
    """Derived rates for a batch. All in [0, 1]."""

    n: int
    # of the principle violations that were INTRODUCED, the fraction that reached
    # "merged" uncaught. This is the headline: it cannot be read off any single
    # input parameter — it depends on the whole gate.
    principle_escape_rate: float
    # of all trials, fraction that merged carrying a violation.
    violation_merge_rate: float
    # of all trials, fraction of clean work wrongly rejected.
    false_reject_rate: float
    # of all trials, fraction sent back for any reason.
    rework_rate: float
    # of all trials, fraction merged clean.
    clean_merge_rate: float
    # breakdown of why rework happened.
    rework_scope_rate: float
    rework_scenario_rate: float
    rework_review_rate: float


def summarize(batch: BatchResult) -> Metrics:
    n = batch.n
    escaped = batch[Outcome.MERGED_WITH_VIOLATION]
    rework = (
        batch[Outcome.REWORK_SCOPE]
        + batch[Outcome.REWORK_SCENARIO]
        + batch[Outcome.REWORK_REVIEW]
    )
    return Metrics(
        n=n,
        principle_escape_rate=_ratio(escaped, batch.principle_violations_introduced),
        violation_merge_rate=_ratio(escaped, n),
        false_reject_rate=_ratio(batch[Outcome.FALSE_REJECT], n),
        rework_rate=_ratio(rework, n),
        clean_merge_rate=_ratio(batch[Outcome.MERGED_CLEAN], n),
        rework_scope_rate=_ratio(batch[Outcome.REWORK_SCOPE], n),
        rework_scenario_rate=_ratio(batch[Outcome.REWORK_SCENARIO], n),
        rework_review_rate=_ratio(batch[Outcome.REWORK_REVIEW], n),
    )
