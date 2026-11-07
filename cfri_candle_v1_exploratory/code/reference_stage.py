"""Choose and verify a matched CFRI/SAITS reference for the candle experiment.

The completed held-out-asset run is reused only when its private data receipt,
frozen source, CPU and SAITS manifests, and all 816 feature-mask checkpoints
verify.  The old run is never written.  Otherwise a separate, resumable
reference is made with the *unchanged* held-out-asset source and fresh Yahoo
data.  This is exploratory reuse, not a new confirmation of the old study.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# In Colab the archived files are next to this module.  This fallback allows
# local audit from the builder workspace, where they are kept in upstream/.
HERE = Path(__file__).resolve().parent
if not (HERE / "holdout_data.py").is_file():
    sys.path.insert(0, str(HERE / "upstream"))

import cfri_core as C
import confirm_saits as CS
import holdout_data as D
import holdout_run as R
import holdout_saits as S


CHOICE_NAME = "reference_choice.json"
FRESH_NAME = "reference_fresh"
EXPECTED_FEATURE_CONDITIONS = 816


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _manifest(path: Path, expected: dict, label: str) -> dict:
    value = D.read_json(path)
    _require(isinstance(value, dict), f"{label} manifest absent or unreadable: {path}")
    for key, wanted in expected.items():
        _require(value.get(key) == wanted, f"{label} manifest {key} differs: {path}")
    return value


def _reference_frames(root: Path) -> tuple[dict, dict, dict]:
    """Read and verify the private snapshot without touching the source root."""
    root = Path(root)
    freeze = D.validate_freeze(root)
    receipt_path = root / D.RECEIPT
    receipt = D.read_json(receipt_path)
    _require(isinstance(receipt, dict), f"missing data receipt: {receipt_path}")
    D._validate_receipt_identity(receipt)
    try:
        frozen_at = datetime.fromisoformat(freeze["freeze_utc"].replace("Z", "+00:00"))
        started_at = datetime.fromisoformat(receipt["acquisition_started_utc"].replace("Z", "+00:00"))
        _require(started_at.utcoffset() == timezone.utc.utcoffset(started_at) and
                 frozen_at <= started_at,
                 "source freeze must precede reference data acquisition")
    except (KeyError, AttributeError, ValueError, TypeError) as exc:
        raise RuntimeError("invalid reference freeze/acquisition chronology") from exc
    _require(not D.provider_failures(receipt), "reference has unresolved provider errors")
    _require(receipt.get("eligible_target_count") == len(D.TARGETS),
             "reference does not contain all 16 target ETFs")
    _require(receipt.get("eligible_peer_count") == len(D.PEERS),
             "reference does not contain all 34 peer ETFs")
    targets, peers = D.load_frames(root)
    _require(list(targets) == list(D.TARGETS), "target order or eligibility differs")
    _require(list(peers) == list(D.PEERS), "peer order or eligibility differs")
    return receipt, targets, peers


def _cpu_manifest(root: Path, targets: dict, peers: dict) -> dict:
    receipt_path = root / D.RECEIPT
    expected = {
        "study": D.STUDY_ID,
        "fold": R.FOLD,
        "classification": "held-out-asset evaluation; freeze required before data acquisition",
        "code_sha256": R.code_hashes(),
        "data_receipt_sha256": _sha(receipt_path.read_bytes()),
        "target_frame_sha256": {t: R.frame_hash(f) for t, f in sorted(targets.items())},
        "peer_frame_sha256": {t: R.frame_hash(f) for t, f in sorted(peers.items())},
        "settings": R.SETTINGS,
        "methods": {"feature": list(R.METHODS_FEATURE), "row": list(R.METHODS_ROW)},
    }
    return _manifest(root / R.OUT_DIR / "run_manifest.json", expected, "CPU")


def _saits_manifest(root: Path, targets: dict, peers: dict) -> dict:
    receipt_path = root / D.RECEIPT
    expected = {
        "study": D.STUDY_ID,
        "fold": D.FOLD_TAG,
        "test_end": D.TEST_END,
        "target_tickers": list(targets),
        "peer_tickers": list(peers),
        "methods_by_mask": {mask: list(names) for mask, names in S.METHODS_BY_MASK.items()},
        "code_sha256": S._code_sha256(),
        "data_receipt_sha256": _sha(receipt_path.read_bytes()),
        "target_frame_sha256": {t: S._frame_sha256(f) for t, f in sorted(targets.items())},
        "peer_frame_sha256": {t: S._frame_sha256(f) for t, f in sorted(peers.items())},
        "config": {"saits": CS.SAITS_CONFIG, "variant": CS.VARIANTS["V2"],
                   "windows": [CS.N_STEPS, CS.STRIDE, CS.BATCH_SIZE],
                   "blocks": list(C.BLOCKS), "rates": list(C.RATES), "seeds": list(C.SEEDS),
                   "projection": "joint_ohlc_project(weights=None)",
                   "peer_alpha": S.PEER_ALPHA, "peer_min_peers": S.PEER_MIN_PEERS,
                   "peer_gains": list(S.PEER_GAINS)},
    }
    value = _manifest(root / S.OUT_DIR / "run_manifest.json", expected, "SAITS")
    environment = value.get("environment")
    _require(isinstance(environment, dict) and
             set(("python", "numpy", "pandas", "torch", "pypots", "device")) <= set(environment),
             "SAITS environment fingerprint is missing")
    _require(environment["device"] in ("cuda", "cpu"), "invalid SAITS device in manifest")
    return value


def _feature_keys(targets: dict) -> list[tuple[str, int, float, int]]:
    keys = []
    for ticker in D.TARGETS:
        parts = D.split_frame(targets[ticker])
        lengths = {part: len(values) for part, values in parts.items()}
        for block in C.BLOCKS:
            for rate in C.RATES:
                if C.feasible(lengths, block, rate, "feature"):
                    for seed in C.SEEDS:
                        keys.append((ticker, block, rate, seed))
    _require(len(keys) == EXPECTED_FEATURE_CONDITIONS,
             f"expected 816 feature conditions, found {len(keys)}")
    return keys


def _check_scores(result: dict, methods: tuple[str, ...], test_mask) -> None:
    _require(set(result.get("scores", {})) == set(methods), "score methods differ")
    _require(set(result.get("ohlc_violation_share", {})) == set(methods),
             "OHLC diagnostics differ")
    for method in methods:
        scores = result["scores"][method]
        _require(set(scores) == set(C.FEATURES), f"{method}: score features differ")
        for col, feature in enumerate(C.FEATURES):
            value = scores[feature]
            _require(isinstance(value, (list, tuple)) and len(value) == 3,
                     f"{method}/{feature}: malformed score")
            _require(all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0
                         for v in value[:2]), f"{method}/{feature}: nonfinite score")
            _require(type(value[2]) is int and value[2] == int(test_mask[:, col].sum()),
                     f"{method}/{feature}: masked-cell count differs")
        violation = result["ohlc_violation_share"][method]
        _require(isinstance(violation, (int, float)) and math.isfinite(violation) and
                 abs(violation) <= 1e-9, f"{method}: OHLC order violation")


def _verify_feature_checkpoints(root: Path, targets: dict, cpu: dict,
                                saits: dict | None) -> None:
    keys = _feature_keys(targets)
    parts_cache = {ticker: D.split_frame(targets[ticker]) for ticker in targets}
    for ticker, block, rate, seed in keys:
        mask_by_part = {part: C.condition_mask(values.shape, ticker, D.FOLD_TAG, part,
                                                block, rate, seed, "feature")
                        for part, values in parts_cache[ticker].items()}
        mask_sha = {part: _sha(mask.tobytes()) for part, mask in mask_by_part.items()}
        masked_cells = {part: int(mask.sum()) for part, mask in mask_by_part.items()}
        checks = [(R, cpu, R.METHODS_FEATURE)]
        if saits is not None:
            checks.append((S, saits, S.METHODS_FEATURE))
        for module, manifest, methods in checks:
            path = module.condition_path(root, ticker, "feature", block, rate, seed)
            fingerprint = (R._fingerprint(manifest, ticker, "feature", block, rate, seed)
                           if module is R else
                           S.condition_fingerprint(manifest, ticker, "feature", block, rate, seed))
            complete = (R.verified_condition(path, fingerprint, methods) if module is R else
                        S.verified_condition(path, fingerprint, "feature"))
            _require(complete, f"incomplete or changed checkpoint: {path}")
            result = D.read_json(path)
            _require(isinstance(result, dict), f"unreadable checkpoint: {path}")
            _require((result.get("ticker"), result.get("fold"), result.get("mask_type"),
                      result.get("block_length"), result.get("seed")) ==
                     (ticker, D.FOLD_TAG, "feature", block, seed) and
                     isinstance(result.get("rate"), (int, float)) and
                     math.isclose(result["rate"], rate, rel_tol=0, abs_tol=1e-12),
                     f"condition identity differs: {path}")
            _require(result.get("mask_sha256") == mask_sha and
                     result.get("masked_cells") == masked_cells,
                     f"recomputed mask differs: {path}")
            _check_scores(result, methods, mask_by_part["test"])


def _verify_cpu_reference(root: Path) -> tuple[dict, dict, dict]:
    _, targets, peers = _reference_frames(root)
    cpu = _cpu_manifest(root, targets, peers)
    _verify_feature_checkpoints(root, targets, cpu, None)
    return targets, peers, cpu


def verify_feature_reference(ref_root: Path) -> tuple[dict, dict, dict, dict]:
    """Verify all 816 matched feature-mask CFRI and SAITS conditions read-only."""
    ref_root = Path(ref_root)
    _, targets, peers = _reference_frames(ref_root)
    cpu = _cpu_manifest(ref_root, targets, peers)
    saits = _saits_manifest(ref_root, targets, peers)
    _verify_feature_checkpoints(ref_root, targets, cpu, saits)
    return targets, peers, cpu, saits


def _source_bundle() -> bytes:
    """Pack byte-identical archived source in a deterministic ZIP."""
    source_dir = D.HERE
    manifest_path = source_dir / "SOURCE_SHA256.json"
    manifest = D.read_json(manifest_path)
    _require(isinstance(manifest, dict) and
             set(D.REQUIRED_FROZEN_FILES) <= set(manifest),
             "archived source manifest is missing files")
    for name, digest in manifest.items():
        path = Path(name)
        _require(not path.is_absolute() and ".." not in path.parts and
                 isinstance(digest, str) and len(digest) == 64,
                 f"invalid archived source path or hash: {name}")
        content = (source_dir / name).read_bytes()
        _require(_sha(content) == digest, f"archived source changed: {name}")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name in sorted((*manifest.keys(), "SOURCE_SHA256.json")):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, (source_dir / name).read_bytes())
    payload = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        _require(archive.testzip() is None, "archived source ZIP CRC failed")
    return payload


def _ensure_fresh_freeze(fresh_root: Path) -> None:
    fresh_root = Path(fresh_root)
    bundle = fresh_root / "frozen_source_bundle.zip"
    receipt = fresh_root / "freeze_receipt.json"
    if receipt.exists():
        _require(bundle.is_file(), "fresh freeze receipt exists without source bundle")
        D.validate_freeze(fresh_root)
        return
    if fresh_root.exists():
        extras = [p.name for p in fresh_root.iterdir() if p != bundle]
        _require(not extras, f"fresh reference has data before source freeze: {extras[:4]}")
    fresh_root.mkdir(parents=True, exist_ok=True)
    payload = _source_bundle()
    if bundle.exists():
        _require(_sha(bundle.read_bytes()) == _sha(payload),
                 "incomplete fresh freeze contains a different source bundle")
    else:
        D.atomic(bundle, payload)
    D.atomic(receipt, _json_bytes({"embedded_bundle_sha256": _sha(payload),
                                   "freeze_utc": datetime.now(timezone.utc).isoformat(),
                                   "classification": "exploratory candle method reference"}))
    D.validate_freeze(fresh_root)


def _load_choice(run_root: Path, old_root: Path) -> dict:
    choice = D.read_json(run_root / CHOICE_NAME)
    _require(isinstance(choice, dict), "run `--stage prepare` before other stages")
    _require(choice.get("mode") in ("reuse", "fresh"), "invalid reference mode")
    _require(choice.get("old_root") == str(old_root), "old reference path changed on resume")
    wanted = str(old_root if choice["mode"] == "reuse" else run_root / FRESH_NAME)
    _require(choice.get("root") == wanted, "reference root changed on resume")
    return choice


def _prepare_fresh_data(fresh_root: Path) -> tuple[dict, dict, dict]:
    """Stop before any method work if the 816-condition panel is unavailable."""
    receipt, targets, peers = D.prepare_data(fresh_root)
    _require(receipt.get("eligible_target_count") == len(D.TARGETS) and
             receipt.get("eligible_peer_count") == len(D.PEERS) and
             list(targets) == list(D.TARGETS) and list(peers) == list(D.PEERS),
             "fresh reference needs all 16 targets and 34 peers for the paired "
             "816-condition study; inspect data_receipt.json and use a new root "
             "if a provider or quality exclusion is final")
    return receipt, targets, peers


def prepare_reference(run_root: Path, old_root: Path) -> Path:
    """Lock reuse/fresh choice; prepare fresh private data before methods."""
    run_root, old_root = Path(run_root).resolve(), Path(old_root).resolve()
    _require(run_root != old_root and not run_root.is_relative_to(old_root) and
             not old_root.is_relative_to(run_root),
             "new run root and old reference root must be disjoint")
    run_root.mkdir(parents=True, exist_ok=True)
    path = run_root / CHOICE_NAME
    if path.exists():
        choice = _load_choice(run_root, old_root)
        ref_root = Path(choice["root"])
        if choice["mode"] == "reuse":
            verify_feature_reference(ref_root)
        else:
            _ensure_fresh_freeze(ref_root)
            _prepare_fresh_data(ref_root)
        print(f"Reference mode locked: {choice['mode']} -> {ref_root}", flush=True)
        return ref_root
    try:
        verify_feature_reference(old_root)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError,
            AssertionError, zipfile.BadZipFile) as exc:
        mode, ref_root = "fresh", run_root / FRESH_NAME
        reason = f"{type(exc).__name__}: {exc}"[:500]
    else:
        mode, ref_root, reason = "reuse", old_root, "all 816 feature checkpoints verified"
    choice = {"mode": mode, "root": str(ref_root), "old_root": str(old_root),
              "selected_utc": datetime.now(timezone.utc).isoformat(),
              "selection_reason": reason}
    D.atomic(path, _json_bytes(choice))
    print(f"Reference mode locked: {mode} -> {ref_root}; {reason}", flush=True)
    if mode == "fresh":
        _ensure_fresh_freeze(ref_root)
        _prepare_fresh_data(ref_root)
    return ref_root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True,
                        help="new candle experiment Drive root")
    parser.add_argument("--old-root", type=Path, required=True,
                        help="completed held-out-asset Drive root (read-only)")
    parser.add_argument("--stage", choices=("prepare", "cpu", "saits", "verify"),
                        required=True)
    args = parser.parse_args()
    run_root, old_root = args.root.resolve(), args.old_root.resolve()
    if args.stage == "prepare":
        prepare_reference(run_root, old_root)
        return
    choice = _load_choice(run_root, old_root)
    ref_root = Path(choice["root"])
    if choice["mode"] == "reuse":
        if args.stage == "verify":
            targets, _, _, _ = verify_feature_reference(ref_root)
            print(f"Reference verified: {len(targets)} targets, "
                  f"{EXPECTED_FEATURE_CONDITIONS} matched feature conditions", flush=True)
        else:
            print(f"{args.stage}: locked reusable reference; no computation needed", flush=True)
        return
    _ensure_fresh_freeze(ref_root)
    if args.stage == "cpu":
        _, targets, peers = _prepare_fresh_data(ref_root)
        result = R.run_cpu(ref_root, targets, peers, mask_types=("feature",))
        _verify_cpu_reference(ref_root)
        print("CPU reference:", result, flush=True)
    elif args.stage == "saits":
        _verify_cpu_reference(ref_root)
        import torch
        _require(torch.cuda.is_available(),
                 "fresh reference needs a CUDA GPU to rerun SAITS on matching data")
        _, targets, peers = _prepare_fresh_data(ref_root)
        result = S.run_saits(ref_root, targets, peers, mask_types=("feature",),
                             device="cuda")
        verify_feature_reference(ref_root)
        print("SAITS reference:", result, flush=True)
    else:
        targets, _, _, _ = verify_feature_reference(ref_root)
        print(f"Reference verified: {len(targets)} targets, "
              f"{EXPECTED_FEATURE_CONDITIONS} matched feature conditions", flush=True)


if __name__ == "__main__":
    main()
