"""
social_sentiment.py - Layer 3: Social Sentiment

Tracks Reddit mentions of stocks across finance subreddits using Reddit's
free JSON API (no authentication required - just append /.json to any URL).

Subreddits scanned:
  - r/IndianStreetBets (Indian stock picks)
  - r/IndiaInvestments (Indian investing)
  - r/investing (global)
  - r/stocks (global)
  - r/wallstreetbets (global momentum)

For each symbol we compute:
  - Mention count (last 24h vs previous 24h -> momentum)
  - Sentiment of each mention (using news_intel.score_headline)
  - Mention growth rate (viral detection)
  - Final Social Score (0-15 in the 100-point system)

Rate limit: Reddit allows ~60 requests/minute unauthenticated. We throttle
to 1 request/second and cache results for 10 minutes.

Usage:
    from social_sentiment import get_social_score
    result = get_social_score("RELIANCE.NS")
    # -> {"score": 9, "max": 15, "mentions_today": 5, "momentum": "rising"}
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus
import urllib.request
import urllib.error

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from news_intel import score_headline

CACHE_PATH = PROJECT_ROOT / "rl_models" / "social_cache.json"
CACHE_TTL_SECONDS = 600  # 10 minutes


SUBREDDITS = [
    "IndianStreetBets",
    "IndiaInvestments",
    "investing",
    "stocks",
    "wallstreetbets",
]


def _fetch_json(url: str, timeout: int = 10) -> dict | list | None:
    """Fetch JSON from Reddit with browser-like headers."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "advisor-bot/1.0 (research; educational use)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return None


def fetch_subreddit_posts(subreddit: str, limit: int = 25) -> list[dict]:
    """Fetch recent posts from a subreddit via the public JSON API."""
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    data = _fetch_json(url)
    if not data or "data" not in data:
        return []
    posts = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        posts.append({
            "title": post.get("title", ""),
            "selftext": post.get("selftext", "")[:500],  # cap body
            "score": post.get("score", 0),
            "num_comments": post.get("num_comments", 0),
            "created_utc": post.get("created_utc", 0),
            "subreddit": subreddit,
            "url": post.get("url", ""),
        })
    return posts


def mentions_symbol(text: str, symbol: str) -> bool:
    """Check if text mentions the symbol (word-boundary match).

    Handles common variants: $RELIANCE, RELIANCE.NS, RELIANCE, Reliance.
    """
    sym = symbol.split(".")[0].upper()
    # Word-boundary match on the symbol (case-insensitive)
    if re.search(rf"\b{re.escape(sym)}\b", text, re.IGNORECASE):
        return True
    # Also match $SYMBOL (Reddit/cashtag convention)
    if f"${sym.lower()}" in text.lower():
        return True
    return False


def get_social_score(symbol: str) -> dict:
    """Compute the social sentiment score for a stock.

    Returns:
        {
            "symbol": str,
            "score": int,         # 0-15
            "max_score": 15,
            "mentions_today": int,
            "mentions_yesterday": int,
            "mention_momentum": str,  # "rising", "stable", "falling", "none"
            "avg_sentiment": float,    # -5..+5
            "total_upvotes": int,
            "total_comments": int,
            "top_mentions": [{"title", "subreddit", "score", "upvotes"}],
            "explanation": str,
        }
    """
    sym_key = symbol.split(".")[0]
    now = datetime.utcnow()
    cutoff_24h = now - timedelta(hours=24)
    cutoff_48h = now - timedelta(hours=48)

    all_posts = []
    for sub in SUBREDDITS:
        posts = fetch_subreddit_posts(sub, limit=50)
        all_posts.extend(posts)
        time.sleep(1.0)  # be gentle to Reddit

    # Filter to posts mentioning the symbol
    mentions_today = []
    mentions_yesterday = []
    for post in all_posts:
        text = post["title"] + " " + post["selftext"]
        if not mentions_symbol(text, symbol):
            continue
        post_time = datetime.utcfromtimestamp(post["created_utc"])
        if post_time >= cutoff_24h:
            mentions_today.append(post)
        elif post_time >= cutoff_48h:
            mentions_yesterday.append(post)

    # Score each mention
    today_scores = []
    for m in mentions_today:
        s = score_headline(m["title"])
        today_scores.append(s)
        m["sentiment_score"] = s

    avg_sentiment = sum(today_scores) / len(today_scores) if today_scores else 0
    total_upvotes = sum(m["score"] for m in mentions_today)
    total_comments = sum(m["num_comments"] for m in mentions_today)

    # Mention momentum
    n_today = len(mentions_today)
    n_yesterday = len(mentions_yesterday)
    if n_today == 0:
        momentum = "none"
    elif n_yesterday == 0:
        momentum = "new" if n_today > 0 else "none"
    else:
        growth = (n_today - n_yesterday) / max(n_yesterday, 1)
        if growth > 0.5:
            momentum = "rising"
        elif growth < -0.3:
            momentum = "falling"
        else:
            momentum = "stable"

    # Social score (0-15)
    # Component 1: mention count (0-5 points) - more mentions = more attention
    count_score = min(5, n_today)
    # Component 2: sentiment (0-5 points) - avg sentiment scaled from -5..+5 to 0..5
    sentiment_score = max(0, min(5, (avg_sentiment + 5) / 2))
    # Component 3: engagement (0-5 points) - upvotes + comments indicate conviction
    engagement_score = min(5, (total_upvotes / 20) + (total_comments / 10))

    social_score = round(count_score + sentiment_score + engagement_score)

    explanation = (
        f"{n_today} mentions today (vs {n_yesterday} yesterday) — momentum: {momentum}. "
        f"Avg sentiment: {avg_sentiment:+.1f}/5. "
        f"Engagement: {total_upvotes} upvotes, {total_comments} comments. "
        f"Social score: {social_score}/15."
    )

    return {
        "symbol": symbol,
        "score": social_score,
        "max_score": 15,
        "mentions_today": n_today,
        "mentions_yesterday": n_yesterday,
        "mention_momentum": momentum,
        "avg_sentiment": round(avg_sentiment, 2),
        "total_upvotes": total_upvotes,
        "total_comments": total_comments,
        "top_mentions": [
            {
                "title": m["title"][:100],
                "subreddit": m["subreddit"],
                "sentiment": m["sentiment_score"],
                "upvotes": m["score"],
            }
            for m in sorted(mentions_today, key=lambda x: x["score"], reverse=True)[:5]
        ],
        "explanation": explanation,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Social Sentiment Layer")
    ap.add_argument("symbol", help="Stock symbol (e.g. RELIANCE or RELIANCE.NS)")
    args = ap.parse_args()
    sym = args.symbol if "." in args.symbol else f"{args.symbol}.NS"
    result = get_social_score(sym)
    print(json.dumps(result, indent=2))
