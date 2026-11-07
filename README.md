# CFRI: Cross-Feature Residual Interpolation

[![Verify results](https://github.com/kurbankotan/cfri-financial-time-series-imputation/actions/workflows/verify-results.yml/badge.svg)](https://github.com/kurbankotan/cfri-financial-time-series-imputation/actions/workflows/verify-results.yml)

This repository accompanies a CFRI-first manuscript revision draft on reconstructing contiguous missing blocks in daily financial time series. CFRI corrects log-linear price interpolation using observed same-day OHLC residuals, applies a volume rule, and enforces the OHLC order. The original Iterative Temporal Regression Imputation (ITRI) experiments and external validation remain here as the development history and comparator evidence. These methods reconstruct historical gaps using both sides of a gap; they are not forecasts or trading systems.

## Study map

| Study | Directory | Evidence status |
|---|---|---|
| ITRI development ablation on BIST 30 and S&P 500 | `notebooks/`, `scripts/`, `results/`, `metadata/` | Original development experiment and held-out test. |
| Matched-mask development comparators | `development_comparators/` | PCHIP, KNN and chained equations on the original data. |
| External validation on 34 country ETFs | `external_validation/` | Frozen classical and neural protocols, results, and explicitly exploratory follow-up analyses. |
| CFRI folds A–C and 2026 fold D | `cfri_confirmatory/` | Exploratory earlier folds and a prespecified new-period test; the public GitHub commit occurred **after** data acquisition, as documented in `cfri_confirmatory/DEVIATIONS.md`. |
| CFRI new-asset holdout on 16 ETFs | `cfri_holdout_v1/` | Locally time-stamped source freeze before acquisition; published after the run. It reuses the 2026 period. |
| Candle-coordinate CFRI extension | `cfri_candle_v1_exploratory/` | Exploratory matched replay designed after the 2026 holdout results were inspected; feature-wise masks only. |
| Figure source and rendered figures | `paper_figures/` | Historical file labels are mapped in `NUMBERING_MAP.md`. |

The study folders contain the original protocols, notebooks, source, analysis scripts, receipts, and derived scores. The historical ITRI filenames and Drive paths remain intact to preserve their provenance. `PACKAGE_PROVENANCE.md` records the source archives used to assemble this repository.

The CFRI-first draft places the method in Sections 3.1–3.4, the ITRI comparator in Section 3.5, the evaluations in Sections 4.1–4.3, and the results in Sections 5.1–5.4. Its main Table 1 reports CFRI fold D and earlier folds; main Table 2 reports the new-asset holdout. Historical ITRI tables and figures remain in this repository, but the draft has no ITRI main tables or main figures. The old-to-current labels are in [`NUMBERING_MAP.md`](NUMBERING_MAP.md).

## Results and interpretation

- In the 2026 fold D test, CFRI met all four prespecified primary decision rules against log-linear interpolation, original ITRI, CFRI without its residual correction, and normalized SAITS V2. In a secondary comparison that applied the same original heuristic OHLC repair to both methods, CFRI had lower error than SAITS in only 13 of 34 ETFs; no general advantage over equally repaired SAITS was established.
- In the 16-ETF new-asset holdout, feature-mask H1 against projected SAITS did not meet its 12-of-16 decision rule (9 of 16). The whole-row peer bridge comparisons H2 and H3 met their rules (16 of 16 each). This is a new-asset test in the same 2026 period, not a new-period test.
- The later candle-coordinate replay used the same 2026 assets and masks. Its fixed half blend reduced equal-ETF all-field NRMSE from 0.138867 for original CFRI to 0.135973 and improved all 16 ETFs relative to CFRI. Against SAITS V2 it won 11 of 16 ETFs on the all-field mean, while SAITS had the lower OHLC-only mean (0.046838 versus 0.047293). The all-field edge comes from the unchanged CFRI volume result. No whole-row candle experiment was run. These candle findings are exploratory.

Read each study's `README.md` and protocol for exact masks, endpoints, settings, and limits.

## Verify the published artifacts

No vendor data are needed for the checks. From the repository root, install the verification dependencies and run:

```bash
python -m pip install numpy==2.1.3 pandas==2.2.3 scipy==1.16.3
python scripts/verify_published_results.py
python development_comparators/verify_comparator_numbers.py
python external_validation/code/verify_reported_numbers.py
python cfri_confirmatory/analysis/verify_reported_numbers.py
python cfri_confirmatory/analysis/fold_D_supplement.py --out /tmp/cfri_fold_D_supplement
python cfri_holdout_v1/analysis/verify_reported_numbers.py
python cfri_candle_v1_exploratory/verify_package.py
```

The GitHub Actions workflow runs these checks on each push. The candle verifier uses only the Python standard library and checks its source hashes, result files, and all 816 condition shards. `SHA256SUMS.txt` records the packaged file bytes. A later data download may differ because the provider can revise historical records.

## Data, citation, and license

Raw Yahoo Finance price and volume tables and private snapshots are excluded. The published files contain derived errors, mask identifiers, settings, diagnostics, and hashes of the input data. The acquisition and freeze receipts are in the relevant study folders. Never add local `raw_do_not_publish`, `raw_cache`, or private snapshot folders to the public repository.

The citation metadata are in [`CITATION.cff`](CITATION.cff). The code is under the [MIT License](LICENSE). See each study folder for its data and result provenance.

**Author:** Kurban Kotan, Manisa Celal Bayar University. [ORCID 0000-0002-6660-0565](https://orcid.org/0000-0002-6660-0565).
