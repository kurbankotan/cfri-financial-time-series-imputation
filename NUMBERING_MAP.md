# CFRI article numbering and historical file labels

The CFRI manuscript is a separate article. The repository retains the earlier ITRI archive and the original names of scripts and exported result files. Their old table and figure numbers are **not** claims that those ITRI results appear in the CFRI article.

The CFRI draft has two main tables, three main figures, Supplementary Notes S1–S3, Tables S1–S10, and Figure S1. Sections 4.1–4.2 describe its tests; Sections 5.1–5.3 report their outcomes. The six displayed main equations are numbered (1)–(6).

| Historical label in v16 or a study script | CFRI article label | Source or status |
|---|---|---|
| Fold D comparison table in the earlier combined draft | Main Table 1 | `cfri_confirmatory/` period test. The v18 article shows fold D columns only; folds A–C are exploratory prose. |
| New-asset decision table in the earlier combined draft | Main Table 2 | `cfri_holdout_v1/` prespecified decisions. |
| Supplementary Note S2 | Supplementary Note S1 | CFRI development and fold D protocol. |
| Supplementary Note S3 | Supplementary Note S2 | New-asset holdout and peer bridge. |
| Supplementary Note S4 | Supplementary Note S3 | Post-hoc candle replay. |
| Supplementary Tables S19–S22 | Supplementary Tables S1–S4 | Fold D feature, method, gap-length, and region detail. |
| Supplementary Tables S23–S25 | Supplementary Tables S5–S7 | New-asset decisions, ETF detail, and gap-length detail. |
| Supplementary Tables S26–S28 | Supplementary Tables S8–S10 | Exploratory candle replay. |
| Supplementary Figure S6 | Main Figure 2 | Fold D gap-length error plot. `cfri_confirmatory/analysis/fold_D_supplement.py` still exports `figure_S6.png`. |
| Supplementary Figure S7 | Supplementary Figure S1 | Fold D asset-level paired differences. The same script still exports `figure_S7.png`. |
| New method schematic | Main Figure 1 | `paper_figures/cfri_method_schematic.png`; drawn by `paper_figures/make_method_diagram.py`. |
| New peer-bridge target plot | Main Figure 3 | `paper_figures/peer_bridge_gain_by_etf.png`; drawn from `cfri_holdout_v1/results/holdout_condition_scores.csv` by `paper_figures/make_peer_bridge_gain.py`. |

The old ITRI diagnostic Note S1, Tables S1–S18, and Figures S1–S5 from the previous combined draft were removed from the **CFRI manuscript and supplement**. Their source archive remains in the historical ITRI directories for provenance and verification. The current `paper_figures/figure_1_itri_workflow.png` and similarly named files are historical images; the CFRI article's Figures 1–3 use the new filenames listed above.

Changing historical script output names would alter frozen source archives without changing any result. This map is the link between preserved filenames and the separate CFRI article.
