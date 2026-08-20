"""
options_flow.py - Layer 5: Options Flow Intelligence

Options flow reveals where smart money is positioning. This module fetches
the options chain via yfinance and computes:

  - Put/Call Ratio (PCR): <0.7 = bullish (too many puts), >1.3 = bearish
  - Open Interest Buildup: Price ↑ + OI ↑ = Long Buildup (bullish)
                          Price ↓ + OI ↑ = Short Buildup (bearish)
                          Price ↑ + OI ↓ = Short Covering (bullish)
                          Price ↓ + OI ↓ = Long Unwinding (bearish)
  - Max Pain: the strike where most options expire worthless — price tends
    to gravitate toward max pain on expiry day
  - Unusual OI spike: strikes with abnormally high OI vs neighbors

The Options Score contributes 0-10 points in the 100-point system.

Usage:
    from options_flow import get_options_score
    result = get_options_score("RELIANCE.NS")
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def fetch_options_chain(symbol: str) -> dict | None:
    """Fetch the nearest-expiry options chain via yfinance.

    Returns:
        {"expiry": str, "calls": DataFrame, "puts": DataFrame, "current_price": float}
        or None if unavailable.
    """
    sym = symbol if "." in symbol else f"{symbol}.NS"
    try:
        ticker = yf.Ticker(sym)
        expiries = ticker.options
        if not expiries:
            return None
        # Use the nearest expiry
        expiry = expiries[0]
        chain = ticker.option_chain(expiry)
        calls = chain.calls
        puts = chain.puts
        if calls.empty or puts.empty:
            return None
        # Current price
        info = ticker.history(period="1d")
        if info.empty:
            return None
        current_price = float(info["Close"].iloc[-1])
        return {
            "expiry": expiry,
            "calls": calls,
            "puts": puts,
            "current_price": current_price,
        }
    except Exception as e:
        return None


def compute_pcr(calls: pd.DataFrame, puts: pd.DataFrame) -> dict:
    """Compute Put/Call Ratio from open interest."""
    total_call_oi = float(calls["openInterest"].sum()) if "openInterest" in calls.columns else 0
    total_put_oi = float(puts["openInterest"].sum()) if "openInterest" in puts.columns else 0
    total_call_vol = float(calls["volume"].sum()) if "volume" in calls.columns else 0
    total_put_vol = float(puts["volume"].sum()) if "volume" in puts.columns else 0

    pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0
    pcr_vol = total_put_vol / total_call_vol if total_call_vol > 0 else 1.0

    return {
        "pcr_oi": round(pcr_oi, 3),
        "pcr_volume": round(pcr_vol, 3),
        "total_call_oi": int(total_call_oi),
        "total_put_oi": int(total_put_oi),
        "total_call_volume": int(total_call_vol),
        "total_put_volume": int(total_put_vol),
    }


def compute_max_pain(calls: pd.DataFrame, puts: pd.DataFrame) -> dict:
    """Compute max pain — the strike where total option holder loss is maximized.

    At max pain, the net payout to option holders is minimized (i.e., writers
    profit most). Price tends to gravitate here on expiry day.
    """
    if calls.empty or puts.empty:
        return {"max_pain_strike": None, "strikes": []}

    strikes = sorted(set(calls["strike"].tolist() + puts["strike"].tolist()))
    if not strikes:
        return {"max_pain_strike": None, "strikes": []}

    pain_at_strike = []
    for s in strikes:
        # Call holders lose money when price < strike (they paid premium)
        # Put holders lose money when price > strike
        call_pain = 0
        for _, row in calls.iterrows():
            if s < row["strike"]:
                # Calls are ITM at this strike -> holders gain, writers lose
                # Pain = -(strike - s) * OI  (negative = holders profit)
                call_pain += (row["strike"] - s) * float(row.get("openInterest", 0))
        put_pain = 0
        for _, row in puts.iterrows():
            if s > row["strike"]:
                put_pain += (s - row["strike"]) * float(row.get("openInterest", 0))
        total_pain = call_pain + put_pain
        pain_at_strike.append({"strike": s, "pain": total_pain})

    # Max pain = strike with MAXIMUM total pain (holders lose most)
    max_pain_entry = max(pain_at_strike, key=lambda x: x["pain"])
    return {
        "max_pain_strike": max_pain_entry["strike"],
        "strikes": pain_at_strike[:20],  # top 20 strikes for charting
    }


def detect_oi_buildup(calls: pd.DataFrame, puts: pd.DataFrame,
                      current_price: float) -> dict:
    """Detect OI buildup patterns near the current price.

    Looks at the ATM (at-the-money) strike and its neighbors to determine
    if there's aggressive call buying (bullish) or put buying (bearish).
    """
    if calls.empty or puts.empty:
        return {"pattern": "unknown", "bias": "neutral"}

    # Find ATM strike (closest to current price)
    atm_call = calls.iloc[(calls["strike"] - current_price).abs().argsort()[:1]]
    atm_put = puts.iloc[(puts["strike"] - current_price).abs().argsort()[:1]]

    if atm_call.empty or atm_put.empty:
        return {"pattern": "unknown", "bias": "neutral"}

    atm_call_oi = float(atm_call["openInterest"].iloc[0])
    atm_put_oi = float(atm_put["openInterest"].iloc[0])
    atm_call_vol = float(atm_call["volume"].iloc[0]) if "volume" in atm_call.columns else 0
    atm_put_vol = float(atm_put["volume"].iloc[0]) if "volume" in atm_put.columns else 0

    # Heuristic: if call volume > 2x call OI, it's fresh buying (long buildup)
    # If put volume > 2x put OI, it's fresh put buying (short buildup)
    call_activity = atm_call_vol / max(atm_call_oi, 1)
    put_activity = atm_put_vol / max(atm_put_oi, 1)

    if call_activity > 1.5 and call_activity > put_activity:
        return {"pattern": "Long Buildup", "bias": "bullish",
                "atm_call_oi": int(atm_call_oi), "atm_call_vol": int(atm_call_vol)}
    if put_activity > 1.5 and put_activity > call_activity:
        return {"pattern": "Short Buildup", "bias": "bearish",
                "atm_put_oi": int(atm_put_oi), "atm_put_vol": int(atm_put_vol)}
    if atm_call_oi > atm_put_oi * 1.5:
        return {"pattern": "Call Heavy", "bias": "bullish",
                "atm_call_oi": int(atm_call_oi), "atm_put_oi": int(atm_put_oi)}
    if atm_put_oi > atm_call_oi * 1.5:
        return {"pattern": "Put Heavy", "bias": "bearish",
                "atm_call_oi": int(atm_call_oi), "atm_put_oi": int(atm_put_oi)}
    return {"pattern": "Balanced", "bias": "neutral",
            "atm_call_oi": int(atm_call_oi), "atm_put_oi": int(atm_put_oi)}


def get_options_score(symbol: str) -> dict:
    """Compute the options flow score (0-10).

    Components:
      - PCR (0-4): PCR < 0.7 = bullish (4), 0.7-1.0 = slight bull (3),
                   1.0-1.3 = slight bear (2), > 1.3 = bearish (1)
      - OI Buildup (0-4): Long Buildup = 4, Call Heavy = 3, Balanced = 2,
                          Put Heavy = 1, Short Buildup = 0
      - Max Pain proximity (0-2): price within 2% of max pain = 2 (expiry magnet),
                                   within 5% = 1, else 0
    """
    chain = fetch_options_chain(symbol)
    if chain is None:
        return {
            "symbol": symbol,
            "score": 5,  # neutral
            "max_score": 10,
            "available": False,
            "explanation": "Options chain not available for this stock.",
        }

    calls = chain["calls"]
    puts = chain["puts"]
    current_price = chain["current_price"]

    pcr = compute_pcr(calls, puts)
    max_pain = compute_max_pain(calls, puts)
    buildup = detect_oi_buildup(calls, puts, current_price)

    # PCR score
    pcr_val = pcr["pcr_oi"]
    if pcr_val < 0.7:
        pcr_score = 4
    elif pcr_val < 1.0:
        pcr_score = 3
    elif pcr_val < 1.3:
        pcr_score = 2
    else:
        pcr_score = 1

    # Buildup score
    buildup_scores = {
        "Long Buildup": 4, "Call Heavy": 3, "Balanced": 2,
        "Put Heavy": 1, "Short Buildup": 0,
    }
    buildup_score = buildup_scores.get(buildup["pattern"], 2)

    # Max pain proximity score
    mp_score = 0
    if max_pain["max_pain_strike"]:
        mp_distance = abs(current_price - max_pain["max_pain_strike"]) / current_price
        if mp_distance < 0.02:
            mp_score = 2
        elif mp_distance < 0.05:
            mp_score = 1

    total = pcr_score + buildup_score + mp_score

    return {
        "symbol": symbol,
        "score": total,
        "max_score": 10,
        "available": True,
        "expiry": chain["expiry"],
        "current_price": round(current_price, 2),
        "pcr": pcr,
        "pcr_score": pcr_score,
        "max_pain": max_pain["max_pain_strike"],
        "max_pain_score": mp_score,
        "oi_buildup": buildup,
        "buildup_score": buildup_score,
        "explanation": (
            f"PCR(OI) {pcr_val:.2f} ({pcr_score}/4) | "
            f"OI pattern: {buildup['pattern']} ({buildup_score}/4) | "
            f"Max pain ₹{max_pain['max_pain_strike']} ({mp_score}/2) | "
            f"Total: {total}/10"
        ),
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Options Flow Intelligence")
    ap.add_argument("symbol", help="Stock symbol")
    args = ap.parse_args()
    result = get_options_score(args.symbol)
    print(json.dumps(result, indent=2, default=str))
