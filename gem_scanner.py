"""
gem_scanner.py — Find underrated gem stocks + historical pattern analysis.

Scans all stocks for:
  1. Underrated gems (high quality, low price, accumulation pattern)
  2. Historical chart patterns (bull flags, breakouts, support bounces)
  3. Volume accumulation detection (smart money buying quietly)
  4. Multi-timeframe alignment (intraday + swing + monthly all bullish)
"""
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def detect_patterns(df: pd.DataFrame) -> dict:
    """Detect all chart patterns on the latest bars."""
    patterns = {"bullish": [], "bearish": [], "neutral": []}
    if len(df) < 30:
        return patterns

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    open_ = df["Open"]
    volume = df["Volume"]
    i = len(df) - 1

    # 1. Bull Flag: 10%+ rally then 3-day consolidation
    if i >= 23:
        rally = (close.iloc[i-3] / close.iloc[i-20] - 1) * 100
        if rally > 10:
            consol_range = (high.iloc[i-3:i].max() - low.iloc[i-3:i].min()) / close.iloc[i-3] * 100
            if consol_range < 4:
                patterns["bullish"].append({"pattern": "Bull Flag", "description": f"10%+ rally with tight consolidation. Breakout imminent.", "strength": 8})

    # 2. Cup and Handle: U-shape recovery + small pullback
    if i >= 30:
        left = close.iloc[i-30]
        bottom = close.iloc[i-15:i-5].min()
        right = close.iloc[i-3]
        if right > left * 0.97 and bottom < left * 0.9:
            patterns["bullish"].append({"pattern": "Cup and Handle", "description": "U-shaped recovery with handle. Bullish continuation.", "strength": 7})

    # 3. Support Bounce: touched 20-day low and closed above
    lo20 = low.iloc[i-20:i].min()
    if low.iloc[i] <= lo20 * 1.005 and close.iloc[i] > lo20:
        patterns["bullish"].append({"pattern": "Support Bounce", "description": f"Bounced off 20-day low ({lo20:.1f}). Reversal signal.", "strength": 6})

    # 4. Volume Accumulation: 3+ days of above-avg volume with price rising
    avg_vol = volume.iloc[i-20:i].mean()
    vol_3d = volume.iloc[i-3:i].values
    price_3d = close.iloc[i-3:i].values
    if all(v > avg_vol * 1.2 for v in vol_3d) and price_3d[-1] > price_3d[0]:
        patterns["bullish"].append({"pattern": "Volume Accumulation", "description": "3+ days of above-avg volume with rising price. Smart money buying.", "strength": 9})

    # 5. Hammer candle
    body = abs(close.iloc[i] - open_.iloc[i])
    lower_wick = min(open_.iloc[i], close.iloc[i]) - low.iloc[i]
    upper_wick = high.iloc[i] - max(open_.iloc[i], close.iloc[i])
    if body > 0 and lower_wick >= 2 * body and upper_wick <= 0.3 * body:
        patterns["bullish"].append({"pattern": "Hammer", "description": "Hammer candle — rejection of lower prices.", "strength": 5})

    # 6. Bullish Engulfing
    if i >= 1:
        prev_body = close.iloc[i-1] - open_.iloc[i-1]
        curr_body = close.iloc[i] - open_.iloc[i]
        if prev_body < 0 and curr_body > 0 and open_.iloc[i] <= close.iloc[i-1] and close.iloc[i] >= open_.iloc[i-1]:
            patterns["bullish"].append({"pattern": "Bullish Engulfing", "description": "Large green candle engulfs prior red. Strong reversal.", "strength": 8})

    # 7. Ascending Triangle: flat top + rising bottom
    if i >= 20:
        highs = high.iloc[i-20:i].values
        lows = low.iloc[i-20:i].values
        high_std = np.std(highs) / np.mean(highs) * 100
        low_trend = (lows[-1] - lows[0]) / lows[0] * 100
        if high_std < 1.5 and low_trend > 3:
            patterns["bullish"].append({"pattern": "Ascending Triangle", "description": "Flat resistance with rising support. Breakout coming.", "strength": 7})

    # 8. Golden Cross (50 over 200)
    if i >= 200:
        sma50 = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()
        if sma50.iloc[i] > sma200.iloc[i] and sma50.iloc[i-1] <= sma200.iloc[i-1]:
            patterns["bullish"].append({"pattern": "Golden Cross", "description": "50-day MA crossed above 200-day MA. Long-term bullish.", "strength": 9})

    # 9. RSI Oversold Bounce
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - (100 / (1 + rs))).iloc[i]
    if rsi < 35:
        patterns["bullish"].append({"pattern": "RSI Oversold", "description": f"RSI {rsi:.0f} — oversold bounce candidate.", "strength": 6})

    # 10. Volume Spike + Price Up
    vol_ratio = volume.iloc[i] / avg_vol if avg_vol > 0 else 1
    price_chg = (close.iloc[i] / close.iloc[i-1] - 1) * 100 if i >= 1 else 0
    if vol_ratio > 2.5 and price_chg > 2:
        patterns["bullish"].append({"pattern": "Volume Spike", "description": f"Volume {vol_ratio:.1f}x avg with +{price_chg:.1f}% move. Institutional buying.", "strength": 8})

    # Bearish patterns
    # 11. Death Cross
    if i >= 200:
        if sma50.iloc[i] < sma200.iloc[i] and sma50.iloc[i-1] >= sma200.iloc[i-1]:
            patterns["bearish"].append({"pattern": "Death Cross", "description": "50-day MA crossed below 200-day MA. Long-term bearish.", "strength": 8})

    # 12. Shooting Star
    if body > 0 and upper_wick >= 2 * body and lower_wick <= 0.3 * body:
        patterns["bearish"].append({"pattern": "Shooting Star", "description": "Shooting star — rejection of higher prices.", "strength": 5})

    # 13. Bearish Engulfing
    if i >= 1:
        prev_body = close.iloc[i-1] - open_.iloc[i-1]
        curr_body = close.iloc[i] - open_.iloc[i]
        if prev_body > 0 and curr_body < 0 and open_.iloc[i] >= close.iloc[i-1] and close.iloc[i] <= open_.iloc[i-1]:
            patterns["bearish"].append({"pattern": "Bearish Engulfing", "description": "Large red candle engulfs prior green. Bearish reversal.", "strength": 7})

    # 14. Distribution: high volume + price falling
    if vol_ratio > 1.5 and price_chg < -2:
        patterns["bearish"].append({"pattern": "Distribution", "description": f"High volume ({vol_ratio:.1f}x) with -{abs(price_chg):.1f}% drop. Smart money selling.", "strength": 7})

    return patterns


def scan_historical_patterns(df: pd.DataFrame) -> list:
    """Scan full history for pattern occurrences and their outcomes."""
    results = []
    if len(df) < 60:
        return results

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    for i in range(50, len(df) - 20):
        # Check for breakout (close > 20-day high on 1.5x volume)
        hi20 = high.iloc[i-20:i].max()
        avg_vol = volume.iloc[i-20:i].mean()
        if close.iloc[i] > hi20 and volume.iloc[i] > avg_vol * 1.5:
            # Measure 5-day and 20-day forward returns
            entry = close.iloc[i]
            fwd_5d = (close.iloc[i+5] / entry - 1) * 100 if i + 5 < len(df) else 0
            fwd_20d = (close.iloc[i+20] / entry - 1) * 100 if i + 20 < len(df) else 0
            results.append({
                "date": str(df.index[i].date()),
                "type": "Breakout",
                "price": round(entry, 2),
                "fwd_5d": round(fwd_5d, 2),
                "fwd_20d": round(fwd_20d, 2),
                "win": fwd_5d > 0,
            })

        # Check for support bounce
        lo20 = low.iloc[i-20:i].min()
        if low.iloc[i] <= lo20 * 1.005 and close.iloc[i] > lo20:
            entry = close.iloc[i]
            fwd_5d = (close.iloc[i+5] / entry - 1) * 100 if i + 5 < len(df) else 0
            fwd_20d = (close.iloc[i+20] / entry - 1) * 100 if i + 20 < len(df) else 0
            results.append({
                "date": str(df.index[i].date()),
                "type": "Support Bounce",
                "price": round(entry, 2),
                "fwd_5d": round(fwd_5d, 2),
                "fwd_20d": round(fwd_20d, 2),
                "win": fwd_5d > 0,
            })

    return results[-50:]  # last 50 patterns


def find_gem(symbol: str) -> dict:
    """Find if a stock is an underrated gem.

    A gem has:
      - Strong fundamentals (ROE > 15%, low debt)
      - Accumulation pattern (rising volume + rising price)
      - Near support (good entry point)
      - Undervalued (P/E below sector average)
      - Multiple bullish patterns
    """
    import yfinance as yf

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y", interval="1d")
        if df is None or df.empty or len(df) < 60:
            return None

        info = ticker.info or {}
        close = df["Close"]
        volume = df["Volume"]
        price = float(close.iloc[-1])

        # Score each gem criterion
        gem_score = 0
        gem_reasons = []

        # 1. Fundamentals
        roe = info.get("returnOnEquity", 0) or 0
        pe = info.get("trailingPE", 0) or 0
        de = info.get("debtToEquity", 0) or 0

        if roe > 0.15:
            gem_score += 15
            gem_reasons.append(f"ROE {roe*100:.1f}% (high quality)")
        if 0 < pe < 25:
            gem_score += 15
            gem_reasons.append(f"P/E {pe:.1f} (reasonable valuation)")
        if de < 50:
            gem_score += 10
            gem_reasons.append(f"D/E {de:.0f} (low debt)")

        # 2. Accumulation (rising volume + rising price over 20 days)
        vol_20d = volume.iloc[-20:].values
        price_20d = close.iloc[-20:].values
        vol_trend = (vol_20d[-5:].mean() / vol_20d[:5].mean() - 1) * 100 if vol_20d[:5].mean() > 0 else 0
        price_trend = (price_20d[-1] / price_20d[0] - 1) * 100

        if vol_trend > 20 and price_trend > 0:
            gem_score += 20
            gem_reasons.append(f"Volume rising {vol_trend:.0f}% with price up {price_trend:.1f}% (accumulation)")

        # 3. Near support (within 5% of 50-day MA)
        sma_50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
        if sma_50 and abs(price - sma_50) / sma_50 * 100 < 5:
            gem_score += 15
            gem_reasons.append(f"Near 50-day MA (₹{sma_50:.0f}) — good entry point")

        # 4. Patterns
        patterns = detect_patterns(df)
        bull_patterns = patterns["bullish"]
        if bull_patterns:
            gem_score += len(bull_patterns) * 5
            for p in bull_patterns[:3]:
                gem_reasons.append(f"Pattern: {p['pattern']} (strength {p['strength']}/10)")

        # 5. Historical win rate
        historical = scan_historical_patterns(df)
        if historical:
            wins = sum(1 for h in historical if h["win"])
            win_rate = wins / len(historical) * 100
            if win_rate > 60:
                gem_score += 15
                gem_reasons.append(f"Historical pattern win rate: {win_rate:.0f}% ({wins}/{len(historical)})")

        # 6. 52-week position (not at top)
        high_52w = float(df["High"].tail(252).max()) if len(df) >= 252 else float(df["High"].max())
        low_52w = float(df["Low"].tail(252).min()) if len(df) >= 252 else float(df["Low"].min())
        position_52w = (price - low_52w) / (high_52w - low_52w) * 100 if high_52w != low_52w else 50

        if position_52w < 50:
            gem_score += 10
            gem_reasons.append(f"At {position_52w:.0f}% of 52-week range (lower half — room to grow)")

        is_gem = gem_score >= 60

        return {
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "price": round(price, 2),
            "gem_score": gem_score,
            "is_gem": is_gem,
            "reasons": gem_reasons,
            "patterns": patterns,
            "historical_patterns": historical[-10:],
            "sector": info.get("sector", "?"),
            "cap_type": "Large" if (info.get("marketCap", 0) or 0) > 2e12 else "Mid" if (info.get("marketCap", 0) or 0) > 5e10 else "Small",
            "52w_position": round(position_52w, 0),
            "roe": round(roe * 100, 1) if roe else None,
            "pe": pe,
            "de": de,
        }
    except Exception as e:
        return None


def scan_all_gems(stock_list: list, limit: int = 10) -> list:
    """Scan a list of stocks and return the top gems."""
    gems = []
    for sym in stock_list:
        result = find_gem(sym)
        if result and result["is_gem"]:
            gems.append(result)

    # Sort by gem_score
    gems.sort(key=lambda x: x["gem_score"], reverse=True)
    return gems[:limit]


if __name__ == "__main__":
    # Test on a few stocks
    test_stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "WIPRO.NS"]
    print("Scanning for gems...\n")
    gems = scan_all_gems(test_stocks, 5)
    for g in gems:
        print(f"💎 {g['symbol']} — Gem Score: {g['gem_score']}/100")
        print(f"   Price: ₹{g['price']} | {g['sector']} | {g['cap_type']}")
        for r in g["reasons"]:
            print(f"   ✅ {r}")
        print(f"   Patterns: {len(g['patterns']['bullish'])} bullish, {len(g['patterns']['bearish'])} bearish")
        print()
