"""Audit every paired candle checkpoint and export an exploratory result ZIP."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import cfri_core as C
import holdout_data as D
import holdout_run as R
import holdout_saits as S
import reference_stage as REF
import candle_runner as CR


OUTPUT_ZIP = "CFRI_candle_v1_results.zip"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def mean(rows: list[float]) -> float:
    if not rows or not all(math.isfinite(v) for v in rows):
        raise RuntimeError("nonfinite or empty metric")
    return float(np.mean(rows))


def _score_check(data: dict, key: tuple) -> None:
    if (data.get("ticker"), data.get("mask_type"), data.get("block_length"),
        data.get("rate"), data.get("seed")) != key:
        raise RuntimeError(f"condition identity differs: {key}")
    if data.get("fold") != D.FOLD_TAG or set(data.get("scores", {})) != set(CR.METHODS):
        raise RuntimeError(f"unexpected fold or methods: {key}")
    if set(data.get("ohlc_violation_share", {})) != set(CR.METHODS):
        raise RuntimeError(f"missing OHLC diagnostics: {key}")
    for method in CR.METHODS:
        scores = data["scores"][method]
        if set(scores) != set(C.FEATURES):
            raise RuntimeError(f"unexpected fields: {key}/{method}")
        if float(data["ohlc_violation_share"][method]) > 1e-9:
            raise RuntimeError(f"OHLC violation: {key}/{method}")
        for feature in C.FEATURES:
            values = scores[feature]
            if (len(values) != 3 or not isinstance(values[2], int) or values[2] <= 0 or
                not all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0
                        for v in values[:2])):
                raise RuntimeError(f"invalid score: {key}/{method}/{feature}")


def load(root: Path) -> tuple[dict, list[dict], list[dict], list[Path], Path]:
    ref = CR.reference_root(root)
    targets, peers, cpu_manifest, saits_manifest = REF.verify_feature_reference(ref)
    m = CR.manifest(root, ref, targets, peers)
    keys = CR.expected_keys(targets)
    if len(keys) != m["expected_conditions"]:
        raise RuntimeError("expected condition count changed")
    expected_files = {CR.condition_path(root, key).name for key in keys}
    found_files = {p.name for p in (root / CR.OUT_DIR).glob("*.json")
                   if p.name != "run_manifest.json" and not p.name.endswith(".done.json")}
    if expected_files != found_files:
        raise RuntimeError(f"candle results incomplete: {len(expected_files-found_files)} missing, "
                           f"{len(found_files-expected_files)} extra")
    condition_rows, feature_rows, shard_paths = [], [], []
    for key in keys:
        cpu, saits, cpu_sha, saits_sha = CR.verify_reference_condition(ref, key, cpu_manifest, saits_manifest)
        path = CR.condition_path(root, key)
        fp = CR.fingerprint(m, key, cpu_sha, saits_sha)
        if not CR.verified_condition(path, fp, key):
            raise RuntimeError(f"candle checkpoint digest/fingerprint invalid: {path}")
        data = D.read_json(path)
        _score_check(data, key)
        if data["mask_sha256"] != cpu["mask_sha256"] or data["masked_cells"] != cpu["masked_cells"]:
            raise RuntimeError(f"mask mismatch with original methods: {key}")
        for method in CR.METHODS:
            for col, field in enumerate(C.FEATURES):
                if data["scores"][method][field][2] != cpu["scores"]["cfri_joint"][field][2]:
                    raise RuntimeError(f"hidden score count differs: {key}/{method}/{field}")
        CR._same_score(data["scores"]["cfri_joint"], cpu["scores"]["cfri_joint"], str(key))
        CR._same_score(data["scores"]["saits_joint"], saits["scores"]["saits_joint"], str(key))
        shard_paths.extend((path, path.with_name(path.name + ".done.json")))
        ticker, mask_type, block, rate, seed = key
        for method in CR.METHODS:
            by_field = data["scores"][method]
            p = mean([float(by_field[field][0]) for field in C.FEATURES[:4]])
            v = float(by_field["volume"][0])
            condition_rows.append({"ticker": ticker, "mask_type": mask_type,
                                   "block_length": block, "rate": rate, "seed": seed,
                                   "method": method, "nrmse": mean(
                                       [float(by_field[field][0]) for field in C.FEATURES]),
                                   "price_nrmse": p, "volume_nrmse": v})
            for field in C.FEATURES:
                x = by_field[field]
                feature_rows.append({"ticker": ticker, "mask_type": mask_type,
                                     "block_length": block, "rate": rate, "seed": seed,
                                     "method": method, "feature": field,
                                     "nrmse": float(x[0]), "nmae": float(x[1]),
                                     "hidden_cells": int(x[2])})
    return m, condition_rows, feature_rows, shard_paths, ref


def _group_mean(rows: list[dict], grouping: tuple[str, ...], measures: tuple[str, ...]) -> list[dict]:
    grouped: dict[tuple, list[dict]] = {}
    for row in rows:
        grouped.setdefault(tuple(row[k] for k in grouping), []).append(row)
    return [{**dict(zip(grouping, key)), **{metric: mean([float(r[metric]) for r in group])
                                           for metric in measures}}
            for key, group in sorted(grouped.items())]


def report(m: dict, condition: list[dict], feature: list[dict]) -> tuple[dict, list[dict], list[dict], str]:
    metrics = ("nrmse", "price_nrmse", "volume_nrmse")
    assets = _group_mean(condition, ("ticker", "method"), metrics)
    blocks_by_asset = _group_mean(condition, ("block_length", "ticker", "method"), metrics)
    blocks = _group_mean(blocks_by_asset, ("block_length", "method"), metrics)
    overall = _group_mean(assets, ("method",), metrics)
    overall_by_method = {r["method"]: r for r in overall}
    by_asset = {(r["ticker"], r["method"]): r for r in assets}
    tickers = sorted(set(r["ticker"] for r in assets))
    paired = {}
    for candidate in ("candle_direct", "candle_half"):
        paired[candidate] = {}
        for comparator in ("cfri_joint", "saits_joint"):
            paired[candidate][comparator] = {
                metric: {"asset_wins": sum(by_asset[(ticker, candidate)][metric] < by_asset[(ticker, comparator)][metric] - 1e-12
                                            for ticker in tickers),
                         "asset_ties": sum(math.isclose(by_asset[(ticker, candidate)][metric],
                                                         by_asset[(ticker, comparator)][metric],
                                                         rel_tol=0, abs_tol=1e-12)
                                           for ticker in tickers),
                         "asset_count": len(tickers),
                         "mean_difference": overall_by_method[candidate][metric] - overall_by_method[comparator][metric]}
                for metric in metrics}
    result = {
        "study": m["study"], "classification": m["settings"]["classification"],
        "condition_count": len(condition) // len(CR.METHODS), "target_count": len(tickers),
        "method_macro_nrmse": overall_by_method, "paired": paired,
        "methods": list(CR.METHODS), "model_fit_count": None,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    lines = ["# CFRI candle geometry: exploratory paired replay", "",
             "This method was designed after the 2026 held-out results were seen. These are descriptive,",
             "exploratory comparisons on the same 2026 targets and feature-wise masks; they are not",
             "a new confirmatory holdout. The feature mask benchmark has no whole-row outage test.", "",
             f"Verified {result['condition_count']} paired conditions across {len(tickers)} ETFs. ",
             "Each condition uses the same target frame, feature mask, original CFRI, and SAITS V2 score.",
             "All new price predictions use the original joint OHLC projection; observed cells stay fixed.", "",
             "## Equal-ETF macro NRMSE", "",
             "| Method | All five fields | OHLC only | Volume |", "|---|---:|---:|---:|" ]
    for method in CR.METHODS:
        x = overall_by_method[method]
        lines.append(f"| {method} | {x['nrmse']:.6f} | {x['price_nrmse']:.6f} | {x['volume_nrmse']:.6f} |")
    lines.extend(["", "## Paired wins by ETF", "",
                  "| Candidate | Comparator | All fields | OHLC only | Volume |", "|---|---|---:|---:|---:|"])
    for candidate in ("candle_direct", "candle_half"):
        for comparator in ("cfri_joint", "saits_joint"):
            x = paired[candidate][comparator]
            lines.append(f"| {candidate} | {comparator} | "
                         + " | ".join(f"{x[k]['asset_wins']}/{len(tickers)}" for k in metrics) + " |")
    lines.extend(["", "## Gap length (equal ETF average)", "",
                  "| Block | Method | All fields | OHLC only |", "|---:|---|---:|---:|"])
    for x in blocks:
        lines.append(f"| {x['block_length']} | {x['method']} | {x['nrmse']:.6f} | {x['price_nrmse']:.6f} |")
    lines.extend(["", "No method or blend weight was selected using these test scores. The direct",
                  "candidate and a fixed 50% log-price blend are both reported. All five feature",
                  "scores, per-condition data and SHA sidecars are included in the ZIP.", ""])
    return result, assets, blocks, "\n".join(lines)


def _source_archive(path: Path) -> None:
    here = Path(__file__).resolve().parent
    selected = [p for p in here.rglob("*") if p.is_file() and
                (p.suffix == ".py" or p.name in ("SOURCE_SHA256.json", "PROTOCOL.md",
                                                 "requirements-colab.txt", "README.md")) and
                "__pycache__" not in p.parts]
    tmp = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(selected):
            archive.write(p, p.relative_to(here).as_posix())
    os.replace(tmp, path)


def _zip_results(root: Path, ref: Path, shards: list[Path], report_files: list[Path]) -> Path:
    source_archive = root / "candle_source_snapshot.zip"
    _source_archive(source_archive)
    entries: list[tuple[Path, str]] = []
    for p in report_files + [root / "reference_choice.json", root / CR.OUT_DIR / "run_manifest.json",
                             root / "candle_source_bundle.zip", root / "candle_source_receipt.json",
                             source_archive]:
        entries.append((p, p.relative_to(root).as_posix()))
    for p in shards:
        entries.append((p, p.relative_to(root).as_posix()))
    ref_files = [ref / D.RECEIPT, ref / "freeze_receipt.json", ref / "frozen_source_bundle.zip",
                 ref / R.OUT_DIR / "run_manifest.json", ref / S.OUT_DIR / "run_manifest.json"]
    for p in ref_files:
        entries.append((p, "reference_evidence/" + p.relative_to(ref).as_posix()))
    manifest = {name: {"sha256": CR.sha(path.read_bytes()), "bytes": path.stat().st_size}
                for path, name in entries}
    manifest_payload = CR.blob({"files": manifest, "raw_prices_included": False,
                                "classification": CR.SETTINGS["classification"]})
    out = root / OUTPUT_ZIP
    tmp = out.with_name(out.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        archive.writestr("package_manifest.json", manifest_payload)
        for path, name in entries:
            archive.write(path, name)
    with zipfile.ZipFile(tmp) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(manifest) | {"package_manifest.json"}:
            raise RuntimeError("output ZIP failed integrity check")
        for name, rec in manifest.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != rec["sha256"]:
                raise RuntimeError(f"output ZIP SHA mismatch: {name}")
    os.replace(tmp, out)
    return out


def analyze(root: Path) -> Path:
    root = Path(root)
    m, conditions, features, shards, ref = load(root)
    result, assets, blocks, markdown = report(m, conditions, features)
    result["model_fit_count"] = sum(bool(D.read_json(p).get("candle_model_fit"))
                                    for p in shards if p.name.endswith(".json") and
                                    not p.name.endswith(".done.json"))
    cfields = ["ticker", "mask_type", "block_length", "rate", "seed", "method",
               "nrmse", "price_nrmse", "volume_nrmse"]
    ffields = ["ticker", "mask_type", "block_length", "rate", "seed", "method", "feature",
               "nrmse", "nmae", "hidden_cells"]
    afields = ["ticker", "method", "nrmse", "price_nrmse", "volume_nrmse"]
    bfields = ["block_length", "method", "nrmse", "price_nrmse", "volume_nrmse"]
    files = [root / "candle_condition_scores.csv", root / "candle_feature_scores.csv",
             root / "candle_asset_scores.csv", root / "candle_block_scores.csv",
             root / "candle_results.json", root / "candle_report.md"]
    for path, rows, fields in zip(files[:4], (conditions, features, assets, blocks),
                                  (cfields, ffields, afields, bfields)):
        write_csv(path, rows, fields)
    D.atomic(files[4], CR.blob(result))
    D.atomic(files[5], markdown.encode())
    out = _zip_results(root, ref, shards, files)
    print(markdown, flush=True)
    print(f"Results ZIP: {out} ({out.stat().st_size:,} bytes)", flush=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.root)


if __name__ == "__main__":
    main()
