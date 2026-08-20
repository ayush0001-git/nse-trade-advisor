"""
deep_analysis.py - "50-year veteran" multi-timeframe analysis + prediction.

This script goes DEEPER than the standard advisor pipeline:
  1. Pulls 4 timeframes: weekly (from daily), daily, 15m, 1m tick
  2. Runs the existing advisor pipeline on daily (regime + signals + plan)
  3. Adds an intraday 15m analysis for entry-timing precision
  4. Adds a 1m micro-structure read of the LAST trading session
     (VWAP, opening-range breakout, last-hour momentum, tick volume profile)
  5. Combines all 4 layers into a multi-timeframe confluence matrix
  6. Generates explicit price predictions for 1-day, 1-week, 1-month horizons
     with bull / base / bear scenarios and confidence bands
  7. Writes a full report to a markdown file in the voice of a veteran trader

Usage:
    python deep_analysis.py SYMBOL [SYMBOL ...]
    python deep_analysis.py DEEDEV.NS RELIANCE.NS TCS.NS
    python deep_analysis.py DEEDEV.NS --capital 100000
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Add the project root to the path so we can import the advisor package.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import yfinance as yf
from advisor.core import Settings, Style, Direction, Regime, Verdict
from advisor import analysis as an
from advisor import engine as eng
from advisor import extras as ex
from advisor.core import normalize_symbol, clean_frame


# =========================================================================== #
#  Multi-timeframe data fetcher
# =========================================================================== #
class MultiTFData:
    """Pull and cache OHLCV data at 4 timeframes for one symbol."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.daily = self._fetch("1d", "max")
        self.hourly = self._fetch("1h", "6mo")
        self.min15 = self._fetch("15m", "1mo")
        self.min5 = self._fetch("5m", "1mo")
        self.min1 = self._fetch("1m", "5d")

    def _fetch(self, interval: str, period: str) -> pd.DataFrame:
        try:
            df = self.ticker.history(interval=interval, period=period, auto_adjust=True)
            if df is None or df.empty:
                return pd.DataFrame()
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            df = df.rename(columns={
                "Open": "open", "High": "high", "Low": "low",
                "Close": "close", "Volume": "volume",
            })
            return df[["open", "high", "low", "close", "volume"]]
        except Exception as e:
            print(f"  ! {self.symbol} {interval}: {type(e).__name__}: {e}")
            return pd.DataFrame()

    def weekly_from_daily(self) -> pd.DataFrame:
        """Resample daily to weekly using the advisor's helper."""
        if self.daily.empty:
            return pd.DataFrame()
        return an.resample_ohlc(self.daily, "W")


# =========================================================================== #
#  Layer 1: Weekly trend (highest timeframe - the tide)
# =========================================================================== #
def analyze_weekly(weekly: pd.DataFrame) -> dict:
    """Read the weekly chart like a veteran: trend, structure, momentum."""
    if len(weekly) < 30:
        return {"available": False, "note": f"only {len(weekly)} weekly bars - too short"}

    close = weekly["close"]
    sma10 = close.rolling(10).mean()
    sma30 = close.rolling(30).mean()
    sma50 = close.rolling(50).mean() if len(close) >= 50 else None

    last = close.iloc[-1]
    s10 = sma10.iloc[-1]
    s30 = sma30.iloc[-1]
    s50 = sma50.iloc[-1] if sma50 is not None else None

    # Aligned bullish stack: close > 10 > 30 > 50
    if last > s10 > s30 and (s50 is None or s10 > s50):
        trend = "up"
        structure = "Aligned bullish stack (price > 10W > 30W > 50W)."
    elif last < s10 < s30 and (s50 is None or s10 < s50):
        trend = "down"
        structure = "Aligned bearish stack (price < 10W < 30W < 50W)."
    else:
        trend = "mixed"
        structure = "Weekly MAs are tangled - no clean trend."

    # 52-week high/low context
    high_52w = close.tail(52).max()
    low_52w = close.tail(52).min()
    pct_from_high = (last - high_52w) / high_52w * 100
    pct_from_low = (last - low_52w) / low_52w * 100

    # Weekly RSI
    rsi_w = an.rsi(close, 14).iloc[-1]

    # Weekly momentum (last 4 weeks % change)
    mom_4w = (last / close.iloc[-5] - 1) * 100 if len(close) >= 5 else 0

    # Weekly MACD
    macd_line, sig_line, hist = an.macd(close)
    macd_w = macd_line.iloc[-1]
    sig_w = sig_line.iloc[-1]
    hist_w = hist.iloc[-1]

    return {
        "available": True,
        "trend": trend,
        "structure": structure,
        "last": round(last, 2),
        "sma_10w": round(s10, 2),
        "sma_30w": round(s30, 2),
        "sma_50w": round(s50, 2) if s50 is not None else None,
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "pct_from_high": round(pct_from_high, 2),
        "pct_from_low": round(pct_from_low, 2),
        "rsi_weekly": round(rsi_w, 1) if not pd.isna(rsi_w) else None,
        "mom_4w_pct": round(mom_4w, 2),
        "macd_weekly": round(macd_w, 2) if not pd.isna(macd_w) else None,
        "macd_signal_weekly": round(sig_w, 2) if not pd.isna(sig_w) else None,
        "macd_hist_weekly": round(hist_w, 2) if not pd.isna(hist_w) else None,
    }


# =========================================================================== #
#  Layer 2: Daily (regime + signals + plan) - reuses the advisor pipeline
# =========================================================================== #
def analyze_daily(data: MultiTFData, settings: Settings) -> dict:
    """Run the full advisor swing pipeline on daily data."""
    if data.daily.empty or len(data.daily) < 30:
        return {"available": False, "note": "insufficient daily data"}

    # Build a CSV-like source so the advisor's Analyzer works without yfinance
    # calls (we already have the data).
    src = _InMemorySource(data.daily)
    agent = eng.Analyzer(settings, source=src)
    idea = agent.analyze(data.symbol, style=Style.SWING, use_llm=False, use_news=False)

    enriched = an.compute_indicators(data.daily, include_vwap=False)
    last = enriched.iloc[-1]

    return {
        "available": True,
        "idea": idea,
        "enriched": enriched,
        "regime": idea.regime.value,
        "verdict": idea.verdict.value,
        "direction": idea.direction.value,
        "confidence": idea.confidence,
        "confluence_score": idea.confluence_score,
        "signals": idea.signals,
        "vetoes": idea.vetoes,
        "plan": idea.plan,
        "scenarios": idea.scenarios,
        "notes": idea.notes,
        "narration": idea.narration,
        # Snapshot for printing
        "snap": {
            "close": float(last["close"]),
            "rsi_14": float(last["rsi_14"]) if not pd.isna(last["rsi_14"]) else None,
            "atr_14": float(last["atr_14"]) if not pd.isna(last["atr_14"]) else None,
            "adx_14": float(last["adx_14"]) if not pd.isna(last["adx_14"]) else None,
            "plus_di": float(last["plus_di"]) if not pd.isna(last["plus_di"]) else None,
            "minus_di": float(last["minus_di"]) if not pd.isna(last["minus_di"]) else None,
            "bb_upper": float(last["bb_upper"]) if not pd.isna(last["bb_upper"]) else None,
            "bb_lower": float(last["bb_lower"]) if not pd.isna(last["bb_lower"]) else None,
            "sma_50": float(last["sma_50"]) if not pd.isna(last["sma_50"]) else None,
            "sma_200": float(last["sma_200"]) if not pd.isna(last["sma_200"]) else None,
            "volume": float(last["volume"]),
            "avg_volume_20": float(last["avg_volume_20"]) if not pd.isna(last["avg_volume_20"]) else None,
        },
    }


class _InMemorySource:
    """A minimal OHLCVSource that serves a pre-fetched DataFrame."""
    name = "memory"

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def get_history(self, symbol, interval="1d", period=None):
        return self._df.copy()

    def get_quote(self, symbol):
        return float(self._df["close"].iloc[-1])


# =========================================================================== #
#  Layer 3: 15-minute intraday - entry-timing precision
# =========================================================================== #
def analyze_15m(data: MultiTFData) -> dict:
    """Read the 15-minute chart for intraday structure and entry timing."""
    if data.min15.empty or len(data.min15) < 30:
        return {"available": False, "note": "insufficient 15m data"}

    df = an.compute_indicators(data.min15, include_vwap=True)
    last = df.iloc[-1]
    close = float(last["close"])
    vwap = float(last["vwap"]) if not pd.isna(last["vwap"]) else None
    rsi_15 = float(last["rsi_14"]) if not pd.isna(last["rsi_14"]) else None

    # Today's session
    today_mask = df.index.normalize() == df.index[-1].normalize()
    today = df[today_mask]
    if today.empty:
        return {"available": True, "note": "no current session in 15m data"}

    or_bars = 6  # 6 x 15m = first 90 minutes
    orb = today.iloc[:or_bars] if len(today) > or_bars else today
    or_high = float(orb["high"].max())
    or_low = float(orb["low"].min())

    session_high = float(today["high"].max())
    session_low = float(today["low"].min())
    session_open = float(today["open"].iloc[0])

    # VWAP relationship
    vwap_pos = "above" if vwap and close > vwap else "below" if vwap else "n/a"

    # Opening range breakout status
    if close > or_high:
        orb_status = "broke above OR high (bullish)"
    elif close < or_low:
        orb_status = "broke below OR low (bearish)"
    else:
        orb_status = f"inside opening range ({or_low:.2f} - {or_high:.2f})"

    # Last-hour momentum (last 4 x 15m bars = 1 hour)
    last_hour = today.tail(4)
    mom_1h = (close / last_hour["open"].iloc[0] - 1) * 100 if len(last_hour) >= 1 else 0

    # Volume profile: morning vs afternoon
    morning = today[today.index.hour < 12]
    afternoon = today[today.index.hour >= 12]
    morning_vol = float(morning["volume"].sum()) if not morning.empty else 0
    afternoon_vol = float(afternoon["volume"].sum()) if not afternoon.empty else 0
    if morning_vol + afternoon_vol > 0:
        vol_profile = f"{morning_vol / (morning_vol + afternoon_vol) * 100:.0f}% morning / {afternoon_vol / (morning_vol + afternoon_vol) * 100:.0f}% afternoon"
    else:
        vol_profile = "n/a"

    return {
        "available": True,
        "close": round(close, 2),
        "vwap": round(vwap, 2) if vwap else None,
        "vwap_position": vwap_pos,
        "rsi_15m": round(rsi_15, 1) if rsi_15 else None,
        "session_open": round(session_open, 2),
        "session_high": round(session_high, 2),
        "session_low": round(session_low, 2),
        "or_high": round(or_high, 2),
        "or_low": round(or_low, 2),
        "orb_status": orb_status,
        "last_hour_mom_pct": round(mom_1h, 2),
        "volume_profile": vol_profile,
    }


# =========================================================================== #
#  Layer 4: 1-minute tick micro-structure (the last session, bar by bar)
# =========================================================================== #
def analyze_1m_tick(data: MultiTFData) -> dict:
    """Read the 1-minute chart of the LAST session - tick-level micro-structure."""
    if data.min1.empty or len(data.min1) < 30:
        return {"available": False, "note": "insufficient 1m data"}

    df = data.min1
    # Just analyze the last session
    today_mask = df.index.normalize() == df.index[-1].normalize()
    today = df[today_mask]
    if today.empty:
        return {"available": False, "note": "no current session in 1m data"}

    close = float(today["close"].iloc[-1])

    # Tick-level VWAP for the session
    typical = (today["high"] + today["low"] + today["close"]) / 3
    pv = typical * today["volume"]
    cum_pv = pv.cumsum()
    cum_vol = today["volume"].cumsum()
    vwap_1m = float(cum_pv.iloc[-1] / cum_vol.iloc[-1]) if cum_vol.iloc[-1] > 0 else None

    # Volume profile buckets (price levels where most volume traded)
    if len(today) >= 10:
        price_buckets = pd.cut(today["close"], bins=10)
        vol_by_bucket = today.groupby(price_buckets)["volume"].sum()
        if not vol_by_bucket.empty:
            top_bucket = vol_by_bucket.idxmax()
            poc = (top_bucket.left + top_bucket.right) / 2  # Point of Control
        else:
            poc = None
    else:
        poc = None

    # Tick momentum: count up-minutes vs down-minutes
    up_min = int((today["close"].diff().dropna() > 0).sum())
    down_min = int((today["close"].diff().dropna() < 0).sum())
    total_min = up_min + down_min

    # Last 30 minutes (closing auction-like behavior)
    last_30 = today.tail(30)
    if len(last_30) >= 2:
        last_30_mom = (float(last_30["close"].iloc[-1]) / float(last_30["open"].iloc[0]) - 1) * 100
    else:
        last_30_mom = 0

    # High/Low of the day so far
    hod = float(today["high"].max())
    lod = float(today["low"].min())

    # Largest single-minute volume spike (proxy for institutional prints)
    if not today.empty:
        avg_1m_vol = float(today["volume"].mean())
        max_1m_vol = float(today["volume"].max())
        spike_ratio = max_1m_vol / avg_1m_vol if avg_1m_vol > 0 else 0
        # When did the spike happen?
        spike_idx = today["volume"].idxmax()
        spike_time = spike_idx.strftime("%H:%M")
        spike_price = float(today.loc[spike_idx, "close"])
    else:
        avg_1m_vol = max_1m_vol = spike_ratio = 0
        spike_time = spike_price = None

    return {
        "available": True,
        "close": round(close, 2),
        "vwap_1m": round(vwap_1m, 2) if vwap_1m else None,
        "poc_price": round(float(poc), 2) if poc else None,
        "up_minutes": up_min,
        "down_minutes": down_min,
        "tick_breadth": f"{up_min}up / {down_min}down of {total_min} min",
        "last_30min_mom_pct": round(last_30_mom, 2),
        "high_of_day": round(hod, 2),
        "low_of_day": round(lod, 2),
        "avg_1m_volume": int(avg_1m_vol),
        "max_1m_volume": int(max_1m_vol),
        "spike_ratio": round(spike_ratio, 2),
        "spike_time": spike_time,
        "spike_price": round(spike_price, 2) if spike_price else None,
    }


# =========================================================================== #
#  Multi-timeframe confluence matrix
# =========================================================================== #
def confluence_matrix(weekly: dict, daily: dict, m15: dict, m1: dict) -> dict:
    """Combine the 4 layers into a single directional read.

    A veteran trader weighs higher timeframes more heavily:
      weekly  : 40%  (the tide - don't fight it)
      daily   : 35%  (the wave - the actual trade)
      15m     : 15%  (entry timing)
      1m      : 10%  (micro-structure confirmation)
    """
    def _dir_score(d: dict) -> float:
        """Return -1 (bearish) .. +1 (bullish) for a layer."""
        if not d.get("available"):
            return 0
        if "trend" in d:  # weekly
            return {"up": 1, "down": -1, "mixed": 0}.get(d["trend"], 0)
        if "direction" in d:  # daily
            return {"long": 1, "short": -1, "none": 0}.get(d.get("direction", "none"), 0)
        if "vwap_position" in d:  # 15m
            return 1 if d.get("vwap_position") == "above" else -1 if d.get("vwap_position") == "below" else 0
        if "up_minutes" in d:  # 1m
            u, dn = d.get("up_minutes", 0), d.get("down_minutes", 0)
            return (u - dn) / (u + dn) if (u + dn) > 0 else 0
        return 0

    w_score = _dir_score(weekly) * 0.40
    d_score = _dir_score(daily) * 0.35
    m15_score = _dir_score(m15) * 0.15
    m1_score = _dir_score(m1) * 0.10
    combined = w_score + d_score + m15_score + m1_score

    if combined > 0.3:
        bias = "BULLISH"
    elif combined < -0.3:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return {
        "weekly_score": round(w_score, 3),
        "daily_score": round(d_score, 3),
        "min15_score": round(m15_score, 3),
        "min1_score": round(m1_score, 3),
        "combined": round(combined, 3),
        "bias": bias,
        "interpretation": (
            f"All four timeframes agree on the downside." if combined < -0.6 else
            f"Strong bearish confluence across timeframes." if combined < -0.3 else
            f"Mixed signals - no clean edge." if -0.3 <= combined <= 0.3 else
            f"Strong bullish confluence across timeframes." if combined < 0.6 else
            f"All four timeframes agree on the upside."
        ),
    }


# =========================================================================== #
#  Prediction generator
# =========================================================================== #
def make_prediction(weekly: dict, daily: dict, m15: dict, m1: dict,
                    conf: dict, settings: Settings) -> dict:
    """Generate explicit price predictions for 1-day, 1-week, 1-month horizons.

    Uses ATR for expected move sizing (a standard volatility-based forecast):
      1-day expected move   = 1 x ATR
      1-week expected move  = sqrt(5) x ATR  (5 trading days)
      1-month expected move = sqrt(21) x ATR (21 trading days)

    Direction is set by the confluence bias; magnitude by ATR.
    """
    if not daily.get("available") or not daily.get("snap"):
        return {"available": False}

    snap = daily["snap"]
    close = snap["close"]
    atr = snap.get("atr_14") or (close * 0.02)  # fallback: 2% of price

    bias_sign = 1 if conf["bias"] == "BULLISH" else -1 if conf["bias"] == "BEARISH" else 0
    confidence_mult = abs(conf["combined"])  # 0..1 - scales how far we push

    # Expected moves
    move_1d = atr * 1.0
    move_1w = atr * (5 ** 0.5)
    move_1m = atr * (21 ** 0.5)

    # Base case: drift in the bias direction proportional to confluence
    drift_1d = bias_sign * move_1d * (0.5 + 0.5 * confidence_mult)
    drift_1w = bias_sign * move_1w * (0.5 + 0.5 * confidence_mult)
    drift_1m = bias_sign * move_1m * (0.5 + 0.5 * confidence_mult)

    # Bull / Base / Bear targets
    base_1d = close + drift_1d
    bull_1d = close + (move_1d * (1.5 if bias_sign >= 0 else 0.5))
    bear_1d = close - (move_1d * (1.5 if bias_sign <= 0 else 0.5))

    base_1w = close + drift_1w
    bull_1w = close + (move_1w * (1.3 if bias_sign >= 0 else 0.4))
    bear_1w = close - (move_1w * (1.3 if bias_sign <= 0 else 0.4))

    base_1m = close + drift_1m
    bull_1m = close + (move_1m * (1.2 if bias_sign >= 0 else 0.3))
    bear_1m = close - (move_1m * (1.2 if bias_sign <= 0 else 0.3))

    # Probability weights from confluence
    p_bias = 0.40 + 0.20 * confidence_mult  # base case probability
    p_oppose = 0.25 - 0.10 * confidence_mult  # opposite case
    p_extend = 1 - p_bias - p_oppose  # extension in the bias direction

    return {
        "available": True,
        "current_price": round(close, 2),
        "atr_14": round(atr, 2),
        "bias": conf["bias"],
        "confluence_strength": abs(conf["combined"]),
        "horizons": {
            "1_day": {
                "bull": round(bull_1d, 2),
                "base": round(base_1d, 2),
                "bear": round(bear_1d, 2),
                "expected_move": round(move_1d, 2),
                "move_pct": round(move_1d / close * 100, 2),
            },
            "1_week": {
                "bull": round(bull_1w, 2),
                "base": round(base_1w, 2),
                "bear": round(bear_1w, 2),
                "expected_move": round(move_1w, 2),
                "move_pct": round(move_1w / close * 100, 2),
            },
            "1_month": {
                "bull": round(bull_1m, 2),
                "base": round(base_1m, 2),
                "bear": round(bear_1m, 2),
                "expected_move": round(move_1m, 2),
                "move_pct": round(move_1m / close * 100, 2),
            },
        },
        "probabilities": {
            "bull": round(p_extend if bias_sign > 0 else p_oppose, 2),
            "base": round(p_bias, 2),
            "bear": round(p_extend if bias_sign < 0 else p_oppose, 2),
        },
    }


# =========================================================================== #
#  Backtest (uses the advisor's existing swing backtest on daily data)
# =========================================================================== #
def run_backtest(data: MultiTFData, settings: Settings) -> dict:
    if data.daily.empty or len(data.daily) < 60:
        return {"available": False, "note": "need >= 60 daily bars for backtest"}
    result = eng.backtest_swing(data.daily, data.symbol, settings)
    return {
        "available": True,
        "result": result,
        "summary": result.summary(),
        "stats": result.stats,
        "n_trades": len(result.trades),
        "last_5_trades": [
            {
                "entry_date": t.entry_date.strftime("%Y-%m-%d"),
                "exit_date": t.exit_date.strftime("%Y-%m-%d"),
                "direction": t.direction,
                "entry": t.entry,
                "exit": t.exit,
                "qty": t.quantity,
                "outcome_r": t.outcome_r,
                "pnl": t.net_pnl,
                "reason": t.reason,
            } for t in result.trades[-5:]
        ],
    }


# =========================================================================== #
#  Report writer (Markdown)
# =========================================================================== #
def write_report(symbol: str, weekly: dict, daily: dict, m15: dict, m1: dict,
                 conf: dict, pred: dict, bt: dict, settings: Settings) -> str:
    """Write the full veteran-style report as Markdown."""

    snap = daily.get("snap", {}) if daily.get("available") else {}
    idea = daily.get("idea") if daily.get("available") else None

    lines = []
    lines.append(f"# {symbol} - Deep Multi-Timeframe Analysis")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST  ")
    lines.append(f"**Capital:** Rs. {settings.capital:,.0f}  ")
    lines.append(f"**Risk per trade:** {settings.risk_pct*100:.1f}%  ")
    lines.append(f"**Style:** Swing (daily) with intraday-timing overlay")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ----- EXECUTIVE SUMMARY ---------------------------------------------- #
    lines.append("## Executive Summary (the 30-second read)")
    lines.append("")
    if pred.get("available"):
        p = pred
        lines.append(f"| Metric | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Current price | **Rs. {p['current_price']}** |")
        lines.append(f"| ATR(14) | Rs. {p['atr_14']} ({p['horizons']['1_day']['move_pct']}% daily move expected) |")
        lines.append(f"| Multi-timeframe bias | **{p['bias']}** (confluence strength: {p['confluence_strength']:.2f}) |")
        if idea:
            lines.append(f"| Verdict | **{idea.verdict.value}** ({idea.direction.value}) |")
            lines.append(f"| Confidence | {idea.confidence:.0f}/100 |")
        lines.append(f"| 1-day forecast | Rs. {p['horizons']['1_day']['bear']} (bear) - Rs. {p['horizons']['1_day']['base']} (base) - Rs. {p['horizons']['1_day']['bull']} (bull) |")
        lines.append(f"| 1-week forecast | Rs. {p['horizons']['1_week']['bear']} (bear) - Rs. {p['horizons']['1_week']['base']} (base) - Rs. {p['horizons']['1_week']['bull']} (bull) |")
        lines.append(f"| 1-month forecast | Rs. {p['horizons']['1_month']['bear']} (bear) - Rs. {p['horizons']['1_month']['base']} (base) - Rs. {p['horizons']['1_month']['bull']} (bull) |")
        if idea and idea.plan and idea.verdict.value in ("TAKE", "WATCH"):
            pl = idea.plan
            lines.append(f"| **Entry** | Rs. {pl.entry} |")
            lines.append(f"| **Stop-loss** | Rs. {pl.stop_loss} (-{pl.risk_per_share}/sh) |")
            lines.append(f"| **Target** | Rs. {pl.target} (+{pl.reward_per_share}/sh) |")
            lines.append(f"| **Quantity** | {pl.quantity} shares (Rs. {pl.position_value:,.0f} deployed) |")
            lines.append(f"| **Risk:Reward** | {pl.risk_reward:.2f} : 1 |")
            lines.append(f"| **Capital at risk** | Rs. {pl.rupees_at_risk:,.0f} ({pl.risk_pct*100:.1f}%) |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ----- LAYER 1: WEEKLY ------------------------------------------------ #
    lines.append("## Layer 1 - Weekly Chart (the tide)")
    lines.append("")
    lines.append("*A 50-year veteran looks at the weekly first. You can fight a daily wave,")
    lines.append("but never fight the weekly tide.*")
    lines.append("")
    if weekly.get("available"):
        lines.append(f"- **Trend:** {weekly['trend'].upper()}")
        lines.append(f"- **Structure:** {weekly['structure']}")
        lines.append(f"- **Last weekly close:** Rs. {weekly['last']}")
        lines.append(f"- **10W SMA:** Rs. {weekly['sma_10w']}  |  **30W SMA:** Rs. {weekly['sma_30w']}  |  **50W SMA:** Rs. {weekly.get('sma_50w', 'n/a')}")
        lines.append(f"- **52-week high:** Rs. {weekly['high_52w']} ({weekly['pct_from_high']}% from high)")
        lines.append(f"- **52-week low:** Rs. {weekly['low_52w']} (+{weekly['pct_from_low']}% from low)")
        lines.append(f"- **Weekly RSI(14):** {weekly['rsi_weekly']}")
        lines.append(f"- **4-week momentum:** {weekly['mom_4w_pct']}%")
        lines.append(f"- **Weekly MACD:** {weekly['macd_weekly']} vs signal {weekly['macd_signal_weekly']} (hist {weekly['macd_hist_weekly']})")
    else:
        lines.append(f"- {weekly.get('note', 'Not available')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ----- LAYER 2: DAILY ------------------------------------------------- #
    lines.append("## Layer 2 - Daily Chart (the wave - the actual trade)")
    lines.append("")
    lines.append("*The daily chart is where trades live or die. Regime first, then signals,")
    lines.append("then a position plan with a real stop and a real target.*")
    lines.append("")
    if daily.get("available"):
        s = snap
        lines.append(f"- **Regime:** {daily['regime']}")
        lines.append(f"- **Verdict:** **{daily['verdict']}** ({daily['direction']})")
        lines.append(f"- **Confidence:** {daily['confidence']:.0f}/100  (confluence: {daily['confluence_score']:+.2f})")
        lines.append(f"- **Close:** Rs. {s['close']}")
        lines.append(f"- **RSI(14):** {s['rsi_14']}")
        lines.append(f"- **ADX(14):** {s['adx_14']} (+DI {s['plus_di']}, -DI {s['minus_di']})")
        lines.append(f"- **ATR(14):** Rs. {s['atr_14']} ({s['atr_14']/s['close']*100:.2f}% of price)")
        lines.append(f"- **Bollinger:** Rs. {s['bb_lower']} - Rs. {s['bb_upper']}")
        lines.append(f"- **50-DMA:** Rs. {s['sma_50']}  |  **200-DMA:** Rs. {s['sma_200']}")
        lines.append(f"- **Volume:** {s['volume']:,.0f} (20-bar avg: {s['avg_volume_20']:,.0f})")
        lines.append("")

        # Signals
        if idea and idea.signals:
            lines.append("### Evidence (confluence)")
            lines.append("")
            bull = idea.bullish_signals
            bear = idea.bearish_signals
            if bull:
                lines.append("**For the trade (+):**")
                for sig in bull[:8]:
                    lines.append(f"- + {sig.note}")
            if bear:
                lines.append("**Against the trade (-):**")
                for sig in bear[:8]:
                    lines.append(f"- - {sig.note}")
            lines.append("")

        # Vetoes
        if idea and idea.vetoes:
            lines.append("### Red signals")
            lines.append("")
            for v in idea.vetoes:
                mark = "!!" if v.severity == "hard" else "! "
                lines.append(f"- {mark} ({v.severity}) {v.reason}")
            lines.append("")

        # Plan
        if idea and idea.plan and idea.verdict.value in ("TAKE", "WATCH"):
            pl = idea.plan
            lines.append("### The plan")
            lines.append("")
            lines.append(f"| | |")
            lines.append(f"|---|---|")
            lines.append(f"| Entry | Rs. {pl.entry} |")
            lines.append(f"| Stop-loss | Rs. {pl.stop_loss} (-Rs. {pl.risk_per_share}/sh, via {pl.stop_method}) |")
            lines.append(f"| Target | Rs. {pl.target} (+Rs. {pl.reward_per_share}/sh) |")
            lines.append(f"| Quantity | {pl.quantity} shares |")
            lines.append(f"| Risk:Reward | {pl.risk_reward:.2f} : 1 |")
            lines.append(f"| Capital at risk | Rs. {pl.rupees_at_risk:,.0f} ({pl.risk_pct*100:.1f}% of capital) |")
            lines.append(f"| Worst-case risk | Rs. {pl.rupees_at_risk_worst:,.0f} (if stop gaps) |")
            lines.append(f"| Position value | Rs. {pl.position_value:,.0f} ({pl.position_pct_of_capital:.0f}% of capital) |")
            lines.append("")

        # Scenarios
        if idea and idea.scenarios:
            lines.append("### Scenarios (rough probabilities, NOT guarantees)")
            lines.append("")
            lines.append("| Scenario | Probability | Price target | Move |")
            lines.append("|---|---|---|---|")
            for sc in idea.scenarios:
                lines.append(f"| {sc.name.upper()} | {sc.probability*100:.0f}% | Rs. {sc.price_target} | {sc.move_pct:+.1f}% |")
            lines.append("")
    else:
        lines.append(f"- {daily.get('note', 'Not available')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ----- LAYER 3: 15-MINUTE -------------------------------------------- #
    lines.append("## Layer 3 - 15-Minute Chart (entry timing)")
    lines.append("")
    lines.append("*Once the daily says 'take the trade', the 15m tells you WHEN. VWAP, the")
    lines.append("opening range, and the last-hour momentum decide your fill quality.*")
    lines.append("")
    if m15.get("available"):
        lines.append(f"- **Last 15m close:** Rs. {m15['close']}")
        lines.append(f"- **VWAP (session):** Rs. {m15['vwap']}  ->  price is **{m15['vwap_position']}** VWAP")
        lines.append(f"- **15m RSI:** {m15['rsi_15m']}")
        lines.append(f"- **Session open / high / low:** Rs. {m15['session_open']} / {m15['session_high']} / {m15['session_low']}")
        lines.append(f"- **Opening range (first 90 min):** Rs. {m15['or_low']} - Rs. {m15['or_high']}")
        lines.append(f"- **ORB status:** {m15['orb_status']}")
        lines.append(f"- **Last-hour momentum:** {m15['last_hour_mom_pct']}%")
        lines.append(f"- **Volume profile:** {m15['volume_profile']}")
    else:
        lines.append(f"- {m15.get('note', 'Not available')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ----- LAYER 4: 1-MINUTE TICK ---------------------------------------- #
    lines.append("## Layer 4 - 1-Minute Tick Micro-Structure (the last session)")
    lines.append("")
    lines.append("*This is where institutional footprints show. Volume spikes, the Point of")
    lines.append("Control, tick-by-tick breadth - the veteran reads the tape here.*")
    lines.append("")
    if m1.get("available"):
        lines.append(f"- **Last tick:** Rs. {m1['close']}")
        lines.append(f"- **Session VWAP (1m cum):** Rs. {m1['vwap_1m']}")
        lines.append(f"- **Point of Control (POC):** Rs. {m1['poc_price']}")
        lines.append(f"- **Tick breadth:** {m1['tick_breadth']}")
        lines.append(f"- **Last 30-min momentum:** {m1['last_30min_mom_pct']}%")
        lines.append(f"- **High / Low of day:** Rs. {m1['high_of_day']} / Rs. {m1['low_of_day']}")
        lines.append(f"- **Avg 1-min volume:** {m1['avg_1m_volume']:,} shares")
        lines.append(f"- **Max 1-min volume:** {m1['max_1m_volume']:,} shares ({m1['spike_ratio']}x average)")
        if m1.get("spike_time"):
            lines.append(f"- **Largest volume spike:** {m1['spike_time']} at Rs. {m1['spike_price']} (possible institutional print)")
    else:
        lines.append(f"- {m1.get('note', 'Not available')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ----- CONFLUENCE MATRIX --------------------------------------------- #
    lines.append("## Multi-Timeframe Confluence Matrix")
    lines.append("")
    lines.append("*The veteran weighs higher timeframes more heavily. Weekly = 40%,")
    lines.append("Daily = 35%, 15m = 15%, 1m = 10%.*")
    lines.append("")
    lines.append("| Timeframe | Weight | Score | Direction |")
    lines.append("|---|---|---|---|")
    lines.append(f"| Weekly  | 40% | {conf['weekly_score']:+.2f} | {weekly.get('trend', 'n/a')} |")
    lines.append(f"| Daily   | 35% | {conf['daily_score']:+.2f} | {daily.get('direction', 'n/a')} |")
    lines.append(f"| 15-min  | 15% | {conf['min15_score']:+.2f} | {m15.get('vwap_position', 'n/a')} |")
    lines.append(f"| 1-min   | 10% | {conf['min1_score']:+.2f} | tick breadth |")
    lines.append(f"| **Combined** | 100% | **{conf['combined']:+.2f}** | **{conf['bias']}** |")
    lines.append("")
    lines.append(f"> {conf['interpretation']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ----- PREDICTION ---------------------------------------------------- #
    lines.append("## Prediction (the forecast)")
    lines.append("")
    lines.append("*Expected moves are ATR-based: 1d = 1 ATR, 1w = sqrt(5) ATR, 1m = sqrt(21) ATR.")
    lines.append("Direction from the confluence bias; magnitude scales with confluence strength.*")
    lines.append("")
    if pred.get("available"):
        p = pred
        lines.append(f"**Current price: Rs. {p['current_price']}**  |  ATR(14): Rs. {p['atr_14']}")
        lines.append("")
        lines.append("### Three horizons, three scenarios each")
        lines.append("")
        lines.append("| Horizon | Bear | Base | Bull | Expected move |")
        lines.append("|---|---|---|---|---|")
        for h in ["1_day", "1_week", "1_month"]:
            hz = p["horizons"][h]
            label = h.replace("_", " ").title()
            lines.append(f"| {label} | Rs. {hz['bear']} | Rs. {hz['base']} | Rs. {hz['bull']} | Rs. {hz['expected_move']} ({hz['move_pct']}%) |")
        lines.append("")
        lines.append("### Probability weights (from confluence strength)")
        lines.append("")
        lines.append(f"- **Bull (extension in bias direction):** {p['probabilities']['bull']*100:.0f}%")
        lines.append(f"- **Base (drift to base case):** {p['probabilities']['base']*100:.0f}%")
        lines.append(f"- **Bear (thesis fails):** {p['probabilities']['bear']*100:.0f}%")
        lines.append("")
        lines.append("> **These probabilities are NOT calibrated win rates.** They are heuristic")
        lines.append("> weights derived from multi-timeframe confluence, not from a 1000-trade")
        lines.append("> backtest. Treat them as 'how strong is the setup', not 'how often it wins.'")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ----- BACKTEST ------------------------------------------------------ #
    lines.append("## Backtest (validation on history)")
    lines.append("")
    lines.append("*The same swing strategy applied to historical daily data. No look-ahead,")
    lines.append("Indian equity costs (brokerage/STT/exchange/GST/SEBI/stamp/slippage) included.*")
    lines.append("")
    if bt.get("available"):
        stats = bt["stats"]
        if bt["n_trades"] > 0:
            lines.append(f"- **Period:** {bt['result'].start.strftime('%Y-%m-%d')} -> {bt['result'].end.strftime('%Y-%m-%d')}")
            lines.append(f"- **Trades:** {stats['trades']}")
            lines.append(f"- **Win rate:** {stats['win_rate']*100:.1f}%")
            lines.append(f"- **Expectancy:** {stats['expectancy_r']:+.2f} R per trade")
            lines.append(f"- **Profit factor:** {stats['profit_factor']}")
            lines.append(f"- **Avg win / Avg loss:** +{stats['avg_win_r']}R / -{stats['avg_loss_r']}R")
            lines.append(f"- **Net return:** {stats['total_return_pct']:+.1f}% (CAGR {stats['cagr_pct']:+.1f}%)")
            lines.append(f"- **Max drawdown:** {stats['max_drawdown_pct']:.1f}% (mark-to-market)")
            lines.append(f"- **Costs paid:** Rs. {stats['costs_paid']:,.0f}")
            lines.append(f"- **Final equity:** Rs. {stats['final_equity']:,.0f} (from Rs. {stats['start_equity']:,.0f})")
            lines.append("")
            lines.append("### Last 5 trades")
            lines.append("")
            lines.append("| Entry date | Exit date | Dir | Entry | Exit | Qty | R | P&L | Reason |")
            lines.append("|---|---|---|---|---|---|---|---|---|")
            for t in bt["last_5_trades"]:
                lines.append(f"| {t['entry_date']} | {t['exit_date']} | {t['direction']} | {t['entry']} | {t['exit']} | {t['qty']} | {t['outcome_r']:+.2f} | Rs. {t['pnl']:+,.0f} | {t['reason']} |")
        else:
            lines.append(f"- {bt['summary']}")
    else:
        lines.append(f"- {bt.get('note', 'Not available')}")
    lines.append("")
    lines.append("> **Backtests overstate live results.** They assume perfect fills, no slippage")
    lines.append("> beyond the model, and a regime that doesn't shift. Paper-trade before going live.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ----- VETERAN'S READ ------------------------------------------------ #
    lines.append("## The veteran's read (the closing argument)")
    lines.append("")
    lines.append("```")
    if idea and idea.narration:
        # Strip the template's AVOID/TAKE prefix since we have the verdict above
        narration = idea.narration.replace("\n\n", "\n\n  ")
        lines.append(f"  {narration}")
    lines.append("```")
    lines.append("")
    lines.append("### Final prediction in one line")
    lines.append("")
    if pred.get("available") and idea:
        p = pred
        h1 = p["horizons"]["1_day"]
        h7 = p["horizons"]["1_week"]
        h30 = p["horizons"]["1_month"]
        lines.append(f"**{symbol}** is currently Rs. {p['current_price']}. The multi-timeframe bias is **{p['bias']}**.")
        lines.append(f"Tomorrow's expected range is Rs. {h1['bear']} - Rs. {h1['bull']} (base Rs. {h1['base']}).")
        lines.append(f"Over the next week: Rs. {h7['bear']} - Rs. {h7['bull']}. Over the next month: Rs. {h30['bear']} - Rs. {h30['bull']}.")
        if idea.verdict.value in ("TAKE", "WATCH") and idea.plan:
            pl = idea.plan
            side = "LONG" if idea.direction.value == "long" else "SHORT"
            lines.append(f"")
            lines.append(f"**Trade plan ({side}):** Enter near Rs. {pl.entry}, stop Rs. {pl.stop_loss}, target Rs. {pl.target} ({pl.risk_reward:.1f}:1 R:R). Size {pl.quantity} shares for Rs. {pl.rupees_at_risk:,.0f} capital risk.")
        elif idea.verdict.value == "AVOID":
            lines.append(f"")
            lines.append(f"**Trade plan: STAND ASIDE.** Red signals fired - this is not a trade to take today.")
        else:
            lines.append(f"")
            lines.append(f"**Trade plan: WAIT.** No clean setup right now. Patience is a position.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*This is software output, not investment advice. Numbers are computed in")
    lines.append("Python; the narration is template-based (set `llm_provider` in config.yaml")
    lines.append("for richer prose). Validate with the backtest above before risking capital.*")

    return "\n".join(lines)


# =========================================================================== #
#  Main
# =========================================================================== #
def analyze_one(symbol: str, settings: Settings) -> str:
    """Run the full deep analysis on one symbol and return the report."""
    print(f"\n{'='*68}")
    print(f"  Deep analysis: {symbol}")
    print(f"{'='*68}")

    print("  [1/6] Fetching multi-timeframe data...")
    data = MultiTFData(symbol)
    print(f"        daily={len(data.daily)}  hourly={len(data.hourly)}  "
          f"15m={len(data.min15)}  5m={len(data.min5)}  1m={len(data.min1)}")

    print("  [2/6] Analyzing weekly chart...")
    weekly = analyze_weekly(data.weekly_from_daily())

    print("  [3/6] Analyzing daily chart (full advisor pipeline)...")
    daily = analyze_daily(data, settings)

    print("  [4/6] Analyzing 15-minute intraday...")
    m15 = analyze_15m(data)

    print("  [5/6] Analyzing 1-minute tick micro-structure...")
    m1 = analyze_1m_tick(data)

    print("  [6/6] Building confluence matrix + prediction + backtest...")
    conf = confluence_matrix(weekly, daily, m15, m1)
    pred = make_prediction(weekly, daily, m15, m1, conf, settings)
    bt = run_backtest(data, settings)

    print(f"\n  Bias: {conf['bias']}  Combined score: {conf['combined']:+.2f}")
    if pred.get("available"):
        h1 = pred["horizons"]["1_day"]
        print(f"  1-day forecast: Rs. {h1['bear']} (bear) - Rs. {h1['base']} (base) - Rs. {h1['bull']} (bull)")
    if bt.get("available") and bt["n_trades"] > 0:
        s = bt["stats"]
        print(f"  Backtest: {s['trades']} trades, {s['win_rate']*100:.1f}% win, "
              f"{s['expectancy_r']:+.2f}R/trade, {s['total_return_pct']:+.1f}% net")

    report = write_report(symbol, weekly, daily, m15, m1, conf, pred, bt, settings)
    return report


def main():
    ap = argparse.ArgumentParser(
        description="Deep multi-timeframe analysis with prediction. "
                    "Use Yahoo symbols: DEEDEV.NS, RELIANCE.NS, TCS.BO, etc.")
    ap.add_argument("symbols", nargs="+", help="One or more Yahoo symbols (e.g. DEEDEV.NS)")
    ap.add_argument("--capital", type=float, default=100_000, help="Trading capital in INR")
    ap.add_argument("--risk-pct", type=float, default=0.01, help="Risk per trade (0.01 = 1%)")
    ap.add_argument("--output-dir", default="reports",
                    help="Directory to save markdown reports (default: reports/)")
    args = ap.parse_args()

    settings = Settings(capital=args.capital, risk_pct=args.risk_pct)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for sym in args.symbols:
        # Normalize: if no .NS/.BO suffix and not an index, default to .NS
        if not sym.startswith("^") and not sym.endswith((".NS", ".BO")):
            sym_yf = normalize_symbol(sym, "NSE")
        else:
            sym_yf = sym

        try:
            report = analyze_one(sym_yf, settings)
            safe_name = sym_yf.replace(".", "_").replace("^", "idx_")
            out_path = out_dir / f"{safe_name}_deep_analysis.md"
            out_path.write_text(report)
            print(f"\n  -> Report saved to: {out_path}")
        except Exception as e:
            print(f"\n  ! FAILED on {sym_yf}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
