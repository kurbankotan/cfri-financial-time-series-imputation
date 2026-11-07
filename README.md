# CFRI: financial time-series imputation

**CFRI** means **Cross-Feature Residual Interpolation**. This repository
preserves the ITRI baseline, CFRI studies, and an exploratory candle-coordinate
extension. It accompanies a manuscript revision draft. The methods reconstruct
historical gaps using observations before and after a missing time point;
they are offline imputers, not forecasting or trading systems.

## Study map

| Directory | What it contains | Status and main result |
|---|---|---|
| `itri_baseline/` | Original BIST 30/S&P 500 ITRI ablation code, Colab notebook, derived results and figures | Historical development baseline; the selected one-day, five-pass setting reached mean test NRMSE 0.198094 on that original study. |
| `itri_external_validation/classical/` | Public source, frozen protocol and notebook for the external 34-ETF classical comparison | Source archive; separate from the original ITRI mask protocol. |
| `itri_external_validation/neural/` | Public BRITS/SAITS source and neural protocol | Source archive; the plan was fixed after classical outcomes were seen. |
| `cfri_confirmatory_fold_D/` | CFRI code and derived scores for 34 ETFs in the 2026 Fold D evaluation | Four prespecified primary comparisons met their decision rules; the projection-equalized SAITS comparison did not (13/34 ETF wins). |
| `cfri_holdout_v1/` | CFRI code, Colab notebook, protocol and derived scores on 16 previously unused ETFs | Feature-mask H1 versus SAITS did not meet its 12/16 rule (9/16); whole-row H2 and H3 did (16/16 each). |
| `cfri_candle_v1_exploratory/` | Exact candle replay source, Colab notebook, paired score tables and 816 condition shards | **Exploratory** replay designed after 2026 holdout outcomes were seen; the fixed half blend improves original CFRI on 16/16 ETFs, but SAITS retains the lower OHLC mean. |

## Read the evidence in order

1. `itri_baseline/` defines the original iterative temporal regression method.
2. `cfri_confirmatory_fold_D/results/fold_D_report.md` gives the frozen
   comparison decisions and limitations.
3. `cfri_holdout_v1/results/holdout_report.md` gives the independent-asset
   feature-mask and whole-row findings, including the failed H1 comparison.
4. `cfri_candle_v1_exploratory/results/candle_report.md` reports the later
   candle experiment. It reuses verified identical 2026 data and masks and is
   **not** a new confirmatory holdout. Only feature-wise masks were replayed.

The candle half blend lowers the equal-ETF all-field mean NRMSE from 0.138867
for original CFRI to 0.135973. Against SAITS V2 it wins 11/16 ETFs on the
all-field mean, while SAITS has the lower OHLC-only mean (0.046838 versus
0.047293). The all-field advantage is inherited from the unchanged CFRI
volume score; it does not establish better price imputation than SAITS.

## Reproduce and verify

Each study folder contains its own instructions and dependencies. The original
ITRI experiment can be checked inside `itri_baseline/` with
`python scripts/verify_published_results.py` after installing that folder's
`requirements.txt`. The CFRI held-out and candle folders contain resumable
Colab notebooks. The candle folder has `verify_package.py` for its source,
score-shard and SHA integrity checks. `SHA256SUMS.txt` in this root records
every other public file in this package.

The original Fold D Colab notebook and frozen Word protocol were unavailable
in the local source archive used to build this package. Its exact six Python
source files and derived run outputs are preserved. The recorded protocol ID
is `CFRI-confirmatory-protocol-v1`; no newly written document is presented as
the pre-run frozen protocol. The held-out source freeze was local; publishing
it to GitHub after the run does not create a public pre-run timestamp.

## Data and GitHub upload

No raw Yahoo OHLCV tables or private data snapshots are redistributed here.
Receipts contain their SHA-256 hashes. A fresh download may differ from the
recorded data snapshot. Create a new repository named
`cfri-financial-time-series-imputation`, extract this ZIP, and use GitHub
Desktop or git to commit the **contents** of its same-named folder at the
repository root. GitHub's browser uploader accepts at most 100 files per
batch; this package has more than 500, so browser upload would require
multiple batches. Do not upload the outer folder as a subdirectory, and do
not add local raw-data caches. The archived notebook and Drive paths retain
their historical `ITRI` names so their executed source bytes and provenance
remain intact.

Repository publication is not a new preregistration of historical runs.
