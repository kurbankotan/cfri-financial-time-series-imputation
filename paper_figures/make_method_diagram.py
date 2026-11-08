"""Create a schematic of fixed CFRI and its later whole-row extension."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


HERE = Path(__file__).resolve().parent


def box(ax, xy, wh, label, face="#eaf2f7", edge="#2a5873", size=9):
    x, y = xy
    w, h = wh
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.013",
            linewidth=1.25, edgecolor=edge, facecolor=face
        )
    )
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=size)


def arrow(ax, a, b):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13,
                                 linewidth=1.3, color="#3b4b56",
                                 connectionstyle="arc3,rad=0"))


def main():
    fig, ax = plt.subplots(figsize=(8.4, 4.0), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box(ax, (0.035, 0.42), (0.16, 0.16), "Target OHLCV\n+ mask", size=11)
    box(ax, (0.245, 0.40), (0.22, 0.20), "Log-price paths\n+ volume rule", size=11)
    box(ax, (0.52, 0.68), (0.21, 0.17), "Feature gap\nsame-day OHLC", face="#eef6f4", edge="#287663", size=10.5)
    box(ax, (0.52, 0.15), (0.21, 0.17), "Whole-row gap\npeer returns", face="#fff3e5", edge="#9e611b", size=10.5)
    box(ax, (0.78, 0.67), (0.18, 0.18), "Training-only ridge\nresidual", face="#eef6f4", edge="#287663", size=10)
    box(ax, (0.78, 0.14), (0.18, 0.18), "Training-only peer\nbridge", face="#fff3e5", edge="#9e611b", size=10)
    box(ax, (0.54, 0.40), (0.38, 0.19), "Preserve observations; enforce OHLC\nFold D: heuristic  |  new assets: exact", face="#eff0f7", edge="#4e5682", size=10)

    arrow(ax, (0.198, 0.50), (0.242, 0.50))
    arrow(ax, (0.466, 0.56), (0.53, 0.69))
    arrow(ax, (0.466, 0.44), (0.53, 0.31))
    arrow(ax, (0.733, 0.765), (0.777, 0.765))
    arrow(ax, (0.733, 0.235), (0.777, 0.235))
    arrow(ax, (0.866, 0.665), (0.78, 0.59))
    arrow(ax, (0.866, 0.335), (0.78, 0.40))

    ax.text(0.62, 0.89, "Original CFRI", ha="center", color="#287663", fontsize=9, weight="bold")
    ax.text(0.62, 0.09, "Later peer-bridge extension", ha="center", color="#9e611b", fontsize=9, weight="bold")
    fig.tight_layout(pad=0.2)
    fig.savefig(HERE / "cfri_method_schematic.png", dpi=300)
    fig.savefig(HERE / "cfri_method_schematic.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
