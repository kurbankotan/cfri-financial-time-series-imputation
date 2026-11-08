"""Verify every canonical file listed in the root SHA256SUMS.txt manifest."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SHA256SUMS.txt"
RECORD = re.compile(r"^([0-9a-f]{64})  (.+)$")


def main() -> None:
    names: set[str] = set()
    for line_no, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        match = RECORD.fullmatch(line)
        if match is None:
            raise SystemExit(f"Malformed manifest line {line_no}")
        expected, name = match.groups()
        path = ROOT / name
        if name in names or not path.is_file() or path.resolve().is_relative_to(ROOT.resolve()) is False:
            raise SystemExit(f"Duplicate, absent, or escaping path: {name}")
        names.add(name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"SHA-256 mismatch: {name}")
    print(f"Verified {len(names)} canonical file hashes")


if __name__ == "__main__":
    main()
