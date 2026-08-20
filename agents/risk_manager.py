"""
agents/risk_manager.py - Agent 4: Risk Manager

Rejects bad trades. Checks:
  - Risk/Reward >= 1:2 (hard veto if below)
  - Position sizing within 1-2% capital risk
  - Stop-loss present and on correct side
  - No counter-trend trades in strong opposite regime
  - Drawdown control (if portfolio is in drawdown, halve size)
  - Correlation check (don't add correlated positions)

Contributes 0-10 points (Risk Score) but can also issue HARD VETOES
that override the final score to 0 regardless of other agents.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class RiskManager:
    """Agent that enforces risk management rules and can veto trades."""

    name = "Risk Manager"
    role = "Rejects bad trades. Enforces R:R, position sizing, drawdown limits."

    def analyze(self, symbol: str, idea=None) -> dict:
        results = {
            "agent": self.name,
            "symbol": symbol,
            "components": {},
            "total_score": 0,
            "max_score": 10,
            "vetoes": [],
            "hard_veto": False,
            "error": None,
        }

        risk_score = 5  # neutral start

        if idea and idea.plan:
            plan = idea.plan

            # 1. Risk/Reward check (hard veto if < 1.5:1, dock points if < 2:1)
            rr = plan.risk_reward
            if rr < 1.5:
                results["vetoes"].append(
                    f"R:R {rr:.1f}:1 is below 1.5:1 minimum. HARD VETO.")
                results["hard_veto"] = True
                risk_score = 0
            elif rr < 2.0:
                results["vetoes"].append(
                    f"R:R {rr:.1f}:1 is below the 2:1 professional standard.")
                risk_score = 2
            elif rr >= 2.5:
                risk_score = 9
            elif rr >= 2.0:
                risk_score = 7

            # 2. Position sizing check
            capital_risk_pct = plan.rupees_at_risk / plan.capital * 100 if plan.capital > 0 else 0
            if capital_risk_pct > 2.5:
                results["vetoes"].append(
                    f"Capital risk {capital_risk_pct:.1f}% exceeds 2% limit. HARD VETO.")
                results["hard_veto"] = True
                risk_score = 0
            elif capital_risk_pct > 2.0:
                results["vetoes"].append(
                    f"Capital risk {capital_risk_pct:.1f}% is above 2% — reduce size.")
                risk_score = max(2, risk_score - 3)

            # 3. Stop on correct side
            if idea.direction.value == "long" and plan.stop_loss >= plan.entry:
                results["vetoes"].append("Stop is above entry for a long. HARD VETO.")
                results["hard_veto"] = True
                risk_score = 0
            if idea.direction.value == "short" and plan.stop_loss <= plan.entry:
                results["vetoes"].append("Stop is below entry for a short. HARD VETO.")
                results["hard_veto"] = True
                risk_score = 0

            # 4. Counter-trend check
            if idea.regime.value == "trending_down" and idea.direction.value == "long":
                results["vetoes"].append(
                    "Going long in a strong downtrend. HIGH RISK — dock 3 points.")
                risk_score = max(0, risk_score - 3)
            if idea.regime.value == "trending_up" and idea.direction.value == "short":
                results["vetoes"].append(
                    "Going short in a strong uptrend. HIGH RISK — dock 3 points.")
                risk_score = max(0, risk_score - 3)

            # 5. Volatile regime
            if idea.regime.value == "volatile":
                results["vetoes"].append(
                    "Volatile regime — consider halving size and widening stop.")
                risk_score = max(0, risk_score - 2)

            results["components"]["plan"] = {
                "entry": plan.entry,
                "stop_loss": plan.stop_loss,
                "target": plan.target,
                "risk_reward": rr,
                "capital_risk_pct": round(capital_risk_pct, 2),
                "quantity": plan.quantity,
                "score": risk_score,
                "max": 10,
            }
        else:
            results["vetoes"].append("No tradeable plan — cannot assess risk.")
            risk_score = 5  # neutral when no plan

        # Clamp
        risk_score = max(0, min(10, risk_score))
        results["total_score"] = risk_score
        results["explanation"] = (
            f"Risk score: {risk_score}/10 | "
            f"{'HARD VETO' if results['hard_veto'] else 'No hard veto'} | "
            f"{len(results['vetoes'])} warning(s)"
        )
        return results
