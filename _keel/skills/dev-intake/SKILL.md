---
name: "Dev: Repository Intake"
id: dev-intake
description: >
  Orient in a KEEL repository before changing anything: find the source-of-truth
  documents, learn what is designed vs. actually built, and report the current
  state and the right next task. Use when you have just opened or joined an
  unfamiliar repo, are auditing project status, are unsure where to start, or are
  asked "what is this / where are we / what should I do next" — i.e. before any
  planning or implementation skill.
version: 1.0
keywords: [keel, onboarding, orientation, intake, audit, builtin]
---

# /dev-intake

**Role:** read-only orientation. You will NOT plan a specific change, write code,
or edit project files. Your only output is an accurate picture of where the
project is and what to do next.

**prompt_version:** 1.0

## What this does

Builds a correct mental model of a KEEL project from its own documents, so you
never reconstruct how the project works by guessing or reading source at random.
The repository is the source of truth; this skill teaches you to read it in the
right order.

## When to use it

The first time you touch a repository in a session, when you are asked to audit
or summarize project status, or whenever you are unsure what the next action
should be. It precedes `dev-plan-task` — orient first, then plan a bounded task.

## Steps

1. **Read the contract and onboarding.** Read `AGENTS.md` (operating rules) and
   `AI_START_HERE.md` (orientation pointer) in full. They define read order and
   the source-of-truth hierarchy.
2. **Read the design truth, top down.** `PRINCIPLES.md` → `CORE.md` →
   `COMPONENTS.md`. These are authoritative for *what the project is and must be*.
   Note the principle ids (P-n) and subsystem boundaries.
3. **Separate designed from built.** Read `STATUS.md` (implementation truth) and
   the newest `CHANGELOG.md` entries. `STATUS.md` — not the design docs — tells
   you what actually works. A design doc describing a feature is not evidence the
   feature exists.
4. **Survey decisions and open work.** Skim `DECISIONS.md` for accepted/assumed
   choices, then list task packets: `keel task list` (or read `tasks/active/`).
5. **Check health, don't assume it.** Run `keel doctor`. Report what it says
   rather than asserting the environment is fine.
6. **Survey skills, don't load them all.** Run `keel skills list` to see what
   workflows exist. Load a full skill body only when you actually reach that step.
7. **Report.** Produce a short briefing: what the project is (one line), current
   phase, what is built vs. pending, any gaps or conflicts you noticed, and the
   single recommended next task. Map conflicts to the source-of-truth hierarchy:
   a mismatch between code and CORE is a defect to investigate, not a new fact.

## Hard constraints

- Do NOT modify any file. This skill only reads and reports.
- Do NOT infer that a capability exists because a design document describes it —
  confirm against `STATUS.md`, tests, or the code itself.
- Do NOT load every skill body to "be thorough." Survey descriptions; load on demand.
- If `AGENTS.md` or the core documents are missing, say so plainly — the repo may
  not be bootstrapped yet (`_keel/BOOTSTRAP.md`).
