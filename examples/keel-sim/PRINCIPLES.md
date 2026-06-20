# KEEL Gate Simulator — PRINCIPLES

> Founding, near-immutable commitments. A CORE statement or implementation that
> violates one is a defect, not a new fact. Amend only via a `principle-amendment`
> task packet.

## P-1 — Mechanism, not realism

The simulator validates how KEEL's *gates respond to given behaviors*. It makes no
claim about how real agents behave. Any output, comment, or report that presents a
synthetic profile parameter as a fact about real agents is a defect.

_Derived from spec §2, §8, FM-3._

## P-2 — Determinism is absolute

The same seed produces byte-identical results, always. No wall-clock, no unseeded
RNG, no reliance on set/dict iteration order may leak into a result. A
non-reproducible run is a defect, not "noise."

_Derived from INV-1, FM-2._

## P-3 — Every metric is counted, never asserted

Each reported number is a ratio of tallied trial outcomes. No metric may be
hand-set, hard-coded, or read directly off a profile parameter. If a result could
be produced without running the trials, it is invalid.

_Derived from INV-4, FM-1._

## P-4 — The core is pure

The core (substrate, profiles, gate, runner, metrics) imports no third-party
package and makes no network call. Dependencies belong only in optional CLI or
reporting edges, never in the trial path.

_Derived from INV-5, spec §3._

## P-5 — The gate runs in order, every trial

Each trial's outcome is produced by actually running scope → scenario → review in
that order. No trial may shortcut to an outcome. The gate's order mirrors KEEL's
real gate; reordering or skipping a stage is a defect.

_Derived from FM-4, and the gate ordering KEEL itself enforces._

---

## Superseded

_(empty at bootstrap)_
