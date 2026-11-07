"""Exploratory, paired candle-geometry experiment on held-out feature masks.

The original held-out source and score shards remain read-only. Every new
condition is bound to the verified reference, masks, inputs, and this source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import cfri_core as C
import holdout_data as D
import holdout_run as R
import holdout_saits as S
import reference_stage as REF
import v2_price as V
from candle_geometry import fit_candle_model, predict_candle_prices


HERE = Path(__file__).resolve().parent
OUT_DIR = "candle_feature"
METHODS = ("cfri_joint", "candle_direct", "candle_half", "saits_joint")
CODE_FILES = ("candle_runner.py", "candle_geometry.py", "reference_stage.py")
SETTINGS = {
    "classification": "exploratory replay after seeing 2026 held-out outcomes",
    "mask_type": "feature",
    "candle_alpha": 10.0,
    "blend_candle_weight": 0.5,
    "original_price_alpha": R.SETTINGS["price_alpha"],
    "original_gain": R.SETTINGS["base_gain"],
    "original_volume_eta": R.SETTINGS["volume_eta"],
    "projection": "v2_price.joint_ohlc_project(weights=None)",
    "blocks": list(C.BLOCKS), "rates": list(C.RATES), "seeds": list(C.SEEDS),
    "fold": D.FOLD_TAG, "test_end": D.TEST_END,
}


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def blob(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def reference_root(root: Path) -> Path:
    choice = D.read_json(root / "reference_choice.json")
    if not isinstance(choice, dict) or choice.get("mode") not in ("reuse", "fresh"):
        raise RuntimeError("reference_choice.json missing; run the reference stages first")
    ref = Path(choice["root"])
    if not ref.is_absolute():
        raise RuntimeError("reference root must be absolute")
    return ref


def expected_keys(targets: dict) -> list[tuple[str, str, int, float, int]]:
    keys = []
    for ticker in D.TARGETS:
        if ticker not in targets:
            continue
        lengths = {part: len(array) for part, array in D.split_frame(targets[ticker]).items()}
        for block in C.BLOCKS:
            for rate in C.RATES:
                if C.feasible(lengths, block, rate, "feature"):
                    for seed in C.SEEDS:
                        keys.append((ticker, "feature", block, rate, seed))
    if not keys:
        raise RuntimeError("no feasible feature conditions")
    return keys


def manifest(root: Path, ref: Path, targets: dict, peers: dict) -> dict:
    choice_path = root / "reference_choice.json"
    receipt_path = ref / D.RECEIPT
    cpu_path = ref / R.OUT_DIR / "run_manifest.json"
    saits_path = ref / S.OUT_DIR / "run_manifest.json"
    source_hashes = {name: sha((HERE / name).read_bytes()) for name in CODE_FILES}
    stable = {
        "study": "cfri-candle-v1-exploratory",
        "reference_root": str(ref),
        "reference_choice_sha256": sha(choice_path.read_bytes()),
        "reference_data_receipt_sha256": sha(receipt_path.read_bytes()),
        "reference_cpu_manifest_sha256": sha(cpu_path.read_bytes()),
        "reference_saits_manifest_sha256": sha(saits_path.read_bytes()),
        "reference_target_frame_sha256": {ticker: R.frame_hash(frame) for ticker, frame in sorted(targets.items())},
        "reference_peer_frame_sha256": {ticker: R.frame_hash(frame) for ticker, frame in sorted(peers.items())},
        "new_code_sha256": source_hashes,
        "upstream_code_sha256": R.code_hashes(),
        "settings": SETTINGS,
        "methods": list(METHODS),
        "expected_conditions": len(expected_keys(targets)),
    }
    path = root / OUT_DIR / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        prior = D.read_json(path)
        if not isinstance(prior, dict) or any(prior.get(k) != v for k, v in stable.items()):
            raise RuntimeError("candle manifest changed; resume only with identical code, data and settings")
        return prior
    stable["created_utc"] = datetime.now(timezone.utc).isoformat()
    D.atomic(path, blob(stable))
    return stable


def condition_path(root: Path, key: tuple[str, str, int, float, int]) -> Path:
    ticker, mask_type, block, rate, seed = key
    if mask_type != "feature":
        raise ValueError("candle experiment supports feature masks only")
    return root / OUT_DIR / f"{ticker}_{mask_type}_b{block}_r{rate:.2f}_s{seed}.json"


def fingerprint(m: dict, key: tuple[str, str, int, float, int], ref_cpu_sha: str,
                ref_saits_sha: str) -> str:
    stable = {k: v for k, v in m.items() if k != "created_utc"}
    stable.update({"key": key, "reference_cpu_condition_sha256": ref_cpu_sha,
                   "reference_saits_condition_sha256": ref_saits_sha})
    return sha(blob(stable))


def verified_condition(path: Path, fp: str, key: tuple[str, str, int, float, int]) -> bool:
    side = D.read_json(path.with_name(path.name + ".done.json"))
    result = D.read_json(path)
    if not (path.is_file() and isinstance(side, dict) and isinstance(result, dict)
            and side.get("fingerprint") == fp and side.get("sha256") == sha(path.read_bytes())
            and result.get("mask_sha256") == side.get("mask_sha256")
            and set(result.get("scores", {})) == set(METHODS)
            and result.get("fold") == D.FOLD_TAG
            and (result.get("ticker"), result.get("mask_type"), result.get("block_length"),
                 result.get("rate"), result.get("seed")) == key):
        return False
    try:
        if set(result["mask_sha256"]) != {"train", "val", "test"} or any(
                not isinstance(result["masked_cells"][part], int) or
                result["masked_cells"][part] <= 0 for part in ("train", "val", "test")):
            return False
        for method in METHODS:
            if set(result["scores"][method]) != set(C.FEATURES):
                return False
            for feature in C.FEATURES:
                nrmse, nmae, count = result["scores"][method][feature]
                if not (math.isfinite(nrmse) and math.isfinite(nmae) and
                        nrmse >= 0 and nmae >= 0 and isinstance(count, int) and count > 0):
                    return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


def verify_reference_condition(ref: Path, key: tuple[str, str, int, float, int],
                               cpu_manifest: dict, saits_manifest: dict) -> tuple[dict, dict, str, str]:
    cp, sp = R.condition_path(ref, *key), S.condition_path(ref, *key)
    if not R.verified_condition(cp, R._fingerprint(cpu_manifest, *key), R.METHODS_FEATURE):
        raise RuntimeError(f"reference CPU checkpoint invalid: {cp}")
    if not S.verified_condition(sp, S.condition_fingerprint(saits_manifest, *key), "feature"):
        raise RuntimeError(f"reference SAITS checkpoint invalid: {sp}")
    cpu, saits = D.read_json(cp), D.read_json(sp)
    if cpu["mask_sha256"] != saits["mask_sha256"] or cpu["masked_cells"] != saits["masked_cells"]:
        raise RuntimeError(f"reference CPU/SAITS masks differ: {key}")
    return cpu, saits, sha(cp.read_bytes()), sha(sp.read_bytes())


def _same_score(a: dict, b: dict, label: str) -> None:
    if set(a) != set(C.FEATURES) or set(b) != set(C.FEATURES):
        raise RuntimeError(f"{label}: score fields differ")
    for feature in C.FEATURES:
        x, y = a[feature], b[feature]
        if int(x[2]) != int(y[2]) or not all(math.isclose(float(x[i]), float(y[i]),
                                                    rel_tol=1e-9, abs_tol=1e-9) for i in (0, 1)):
            raise RuntimeError(f"{label}: recomputed original CFRI differs on {feature}: {x} vs {y}")


def one_condition(frame, key: tuple[str, str, int, float, int],
                  cpu: dict, saits: dict) -> dict:
    t0 = time.perf_counter()
    ticker, mask_type, block, rate, seed = key
    parts = D.split_frame(frame)
    masks = {part: C.condition_mask(arr.shape, ticker, D.FOLD_TAG, part,
                                    block, rate, seed, mask_type)
             for part, arr in parts.items()}
    mask_sha = {part: sha(mask.tobytes()) for part, mask in masks.items()}
    counts = {part: int(mask.sum()) for part, mask in masks.items()}
    if mask_sha != cpu["mask_sha256"] or mask_sha != saits["mask_sha256"]:
        raise RuntimeError(f"new masks do not match both reference methods: {key}")
    if counts != cpu["masked_cells"] or counts != saits["masked_cells"]:
        raise RuntimeError(f"new mask counts do not match both reference methods: {key}")
    train, test = parts["train"], parts["test"]
    tr_mask, te_mask = masks["train"], masks["test"]
    _, scales = C.observed_scaler(train, tr_mask)
    base_log, designs = C.prepare_price_eval(test, te_mask)
    training = C.prepare_price_training(train, tr_mask, ticker, D.FOLD_TAG, block, rate, seed)
    original_models = C.fit_price_models(training, R.SETTINGS["price_alpha"])
    original_prices = C.price_candidate(base_log, designs, original_models, R.SETTINGS["base_gain"])
    visible = C.corrupt(test, te_mask)
    volume = C.volume_log_candidate(test, te_mask, R.SETTINGS["volume_eta"])
    original_est = R.estimate_from_prices(visible, te_mask, original_prices, volume)
    original_est = V.joint_ohlc_project(original_est, te_mask)
    original_score = C.score_method(test, original_est, te_mask, scales)
    _same_score(original_score, cpu["scores"]["cfri_joint"], str(key))

    model = fit_candle_model(train, tr_mask, ticker, D.FOLD_TAG, block, rate, seed,
                             alpha=SETTINGS["candle_alpha"])
    direct_prices = predict_candle_prices(test, te_mask, model, original_prices)
    if direct_prices.shape != original_prices.shape or not np.isfinite(direct_prices).all() or (direct_prices <= 0).any():
        raise RuntimeError("candle model produced invalid prices")
    if not np.allclose(direct_prices[~te_mask[:, :4]], test[:, :4][~te_mask[:, :4]], rtol=0, atol=1e-10):
        raise RuntimeError("candle model changed observed prices")
    direct_est = R.estimate_from_prices(visible, te_mask, direct_prices, volume)
    direct_est = V.joint_ohlc_project(direct_est, te_mask)
    w = SETTINGS["blend_candle_weight"]
    blend_prices = np.exp((1.0 - w) * np.log(original_prices) + w * np.log(direct_prices))
    blend_prices[~te_mask[:, :4]] = test[:, :4][~te_mask[:, :4]]
    blend_est = R.estimate_from_prices(visible, te_mask, blend_prices, volume)
    blend_est = V.joint_ohlc_project(blend_est, te_mask)
    scores = {"cfri_joint": original_score,
              "candle_direct": C.score_method(test, direct_est, te_mask, scales),
              "candle_half": C.score_method(test, blend_est, te_mask, scales),
              "saits_joint": saits["scores"]["saits_joint"]}
    violations = {"cfri_joint": C.ohlc_violations(original_est, te_mask)[0],
                  "candle_direct": C.ohlc_violations(direct_est, te_mask)[0],
                  "candle_half": C.ohlc_violations(blend_est, te_mask)[0],
                  "saits_joint": saits["ohlc_violation_share"]["saits_joint"]}
    if any(value > 1e-9 for value in violations.values()):
        raise RuntimeError(f"OHLC order violation after projection: {key}")
    return {"ticker": ticker, "fold": D.FOLD_TAG, "mask_type": mask_type,
            "block_length": block, "rate": rate, "seed": seed,
            "mask_sha256": mask_sha, "masked_cells": counts,
            "scores": scores, "ohlc_violation_share": violations,
            "candle_model_fit": model is not None,
            "seconds": float(time.perf_counter() - t0),
            "completed_utc": datetime.now(timezone.utc).isoformat()}


def run(root: Path, max_new_conditions: int | None = None) -> dict:
    root = Path(root)
    ref = reference_root(root)
    targets, peers, cpu_manifest, saits_manifest = REF.verify_feature_reference(ref)
    m = manifest(root, ref, targets, peers)
    keys = expected_keys(targets)
    if len(keys) != m["expected_conditions"]:
        raise RuntimeError("condition count changed")
    summary = {"total": len(keys), "new": 0, "skipped": 0, "stopped_early": False}
    for key in keys:
        cpu, saits, cpu_sha, saits_sha = verify_reference_condition(ref, key, cpu_manifest, saits_manifest)
        path = condition_path(root, key)
        fp = fingerprint(m, key, cpu_sha, saits_sha)
        if verified_condition(path, fp, key):
            summary["skipped"] += 1
            continue
        if max_new_conditions is not None and summary["new"] >= max_new_conditions:
            summary["stopped_early"] = True
            break
        result = one_condition(targets[key[0]], key, cpu, saits)
        content = blob(result)
        D.atomic(path, content)
        D.atomic(path.with_name(path.name + ".done.json"),
                 blob({"fingerprint": fp, "sha256": sha(content),
                       "mask_sha256": result["mask_sha256"]}))
        summary["new"] += 1
        if summary["new"] == 1 or (summary["new"] + summary["skipped"]) % 25 == 0:
            print(f"[CANDLE] {summary['new'] + summary['skipped']}/{len(keys)} saved or verified", flush=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("run",), default="run")
    parser.add_argument("--max-new-conditions", type=int)
    args = parser.parse_args()
    print(run(args.root, args.max_new_conditions), flush=True)


if __name__ == "__main__":
    main()
