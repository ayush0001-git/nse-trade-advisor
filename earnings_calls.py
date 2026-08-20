"""
earnings_calls.py - Earnings Call Transcript Analysis

Fetches and analyzes earnings call transcripts to detect:
  - Management tone (positive vs negative word ratio in Q&A)
  - Guidance changes (raised, lowered, affirmed)
  - Hedging language (red flags for future weakness)
  - Analyst engagement depth

Sources (free):
  - yfinance .calendar for earnings dates
  - Google News RSS for transcript coverage
  - Moneycontrol/ET RSS for Indian earnings coverage

The module doesn't fetch full transcripts (those require paid APIs like
Seeking Alpha or Motley Fool), but it DOES analyze news coverage OF earnings
calls, which captures most of the signal.

Usage:
    from earnings_calls import get_earnings_signal
    result = get_earnings_signal("RELIANCE.NS")
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

from news_intel import score_headline, fetch_headlines


# Earnings-specific keywords for classification
GUIDANCE_RAISED = ["raises guidance", "raises outlook", "upbeat", "raises forecast",
                   "strong outlook", "raises revenue", "raises eps guidance"]
GUIDANCE_LOWERED = ["cuts guidance", "lowers outlook", "cautious", "weak outlook",
                    "cuts forecast", "warns", "disappoints"]
HEDGING_PHRASES = ["we'll see", "challenging", "headwinds", "cautiously optimistic",
                   "macro uncertainty", "softness", "slowing", "pressure",
                   "near-term", "visibility is low"]
BEAT_WORDS = ["beats", "beats estimates", "tops estimates", "better than expected",
              "strong results", "record revenue", "record profit"]
MISS_WORDS = ["misses", "below estimates", "worse than expected", "weak results",
              "loss widens", "revenue falls"]


def fetch_earnings_news(symbol: str) -> list[dict]:
    """Fetch news specifically about earnings/results for this stock."""
    headlines = fetch_headlines(symbol, limit=30)
    # Filter to earnings-related headlines
    earnings_headlines = []
    for h in headlines:
        title_lower = h["title"].lower()
        if any(kw in title_lower for kw in
               ["earnings", "results", "quarterly", "q1", "q2", "q3", "q4",
                "revenue", "profit", "eps", "guidance", "beat", "miss"]):
            earnings_headlines.append(h)
    return earnings_headlines


def analyze_earnings_tone(headlines: list[dict]) -> dict:
    """Analyze the tone of earnings-related headlines.

    Returns:
        {
            "tone_score": float,  # -5..+5
            "beat_count": int,
            "miss_count": int,
            "guidance_raised": bool,
            "guidance_lowered": bool,
            "hedging_detected": list[str],  # phrases found
            "explanation": str,
        }
    """
    if not headlines:
        return {
            "tone_score": 0,
            "beat_count": 0,
            "miss_count": 0,
            "guidance_raised": False,
            "guidance_lowered": False,
            "hedging_detected": [],
            "explanation": "No earnings-related news found.",
        }

    beat_count = miss_count = 0
    guidance_raised = guidance_lowered = False
    hedging_found = []
    total_scores = []

    for h in headlines:
        title = h["title"]
        title_lower = title.lower()

        if any(kw in title_lower for kw in BEAT_WORDS):
            beat_count += 1
        if any(kw in title_lower for kw in MISS_WORDS):
            miss_count += 1
        if any(kw in title_lower for kw in GUIDANCE_RAISED):
            guidance_raised = True
        if any(kw in title_lower for kw in GUIDANCE_LOWERED):
            guidance_lowered = True
        for phrase in HEDGING_PHRASES:
            if phrase in title_lower and phrase not in hedging_found:
                hedging_found.append(phrase)

        total_scores.append(score_headline(title))

    avg_tone = sum(total_scores) / len(total_scores) if total_scores else 0

    explanation_parts = [
        f"{len(headlines)} earnings-related headlines",
        f"beats: {beat_count}",
        f"misses: {miss_count}",
        f"avg tone: {avg_tone:+.1f}/5",
    ]
    if guidance_raised:
        explanation_parts.append("guidance RAISED ✓")
    if guidance_lowered:
        explanation_parts.append("guidance LOWERED ✗")
    if hedging_found:
        explanation_parts.append(f"hedging: {', '.join(hedging_found[:3])}")

    return {
        "tone_score": round(avg_tone, 2),
        "beat_count": beat_count,
        "miss_count": miss_count,
        "guidance_raised": guidance_raised,
        "guidance_lowered": guidance_lowered,
        "hedging_detected": hedging_found,
        "explanation": " | ".join(explanation_parts),
    }


def get_earnings_signal(symbol: str) -> dict:
    """Get the earnings call signal for a stock.

    Returns a score 0-10 (positive earnings momentum) and qualitative flags.
    """
    headlines = fetch_earnings_news(symbol)
    tone = analyze_earnings_tone(headlines)

    # Compute score (0-10)
    score = 5  # neutral baseline
    score += min(3, tone["beat_count"])  # up to +3 for beats
    score -= min(3, tone["miss_count"])  # up to -3 for misses
    if tone["guidance_raised"]:
        score += 2
    if tone["guidance_lowered"]:
        score -= 2
    if tone["hedging_detected"]:
        score -= len(tone["hedging_detected"])  # -1 per hedging phrase
    # Tone adjustment
    score += max(-2, min(2, tone["tone_score"] / 2.5))
    score = max(0, min(10, score))

    # Determine signal
    if score >= 7 and tone["guidance_raised"]:
        signal = "POSITIVE EARNINGS MOMENTUM — hold for PEAD drift (30-60 days)"
    elif score >= 6:
        signal = "MILDLY POSITIVE — earnings support the thesis"
    elif score <= 3 and tone["guidance_lowered"]:
        signal = "NEGATIVE EARNINGS MOMENTUM — avoid or exit"
    elif score <= 4:
        signal = "MILDLY NEGATIVE — earnings contradict the thesis"
    else:
        signal = "NEUTRAL — no clear earnings signal"

    return {
        "symbol": symbol,
        "score": round(score),
        "max_score": 10,
        "signal": signal,
        "tone": tone,
        "headline_count": len(headlines),
        "headlines": [{"title": h["title"], "score": score_headline(h["title"])}
                      for h in headlines[:5]],
        "explanation": tone["explanation"],
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Earnings Call Analysis")
    ap.add_argument("symbol", help="Stock symbol")
    args = ap.parse_args()
    sym = args.symbol if "." in args.symbol else f"{args.symbol}.NS"
    result = get_earnings_signal(sym)
    print(json.dumps(result, indent=2))
