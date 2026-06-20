# KEEL skills

A tool-agnostic, filesystem-based skill system. A **skill** is a folder under
`_keel/skills/` containing a `SKILL.md`:

```
_keel/skills/
├── README.md                  # this file (ignored by the loader)
├── dev-plan-task/             # a skill
│   └── SKILL.md
├── my-skill/
│   ├── SKILL.md               # required
│   ├── scripts/               # optional bundled files
│   │   └── helper.py
│   └── references/
│       └── cheatsheet.md
```

The folder name is the skill **id** (kebab-case). Drop a new folder in, and it
is immediately discoverable — no registration step.

## SKILL.md format

YAML frontmatter (between `---` fences) + a markdown body:

```markdown
---
name: My Skill
description: >
  What this does AND when to use it, in 1-3 sentences. This is the only text an
  agent sees when surveying skills, so make the trigger explicit.
version: 0.1
keywords: [example]
---

# My Skill

Full instructions for the agent go here...
```

Required frontmatter: `name`, `description`. Everything else is optional. If you
include `id`, it must match the folder name.

## Progressive disclosure

The system is built so agents don't load every skill body into context:

1. **Survey** — `keel-skills list` / `repo.list_skills()` reads only frontmatter.
   `repo.skills_index()` renders a compact id+description list to inject into a
   prompt.
2. **Load** — when a skill is relevant, `repo.get_skill(id)` pulls the full body.
3. **Bundled files** — `repo.load_skill_file(id, "scripts/helper.py")` reads a
   bundled file on demand.

KEEL is the registry and loader. It does **not** execute bundled scripts or
decide when a skill fires — that stays with whatever agent consumes the skill,
which is what keeps the system open and tool-neutral.

## Authoring a skill

```bash
keel-skills new my-skill --name "My Skill" --description "Does X. Use when Y."
# or, no install:
python _keel/scripts/agent/skills.py new my-skill
```

This scaffolds `_keel/skills/my-skill/SKILL.md` from
`_keel/templates/SKILL.template.md`. Edit the description and body, add any
bundled files, done.

## CLI

```bash
keel-skills list                 # id + description for every skill
keel-skills show dev-plan-task   # print the full body + bundled file list
keel-skills search planning      # match id/name/description/keywords
keel-skills new my-skill         # scaffold a new skill
```

## Python API

```python
from keel import KeelRepo
repo = KeelRepo.discover()

for info in repo.list_skills():          # cheap: frontmatter only
    print(info.id, "-", info.description)

skill = repo.get_skill("dev-plan-task")  # full load
print(skill.render())                    # the body, ready to inject

prompt_context = repo.skills_index()     # compact index for an agent
```

## The builtin `dev-*` skills

The seven `dev-*` skills implement the KEEL task-packet workflow (plan → build
context → implement → write scenario → review → handoff, plus map-module). They
ship with KEEL and use the same format as any skill you author — they're just
the ones included by default.

## Wiring into agent tools

### Claude Code

Claude Code reads slash commands from `.claude/commands/`. To expose KEEL skills
as commands, copy each skill's body:

```bash
for d in _keel/skills/*/; do
  id=$(basename "$d")
  cp "$d/SKILL.md" ".claude/commands/$id.md"
done
```

(Or symlink, or generate on demand from `repo.get_skill(id).body`.)

### Other agents / custom orchestrators

Use the Python API or `keel-skills` CLI to survey and load skills, then inject
the loaded body into your agent's prompt. Nothing about the format is
Claude-specific.
