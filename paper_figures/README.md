# CFRI article figures

| CFRI article | Image | Source and reproduction |
|---|---|---|
| Figure 1, method schematic | `cfri_method_schematic.png` | `make_method_diagram.py` (also exports SVG). |
| Figure 2, fold D gap-length profile | `fold_D_gap_length_profile.png` | Original fold D Supplementary Figure S6, promoted to the main article. Recompute its source data and historical `figure_S6.png` with `cfri_confirmatory/analysis/fold_D_supplement.py`. |
| Figure 3, peer-bridge gain by ETF | `peer_bridge_gain_by_etf.png` | `make_peer_bridge_gain.py` uses `cfri_holdout_v1/results/holdout_condition_scores.csv` (also exports SVG). |

To redraw Figures 1 and 3 from the repository root, install `matplotlib` and run:

```bash
python paper_figures/make_method_diagram.py
python paper_figures/make_peer_bridge_gain.py
```

To reproduce the fold D source table and its plot, install the numerical dependencies listed in the root README plus `matplotlib`, then run:

```bash
python cfri_confirmatory/analysis/fold_D_supplement.py --out /tmp/cfri_fold_D_figures
```

The historical ITRI images named `figure_1_itri_workflow.png` through `figure_7_level_shift.png` are preserved as archive assets. They are not CFRI article Figures 1–3. The current supplement's Figure S1 comes from that fold D script's historical `figure_S7.png` output and is embedded in the supplement DOCX. The root `SHA256SUMS.txt` verifies the published figure PNG and SVG bytes; `verify_cfri_figures.py` checks Figure 3's paired source contrast.
