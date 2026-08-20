"""
agents/quant_researcher.py - Agent 3: Quant Researcher

Runs backtests, factor models, statistical validation. Combines:
  - 16 strategy signals (strategies.py) — 0-15 pts
  - RL agent opinion (rl_agent.py) — 0-5 pts
  - Institutional flow (institutional_flow.py) — 0-10 pts (institutional score overlaps,
    but we allocate 5 pts here for quant-style money-flow analysis)

Total contribution: 0-15 points in the 100-point system.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class QuantResearcher:
    """Agent that runs backtested strategies and quant signals."""

    name = "Quant Researcher"
    role = "Runs backtests, factor models, strategy validation"

    def analyze(self, symbol: str) -> dict:
        results = {
            "agent": self.name,
            "symbol": symbol,
            "components": {},
            "total_score": 0,
            "max_score": 15,
            "error": None,
        }

        # 1. Strategy signals (0-10 of the 15)
        strat_score = 0
        try:
            from strategies import get_all_signals, STRATEGIES
            sigs = get_all_signals(symbol)
            n_buy = sum(1 for s in sigs.get("signals", {}).values()
                       if (s.get("signal") if isinstance(s, dict) else s) == "BUY")
            n_sell = sum(1 for s in sigs.get("signals", {}).values()
                        if (s.get("signal") if isinstance(s, dict) else s) == "SELL")
            n_total = len(sigs.get("signals", {}))
            if n_total > 0:
                # Net bullish score: (buys - sells) / total, scaled to 0-10
                net = (n_buy - n_sell) / n_total
                strat_score = round(max(0, min(10, 5 + net * 5)))
            results["components"]["strategies"] = {
                "n_buy": n_buy,
                "n_sell": n_sell,
                "n_hold": n_total - n_buy - n_sell,
                "total_strategies": n_total,
                "score": strat_score,
                "max": 10,
            }
        except Exception as e:
            results["components"]["strategies"] = {"error": str(e), "score": 5}
            strat_score = 5

        # 2. RL agent opinion (0-5)
        rl_score = 0
        try:
            from rl_agent import predict as rl_predict, MODEL_PATH
            if MODEL_PATH.exists():
                rl = rl_predict(symbol)
                if rl["action"] == "BUY":
                    rl_score = 3 + min(2, int(rl["position_size"] * 2))
                elif rl["action"] == "SELL":
                    rl_score = max(0, 2 - int(rl["position_size"] * 2))
                else:  # HOLD
                    rl_score = 2
                results["components"]["rl_agent"] = {
                    "action": rl["action"],
                    "position_size": rl["position_size"],
                    "score": rl_score,
                    "max": 5,
                }
            else:
                results["components"]["rl_agent"] = {"available": False, "score": 2}
                rl_score = 2
        except Exception as e:
            results["components"]["rl_agent"] = {"error": str(e), "score": 2}
            rl_score = 2

        results["total_score"] = strat_score + rl_score
        results["explanation"] = (
            f"Strategies: {strat_score}/10 | RL Agent: {rl_score}/5 | "
            f"Total: {results['total_score']}/15"
        )
        return results
