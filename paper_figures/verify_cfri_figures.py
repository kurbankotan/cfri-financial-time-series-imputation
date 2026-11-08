"""Verify the derived source values and PNG dimensions of CFRI Figures 1–3."""

from __future__ import annotations

import csv
import struct
from collections import defaultdict
from pathlib import Path
from statistics import mean


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "cfri_holdout_v1/results/holdout_condition_scores.csv"
METHODS = ("cfri_joint", "cfri_peer_target_joint")


def png_size(path: Path) -> tuple[int, int]:
    blob = path.read_bytes()[:24]
    if blob[:8] != b"\x89PNG\r\n\x1a\n" or blob[12:16] != b"IHDR":
        raise AssertionError(f"Invalid PNG: {path.name}")
    return struct.unpack(">II", blob[16:24])


def main() -> None:
    expected = {
        "cfri_method_schematic.png": (2520, 1200),
        "fold_D_gap_length_profile.png": (2160, 900),
        "peer_bridge_gain_by_etf.png": (2310, 1500),
    }
    for name, shape in expected.items():
        assert png_size(HERE / name) == shape, name

    scores: dict[str, dict[str, dict[tuple[str, str, str], float]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["mask_type"] != "row" or row["method"] not in METHODS:
                continue
            key = (row["block_length"], row["rate"], row["seed"])
            slot = scores[row["ticker"]][row["method"]]
            assert key not in slot
            slot[key] = float(row["nrmse"])

    assert len(scores) == 16
    gain = {}
    for ticker, methods in scores.items():
        unbridged, bridged = (methods[name] for name in METHODS)
        assert len(unbridged) == len(bridged) == 51
        assert unbridged.keys() == bridged.keys()
        gain[ticker] = mean(unbridged[key] - bridged[key] for key in unbridged)

    assert all(value > 0 for value in gain.values())
    assert abs(mean(gain.values()) - 0.014193316284619525) < 1e-12
    assert abs((gain["EEM"] + gain["EFA"]) / sum(gain.values()) - 0.5269835773146405) < 1e-12
    print("Verified CFRI Figure 1–3 PNGs and Figure 3 source contrast: 16 ETFs × 51 matched conditions")


if __name__ == "__main__":
    main()
