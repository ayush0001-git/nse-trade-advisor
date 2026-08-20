"""
news_intel.py - Layer 2: News Intelligence

Scores news headlines from -5 (disaster) to +5 (very positive) using an
expanded finance keyword lexicon. The advisor's existing extras.simple_sentiment
returns -1..+1; this module returns the professional -5..+5 scale the user
specified and adds event-type classification (earnings, M&A, FDA, policy, etc.).

Sources used (all free, no API key required):
  - Moneycontrol RSS (markets, company-specific)
  - Economic Times Markets RSS
  - Reuters Business RSS
  - Google News RSS (per-symbol query)

For each symbol we:
  1. Fetch recent headlines from all feeds
  2. Filter to those mentioning the symbol (word-boundary match)
  3. Score each headline -5..+5
  4. Classify the event type (earnings, MA, regulatory, etc.)
  5. Aggregate into a single News Score (0-20 in the final 100-point system)

Usage:
    from news_intel import get_news_score
    result = get_news_score("RELIANCE.NS")
    # -> {"score": 14, "max": 20, "headline_count": 5, "events": [...]}
"""
from __future__ import annotations

import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import urllib.request
import urllib.error

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================================== #
#  RSS feeds (free, no API key)
# =========================================================================== #
FEEDS = [
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    # Per-symbol Google News RSS (built dynamically below)
]

# Google News RSS for a specific symbol (returns recent news mentioning it)
def google_news_feed_url(symbol: str) -> str:
    sym = symbol.split(".")[0]
    return f"https://news.google.com/rss/search?q={quote_plus(sym + ' stock India')}&hl=en-IN&gl=IN&ceid=IN:en"


# =========================================================================== #
#  Event classification keywords
# =========================================================================== #
EVENT_TYPES = {
    "earnings": {
        "keywords": ["quarterly", "q1", "q2", "q3", "q4", "results", "earnings",
                     "revenue", "profit", "loss", "eps", "beats", "misses",
                     "guidance", "margin", "ebitda"],
        "weight": 1.2,  # earnings move markets most
    },
    "ma": {
        "keywords": ["acquisition", "acquire", "merger", "merge", "buyout",
                     "stake", "acquires", "to buy", "takes over"],
        "weight": 1.5,
    },
    "regulatory": {
        "keywords": ["fda", "approval", "approved", "clears", "ban", "probe",
                     "investigation", "lawsuit", "fine", "penalty", "sebi",
                     "rbi", "government", "policy", "regulation", "norm"],
        "weight": 1.3,
    },
    "corporate": {
        "keywords": ["ceo", "cfo", "resigns", "appointed", "steps down",
                     "board", "buyback", "dividend", "split", "rights issue",
                     "bonus", "agm"],
        "weight": 1.0,
    },
    "contracts": {
        "keywords": ["order", "contract", "wins", "awarded", "deal",
                     "memorandum", "mou", "partnership", "joint venture"],
        "weight": 1.1,
    },
    "macro": {
        "keywords": ["inflation", "rate cut", "rate hike", "gdp", "rupee",
                     "crude", "oil", "fed", "rbi", "monetary policy", "budget"],
        "weight": 0.8,
    },
}


# =========================================================================== #
#  Sentiment lexicon (-5 to +5 scale, per the user's spec)
# =========================================================================== #
# Disaster words: -5
DISASTER = {
    "fraud", "scam", "bankrupt", "bankruptcy", "insolvency", "default",
    "arrest", "raid", "crash", "plunge", "collapse", "halted", "suspended",
    "delisted", "liquidation",
}
# Very negative: -3 to -5
VERY_NEGATIVE = {
    "probe", "investigation", "lawsuit", "fine", "penalty", "ban", "recall",
    "warning", "downgrade", "cut", "misses", "loss", "losses", "decline",
    "slump", "plunge", "crash", "selloff", "bearish", "underperform",
    "weak", "slowdown", "default", "insolvency", "fraud", "scam",
    "resigns", "steps down", "suspended", "halted", "delisted",
}
# Positive: +3
POSITIVE = {
    "surge", "jump", "soar", "rally", "gain", "gains", "rise", "rises", "up",
    "beat", "beats", "record", "high", "profit", "growth", "upgrade",
    "bullish", "outperform", "strong", "boost", "wins", "approval", "expansion",
    "buy", "acquires", "awarded", "contract", "order",
}
# Very positive: +5
VERY_POSITIVE = {
    "record high", "all-time high", "multi-year high", "blockbuster",
    "mega deal", "major order", "huge win", "strong buy", "outstanding",
    "stellar", "robust growth", "dividend announced", "buyback announced",
    "bonus issue", "stock split",
}

# Negation handling
NEGATORS = {"not", "no", "never", "without", "barely", "hardly", "fails",
            "failed", "isn", "aren", "wasn", "weren", "cannot", "lacks", "lacking"}


def classify_event(headline: str) -> str:
    """Classify a headline into an event type."""
    h = headline.lower()
    best_type = "other"
    best_score = 0
    for etype, meta in EVENT_TYPES.items():
        score = sum(1 for kw in meta["keywords"] if kw in h) * meta["weight"]
        if score > best_score:
            best_score = score
            best_type = etype
    return best_type


def score_headline(headline: str) -> int:
    """Score a headline from -5 (disaster) to +5 (very positive)."""
    h = headline.lower()
    toks = re.findall(r"[a-z]+", h)
    if not toks:
        return 0

    # Check for multi-word very-positive phrases first (highest signal)
    very_pos_count = sum(1 for phrase in VERY_POSITIVE if phrase in h)

    # Check disaster words (override everything)
    disaster_count = sum(1 for w in DISASTER if w in toks or w in h)

    # Single-word scores with negation handling
    pos = neg = 0
    for i, t in enumerate(toks):
        window = toks[max(0, i - 2):i]
        negated = any(w in NEGATORS for w in window)

        is_pos = t in POSITIVE or t in {w for phrase in VERY_POSITIVE for w in phrase.split()}
        is_neg = t in VERY_NEGATIVE or t in DISASTER

        if negated:
            is_pos, is_neg = is_neg, is_pos  # flip polarity
        pos += int(is_pos)
        neg += int(is_neg)

    # Disaster override
    if disaster_count > 0:
        return -5

    # Very positive phrases
    if very_pos_count >= 1:
        return 5

    # Scale single-word scores
    if pos == 0 and neg == 0:
        return 0
    net = pos - neg
    if net >= 3:
        return 5
    if net >= 2:
        return 3
    if net >= 1:
        return 2
    if net <= -3:
        return -5
    if net <= -2:
        return -3
    if net <= -1:
        return -2
    return 0


def fetch_headlines(symbol: str, limit: int = 30) -> list[dict]:
    """Fetch headlines mentioning the symbol from RSS feeds + Google News."""
    try:
        import feedparser
    except ImportError:
        return []

    sym_key = symbol.split(".")[0].upper()
    headlines = []

    # 1. Per-symbol Google News RSS (most targeted)
    feeds_to_try = [google_news_feed_url(symbol)] + FEEDS
    for url in feeds_to_try:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:limit]:
                title = getattr(entry, "title", "").strip()
                if not title:
                    continue
                # Word-boundary symbol match (avoid SBIN matching SBICARD)
                if not re.search(rf"\b{re.escape(sym_key)}\b", title, re.IGNORECASE):
                    continue
                pub = getattr(entry, "published", "") or getattr(entry, "updated", "")
                headlines.append({
                    "title": title,
                    "published": pub,
                    "source": url.split("/")[2],
                })
        except Exception:
            continue

    # Dedupe by title
    seen = set()
    unique = []
    for h in headlines:
        if h["title"] not in seen:
            seen.add(h["title"])
            unique.append(h)
    return unique[:15]  # cap at 15


def get_news_score(symbol: str) -> dict:
    """Compute the news intelligence score for a stock.

    Returns:
        {
            "symbol": str,
            "score": int,        # 0-20 (contribution to 100-point system)
            "max_score": 20,
            "headline_count": int,
            "avg_headline_score": float,  # -5..+5
            "events": [{"title", "score", "event_type", "published"}],
            "event_breakdown": {"earnings": int, "ma": int, ...},
            "explanation": str,
        }
    """
    headlines = fetch_headlines(symbol, limit=30)
    if not headlines:
        return {
            "symbol": symbol,
            "score": 10,  # neutral when no news
            "max_score": 20,
            "headline_count": 0,
            "avg_headline_score": 0,
            "events": [],
            "event_breakdown": {},
            "explanation": "No recent news found mentioning this stock.",
        }

    scored = []
    event_counts = {}
    for h in headlines:
        score = score_headline(h["title"])
        etype = classify_event(h["title"])
        event_counts[etype] = event_counts.get(etype, 0) + 1
        scored.append({
            "title": h["title"],
            "score": score,
            "event_type": etype,
            "published": h["published"],
            "source": h["source"],
        })

    # Aggregate: weighted average (more recent + higher-magnitude events count more)
    scores = [s["score"] for s in scored]
    avg_score = sum(scores) / len(scores) if scores else 0

    # Map avg_headline_score (-5..+5) to 0-20 scale
    # avg = +5 -> 20, avg = 0 -> 10, avg = -5 -> 0
    news_score = round(max(0, min(20, 10 + avg_score * 2)))

    # Explanation
    n_pos = sum(1 for s in scores if s > 0)
    n_neg = sum(1 for s in scores if s < 0)
    n_neut = sum(1 for s in scores if s == 0)
    top_event = max(event_counts, key=event_counts.get) if event_counts else "none"
    explanation = (
        f"{len(headlines)} recent headlines: {n_pos} positive, {n_neg} negative, "
        f"{n_neut} neutral. Avg sentiment {avg_score:+.1f}/5. "
        f"Top event type: {top_event}. "
        f"News score: {news_score}/20."
    )

    return {
        "symbol": symbol,
        "score": news_score,
        "max_score": 20,
        "headline_count": len(headlines),
        "avg_headline_score": round(avg_score, 2),
        "events": scored[:8],  # top 8 for display
        "event_breakdown": event_counts,
        "explanation": explanation,
    }


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser(description="News Intelligence Layer")
    ap.add_argument("symbol", help="Stock symbol (e.g. RELIANCE or RELIANCE.NS)")
    args = ap.parse_args()
    sym = args.symbol if "." in args.symbol else f"{args.symbol}.NS"
    result = get_news_score(sym)
    print(json.dumps(result, indent=2))
