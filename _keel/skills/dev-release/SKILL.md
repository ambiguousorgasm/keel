---
name: "Dev: Release"
id: dev-release
description: >
  Carry out release-adjacent work: version bumps, release notes, tagging,
  packaging/build, publishing, deployment, and migrations. Use ONLY when a human
  has explicitly asked for a release step. This skill is manual-only — an agent
  must never select or run it on its own, because its actions are irreversible or
  externally visible.
version: 1.0
keywords: [keel, release, versioning, packaging, deploy, migration, builtin]
manual_only: true
---

# /dev-release

**Role:** release operator, under explicit human direction. Every irreversible or
externally-visible action requires an unambiguous human go-ahead for *that* action.

**prompt_version:** 1.0

> **Manual-only.** This skill is exported with `disable-model-invocation: true`.
> Do not invoke it because a task "seems release-ish." Run it only when a human
> explicitly asks for the specific release step.

## What this does

Performs the deliberate, hard-to-undo work at the edge of a project: cutting a
version, writing release notes from the changelog, tagging, building/packaging,
publishing, deploying, and running migrations. These actions leave the repo's
safe boundary, so they are gated behind explicit human intent rather than agent
judgment.

## When to use it

Only on explicit human instruction naming the release action (e.g. "cut v0.2.0",
"build the release artifact", "publish", "run the migration"). Never as an
inferred next step, never to "finish" a feature, never autonomously.

## Steps

1. **Confirm the mandate.** Restate exactly which release action was requested and
   confirm scope. If the instruction is ambiguous about what will be published,
   tagged, deployed, or migrated, STOP and ask.
2. **Pre-flight.** Ensure the gate is green (`just check` / `keel doctor`), the
   working tree is clean, and `STATUS.md`/`CHANGELOG.md` reflect what is shipping.
   A red gate blocks the release.
3. **Stage the reversible parts first.** Version bump, release notes drafted from
   `CHANGELOG.md`, regenerated artifacts (e.g. `keel skills sync`, code map).
   Show these for review before anything irreversible.
4. **Gate each irreversible action separately.** Tagging, publishing, deploying,
   and migrations each get their own explicit confirmation. Do not batch them
   behind one "yes". State plainly what cannot be undone.
5. **Record it.** Add a `CHANGELOG.md` entry; if the release embodies a decision,
   add a `DECISIONS.md` entry citing principles. Update `STATUS.md` if the
   released state changes what is "built".
6. **Report.** List exactly what was changed, tagged, published, deployed, or
   migrated, and what remains manual.

## Hard constraints

- NEVER run autonomously or as an inferred step. Explicit per-action human
  go-ahead is required for anything irreversible or externally visible.
- NEVER publish, deploy, or migrate on a red gate or a dirty tree.
- NEVER weaken checks or skip the gate to get a release out.
- Destructive/irreversible operations (force-push, deletes, prod migrations) get
  an explicit, specific confirmation each — never a blanket approval.
- If credentials or secrets are involved, do not read, log, or echo them.
