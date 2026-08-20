"""
bt_engine.py — thin wrapper around backtesting.py that reuses the advisor's
core indicator logic. Runs the same daily SMA/RSI/ADX/ATR based long strategy
that drives the live scan, so what you backtest is close to what you'd trade.

Long-only (matches the "cash equity only" default). The advisor's own richer
backtester in engine.py still exists — this one is here specifically to produce
the interactive HTML report + parameter heat-map that backtesting.py generates.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from .analysis import sma, rsi, atr, adx


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the OHLCV columns are named as backtesting.py expects."""
    rename = {}
    for src, dst in [("Open", "Open"), ("High", "High"), ("Low", "Low"),
                     ("Close", "Close"), ("Volume", "Volume"),
                     ("open", "Open"), ("high", "High"), ("low", "Low"),
                     ("close", "Close"), ("volume", "Volume")]:
        if src in df.columns and dst not in df.columns:
            rename[src] = dst
    out = df.rename(columns=rename).copy()
    for req in ["Open", "High", "Low", "Close"]:
        if req not in out.columns:
            raise ValueError(f"Data missing column {req}")
    if "Volume" not in out.columns:
        out["Volume"] = 0
    out = out.dropna(subset=["Open", "High", "Low", "Close"])
    out.index = pd.to_datetime(out.index)
    return out


class SwingLong(Strategy):
    """Simple long-only swing strategy mirroring the advisor's TAKE conditions.

    Entry (all must be true):
      - Close above 20-SMA (short-term momentum)
      - Close above 200-SMA (long-term trend intact)
      - RSI(14) between 45 and 70 (not oversold, not overbought)
      - ADX(14) >= 20 (trending, not chop)

    Exit:
      - Fixed ATR-based stop (2x ATR) and target (5x ATR) → ~2.5:1 R:R
      - Or breakeven trail once +1R is reached
    """
    rsi_low = 45
    rsi_high = 70
    adx_min = 20
    atr_stop_mult = 2.0
    atr_target_mult = 5.0

    def init(self):
        close = pd.Series(self.data.Close, index=self.data.index)
        high = pd.Series(self.data.High, index=self.data.index)
        low = pd.Series(self.data.Low, index=self.data.index)

        self.sma20 = self.I(lambda: sma(close, 20).values, name="SMA20")
        self.sma200 = self.I(lambda: sma(close, 200).values, name="SMA200")
        self.rsi14 = self.I(lambda: rsi(close, 14).values, name="RSI14")
        self.atr14 = self.I(lambda: atr(high, low, close, 14).values, name="ATR14")
        # adx() returns a 3-tuple (adx, +DI, -DI); we only need the ADX line
        self.adx14 = self.I(lambda: adx(high, low, close, 14)[0].values, name="ADX14")

    def next(self):
        price = float(self.data.Close[-1])
        atr_now = float(self.atr14[-1]) if not np.isnan(self.atr14[-1]) else 0.0
        rsi_now = float(self.rsi14[-1]) if not np.isnan(self.rsi14[-1]) else 50.0
        adx_now = float(self.adx14[-1]) if not np.isnan(self.adx14[-1]) else 0.0
        s20 = float(self.sma20[-1]) if not np.isnan(self.sma20[-1]) else price
        s200 = float(self.sma200[-1]) if not np.isnan(self.sma200[-1]) else price

        if atr_now <= 0:
            return

        # entry
        if not self.position:
            entry_ok = (
                price > s20 and price > s200
                and self.rsi_low <= rsi_now <= self.rsi_high
                and adx_now >= self.adx_min
            )
            if entry_ok:
                stop = price - self.atr_stop_mult * atr_now
                target = price + self.atr_target_mult * atr_now
                # position size = 25% of equity per trade cap
                self.buy(sl=stop, tp=target, size=0.25)


def run_backtest(df: pd.DataFrame, cash: float = 100_000.0,
                 commission: float = 0.001) -> dict:
    """Run the SwingLong strategy on df and return a JSON-friendly summary.

    df: OHLCV DataFrame indexed by date.
    cash: starting capital.
    commission: fractional per-trade cost (0.001 = 0.1%).
    """
    data = _prep(df)
    if len(data) < 250:
        raise ValueError(f"Need at least 250 daily bars for the 200-SMA warm-up, got {len(data)}.")

    bt = Backtest(data, SwingLong, cash=cash, commission=commission,
                  finalize_trades=True)
    stats = bt.run()

    equity_curve = stats["_equity_curve"]["Equity"].astype(float)
    trades = stats["_trades"]

    # Serialize for JSON
    def _num(v):
        try:
            f = float(v)
            if np.isnan(f) or np.isinf(f):
                return None
            return f
        except (TypeError, ValueError):
            return None

    payload = {
        "start": str(data.index[0].date()),
        "end": str(data.index[-1].date()),
        "bars": int(len(data)),
        "starting_cash": float(cash),
        "final_equity": _num(stats.get("Equity Final [$]")),
        "peak_equity": _num(stats.get("Equity Peak [$]")),
        "return_pct": _num(stats.get("Return [%]")),
        "buy_hold_pct": _num(stats.get("Buy & Hold Return [%]")),
        "cagr_pct": _num(stats.get("CAGR [%]")),
        "sharpe": _num(stats.get("Sharpe Ratio")),
        "sortino": _num(stats.get("Sortino Ratio")),
        "calmar": _num(stats.get("Calmar Ratio")),
        "max_drawdown_pct": _num(stats.get("Max. Drawdown [%]")),
        "trades": int(stats.get("# Trades", 0) or 0),
        "win_rate_pct": _num(stats.get("Win Rate [%]")),
        "best_trade_pct": _num(stats.get("Best Trade [%]")),
        "worst_trade_pct": _num(stats.get("Worst Trade [%]")),
        "avg_trade_pct": _num(stats.get("Avg. Trade [%]")),
        "exposure_time_pct": _num(stats.get("Exposure Time [%]")),
        "kelly": _num(stats.get("Kelly Criterion")),
        # Sparkline: down-sample equity curve to ~120 points for a light plot
        "equity_series": _downsample(equity_curve, 120),
        "trades_table": _trades_to_list(trades),
    }
    return payload


def render_html_report(df: pd.DataFrame, cash: float, out_path: Path) -> None:
    """Run the strategy and write backtesting.py's interactive Bokeh HTML report."""
    data = _prep(df)
    bt = Backtest(data, SwingLong, cash=cash, commission=0.001, finalize_trades=True)
    bt.run()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bt.plot(filename=str(out_path), open_browser=False, resample=False)


def _num(v):
    try:
        f = float(v)
        if np.isnan(f) or np.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _stats_summary(stats) -> dict:
    """Extract the fields we compare across optimizer runs."""
    return {
        "sharpe": _num(stats.get("Sharpe Ratio")),
        "return_pct": _num(stats.get("Return [%]")),
        "trades": int(stats.get("# Trades", 0) or 0),
        "win_rate_pct": _num(stats.get("Win Rate [%]")),
        "max_drawdown_pct": _num(stats.get("Max. Drawdown [%]")),
    }


def run_optimize(df: pd.DataFrame, cash: float = 100_000.0,
                 method: str = "sambo",
                 max_tries: int = 60) -> dict:
    """Sweep SwingLong's RSI/ADX thresholds against 5y of data.

    Grid (kept small so 20-60s runtime holds up):
      rsi_low  in 35..50 step 5
      rsi_high in 65..80 step 5
      adx_min  in 15..30 step 5
    Constraint: rsi_low < rsi_high.

    Maximizes Sharpe. Tries SAMBO first (default optimizer of backtesting.py),
    falls back to a plain grid search if the sambo extra is not installed.

    Returns a JSON-friendly dict with the winner, the class-default baseline,
    a heatmap aggregated over adx_min, and metadata about the run.
    """
    data = _prep(df)
    if len(data) < 250:
        raise ValueError(
            f"Need at least 250 daily bars for the 200-SMA warm-up, got {len(data)}.")

    rsi_low_grid = list(range(35, 55, 5))     # [35, 40, 45, 50]
    rsi_high_grid = list(range(65, 85, 5))    # [65, 70, 75, 80]
    adx_min_grid = list(range(15, 35, 5))     # [15, 20, 25, 30]

    def _constraint(p) -> bool:
        return p.rsi_low < p.rsi_high

    total_valid = sum(
        1 for a in rsi_low_grid for b in rsi_high_grid for c in adx_min_grid
        if a < b
    )

    # --- Baseline (class defaults) ---
    bt_base = Backtest(data, SwingLong, cash=cash, commission=0.001,
                       finalize_trades=True)
    base_stats = bt_base.run()
    baseline = _stats_summary(base_stats)

    # --- Optimizer ---
    bt = Backtest(data, SwingLong, cash=cash, commission=0.001,
                  finalize_trades=True)

    method_used = method
    heatmap_series = None
    best_stats = None

    def _do_optimize(m: str):
        return bt.optimize(
            rsi_low=rsi_low_grid,
            rsi_high=rsi_high_grid,
            adx_min=adx_min_grid,
            maximize="Sharpe Ratio",
            method=m,
            max_tries=max_tries,
            constraint=_constraint,
            return_heatmap=True,
            random_state=42,
        )

    try:
        if method == "sambo":
            try:
                best_stats, heatmap_series = _do_optimize("sambo")
                method_used = "sambo"
            except (ImportError, ModuleNotFoundError):
                best_stats, heatmap_series = _do_optimize("grid")
                method_used = "grid"
        else:
            best_stats, heatmap_series = _do_optimize(method)
            method_used = method
    except (ImportError, ModuleNotFoundError):
        # Second-chance fallback if sambo import bubbled up later
        best_stats, heatmap_series = _do_optimize("grid")
        method_used = "grid"

    best_params = best_stats._strategy  # backtesting.py attaches params here
    best_summary = _stats_summary(best_stats)
    best_summary.update({
        "rsi_low": int(getattr(best_params, "rsi_low", 0)),
        "rsi_high": int(getattr(best_params, "rsi_high", 0)),
        "adx_min": int(getattr(best_params, "adx_min", 0)),
    })

    # --- Heatmap: aggregate over adx_min → mean Sharpe per (rsi_low, rsi_high) ---
    heatmap_cells: list[dict] = []
    if heatmap_series is not None and len(heatmap_series) > 0:
        try:
            hm = heatmap_series.copy()
            hm.name = "sharpe"
            grouped = (
                hm.reset_index()
                .groupby(["rsi_low", "rsi_high"])["sharpe"]
                .mean()
                .reset_index()
            )
            for _, row in grouped.iterrows():
                heatmap_cells.append({
                    "rsi_low": int(row["rsi_low"]),
                    "rsi_high": int(row["rsi_high"]),
                    "sharpe": _num(row["sharpe"]),
                })
        except Exception:
            heatmap_cells = []

    def _delta(a, b):
        if a is None or b is None:
            return None
        return a - b

    return {
        "best": best_summary,
        "baseline": baseline,
        "improvement_sharpe": _delta(best_summary.get("sharpe"), baseline.get("sharpe")),
        "improvement_return_pct": _delta(best_summary.get("return_pct"), baseline.get("return_pct")),
        "heatmap": heatmap_cells,
        "grid": {
            "rsi_low": rsi_low_grid,
            "rsi_high": rsi_high_grid,
            "adx_min": adx_min_grid,
        },
        "method_used": method_used,
        "attempts": int(total_valid),
        "start": str(data.index[0].date()),
        "end": str(data.index[-1].date()),
        "bars": int(len(data)),
    }


def _run_single(data: pd.DataFrame, cash: float, rsi_low: int, rsi_high: int,
                adx_min: int) -> dict | None:
    """Run one SwingLong backtest with the given params. Returns _stats_summary
    or None on failure. Used by run_walk_forward."""
    try:
        class _S(SwingLong):
            pass
        _S.rsi_low = rsi_low
        _S.rsi_high = rsi_high
        _S.adx_min = adx_min
        bt = Backtest(data, _S, cash=cash, commission=0.001, finalize_trades=True)
        stats = bt.run()
        return _stats_summary(stats)
    except Exception:
        return None


def run_walk_forward(df: pd.DataFrame, cash: float = 100_000.0,
                     train_bars: int = 252, test_bars: int = 63,
                     step_bars: int = 63) -> dict:
    """Walk-forward optimization: rolling in-sample train + out-of-sample test folds.

    For each fold:
      1. Grid-search (rsi_low, rsi_high, adx_min) on the TRAIN slice.
      2. Take the Sharpe-maximizing combo.
      3. Evaluate THAT combo on the immediately following TEST slice.
    Each fold's data is prepended with the trailing 200 bars from BEFORE the
    fold start so the 200-SMA warms up cleanly (SwingLong needs it).

    Returns per-fold IS/OOS metrics plus aggregate stats and an honest
    "robust params" recommendation (mode across folds) that we then verify
    on the full period as a sanity check. Compare against the naive
    in-sample-only best (what run_optimize would say) to see the overfit gap.
    """
    data = _prep(df)
    warmup = 200
    if len(data) < warmup + train_bars + test_bars:
        raise ValueError(
            f"Need at least {warmup + train_bars + test_bars} daily bars for walk-forward, "
            f"got {len(data)}.")

    # Grid: full 4×4×4 (64 combos, all rsi_low<rsi_high valid). If we detect
    # this is too slow after fold 1, we downsample to 3×3×3 for the rest.
    rsi_low_grid = [35, 40, 45, 50]
    rsi_high_grid = [65, 70, 75, 80]
    adx_min_grid = [15, 20, 25, 30]
    downsampled = False

    def _combos(lo_grid, hi_grid, adx_grid):
        for lo in lo_grid:
            for hi in hi_grid:
                if lo >= hi:
                    continue
                for ax in adx_grid:
                    yield (lo, hi, ax)

    folds: list[dict] = []
    import time as _time
    t0 = _time.time()
    # First valid fold_start is `warmup` so we can prepend 200 warmup bars
    # from BEFORE the fold's training window.
    fold_start = warmup
    while fold_start + train_bars + test_bars <= len(data):
        train_slice_start = fold_start
        train_slice_end = fold_start + train_bars
        test_slice_start = train_slice_end
        test_slice_end = test_slice_start + test_bars

        # Prepend the trailing 200 warmup bars so SMA200 is populated inside
        # the train (and test) windows. Backtest sees them but we only measure
        # trades entered within the intended window because entries below the
        # 200-SMA get filtered; the warmup bars simply prevent NaN-driven
        # skipping in the first ~200 bars of every fold.
        train_data = data.iloc[train_slice_start - warmup:train_slice_end].copy()
        test_data = data.iloc[test_slice_start - warmup:test_slice_end].copy()

        # In-sample sweep
        lo_g = rsi_low_grid if not downsampled else [35, 42, 50]
        hi_g = rsi_high_grid if not downsampled else [65, 72, 80]
        ax_g = adx_min_grid if not downsampled else [15, 22, 30]

        best = None
        best_params = None
        for (lo, hi, ax) in _combos(lo_g, hi_g, ax_g):
            s = _run_single(train_data, cash, lo, hi, ax)
            if s is None or s.get("sharpe") is None:
                continue
            if best is None or (s["sharpe"] is not None and s["sharpe"] > best["sharpe"]):
                best = s
                best_params = (lo, hi, ax)

        if best is None or best_params is None:
            fold_start += step_bars
            continue

        # Out-of-sample eval with the IS winner
        oos = _run_single(test_data, cash, *best_params)
        if oos is None:
            fold_start += step_bars
            continue

        folds.append({
            "train_start": str(data.index[train_slice_start].date()),
            "train_end": str(data.index[train_slice_end - 1].date()),
            "test_start": str(data.index[test_slice_start].date()),
            "test_end": str(data.index[test_slice_end - 1].date()),
            "is_best_params": {"rsi_low": int(best_params[0]),
                               "rsi_high": int(best_params[1]),
                               "adx_min": int(best_params[2])},
            "is_sharpe": best.get("sharpe"),
            "oos_sharpe": oos.get("sharpe"),
            "oos_return_pct": oos.get("return_pct"),
            "oos_trades": int(oos.get("trades") or 0),
            "oos_win_rate_pct": oos.get("win_rate_pct"),
        })

        # After fold 1, if we've already burned >30s, downsample the remaining
        # grid to keep the 90s budget.
        if len(folds) == 1 and (_time.time() - t0) > 30 and not downsampled:
            downsampled = True

        fold_start += step_bars

    elapsed = _time.time() - t0

    n = len(folds)
    if n == 0:
        return {
            "folds": [], "n_folds": 0,
            "warning": "No folds could be completed — data too short or too many failures.",
            "elapsed_sec": round(elapsed, 1),
        }

    is_sharpes = [f["is_sharpe"] for f in folds if f["is_sharpe"] is not None]
    oos_sharpes = [f["oos_sharpe"] for f in folds if f["oos_sharpe"] is not None]

    def _mean(xs): return float(np.mean(xs)) if xs else None
    def _median(xs): return float(np.median(xs)) if xs else None

    mean_oos = _mean(oos_sharpes)
    median_oos = _median(oos_sharpes)
    mean_is = _mean(is_sharpes)
    gap_mean = None
    if mean_is is not None and mean_oos is not None:
        gap_mean = mean_is - mean_oos

    # Majority-voted robust params (mode across folds)
    from collections import Counter
    combos = Counter((f["is_best_params"]["rsi_low"],
                      f["is_best_params"]["rsi_high"],
                      f["is_best_params"]["adx_min"]) for f in folds)
    (robust_tuple, robust_count) = combos.most_common(1)[0]
    robust_params = {
        "rsi_low": robust_tuple[0], "rsi_high": robust_tuple[1],
        "adx_min": robust_tuple[2], "picked_by_frac": round(robust_count / n, 3),
    }

    # Full-period sanity checks
    robust_full = _run_single(data, cash, *robust_tuple)
    baseline_full = _run_single(data, cash, 45, 70, 20)

    # In-sample-only best (what run_optimize would pick) on the full 5y
    is_only_best = None
    is_only_params = None
    for (lo, hi, ax) in _combos(rsi_low_grid, rsi_high_grid, adx_min_grid):
        s = _run_single(data, cash, lo, hi, ax)
        if s is None or s.get("sharpe") is None:
            continue
        if is_only_best is None or s["sharpe"] > is_only_best["sharpe"]:
            is_only_best = s
            is_only_params = (lo, hi, ax)

    warning = None
    warnings = []
    if n < 4:
        warnings.append(f"Only {n} folds — history too short to walk-forward meaningfully.")
    if gap_mean is not None and mean_oos is not None and gap_mean > 0 and mean_oos < 0.5 * gap_mean:
        warnings.append("Large IS→OOS Sharpe drop vs OOS level — likely overfitting.")
    if downsampled:
        warnings.append("Grid was downsampled to 3×3×3 after fold 1 to hold the 90s budget.")
    if warnings:
        warning = " ".join(warnings)

    def _num(v):
        try:
            f = float(v)
            if np.isnan(f) or np.isinf(f):
                return None
            return f
        except (TypeError, ValueError):
            return None

    return {
        "folds": folds,
        "n_folds": n,
        "mean_oos_sharpe": _num(mean_oos),
        "median_oos_sharpe": _num(median_oos),
        "mean_is_sharpe": _num(mean_is),
        "is_oos_gap_mean": _num(gap_mean),
        "robust_params": robust_params,
        "robust_full_period_sharpe": _num((robust_full or {}).get("sharpe")),
        "robust_full_period_return_pct": _num((robust_full or {}).get("return_pct")),
        "baseline_full_period_sharpe": _num((baseline_full or {}).get("sharpe")),
        "baseline_full_period_return_pct": _num((baseline_full or {}).get("return_pct")),
        "in_sample_only_best": {
            "params": ({"rsi_low": is_only_params[0], "rsi_high": is_only_params[1],
                        "adx_min": is_only_params[2]} if is_only_params else None),
            "full_period_sharpe": _num((is_only_best or {}).get("sharpe")),
            "full_period_return_pct": _num((is_only_best or {}).get("return_pct")),
        },
        "warning": warning,
        "elapsed_sec": round(elapsed, 1),
        "downsampled": downsampled,
        "train_bars": train_bars,
        "test_bars": test_bars,
        "step_bars": step_bars,
        "start": str(data.index[0].date()),
        "end": str(data.index[-1].date()),
        "bars": int(len(data)),
    }


def _downsample(series: pd.Series, n: int) -> list[dict]:
    if len(series) == 0:
        return []
    step = max(1, len(series) // n)
    idx = series.index[::step]
    vals = series.values[::step]
    return [{"t": str(t.date()) if hasattr(t, "date") else str(t), "v": float(v)}
            for t, v in zip(idx, vals)]


def _trades_to_list(trades_df: pd.DataFrame) -> list[dict]:
    if trades_df is None or len(trades_df) == 0:
        return []
    rows = []
    for _, r in trades_df.head(50).iterrows():
        rows.append({
            "entry_time": str(getattr(r.get("EntryTime"), "date", lambda: r.get("EntryTime"))()),
            "exit_time": str(getattr(r.get("ExitTime"), "date", lambda: r.get("ExitTime"))()),
            "size": float(r.get("Size", 0)),
            "entry_price": float(r.get("EntryPrice", 0)),
            "exit_price": float(r.get("ExitPrice", 0)),
            "pnl": float(r.get("PnL", 0)),
            "return_pct": float(r.get("ReturnPct", 0)) * 100,
        })
    return rows
