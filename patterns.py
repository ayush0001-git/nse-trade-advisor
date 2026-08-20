"""
patterns.py - Candlestick pattern detection (no external TA-Lib dependency).

Based on research from GitHub candlestick-patterns topics and classic
Japanese candlestick analysis (Steve Nison's work). All patterns are
detected with pure-pandas logic so they always install and run.

Patterns implemented (10 total, 5 bullish + 5 bearish):

  BULLISH:
    1. Hammer         - small body at top, long lower wick (>= 2x body)
    2. Bullish Engulfing - large green candle engulfs prior red candle
    3. Morning Star   - 3-candle: red → small body → large green
    4. Bullish Harami - small green body inside prior large red body
    5. Piercing Line  - opens below prior low, closes above prior midpoint

  BEARISH:
    6. Shooting Star  - small body at bottom, long upper wick
    7. Bearish Engulfing - large red candle engulfs prior green candle
    8. Evening Star   - 3-candle: green → small body → large red
    9. Bearish Harami - small red body inside prior large green body
   10. Dark Cloud Cover - opens above prior high, closes below prior midpoint

Each function returns True/False for the latest bar. The `detect_all()`
function returns a list of all patterns detected on the latest bar.

Usage:
    from patterns import detect_all
    found = detect_all(df)  # df is an OHLCV DataFrame
    # -> {"hammer": False, "bullish_engulfing": True, ...}
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# =========================================================================== #
#  Helpers
# =========================================================================== #
def _body(open_: float, close: float) -> float:
    """Absolute body size."""
    return abs(close - open_)


def _upper_wick(high: float, open_: float, close: float) -> float:
    return high - max(open_, close)


def _lower_wick(low: float, open_: float, close: float) -> float:
    return min(open_, close) - low


def _is_green(open_: float, close: float) -> bool:
    return close > open_


def _is_red(open_: float, close: float) -> bool:
    return close < open_


# =========================================================================== #
#  Bullish patterns
# =========================================================================== #
def hammer(df: pd.DataFrame, i: int | None = None) -> bool:
    """Hammer: small body at top, long lower wick (>= 2x body), green or red.

    Context: appears after a downtrend, signals reversal up.
    """
    i = i if i is not None else len(df) - 1
    if i < 1:
        return False
    row = df.iloc[i]
    o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
    body = _body(o, c)
    if body <= 0:
        return False
    lower = _lower_wick(l, o, c)
    upper = _upper_wick(h, o, c)
    # Lower wick must be at least 2x body, upper wick small (< 0.3 * body)
    return lower >= 2.0 * body and upper <= 0.3 * body


def bullish_engulfing(df: pd.DataFrame, i: int | None = None) -> bool:
    """Bullish Engulfing: large green candle engulfs prior red candle."""
    i = i if i is not None else len(df) - 1
    if i < 1:
        return False
    prev = df.iloc[i - 1]
    curr = df.iloc[i]
    po, pc = float(prev["open"]), float(prev["close"])
    co, cc = float(curr["open"]), float(curr["close"])
    if not _is_red(po, pc) or not _is_green(co, cc):
        return False
    # Current green candle's body engulfs prior red candle's body
    return co <= pc and cc >= po


def morning_star(df: pd.DataFrame, i: int | None = None) -> bool:
    """Morning Star: red → small body → large green that closes above first's mid."""
    i = i if i is not None else len(df) - 1
    if i < 2:
        return False
    r1 = df.iloc[i - 2]
    r2 = df.iloc[i - 1]
    r3 = df.iloc[i]
    o1, c1 = float(r1["open"]), float(r1["close"])
    o2, c2 = float(r2["open"]), float(r2["close"])
    o3, c3 = float(r3["open"]), float(r3["close"])
    # 1st: large red
    if not _is_red(o1, c1) or _body(o1, c1) < 0.01 * c1:
        return False
    # 2nd: small body (any color)
    if _body(o2, c2) > 0.5 * _body(o1, c1):
        return False
    # 3rd: large green closing above midpoint of 1st
    if not _is_green(o3, c3) or _body(o3, c3) < 0.5 * _body(o1, c1):
        return False
    return c3 > (o1 + c1) / 2


def bullish_harami(df: pd.DataFrame, i: int | None = None) -> bool:
    """Bullish Harami: small green body inside prior large red body."""
    i = i if i is not None else len(df) - 1
    if i < 1:
        return False
    prev = df.iloc[i - 1]
    curr = df.iloc[i]
    po, pc = float(prev["open"]), float(prev["close"])
    co, cc = float(curr["open"]), float(curr["close"])
    if not _is_red(po, pc) or not _is_green(co, cc):
        return False
    # Current body inside prior body
    return co >= pc and cc <= po and _body(co, cc) < 0.5 * _body(po, pc)


def piercing_line(df: pd.DataFrame, i: int | None = None) -> bool:
    """Piercing Line: opens below prior low, closes above prior midpoint."""
    i = i if i is not None else len(df) - 1
    if i < 1:
        return False
    prev = df.iloc[i - 1]
    curr = df.iloc[i]
    po, ph, pl, pc = float(prev["open"]), float(prev["high"]), float(prev["low"]), float(prev["close"])
    co, cc = float(curr["open"]), float(curr["close"])
    if not _is_red(po, pc) or not _is_green(co, cc):
        return False
    # Opens below prior low, closes above prior midpoint but below prior open
    return co < pl and cc > (po + pc) / 2 and cc < po


# =========================================================================== #
#  Bearish patterns
# =========================================================================== #
def shooting_star(df: pd.DataFrame, i: int | None = None) -> bool:
    """Shooting Star: small body at bottom, long upper wick (>= 2x body)."""
    i = i if i is not None else len(df) - 1
    if i < 1:
        return False
    row = df.iloc[i]
    o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
    body = _body(o, c)
    if body <= 0:
        return False
    upper = _upper_wick(h, o, c)
    lower = _lower_wick(l, o, c)
    return upper >= 2.0 * body and lower <= 0.3 * body


def bearish_engulfing(df: pd.DataFrame, i: int | None = None) -> bool:
    """Bearish Engulfing: large red candle engulfs prior green candle."""
    i = i if i is not None else len(df) - 1
    if i < 1:
        return False
    prev = df.iloc[i - 1]
    curr = df.iloc[i]
    po, pc = float(prev["open"]), float(prev["close"])
    co, cc = float(curr["open"]), float(curr["close"])
    if not _is_green(po, pc) or not _is_red(co, cc):
        return False
    return co >= pc and cc <= po


def evening_star(df: pd.DataFrame, i: int | None = None) -> bool:
    """Evening Star: green → small body → large red closing below first's mid."""
    i = i if i is not None else len(df) - 1
    if i < 2:
        return False
    r1 = df.iloc[i - 2]
    r2 = df.iloc[i - 1]
    r3 = df.iloc[i]
    o1, c1 = float(r1["open"]), float(r1["close"])
    o2, c2 = float(r2["open"]), float(r2["close"])
    o3, c3 = float(r3["open"]), float(r3["close"])
    if not _is_green(o1, c1) or _body(o1, c1) < 0.01 * c1:
        return False
    if _body(o2, c2) > 0.5 * _body(o1, c1):
        return False
    if not _is_red(o3, c3) or _body(o3, c3) < 0.5 * _body(o1, c1):
        return False
    return c3 < (o1 + c1) / 2


def bearish_harami(df: pd.DataFrame, i: int | None = None) -> bool:
    """Bearish Harami: small red body inside prior large green body."""
    i = i if i is not None else len(df) - 1
    if i < 1:
        return False
    prev = df.iloc[i - 1]
    curr = df.iloc[i]
    po, pc = float(prev["open"]), float(prev["close"])
    co, cc = float(curr["open"]), float(curr["close"])
    if not _is_green(po, pc) or not _is_red(co, cc):
        return False
    return co <= pc and cc >= po and _body(co, cc) < 0.5 * _body(po, pc)


def dark_cloud_cover(df: pd.DataFrame, i: int | None = None) -> bool:
    """Dark Cloud Cover: opens above prior high, closes below prior midpoint."""
    i = i if i is not None else len(df) - 1
    if i < 1:
        return False
    prev = df.iloc[i - 1]
    curr = df.iloc[i]
    po, ph, pl, pc = float(prev["open"]), float(prev["high"]), float(prev["low"]), float(prev["close"])
    co, cc = float(curr["open"]), float(curr["close"])
    if not _is_green(po, pc) or not _is_red(co, cc):
        return False
    return co > ph and cc < (po + pc) / 2 and cc > po


# =========================================================================== #
#  Registry
# =========================================================================== #
BULLISH_PATTERNS = {
    "hammer": {"fn": hammer, "name": "Hammer", "direction": "bullish",
               "description": "Small body at top, long lower wick — reversal after downtrend."},
    "bullish_engulfing": {"fn": bullish_engulfing, "name": "Bullish Engulfing",
                          "direction": "bullish",
                          "description": "Large green candle engulfs prior red — strong bullish reversal."},
    "morning_star": {"fn": morning_star, "name": "Morning Star", "direction": "bullish",
                     "description": "3-candle bottom reversal: red → small → large green."},
    "bullish_harami": {"fn": bullish_harami, "name": "Bullish Harami", "direction": "bullish",
                       "description": "Small green inside prior large red — indecision turning bullish."},
    "piercing_line": {"fn": piercing_line, "name": "Piercing Line", "direction": "bullish",
                      "description": "Opens below prior low, closes above midpoint — bullish reversal."},
}

BEARISH_PATTERNS = {
    "shooting_star": {"fn": shooting_star, "name": "Shooting Star", "direction": "bearish",
                      "description": "Small body at bottom, long upper wick — reversal after uptrend."},
    "bearish_engulfing": {"fn": bearish_engulfing, "name": "Bearish Engulfing",
                          "direction": "bearish",
                          "description": "Large red candle engulfs prior green — strong bearish reversal."},
    "evening_star": {"fn": evening_star, "name": "Evening Star", "direction": "bearish",
                     "description": "3-candle top reversal: green → small → large red."},
    "bearish_harami": {"fn": bearish_harami, "name": "Bearish Harami", "direction": "bearish",
                       "description": "Small red inside prior large green — indecision turning bearish."},
    "dark_cloud_cover": {"fn": dark_cloud_cover, "name": "Dark Cloud Cover", "direction": "bearish",
                         "description": "Opens above prior high, closes below midpoint — bearish reversal."},
}

ALL_PATTERNS = {**BULLISH_PATTERNS, **BEARISH_PATTERNS}


def detect_all(df: pd.DataFrame, i: int | None = None) -> dict:
    """Detect all patterns on the latest bar (or bar i).

    Returns a dict mapping pattern_key -> bool.
    """
    i = i if i is not None else len(df) - 1
    return {key: bool(meta["fn"](df, i)) for key, meta in ALL_PATTERNS.items()}


def detect_with_context(df: pd.DataFrame, i: int | None = None) -> dict:
    """Detect patterns plus their direction + descriptions for display."""
    i = i if i is not None else len(df) - 1
    detected = detect_all(df, i)
    return {
        "patterns_found": [k for k, v in detected.items() if v],
        "bullish_patterns": [
            {"key": k, "name": BULLISH_PATTERNS[k]["name"],
             "description": BULLISH_PATTERNS[k]["description"]}
            for k, v in detected.items() if v and k in BULLISH_PATTERNS
        ],
        "bearish_patterns": [
            {"key": k, "name": BEARISH_PATTERNS[k]["name"],
             "description": BEARISH_PATTERNS[k]["description"]}
            for k, v in detected.items() if v and k in BEARISH_PATTERNS
        ],
        "n_bullish": sum(1 for k, v in detected.items() if v and k in BULLISH_PATTERNS),
        "n_bearish": sum(1 for k, v in detected.items() if v and k in BEARISH_PATTERNS),
        "bias": ("bullish" if sum(1 for k, v in detected.items() if v and k in BULLISH_PATTERNS) >
                 sum(1 for k, v in detected.items() if v and k in BEARISH_PATTERNS) else
                 "bearish" if sum(1 for k, v in detected.items() if v and k in BEARISH_PATTERNS) >
                 sum(1 for k, v in detected.items() if v and k in BULLISH_PATTERNS) else "neutral"),
    }


if __name__ == "__main__":
    # Self-test on a synthetic DataFrame
    import sys
    sys.path.insert(0, ".")
    from advisor import analysis as an

    # Build a small synthetic frame
    n = 50
    rng = np.random.default_rng(42)
    close = 100 * np.cumprod(1 + rng.normal(0.001, 0.015, n))
    df = pd.DataFrame({
        "open": np.roll(close, 1),
        "high": close * (1 + np.abs(rng.normal(0, 0.01, n))),
        "low": close * (1 - np.abs(rng.normal(0, 0.01, n))),
        "close": close,
        "volume": rng.integers(1e6, 5e6, n).astype(float),
    })
    df.loc[df.index[0], "open"] = close[0]
    df = an.compute_indicators(df, include_vwap=False)
    result = detect_with_context(df)
    print("Latest bar patterns detected:")
    print(f"  Bullish: {result['n_bullish']}, Bearish: {result['n_bearish']}, Bias: {result['bias']}")
    for p in result["bullish_patterns"]:
        print(f"  + {p['name']}: {p['description']}")
    for p in result["bearish_patterns"]:
        print(f"  - {p['name']}: {p['description']}")
    if not result["patterns_found"]:
        print("  (no patterns on latest bar)")
    print(f"\nAll {len(ALL_PATTERNS)} pattern detectors loaded OK.")
