"""Reference CSV cleaner for the example-csv-clean skill.

Intentionally dependency-light. This is illustrative, not production-grade.
"""
from __future__ import annotations

import csv
import sys


def clean(rows: list[list[str]]) -> list[list[str]]:
    if not rows:
        return rows
    header, *body = rows
    header = [h.strip().lower().replace(" ", "_") for h in header]
    body = [r for r in body if any(cell.strip() for cell in r)]
    return [header, *body]


if __name__ == "__main__":
    reader = csv.reader(sys.stdin)
    writer = csv.writer(sys.stdout)
    writer.writerows(clean(list(reader)))
