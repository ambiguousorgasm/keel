#!/bin/bash
# run.sh — KEEL startup and launcher
#
# First run: creates the venv, installs dependencies, then starts KEEL.
# Every run after: skips straight to starting KEEL (nothing reinstalled).
# Use this as your go-to for running KEEL at any time.
#
# Usage:
#   ./run.sh                  interactive menu
#   ./run.sh --help           full command list
#   ./run.sh guide            rules & usage
#   ./run.sh init ./myproject create a new project
#   ./run.sh doctor           check environment health

set -e
cd "$(dirname "$0")"

VENV=".venv"
REQUIREMENTS="_keel/requirements.txt"
MARKER="$VENV/.keel_installed"   # touched after a successful install

# ── 1. create the venv if it doesn't exist ───────────────────────────────────
if [ ! -d "$VENV" ]; then
    echo "Setting up KEEL for the first time..."
    echo "→ Creating virtual environment..."
    python3 -m venv "$VENV"
fi

# ── 2. activate ──────────────────────────────────────────────────────────────
source "$VENV/bin/activate"

# ── 3. install dependencies only if not already satisfied ────────────────────
if [ ! -f "$MARKER" ]; then
    echo "→ Installing dependencies (one-time only)..."
    pip install -q -e _keel
    touch "$MARKER"
    echo "→ Done. Starting KEEL..."
    echo ""
else
    # Quick check: if someone deletes a package manually, reinstall.
    if ! python -c "import jsonschema, yaml" 2>/dev/null; then
        echo "→ Dependencies missing — reinstalling..."
        pip install -q -e _keel
        touch "$MARKER"
        echo ""
    fi
fi

# ── 4. run ───────────────────────────────────────────────────────────────────
python _keel/start.py "$@"
