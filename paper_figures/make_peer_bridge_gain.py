"""Plot the prespecified new-asset whole-row peer-bridge contrast.

The source file contains 816 matched conditions per mask type. Each bar is the
target ETF's mean unbridged CFRI NRMSE minus its mean bridged CFRI NRMSE.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "cfri_holdout_v1/results/holdout_condition_scores.csv"


def main() -> None:
    scores: dict[str, dict[str, dict[tuple[str, str, str], float]]] = defaultdict(lambda: defaultdict(dict))
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["mask_type"] != "row":
                continue
            if row["method"] in {"cfri_joint", "cfri_peer_target_joint"}:
                condition = (row["block_length"], row["rate"], row["seed"])
                assert condition not in scores[row["ticker"]][row["method"]]
                scores[row["ticker"]][row["method"]][condition] = float(row["nrmse"])

    assert len(scores) == 16
    gains = []
    for ticker, methods in scores.items():
        assert len(methods["cfri_joint"]) == len(methods["cfri_peer_target_joint"]) == 51
        assert methods["cfri_joint"].keys() == methods["cfri_peer_target_joint"].keys()
        gains.append(
            (ticker, mean(methods["cfri_joint"][key] - methods["cfri_peer_target_joint"][key]
                          for key in methods["cfri_joint"]))
        )
    gains.sort(key=lambda item: item[1])
    assert all(gain > 0 for _, gain in gains)
    assert abs(mean(gain for _, gain in gains) - (0.17132885819724206 - 0.15713554191262252)) < 1e-12

    fig, ax = plt.subplots(figsize=(7.7, 5.0), dpi=300)
    labels = [item[0] for item in gains]
    values = [item[1] for item in gains]
    colors = ["#bb6f19" if ticker in {"EFA", "EEM"} else "#277da8" for ticker in labels]
    ax.barh(labels, values, color=colors, height=0.72)
    ax.axvline(mean(values), color="#363636", linestyle="--", linewidth=1.1)
    ax.text(mean(values) + 0.001, 0.3, "16-ETF mean", fontsize=8, color="#363636")
    ax.set_xlabel("NRMSE reduction from peer bridge (unbridged minus bridged)", fontsize=9)
    ax.set_xlim(0, 0.082)
    ax.grid(axis="x", color="#d9d9d9", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "peer_bridge_gain_by_etf.png", dpi=300)
    fig.savefig(HERE / "peer_bridge_gain_by_etf.svg")
    plt.close(fig)
    print(f"16 ETF; mean NRMSE gain {mean(values):.6f}")


if __name__ == "__main__":
    main()
