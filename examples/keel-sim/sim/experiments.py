"""experiments — named parameter sweeps that produce falsifiable claims.

Each experiment validates a specific KEEL design decision. Results are text
tables. Consumes only the public outputs of runner + metrics (not internals).

Reminder (P-1): every claim is about KEEL's MECHANISM responding to chosen
synthetic behaviors — never a claim about how real agents behave.
"""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import summarize
from .profiles import Builder, Reviewer, ReviewerMode
from .runner import run_batch
from .substrate import Project

DEFAULT_N = 10_000
DEFAULT_SEED = 1234


@dataclass
class Row:
    label: str
    values: dict[str, float]


@dataclass
class ExperimentResult:
    title: str
    claim: str
    columns: list[str]
    rows: list[Row]

    def render(self) -> str:
        out = [f"## {self.title}", "", f"_Claim tested: {self.claim}_", ""]
        header = "| " + " | ".join(["sweep", *self.columns]) + " |"
        sep = "|" + "|".join(["---"] * (len(self.columns) + 1)) + "|"
        out += [header, sep]
        for r in self.rows:
            cells = [f"{r.values[c]:.3f}" for c in self.columns]
            out.append("| " + " | ".join([r.label, *cells]) + " |")
        return "\n".join(out) + "\n"


# ── E1: scope enforcement is mechanical ──────────────────────────────────────


def exp_scope_is_mechanical(n: int = DEFAULT_N, seed: int = DEFAULT_SEED) -> ExperimentResult:
    """As builder scope-creep rises, the deterministic scope gate catches all of
    it (escaped-scope ≈ 0) — but ONLY when scope enforcement is on. With it off,
    scope violations merge at the creep rate. Validates: scope is a machine
    guarantee, not a review burden."""
    project = Project()
    reviewer = Reviewer()
    rows = []
    for creep in (0.0, 0.1, 0.2, 0.35, 0.5):
        builder = Builder(scope_creep_rate=creep, principle_drift_rate=0.0)
        on = summarize(run_batch(builder, reviewer, project, n=n, seed=seed))
        off = summarize(
            run_batch(builder, reviewer, project, n=n, seed=seed, scope_enforcement=False)
        )
        rows.append(Row(
            label=f"creep={creep:.2f}",
            values={
                "scope_rework (on)": on.rework_scope_rate,
                "merged_clean (on)": on.clean_merge_rate,
                "merged_clean (off)": off.clean_merge_rate,
            },
        ))
    return ExperimentResult(
        title="E1 — Scope enforcement is mechanical",
        claim="with scope enforcement on, builder scope-creep is caught deterministically; with it off, it merges at the creep rate.",
        columns=["scope_rework (on)", "merged_clean (on)", "merged_clean (off)"],
        rows=rows,
    )


# ── E2: principle drift depends on review ────────────────────────────────────


def exp_principles_need_review(n: int = DEFAULT_N, seed: int = DEFAULT_SEED) -> ExperimentResult:
    """Holding builder drift fixed, the principle ESCAPE rate tracks
    (1 - reviewer.catch_rate). The reviewer is the only thing standing between a
    principle violation and a merge (INV-3). Validates: the independent reviewer
    is load-bearing for principles."""
    project = Project()
    builder = Builder(scope_creep_rate=0.0, principle_drift_rate=0.2, competence=1.0)
    rows = []
    for catch in (0.0, 0.5, 0.7, 0.9, 0.99):
        reviewer = Reviewer(catch_rate=catch, false_positive_rate=0.0)
        m = summarize(run_batch(builder, reviewer, project, n=n, seed=seed))
        rows.append(Row(
            label=f"catch={catch:.2f}",
            values={
                "escape_rate": m.principle_escape_rate,
                "1 - catch": 1.0 - catch,
                "violation_merge": m.violation_merge_rate,
            },
        ))
    return ExperimentResult(
        title="E2 — Principle drift depends on independent review",
        claim="principle escape rate ≈ (1 - reviewer catch_rate); review is the sole catcher.",
        columns=["escape_rate", "1 - catch", "violation_merge"],
        rows=rows,
    )


# ── E3: read the diff, not the story ─────────────────────────────────────────


def exp_diff_vs_story(n: int = DEFAULT_N, seed: int = DEFAULT_SEED) -> ExperimentResult:
    """A reviewer who reads the builder's EXPLANATION lets a skilled rationalizer
    erode the catch; a reviewer who reads the DIFF does not. Same catch_rate,
    same builder — only the reviewer's mode differs. Validates KEEL's explicit
    dev-review-diff rule: review the raw diff, not the builder's framing."""
    project = Project()
    rows = []
    for rationalization in (0.0, 0.4, 0.7, 0.9):
        builder = Builder(
            scope_creep_rate=0.0, principle_drift_rate=0.2, competence=1.0,
            rationalization=rationalization,
        )
        diff_mode = Reviewer(
            catch_rate=0.8, false_positive_rate=0.0,
            framing_susceptibility=0.7, mode=ReviewerMode.DIFF,
        )
        story_mode = Reviewer(
            catch_rate=0.8, false_positive_rate=0.0,
            framing_susceptibility=0.7, mode=ReviewerMode.STORY,
        )
        d = summarize(run_batch(builder, diff_mode, project, n=n, seed=seed))
        s = summarize(run_batch(builder, story_mode, project, n=n, seed=seed))
        rows.append(Row(
            label=f"rationalize={rationalization:.2f}",
            values={
                "escape (reads diff)": d.principle_escape_rate,
                "escape (reads story)": s.principle_escape_rate,
                "story penalty": s.principle_escape_rate - d.principle_escape_rate,
            },
        ))
    return ExperimentResult(
        title="E3 — Read the diff, not the story",
        claim="reading the builder's explanation lets rationalization erode the catch; reading the diff is immune.",
        columns=["escape (reads diff)", "escape (reads story)", "story penalty"],
        rows=rows,
    )


# ── E4: cumulative drift over a horizon ──────────────────────────────────────


def exp_cumulative_drift(
    tasks: int = 500, seed: int = DEFAULT_SEED
) -> ExperimentResult:
    """Over a long sequence of tasks, escaped principle violations accumulate.
    The accumulation rate is governed by the reviewer's catch_rate. Validates:
    why high catch rate + PRINCIPLES matter for long-horizon stability."""
    project = Project()
    builder = Builder(scope_creep_rate=0.0, principle_drift_rate=0.15, competence=1.0)
    rows = []
    for catch in (0.6, 0.8, 0.95):
        reviewer = Reviewer(catch_rate=catch, false_positive_rate=0.0)
        # one batch of `tasks` trials = the horizon; escaped count is cumulative drift.
        batch = run_batch(builder, reviewer, project, n=tasks, seed=seed)
        from .gate import Outcome
        escaped = batch[Outcome.MERGED_WITH_VIOLATION]
        rows.append(Row(
            label=f"catch={catch:.2f}",
            values={
                "escaped_violations": float(escaped),
                "per_100_tasks": escaped / tasks * 100,
            },
        ))
    return ExperimentResult(
        title=f"E4 — Cumulative drift over {tasks} tasks",
        claim="escaped principle violations accumulate; the rate is set by reviewer catch_rate.",
        columns=["escaped_violations", "per_100_tasks"],
        rows=rows,
    )


ALL_EXPERIMENTS = [
    exp_scope_is_mechanical,
    exp_principles_need_review,
    exp_diff_vs_story,
    exp_cumulative_drift,
]


def run_all() -> str:
    parts = [
        "# KEEL Gate Simulator — Results",
        "",
        "> Mechanism validation only (P-1): each number is how KEEL's gate responds "
        "to chosen synthetic behaviors, NOT a claim about real agents.",
        "",
    ]
    for fn in ALL_EXPERIMENTS:
        parts.append(fn().render())
    return "\n".join(parts)
