# KEEL — Complete Package

This archive contains the full KEEL system plus a worked example and an
integration brief. KEEL is a **repo-native agent development operating system**:
a project template + tooling that keeps AI coding agents on-task by making the
repository the single source of truth.

## What's in here

```
keel-complete/
├── _keel/                         ← THE PRODUCT: the KEEL operating system
│   ├── start.py                   ← run this first:  python _keel/start.py
│   ├── README.md                  ← the full human guide
│   ├── BOOTSTRAP.md               ← the agent-facing bootstrap protocol
│   ├── scripts/keel/              ← the `keel` Python package + CLI + MCP server
│   ├── skills/                    ← builtin skills (dev-* workflow + explain-clear)
│   ├── templates/                 ← the document templates bootstrap fills
│   └── examples/url-shortener/    ← a tiny worked bootstrap example
│
├── examples/
│   └── keel-sim/                  ← a REAL KEEL project: the gate simulator that
│                                    validates KEEL's own design decisions. Built
│                                    as a governed KEEL project (its own PRINCIPLES,
│                                    CORE, tasks). See its RESULTS.md.
│
└── docs/
    └── portfolio-tool-design-brief.md  ← spec/prompt for building a separate
                                           multi-project portfolio manager that
                                           reads KEEL projects.
```

## The one file you need

```bash
./run.sh          # first run: sets up everything, then starts KEEL
./run.sh          # every run after: skips straight to KEEL
./run.sh --help   # pass any keel arguments through
./run.sh guide
./run.sh init ./myproject
```

`run.sh` is the go-to launcher. It:
1. Creates a virtual environment (`.venv/`) if one doesn't exist
2. Installs KEEL and its dependencies once, then never reinstalls unless something is missing
3. Activates the venv
4. Runs `_keel/start.py`

Make it executable the first time:
```bash
chmod +x run.sh
./run.sh
```

---

## Requirements

KEEL needs **Python 3.11+** and two small packages: `jsonschema` and `pyyaml`.
If you run it without them, the entry scripts tell you exactly how to install
them. To do it up front:

```bash
pip install -r _keel/requirements.txt    # jsonschema + pyyaml
# or just install KEEL, which pulls them in automatically:
pip install -e _keel
```

## Get started in 30 seconds

**Option A — run directly (zero install):**
```bash
cd keel-complete/_keel
python main.py          # interactive menu
python main.py --help   # full command list
python main.py guide    # rules & usage
```

**Option B — use the interactive startup script:**
```bash
cd keel-complete
python _keel/start.py
```

**Option C — install the `keel` command globally:**
```bash
pip install -e _keel
keel                    # interactive menu, from anywhere
```

## The CLI at a glance

```
keel                    interactive menu (in a terminal)
keel --help             full command list      (keel <cmd> --help for each)
keel --version          show the version
keel init [path]        create a new project    (--spec FILE to seed from a spec)
keel guide              rules & usage overview
keel info               orientation summary of the current project
keel doctor             check the environment is wired correctly
keel task …             create / list / context / verify task packets
keel skills …           list / show / search / new skills
keel code-map           refresh docs/code-map/
keel mcp                run the MCP server (needs:  pip install -e '_keel[mcp]')
```

## The core idea, in one paragraph

The **repository is the source of truth**, not the agent. Work happens as bounded
**task packets**: an agent takes one, works inside a declared scope, proves it
against a **gate** (scope + scenario + independent review), and hands off — never
"continuing the project" open-loop. Durable truth lives in files, in a fixed order
of authority: `PRINCIPLES.md → CORE.md → DECISIONS.md / COMPONENTS.md → STATUS.md
→ CHANGELOG.md`. Everything else (the API, the CLI, the MCP server, skills) is a
thin, stateless layer over that.

## Three ways to drive KEEL

- **CLI** — the `keel` command (or `python _keel/start.py` with no install).
- **Python API** — `from keel import KeelRepo` (see `_keel/scripts/keel/README.md`).
- **MCP server** — exposes tasks/skills/governance as tools to MCP-aware agents
  like Claude Code (see `_keel/scripts/keel/MCP.md`).

All three are stateless wrappers over the same repo-as-truth core, with the same
gates. None is a shortcut around the others.

## Running the tests

```bash
pip install -e '_keel[mcp]' pytest
pytest _keel/tests/                 # the KEEL system tests
pytest examples/keel-sim/tests/     # the simulator's tests
```

## A note on the example (`examples/keel-sim`)

The gate simulator is both a working tool and a proof: it runs synthetic agents
with known biases against KEEL's gate and measures whether the gate behaves as
designed. Its `RESULTS.md` shows, for instance, that a reviewer who reads the raw
diff is immune to a builder's rationalization while one who reads the builder's
*explanation* is not — validating KEEL's "review the diff, not the story" rule.
It's mechanism validation, not a claim about real agents — see its `PRINCIPLES.md`.
# keel
