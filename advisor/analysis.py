"""
advisor.analysis
================
The technical-analysis layer, merging four concerns into one file:

  1. **Indicators** - a pure-pandas TA engine (RSI, MACD, ATR, ADX, Bollinger,
     OBV, VWAP). Wilder smoothing uses the exact SMA-seeded recursion so the
     numbers match TradingView/ChartIQ rather than drifting on early bars.
  2. **Regime**     - market-regime detection (trending / ranging / volatile /
     unknown). Drives which setups in the signals layer are even allowed.
  3. **Signals**    - swing + intraday signal generators and confluence scoring.
     Signals are regime-aware: a lower-Bollinger tag is only a buy in a range,
     never in a downtrend; breakout signals are penalised in ranges.
  4. **Risk**       - position sizing (fixed-fractional / percent-risk), stops
     (ATR / structure), targets, multi-scenario reasoning, red-signal vetoes,
     expectancy, and fractional Kelly. Pure deterministic arithmetic.

Nothing here does I/O - it all operates on in-memory DataFrames and Python
numbers. That makes it fast, testable, and free of side effects.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from dataclasses import dataclass

from .core import (
    Direction, IndicatorSnapshot, PositionPlan, Regime, Scenario, Signal, Veto,
)


# =========================================================================== #
#  1.  INDICATORS
# =========================================================================== #
OPEN, HIGH, LOW, CLOSE, VOLUME = "open", "high", "low", "close", "volume"


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _wilder(series: pd.Series, period: int) -> pd.Series:
    """Wilder's smoothing (RMA). Exact SMA-seeded recursion, robust to NaNs."""
    arr = series.to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan)
    valid_idx = np.where(~np.isnan(arr))[0]
    if len(valid_idx) < period:
        return pd.Series(out, index=series.index)

    seed_pos = valid_idx[period - 1]
    out[seed_pos] = float(np.mean(arr[valid_idx[:period]]))
    inv = 1.0 / period
    for i in range(seed_pos + 1, len(arr)):
        prev = out[i - 1]
        if np.isnan(prev):
            continue
        cur = arr[i]
        out[i] = prev if np.isnan(cur) else prev + (cur - prev) * inv
    return pd.Series(out, index=series.index)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = _wilder(gain, period)
    avg_loss = _wilder(loss, period)
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    out = out.where(avg_loss != 0.0, 100.0)
    return out


def macd(close: pd.Series, fast: int = 12, slow: int = 26,
         signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Returns (macd_line, signal_line, histogram)."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range (Wilder)."""
    return _wilder(true_range(high, low, close), period)


def bollinger(close: pd.Series, period: int = 20,
              std_mult: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Returns (upper, mid, lower, width). Population std (Bollinger's original)."""
    mid = sma(close, period)
    sd = close.rolling(window=period, min_periods=period).std(ddof=0)
    upper = mid + std_mult * sd
    lower = mid - std_mult * sd
    width = (upper - lower) / mid.replace(0.0, np.nan)
    width = width.clip(lower=0.0, upper=5.0)
    return upper, mid, lower, width


def adx(high: pd.Series, low: pd.Series, close: pd.Series,
        period: int = 14) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Average Directional Index. Returns (adx, plus_di, minus_di)."""
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)

    tr = true_range(high, low, close)
    atr_ = _wilder(tr, period)

    plus_di = 100.0 * _wilder(plus_dm, period) / atr_.replace(0.0, np.nan)
    minus_di = 100.0 * _wilder(minus_dm, period) / atr_.replace(0.0, np.nan)
    plus_di = plus_di.clip(0.0, 100.0)
    minus_di = minus_di.clip(0.0, 100.0)

    di_sum = (plus_di + minus_di).replace(0.0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / di_sum
    adx_ = _wilder(dx, period).clip(0.0, 100.0)
    return adx_, plus_di, minus_di


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume."""
    direction = np.sign(close.diff().fillna(0.0))
    return (direction * volume).cumsum()


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
         session_reset: bool = True) -> pd.Series:
    """Volume-Weighted Average Price. Resets each session for intraday data."""
    typical = (high + low + close) / 3.0
    pv = typical * volume

    if session_reset and isinstance(close.index, pd.DatetimeIndex):
        day = close.index.normalize()
        cum_pv = pv.groupby(day).cumsum()
        cum_vol = volume.groupby(day).cumsum()
    else:
        cum_pv = pv.cumsum()
        cum_vol = volume.cumsum()
    return cum_pv / cum_vol.replace(0.0, np.nan)


def compute_indicators(df: pd.DataFrame, include_vwap: bool = False) -> pd.DataFrame:
    """Enrich an OHLCV DataFrame with every indicator column. Returns a copy."""
    _validate(df)
    out = df.copy()

    out["sma_20"] = sma(out[CLOSE], 20)
    out["sma_50"] = sma(out[CLOSE], 50)
    out["sma_200"] = sma(out[CLOSE], 200)
    out["ema_20"] = ema(out[CLOSE], 20)

    out["rsi_14"] = rsi(out[CLOSE], 14)

    macd_line, macd_sig, macd_hist = macd(out[CLOSE])
    out["macd"] = macd_line
    out["macd_signal"] = macd_sig
    out["macd_hist"] = macd_hist

    bb_u, bb_m, bb_l, bb_w = bollinger(out[CLOSE])
    out["bb_upper"], out["bb_mid"], out["bb_lower"], out["bb_width"] = bb_u, bb_m, bb_l, bb_w

    out["atr_14"] = atr(out[HIGH], out[LOW], out[CLOSE], 14)
    out["atr_pct"] = out["atr_14"] / out[CLOSE].replace(0.0, np.nan)

    adx_, plus_di, minus_di = adx(out[HIGH], out[LOW], out[CLOSE], 14)
    out["adx_14"], out["plus_di"], out["minus_di"] = adx_, plus_di, minus_di

    out["obv"] = obv(out[CLOSE], out[VOLUME])
    # Baseline EXCLUDES the current bar (today's volume shouldn't be in its own avg).
    out["avg_volume_20"] = out[VOLUME].shift(1).rolling(20, min_periods=20).mean()

    out["recent_high_20"] = out[HIGH].rolling(20, min_periods=20).max()
    out["recent_low_20"] = out[LOW].rolling(20, min_periods=20).min()
    out["recent_high_52w"] = out[HIGH].rolling(252, min_periods=126).max()
    out["recent_low_52w"] = out[LOW].rolling(252, min_periods=126).min()

    if include_vwap:
        looks_daily = False
        if isinstance(out.index, pd.DatetimeIndex) and len(out.index) > 2:
            median_gap = pd.Series(out.index).diff().median()
            looks_daily = (median_gap is not None
                           and median_gap >= pd.Timedelta(hours=20))
        if looks_daily:
            import warnings
            warnings.warn(
                "include_vwap=True but the data looks daily. VWAP is only "
                "meaningful intraday; skipping it.",
                stacklevel=2)
        else:
            out["vwap"] = vwap(out[HIGH], out[LOW], out[CLOSE], out[VOLUME])

    return out


def snapshot(df_with_indicators: pd.DataFrame) -> IndicatorSnapshot:
    """Pull the most recent row of an indicator-enriched frame into a snapshot."""
    last = df_with_indicators.iloc[-1]

    def g(col: str):
        if col not in df_with_indicators.columns:
            return None
        v = last[col]
        return None if pd.isna(v) else float(v)

    return IndicatorSnapshot(
        close=float(last[CLOSE]),
        sma_20=g("sma_20"), sma_50=g("sma_50"), sma_200=g("sma_200"),
        ema_20=g("ema_20"), rsi_14=g("rsi_14"),
        macd=g("macd"), macd_signal=g("macd_signal"), macd_hist=g("macd_hist"),
        bb_upper=g("bb_upper"), bb_mid=g("bb_mid"), bb_lower=g("bb_lower"),
        bb_width=g("bb_width"),
        atr_14=g("atr_14"), atr_pct=g("atr_pct"),
        adx_14=g("adx_14"), plus_di=g("plus_di"), minus_di=g("minus_di"),
        vwap=g("vwap"), obv=g("obv"),
        avg_volume_20=g("avg_volume_20"), last_volume=g(VOLUME),
        recent_high_20=g("recent_high_20"), recent_low_20=g("recent_low_20"),
        recent_high_52w=g("recent_high_52w"), recent_low_52w=g("recent_low_52w"),
    )


def _validate(df: pd.DataFrame) -> None:
    required = {OPEN, HIGH, LOW, CLOSE, VOLUME}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"DataFrame is missing required columns: {sorted(missing)}. "
            f"Got: {sorted(df.columns)}"
        )
    if len(df) < 2:
        raise ValueError("Need at least 2 rows of data to compute indicators.")


def resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample an OHLCV frame to a higher timeframe (e.g. 'W' weekly)."""
    if not isinstance(df.index, pd.DatetimeIndex):
        return df.iloc[0:0]
    agg = df.resample(rule).agg(
        {OPEN: "first", HIGH: "max", LOW: "min", CLOSE: "last", VOLUME: "sum"}
    )
    return agg.dropna(subset=[OPEN, HIGH, LOW, CLOSE])


def higher_tf_trend(df: pd.DataFrame, rule: str = "W",
                    fast: int = 10, slow: int = 30) -> str:
    """Direction of the HIGHER timeframe trend. Returns 'up', 'down', or 'none'."""
    res = resample_ohlc(df, rule)
    if len(res) < slow + 1:
        return "none"
    c = res[CLOSE]
    fast_ma = c.rolling(fast).mean().iloc[-1]
    slow_ma = c.rolling(slow).mean().iloc[-1]
    last = c.iloc[-1]
    if pd.isna(fast_ma) or pd.isna(slow_ma) or pd.isna(last):
        return "none"
    if last > fast_ma > slow_ma:
        return "up"
    if last < fast_ma < slow_ma:
        return "down"
    return "none"


# =========================================================================== #
#  2.  REGIME
# =========================================================================== #
ADX_TREND = 25.0
ADX_RANGE = 20.0
ATR_PCTL_VOLATILE = 0.80
ATR_LOOKBACK = 100
DI_GAP = 3.0
VOL_SMOOTH_BARS = 3
VOL_PERSIST_BARS = 2


@dataclass
class RegimeRead:
    regime: Regime
    adx: float | None
    atr_pct: float | None
    atr_percentile: float | None
    bb_width: float | None
    explanation: str


def classify_regime(df_with_indicators: pd.DataFrame) -> RegimeRead:
    """Classify the current regime from an indicator-enriched DataFrame."""
    last = df_with_indicators.iloc[-1]
    adx = _f(last.get("adx_14"))
    plus_di = _f(last.get("plus_di"))
    minus_di = _f(last.get("minus_di"))
    atr_pct = _f(last.get("atr_pct"))
    bb_width = _f(last.get("bb_width"))

    atr_percentile = None
    elevated_persisted = False
    if "atr_pct" in df_with_indicators.columns and atr_pct is not None:
        col = df_with_indicators["atr_pct"].dropna()
        recent = col.tail(ATR_LOOKBACK)
        if len(recent) >= 20:
            smoothed_cur = float(col.tail(VOL_SMOOTH_BARS).mean())
            atr_percentile = float((recent <= smoothed_cur).mean())
            thresh = float(recent.quantile(ATR_PCTL_VOLATILE))
            median = float(recent.median())
            last_raw = col.tail(VOL_PERSIST_BARS)
            elevated_persisted = (
                len(last_raw) >= VOL_PERSIST_BARS
                and bool((last_raw >= thresh).all())
                and median > 0 and bool((last_raw >= 1.4 * median).all())
            )

    bb_elevated = None
    if "bb_width" in df_with_indicators.columns and bb_width is not None:
        bw = df_with_indicators["bb_width"].dropna().tail(ATR_LOOKBACK)
        if len(bw) >= 20:
            bb_elevated = bool(bb_width >= bw.quantile(ATR_PCTL_VOLATILE))

    if atr_percentile is not None and atr_percentile >= ATR_PCTL_VOLATILE and elevated_persisted:
        confirm = " (Bollinger width confirms.)" if bb_elevated else \
                  " (Bollinger width does not confirm - treat as borderline.)" \
                  if bb_elevated is False else ""
        return RegimeRead(
            regime=Regime.VOLATILE,
            adx=adx, atr_pct=atr_pct, atr_percentile=atr_percentile, bb_width=bb_width,
            explanation=(
                f"Volatility is elevated and persistent (smoothed ATR ~{atr_pct*100:.2f}% "
                f"of price, {atr_percentile*100:.0f}th percentile of the last "
                f"{ATR_LOOKBACK} bars).{confirm} Reduce size and widen stops; many "
                f"setups are unreliable here."
            ),
        )

    if adx is None:
        return RegimeRead(
            regime=Regime.UNKNOWN, adx=adx, atr_pct=atr_pct,
            atr_percentile=atr_percentile, bb_width=bb_width,
            explanation="Not enough data to read trend strength (ADX unavailable).",
        )

    if adx >= ADX_TREND:
        if plus_di is None or minus_di is None:
            return RegimeRead(
                Regime.UNKNOWN, adx, atr_pct, atr_percentile, bb_width,
                explanation=f"ADX {adx:.1f} signals a trend but DI values are "
                            f"unavailable to confirm the side.")
        gap = plus_di - minus_di
        if gap >= DI_GAP:
            reg = Regime.TRENDING_UP
            expl = (
                f"Strong uptrend: ADX {adx:.1f} (>25) with +DI {plus_di:.1f} clearly "
                f"over -DI {minus_di:.1f}. Trend-following longs are favoured; "
                f"fade-the-trend setups are discouraged."
            )
        elif gap <= -DI_GAP:
            reg = Regime.TRENDING_DOWN
            expl = (
                f"Strong downtrend: ADX {adx:.1f} (>25) with -DI {minus_di:.1f} clearly "
                f"over +DI {plus_di:.1f}. Longs face a headwind; be very selective."
            )
        else:
            return RegimeRead(
                Regime.UNKNOWN, adx, atr_pct, atr_percentile, bb_width,
                explanation=(
                    f"ADX {adx:.1f} shows trend strength but +DI ({plus_di:.1f}) and "
                    f"-DI ({minus_di:.1f}) are within {DI_GAP:.0f} of each other - the "
                    f"direction isn't decided. Wait for one side to take control."
                ),
            )
        return RegimeRead(reg, adx, atr_pct, atr_percentile, bb_width, expl)

    if adx < ADX_RANGE:
        return RegimeRead(
            Regime.RANGING, adx, atr_pct, atr_percentile, bb_width,
            explanation=(
                f"Range / chop: ADX {adx:.1f} (<20) means no dominant trend. "
                f"Breakouts often fail; mean-reversion near support/resistance is "
                f"the higher-odds play, but tighten expectations."
            ),
        )

    return RegimeRead(
        Regime.UNKNOWN, adx, atr_pct, atr_percentile, bb_width,
        explanation=(
            f"Transitional: ADX {adx:.1f} sits between 20 and 25 - the market is "
            f"deciding. Wait for confirmation before committing size."
        ),
    )


def _f(v) -> float | None:
    if v is None or pd.isna(v):
        return None
    return float(v)


# =========================================================================== #
#  3.  SIGNALS
# =========================================================================== #
def _crossed_above(series: pd.Series, other: pd.Series) -> bool:
    if len(series) < 2:
        return False
    a0, a1 = series.iloc[-2], series.iloc[-1]
    b0, b1 = other.iloc[-2], other.iloc[-1]
    if pd.isna(a0) or pd.isna(a1) or pd.isna(b0) or pd.isna(b1):
        return False
    return a0 <= b0 and a1 > b1


def _crossed_below(series: pd.Series, other: pd.Series) -> bool:
    if len(series) < 2:
        return False
    a0, a1 = series.iloc[-2], series.iloc[-1]
    b0, b1 = other.iloc[-2], other.iloc[-1]
    if pd.isna(a0) or pd.isna(a1) or pd.isna(b0) or pd.isna(b1):
        return False
    return a0 >= b0 and a1 < b1


def _ok(*vals) -> bool:
    return all(v is not None and not pd.isna(v) for v in vals)


def _last_two_same_session(df: pd.DataFrame) -> bool:
    if not isinstance(df.index, pd.DatetimeIndex) or len(df.index) < 2:
        return False
    return df.index[-1].normalize() == df.index[-2].normalize()


def _persisted_side(close: pd.Series, ma: pd.Series, above: bool, bars: int = 2) -> bool:
    if len(close) < bars:
        return False
    c = close.iloc[-bars:]
    m = ma.iloc[-bars:]
    if c.isna().any() or m.isna().any():
        return False
    return bool((c > m).all()) if above else bool((c < m).all())


def swing_signals(df: pd.DataFrame, regime: "Regime | None" = None,
                  htf: str | None = None) -> list[Signal]:
    """Generate swing-trade evidence from an indicator-enriched daily frame."""
    s: list[Signal] = []
    last = df.iloc[-1]
    close = float(last["close"])

    sma50, sma200 = last.get("sma_50"), last.get("sma_200")
    sma20 = last.get("sma_20")
    rsi = last.get("rsi_14")
    macd_line, macd_sig = last.get("macd"), last.get("macd_signal")
    bb_u, bb_l = last.get("bb_upper"), last.get("bb_lower")
    vol, avg_vol = last.get("volume"), last.get("avg_volume_20")
    hi20, lo20 = last.get("recent_high_20"), last.get("recent_low_20")
    hi52, lo52 = last.get("recent_high_52w"), last.get("recent_low_52w")
    trending_up = regime == Regime.TRENDING_UP
    trending_down = regime == Regime.TRENDING_DOWN
    ranging = regime == Regime.RANGING

    # --- 1) Long-term trend filter (price vs 200 SMA) ------------------- #
    if _ok(sma200):
        if _persisted_side(df["close"], df["sma_200"], above=True, bars=2):
            s.append(Signal("above_200sma", Direction.LONG, 0.20,
                            f"Price ({close:.1f}) has held above the 200-day SMA "
                            f"({sma200:.1f}) - long-term trend is up.", close - sma200))
        elif _persisted_side(df["close"], df["sma_200"], above=False, bars=2):
            s.append(Signal("below_200sma", Direction.SHORT, 0.20,
                            f"Price ({close:.1f}) has held below the 200-day SMA "
                            f"({sma200:.1f}) - long-term trend is down.", close - sma200))

    # --- 1b) Multi-timeframe alignment --------------------------------- #
    if htf == "up":
        s.append(Signal("htf_uptrend", Direction.LONG, 0.15,
                        "Higher timeframe (weekly) trend is up - supports longs."))
    elif htf == "down":
        s.append(Signal("htf_downtrend", Direction.SHORT, 0.15,
                        "Higher timeframe (weekly) trend is down - supports shorts."))

    # --- 2) Medium-term MA alignment (50 vs 200) ----------------------- #
    if _ok(sma50, sma200):
        if sma50 > sma200:
            s.append(Signal("golden_alignment", Direction.LONG, 0.15,
                            "50-SMA above 200-SMA (golden-cross structure)."))
        else:
            s.append(Signal("death_alignment", Direction.SHORT, 0.15,
                            "50-SMA below 200-SMA (death-cross structure)."))

    # --- 3) Price vs 20-SMA -------------------------------------------- #
    if _ok(sma20):
        if close > sma20:
            s.append(Signal("above_20sma", Direction.LONG, 0.08,
                            "Trading above the 20-day SMA (short-term strength)."))
        else:
            s.append(Signal("below_20sma", Direction.SHORT, 0.08,
                            "Trading below the 20-day SMA (short-term weakness)."))

    # --- 4) RSI momentum / reversal ------------------------------------ #
    if _ok(rsi):
        if rsi < 30:
            s.append(Signal("rsi_oversold", Direction.LONG, 0.15,
                            f"RSI {rsi:.0f} is oversold (<30) - bounce candidate.", rsi))
        elif rsi > 70:
            s.append(Signal("rsi_overbought", Direction.SHORT, 0.15,
                            f"RSI {rsi:.0f} is overbought (>70) - pullback risk.", rsi))
        elif rsi >= 55:
            s.append(Signal("rsi_bull_momentum", Direction.LONG, 0.07,
                            f"RSI {rsi:.0f} (>55) shows bullish momentum.", rsi))
        elif rsi <= 45:
            s.append(Signal("rsi_bear_momentum", Direction.SHORT, 0.07,
                            f"RSI {rsi:.0f} (<45) shows bearish momentum.", rsi))

    # --- 5) MACD cross ------------------------------------------------- #
    if "macd" in df.columns and "macd_signal" in df.columns:
        if _crossed_above(df["macd"], df["macd_signal"]):
            s.append(Signal("macd_bull_cross", Direction.LONG, 0.15,
                            "MACD just crossed above its signal line (fresh bullish momentum)."))
        elif _crossed_below(df["macd"], df["macd_signal"]):
            s.append(Signal("macd_bear_cross", Direction.SHORT, 0.15,
                            "MACD just crossed below its signal line (fresh bearish momentum)."))
        elif _ok(macd_line, macd_sig):
            if macd_line > macd_sig:
                s.append(Signal("macd_bull", Direction.LONG, 0.06,
                                "MACD is above its signal line."))
            else:
                s.append(Signal("macd_bear", Direction.SHORT, 0.06,
                                "MACD is below its signal line."))

    # --- 6) Bollinger location - GATED BY REGIME ----------------------- #
    if _ok(bb_l, bb_u):
        if close <= bb_l:
            if ranging or regime is None:
                s.append(Signal("bb_lower_touch", Direction.LONG, 0.10,
                                "Lower-Bollinger tag in a range - mean-reversion long."))
            elif trending_up:
                s.append(Signal("bb_pullback_uptrend", Direction.LONG, 0.06,
                                "Pullback to the lower band within an uptrend - "
                                "possible continuation buy."))
        elif close >= bb_u:
            if ranging or regime is None:
                s.append(Signal("bb_upper_touch", Direction.SHORT, 0.10,
                                "Upper-Bollinger tag in a range - mean-reversion short."))
            elif trending_down:
                s.append(Signal("bb_rally_downtrend", Direction.SHORT, 0.06,
                                "Rally to the upper band within a downtrend - "
                                "possible continuation short."))

    # --- 7) Support / resistance & breakouts (mutually exclusive) ------ #
    if _ok(hi20):
        if close >= hi20 * 0.995:
            s.append(Signal("breakout_20d_high", Direction.LONG, 0.10,
                            f"At/through the 20-day high ({hi20:.1f}) - upside breakout."))
        elif (ranging or regime is None) and close >= hi20 * 0.98:
            s.append(Signal("near_resistance", Direction.SHORT, 0.08,
                            f"Approaching the 20-day high ({hi20:.1f}) in a range - resistance."))
    if _ok(lo20):
        if close <= lo20 * 1.005:
            s.append(Signal("breakdown_20d_low", Direction.SHORT, 0.10,
                            f"At/through the 20-day low ({lo20:.1f}) - downside breakdown."))
        elif (ranging or regime is None) and close <= lo20 * 1.02:
            s.append(Signal("near_support", Direction.LONG, 0.08,
                            f"Approaching the 20-day low ({lo20:.1f}) in a range - support."))

    if _ok(hi52) and close >= hi52 * 0.98 and trending_up:
        s.append(Signal("near_52w_high", Direction.LONG, 0.08,
                        f"Within 2% of the 52-week high ({hi52:.1f}) - strong momentum."))
    if _ok(lo52) and close <= lo52 * 1.02 and trending_down:
        s.append(Signal("near_52w_low", Direction.SHORT, 0.08,
                        f"Within 2% of the 52-week low ({lo52:.1f}) - persistent weakness."))

    # --- 8) Volume confirmation ---------------------------------------- #
    if _ok(vol, avg_vol) and avg_vol > 0:
        ratio = vol / avg_vol
        chg = df["close"].pct_change().iloc[-1]
        if ratio >= 1.5 and _ok(chg) and np.isfinite(chg):
            if chg > 0:
                s.append(Signal("volume_confirm_up", Direction.LONG, 0.08,
                                f"Volume {ratio:.1f}x the 20-day average on an up day "
                                f"(conviction behind the move).", ratio))
            elif chg < 0:
                s.append(Signal("volume_confirm_down", Direction.SHORT, 0.08,
                                f"Volume {ratio:.1f}x average on a down day "
                                f"(distribution).", ratio))

    # --- 9) OBV confirmation / divergence ------------------------------ #
    if "obv" in df.columns and len(df) >= 25:
        obv_chg = df["obv"].iloc[-1] - df["obv"].iloc[-20]
        px_chg = close - df["close"].iloc[-20]
        if _ok(obv_chg, px_chg) and px_chg != 0:
            if px_chg > 0 and obv_chg > 0:
                s.append(Signal("obv_confirms_up", Direction.LONG, 0.06,
                                "OBV rising with price - volume confirms the advance."))
            elif px_chg > 0 and obv_chg < 0:
                s.append(Signal("obv_bearish_divergence", Direction.SHORT, 0.08,
                                "Price up but OBV falling - the advance lacks volume (divergence)."))
            elif px_chg < 0 and obv_chg < 0:
                s.append(Signal("obv_confirms_down", Direction.SHORT, 0.06,
                                "OBV falling with price - volume confirms the decline."))
            elif px_chg < 0 and obv_chg > 0:
                s.append(Signal("obv_bullish_divergence", Direction.LONG, 0.08,
                                "Price down but OBV rising - quiet accumulation (divergence)."))
    return s


def intraday_signals(df: pd.DataFrame, opening_range_bars: int = 6) -> list[Signal]:
    """Generate intraday evidence. Expects a frame with a 'vwap' column."""
    s: list[Signal] = []
    last = df.iloc[-1]
    close = float(last["close"])
    vwap = last.get("vwap")
    rsi = last.get("rsi_14")

    if _ok(vwap):
        same_session = _last_two_same_session(df)
        if close > vwap:
            s.append(Signal("above_vwap", Direction.LONG, 0.16,
                            f"Trading above VWAP ({vwap:.1f}) - intraday buyers in control.",
                            close - vwap))
            if same_session and "vwap" in df.columns and _crossed_above(df["close"], df["vwap"]):
                s.append(Signal("vwap_reclaim", Direction.LONG, 0.08,
                                "Just reclaimed VWAP from below (momentum shift up)."))
        else:
            s.append(Signal("below_vwap", Direction.SHORT, 0.16,
                            f"Trading below VWAP ({vwap:.1f}) - intraday sellers in control.",
                            close - vwap))
            if same_session and "vwap" in df.columns and _crossed_below(df["close"], df["vwap"]):
                s.append(Signal("vwap_lost", Direction.SHORT, 0.08,
                                "Just lost VWAP from above (momentum shift down)."))

    if isinstance(df.index, pd.DatetimeIndex) and len(df) > opening_range_bars:
        today = df.index.normalize() == df.index[-1].normalize()
        session = df[today]
        if len(session) > opening_range_bars:
            orb = session.iloc[:opening_range_bars]
            or_high, or_low = orb["high"].max(), orb["low"].min()
            if close > or_high:
                s.append(Signal("orb_breakout_up", Direction.LONG, 0.18,
                                f"Broke above the opening range high ({or_high:.1f})."))
            elif close < or_low:
                s.append(Signal("orb_breakout_down", Direction.SHORT, 0.18,
                                f"Broke below the opening range low ({or_low:.1f})."))

    if _ok(rsi):
        if rsi >= 60:
            s.append(Signal("intraday_rsi_strong", Direction.LONG, 0.08,
                            f"Intraday RSI {rsi:.0f} - strong momentum."))
        elif rsi <= 40:
            s.append(Signal("intraday_rsi_weak", Direction.SHORT, 0.08,
                            f"Intraday RSI {rsi:.0f} - weak momentum."))

    if "macd" in df.columns and "macd_signal" in df.columns:
        if _crossed_above(df["macd"], df["macd_signal"]):
            s.append(Signal("intraday_macd_bull", Direction.LONG, 0.10,
                            "Intraday MACD bullish cross."))
        elif _crossed_below(df["macd"], df["macd_signal"]):
            s.append(Signal("intraday_macd_bear", Direction.SHORT, 0.10,
                            "Intraday MACD bearish cross."))
    return s


def score_confluence(signals: list[Signal]) -> tuple[float, Direction, float]:
    """Collapse signals into (net_score, dominant_direction, confidence 0-100)."""
    if not signals:
        return 0.0, Direction.NONE, 0.0

    long_w = sum(s.weight for s in signals if s.direction == Direction.LONG)
    short_w = sum(s.weight for s in signals if s.direction == Direction.SHORT)
    total_w = long_w + short_w
    if total_w == 0:
        return 0.0, Direction.NONE, 0.0

    net = (long_w - short_w) / total_w     # -1..+1

    if net > 0.15:
        direction = Direction.LONG
    elif net < -0.15:
        direction = Direction.SHORT
    else:
        direction = Direction.NONE

    if direction == Direction.LONG:
        supporting = sum(1 for s in signals if s.direction == Direction.LONG)
    elif direction == Direction.SHORT:
        supporting = sum(1 for s in signals if s.direction == Direction.SHORT)
    else:
        supporting = 0

    lopsided = abs(net)
    breadth = min(supporting, 6) / 6.0
    confidence = 100.0 * (0.55 * lopsided + 0.45 * breadth)
    if supporting < 3:
        confidence *= 0.6
    confidence = round(confidence, 1)
    return round(net, 3), direction, confidence


# =========================================================================== #
#  4.  RISK  -  sizing, stops, targets, scenarios, vetoes, expectancy, Kelly
# =========================================================================== #
def atr_stop(entry: float, atr: float, direction: Direction, mult: float = 2.0) -> float:
    """Volatility-based stop. Distance scales with ATR."""
    if direction == Direction.LONG:
        return entry - mult * atr
    return entry + mult * atr


def structure_stop(entry: float, swing_level: float, direction: Direction,
                   buffer_pct: float = 0.003) -> float:
    """Stop just beyond a structural level with a small buffer."""
    if direction == Direction.LONG:
        return swing_level * (1.0 - buffer_pct)
    return swing_level * (1.0 + buffer_pct)


def choose_stop(entry: float, atr: float, direction: Direction,
                swing_level: float | None, mult: float = 2.0, method: str = "atr",
                ) -> tuple[float, str]:
    """Pick a stop. Returns (stop_price, method_used)."""
    a_stop = atr_stop(entry, atr, direction, mult)

    def _valid(stop: float) -> bool:
        return stop < entry if direction == Direction.LONG else stop > entry

    if method == "structure" and swing_level is not None:
        s_stop = structure_stop(entry, swing_level, direction)
        if _valid(s_stop):
            return s_stop, "structure"
        return a_stop, "atr (structure level was on the wrong side)"
    if method == "wider" and swing_level is not None:
        s_stop = structure_stop(entry, swing_level, direction)
        if _valid(s_stop):
            if direction == Direction.LONG:
                return min(a_stop, s_stop), "wider(atr|structure)"
            return max(a_stop, s_stop), "wider(atr|structure)"
        return a_stop, "atr (structure level was on the wrong side)"
    return a_stop, "atr"


def target_for_rr(entry: float, stop: float, direction: Direction, rr: float) -> float:
    """Price that achieves the desired reward:risk multiple."""
    risk = abs(entry - stop)
    if direction == Direction.LONG:
        return entry + rr * risk
    return entry - rr * risk


def position_size(capital: float, entry: float, stop: float,
                  risk_pct: float, max_exposure_pct: float = 0.25,
                  ) -> tuple[int, float]:
    """Fixed-fractional position size. Returns (quantity, rupees_at_risk)."""
    rupees_at_risk = capital * risk_pct
    risk_per_share = abs(entry - stop)
    if risk_per_share <= 0:
        return 0, 0.0

    qty_risk = math.floor(rupees_at_risk / risk_per_share)
    qty_exposure = math.floor((capital * max_exposure_pct) / entry) if entry > 0 else 0
    qty = max(0, min(qty_risk, qty_exposure))
    actual_risk = qty * risk_per_share
    return qty, round(actual_risk, 2)


def build_plan(entry: float, atr: float, direction: Direction, capital: float,
               *, risk_pct: float = 0.01, atr_mult: float = 2.0, target_rr: float = 2.0,
               max_exposure_pct: float = 0.25, swing_level: float | None = None,
               stop_method: str = "atr", slippage_pct: float = 0.0,
               gap_buffer_atr: float = 0.0) -> PositionPlan:
    """Assemble a complete, executable position plan."""
    stop, method = choose_stop(entry, atr, direction, swing_level, atr_mult, stop_method)
    target = target_for_rr(entry, stop, direction, target_rr)

    risk_per_share = abs(entry - stop)
    buffer = max(slippage_pct * entry, gap_buffer_atr * atr)
    worst_rps = risk_per_share + buffer

    sizing_stop = stop - buffer if direction == Direction.LONG else stop + buffer
    qty, _ = position_size(capital, entry, sizing_stop, risk_pct, max_exposure_pct)

    reward_per_share = abs(target - entry)
    rr = reward_per_share / risk_per_share if risk_per_share > 0 else 0.0
    position_value = qty * entry
    rupees_to_target = qty * reward_per_share
    rupees_at_risk = qty * risk_per_share
    rupees_at_risk_worst = qty * worst_rps

    return PositionPlan(
        entry=round(entry, 2),
        stop_loss=round(stop, 2),
        target=round(target, 2),
        quantity=qty,
        capital=round(capital, 2),
        risk_pct=risk_pct,
        rupees_at_risk=round(rupees_at_risk, 2),
        rupees_to_target=round(rupees_to_target, 2),
        risk_per_share=round(risk_per_share, 2),
        reward_per_share=round(reward_per_share, 2),
        risk_reward=round(rr, 2),
        worst_case_risk_per_share=round(worst_rps, 2),
        rupees_at_risk_worst=round(rupees_at_risk_worst, 2),
        gap_buffer=round(buffer, 2),
        position_value=round(position_value, 2),
        position_pct_of_capital=round(100 * position_value / capital, 1) if capital else 0.0,
        stop_method=method,
    )


def build_scenarios(entry: float, stop: float, target: float, atr: float,
                    direction: Direction, confidence: float,
                    regime: Regime) -> list[Scenario]:
    """Produce bull / base / bear outcomes with rough probabilities."""
    conf = max(0.0, min(confidence, 100.0)) / 100.0

    aligned = (
        (direction == Direction.LONG and regime in (Regime.TRENDING_UP, Regime.RANGING))
        or (direction == Direction.SHORT and regime in (Regime.TRENDING_DOWN, Regime.RANGING))
    )
    regime_adj = 0.05 if aligned else -0.08
    if regime == Regime.VOLATILE:
        regime_adj -= 0.05

    p_work = min(0.75, max(0.25, 0.40 + 0.30 * conf + regime_adj))
    p_bull = round(p_work * 0.45, 2)
    p_base = round(p_work - p_bull, 2)
    p_bear = round(1.0 - p_bull - p_base, 2)

    sign = 1 if direction == Direction.LONG else -1
    bull_target = entry + sign * 3.0 * atr
    bull_move = 100 * (bull_target - entry) / entry
    base_move = 100 * (target - entry) / entry
    bear_move = 100 * (stop - entry) / entry

    return [
        Scenario(
            "bull", p_bull, round(bull_target, 2), round(bull_move, 2),
            f"Momentum extends ~3 ATR in your favour to {bull_target:.1f}. "
            f"Trail the stop and let it run.",
        ),
        Scenario(
            "base", p_base, round(target, 2), round(base_move, 2),
            f"Trade reaches the planned target {target:.1f} (R:R met). "
            f"Book or scale out as planned.",
        ),
        Scenario(
            "bear", p_bear, round(stop, 2), round(bear_move, 2),
            f"Thesis fails and the stop at {stop:.1f} is hit for a controlled "
            f"-1R loss. This WILL happen on a fraction of trades - that is normal.",
        ),
    ]


def evaluate_vetoes(*, direction: Direction, regime: Regime, plan: PositionPlan,
                    confidence: float, atr: float, volume_ratio: float | None,
                    is_breakout: bool, min_rr: float = 2.0, min_confidence: float = 35.0,
                    earnings_soon: bool | None = None) -> list[Veto]:
    """The veteran's 'no-go' checklist."""
    v: list[Veto] = []

    wrong_side = ((direction == Direction.LONG and plan.stop_loss >= plan.entry) or
                  (direction == Direction.SHORT and plan.stop_loss <= plan.entry))
    if wrong_side:
        v.append(Veto("stop_wrong_side",
                      "Stop is on the wrong side of entry - this indicates bad/"
                      "gapped data. Refusing the trade until the data is sane.", "hard"))

    if plan.risk_reward < min_rr:
        v.append(Veto("rr_too_low",
                      f"Risk:reward is {plan.risk_reward:.2f}, below the {min_rr:.1f} "
                      f"minimum. The math doesn't justify the risk.", "hard"))

    if plan.quantity <= 0:
        v.append(Veto("no_size",
                      "Position size rounds to 0 shares - capital too small for "
                      "this stop distance at the chosen risk %. Skip or widen risk %.",
                      "hard"))

    if atr > 0 and plan.risk_per_share < 0.5 * atr:
        v.append(Veto("stop_too_tight",
                      f"Stop is only {plan.risk_per_share:.2f} away vs ATR {atr:.2f} - "
                      f"likely to be stopped out by normal noise.", "hard"))

    if direction == Direction.LONG and regime == Regime.TRENDING_DOWN:
        v.append(Veto("counter_trend",
                      "Going long into a strong downtrend (ADX>25, -DI>+DI). "
                      "Counter-trend trades are low-odds - need a very good reason.",
                      "hard"))
    if direction == Direction.SHORT and regime == Regime.TRENDING_UP:
        v.append(Veto("counter_trend",
                      "Shorting into a strong uptrend. Low-odds - reconsider.", "hard"))

    if confidence < min_confidence:
        v.append(Veto("low_confidence",
                      f"Evidence confidence {confidence:.0f} is below the "
                      f"{min_confidence:.0f} floor - the setup is not clean enough.",
                      "soft"))

    if regime == Regime.VOLATILE:
        v.append(Veto("volatile_regime",
                      "Volatility is elevated - consider halving size and widening "
                      "the stop. Slippage and gaps are more likely.", "soft"))

    if is_breakout and (volume_ratio is None or volume_ratio < 1.2):
        v.append(Veto("weak_breakout_volume",
                      "Breakout is not backed by above-average volume - higher "
                      "chance of a failed/false breakout.", "soft"))

    if is_breakout and regime == Regime.RANGING:
        v.append(Veto("range_breakout",
                      "This is a breakout signal but the market is ranging (ADX<20), "
                      "where breakouts frequently fail back into the range. Lower odds.",
                      "soft"))

    if earnings_soon:
        v.append(Veto("event_risk",
                      "An earnings/major event appears imminent - gap risk through "
                      "your stop. Size down or wait until after the event.", "soft"))
    return v


def expectancy_r(win_rate: float, avg_win_r: float, avg_loss_r: float = 1.0) -> float:
    """Expectancy in R-multiples."""
    return win_rate * avg_win_r - (1.0 - win_rate) * avg_loss_r


def breakeven_win_rate(rr: float) -> float:
    """Win rate needed just to break even at a given reward:risk."""
    return 1.0 / (1.0 + rr)


def kelly_fraction(win_rate: float, payoff_b: float, cap: float = 0.25) -> float:
    """Full Kelly fraction f* = (b*p - q) / b, clipped to [0, cap]."""
    if payoff_b <= 0:
        return 0.0
    p, q = win_rate, 1.0 - win_rate
    f = (payoff_b * p - q) / payoff_b
    return max(0.0, min(f, cap))


def fractional_kelly(win_rate: float, payoff_b: float, fraction: float = 0.25,
                     cap: float = 0.25) -> float:
    """Fractional (quarter) Kelly - the safe, professional version."""
    return round(min(kelly_fraction(win_rate, payoff_b, cap=1.0) * fraction, cap), 4)


# =========================================================================== #
#  5.  LABELING  -  Triple-Barrier Method (Lopez de Prado, AFML ch. 3)
# =========================================================================== #
def triple_barrier_labels(prices: pd.Series, take_profit_atr: float,
                          stop_loss_atr: float, max_hold_bars: int,
                          atr_series: pd.Series,
                          direction: str = "long") -> pd.DataFrame:
    """Triple-Barrier labels for ML/RL training on realistic TP/SL/timeout outcomes.

    For each bar `i`, opens a hypothetical trade at ``prices[i]`` and walks
    forward up to ``max_hold_bars`` looking at subsequent closes. Whichever
    barrier is touched first (all evaluated on close prices only) determines
    the label:

      * ``+1`` win     - the take-profit barrier was reached
      * ``-1`` loss    - the stop-loss barrier was reached
      * ``0``  timeout - the time barrier expired without either being hit

    Barriers are set in ATR units, mirroring for shorts:

      * long:  TP = close + take_profit_atr * ATR   SL = close - stop_loss_atr * ATR
      * short: TP = close - take_profit_atr * ATR   SL = close + stop_loss_atr * ATR

    Parameters
    ----------
    prices : pd.Series
        Close prices indexed by date/time.
    take_profit_atr : float
        Profit barrier distance in ATR units (e.g. 5.0 -> 5 x ATR away).
    stop_loss_atr : float
        Loss barrier distance in ATR units (e.g. 2.0 -> 2 x ATR away).
    max_hold_bars : int
        Time barrier: number of forward bars after which the trade times out.
    atr_series : pd.Series
        ATR values aligned to ``prices`` (same index).
    direction : {"long", "short"}, default "long"
        Trade direction. Barriers mirror for shorts.

    Returns
    -------
    pd.DataFrame
        Indexed like ``prices`` with columns:
          * ``label``   - int in {+1, -1, 0}
          * ``hit_bar`` - forward bar count where a barrier was hit (NaN if
                          no exit was observed - e.g. bar has invalid ATR or
                          is the very last bar with no forward data).
          * ``return``  - realized return at exit (direction-adjusted, so a
                          winning short shows a positive number).

    Example
    -------
    >>> import pandas as pd, numpy as np
    >>> from advisor.analysis import triple_barrier_labels
    >>> close = pd.Series(np.linspace(100, 110, 30),
    ...                   index=pd.date_range("2024-01-01", periods=30, freq="B"))
    >>> atr = pd.Series(0.2, index=close.index)
    >>> triple_barrier_labels(close, 5.0, 2.0, 10, atr, direction="long").head()
    """
    if direction not in ("long", "short"):
        raise ValueError(f"direction must be 'long' or 'short', got {direction!r}")
    if take_profit_atr <= 0 or stop_loss_atr <= 0:
        raise ValueError("take_profit_atr and stop_loss_atr must be positive")
    if max_hold_bars < 1:
        raise ValueError("max_hold_bars must be >= 1")

    prices = prices.astype(float)
    atr_aligned = atr_series.astype(float).reindex(prices.index)

    px = prices.to_numpy()
    at = atr_aligned.to_numpy()
    n = len(px)
    sign = 1 if direction == "long" else -1

    labels = np.zeros(n, dtype=int)
    hit_bar = np.full(n, np.nan)
    ret = np.full(n, np.nan)

    for i in range(n):
        entry = px[i]
        atr_i = at[i]
        if not (np.isfinite(entry) and np.isfinite(atr_i)) or atr_i <= 0:
            hit_bar[i] = np.nan
            ret[i] = np.nan
            continue

        tp = entry + sign * take_profit_atr * atr_i
        sl = entry - sign * stop_loss_atr * atr_i
        end = min(i + max_hold_bars, n - 1)
        if end == i:  # no forward data
            continue

        label = 0
        hit = end - i           # default: time barrier
        exit_px = px[end]

        for j in range(i + 1, end + 1):
            p = px[j]
            if not np.isfinite(p):
                continue
            if sign == 1:
                if p >= tp:
                    label, hit, exit_px = 1, j - i, p
                    break
                if p <= sl:
                    label, hit, exit_px = -1, j - i, p
                    break
            else:
                if p <= tp:
                    label, hit, exit_px = 1, j - i, p
                    break
                if p >= sl:
                    label, hit, exit_px = -1, j - i, p
                    break

        labels[i] = label
        hit_bar[i] = hit
        ret[i] = sign * (exit_px - entry) / entry if entry != 0 else np.nan

    return pd.DataFrame(
        {"label": labels, "hit_bar": hit_bar, "return": ret},
        index=prices.index,
    )
