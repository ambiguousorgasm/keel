# KEEL Gate Simulator — Results

> Mechanism validation only (P-1): each number is how KEEL's gate responds to chosen synthetic behaviors, NOT a claim about real agents.

## E1 — Scope enforcement is mechanical

_Claim tested: with scope enforcement on, builder scope-creep is caught deterministically; with it off, it merges at the creep rate._

| sweep | scope_rework (on) | merged_clean (on) | merged_clean (off) |
|---|---|---|---|
| creep=0.00 | 0.000 | 0.883 | 0.883 |
| creep=0.10 | 0.099 | 0.797 | 0.883 |
| creep=0.20 | 0.200 | 0.706 | 0.883 |
| creep=0.35 | 0.352 | 0.570 | 0.883 |
| creep=0.50 | 0.500 | 0.439 | 0.883 |

## E2 — Principle drift depends on independent review

_Claim tested: principle escape rate ≈ (1 - reviewer catch_rate); review is the sole catcher._

| sweep | escape_rate | 1 - catch | violation_merge |
|---|---|---|---|
| catch=0.00 | 1.000 | 1.000 | 0.192 |
| catch=0.50 | 0.495 | 0.500 | 0.095 |
| catch=0.70 | 0.294 | 0.300 | 0.057 |
| catch=0.90 | 0.102 | 0.100 | 0.020 |
| catch=0.99 | 0.005 | 0.010 | 0.001 |

## E3 — Read the diff, not the story

_Claim tested: reading the builder's explanation lets rationalization erode the catch; reading the diff is immune._

| sweep | escape (reads diff) | escape (reads story) | story penalty |
|---|---|---|---|
| rationalize=0.00 | 0.198 | 0.198 | 0.000 |
| rationalize=0.40 | 0.198 | 0.408 | 0.210 |
| rationalize=0.70 | 0.198 | 0.585 | 0.387 |
| rationalize=0.90 | 0.198 | 0.704 | 0.505 |

## E4 — Cumulative drift over 500 tasks

_Claim tested: escaped principle violations accumulate; the rate is set by reviewer catch_rate._

| sweep | escaped_violations | per_100_tasks |
|---|---|---|
| catch=0.60 | 17.000 | 3.400 |
| catch=0.80 | 9.000 | 1.800 |
| catch=0.95 | 0.000 | 0.000 |

