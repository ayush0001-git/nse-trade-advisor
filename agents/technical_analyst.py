"""
agents/technical_analyst.py - Agent 2: Technical Analyst

Reads price, volume, VWAP, options. Combines:
  - Advisor TA engine (indicators + regime + signals) — weighted into 30 pts
  - Candlestick patterns (patterns.py) — weighted into 30 pts
  - Options flow (options_flow.py) — 0-10 pts
  - Sector rotation (sector_rotation.py) — weighted into 30 pts

Total contribution: 0-30 points in the 100-point system (Technical Score).
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TechnicalAnalyst:
    """Agent that reads price action, indicators, patterns, and options flow."""

    name = "Technical Analyst"
    role = "Reads price, volume, VWAP, indicators, patterns, options"

    def analyze(self, symbol: str, idea=None) -> dict:
        """Run the technical analysis.

        Args:
            symbol: Stock symbol
            idea: Optional pre-computed advisor TradeIdea (to avoid re-fetching)
        """
        results = {
            "agent": self.name,
            "symbol": symbol,
            "components": {},
            "total_score": 0,
            "max_score": 30,
            "error": None,
        }

        # 1. Advisor TA engine — the core technical read
        advisor_score = 0
        try:
            if idea is None:
                from advisor.core import Settings, Style, load_settings, get_source
                from advisor.engine import Analyzer
                cfg = PROJECT_ROOT / "config.yaml"
                s = load_settings(str(cfg)) if cfg.exists() else Settings()
                source = get_source(s.data_source, exchange=s.exchange, directory=s.csv_dir)
                agent = Analyzer(s, source=source)
                idea = agent.analyze(symbol, style=Style.SWING, use_llm=False, use_news=False)

            # Map advisor verdict+confidence to 0-18 points (of the 30)
            if idea.direction.value == "short":
                advisor_score = 0  # short setup — excluded from buy score
            elif idea.verdict.value == "TAKE":
                advisor_score = 12 + int(idea.confidence * 0.06)  # 12-18
            elif idea.verdict.value == "WATCH":
                advisor_score = 6 + int(idea.confidence * 0.06)   # 6-12
            elif idea.verdict.value == "NO_SETUP":
                advisor_score = 3
            elif idea.verdict.value == "AVOID":
                advisor_score = 0

            results["components"]["advisor"] = {
                "verdict": idea.verdict.value,
                "direction": idea.direction.value,
                "confidence": idea.confidence,
                "regime": idea.regime.value,
                "score": advisor_score,
                "max": 18,
            }
            if idea.direction.value == "short":
                results["components"]["advisor"]["note"] = (
                    "short setup — excluded from buy score"
                )
        except Exception as e:
            results["components"]["advisor"] = {"error": str(e), "score": 9}
            advisor_score = 9

        # 2. Candlestick patterns (0-6)
        try:
            from patterns import detect_with_context
            from strategies import fetch_stock_data
            sym = symbol if "." in symbol else f"{symbol}.NS"
            df = fetch_stock_data(sym, period="1y")
            pats = detect_with_context(df)
            # 2 points per bullish pattern, -2 per bearish, clamped 0-6
            pat_score = max(0, min(6, pats["n_bullish"] * 2 - pats["n_bearish"] * 2 + 3))
            results["components"]["patterns"] = {
                "n_bullish": pats["n_bullish"],
                "n_bearish": pats["n_bearish"],
                "bias": pats["bias"],
                "score": pat_score,
                "max": 6,
            }
        except Exception as e:
            results["components"]["patterns"] = {"error": str(e), "score": 3}
            pat_score = 3

        # 3. Sector rotation (0-6)
        try:
            from sector_rotation import SectorRotation
            sr = SectorRotation()
            sr.load_cached()
            sym = symbol if "." in symbol else f"{symbol}.NS"
            ctx = sr.get_context(sym)
            if ctx.get("available"):
                if ctx["bias"] == "BULLISH":
                    sec_score = 5 + min(1, int(ctx["momentum_pct"] / 10))
                elif ctx["bias"] == "BEARISH":
                    sec_score = max(0, 2 - int(abs(ctx["momentum_pct"]) / 10))
                else:
                    sec_score = 3
                results["components"]["sector"] = {
                    "sector": ctx["sector"],
                    "rank": ctx["sector_rank"],
                    "bias": ctx["bias"],
                    "momentum": ctx["momentum_pct"],
                    "score": sec_score,
                    "max": 6,
                }
            else:
                sec_score = 3
                results["components"]["sector"] = {"available": False, "score": 3}
        except Exception as e:
            results["components"]["sector"] = {"error": str(e), "score": 3}
            sec_score = 3

        results["total_score"] = advisor_score + pat_score + sec_score
        results["explanation"] = (
            f"Advisor: {advisor_score}/18 | Patterns: {pat_score}/6 | "
            f"Sector: {sec_score}/6 | Total: {results['total_score']}/30"
        )
        return results
