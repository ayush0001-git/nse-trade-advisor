"""
consensus.py - Aggregates all opinions into a single 0-100 conviction score.

The advisor now has 5 independent opinion sources:
  1. Advisor verdict (TA + regime + risk)
  2. RL agent (PPO trained on NSE)
  3. Sector rotation (top-down from Zerodha)
  4. Strategy Lab (6 backtested strategies)
  5. Candlestick patterns (10 patterns)

This module weights and combines them into a single CONVICTION score:
  - 90-100: All systems go. Multiple confirmations. Highest-conviction trade.
  - 70-89:  Strong setup, minor disagreement.
  - 50-69:  Mixed signals. Trade smaller size or wait.
  - 30-49:  Weak setup. Stand aside.
  - 0-29:   Conflicting signals. AVOID.

Weights (configurable):
  Advisor:    35%  (the core engine, most risk-managed)
  RL agent:   15%  (the ML second opinion)
  Sector:     15%  (top-down context)
  Strategies: 20%  (6 backtested rules)
  Patterns:   15%  (price action micro-structure)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def _advisor_score(verdict: str, direction: str, confidence: float) -> float:
    """Convert advisor verdict/direction/confidence into a -100..+100 score.

    Positive = bullish, negative = bearish, 0 = neutral.
    """
    if verdict == "NO_SETUP" or direction == "none":
        return 0
    sign = 1 if direction == "long" else -1
    if verdict == "TAKE":
        return sign * (60 + 0.4 * confidence)  # 60..100
    if verdict == "WATCH":
        return sign * (30 + 0.3 * confidence)  # 30..60
    if verdict == "AVOID":
        # AVOID with a direction is a strong anti-signal in that direction
        return sign * -50
    return 0


def _rl_score(action: str, position_size: float) -> float:
    """Convert RL action + size into -100..+100."""
    if action == "BUY":
        return 50 + 50 * position_size  # 50..100
    if action == "SELL":
        return -(50 + 50 * position_size)  # -50..-100
    return 0  # HOLD


def _sector_score(bias: str, momentum_pct: float) -> float:
    """Convert sector bias into -100..+100."""
    if bias == "BULLISH":
        return min(100, max(40, momentum_pct * 8))  # scale momentum to 40..100
    if bias == "BEARISH":
        return max(-100, min(-40, momentum_pct * 8))
    return 0  # NEUTRAL


def _strategy_score(signals: dict) -> float:
    """Average across all 6 strategies. Each BUY=+1, SELL=-1, HOLD=0."""
    if not signals:
        return 0
    total = 0
    n = 0
    for s in signals.values():
        sig = s.get("signal", "HOLD") if isinstance(s, dict) else s
        if sig == "BUY":
            total += 1
        elif sig == "SELL":
            total -= 1
        n += 1
    if n == 0:
        return 0
    # 6 strategies agreeing = ±100, 3 agreeing = ±50
    return (total / n) * 100


def _pattern_score(patterns: dict) -> float:
    """Net bullish - bearish patterns, scaled to -100..+100."""
    if not patterns:
        return 0
    n_bull = patterns.get("n_bullish", 0)
    n_bear = patterns.get("n_bearish", 0)
    # Each pattern is worth ~20 points (max 5 of each side)
    return max(-100, min(100, (n_bull - n_bear) * 20))


def compute_consensus(
    advisor: Optional[dict] = None,
    rl: Optional[dict] = None,
    sector: Optional[dict] = None,
    strategies: Optional[dict] = None,
    patterns: Optional[dict] = None,
    weights: Optional[dict] = None,
) -> dict:
    """Compute the final consensus conviction score.

    Each input is a dict from the respective module:
      advisor:    {"verdict": "TAKE", "direction": "long", "confidence": 75.0}
      rl:         {"action": "BUY", "position_size": 0.6}
      sector:     {"bias": "BULLISH", "momentum_pct": 8.0}
      strategies: {"turn_of_month": {"signal": "BUY"}, ...}
      patterns:   {"n_bullish": 2, "n_bearish": 0, "bias": "bullish"}
    """
    w = weights or {
        "advisor": 0.35,
        "rl": 0.15,
        "sector": 0.15,
        "strategies": 0.20,
        "patterns": 0.15,
    }

    scores = {}
    if advisor:
        scores["advisor"] = _advisor_score(
            advisor.get("verdict", "NO_SETUP"),
            advisor.get("direction", "none"),
            advisor.get("confidence", 0),
        )
    if rl:
        scores["rl"] = _rl_score(rl.get("action", "HOLD"), rl.get("position_size", 0))
    if sector and sector.get("available"):
        scores["sector"] = _sector_score(
            sector.get("bias", "NEUTRAL"),
            sector.get("momentum_pct", 0),
        )
    if strategies and "signals" in strategies:
        scores["strategies"] = _strategy_score(strategies["signals"])
    if patterns:
        scores["patterns"] = _pattern_score(patterns)

    # Weighted average (only over components that are present)
    total_weight = sum(w.get(k, 0) for k in scores)
    if total_weight == 0:
        return {
            "available": False,
            "conviction": 0,
            "bias": "NEUTRAL",
            "components": {},
            "agreement": 0,
        }

    weighted_sum = sum(scores[k] * w.get(k, 0) for k in scores)
    conviction = weighted_sum / total_weight  # -100..+100

    # Direction (sign) + magnitude
    if conviction > 50:
        bias = "STRONG BULLISH"
    elif conviction > 20:
        bias = "BULLISH"
    elif conviction > -20:
        bias = "NEUTRAL"
    elif conviction > -50:
        bias = "BEARISH"
    else:
        bias = "STRONG BEARISH"

    # Agreement: are all present components on the same side?
    signs = [1 if s > 20 else -1 if s < -20 else 0 for s in scores.values()]
    n_strong = sum(1 for s in signs if s != 0)
    if n_strong == 0:
        agreement = 0
    else:
        # agreement = fraction of strong signals that agree with the dominant sign
        dominant = 1 if sum(signs) > 0 else -1
        n_agree = sum(1 for s in signs if s == dominant)
        agreement = round(n_agree / n_strong * 100)

    # Final conviction as absolute 0-100 (magnitude only)
    abs_conviction = round(abs(conviction))

    return {
        "available": True,
        "conviction": abs_conviction,  # 0-100
        "signed_score": round(conviction, 1),  # -100..+100
        "bias": bias,
        "agreement_pct": agreement,
        "components": {k: round(v, 1) for k, v in scores.items()},
        "weights_used": {k: w.get(k, 0) for k in scores},
        "interpretation": _interpret(abs_conviction, bias, agreement),
    }


def _interpret(conviction: int, bias: str, agreement: int) -> str:
    """Plain-English interpretation of the consensus."""
    if conviction >= 80 and agreement >= 80:
        return ("🟢 HIGH-CONVICTION TRADE. Multiple systems agree strongly. "
                "This is the kind of setup worth risking full size on.")
    if conviction >= 65 and agreement >= 60:
        return ("🟢 Strong setup with broad agreement. Trade normal size.")
    if conviction >= 50:
        return ("🟡 Decent setup but with some disagreement. Trade half size.")
    if conviction >= 30:
        return ("🟡 Mixed signals. Wait for more confirmation or trade very small.")
    if conviction >= 10:
        return ("🔴 Weak setup. Stand aside.")
    return ("🔴 Conflicting signals across systems. AVOID.")


def get_full_consensus(symbol: str) -> dict:
    """Convenience: gather all 5 opinions for a symbol and compute consensus.

    This is what the web app calls. It runs each opinion module in turn
    (with graceful fallback if a module isn't available).
    """
    import json
    sym = symbol if "." in symbol else f"{symbol}.NS"

    # 1. Advisor (re-run live analysis)
    advisor_data = None
    try:
        from advisor.core import Settings, load_settings
        from advisor.engine import Analyzer
        from advisor.core import get_source
        cfg_path = PROJECT_ROOT / "config.yaml"
        s = load_settings(str(cfg_path)) if cfg_path.exists() else Settings()
        source = get_source(s.data_source, exchange=s.exchange, directory=s.csv_dir)
        agent = Analyzer(s, source=source)
        idea = agent.analyze(symbol, style=__import__("advisor.core", fromlist=["Style"]).Style.SWING,
                             use_llm=False, use_news=False)
        advisor_data = {
            "verdict": idea.verdict.value,
            "direction": idea.direction.value,
            "confidence": idea.confidence,
            "current_price": idea.indicators.close,
        }
    except Exception as e:
        advisor_data = {"error": str(e)}

    # 2. RL agent
    rl_data = None
    try:
        from rl_agent import predict as rl_predict, MODEL_PATH
        if MODEL_PATH.exists():
            rl_data = rl_predict(symbol)
    except Exception as e:
        rl_data = {"error": str(e), "available": False}

    # 3. Sector context
    sector_data = None
    try:
        from sector_rotation import SectorRotation
        sr = SectorRotation()
        sr.load_cached()
        sector_data = sr.get_context(sym)
    except Exception as e:
        sector_data = {"available": False, "error": str(e)}

    # 4. Strategy Lab signals
    strategies_data = None
    try:
        from strategies import get_all_signals
        strategies_data = get_all_signals(symbol)
    except Exception as e:
        strategies_data = {"error": str(e)}

    # 5. Candlestick patterns
    patterns_data = None
    try:
        from patterns import detect_with_context
        from strategies import fetch_stock_data
        df = fetch_stock_data(sym, period="1y")
        patterns_data = detect_with_context(df)
    except Exception as e:
        patterns_data = {"error": str(e)}

    # Compute consensus
    consensus = compute_consensus(
        advisor=advisor_data if "error" not in advisor_data else None,
        rl=rl_data if rl_data and "error" not in rl_data else None,
        sector=sector_data if sector_data and sector_data.get("available") else None,
        strategies=strategies_data if strategies_data and "error" not in strategies_data else None,
        patterns=patterns_data if patterns_data and "error" not in patterns_data else None,
    )

    return {
        "symbol": sym,
        "current_price": advisor_data.get("current_price") if advisor_data else None,
        "consensus": consensus,
        "components": {
            "advisor": advisor_data,
            "rl": rl_data,
            "sector": sector_data,
            "strategies": strategies_data,
            "patterns": patterns_data,
        },
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Consensus scoring across all opinion engines")
    ap.add_argument("symbol", help="Stock symbol, e.g. RELIANCE or RELIANCE.NS")
    args = ap.parse_args()
    import json
    result = get_full_consensus(args.symbol)
    # Print just the consensus portion for readability
    print(json.dumps(result["consensus"], indent=2))
    print(f"\nComponents present: {list(result['components'].keys())}")
    for k, v in result["components"].items():
        if v and "error" in v:
            print(f"  {k}: ERROR - {v['error'][:80]}")
        elif v:
            print(f"  {k}: OK")
        else:
            print(f"  {k}: not available")
