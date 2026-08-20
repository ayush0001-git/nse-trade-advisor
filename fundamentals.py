"""
fundamentals.py - Layer: Fundamental Analysis

Fetches fundamental data from yfinance .info and scores the stock on:
  - Valuation (P/E, P/B vs sector)
  - Growth (revenue & earnings growth)
  - Profitability (margins, ROE)
  - Financial health (debt/equity, current ratio)

Contributes 0-10 points in the 100-point system.

Usage:
    from fundamentals import get_fundamental_score
    result = get_fundamental_score("RELIANCE.NS")
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def fetch_fundamentals(symbol: str) -> dict:
    """Fetch fundamental data via yfinance .info."""
    sym = symbol if "." in symbol else f"{symbol}.NS"
    try:
        ticker = yf.Ticker(sym)
        info = ticker.info
        return {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "peg_ratio": info.get("pegRatio"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            "beta": info.get("beta"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            # Profitability
            "profit_margins": info.get("profitMargins"),
            "operating_margins": info.get("operatingMargins"),
            "return_on_equity": info.get("returnOnEquity"),
            "return_on_assets": info.get("returnOnAssets"),
            # Growth
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "revenue_quarterly_growth": info.get("revenueQuarterlyGrowth"),
            "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
            # Financial health
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "total_cash": info.get("totalCash"),
            "total_debt": info.get("totalDebt"),
            # Per-share
            "book_value": info.get("bookValue"),
            "earnings_per_share": info.get("trailingEps"),
            "revenue_per_share": info.get("revenuePerShare"),
            # Sector
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_fundamental_score(symbol: str) -> dict:
    """Compute the fundamental score (0-10).

    Components:
      - Valuation (0-3): P/E and P/B relative to reasonable thresholds
      - Growth (0-3): revenue + earnings growth
      - Profitability (0-2): margins + ROE
      - Financial health (0-2): debt/equity + current ratio
    """
    info = fetch_fundamentals(symbol)
    if "error" in info:
        return {
            "symbol": symbol,
            "score": 5,  # neutral
            "max_score": 10,
            "available": False,
            "explanation": f"Fundamentals unavailable: {info['error'][:100]}",
        }

    scores = {}

    # 1. Valuation (0-3)
    pe = info.get("pe_ratio")
    pb = info.get("pb_ratio")
    if pe is not None and pe > 0:
        if pe < 15:
            val_score = 3
        elif pe < 25:
            val_score = 2
        elif pe < 40:
            val_score = 1
        else:
            val_score = 0
    else:
        val_score = 1  # neutral if no P/E (could be loss-making)
    # Adjust for P/B
    if pb is not None and pb > 0:
        if pb < 1.5:
            val_score = min(3, val_score + 1)
        elif pb > 5:
            val_score = max(0, val_score - 1)
    scores["valuation"] = val_score

    # 2. Growth (0-3)
    rev_g = info.get("revenue_growth") or 0
    earn_g = info.get("earnings_growth") or 0
    if rev_g > 0.20 or earn_g > 0.25:
        growth_score = 3
    elif rev_g > 0.10 or earn_g > 0.15:
        growth_score = 2
    elif rev_g > 0.03 or earn_g > 0.05:
        growth_score = 1
    else:
        growth_score = 0
    scores["growth"] = growth_score

    # 3. Profitability (0-2)
    margins = info.get("profit_margins") or 0
    roe = info.get("return_on_equity") or 0
    if margins > 0.15 and roe > 0.15:
        prof_score = 2
    elif margins > 0.08 or roe > 0.10:
        prof_score = 1
    else:
        prof_score = 0
    scores["profitability"] = prof_score

    # 4. Financial health (0-2)
    de = info.get("debt_to_equity")
    cr = info.get("current_ratio")
    health_score = 0
    if de is not None:
        if de < 50:  # yfinance reports D/E as percentage (e.g. 50 = 0.5)
            health_score += 1
        elif de > 200:
            health_score -= 1
    if cr is not None and cr > 1.0:
        health_score += 1
    health_score = max(0, min(2, health_score))
    scores["financial_health"] = health_score

    total = sum(scores.values())

    # Explanation
    parts = []
    if pe: parts.append(f"P/E {pe:.1f}")
    if pb: parts.append(f"P/B {pb:.1f}")
    if rev_g: parts.append(f"Rev growth {rev_g*100:.1f}%")
    if earn_g: parts.append(f"EPS growth {earn_g*100:.1f}%")
    if margins: parts.append(f"Margin {margins*100:.1f}%")
    if roe: parts.append(f"ROE {roe*100:.1f}%")
    if de is not None: parts.append(f"D/E {de:.0f}")
    explanation = (
        f"Valuation {scores['valuation']}/3 | Growth {scores['growth']}/3 | "
        f"Profitability {scores['profitability']}/2 | Health {scores['financial_health']}/2 | "
        f"Total {total}/10. ({'; '.join(parts)})"
    )

    return {
        "symbol": symbol,
        "score": total,
        "max_score": 10,
        "available": True,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "fundamentals": {k: v for k, v in info.items() if v is not None},
        "scores": scores,
        "explanation": explanation,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Fundamental Analysis Layer")
    ap.add_argument("symbol", help="Stock symbol")
    args = ap.parse_args()
    result = get_fundamental_score(args.symbol)
    print(json.dumps(result, indent=2, default=str))
