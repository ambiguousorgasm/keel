---
name: "Dev: Update Docs"
id: dev-update-docs
description: >
  Update project documentation so it matches the code as built — governance
  docs (CORE, COMPONENTS, module cards), user/reference docs, and the code map.
  Use when documentation has drifted from the implementation, when a shipped
  change left docs stale, or when a task explicitly asks to document or correct
  reference material. NOT for design decisions (use a DECISIONS entry) and NOT
  for the per-task handoff (use dev-update-handoff).
version: 1.0
keywords: [keel, documentation, docs, drift, reference, builtin]
---

# /dev-update-docs

**Role:** documentation maintainer. You bring the prose in line with reality;
you do not change behavior or invent design.

**prompt_version:** 1.0

## What this does

Closes the gap between what the docs claim and what the code does, treating the
code and `STATUS.md` as ground truth and the documentation as the thing that must
be corrected to match. It keeps KEEL's documents trustworthy enough that an agent
can rely on them instead of re-reading the whole tree.

## When to use it

When you notice or are told that documentation no longer matches the code: a
renamed interface, a changed boundary, a removed feature still described as
present, a stale module card, or an out-of-date reference/README section. Use it
as a deliberate task — not as a side effect of an unrelated implementation task.

## Steps

1. **Establish ground truth first.** Read the relevant source and `STATUS.md`.
   What the code actually does wins over what any document says.
2. **Locate the authoritative doc for the claim.** Design truth lives in
   `CORE.md`/`COMPONENTS.md`/module cards under `docs/`; implementation truth in
   `STATUS.md`; history in `CHANGELOG.md`. Edit the right layer — do not restate
   design truth inside a reference doc.
3. **Correct the drift, minimally.** Change only what is wrong or missing. Match
   the existing voice and structure. Do not expand scope into a rewrite.
4. **Respect the hierarchy.** If the fix would change *design* (not just describe
   it), stop: that needs a `DECISIONS.md` entry citing principles, or a
   `principle-amendment` packet — not a doc edit. Documentation records design; it
   does not set it.
5. **Refresh generated docs.** If the code map is stale, run `keel code-map`. If
   skills changed, run `keel skills sync` so `.agents/` and the catalog match.
6. **Verify references resolve.** Check that links, file paths, INV-n/FM-n/P-n
   ids, and command names you touched are real and current.

## Hard constraints

- Do NOT change code behavior under cover of a docs task.
- Do NOT invent capabilities or document intended-but-unbuilt features as if they
  exist; describe what `STATUS.md` and the code support, and mark the rest clearly.
- Do NOT duplicate large instruction blocks across `README.md`, `AGENTS.md`, and
  skills — point to the canonical source instead.
- Do NOT edit `PRINCIPLES.md`, and do NOT smuggle a design decision into prose.
