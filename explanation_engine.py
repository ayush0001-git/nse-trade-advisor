"""
explanation_engine.py - Generates a plain-English "why buy" explanation for any stock.

Combines all the agent outputs into a narrative that explains:
  1. What the stock is and what it does
  2. Why the system recommends it (or doesn't)
  3. What could go wrong (risks)
  4. What the historical pattern suggests
  5. What the knowledge base says about this type of setup

Usage:
    from explanation_engine import explain_stock
    explanation = explain_stock("RELIANCE.NS")
    print(explanation["narrative"])
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def explain_stock(symbol: str) -> dict:
    """Generate a full explanation for why to buy (or not buy) a stock.

    Returns a dict with:
      - narrative: the full plain-English explanation
      - score: the 100-point score
      - rating: STRONG BUY / WATCHLIST / SPECULATIVE / IGNORE
      - key_reasons: list of the main reasons for/against
      - risks: list of the main risks
      - historical_context: similar past patterns and outcomes
      - knowledge_rules: relevant rules from the knowledge base
    """
    # Run the full 5-agent pipeline
    from agents.portfolio_manager import PortfolioManager
    pm = PortfolioManager()
    result = pm.analyze(symbol)

    score = result["final_score"]
    rating = result["rating"]
    scores = result["scores"]
    agents = result["agents"]

    # Build the narrative
    narrative_parts = []
    key_reasons = []
    risks = []

    sym = symbol.replace(".NS", "").replace(".BO", "")

    # --- INTRODUCTION --- #
    narrative_parts.append(f"# {sym} — Stock Analysis")

    # Get fundamentals for company description
    fund = agents.get("fundamentals", {})
    if fund and fund.get("available"):
        sector = fund.get("sector", "Unknown")
        industry = fund.get("industry", "")
        pe = fund.get("fundamentals", {}).get("pe_ratio")
        mcap = fund.get("fundamentals", {}).get("market_cap")

        company_desc = f"**Sector:** {sector}"
        if industry:
            company_desc += f" | **Industry:** {industry}"
        if mcap:
            if mcap > 2e12:
                cap_class = "Large-cap"
            elif mcap > 5e10:
                cap_class = "Mid-cap"
            else:
                cap_class = "Small-cap"
            company_desc += f" | **Classification:** {cap_class}"
        narrative_parts.append(f"\n{company_desc}\n")

    # --- VERDICT --- #
    narrative_parts.append(f"## Verdict: {rating} ({score}/100)")
    narrative_parts.append(f"\n{result['recommendation']}\n")

    # --- SCORE BREAKDOWN --- #
    narrative_parts.append("## Score Breakdown")
    score_labels = {
        "technical": "📊 Technical Analysis",
        "news": "📰 News Intelligence",
        "sentiment": "💬 Social Sentiment",
        "institutional": "🏛️ Institutional Flow",
        "options": "🎯 Options Flow",
        "fundamentals": "📈 Fundamentals",
    }
    for key, val in scores.items():
        label = score_labels.get(key, key)
        max_val = {"technical": 30, "news": 20, "sentiment": 15,
                   "institutional": 15, "options": 10, "fundamentals": 10}.get(key, 10)
        pct = val / max_val * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        narrative_parts.append(f"- {label}: {val}/{max_val} [{bar}] {pct:.0f}%")
    narrative_parts.append("")

    # --- WHY BUY (or not) --- #
    narrative_parts.append("## Key Reasons")

    # Technical reasons
    tech = agents.get("technical", {})
    if tech:
        advisor = tech.get("components", {}).get("advisor", {})
        if advisor.get("verdict") == "TAKE":
            key_reasons.append(f"✅ **Technical setup is strong** — verdict: {advisor.get('verdict')}, "
                              f"direction: {advisor.get('direction')}, confidence: {advisor.get('confidence')}/100")
        elif advisor.get("verdict") == "AVOID":
            risks.append(f"❌ **Technical setup is weak** — verdict: {advisor.get('verdict')}")

        patterns = tech.get("components", {}).get("patterns", {})
        if patterns.get("n_bullish", 0) > 0:
            key_reasons.append(f"✅ **{patterns['n_bullish']} bullish candlestick pattern(s)** detected on the latest bar")
        if patterns.get("n_bearish", 0) > 0:
            risks.append(f"⚠️ **{patterns['n_bearish']} bearish candlestick pattern(s)** detected")

        sector = tech.get("components", {}).get("sector", {})
        if sector.get("available"):
            if sector.get("bias") == "BULLISH":
                key_reasons.append(f"✅ **Sector tailwind** — {sector.get('sector')} sector ranked #{sector.get('rank')} "
                                  f"with {sector.get('momentum')}% momentum")
            elif sector.get("bias") == "BEARISH":
                risks.append(f"⚠️ **Sector headwind** — {sector.get('sector')} sector ranked #{sector.get('rank')} "
                           f"with {sector.get('momentum')}% momentum")

    # News reasons
    news = agents.get("news", {})
    if news:
        ni = news.get("components", {}).get("news_intel", {})
        if ni.get("headline_count", 0) > 0:
            avg_sent = ni.get("avg_headline_score", 0)
            if avg_sent > 1:
                key_reasons.append(f"✅ **Positive news sentiment** — {ni.get('headline_count')} headlines, "
                                  f"average score {avg_sent}/5")
            elif avg_sent < -1:
                risks.append(f"❌ **Negative news sentiment** — {ni.get('headline_count')} headlines, "
                           f"average score {avg_sent}/5")

        social = news.get("components", {}).get("social_sentiment", {})
        if social.get("mentions_today", 0) > 0:
            momentum = social.get("mention_momentum", "none")
            if momentum == "rising":
                key_reasons.append(f"✅ **Social buzz rising** — {social.get('mentions_today')} mentions today "
                                  f"(vs {social.get('mentions_yesterday')} yesterday)")
            elif momentum == "falling":
                risks.append(f"⚠️ **Social buzz falling** — mentions declining")

    # Institutional reasons
    inst = agents.get("institutional", {})
    if inst and inst.get("score", 0) >= 10:
        delivery = inst.get("delivery_pct", 0)
        if delivery > 55:
            key_reasons.append(f"✅ **High delivery %** ({delivery:.0f}%) — investors accumulating, not intraday flipping")
        fii_net = inst.get("fii_net_cr", 0)
        if fii_net > 500:
            key_reasons.append(f"✅ **FII buying** — net ₹{fii_net:.0f}cr today")
        elif fii_net < -500:
            risks.append(f"❌ **FII selling** — net ₹{fii_net:.0f}cr today")
    elif inst and inst.get("score", 0) <= 5:
        risks.append("⚠️ **Weak institutional flow** — low delivery or FII selling")

    # Options reasons
    opts = agents.get("options", {})
    if opts and opts.get("available"):
        buildup = opts.get("oi_buildup", {})
        pattern = buildup.get("pattern", "")
        if "Long" in pattern:
            key_reasons.append(f"✅ **Options: {pattern}** — smart money positioning bullish")
        elif "Short" in pattern:
            risks.append(f"❌ **Options: {pattern}** — smart money positioning bearish")

    # Fundamentals reasons
    if fund and fund.get("available"):
        scores_f = fund.get("scores", {})
        if scores_f.get("growth", 0) >= 2:
            key_reasons.append(f"✅ **Strong growth** — revenue and earnings growing above 10%")
        if scores_f.get("profitability", 0) >= 2:
            key_reasons.append(f"✅ **High profitability** — strong margins and ROE")
        if scores_f.get("valuation", 0) <= 1:
            risks.append(f"⚠️ **Expensive valuation** — P/E or P/B above sector average")
        if scores_f.get("financial_health", 0) <= 0:
            risks.append(f"❌ **Weak financial health** — high debt or low current ratio")

    # Earnings reasons
    earn = agents.get("earnings", {})
    if earn and earn.get("tone"):
        tone = earn["tone"]
        if tone.get("guidance_raised"):
            key_reasons.append("✅ **Guidance raised** — management confident in future")
        if tone.get("guidance_lowered"):
            risks.append("❌ **Guidance lowered** — management cautious about future")
        if tone.get("hedging_detected"):
            risks.append(f"⚠️ **Hedging language detected** — {', '.join(tone['hedging_detected'][:2])}")

    # Output reasons
    for reason in key_reasons:
        narrative_parts.append(reason)
    if not key_reasons:
        narrative_parts.append("No strong bullish reasons found.")
    narrative_parts.append("")

    # --- RISKS --- #
    if risks:
        narrative_parts.append("## ⚠️ Risks & Red Flags")
        for risk in risks:
            narrative_parts.append(risk)
        narrative_parts.append("")

    # Risk manager vetoes
    risk_agent = agents.get("risk", {})
    if risk_agent.get("vetoes"):
        narrative_parts.append("### Risk Manager Warnings:")
        for v in risk_agent["vetoes"]:
            narrative_parts.append(f"- ⚠️ {v}")
        narrative_parts.append("")

    # --- HISTORICAL CONTEXT --- #
    similar_patterns = result.get("similar_patterns", [])
    if similar_patterns:
        narrative_parts.append("## 📊 Historical Pattern Match")
        narrative_parts.append("Similar setups in the past had these outcomes:")
        for p in similar_patterns[:3]:
            narrative_parts.append(
                f"- **{p.get('type', '?')}** on {p.get('symbol', '?')} ({p.get('date', '?')}): "
                f"1d: {p.get('outcome_1d', '?')}%, 5d: {p.get('outcome_5d', '?')}%, "
                f"20d: {p.get('outcome_20d', '?')}%"
            )
        narrative_parts.append("")

    # --- KNOWLEDGE BASE --- #
    rules = result.get("knowledge_rules", [])
    if rules:
        narrative_parts.append("## 📚 Relevant Knowledge")
        for rule in rules[:3]:
            source = rule.get("source", "Unknown")
            text = rule.get("rule", "")
            narrative_parts.append(f"- **{source}:** {text[:200]}")
        narrative_parts.append("")

    # --- ACTION PLAN --- #
    narrative_parts.append("## 🎯 Action Plan")
    if score >= 80:
        narrative_parts.append("✅ **BUY** — Full position size (1% risk). This is a high-conviction trade.")
    elif score >= 70:
        narrative_parts.append("🟡 **WATCHLIST** — Normal position size (1% risk). Good setup with minor concerns.")
    elif score >= 60:
        narrative_parts.append("🟠 **SPECULATIVE** — Half position size (0.5% risk). Mixed signals, trade small.")
    else:
        narrative_parts.append("🔴 **AVOID** — Do not trade. Insufficient conviction or conflicting signals.")

    # Add entry/stop/target if available
    advisor_comp = tech.get("components", {}).get("advisor", {}) if tech else {}
    plan = advisor_comp.get("plan") or agents.get("risk", {}).get("components", {}).get("plan")
    if plan:
        narrative_parts.append(f"\n- **Entry:** ₹{plan.get('entry', '?')}")
        narrative_parts.append(f"- **Stop-loss:** ₹{plan.get('stop_loss', '?')} ({plan.get('risk_reward', '?')}:1 R:R)")
        narrative_parts.append(f"- **Target:** ₹{plan.get('target', '?')}")
        narrative_parts.append(f"- **Position size:** {plan.get('quantity', '?')} shares "
                              f"(₹{plan.get('rupees_at_risk', '?')} at risk)")

    narrative = "\n".join(narrative_parts)

    return {
        "symbol": symbol,
        "score": score,
        "rating": rating,
        "narrative": narrative,
        "key_reasons": key_reasons,
        "risks": risks,
        "historical_patterns": similar_patterns,
        "knowledge_rules": rules,
        "recommendation": result["recommendation"],
        "full_analysis": result,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate stock explanation")
    ap.add_argument("symbol", help="Stock symbol")
    args = ap.parse_args()
    result = explain_stock(args.symbol)
    print(result["narrative"])
