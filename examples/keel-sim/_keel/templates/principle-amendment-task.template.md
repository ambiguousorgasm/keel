# <ID> — Principle Amendment: <P-n short name>

> This is a `principle-amendment` task. It uses a heavier process than an
> ordinary task because PRINCIPLES is the near-immutable layer. Do not collapse
> these requirements into a regular task brief.

## Principle being changed

- **Principle id:** P-n
- **Current statement:**
  > <verbatim from PRINCIPLES.md>

## Proposed change

- **Type:** amend | supersede | retire
- **Proposed new statement** (if amend or supersede):
  > <new falsifiable sentence>
- **New principle id** (if supersede): P-<next>

## Justification

> What in the project's purpose, scope, or environment has shifted to justify
> reopening this principle. Be specific. "I changed my mind" is not enough.

- ...

## Downstream impact

> CORE.md sections, DECISIONS.md entries, and module cards that depend on this
> principle. Each must be reviewed for consistency after the amendment lands.

- **CORE.md sections affected:**
- **DECISIONS.md entries depending on P-n:**
- **Module cards affected:**

## Required reviewers

- An independent reviewer from a **different model family** than the proposer.
- The reviewer must explicitly confirm that the justification is real and not
  a rationalization for an in-flight implementation difficulty.
- If the change retires or weakens a safety/safeguard principle, a human
  reviewer is REQUIRED (no agent-only sign-off).

## On approval

- [ ] Mark old P-n as `superseded-by P-m` in PRINCIPLES.md (never delete).
- [ ] Append the new entry.
- [ ] Add a `CHANGELOG.md` entry under its own `## Principle Amendment` heading
      linking to this task packet.
- [ ] Re-audit DECISIONS.md entries that cited the old P-n; record any
      downstream amendments as new DECISIONS entries.

## Acceptance

- The amendment is recorded correctly in PRINCIPLES.md and CHANGELOG.md.
- No CORE.md statement violates the new principle (or, if it does, a follow-up
  task is opened to bring CORE into compliance).
- The dependent DECISIONS entries are re-audited.
