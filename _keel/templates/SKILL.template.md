---
name: {{NAME}}
id: {{ID}}
description: >
  {{DESCRIPTION}}
  (Write 1-3 sentences covering BOTH what this skill does AND when an agent
  should reach for it. This text is all an agent sees when surveying skills —
  make the trigger conditions explicit. e.g. "Convert a messy CSV into a clean
  schema-validated table. Use when the user uploads tabular data that needs
  cleaning before analysis.")
version: 0.1
keywords: []
# Optional flags:
#   manual_only: true   # never auto-selected by an agent; exported with
#                       # disable-model-invocation:true (use for release/destructive work)
#   export: false       # keep this skill out of .agents/skills/ (e.g. a local demo)
# Optional: document expected inputs so callers know how to invoke this skill.
# inputs:
#   - name: target
#     description: what the skill operates on
---

# {{NAME}}

> Replace this body with the full instructions an agent should follow once this
> skill is loaded. The body is only pulled into context when the skill is
> actually used (progressive disclosure), so it can be as detailed as needed.

## What this does

<one paragraph>

## When to use it

<the conditions that should trigger this skill — mirror the description>

## Steps

1. ...
2. ...

## Hard constraints

- <things the agent must NOT do>

## Bundled files (optional)

If this skill ships helper scripts or references, put them alongside SKILL.md:

```
{{ID}}/
├── SKILL.md
├── scripts/
│   └── helper.py
└── references/
    └── notes.md
```

Reference them by relative path; an agent loads them on demand via
`keel.load_skill_file("{{ID}}", "scripts/helper.py")`. KEEL exposes bundled
files but does not execute them — running a helper is the agent's decision.
