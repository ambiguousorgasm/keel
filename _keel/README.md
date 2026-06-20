# KEEL — Repo-Native Agent Development OS

A reusable, project-agnostic "development operating system" you drop into a new
(or existing) repository. You write one design spec, an AI agent reads a fixed
bootstrap protocol, and it transforms that spec into a governed project scaffold.
After that, Claude Code or any other coding agent works inside the scaffold as a
disciplined, mostly-stateless worker.

KEEL is built for **software and system-design projects** — the templates assume
subsystems, scope globs, and scenario tests. Non-code projects can use it too
(a "subsystem" becomes a "section," a "scenario test" becomes a "review
checkpoint"), but that's not where most of the design effort went.

This README is the human-facing guide. The agent-facing protocol is
`BOOTSTRAP.md`.

---

## Start here

From a fresh copy of KEEL, just run:

```bash
python start.py
```

No installation required. It launches an interactive menu where you can create a
new project or read the rules & usage. If you'd like the `keel` command available
everywhere, it offers to install it for you (you can also skip that and keep
using `start.py`).

Prefer to do it by hand? See **Quick start** just below.

---

## Quick start

Create a new KEEL project and let an AI bootstrap it:

```bash
pip install -e _keel          # installs the `keel` command + bundled template
keel init ./my-project        # interactive: asks name, prefix, runner, git
cd ./my-project
# edit PROJECT_SPEC.md, then open the project in an AI coding tool and say:
#   "Read _keel/BOOTSTRAP.md and follow it."
keel doctor                   # confirm the environment is healthy
```

`keel init` sets up the project *frame* — the `_keel/` OS, a `PROJECT_SPEC.md`
skeleton, a valid placeholder `spec_model.yml`, justfile/Makefile, `.gitignore`,
optional git + `.env.example`. It deliberately stops there: writing your
PRINCIPLES, CORE, and module cards requires an AI reading your spec, which is the
bootstrap step. Run `keel` with no arguments for an interactive menu, or
`keel guide` for the rules & usage overview.



## Why this exists

What degrades on a long, multi-agent project is rarely the models' raw coding
ability. It is that the project's **true state** becomes distributed across code,
half-finished implementation, architecture docs, prior chats, planned phases,
scratch notes, and per-model memory. Every new agent has to reconstruct that
state, guess which documents are current, and decide where a task begins and ends.
Quality decays at the seams, not in the models.

This OS fixes that with three moves:

1. **The repository is the source of truth.** Agents are treated as stateless
   specialists. They are not the project's memory, project manager, or canon.
2. **A fixed bootstrap protocol** turns a single human-written design spec into
   the full governance scaffold — principles, core doc, component registry,
   decision log, status, module cards, scenario tests, task structure — so you
   never hand-build it again.
3. **A bounded task-packet workflow** forces every coding task to receive a
   defined scope, an authority boundary, a testable definition of done, and a
   required handoff record. No model is ever asked to "continue building the
   thing."

The goal is not to make agents remember more. It is to make them **need to
remember less**, because the repo hands them the correct task, current
constraints, limited scope, evidence standard, and next handoff every time.

---

## How to use this (five steps)

### Step 0 — Drop the OS in

Copy this entire `_keel/` folder into the root of your repository. It is inert
until you run it.

### Step 1 — Write your spec

Copy the template to the repo root and fill it in:

```bash
cp _keel/templates/PROJECT_SPEC.template.md ./PROJECT_SPEC.md
```

This is the *only* free-form authoring you do. Spend your effort here: the
quality of the generated scaffold is bounded by the quality of this spec. The
template is structured precisely so the bootstrap can extract modules,
invariants, and failure modes deterministically.

If you only invest in one thing, invest in writing tight **subsystems**,
**invariants**, and **failure modes**. Everything good downstream flows from
those three.

### Step 2 — Run the bootstrap

Open a fresh agent session (Claude Code is ideal because it can read and write
files in the repo) and give it exactly one instruction:

> Read `_keel/BOOTSTRAP.md` and follow it. The design spec is at `PROJECT_SPEC.md`.

The agent reads the protocol, reads your spec, asks any blocking clarifying
questions, then generates the full scaffold and writes a **bootstrap report** to
`_keel/BOOTSTRAP_REPORT.md` listing everything it created and every assumption it
made.

**Read that report before doing anything else** — it is where you catch a misread
spec cheaply.

### Step 3 — Review the seed (the five-minute gate)

In order:

1. **Read `PRINCIPLES.md` first.** Every principle should be falsifiable and feel
   like something you'd be willing to defend a year from now. Edit now if not.
2. Skim the generated `CORE.md`, `COMPONENTS.md`, the module cards, and the
   seeded `DECISIONS.md`.
3. Correct anything wrong now, while it's a dozen files instead of fifty.

### Step 4 — Work via task packets

From here, no one "continues building the project." Every nontrivial change
becomes a task packet:

```
tasks/active/<ID>-<slug>/
├── brief.md          # objective, allowed scope, non-goals, acceptance
├── plan.md           # the agent's plan-only pass, approved before any code
├── context.md        # GENERATED by scripts/agent/build_context.py
├── acceptance.yml    # executable definition of done
├── evidence/
│   └── trace.jsonl   # append-only log: role, model, action, command, result
├── review.md         # the independent reviewer's findings
└── handoff.md        # the required closing record
```

One builder agent, one independent reviewer agent (different model family),
isolated git worktrees, executable checks, structured handoffs.

---

## What's inside `_keel/`

```
_keel/
├── BOOTSTRAP.md             # the protocol the agent follows (don't edit lightly)
├── README.md                # this file
├── LICENSE                  # MIT
├── requirements.txt         # pyyaml, jsonschema
├── spec_model.schema.json   # validates the structured extraction in Step 2
├── spec_model.yml           # (generated) the extracted model
├── BOOTSTRAP_REPORT.md      # (generated) bootstrap output + assumptions
├── templates/               # all 14 templates (filled in during bootstrap)
├── scripts/
│   ├── keel/                # the keel Python package (importable API)
│   │   ├── api.py           # KeelRepo — the stateless integration surface
│   │   ├── operations.py    # core logic (single implementation)
│   │   ├── helpers.py       # low-level helpers
│   │   ├── errors.py        # KeelError hierarchy
│   │   └── README.md        # API reference
│   └── agent/               # thin CLI wrappers over keel.api
├── skills/                  # 7 ready-to-use agent prompts (/dev-plan-task, etc.)
├── tests/                   # KEEL's own unit tests (pytest _keel/tests/)
└── examples/
    └── url-shortener/       # worked end-to-end example to calibrate against
```

---

## Source-of-truth hierarchy

The bootstrap generates a layered governance system. From most authoritative to
least:

| Layer | File | Mutability |
|---|---|---|
| Founding commitments | `PRINCIPLES.md` | Near-immutable (amend via heavyweight process) |
| Design truth | `CORE.md` | Mutable via `DECISIONS.md`, accountable to PRINCIPLES |
| Decision log | `DECISIONS.md` | Append-only; each entry cites principles checked |
| Component registry | `COMPONENTS.md` | Reflects current architecture |
| Implementation truth | `STATUS.md` | Reflects what's actually built |
| Historical record | `CHANGELOG.md` | Append-only, non-normative |

A mismatch between code and CORE is a defect to investigate. A mismatch between
CORE and PRINCIPLES is also a defect — the PRINCIPLES layer is what prevents slow
drift from the project's founding intent.

---

## Renaming the OS

This template uses `KEEL` as a placeholder codename. If you want to rename it,
change it in exactly one place — `BOOTSTRAP.md`'s title line — and the generated
scaffold follows. Do not maintain two naming schemes.

The canonical filenames (`PRINCIPLES.md`, `CORE.md`, `AGENTS.md`, etc.) can also
be renamed if you have a strong preference, but the templates and bootstrap
protocol will need matching edits. Default: keep them as-is — agents have
training-data familiarity with `AGENTS.md` in particular.

---

## Recommended `.gitignore` additions

Add these entries to your project's `.gitignore`:

```
.worktrees/
__pycache__/
*.pyc
.pytest_cache/
```

**Do commit:** `_keel/spec_model.yml` and `_keel/BOOTSTRAP_REPORT.md`. They are
generated, but they are part of the project's truth — reviewers should be able
to see them in PRs.

## Python dependencies (for the scripts)

The agent scripts in `_keel/scripts/agent/` require:

```
pip install pyyaml jsonschema
```

Python 3.11+ is recommended.

## Testing KEEL itself

KEEL ships with unit tests for the agent scripts and the Python API:

```bash
pip install pytest pyyaml jsonschema
pytest _keel/tests/
```

The tests run with or without the package installed. For programmatic use of
the API from other tools, install it editable:

```bash
pip install -e _keel        # exposes `import keel` + the unified `keel` CLI
```

See `_keel/scripts/keel/README.md` for the full API reference.

## MCP server

KEEL ships an MCP server that exposes tasks, skills, and governance as tools to
any MCP-aware agent (Claude Code, Claude Desktop, Cursor, custom clients):

```bash
pip install -e '_keel[mcp]'
keel-mcp --root /path/to/repo
```

It's a thin, stateless wrapper over the Python API — same gates, same source of
truth. See `_keel/scripts/keel/MCP.md` for wiring into Claude Desktop / Code and
the full tool catalog.

## Skills & agent discovery (Zed, Claude Code, Codex, Gemini)

Skills are task-scoped workflows. They live **canonically** in `_keel/skills/<id>/`
(so they travel with the OS and update cleanly), and are **published** for
agent discovery to `.agents/skills/<id>/` — the portable Agent Skills layout that
Zed's native agent, Claude Code, Codex, and Gemini all read. One source of truth,
two surfaces:

```bash
keel skills sync     # regenerate .agents/skills/ + .agents/SKILLS.md from _keel/skills/
keel skills lint     # validate frontmatter, names, manual-only safeguards, and drift
```

`keel init` runs the sync for you, so a fresh project is agent-discoverable
immediately. In Zed, open the repo and the agent sees the skill catalog and
selects the one whose **description** matches the task; `AGENTS.md` is the
always-on contract that tells it to orient first and load only the relevant
skill. The `.agents/` tree is a generated build artifact (each mirror carries a
DO-NOT-EDIT banner) — edit the canonical skill in `_keel/skills/`, then re-sync.

A skill may set two optional frontmatter flags: `manual_only: true` (never
auto-selected; exported with the cross-tool `disable-model-invocation: true`
safeguard — used by `dev-release`), and `export: false` (kept out of `.agents/`,
e.g. a local demo).

## Worked example

See `_keel/examples/url-shortener/` for a complete sample bootstrap output —
a small but non-trivial project (URL shortener with storage, encoder, API,
analytics) showing what `PRINCIPLES.md`, `CORE.md`, `COMPONENTS.md`, a module
card, a task brief, and a `BOOTSTRAP_REPORT.md` look like when bootstrap runs
correctly. Use it for calibration: if your own bootstrap output is materially
thinner than this, push back on the agent or improve your `PROJECT_SPEC.md`.

---

## What you get out of it

A repo where any agent — on any day, with no memory of prior sessions — can be
pointed at a task folder and produce correct, scoped, test-backed, reviewable work
that updates the project's shared state honestly.

---

## First-run checklist

```
[ ] Copy _keel/ into the repo root.
[ ] cp _keel/templates/PROJECT_SPEC.template.md ./PROJECT_SPEC.md and fill it in
    (subsystems, invariants, failure modes are load-bearing).
[ ] New agent session: "Read _keel/BOOTSTRAP.md and follow it. Spec is
    PROJECT_SPEC.md."
[ ] Answer the agent's blocking questions; let it generate the scaffold.
[ ] Read _keel/BOOTSTRAP_REPORT.md end to end. Verify its extracted model matches
    intent.
[ ] Review PRINCIPLES.md FIRST — every principle should be falsifiable and feel
    like something you'd be willing to defend a year from now. Edit now if not.
[ ] Correct CORE.md / COMPONENTS.md / module cards / DECISIONS.md against the
    principles you just confirmed.
[ ] Confirm `just check` runs (even if most scenarios xfail).
[ ] Pick the recommended first task. Create its packet. Build context. Implement
    in a worktree. Independent review. Gate. Merge. Handoff.
```
