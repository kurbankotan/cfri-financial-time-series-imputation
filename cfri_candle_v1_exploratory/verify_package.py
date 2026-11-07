#!/usr/bin/env python3
"""Verify the extracted public CFRI candle directory with standard Python."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    listed = {}
    for line in (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if name in listed or len(digest) != 64:
            raise RuntimeError(f"duplicate or malformed manifest entry: {name}")
        listed[name] = digest
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
    if set(listed) != actual - {"SHA256SUMS.txt"}:
        raise RuntimeError("missing or extra files in package directory")
    for name, digest in listed.items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise RuntimeError(f"file SHA mismatch: {name}")
    with zipfile.ZipFile(ROOT / "results" / "CFRI_candle_v1_results_full.zip") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("full results ZIP CRC failure")
        manifest = json.loads(archive.read("package_manifest.json"))["files"]
        if set(manifest) != set(archive.namelist()) - {"package_manifest.json"}:
            raise RuntimeError("full results member list mismatch")
        for name, info in manifest.items():
            payload = archive.read(name)
            if len(payload) != info["bytes"] or sha(payload) != info["sha256"]:
                raise RuntimeError(f"full results SHA mismatch: {name}")
        condition_names = [n for n in manifest if n.startswith("candle_feature/") and
                           n.endswith(".json") and not n.endswith(".done.json") and
                           n != "candle_feature/run_manifest.json"]
        if len(condition_names) != 816:
            raise RuntimeError("full results missing feature conditions")
    source_manifest = json.loads((ROOT / "code" / "CANDLE_SOURCE_SHA256.json").read_text())
    for name, digest in source_manifest.items():
        if sha((ROOT / "code" / name).read_bytes()) != digest:
            raise RuntimeError(f"source code changed: {name}")
    for path in ROOT.rglob("*"):
        if path.is_file() and any(s in path.as_posix().lower() for s in
                                  ("raw_do_not_publish", "raw_cache", "private_data")):
            raise RuntimeError(f"private raw-data path found: {path}")
    print(f"Verified {len(listed)} public files, {len(condition_names)} condition shards, no raw tables")


if __name__ == "__main__":
    main()
