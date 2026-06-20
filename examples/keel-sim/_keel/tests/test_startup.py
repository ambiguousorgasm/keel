"""Test the top-level start.py entry script."""
from __future__ import annotations

import py_compile
from pathlib import Path

START = Path(__file__).resolve().parents[1] / "start.py"


def test_start_script_exists():
    assert START.is_file(), "start.py must be at the KEEL root"


def test_start_script_compiles():
    py_compile.compile(str(START), doraise=True)


def test_start_script_references_menu():
    text = START.read_text()
    # It must reuse the unified CLI (not reimplement it) and be no-install capable.
    assert "from keel.main import main" in text
    assert "scripts" in text.lower()
