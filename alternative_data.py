"""
alternative_data.py - Alternative Data Signals

Provides signals from non-traditional data sources:
  - Google Trends (search interest proxy)
  - Job posting trends (LinkedIn/Indeed activity proxy)
  - App download trends (for consumer-tech)
  - Web traffic trends (Similarweb proxy)

Since most alternative data APIs require paid subscriptions, this module
uses free proxies:
  - Google Trends: Google News RSS volume as a proxy for search interest
  - Job postings: LinkedIn RSS feeds for company job postings
  - App downloads: Not available free; we skip and return neutral
  - Web traffic: Not available free; we skip and return neutral

The signals are directional (rising/stable/falling) rather than absolute.
Combined score: 0-5 (bonus points added to the fundamentals score).

Usage:
    from alternative_data import get_alt_data_score
    result = get_alt_data_score("RELIANCE.NS")
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


def _fetch_rss_count(url: str, timeout: int = 10) -> int:
    """Count items in an RSS feed (proxy for activity/momentum)."""
    try:
        import feedparser
        # Fetch with an explicit timeout so a hung feed can't block forever
        # (feedparser.parse(url) would fetch without any timeout).
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        parsed = feedparser.parse(data)
        return len(parsed.entries)
    except Exception:
        return 0


def get_google_trends_proxy(symbol: str) -> dict:
    """Proxy Google Trends using Google News RSS item count.

    More news = more search interest = more attention. We compare the
    current 7-day news volume to the historical average.
    """
    sym = symbol.split(".")[0]
    # Current week news count
    url_now = (f"https://news.google.com/rss/search?q={quote_plus(sym + ' stock')}"
               f"&hl=en-IN&gl=IN&ceid=IN:en&when=7d")
    count_now = _fetch_rss_count(url_now)

    # Historical (broader query, ~30 days)
    url_hist = (f"https://news.google.com/rss/search?q={quote_plus(sym + ' stock')}"
                f"&hl=en-IN&gl=IN&ceid=IN:en&when=30d")
    count_hist = _fetch_rss_count(url_hist)

    # Normalize: if weekly count > 1/4 of monthly, interest is rising
    if count_hist == 0:
        momentum = "unknown"
    elif count_now > count_hist / 4 * 1.5:
        momentum = "rising"
    elif count_now < count_hist / 4 * 0.5:
        momentum = "falling"
    else:
        momentum = "stable"

    return {
        "news_count_7d": count_now,
        "news_count_30d": count_hist,
        "momentum": momentum,
        "explanation": f"News volume: {count_now} (7d) vs {count_hist} (30d) — {momentum}",
    }


def get_linkedin_jobs_proxy(symbol: str) -> dict:
    """Proxy job posting activity using LinkedIn RSS (if available)."""
    sym = symbol.split(".")[0]
    # LinkedIn doesn't have a clean public RSS for jobs anymore.
    # We use Google News search for "hiring" + company as a proxy.
    url = (f"https://news.google.com/rss/search?q={quote_plus(sym + ' hiring OR layoffs')}"
           f"&hl=en-IN&gl=IN&ceid=IN:en&when=30d")
    count = _fetch_rss_count(url)

    if count > 5:
        signal = "active_hiring"
    elif count > 0:
        signal = "moderate_activity"
    else:
        signal = "no_news"

    return {
        "jobs_news_count": count,
        "signal": signal,
        "explanation": f"{count} news items about hiring/layoffs in 30d — {signal}",
    }


def get_alt_data_score(symbol: str) -> dict:
    """Compute the alternative data score (0-5 bonus points).

    This is added as a bonus to the fundamentals score in the 100-point system.
    """
    trends = get_google_trends_proxy(symbol)
    jobs = get_linkedin_jobs_proxy(symbol)

    score = 2  # neutral baseline
    if trends["momentum"] == "rising":
        score += 2
    elif trends["momentum"] == "falling":
        score -= 1
    if jobs["signal"] == "active_hiring":
        score += 1
    elif jobs["signal"] == "no_news":
        score -= 0  # neutral

    score = max(0, min(5, score))

    return {
        "symbol": symbol,
        "score": score,
        "max_score": 5,
        "google_trends": trends,
        "job_postings": jobs,
        "explanation": (
            f"Search interest: {trends['momentum']} | "
            f"Jobs: {jobs['signal']} | "
            f"Alt-data bonus: {score}/5"
        ),
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Alternative Data Signals")
    ap.add_argument("symbol", help="Stock symbol")
    args = ap.parse_args()
    sym = args.symbol if "." in args.symbol else f"{args.symbol}.NS"
    result = get_alt_data_score(sym)
    print(json.dumps(result, indent=2))
