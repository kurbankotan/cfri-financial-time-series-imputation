# Expanded ITRI validation — locked external universe and protocol

The prespecified 34-ETF universe is in `asset_universe_v1.json` and the
evaluation decisions are in `PROTOCOL_v1.md`. Both were frozen on 2026-09-23
before any new ETF performance results were inspected.

This is a **new study**, not a rewrite of the archived 6,048-run experiment or
its reported figures. Results from the old and new mask generators must never
be pooled as if they came from one protocol.

## Why new data are required

The old 108 conditions are combinations of mask length, rate, and seed on only
two underlying index series. Altering seeds or using a different p-value cannot
turn them into 108 independent market samples. A wider, prespecified set of
underlying series and distinct chronological evaluation periods is needed for
an external-robustness claim. Shared market shocks can still correlate distinct
assets, so statistical analysis must preserve the asset/calendar grouping.

## Locked design before new test results

1. Specify the asset eligibility rules, data provider, symbols, date range,
   license, exclusion rules, and exact downloaded-file hashes before analysis.
   Avoid selecting assets based on ITRI test performance.
2. Keep the original BIST 30 and S&P 500 panels as development data. Before
   inspecting any new scores, designate other series as external test assets.
   The previously selected ITRI setting (`w=1, p=5`) stays locked for the
   primary transfer test. Do not reselect its window or pass count on those
   assets. Use per-asset chronological partitions; fit scalers and model
   weights on training data only. A validation partition may set early
   stopping and predeclared comparator choices, but test data may not guide
   any change. Report the exact tuning budget for every method.
3. Keep the original segment-based masks as a labeled legacy sensitivity
   analysis. Use `strict_block_mask` for the new main block-length experiment;
   report the observed maximal run-length distribution and any final partial
   run. Reuse the exact same mask array across methods for each condition.
4. Compare ITRI with interpolation/PCHIP and at least two dedicated temporal
   imputers, provisionally BRITS and SAITS. Their input windows, available
   context, training split, random seeds, and selection budgets must be stated.
5. Report each asset's and nonoverlapping test period's paired result, not
   just a grand mean. Aggregate mask seeds within each asset/period before
   inference. Assets exposed to common market shocks can remain dependent;
   account for asset groups and calendar periods rather than calling every
   symbol independent. Avoid population-level p-values if the final cluster
   count is too small or cross-market dependence remains high.
6. Decide whether the article is a carefully bounded benchmark or includes a
   genuine methodological extension. A stability-controlled variant may be
   tested, but its form and tuning must be fixed before the new held-out tests.
7. Publish exact code, environment, immutable input snapshots where licensing
   permits, hashes, exclusion logs, row-level results, and a rerun guide.

The manuscript, abstract, title, tables, and claims will be updated **only
after** the new experiments pass numerical and visual audits. No submission is
authorized by this protocol file.

## Received snapshot and classical experiment

The author's 2026-09-23 Colab download was audited without extracting or
republishing OHLCV. `received_snapshot_audit.json` records 34/34 eligible
assets, 68 verified raw/clean CSV hashes, and 94,044 total daily rows. The
prespecified 5-feature mask grid passed 486 shape/condition checks.

`run_classical_benchmark.py` compares linear interpolation, PCHIP, KNN-5,
chained ridge, and the archived ITRI `w=1,p=5` logic on each asset's three
nonoverlapping test periods. It records five feature-level errors per method
and condition, logs non-convergence warnings, uses observed-only training
statistics for scaling, refuses changed input hashes, and checkpoints by
asset/fold. Eight offline tests pass, including the longest/30% gap case. A
two-condition EWC pilot ran and resumed successfully; pilot scores are **not**
scientific results and must not enter the paper.

The readable Colab notebook is
`ITRI_classical_full_Colab_upload_on_run.ipynb`. Open it in Colab and select
**Run all** on a CPU runtime. After dependency/source setup, Colab asks the
author to upload exactly one private data ZIP. The notebook checks its SHA-256
against the audited snapshot, runs the full experiment, and downloads
`ITRI_classical_full_results.zip`, which contains results, code, protocol,
metadata, and a completion marker but no raw OHLCV. The notebook itself is
about 40 KB and does not embed private data.
It does not persist intermediate checkpoints across a Colab reset; if the
runtime disconnects, rerun from the start. Do not treat an incomplete output
as a final result. An A100 is not needed for these classical baselines.

The public-safe code can be uploaded to the repository separately, without
the private notebook or raw data snapshot. Verify final rights before sharing
any vendor history.

## Remaining implementation and checks

- Data-source rights, exact downloaded-file hashes, and QC exclusions cannot
  be settled until the first acquisition run. These are logged, not used to
  choose assets by their scores.
- Run the full classical notebook and independently reconcile every shard and
  per-feature/condition row. Build and validate the BRITS and SAITS comparison
  on the same locked panel/masks before revising manuscript claims or tables.
  A100 may help neural training; actual resource needs come from a pilot.
- Check a target journal's current SCIE/JCR category and fee policy before
  submission. Journal choice does not change this scientific protocol.
