#!/bin/bash
# build.sh — build the standalone keel executable with PyInstaller
#
# Usage (from the _keel/ directory or a parent):
#   cd _keel/ && ./build.sh
#   # or from the repo root:
#   ./_keel/build.sh
#
# Output: _keel/dist/keel  (or dist/keel.exe on Windows)
# After building, copy that single file anywhere — no Python needed.

set -e
cd "$(dirname "$0")"   # always run from _keel/

echo "=== KEEL — PyInstaller build ==="
echo "Working directory: $(pwd)"
echo

# ── 1. check prerequisites ────────────────────────────────────────────────────
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

if ! python3 -c "import jsonschema, yaml" 2>/dev/null; then
    echo "Runtime deps not found. Installing..."
    pip install -r requirements.txt
fi

# ── 2. rebuild the bundled template zip (so the exe ships the latest templates) ──
echo "→ rebuilding bundled template zip..."
python3 scripts/build_template_zip.py

# ── 3. clean previous build artifacts ────────────────────────────────────────
echo "→ cleaning previous build..."
rm -rf build/ dist/

# ── 4. run PyInstaller ────────────────────────────────────────────────────────
echo "→ running PyInstaller..."
pyinstaller keel.spec

# ── 5. report ─────────────────────────────────────────────────────────────────
echo
if [ -f "dist/keel" ] || [ -f "dist/keel.exe" ]; then
    echo "✅ Build complete!"
    ls -lh dist/keel* 2>/dev/null || ls -lh dist/keel.exe 2>/dev/null
    echo
    echo "Test it:"
    echo "  ./dist/keel --version"
    echo "  ./dist/keel --help"
    echo "  ./dist/keel guide"
    echo "  ./dist/keel init ./myproject"
    echo
    echo "To distribute: copy dist/keel (or dist/keel.exe) to any machine."
    echo "No Python installation required on the target."
else
    echo "❌ Build failed — check output above."
    exit 1
fi
