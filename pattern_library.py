"""
pattern_library.py - Historical chart pattern detection and storage.

Detects and stores chart patterns from historical data so the AI can find
similar past setups. Patterns stored:
  - Breakouts (price crosses 20-day high on high volume)
  - Gap-ups (open > previous high by 1%+)
  - Gap-downs (open < previous low by 1%+)
  - Bull flags (consolidation after a 10%+ rally)
  - Reversals (3+ down days followed by a strong up day)
  - Support bounces (price touches 50-day low and closes above it)
  - Resistance breaks (price closes above 20-day high after approaching it)

Each pattern is stored with:
  - The pattern type and description
  - The stock symbol and date
  - The price action that followed (1d, 5d, 20d outcomes)
  - The regime at the time

Usage:
    from pattern_library import PatternLibrary
    pl = PatternLibrary()
    pl.scan_stock("RELIANCE.NS")  # detect & store patterns from history
    similar = pl.find_similar("bull flag breakout high volume trending up")
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_warehouse import get_warehouse
from strategies import fetch_stock_data
from advisor import analysis as an
from advisor.core import Regime


class PatternLibrary:
    """Detects, stores, and retrieves historical chart patterns."""

    def __init__(self):
        self.dw = get_warehouse()

    def scan_stock(self, symbol: str) -> int:
        """Scan a stock's full history for patterns and store them.

        Returns the number of patterns detected and stored.
        """
        sym = symbol if "." in symbol else f"{symbol}.NS"
        print(f"  Scanning {sym} for patterns...")

        try:
            df = fetch_stock_data(sym, period="5y")
        except Exception as e:
            print(f"    ! data fetch failed: {e}")
            return 0

        if len(df) < 60:
            print(f"    ! insufficient data ({len(df)} bars)")
            return 0

        patterns = []
        for i in range(60, len(df) - 20):  # need 20 bars ahead for outcomes
            detected = self._detect_patterns_at(df, i)
            for p in detected:
                # Compute outcomes (1d, 5d, 20d forward returns)
                entry = float(df["close"].iloc[i])
                p1 = float(df["close"].iloc[i + 1]) if i + 1 < len(df) else entry
                p5 = float(df["close"].iloc[i + 5]) if i + 5 < len(df) else entry
                p20 = float(df["close"].iloc[i + 20]) if i + 20 < len(df) else entry

                p["outcome_1d"] = round((p1 - entry) / entry * 100, 2)
                p["outcome_5d"] = round((p5 - entry) / entry * 100, 2)
                p["outcome_20d"] = round((p20 - entry) / entry * 100, 2)
                p["entry_price"] = round(entry, 2)
                p["symbol"] = sym
                p["date"] = str(df.index[i].date())

                # Get regime at detection time
                try:
                    sub = df.iloc[:i + 1]
                    if len(sub) >= 30:
                        p["regime"] = an.classify_regime(sub).regime.value
                    else:
                        p["regime"] = "unknown"
                except Exception:
                    p["regime"] = "unknown"

                patterns.append(p)

        if not patterns:
            print(f"    no patterns detected")
            return 0

        # Store in vector DB
        documents = [p["description"] for p in patterns]
        metadatas = [{k: v for k, v in p.items() if k != "description"} for p in patterns]
        ids = [f"pattern_{sym}_{p['date']}_{p['type']}_{i}" for i, p in enumerate(patterns)]

        col = self.dw.get_collection("pattern_library")
        try:
            col.delete(ids=ids)  # remove old entries
        except Exception:
            pass
        col.add(documents=documents, metadatas=metadatas, ids=ids)

        # Print summary
        type_counts = {}
        for p in patterns:
            type_counts[p["type"]] = type_counts.get(p["type"], 0) + 1
        print(f"    detected {len(patterns)} patterns: {type_counts}")

        return len(patterns)

    def _detect_patterns_at(self, df: pd.DataFrame, i: int) -> list[dict]:
        """Detect all patterns at bar i."""
        patterns = []
        row = df.iloc[i]
        close = float(row["close"])
        open_ = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        vol = float(row["volume"])

        # Need prior data
        if i < 20:
            return patterns

        prev_close = float(df["close"].iloc[i - 1])
        prev_high = float(df["high"].iloc[i - 1])
        prev_low = float(df["low"].iloc[i - 1])
        avg_vol = float(df["volume"].iloc[i - 20:i].mean()) if i >= 20 else vol
        hi20 = float(df["high"].iloc[i - 20:i].max())
        lo20 = float(df["low"].iloc[i - 20:i].min())

        # 1. Breakout: close above 20-day high on above-average volume
        if close > hi20 and vol > avg_vol * 1.5:
            patterns.append({
                "type": "breakout",
                "description": f"Breakout above 20-day high ({hi20:.1f}) on {vol/avg_vol:.1f}x average volume. "
                               f"Price closed at {close:.1f}, up {(close/prev_close-1)*100:.1f}%.",
            })

        # 2. Gap-up: opens above previous high by 1%+
        gap_pct = (open_ / prev_close - 1) * 100
        if gap_pct > 1.0:
            patterns.append({
                "type": "gap_up",
                "description": f"Gap-up of {gap_pct:.1f}% (open {open_:.1f} vs prev close {prev_close:.1f}). "
                               f"Closed at {close:.1f}, {'held the gap' if close > open_ else 'filled the gap'}.",
            })

        # 3. Gap-down: opens below previous low by 1%+
        if gap_pct < -1.0:
            patterns.append({
                "type": "gap_down",
                "description": f"Gap-down of {gap_pct:.1f}% (open {open_:.1f} vs prev close {prev_close:.1f}). "
                               f"Closed at {close:.1f}, {'recovered' if close > open_ else 'stayed down'}.",
            })

        # 4. Bull flag: 10%+ rally in 20 days, then 3-day consolidation (range < 3%)
        if i >= 23:
            rally_start = float(df["close"].iloc[i - 20])
            rally_end = float(df["close"].iloc[i - 3])
            rally_pct = (rally_end / rally_start - 1) * 100
            if rally_pct > 10:
                # Check 3-day consolidation
                consol_range = (df["high"].iloc[i - 3:i].max() - df["low"].iloc[i - 3:i].min()) / rally_end * 100
                if consol_range < 3:
                    patterns.append({
                        "type": "bull_flag",
                        "description": f"Bull flag after {rally_pct:.1f}% rally. "
                                       f"3-day consolidation range {consol_range:.1f}%. "
                                       f"Price at {close:.1f}.",
                    })

        # 5. Reversal: 3+ down days then strong up day
        if i >= 3:
            down_count = sum(1 for k in range(1, 4) if df["close"].iloc[i - k] < df["close"].iloc[i - k - 1])
            if down_count >= 3 and close > prev_close:
                up_pct = (close / prev_close - 1) * 100
                if up_pct > 1:
                    patterns.append({
                        "type": "reversal",
                        "description": f"Reversal after {down_count} down days. "
                                       f"Up {up_pct:.1f}% on volume {vol/avg_vol:.1f}x average. "
                                       f"Price at {close:.1f}.",
                    })

        # 6. Support bounce: touches 20-day low and closes above it
        if low <= lo20 * 1.005 and close > lo20:
            patterns.append({
                "type": "support_bounce",
                "description": f"Support bounce at 20-day low ({lo20:.1f}). "
                               f"Touched {low:.1f}, closed at {close:.1f}.",
            })

        # 7. Volume spike: volume > 3x average with price move
        if vol > avg_vol * 3:
            price_chg = (close / prev_close - 1) * 100
            patterns.append({
                "type": "volume_spike",
                "description": f"Volume spike {vol/avg_vol:.1f}x average with price {'up' if price_chg > 0 else 'down'} "
                               f"{abs(price_chg):.1f}%. Price at {close:.1f}.",
            })

        return patterns

    def find_similar(self, description: str, n: int = 5) -> list[dict]:
        """Find historical patterns similar to the described setup."""
        results = self.dw.query(description, collection="pattern_library", n=n)
        for r in results:
            meta = r["metadata"]
            r["outcome_summary"] = (
                f"1d: {meta.get('outcome_1d', '?')}%, "
                f"5d: {meta.get('outcome_5d', '?')}%, "
                f"20d: {meta.get('outcome_20d', '?')}%"
            )
        return results

    def get_pattern_stats(self) -> dict:
        """Return stats about stored patterns by type."""
        col = self.dw.get_collection("pattern_library")
        if not col or col.count() == 0:
            return {"total": 0, "by_type": {}}
        # Get all metadata (up to 1000 entries)
        try:
            all_data = col.get(limit=1000, include=["metadatas"])
            type_counts = {}
            for m in all_data.get("metadatas", []):
                t = m.get("type", "unknown")
                type_counts[t] = type_counts.get(t, 0) + 1
            return {"total": col.count(), "by_type": type_counts}
        except Exception:
            return {"total": col.count(), "by_type": {}}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Pattern Library")
    sub = ap.add_subparser(dest="command", required=True)
    sc = sub.add_parser("scan", help="Scan a stock for patterns")
    sc.add_argument("symbol")
    q = sub.add_parser("query", help="Find similar patterns")
    q.add_argument("description")
    sub.add_parser("stats", help="Show pattern stats")
    args = ap.parse_args()

    pl = PatternLibrary()
    if args.command == "scan":
        n = pl.scan_stock(args.symbol)
        print(f"\nStored {n} patterns.")
    elif args.command == "query":
        results = pl.find_similar(args.description)
        print(f"\nSimilar patterns ({len(results)}):")
        for r in results:
            m = r["metadata"]
            print(f"  [{r['distance']:.3f}] {m.get('type', '?')} {m.get('symbol', '?')} "
                  f"({m.get('date', '?')}) {m.get('regime', '?')}")
            print(f"    {r['document'][:120]}")
            print(f"    Outcome: {r['outcome_summary']}")
    elif args.command == "stats":
        print(json.dumps(pl.get_pattern_stats(), indent=2))
