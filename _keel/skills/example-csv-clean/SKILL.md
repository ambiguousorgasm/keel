---
name: Example - CSV Clean
id: example-csv-clean
description: >
  Example skill demonstrating bundled files. Cleans a messy CSV into a tidy,
  consistently-typed table. Use when someone hands you tabular data with ragged
  rows, mixed types, or junk headers that needs normalizing before analysis.
version: 0.1
keywords: [example, csv, data-cleaning, demo]
---

# Example — CSV Clean

> This is a sample skill included to demonstrate the skill format, including
> bundled scripts and references. Delete it or use it as a starting point.

## What this does

Takes a messy CSV and produces a cleaned version: trimmed headers, consistent
column types, dropped fully-empty rows.

## When to use it

When tabular input needs normalizing before any analysis or import. If the data
is already clean, skip this skill.

## Steps

1. Read the reference at `references/rules.md` for the cleaning conventions.
2. Apply the helper at `scripts/clean.py` (or follow its logic inline).
3. Report what was changed: rows dropped, columns retyped, headers fixed.

## Hard constraints

- Never silently drop rows that contain real data — only fully-empty rows.
- Never guess a type that loses precision (don't coerce IDs to floats).

## Bundled files

- `references/rules.md` — the cleaning conventions.
- `scripts/clean.py` — a reference implementation. KEEL exposes it; running it
  is the agent's choice.
