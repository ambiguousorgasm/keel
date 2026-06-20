#!/usr/bin/env python3
"""KEEL — runnable entry point.

    python main.py [args]

Works with no installation. Equivalent to running `keel [args]` after
`pip install -e .`. Can be placed anywhere as long as it's in the same
directory as _keel/ (or IS inside _keel/).

Examples:
    python main.py                  # interactive menu
    python main.py --help           # full command list
    python main.py --version        # show version
    python main.py guide            # rules & usage
    python main.py init ./myproject # create a new project
    python main.py doctor           # check environment health
    python main.py info             # current project summary
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── resolve the `keel` package location ──────────────────────────────────────
#
# Support three layouts:
#   A) This file is at _keel/main.py     → scripts/ is a sibling
#   B) This file is at _keel/scripts/keel/main.py  → already inside the package
#      (running the internal file directly — unusual but handle it)
#   C) This file is next to _keel/       → scripts/ is at _keel/scripts/

_HERE = Path(__file__).resolve().parent

def _find_scripts() -> Path | None:
    # Case A: _keel/main.py, scripts/ is next door
    if (_HERE / "scripts" / "keel" / "main.py").is_file():
        return _HERE / "scripts"
    # Case B: already inside scripts/keel/ — parent's parent is scripts
    if (_HERE / "__init__.py").is_file():
        return _HERE.parent
    # Case C: next to _keel/
    if (_HERE / "_keel" / "scripts" / "keel" / "main.py").is_file():
        return _HERE / "_keel" / "scripts"
    return None

_scripts = _find_scripts()
if _scripts is None:
    print(
        "ERROR: could not locate the KEEL package.\n"
        "Run this script from inside the _keel/ directory or a project root.\n"
        "Or install: pip install -e _keel",
        file=sys.stderr,
    )
    sys.exit(1)

if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))

# ── check runtime dependencies before importing the package ──────────────────


def _missing_deps() -> list[str]:
    import importlib.util
    missing = []
    if importlib.util.find_spec("yaml") is None:
        missing.append("pyyaml")
    if importlib.util.find_spec("jsonschema") is None:
        missing.append("jsonschema")
    return missing


def _dep_message(missing: list[str]) -> str:
    pkgs = " ".join(missing)
    return (
        "KEEL needs Python packages that aren't installed: "
        + ", ".join(missing)
        + "\n\nInstall them with either:\n"
        f"    pip install {pkgs}\n"
        "  or, from the _keel/ directory:\n"
        "    pip install -r requirements.txt\n\n"
        "If you get an 'externally-managed-environment' error, try:\n"
        f"    pip install --user {pkgs}\n\n"
        "Or install KEEL itself (pulls deps automatically), from _keel/:\n"
        "    pip install -e ."
    )


_missing = _missing_deps()
if _missing:
    print(_dep_message(_missing), file=sys.stderr)
    sys.exit(1)

# ── delegate to the real CLI ──────────────────────────────────────────────────

from keel.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
