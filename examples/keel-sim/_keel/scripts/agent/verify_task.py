#!/usr/bin/env python3
"""Path-run shim → unified `keel` CLI (task verify). No-install convenience; prefer
the installed `keel task verify` command when available."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from keel.main import main  # noqa: E402

if __name__ == "__main__":
    sys.argv = ["keel", *"task verify".split(), *sys.argv[1:]]
    raise SystemExit(main())
