"""
agents/portfolio_manager.py - Agent 5: Portfolio Manager

The final decision layer. Combines all 4 other agents + fundamentals +
institutional flow + RAG knowledge base into the final 100-point score.

100-Point Score Breakdown:
  Technical Score (30)    — from TechnicalAnalyst agent
  News Score (20)         — from NewsHunter agent (news_intel portion)
  Sentiment Score (15)    — from NewsHunter agent (social portion)
  Institutional Score (15) — institutional_flow.py (FII/DII, delivery, block deals)
  Options Score (10)      — options_flow.py (PCR, OI buildup, max pain)
  Fundamentals (10)       — fundamentals.py (P/E, growth, profitability)

Final:
  80+  = Strong Buy Candidate
  70-80 = Watchlist
  60-70 = Speculative
  Below 60 = Ignore

If the Risk Manager issues a HARD VETO, the final score is capped at 30
regardless of other agents' inputs.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class PortfolioManager:
    """The final agent that combines all opinions into a 100-point score."""

    name = "Portfolio Manager"
    role = "Combines all agents + RAG rules into final 100-point score"

    def analyze(self, symbol: str) -> dict:
        """Run the full 5-agent pipeline and produce the final score."""
        from agents.technical_analyst import TechnicalAnalyst
        from agents.news_hunter import NewsHunter
        from agents.quant_researcher import QuantResearcher
        from agents.risk_manager import RiskManager
        from knowledge_base import get_rules_for_context

        results = {
            "symbol": symbol,
            "timestamp": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
            "agents": {},
            "scores": {},
            "final_score": 0,
            "max_score": 100,
            "rating": "",
            "recommendation": "",
            "knowledge_rules": [],
            "error": None,
        }

        # Get the advisor idea first (shared between Technical + Risk agents)
        idea = None
        try:
            from advisor.core import Settings, Style, load_settings, get_source
            from advisor.engine import Analyzer
            cfg = PROJECT_ROOT / "config.yaml"
            s = load_settings(str(cfg)) if cfg.exists() else Settings()
            source = get_source(s.data_source, exchange=s.exchange, directory=s.csv_dir)
            agent = Analyzer(s, source=source)
            idea = agent.analyze(symbol, style=Style.SWING, use_llm=False, use_news=False)
        except Exception as e:
            results["error"] = f"Advisor failed: {e}"

        # Run each agent
        results["agents"]["technical"] = TechnicalAnalyst().analyze(symbol, idea=idea)
        results["agents"]["news"] = NewsHunter().analyze(symbol)
        results["agents"]["quant"] = QuantResearcher().analyze(symbol)
        results["agents"]["risk"] = RiskManager().analyze(symbol, idea=idea)

        # Map agent scores to the 100-point system
        technical = results["agents"]["technical"]["total_score"]  # 0-30
        news_intel_score = results["agents"]["news"]["components"].get("news_intel", {}).get("score", 10)  # 0-20
        social_score = results["agents"]["news"]["components"].get("social_sentiment", {}).get("score", 7)  # 0-15
        quant = results["agents"]["quant"]["total_score"]  # 0-15 (strategies + RL)

        # Institutional flow (0-15)
        institutional_score = 7  # neutral
        try:
            from institutional_flow import get_institutional_score
            inst = get_institutional_score(symbol)
            institutional_score = inst.get("score", 7)
            results["agents"]["institutional"] = inst
        except Exception as e:
            results["agents"]["institutional"] = {"error": str(e), "score": 7}

        # Options flow (0-10)
        options_score = 5  # neutral
        try:
            from options_flow import get_options_score
            opts = get_options_score(symbol)
            options_score = opts.get("score", 5)
            results["agents"]["options"] = opts
        except Exception as e:
            results["agents"]["options"] = {"error": str(e), "score": 5}

        # Fundamentals (0-10)
        fundamental_score = 5  # neutral
        try:
            from fundamentals import get_fundamental_score
            fund = get_fundamental_score(symbol)
            fundamental_score = fund.get("score", 5)
            results["agents"]["fundamentals"] = fund
        except Exception as e:
            results["agents"]["fundamentals"] = {"error": str(e), "score": 5}

        # Alternative data (0-5 bonus, added to fundamentals)
        alt_data_bonus = 0
        try:
            from alternative_data import get_alt_data_score
            alt = get_alt_data_score(symbol)
            alt_data_bonus = alt.get("score", 2) - 2  # neutral=0, max +3, min -2
            results["agents"]["alt_data"] = alt
        except Exception as e:
            results["agents"]["alt_data"] = {"error": str(e), "score": 2}
        # Cap fundamentals at 10 after bonus
        fundamental_score = max(0, min(10, fundamental_score + alt_data_bonus))

        # Earnings call signal (modifies the news score)
        earnings_modifier = 0
        try:
            from earnings_calls import get_earnings_signal
            earn = get_earnings_signal(symbol)
            # If earnings tone is strong, add up to +3 to news score
            earn_score = earn.get("score", 5)
            earnings_modifier = max(-3, min(3, earn_score - 5))
            results["agents"]["earnings"] = earn
        except Exception as e:
            results["agents"]["earnings"] = {"error": str(e), "score": 5}
        news_intel_score = max(0, min(20, news_intel_score + earnings_modifier))

        # Assemble the 100-point score
        # Note: quant agent (15) overlaps with technical (30) and institutional (15).
        # We use the quant score as a tiebreaker/bonus rather than adding it fully
        # to avoid double-counting. The 100 points come from:
        #   Technical (30) + News (20) + Social (15) + Institutional (15) + Options (10) + Fundamentals (10) = 100
        # The quant and risk agents are modifiers, not additive components.

        results["scores"] = {
            "technical": technical,          # 0-30
            "news": news_intel_score,        # 0-20
            "sentiment": social_score,       # 0-15
            "institutional": institutional_score,  # 0-15
            "options": options_score,        # 0-10
            "fundamentals": fundamental_score,  # 0-10
        }

        final = sum(results["scores"].values())

        # Apply risk manager modifiers
        risk = results["agents"]["risk"]
        if risk.get("hard_veto"):
            final = min(final, 30)  # cap at 30 if hard veto
            results["hard_veto"] = True
            results["veto_reasons"] = risk.get("vetoes", [])
        else:
            # Risk score as bonus/penalty: 0-10 maps to -5..+5 adjustment
            risk_adj = risk["total_score"] - 5  # -5..+5
            final = max(0, min(100, final + risk_adj))

        # Quant as small bonus (0-3 points max)
        quant_bonus = min(3, quant // 5)
        final = max(0, min(100, final + quant_bonus))

        results["final_score"] = round(final)

        # Rating
        if final >= 80:
            results["rating"] = "STRONG BUY"
            results["recommendation"] = "🟢 Strong Buy Candidate — multiple systems agree with strong conviction. Worth full position size."
        elif final >= 70:
            results["rating"] = "WATCHLIST"
            results["recommendation"] = "🟡 Watchlist — good setup but not perfect. Trade normal size."
        elif final >= 60:
            results["rating"] = "SPECULATIVE"
            results["recommendation"] = "🟠 Speculative — mixed signals. Trade half size or wait for confirmation."
        else:
            results["rating"] = "IGNORE"
            results["recommendation"] = "🔴 Ignore — insufficient conviction or conflicting signals. Stand aside."

        # Retrieve relevant knowledge base rules for context
        direction = idea.direction.value if idea else ""
        regime = idea.regime.value if idea else ""
        rr = idea.plan.risk_reward if idea and idea.plan else 0

        # --- RAG from the vector database (ChromaDB) --- #
        # 1. Investor wisdom (Buffett, Marks, Dalio, etc.)
        rag_context = f"{direction} {regime} risk reward {rr}"
        dw = None
        try:
            from data_warehouse import get_warehouse
            dw = get_warehouse()
            wisdom_results = dw.get_relevant_wisdom(rag_context, n=3)
            results["knowledge_rules"] = [
                {
                    "rule": r["document"][:200],
                    "source": r["metadata"].get("source", "unknown"),
                    "relevance": round(1 - r["distance"], 3),
                    "category": r["metadata"].get("category", ""),
                }
                for r in wisdom_results
            ]
        except Exception:
            # Fall back to the keyword-based KB if ChromaDB is unavailable
            results["knowledge_rules"] = get_rules_for_context(
                verdict=results["rating"], direction=direction,
                regime=regime, risk_reward=rr, has_news=True
            )[:5]

        # 2. Similar historical patterns (from pattern_library)
        try:
            pattern_desc = f"{direction} {regime} "
            if idea and idea.signals:
                # Use the top signal as part of the pattern description
                top_signal = max(idea.signals, key=lambda s: s.weight)
                pattern_desc += top_signal.name
            similar_patterns = (
                dw.get_similar_patterns(pattern_desc, n=3) if dw is not None else []
            )
            results["similar_patterns"] = [
                {
                    "type": p["metadata"].get("type", "?"),
                    "symbol": p["metadata"].get("symbol", "?"),
                    "date": p["metadata"].get("date", "?"),
                    "outcome_1d": p["metadata"].get("outcome_1d", "?"),
                    "outcome_5d": p["metadata"].get("outcome_5d", "?"),
                    "outcome_20d": p["metadata"].get("outcome_20d", "?"),
                    "description": p["document"][:150],
                }
                for p in similar_patterns
            ]
        except Exception:
            results["similar_patterns"] = []

        # Final explanation
        results["explanation"] = (
            f"Technical {technical}/30 | News {news_intel_score}/20 | "
            f"Sentiment {social_score}/15 | Institutional {institutional_score}/15 | "
            f"Options {options_score}/10 | Fundamentals {fundamental_score}/10 | "
            f"= {final}/100 ({results['rating']})"
        )

        return results


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser(description="Portfolio Manager - Final 100-point score")
    ap.add_argument("symbol", help="Stock symbol")
    args = ap.parse_args()
    pm = PortfolioManager()
    result = pm.analyze(args.symbol)
    # Print summary
    print(f"\n{'='*60}")
    print(f"  {result['symbol']} — FINAL SCORE: {result['final_score']}/100")
    print(f"  Rating: {result['rating']}")
    print(f"{'='*60}")
    print(result["explanation"])
    print(f"\n{result['recommendation']}")
    if result.get("hard_veto"):
        print(f"\n⚠ HARD VETO:")
        for v in result["veto_reasons"]:
            print(f"  - {v}")
    print(f"\n📚 Relevant Knowledge Base Rules:")
    for rule in result["knowledge_rules"]:
        print(f"  [{rule['relevance']:.2f}] {rule['source']}")
        print(f"    {rule['rule'][:150]}")
