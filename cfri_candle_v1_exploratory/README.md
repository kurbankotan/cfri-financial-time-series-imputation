# CFRI candle geometry: exploratory matched replay

This directory accompanies the manuscript revision draft. It contains the exact
source embedded in the Colab notebook and the derived results of the completed
2026 held-out-asset feature-mask replay. **The candle method was designed after
the 2026 held-out results were inspected. This experiment is exploratory, not
an independently frozen confirmation.** Do not attach its gains to the earlier
confirmatory Fold D or held-out-asset hypothesis decisions.

## What was tested

The method jointly predicts log OHLC via midpoint, signed body, nonnegative
upper wick and nonnegative lower wick. It keeps the original CFRI volume rule,
uses the original exact OHLC projection for all comparable price predictions,
and preserves observed values. Both direct candle predictions and a fixed 50%
log-price blend with original CFRI were evaluated. No candidate or blend weight
was selected using the reported test scores.

The previous 16-target-ETF run at `MyDrive/ITRI/CFRI_holdout_v1_local` was
verified and reused read-only. All 816 feature-mask conditions, source hashes,
input-frame hashes, mask hashes/counts, CPU scores and SAITS scores matched that
reference. The old benchmark's private raw Yahoo tables are **not** in this
public package. Source and reference receipts record their SHA-256 digests.

| Equal-ETF macro NRMSE | All five fields | OHLC only | Volume |
|---|---:|---:|---:|
| Original CFRI | 0.138867 | 0.050910 | 0.490697 |
| Candle direct | 0.136280 | 0.047676 | 0.490697 |
| Candle 50% blend | 0.135973 | 0.047293 | 0.490697 |
| Projected SAITS V2 | 0.139900 | 0.046838 | 0.512149 |

The fixed blend improves the original CFRI mean on all 16 ETFs and lowers
OHLC-only NRMSE by 7.10%. Against SAITS it wins the all-field ETF mean in
11/16 ETFs, while SAITS still has the lower OHLC-only macro mean. The candle
method's all-field lead over SAITS comes from the unchanged CFRI volume result. This is
not evidence that candle geometry is generally superior to SAITS for prices.
The experiment did not evaluate whole-row outages for the new method.

## Directory map

- `code/`: byte-identical source from the completed Colab run, including the
  unchanged original held-out-asset modules and the new candle modules.
- `CFRI_candle_v1_Colab.ipynb`: self-contained resumable Colab notebook.
- `results/`: human-readable report, JSON summary, CSV score tables, source and
  reference receipts and manifests. `CFRI_candle_v1_results_full.zip` contains
  the 816 per-condition JSON score shards and SHA sidecars. It excludes raw data.
- `PROTOCOL.md`: accurate description of the executed exploratory workflow.
- `SHA256SUMS.txt`: SHA-256 digest of every other file in this directory.
- `verify_package.py`: verifies this directory and the nested results ZIP using
  only the Python standard library.

## Reproduce or inspect

Run `python verify_package.py` from this directory to check package integrity.
For a Colab rerun, open `CFRI_candle_v1_Colab.ipynb` and run all cells. The
notebook stores progress in a separate Drive root under
`MyDrive/ITRI/CFRI_candle_v1_exploratory`. If the old private reference remains
complete, CPU plus standard RAM is enough. Otherwise it reacquires data and
reruns CFRI and SAITS on the same snapshot; an A100 GPU is recommended for
that fresh reference path. The notebook resumes verified checkpoints after an
interruption and downloads the final results ZIP automatically.

Do not present any future rerun on the same 2026 assets as an independent
confirmation. A new locked study should use a new market period or new assets
and add whole-row missingness, with price-specific metrics reported separately.
