# Executed workflow: CFRI candle geometry v1

**Status:** retrospective description of an exploratory experiment. It is not
a prospective protocol, preregistration, or modification of the earlier frozen
CFRI protocols. Source and settings were fixed before this *particular Colab
run*, but the method was devised after 2026 held-out results were seen.

## Benchmark and partitions

- 16 held-out ETF targets: XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY,
  SPY, QQQ, IWM, EFA, EEM, IBB, IYR. The original 34-ETF peer pool is present
  in the verified reference, although this feature-mask candle comparison does
  not use the peer bridge.
- Training: 2015–2024. Validation: 2025. Test: January–September 2026, ending
  2026-09-30. These are the original held-out-asset partitions.
- Feature-wise masks only; block lengths 1, 2, 3, 5, 10, 20 trading days;
  rates 10%, 20%, 30%; seeds 11, 23, 37. Feasibility filters yield 51 paired
  conditions per ETF, 816 total. The original mask generator and seeds are
  preserved, and all train/validation/test mask SHA and cell counts match the
  original CFRI and SAITS reference shards.

## Fixed new method

Let log O, log H, log L, log C denote daily log prices. The model predicts four
coordinates: midpoint m=(log O+log C)/2, signed body b=log C−log O, upper wick
u=log H−max(log O,log C), and lower wick d=min(log O,log C)−log L.
Wicks are constrained nonnegative at reconstruction. Visible-only temporal
log interpolation supplies the anchor and gap-context predictors. Two
deterministic auxiliary masks create training labels only at originally
observed training OHLC rows. Multioutput Ridge uses alpha=10. Corrections are
clipped to fixed bounds; rows without any same-day visible price use the
original CFRI fallback. The observed price cells are restored exactly.

The original CFRI price rule uses alpha=10 and gain=0.75. Its volume rule uses
eta=0.5 unchanged for both candle variants. `candle_direct` uses the new price
candidate. `candle_half` uses a fixed 0.5/0.5 blend in log-price coordinates
with original CFRI. The same exact joint OHLC projection is then applied to
original CFRI and both candle candidates. SAITS V2 reference scores were
imported from the verified matching held-out run.

## Scoring and interpretation

NRMSE divides each masked-cell RMSE by the standard deviation estimated from
visible training observations. Scores are first averaged over the 51 feasible
conditions per ETF and then equally across the 16 ETFs. All-field NRMSE is
the unweighted average of open, high, low, close, and volume. OHLC-only NRMSE
averages the four prices; volume is shown separately. Both new variants and
both comparators are reported regardless of outcome, including per-asset,
gap-length, condition and feature tables. No significance threshold or
confirmatory success rule was applied to this exploratory run.

The experiment tests offline imputation, not forecasting. It does not test
whole-row or market-wide missingness for candle geometry. The private raw
Yahoo tables are omitted from this GitHub companion; data receipts contain
their hashes, and the Colab run verified them before scoring. The original
reference shards are also not duplicated as loose files here; the completed
original study archive and this run's reference manifests support provenance.
