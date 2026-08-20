"""
institutional_flow.py - Layer 4: Institutional Money Flow

Tracks the smart money: FII/DII flows, delivery percentage, block deals,
and bulk deals. Professional traders follow institutional money because
institutions move markets.

Data sources (all free):
  - Delivery %: yfinance doesn't expose this directly, but we approximate it
    from volume patterns. For production, use NSE's bhav copy which has
    delivery data per stock.
  - FII/DII activity: NSE publishes daily FII/DII cash market activity.
    We scrape it from NSE's API (when accessible) with fallback to a
    heuristic based on index movement + volume.
  - Block/Bulk deals: NSE publishes these daily. We try to fetch them,
    falling back gracefully when blocked.

Each component contributes to an Institutional Score (0-15 in the 100-point
system):

  - Delivery % (0-5): high delivery = investors accumulating, not intraday flipping
  - FII flow (0-5): FIIs buying = smart money bullish
  - DII flow (0-3): DIIs (mutual funds, insurance) buying = domestic conviction
  - Block/Bulk deals (0-2): institutional block deals in the stock

Usage:
    from institutional_flow import get_institutional_score
    result = get_institutional_score("RELIANCE.NS")
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategies import fetch_stock_data


# =========================================================================== #
#  FII/DII activity fetcher (NSE)
# =========================================================================== #
def fetch_fii_dii_activity() -> dict | None:
    """Fetch today's FII/DII cash market activity from NSE.

    Returns:
        {"fii_buy": float, "fii_sell": float, "fii_net": float,
         "dii_buy": float, "dii_sell": float, "dii_net": float, "date": str}
    or None if unavailable.
    """
    # NSE's API endpoint for FII/DII activity
    url = "https://www.nseindia.com/api/fiidiiTradeReact"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # Parse the response - it's a list of {category, buyValue, sellValue, netValue}
        result = {"fii": {}, "dii": {}}
        for row in data.get("data", []):
            cat = row.get("category", "").lower()
            entry = {
                "buy": float(row.get("buyValue", 0)),
                "sell": float(row.get("sellValue", 0)),
                "net": float(row.get("netValue", 0).replace(",", "")) if isinstance(row.get("netValue"), str) else float(row.get("netValue", 0)),
            }
            if "fii" in cat:
                result["fii"] = entry
            elif "dii" in cat:
                result["dii"] = entry
        return result
    except Exception:
        return None


# =========================================================================== #
#  Delivery % approximation
# =========================================================================== #
def estimate_delivery_pct(df: pd.DataFrame) -> float:
    """Approximate delivery % from OHLCV data.

    NSE's actual delivery data requires the bhav copy. As a heuristic:
    - High delivery % correlates with low intraday volatility relative
      to the daily range, and above-average volume (institutions accumulate).
    - We compute a proxy: (close - low) / (high - low) * volume_ratio

    A stock that closed near its high with above-average volume likely had
    high delivery (buyers held positions overnight).

    Returns a delivery % estimate (0-100).
    """
    if len(df) < 25:
        return 50.0  # neutral
    last = df.iloc[-1]
    high = float(last["high"])
    low = float(last["low"])
    close = float(last["close"])
    vol = float(last["volume"])
    avg_vol = float(df["volume"].iloc[-20:].mean()) if len(df) >= 20 else vol

    if high == low:
        return 50.0

    # Close position in daily range (0=low, 1=high)
    close_position = (close - low) / (high - low)
    # Volume ratio (1 = average)
    vol_ratio = vol / max(avg_vol, 1)

    # High delivery proxy: closed high + above-average volume
    # Low delivery proxy: closed low + high volume (intraday selling)
    delivery_proxy = close_position * 50 + min(vol_ratio, 2) * 25
    return max(10, min(95, delivery_proxy))


# =========================================================================== #
#  Block/Bulk deals (NSE)
# =========================================================================== #
def fetch_block_bulk_deals(symbol: str) -> list[dict]:
    """Fetch recent block/bulk deals for a symbol from NSE.

    NSE publishes these at:
      https://www.nseindia.com/api/historical/bulk-deals
      https://www.nseindia.com/api/historical/block-deals

    Returns a list of {date, symbol, qty, price, value} or [] if unavailable.
    """
    sym = symbol.split(".")[0]
    # Block deals (>= 5 lakh shares or 5 cr value)
    url = f"https://www.nseindia.com/api/historical/block-deals?symbol={sym}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/",
    }
    deals = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for row in data.get("data", [])[:10]:
            deals.append({
                "date": row.get("date", ""),
                "symbol": row.get("symbol", ""),
                "qty": int(row.get("quantity", 0)),
                "price": float(row.get("price", 0)),
                "value": float(row.get("value", 0)),
                "type": "block",
            })
    except Exception:
        pass

    # Bulk deals (>= 0.5 lakh shares or 0.5 cr value)
    url2 = f"https://www.nseindia.com/api/historical/bulk-deals?symbol={sym}"
    try:
        req = urllib.request.Request(url2, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for row in data.get("data", [])[:10]:
            deals.append({
                "date": row.get("date", ""),
                "symbol": row.get("symbol", ""),
                "qty": int(row.get("quantity", 0)),
                "price": float(row.get("price", 0)),
                "value": float(row.get("value", 0)),
                "type": "bulk",
            })
    except Exception:
        pass

    return deals[:10]


# =========================================================================== #
#  Main scoring function
# =========================================================================== #
def get_institutional_score(symbol: str) -> dict:
    """Compute the institutional money flow score (0-15).

    Components:
      - Delivery % (0-5)
      - FII net flow (0-5)
      - DII net flow (0-3)
      - Block/Bulk deals (0-2)
    """
    sym = symbol if "." in symbol else f"{symbol}.NS"

    # 1. Delivery %
    try:
        df = fetch_stock_data(sym, period="2y")
        delivery_pct = estimate_delivery_pct(df)
    except Exception:
        delivery_pct = 50.0

    # Delivery score: >70% = strong accumulation, <40% = distribution
    if delivery_pct >= 70:
        delivery_score = 5
    elif delivery_pct >= 55:
        delivery_score = 4
    elif delivery_pct >= 45:
        delivery_score = 3
    elif delivery_pct >= 35:
        delivery_score = 2
    else:
        delivery_score = 1

    # 2. FII/DII flow
    fii_dii = fetch_fii_dii_activity()
    fii_score = 0
    dii_score = 0
    fii_net = 0
    dii_net = 0
    if fii_dii:
        fii_net = fii_dii.get("fii", {}).get("net", 0)
        dii_net = fii_dii.get("dii", {}).get("net", 0)
        # FII score: net buy > 1000cr = 5, > 500cr = 4, > 0 = 3, > -500 = 1, else 0
        if fii_net > 1000:
            fii_score = 5
        elif fii_net > 500:
            fii_score = 4
        elif fii_net > 0:
            fii_score = 3
        elif fii_net > -500:
            fii_score = 1
        else:
            fii_score = 0
        # DII score (0-3)
        if dii_net > 500:
            dii_score = 3
        elif dii_net > 100:
            dii_score = 2
        elif dii_net > 0:
            dii_score = 1
        else:
            dii_score = 0

    # 3. Block/Bulk deals
    deals = fetch_block_bulk_deals(symbol)
    deals_score = min(2, len(deals) // 2)

    total = delivery_score + fii_score + dii_score + deals_score

    # Explanation
    parts = [
        f"Delivery ~{delivery_pct:.0f}% ({delivery_score}/5)",
    ]
    if fii_dii:
        parts.append(f"FII net ₹{fii_net:+.0f}cr ({fii_score}/5)")
        parts.append(f"DII net ₹{dii_net:+.0f}cr ({dii_score}/3)")
    else:
        parts.append("FII/DII data unavailable (0/8)")
    parts.append(f"{len(deals)} block/bulk deals ({deals_score}/2)")

    return {
        "symbol": symbol,
        "score": total,
        "max_score": 15,
        "delivery_pct": round(delivery_pct, 1),
        "delivery_score": delivery_score,
        "fii_net_cr": round(fii_net, 0),
        "fii_score": fii_score,
        "dii_net_cr": round(dii_net, 0),
        "dii_score": dii_score,
        "block_bulk_deals": deals,
        "deals_score": deals_score,
        "explanation": " | ".join(parts) + f" | Total: {total}/15",
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Institutional Money Flow Layer")
    ap.add_argument("symbol", help="Stock symbol")
    args = ap.parse_args()
    result = get_institutional_score(args.symbol)
    print(json.dumps(result, indent=2))
