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


def test_root_main_py_exists():
    root_main = Path(__file__).resolve().parents[1] / "main.py"
    assert root_main.is_file(), "_keel/main.py must exist as the direct-run entry"


def test_root_main_py_compiles():
    import py_compile
    root_main = Path(__file__).resolve().parents[1] / "main.py"
    py_compile.compile(str(root_main), doraise=True)


def test_root_main_delegates_to_keel_main():
    root_main = (Path(__file__).resolve().parents[1] / "main.py").read_text()
    assert "from keel.main import main" in root_main
    assert "_find_scripts" in root_main  # path-resolution helper present


def test_main_py_has_dependency_check():
    text = (Path(__file__).resolve().parents[1] / "main.py").read_text()
    assert "_missing_deps" in text
    assert "requirements.txt" in text
    # the check must run before importing the package
    assert text.index("_missing_deps()") < text.index("from keel.main import main")


def test_start_py_has_dependency_check():
    text = (Path(__file__).resolve().parents[1] / "start.py").read_text()
    assert "_missing_deps" in text
    assert "requirements.txt" in text
