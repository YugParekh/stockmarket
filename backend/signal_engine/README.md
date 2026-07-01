# Signal Engine — Backtest Report

This is an honest report on whether the technical-indicator-based prediction engines in
this package are trustworthy enough to present to real traders as a directional signal.
**Short answer: no, not as a standalone "trust the confidence number" signal** — see
Verdict below. This replaces the old `_prediction_from_series` in `backend/main.py`,
which output a hardcoded `min(95, max(55, ...))` confidence with no relationship to
actual historical accuracy.

All numbers below come from one specific run of `python -m signal_engine.backtest`
against a freshly-pulled dataset (cache cleared beforehand), reproduced end-to-end and
verified before writing this report.

## Methodology

- **Data**: real daily OHLCV from yfinance, ~8 years, for 8 liquid symbols: AAPL, MSFT,
  GOOGL, AMZN, NVDA, TSLA (large caps) and SPY, QQQ (index ETFs, included as a lower-noise
  sanity check).
- **Features**: 11 technical indicators computed via the `pandas-ta` library (0.4.71b0) —
  RSI-14, MACD histogram, Bollinger %B, ATR, OBV slope, SMA 20/50 crossover, EMA 20/50
  crossover, momentum over 5/10/20 days, and a volume z-score (concept adapted from
  `main.py`'s `_score_sentiment`, reimplemented independently). See "Why pandas-ta" below
  for the dependency tradeoff this involved.
- **Labels**: forward direction over 1-day and 5-day horizons (`close[t+h] > close[t]`).
  Labels are never used as features.
- **No lookahead**: walk-forward validation only. Data pooled across symbols and sorted
  by date; the first 2 calendar years are reserved purely for training. For every
  subsequent year Y, models are trained/scored using only data with `date < start of Y`,
  then evaluated on year Y. This repeats through the full history — every accuracy number
  below is out-of-sample. Verified directly by tests in
  `backend/tests/test_signal_engine_indicators.py` and `test_signal_engine_backtest.py`
  (indicators computed on a truncated series match the full series on the overlapping
  prefix; every walk-forward fold's train dates strictly precede its test dates).
- **Two engines compared on identical rows**: `rule_based.py` (fixed-weight, interpretable
  ensemble of 7 signed indicator signals) and `ml_model.py`
  (`HistGradientBoostingClassifier`, retrained annually on all 11 features).
- **Two naive baselines, same rows**: `always_up` (predict UP every time — a real baseline
  given equities drift upward over time) and `previous_day` (predict the same direction as
  the prior day's realized move).
- **Calibration**: `calibration.py` buckets predictions by conviction (distance of the
  predicted probability from 0.5) and reports the ACTUAL historical accuracy in each
  bucket — this is what "confidence" means in this system: a measured track record, not a
  formula.

## Results (n=13,048 out-of-sample predictions per engine per horizon)

### 1-day forward direction

| Approach | Accuracy |
|---|---|
| Rule-based | 51.24% |
| ML (gradient boosting) | 52.62% |
| Baseline: always predict UP | **53.66%** |
| Baseline: previous-day continuation | 49.63% |

### 5-day forward direction

| Approach | Accuracy |
|---|---|
| Rule-based | 53.85% |
| ML (gradient boosting) | 53.81% |
| Baseline: always predict UP | **56.62%** |
| Baseline: previous-day continuation | 50.08% |

**Neither engine beats the naive "always predict UP" baseline, at either horizon.** This
is because these 8 symbols had a strong upward drift over the backtest window — simply
assuming "stocks go up" captures more of that drift than either model's technical-
indicator signals do. This is a real, important finding, not a bug to explain away. (An
earlier hand-rolled, pandas-ta-free reimplementation of the same 10 core indicators was
cross-checked during development and landed within ~0.1 point of every number above —
this conclusion is not an artifact of one particular indicator implementation.)

### Calibration — and a real defect worth flagging

The ML model's calibration is roughly sane: accuracy generally rises from ~51% in its
lowest-conviction buckets to ~54-57% in its highest-conviction buckets, at both horizons.
Weak, but at least directionally honest.

The rule-based model's calibration is **inverted at the high end, at both horizons**: its
*most* confident bucket is *less* accurate than several less-confident buckets. At 1-day,
the top bucket scores 48.87% — worse than a coin flip — while a middle bucket scores
52.79%. At 5-day, the top bucket (51.50%) is also below several middle buckets (peak
57.45%). A model whose highest-conviction predictions are its least reliable is actively
misleading if its raw score were shown to a user as "confidence." This is why
`calibration.py` maps scores to bucket-measured accuracy rather than trusting the model's
own confidence claim — but it also means the rule-based engine's fixed weights need
rework before its raw score is a meaningful ranking signal at all.

### Per-symbol accuracy — full breakdown, both engines, both horizons

**1-day horizon**

| Symbol | Rule-based | ML | Always-up | Prev-day |
|---|---|---|---|---|
| AAPL | 50.77% | 50.58% | 52.97% | 49.17% |
| AMZN | 49.85% | 52.61% | 52.12% | 50.03% |
| GOOGL | 51.75% | 52.91% | 53.95% | 49.42% |
| MSFT | 50.83% | 51.81% | 52.30% | 48.80% |
| NVDA | 50.09% | 50.89% | 54.20% | 49.91% |
| QQQ | 52.97% | 55.06% | 56.10% | 50.03% |
| SPY | 52.61% | 54.87% | 55.06% | 49.42% |
| TSLA | 51.07% | 52.24% | 52.54% | 50.28% |

**5-day horizon**

| Symbol | Rule-based | ML | Always-up | Prev-day |
|---|---|---|---|---|
| AAPL | 54.81% | 52.79% | 56.04% | 51.99% |
| AMZN | 50.89% | 52.54% | 54.02% | 49.85% |
| GOOGL | 53.10% | 54.08% | 56.65% | 48.80% |
| MSFT | 53.40% | 54.87% | 56.59% | 49.42% |
| NVDA | 53.40% | 51.26% | 58.25% | 50.40% |
| QQQ | 55.98% | 57.27% | 59.35% | 49.60% |
| SPY | 56.22% | 59.04% | 60.64% | 49.23% |
| TSLA | 53.03% | **48.62%** | 51.44% | 51.38% |

Index ETFs (SPY, QQQ) are consistently the most "predictable" across every approach,
including the naive baselines — expected, since they average out single-stock
idiosyncratic noise and have the cleanest upward drift. TSLA is the most erratic: the ML
engine actually scores *below* a coin flip on TSLA at the 5-day horizon (48.62%), a
reminder that pooled/aggregate accuracy hides real per-symbol variance, some of it worse
than chance.

### Calibration tables — all 4 engine/horizon combinations

Buckets are quantile-based (~1,630 rows each). **Small buckets are noisy**: with n≈1,630
and accuracy near 50%, each bucket's accuracy has a standard error of roughly ±1.2
points, so 1-2 point differences between adjacent buckets are not necessarily meaningful.

**1-day, rule-based** (highest-conviction bucket is the *worst*, not the best):

| Strength range | n | Accuracy |
|---|---|---|
| 0.000–0.032 | 1631 | 50.15% |
| 0.032–0.065 | 1631 | 51.13% |
| 0.065–0.095 | 1631 | 51.69% |
| 0.095–0.124 | 1631 | 52.54% |
| 0.124–0.154 | 1631 | 52.79% |
| 0.154–0.190 | 1631 | 51.69% |
| 0.190–0.245 | 1631 | 51.07% |
| 0.245–0.479 (highest conviction) | 1631 | **48.87%** |

**1-day, ML** (mostly increasing, but not cleanly monotonic):

| Strength range | n | Accuracy |
|---|---|---|
| 0.000–0.017 | 1631 | 51.20% |
| 0.017–0.029 | 1630 | 51.04% |
| 0.029–0.039 | 1632 | 53.98% |
| 0.039–0.050 | 1631 | 51.62% |
| 0.050–0.062 | 1631 | 52.24% |
| 0.062–0.081 | 1631 | 53.34% |
| 0.081–0.120 | 1631 | 52.91% |
| 0.120–0.399 (highest conviction) | 1631 | 54.63% |

**5-day, rule-based** (peak accuracy is in the middle, not at the extreme):

| Strength range | n | Accuracy |
|---|---|---|
| 0.000–0.032 | 1631 | 53.16% |
| 0.032–0.065 | 1631 | 54.63% |
| 0.065–0.095 | 1631 | 52.54% |
| 0.095–0.124 | 1631 | 56.22% |
| 0.124–0.154 | 1631 | **57.45%** (best) |
| 0.154–0.190 | 1631 | 53.28% |
| 0.190–0.245 | 1631 | 52.05% |
| 0.245–0.479 (highest conviction) | 1631 | 51.50% |

**5-day, ML** (the most well-behaved / close to monotonic):

| Strength range | n | Accuracy |
|---|---|---|
| 0.000–0.023 | 1631 | 51.62% |
| 0.023–0.046 | 1631 | 51.20% |
| 0.046–0.067 | 1631 | 53.77% |
| 0.067–0.090 | 1631 | 54.14% |
| 0.090–0.117 | 1631 | 53.65% |
| 0.117–0.149 | 1631 | 54.63% |
| 0.149–0.202 | 1631 | 54.57% |
| 0.202–0.452 (highest conviction) | 1631 | **56.90%** (best) |

**Honest answer to "does an X%-confidence bucket actually hit ~X% of the time?"**: this
calibration is measuring something real — genuine historical accuracy within
score-strength buckets, not a formula — but it is not reliably monotonic for 3 of the 4
engine/horizon combinations (higher model conviction did not consistently mean higher
historical accuracy). Only the 5-day ML calibration behaves close to as one would hope.
No bucket across all 4 tables reaches 60% accuracy, so under no honest reading of this
data should a user ever see an 80-95%-style confidence number, which is exactly what the
current `main.py` formula fabricates today.

## Verdict

- **Do not present either engine's raw output as a trustworthy standalone trading
  signal.** Out-of-sample directional accuracy for both is in the low-to-mid 50s and
  neither clears the "just assume markets go up" baseline. This is the expected, honest
  outcome for daily-bar direction prediction from price/volume technical features alone —
  it is a genuinely hard problem, and a model claiming much better than this without a
  fundamentally different data source (order flow, alternative data, cross-asset signals)
  should be treated with suspicion, not admiration.
- **If shipped at all, ship the ML engine, not the rule-based one**, and only with
  calibrated confidence (never above ~57%, per the measured bucket accuracy) and explicit
  "weak signal" framing in the UI. The rule-based engine's inverted high-confidence
  calibration makes it actively worse than showing nothing.
- **Recommended framing for real traders**: replace "UP, 87% confidence" style output
  with something like "Weak bullish lean (~55% historical accuracy in similar conditions,
  vs. ~57% for simply assuming an uptrend)" — honest about the fact that this is a
  marginal edge at best, and sometimes not even that.
- This does not mean the broader analytics product is worthless — real price/news data,
  risk metrics (volatility, VaR), and transparent historical accuracy tracking are all
  legitimately useful to a trader even when the directional call itself is weak. The fix
  for "trustworthy" here is honesty about a hard problem, not a better-sounding number.

## Caveats and limitations

- **Daily-bar direction prediction is intrinsically hard.** Accuracy in the 49-59% range
  across both engines and both naive baselines is the expected, literature-consistent
  result for this class of problem, not evidence of a modeling mistake. Liquid, widely
  followed symbols are close to informationally efficient at the daily-bar horizon.
- **Survivorship / selection bias.** All 8 symbols (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA,
  SPY, QQQ) are large, currently-successful companies or broad index ETFs that trended
  upward over the backtest window. That is exactly why "always predict UP" is such a
  strong baseline here — it reflects which 8 tickers were chosen and what they actually
  did, not a general truth about market predictability.
- **Small effect sizes, real sampling noise.** Bucket-level and engine-vs-engine
  differences of 1-3 points, on samples of ~1,600-13,000 rows, are within or near the
  range of sampling noise. Don't over-read small gaps as meaningful.
- **Transaction costs, slippage, and spread are not modeled at all.** None of these
  accuracy numbers say anything about real-world profitability; a strategy needs a
  meaningfully larger directional edge than ~53% to overcome realistic trading frictions.
- **Direction only, not magnitude.** A correct call ahead of a −0.01% move and a correct
  call ahead of a +5% move are scored identically.
- **Annual retraining cadence, model choice, and feature set are judgment calls**, not
  swept/tuned hyperparameters — this avoids overfitting the backtest to this specific
  report, but also means the numbers above are one reasonable configuration, not a ceiling
  or floor on what's achievable with this general approach.
- **~8 years / 8 symbols is a small backtest by quantitative-research standards.** It
  spans one broad market regime (a long bull run including the 2020 COVID crash/recovery
  and the 2022 bear market) and may not generalize to other symbols, periods, or genuinely
  novel regimes.

## Why pandas-ta

`pandas-ta` is unmaintained and imports `numpy.NaN`, an attribute removed in numpy>=1.24,
which causes an immediate `ImportError` against a plain numpy 2.x install. This was hit
and resolved directly, not assumed away:

1. `pip install pandas-ta` installs **pandas-ta 0.4.71b0**, which resolves against numpy
   2.2.6 (this project's numpy was at 2.5.0 beforehand; 2.2.6 still satisfies every other
   dependency's requirements, verified by the full test suite passing).
2. Adding `numpy.NaN = numpy.nan` immediately before `import pandas_ta` (top of
   `indicators.py`) fixes the import. `ta.rsi`, `ta.macd`, `ta.bbands`, `ta.atr`, `ta.obv`,
   `ta.sma`, and `ta.ema` were verified against synthetic OHLCV data (correct output
   shape, sane bounds, no lookahead — see `test_signal_engine_indicators.py`) before being
   relied on for the real backtest.
3. **Tradeoff, stated plainly**: this makes indicators.py depend on an unmaintained
   package via a monkeypatch, with an implicit numpy-version sensitivity not otherwise
   needed elsewhere in this codebase. That is a real ongoing maintenance cost. It was kept
   over a full hand-rolled reimplementation because (a) the shim is verified to work now,
   (b) a hand-rolled cross-check during development landed within ~0.1 point of every
   number in this report, so there's no accuracy reason to prefer one over the other, and
   (c) `pandas-ta` gives EMA crossover "for free" alongside SMA crossover. If `pandas-ta`
   breaks on a future numpy release, `indicators.py`'s public interface
   (`build_features(df) -> DataFrame[FEATURE_COLUMNS]`) is narrow enough that swapping in
   hand-rolled formulas later is a contained, low-risk change — it would not touch
   `dataset.py`, `rule_based.py`, `ml_model.py`, `calibration.py`, or `backtest.py`.

## Tests

New tests, no network calls, synthetic OHLCV fixtures built in-test:

- `backend/tests/test_signal_engine_indicators.py` — feature-column presence/shape,
  RSI∈[0,100], Bollinger %B sanity bounds, ATR non-negativity, momentum columns matching
  manual `pct_change`, warm-up-period NaN behavior, and **no-lookahead leakage tests**:
  indicators computed on a truncated series vs. the full series are identical on the
  overlapping prefix, checked at several different truncation points.
- `backend/tests/test_signal_engine_calibration.py` — bucketing/accuracy computation
  against synthetic `(predicted_score, actual_outcome)` pairs with known ground truth
  (perfect predictor → 100%, random predictor → ~50%, an explicit two-regime construction
  recovers approximately the two known accuracy levels), plus `confidence_for` behavior
  including the extreme-score fallback case.
- `backend/tests/test_signal_engine_backtest.py` — the walk-forward split mechanism
  itself: for every fold, asserts `max(train dates) < min(test dates)` (the no-lookahead
  guarantee at the mechanism level), plus checks that the rule-based and ML engines score
  identical out-of-sample rows, that baselines share the same row set, and that
  insufficient history raises rather than silently producing garbage.

All 44 tests pass (`cd backend && source .venv/bin/activate && pytest tests/`), including
the pre-existing 16 characterization tests for `backend/main.py` — this work does not
touch `main.py` and has not changed its behavior.

## Reproducing this report

```bash
cd backend
source .venv/bin/activate
python -m signal_engine.backtest
```

Results are cached to `data_cache/` (yfinance OHLCV as parquet, per symbol/period) and
`data_cache/backtest_results/latest_backtest.json` (full metrics). Delete `data_cache/`
to force a fresh pull from yfinance. All 8 symbols were fetched successfully in the run
these numbers come from — no retries or failures.
