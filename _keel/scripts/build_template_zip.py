#!/usr/bin/env python3
"""Rebuild the bundled template zip from the live _keel/ tree.

Run this before packaging or release WHENEVER the _keel/ template changes
(templates, skills, scripts, BOOTSTRAP.md, etc.). `keel init` extracts this zip
to scaffold new projects, so a stale zip means new projects get stale KEEL.

    python _keel/scripts/build_template_zip.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from keel.scaffold import build_template_archive  # noqa: E402


def main() -> int:
    keel_root = Path(__file__).resolve().parents[1]  # _keel/
    dest = keel_root / "scripts" / "keel" / "assets" / "keel_template.zip"
    n = build_template_archive(keel_root, dest)
    print(f"✅ rebuilt {dest.relative_to(keel_root.parent)} ({n} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
