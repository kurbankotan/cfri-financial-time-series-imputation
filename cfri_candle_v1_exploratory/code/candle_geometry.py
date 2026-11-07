"""Exploratory candle-coordinate alternative to CFRI's independent price fits.

The method learns OHLC geometry from pseudo-masked *training* bars.  It never
uses an originally hidden training price as a target, and inference builds its
features only after hiding the requested cells.  The caller retains the frozen
CFRI volume rule and applies the same exact OHLC projection to all comparators.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

import cfri_core as core


@dataclass(frozen=True)
class CandleModel:
    scaler: StandardScaler
    ridge: Ridge
    training_rows: int


def _masked_design(raw: np.ndarray, hidden: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return predictors and a visible-only log-linear price anchor.

    Four relative log prices, four mask bits, and each field's log gap length
    and fractional position make 16 predictors.  Centering by the interpolated
    open/close midpoint removes the asset's absolute price level.
    """
    raw = np.asarray(raw, dtype=float)
    hidden = np.asarray(hidden, dtype=bool)
    if raw.ndim != 2 or raw.shape != hidden.shape or raw.shape[1] < 4:
        raise ValueError("raw and hidden must be matching OHLC arrays")
    price_hidden = hidden[:, :4]
    observed = raw[:, :4][~price_hidden]
    if not np.isfinite(observed).all() or np.any(observed <= 0):
        raise ValueError("observed prices must be finite and positive")

    visible = raw[:, :4].copy()
    visible[price_hidden] = np.nan
    log_visible = np.log(visible)
    base_log = core.linear_fill(log_visible)
    anchor = 0.5 * (base_log[:, 0] + base_log[:, 3])

    length = np.zeros_like(base_log)
    position = np.zeros_like(base_log)
    for d in range(4):
        for start, stop in core.mask_runs(price_hidden[:, d]):
            width = stop - start
            length[start:stop, d] = math.log1p(width)
            position[start:stop, d] = np.arange(1, width + 1) / (width + 1)
    design = np.column_stack(
        (base_log - anchor[:, None], price_hidden.astype(float), length, position)
    )
    if design.shape != (len(raw), 16) or not np.isfinite(design).all():
        raise AssertionError("invalid candle design")
    return design, anchor


def _candle_targets(prices: np.ndarray, anchor: np.ndarray) -> np.ndarray:
    """Coordinates: midpoint, signed body, and nonnegative upper/lower wicks."""
    log_prices = np.log(np.asarray(prices, dtype=float))
    o, h, l, c = (log_prices[:, j] for j in range(4))
    midpoint = 0.5 * (o + c)
    body = c - o
    upper = h - np.maximum(o, c)
    lower = np.minimum(o, c) - l
    if np.any(upper < -1e-6) or np.any(lower < -1e-6):
        raise ValueError("training labels violate OHLC order")
    return np.column_stack((midpoint - anchor, body, np.maximum(upper, 0), np.maximum(lower, 0)))


def fit_candle_model(
    train_raw: np.ndarray,
    train_mask: np.ndarray,
    ticker: str,
    fold: str,
    block: int,
    rate: float,
    seed: int,
    alpha: float = 10.0,
) -> CandleModel | None:
    """Fit a deterministic, training-only ridge model on two auxiliary masks.

    A complete OHLC label is used only when all four cells were visible under
    ``train_mask`` before the auxiliary mask.  The auxiliary mask is unioned
    with ``train_mask`` before constructing any predictors.  Return ``None``
    when there are too few legal examples for a stable fit.
    """
    train_raw = np.asarray(train_raw, dtype=float)
    train_mask = np.asarray(train_mask, dtype=bool)
    if train_raw.ndim != 2 or train_raw.shape != train_mask.shape or train_raw.shape[1] != 5:
        raise ValueError("train_raw and train_mask must be matching OHLCV arrays")
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be finite and positive")
    observed = train_raw[:, :4][~train_mask[:, :4]]
    if not np.isfinite(observed).all() or np.any(observed <= 0):
        raise ValueError("observed training prices must be finite and positive")

    matrices: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    complete_original = ~train_mask[:, :4].any(axis=1)
    for repetition in range(2):
        pseudo = core.strict_block_mask(
            train_raw.shape,
            rate,
            block,
            core.auxiliary_seed(ticker, fold, block, rate, seed, repetition),
        )
        effective = train_mask | pseudo
        design, anchor = _masked_design(train_raw, effective)
        selected = complete_original & pseudo[:, :4].any(axis=1) & (~effective[:, :4]).any(axis=1)
        if selected.any():
            matrices.append(design[selected])
            labels.append(_candle_targets(train_raw[selected, :4], anchor[selected]))
    if not matrices:
        return None
    x = np.vstack(matrices)
    y = np.vstack(labels)
    if len(x) < 60 or not np.isfinite(y).all():
        return None
    scaler = StandardScaler().fit(x)
    ridge = Ridge(alpha=float(alpha)).fit(scaler.transform(x), y)
    return CandleModel(scaler=scaler, ridge=ridge, training_rows=len(x))


def predict_candle_prices(
    raw: np.ndarray,
    hidden: np.ndarray,
    model: CandleModel | None,
    baseline_prices: np.ndarray,
) -> np.ndarray:
    """Predict positive OHLC prices and preserve every visible price exactly.

    Rows with no visible same-day OHLC price, or with no fitted model, use the
    supplied baseline.  The structural predictions may need the shared exact
    OHLC projection after visible prices are restored; this is intentionally a
    separate, identical postprocessing step for CFRI, SAITS, and this method.
    """
    raw = np.asarray(raw, dtype=float)
    hidden = np.asarray(hidden, dtype=bool)
    baseline_prices = np.asarray(baseline_prices, dtype=float)
    if raw.ndim != 2 or raw.shape != hidden.shape or raw.shape[1] < 4:
        raise ValueError("raw and hidden must be matching OHLC arrays")
    if baseline_prices.shape != (len(raw), 4):
        raise ValueError("baseline_prices must have four price columns")
    if not np.isfinite(baseline_prices).all() or np.any(baseline_prices <= 0):
        raise ValueError("baseline prices must be finite and positive")
    observed = raw[:, :4][~hidden[:, :4]]
    if not np.isfinite(observed).all() or np.any(observed <= 0):
        raise ValueError("observed prices must be finite and positive")

    out = baseline_prices.copy()
    out[~hidden[:, :4]] = raw[:, :4][~hidden[:, :4]]
    if model is None:
        return out
    selected = hidden[:, :4].any(axis=1) & (~hidden[:, :4]).any(axis=1)
    if not selected.any():
        return out
    design, anchor = _masked_design(raw, hidden)
    pred = model.ridge.predict(model.scaler.transform(design[selected]))
    if pred.shape != (int(selected.sum()), 4):
        raise AssertionError("invalid candle prediction")
    # Bounding corrections prevents a rare extrapolation from making an
    # implausibly extreme or nonfinite OHLC bar.  The bounds are fixed a priori.
    midpoint = anchor[selected] + np.clip(pred[:, 0], -0.25, 0.25)
    body = np.clip(pred[:, 1], -0.25, 0.25)
    upper = np.clip(pred[:, 2], 0.0, 0.25)
    lower = np.clip(pred[:, 3], 0.0, 0.25)
    o = midpoint - 0.5 * body
    c = midpoint + 0.5 * body
    log_candidate = np.column_stack(
        (o, np.maximum(o, c) + upper, np.minimum(o, c) - lower, c)
    )
    candidate = np.exp(log_candidate)
    if not np.isfinite(candidate).all() or np.any(candidate <= 0):
        raise RuntimeError("candle model produced nonpositive or nonfinite prices")
    row_indices = np.flatnonzero(selected)
    for j in range(4):
        use = hidden[row_indices, j]
        out[row_indices[use], j] = candidate[use, j]
    out[~hidden[:, :4]] = raw[:, :4][~hidden[:, :4]]
    return out
