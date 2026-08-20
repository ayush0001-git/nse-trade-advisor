"""
sector_rotation.py - Top-down sector context overlay.

Inspired by Zerodha Varsity's "Top-down vs Bottom-up" article:
  https://zerodha.com/varsity/chapter/top-down-versus-bottom-up-stock-picking-strategies/

The advisor currently analyzes each stock in isolation. This module adds the
missing top-down layer: it ranks Nifty sector indices by momentum, then tags
each stock with its sector's strength. The advisor can then REWARD trades in
strong sectors and PENALIZE trades in weak sectors.

Nifty sector indices used (Yahoo tickers):
  - NIFTY BANK          (^NSEBANK)
  - NIFTY IT            (^CNXIT)
  - NIFTY AUTO          (^CNXAUTO)
  - NIFTY FMCG          (^CNXFMCG)
  - NIFTY PHARMA        (^CNXPHARMA)
  - NIFTY METAL         (^CNXMETAL)
  - NIFTY ENERGY        (^CNXENERGY)
  - NIFTY REALTY        (^CNXREALTY)
  - NIFTY MEDIA         (^CNXMEDIA)
  - NIFTY PSU BANK      (^CNXPSUBANK)
  - NIFTY FIN SERVICE   (NIFTY_FIN_SERVICE.NS)
  - NIFTY MIDCAP 100    (^CNXMIDCAP)
  - NIFTY SMALLCAP 100  (^CNXSMALLCAP)

For each stock symbol we look up its sector (hard-coded mapping for the
top 50 NSE stocks; extend as needed). Stocks without a sector mapping get
NEUTRAL context.

Usage:
    from sector_rotation import SectorRotation
    sr = SectorRotation()
    sr.refresh()                       # fetch latest sector data
    context = sr.get_context("RELIANCE.NS")
    # -> {"sector": "ENERGY", "rank": 2, "momentum": +12.3%, "bias": "BULLISH"}
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from advisor import analysis as an

CACHE_PATH = PROJECT_ROOT / "rl_models" / "sector_data.json"
CACHE_PATH.parent.mkdir(exist_ok=True)


# =========================================================================== #
#  Nifty sector indices (Yahoo tickers)
# =========================================================================== #
SECTOR_INDICES = {
    "BANK":       "^NSEBANK",
    "IT":         "^CNXIT",
    "AUTO":       "^CNXAUTO",
    "FMCG":       "^CNXFMCG",
    "PHARMA":     "^CNXPHARMA",
    "METAL":      "^CNXMETAL",
    "ENERGY":     "^CNXENERGY",
    "REALTY":     "^CNXREALTY",
    "MEDIA":      "^CNXMEDIA",
    "PSU_BANK":   "^CNXPSUBANK",
    "FIN":        "NIFTY_FIN_SERVICE.NS",
    "MIDCAP":     "^CNXMIDCAP",
    "SMALLCAP":   "^CNXSMALLCAP",
}


# =========================================================================== #
#  Stock -> sector mapping (extend as needed)
# =========================================================================== #
STOCK_SECTOR_MAP = {
    # NIFTY 50
    "RELIANCE.NS": "ENERGY", "TCS.NS": "IT", "HDFCBANK.NS": "BANK",
    "INFY.NS": "IT", "ICICIBANK.NS": "BANK", "SBIN.NS": "PSU_BANK",
    "BHARTIARTL.NS": "MEDIA", "ITC.NS": "FMCG", "LT.NS": "FIN",
    "AXISBANK.NS": "BANK", "HINDUNILVR.NS": "FMCG", "MARUTI.NS": "AUTO",
    "KOTAKBANK.NS": "BANK", "BAJFINANCE.NS": "FIN", "ASIANPAINT.NS": "FMCG",
    "HCLTECH.NS": "IT", "WIPRO.NS": "IT", "SUNPHARMA.NS": "PHARMA",
    "TATAMOTORS.NS": "AUTO", "TITAN.NS": "FMCG", "ULTRACEMCO.NS": "REALTY",
    "NESTLEIND.NS": "FMCG", "POWERGRID.NS": "ENERGY", "NTPC.NS": "ENERGY",
    "TATASTEEL.NS": "METAL", "M&M.NS": "AUTO", "ONGC.NS": "ENERGY",
    "TECHM.NS": "IT", "COALINDIA.NS": "ENERGY", "BAJAJFINSV.NS": "FIN",
    "GRASIM.NS": "METAL", "INDUSINDBK.NS": "BANK", "ADANIENT.NS": "ENERGY",
    "JSWSTEEL.NS": "METAL", "HINDALCO.NS": "METAL", "DIVISLAB.NS": "PHARMA",
    "DRREDDY.NS": "PHARMA", "CIPLA.NS": "PHARMA", "BAJAJ-AUTO.NS": "AUTO",
    "BRITANNIA.NS": "FMCG", "EICHERMOT.NS": "AUTO", "HEROMOTOCO.NS": "AUTO",
    "BPCL.NS": "ENERGY", "SHRIRAMFIN.NS": "FIN", "TATAPOWER.NS": "ENERGY",
    "ADANIPORTS.NS": "FIN", "LTIM.NS": "IT", "HDFCLIFE.NS": "FIN",
    "SBILIFE.NS": "FIN", "TRENT.NS": "FMCG",
    # More mid-caps
    "DMART.NS": "FMCG", "ZOMATO.NS": "MEDIA", "PIDILITIND.NS": "FMCG",
    "DABUR.NS": "FMCG", "GODREJCP.NS": "FMCG", "MARICO.NS": "FMCG",
    "COLPAL.NS": "FMCG", "HAVELLS.NS": "FMCG", "BANKBARODA.NS": "PSU_BANK",
    "PNB.NS": "PSU_BANK", "IOC.NS": "ENERGY", "VEDL.NS": "METAL",
    "NMDC.NS": "METAL", "SAIL.NS": "METAL", "JINDALSTEL.NS": "METAL",
    "APLAPOLLO.NS": "METAL", "TORNTPHARM.NS": "PHARMA", "AUROPHARMA.NS": "PHARMA",
    "ALKEM.NS": "PHARMA", "LAURUSLABS.NS": "PHARMA", "BIOCON.NS": "PHARMA",
    "ZYDUSLIFE.NS": "PHARMA", "GLENMARK.NS": "PHARMA", "IPCALAB.NS": "PHARMA",
    "MAXHEALTH.NS": "PHARMA", "ABFRL.NS": "FMCG", "TATACONSUM.NS": "FMCG",
    "BAJAJHLDNG.NS": "FIN", "ICICIPRULI.NS": "FIN", "HDFCAMC.NS": "FIN",
    "ICICIGI.NS": "FIN", "SBICARD.NS": "FIN", "BANDHANBNK.NS": "BANK",
    "FEDERALBNK.NS": "BANK", "IDFCFIRSTB.NS": "BANK", "AUBANK.NS": "BANK",
    "MUTHOOTFIN.NS": "FIN", "CHOLAFIN.NS": "FIN", "PFC.NS": "FIN",
    "RECLTD.NS": "FIN", "LICHSGFIN.NS": "FIN",
    "SIEMENS.NS": "FIN", "ABB.NS": "FIN", "CGPOWER.NS": "FIN",
    "POLYCAB.NS": "FIN", "BEL.NS": "FIN", "HAL.NS": "FIN", "BHEL.NS": "FIN",
}


# =========================================================================== #
#  SectorRotation
# =========================================================================== #
@dataclass
class SectorStat:
    sector: str
    ticker: str
    current: float
    return_1m: float
    return_3m: float
    return_6m: float
    return_1y: float
    momentum_score: float  # weighted avg of the returns
    rank: int = 0


class SectorRotation:
    """Fetches sector index data, ranks sectors by momentum, tags stocks."""

    def __init__(self, lookback_days: int = 252):
        self.lookback_days = lookback_days
        self.sectors: dict[str, SectorStat] = {}
        self.last_refresh: Optional[str] = None

    def refresh(self) -> None:
        """Fetch fresh sector data from Yahoo and compute momentum scores."""
        print(f"Refreshing sector data for {len(SECTOR_INDICES)} indices...")
        end = datetime.now()
        start = end - timedelta(days=self.lookback_days + 60)  # buffer
        stats = {}
        for sector, ticker in SECTOR_INDICES.items():
            try:
                t = yf.Ticker(ticker)
                df = t.history(start=start.strftime("%Y-%m-%d"),
                               end=end.strftime("%Y-%m-%d"),
                               interval="1d", auto_adjust=True)
                if df is None or df.empty or len(df) < 30:
                    print(f"  ! {sector} ({ticker}): insufficient data")
                    continue
                close = df["Close"]
                current = float(close.iloc[-1])
                ret_1m = self._return(close, 21)
                ret_3m = self._return(close, 63)
                ret_6m = self._return(close, 126)
                ret_1y = self._return(close, 252) if len(close) >= 252 else ret_6m
                # Weighted momentum: 50% 1m, 30% 3m, 20% 6m (recent weighted)
                momentum = 0.5 * ret_1m + 0.3 * ret_3m + 0.2 * ret_6m
                stats[sector] = SectorStat(
                    sector=sector, ticker=ticker, current=round(current, 2),
                    return_1m=round(ret_1m * 100, 2),
                    return_3m=round(ret_3m * 100, 2),
                    return_6m=round(ret_6m * 100, 2),
                    return_1y=round(ret_1y * 100, 2),
                    momentum_score=round(momentum * 100, 2),
                )
                print(f"  + {sector:<10} momentum={momentum*100:>+6.2f}%  "
                      f"1m={ret_1m*100:>+5.1f}%  3m={ret_3m*100:>+5.1f}%")
                time.sleep(0.3)
            except Exception as e:
                print(f"  ! {sector} ({ticker}): {e}")

        # Rank by momentum
        ranked = sorted(stats.values(), key=lambda s: s.momentum_score, reverse=True)
        for i, s in enumerate(ranked, 1):
            s.rank = i
        self.sectors = {s.sector: s for s in ranked}
        self.last_refresh = datetime.now().isoformat(timespec="seconds")

        # Save cache
        cache = {
            "last_refresh": self.last_refresh,
            "sectors": {k: v.__dict__ for k, v in self.sectors.items()},
        }
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=2)
        print(f"\nSector data refreshed at {self.last_refresh}")

    def load_cached(self) -> bool:
        """Load cached sector data if available."""
        if not CACHE_PATH.exists():
            return False
        try:
            with open(CACHE_PATH) as f:
                cache = json.load(f)
            self.last_refresh = cache["last_refresh"]
            self.sectors = {
                k: SectorStat(**v) for k, v in cache["sectors"].items()
            }
            return True
        except Exception:
            return False

    def _return(self, close: pd.Series, days: int) -> float:
        if len(close) <= days:
            return 0.0
        return (close.iloc[-1] - close.iloc[-days - 1]) / close.iloc[-days - 1]

    def get_sector_for_stock(self, symbol: str) -> Optional[str]:
        """Look up which sector a stock belongs to."""
        sym = symbol.upper().replace(".NS", ".NS").replace(".BO", ".BO")
        return STOCK_SECTOR_MAP.get(sym)

    def get_context(self, symbol: str) -> dict:
        """Get the sector context for a stock.

        Returns a dict with the stock's sector, its rank, momentum, and a
        'bias' field that can be used to nudge the advisor's confidence:
          - BULLISH: sector in top 1/3
          - NEUTRAL: sector in middle 1/3
          - BEARISH: sector in bottom 1/3
        """
        if not self.sectors:
            self.load_cached()
        if not self.sectors:
            return {"available": False, "reason": "no sector data - run refresh()"}

        sector = self.get_sector_for_stock(symbol)
        if sector is None:
            return {"available": False, "reason": f"no sector mapping for {symbol}"}

        stat = self.sectors.get(sector)
        if stat is None:
            return {"available": False, "reason": f"no data for sector {sector}"}

        n_sectors = len(self.sectors)
        if stat.rank <= n_sectors // 3:
            bias = "BULLISH"
        elif stat.rank <= 2 * n_sectors // 3:
            bias = "NEUTRAL"
        else:
            bias = "BEARISH"

        return {
            "available": True,
            "symbol": symbol,
            "sector": sector,
            "sector_rank": stat.rank,
            "n_sectors": n_sectors,
            "momentum_pct": stat.momentum_score,
            "return_1m_pct": stat.return_1m,
            "return_3m_pct": stat.return_3m,
            "return_6m_pct": stat.return_6m,
            "return_1y_pct": stat.return_1y,
            "bias": bias,
            "explanation": (
                f"{symbol} is in the {sector} sector, ranked #{stat.rank} of "
                f"{n_sectors} by momentum ({stat.momentum_score:+.2f}% weighted). "
                f"Sector bias: {bias}."
            ),
        }

    def get_top_sectors(self, n: int = 3) -> list[dict]:
        """Return the top N sectors by momentum."""
        if not self.sectors:
            self.load_cached()
        ranked = sorted(self.sectors.values(), key=lambda s: s.rank)
        return [s.__dict__ for s in ranked[:n]]

    def get_bottom_sectors(self, n: int = 3) -> list[dict]:
        """Return the bottom N sectors by momentum."""
        if not self.sectors:
            self.load_cached()
        ranked = sorted(self.sectors.values(), key=lambda s: -s.rank)
        return [s.__dict__ for s in ranked[:n]]


# =========================================================================== #
#  CLI
# =========================================================================== #
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Sector rotation overlay")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("refresh", help="Fetch fresh sector data")
    p = sub.add_parser("context", help="Get sector context for a stock")
    p.add_argument("symbol")
    sub.add_parser("top", help="Show top sectors")
    args = ap.parse_args()

    sr = SectorRotation()
    if args.command == "refresh":
        sr.refresh()
        print(f"\nTop 3 sectors:")
        for s in sr.get_top_sectors(3):
            print(f"  #{s['rank']} {s['sector']:<10}  momentum={s['momentum_score']:>+6.2f}%")
        print(f"\nBottom 3 sectors:")
        for s in sr.get_bottom_sectors(3):
            print(f"  #{s['rank']} {s['sector']:<10}  momentum={s['momentum_score']:>+6.2f}%")
    elif args.command == "context":
        if not sr.load_cached():
            print("No cached data. Run: python sector_rotation.py refresh")
        else:
            print(json.dumps(sr.get_context(args.symbol), indent=2))
    elif args.command == "top":
        if not sr.load_cached():
            print("No cached data. Run: python sector_rotation.py refresh")
        else:
            print(f"All sectors by momentum (last refresh: {sr.last_refresh}):")
            for s in sorted(sr.sectors.values(), key=lambda x: x.rank):
                print(f"  #{s.rank:<2} {s.sector:<10}  momentum={s.momentum_score:>+6.2f}%  "
                      f"1m={s.return_1m:>+5.1f}%  3m={s.return_3m:>+5.1f}%")
