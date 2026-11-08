# CFRI: Cross-Feature Residual Interpolation

[![Verify results](https://github.com/kurbankotan/cfri-financial-time-series-imputation/actions/workflows/verify-results.yml/badge.svg)](https://github.com/kurbankotan/cfri-financial-time-series-imputation/actions/workflows/verify-results.yml)

This repository accompanies the separate CFRI manuscript draft, *Cross-Feature Residual Interpolation for Financial Time-Series Imputation*. CFRI corrects a hidden log-price path using the residuals of observed same-day OHLC fields, treats volume separately, and preserves observed cells and OHLC order. A later extension uses visible peer returns for an isolated whole-row outage. The methods use both endpoints of a gap and reconstruct historical records; they are not forecasts or trading systems.

The related Iterative Temporal Regression Imputation (ITRI) manuscript is under editorial review. Its original development and external-validation files are retained here as a historical provenance archive and for the fixed ITRI comparator, **not as results of the CFRI article**. The CFRI manuscript does not reproduce their old tables or figures. See [`NUMBERING_MAP.md`](NUMBERING_MAP.md) for the distinction between historical source labels and the article's labels.

## Article and evidence map

| Evidence | Directory | CFRI article location and status |
|---|---|---|
| CFRI exploratory folds A–C and locally frozen 2026 fold D | `cfri_confirmatory/` | Method Sections 3.1–3.3; design Section 4.1; result Section 5.1, Table 1, Figure 2, Supplementary Note S1, Tables S1–S4, Figure S1. A–C were inspected during development; fold D is the fixed new-period test. The public commit followed data acquisition. |
| New-asset 16-ETF evaluation with exact OHLC projection and peer bridge | `cfri_holdout_v1/` | Sections 3.4, 4.2, 5.2; Table 2, Figure 3, Supplementary Note S2, Tables S5–S7. A locally frozen new-asset test in the same 2026 calendar. |
| Candle-coordinate replay | `cfri_candle_v1_exploratory/` | Section 5.3, Supplementary Note S3, Tables S8–S10. Designed after holdout results; exploratory, feature-wise masks only. |
| Final article figures | `paper_figures/` | Main Figures 1–3, figure source and figure map. |

The original ITRI archive is in `notebooks/`, `scripts/`, `results/`, `metadata/`, `development_comparators/`, and `external_validation/`. Historical filenames, protocols, and derived scores remain byte-identical to their original archive to preserve provenance. [`PACKAGE_PROVENANCE.md`](PACKAGE_PROVENANCE.md) records the archives used to assemble the repository. The article uses ITRI only as a fixed temporal comparator on fold D, with the same new masks as CFRI. Its earlier ITRI numerical analyses are not part of this CFRI article.

## Main findings and limits

- On 34 ETFs in the January–September 2026 fold D, fixed CFRI met four prespecified decision rules against log-linear interpolation, original ITRI, a no-residual CFRI ablation, and normalized SAITS V2. After the same original heuristic OHLC repair was applied to SAITS, CFRI led in only 13/34 ETFs and SAITS had lower price-only error.
- On 16 new ETFs, the feature-wise comparison with exactly projected SAITS failed the prespecified win threshold (9/16). Under isolated target-only whole-row gaps, the peer bridge met both prespecified comparisons (16/16 each). Masking the peers also removed its benefit. The bridge gain is concentrated in EEM and EFA.
- The later candle-coordinate replay reduced CFRI error on the same masks but did not beat SAITS on OHLC-only error. It has no independent new-period or new-asset confirmation.

These are controlled retrospective masks, not naturally occurring outages. A jointly peer-trained comparator and a later locked test of the final method remain open evaluations.

## Verify without vendor data

Install the numerical verification dependencies and run the checks from the repository root:

```bash
python -m pip install numpy==2.1.3 pandas==2.2.3 scipy==1.16.3
python scripts/verify_manifest.py
python scripts/verify_published_results.py
python development_comparators/verify_comparator_numbers.py
python external_validation/code/verify_reported_numbers.py
python cfri_confirmatory/analysis/verify_reported_numbers.py
python cfri_confirmatory/analysis/fold_D_supplement.py --out /tmp/cfri_fold_D_supplement
python cfri_holdout_v1/analysis/verify_reported_numbers.py
python cfri_candle_v1_exploratory/verify_package.py
```

The GitHub Actions workflow runs these checks on each push. The first three Python checks verify the historical ITRI archive; the later checks verify the CFRI article evidence. `SHA256SUMS.txt` records the packaged canonical file bytes. A later vendor download may differ because the provider can revise historical market data.

## Data, citation, and license

Raw Yahoo Finance price and volume tables and private snapshots are excluded. Public files contain derived errors, mask identifiers, settings, diagnostics, and hashes of input data. Acquisition and freeze receipts are in the study folders. Do not upload local `raw_do_not_publish`, `raw_cache`, or private snapshot folders.

Citation metadata are in [`CITATION.cff`](CITATION.cff). The code is under the [MIT License](LICENSE); study folders document the provenance of result files. No publication or release version is claimed for the draft.

**Author:** Kurban Kotan, Manisa Celal Bayar University. [ORCID 0000-0002-6660-0565](https://orcid.org/0000-0002-6660-0565).
