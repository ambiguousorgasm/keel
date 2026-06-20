#!/usr/bin/env python3
"""KEEL — start here.

    python start.py

This is the friendly entry point. It works with NO installation: it makes the
`keel` tooling importable in-process and launches the interactive menu (create a
project, see the guide). It can also optionally install the `keel` command so you
can run `keel` from anywhere afterward.

You never need this script again once `keel` is installed — but it's a safe,
dependency-free way to get going from a fresh copy of KEEL.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # the _keel/ directory
SCRIPTS = HERE / "scripts"                       # where the `keel` package lives


def _python_ok() -> bool:
    return sys.version_info >= (3, 11)


def _keel_already_installed() -> bool:
    """True if `keel` is importable as a real install (before we touch sys.path)."""
    try:
        import importlib.util
        return importlib.util.find_spec("keel") is not None
    except Exception:
        return False


def _missing_deps() -> list[str]:
    import importlib.util
    missing = []
    if importlib.util.find_spec("yaml") is None:
        missing.append("pyyaml")
    if importlib.util.find_spec("jsonschema") is None:
        missing.append("jsonschema")
    return missing


def _offer_install() -> None:
    try:
        ans = input(
            "Install the `keel` command so you can run it from anywhere? [y/N]: "
        ).strip().lower()
    except EOFError:
        ans = ""
    if not ans.startswith("y"):
        print("Skipping install — continuing in no-install mode.\n")
        return
    print("Installing (pip install -e .) …")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(HERE)], check=True
        )
        print("✅ Installed. You can now run `keel` directly from any project.\n")
    except subprocess.CalledProcessError:
        print("⚠ Install failed — continuing in no-install mode. To install later:")
        print(f"    pip install -e {HERE}\n")


def main() -> int:
    print("=" * 60)
    print("  KEEL — repo-native agent development operating system")
    print("=" * 60)

    if not _python_ok():
        print(
            f"⚠ KEEL targets Python 3.11+. You have {sys.version.split()[0]}.\n"
            "  It may still work, but consider upgrading.\n"
        )

    installed = _keel_already_installed()

    # Make the package importable even without an install (KEEL supports this).
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))

    # If not installed and we're in a terminal, offer the convenience install.
    if not installed and sys.stdin.isatty():
        _offer_install()

    # Verify runtime dependencies are present before importing the package.
    missing = _missing_deps()
    if missing:
        pkgs = " ".join(missing)
        print(
            "KEEL needs Python packages that aren't installed: "
            + ", ".join(missing)
            + "\n\nInstall them with either:\n"
            f"    pip install {pkgs}\n"
            "  or, from this _keel/ directory:\n"
            "    pip install -r requirements.txt\n\n"
            "If you get an 'externally-managed-environment' error, try:\n"
            f"    pip install --user {pkgs}\n",
            file=sys.stderr,
        )
        return 1

    try:
        from keel.main import main as keel_main
    except Exception as e:  # pragma: no cover
        print(f"ERROR: could not load KEEL ({e}).")
        print(f"Run this from inside the KEEL directory: {HERE}")
        return 1

    # Reuse the unified CLI's bare-invocation behavior: interactive menu in a
    # terminal, help otherwise.
    sys.argv = ["keel"]
    return keel_main()


if __name__ == "__main__":
    raise SystemExit(main())
