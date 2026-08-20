"""
agents/news_hunter.py - Agent 1: News Hunter

Reads news, earnings, filings, transcripts. Combines:
  - RSS news sentiment (news_intel.py) — 0-20 pts
  - Social sentiment (social_sentiment.py) — 0-15 pts

Total contribution: 0-35 points in the 100-point system.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class NewsHunter:
    """Agent that hunts for news, earnings, and social sentiment."""

    name = "News Hunter"
    role = "Reads news, earnings, filings, and social sentiment"

    def analyze(self, symbol: str) -> dict:
        """Run the news hunter analysis for a stock."""
        results = {
            "agent": self.name,
            "symbol": symbol,
            "components": {},
            "total_score": 0,
            "max_score": 35,
            "error": None,
        }

        # 1. News Intelligence (0-20)
        try:
            from news_intel import get_news_score
            news = get_news_score(symbol)
            results["components"]["news_intel"] = news
            results["total_score"] += news.get("score", 0)
        except Exception as e:
            results["components"]["news_intel"] = {"error": str(e), "score": 10}
            results["total_score"] += 10  # neutral fallback

        # 2. Social Sentiment (0-15)
        try:
            from social_sentiment import get_social_score
            social = get_social_score(symbol)
            results["components"]["social_sentiment"] = social
            results["total_score"] += social.get("score", 0)
        except Exception as e:
            results["components"]["social_sentiment"] = {"error": str(e), "score": 7}
            results["total_score"] += 7  # neutral fallback

        # 3. FinBERT sentiment on stored news_archive headlines.
        # Additive signal only — does NOT change the 0-35 total_score.
        # Exposed as sentiment_score in [-1, +1] with headline_count metadata.
        try:
            from advisor.news_agg import sentiment_for_symbol
            agg = sentiment_for_symbol(symbol)
            results["components"]["finbert_sentiment"] = agg
            results["sentiment_score"] = float(agg.get("mean_score", 0.0))
            results["sentiment_headlines"] = int(agg.get("headline_count", 0))
        except Exception as e:
            results["components"]["finbert_sentiment"] = {"error": str(e)}
            results["sentiment_score"] = 0.0
            results["sentiment_headlines"] = 0

        results["explanation"] = (
            f"News Intelligence: {results['components'].get('news_intel', {}).get('score', 0)}/20 | "
            f"Social Sentiment: {results['components'].get('social_sentiment', {}).get('score', 0)}/15 | "
            f"FinBERT: {results['sentiment_score']:+.2f} "
            f"({results['sentiment_headlines']} headlines) | "
            f"Total: {results['total_score']}/35"
        )
        return results
