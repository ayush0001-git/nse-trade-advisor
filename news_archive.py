"""
news_archive.py - News archive with price outcomes.

The most valuable dataset per the user's ranking: news headlines stored with
1-day, 5-day, and 30-day price reactions. This lets the AI learn:
  "When this type of news happens, what usually happens next?"

Workflow:
  1. Fetch news headlines for a stock (via RSS)
  2. For each headline, look up the stock's price 1/5/30 days after
  3. Store in ChromaDB with metadata: {symbol, date, headline, outcome_1d, outcome_5d, outcome_30d}
  4. Query: "find news similar to this headline, what was the outcome?"

Usage:
    from news_archive import NewsArchive
    na = NewsArchive()
    na.archive_stock_news("RELIANCE.NS")  # fetch + store
    similar = na.find_similar("RELIANCE beats Q3 estimates")
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_warehouse import get_warehouse
from news_intel import fetch_headlines, score_headline
from strategies import fetch_stock_data


class NewsArchive:
    """Manages the news-with-outcomes collection in the vector DB."""

    def __init__(self):
        self.dw = get_warehouse()

    def archive_stock_news(self, symbol: str, lookback_days: int = 90) -> int:
        """Fetch news for a stock and store with price outcomes.

        Only archives news old enough to have 30-day outcomes (i.e., news
        from at least 30 days ago). Recent news is stored without outcomes.

        Returns the number of articles archived.
        """
        sym = symbol if "." in symbol else f"{symbol}.NS"
        print(f"  Archiving news for {sym}...")

        # Fetch headlines
        headlines = fetch_headlines(sym, limit=30)
        if not headlines:
            print(f"    no headlines found")
            return 0

        # Fetch price data for outcome calculation (need 60 days beyond oldest news)
        try:
            df = fetch_stock_data(sym, period="1y")
        except Exception as e:
            print(f"    ! price data fetch failed: {e}")
            return 0

        # For each headline, compute outcomes
        documents = []
        metadatas = []
        ids = []
        archived = 0

        for h in headlines:
            title = h["title"]
            # Try to parse the publication date
            pub_date = self._parse_date(h.get("published", ""))
            if pub_date is None:
                continue

            # Find the price on the news date and 1/5/30 days after
            outcomes = self._compute_outcomes(df, pub_date)

            # Build the document text (what the vector DB indexes)
            doc_text = f"{title} [{sym} on {pub_date.strftime('%Y-%m-%d')}]"
            if outcomes:
                doc_text += f" -> 1d: {outcomes['outcome_1d']:+.1f}%, 5d: {outcomes['outcome_5d']:+.1f}%, 30d: {outcomes['outcome_30d']:+.1f}%"

            sentiment = score_headline(title)

            metadata = {
                "symbol": sym,
                "date": pub_date.strftime("%Y-%m-%d"),
                "headline": title[:200],  # chroma metadata has size limits
                "sentiment": sentiment,
                "source": h.get("source", "unknown"),
            }
            if outcomes:
                metadata["outcome_1d"] = outcomes["outcome_1d"]
                metadata["outcome_5d"] = outcomes["outcome_5d"]
                metadata["outcome_30d"] = outcomes["outcome_30d"]
                metadata["has_outcomes"] = True
            else:
                metadata["has_outcomes"] = False

            doc_id = f"news_{sym}_{pub_date.strftime('%Y%m%d')}_{hash(title) % 10000}"

            documents.append(doc_text)
            metadatas.append(metadata)
            ids.append(doc_id)
            archived += 1

        if documents:
            # Upsert (in case we're re-archiving)
            col = self.dw.get_collection("news_archive")
            try:
                col.delete(ids=ids)  # remove old entries first
            except Exception:
                pass
            col.add(documents=documents, metadatas=metadatas, ids=ids)

        print(f"    archived {archived} headlines for {sym}")
        return archived

    def _parse_date(self, pub_str: str) -> Optional[datetime]:
        """Parse various RSS date formats."""
        if not pub_str:
            return None
        # Try common RSS date formats
        formats = [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(pub_str.strip(), fmt)
            except ValueError:
                continue
        # Try dateutil as fallback
        try:
            from dateutil import parser
            return parser.parse(pub_str)
        except Exception:
            return None

    def _compute_outcomes(self, df: pd.DataFrame, news_date: datetime) -> Optional[dict]:
        """Compute 1-day, 5-day, 30-day returns after the news date.

        Returns None if the news date is too recent or outside the data range.
        """
        # Normalize news_date to date (no time)
        news_date = news_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Find the index position closest to news_date
        try:
            # Find the first trading day ON OR AFTER news_date
            mask = df.index >= pd.Timestamp(news_date)
            if mask.sum() == 0:
                return None
            start_idx = mask.argmax()
            entry_price = float(df["close"].iloc[start_idx])

            # 1-day outcome: next trading day's close
            if start_idx + 1 < len(df):
                p1 = float(df["close"].iloc[start_idx + 1])
                outcome_1d = (p1 - entry_price) / entry_price * 100
            else:
                return None  # not enough data

            # 5-day outcome
            if start_idx + 5 < len(df):
                p5 = float(df["close"].iloc[start_idx + 5])
                outcome_5d = (p5 - entry_price) / entry_price * 100
            else:
                return None

            # 30-day outcome
            if start_idx + 30 < len(df):
                p30 = float(df["close"].iloc[start_idx + 30])
                outcome_30d = (p30 - entry_price) / entry_price * 100
            else:
                return None  # news too recent for 30-day outcome

            return {
                "outcome_1d": round(outcome_1d, 2),
                "outcome_5d": round(outcome_5d, 2),
                "outcome_30d": round(outcome_30d, 2),
            }
        except Exception:
            return None

    def find_similar(self, headline: str, n: int = 5) -> list[dict]:
        """Find past news similar to this headline, with their outcomes.

        This is the key RAG query: "when news like this happened before,
        what happened to the stock price?"
        """
        results = self.dw.query(headline, collection="news_archive", n=n)
        # Enrich with outcome stats
        for r in results:
            meta = r["metadata"]
            if meta.get("has_outcomes"):
                r["outcome_summary"] = (
                    f"1d: {meta['outcome_1d']:+.1f}%, "
                    f"5d: {meta['outcome_5d']:+.1f}%, "
                    f"30d: {meta['outcome_30d']:+.1f}%"
                )
            else:
                r["outcome_summary"] = "outcomes pending (news too recent)"
        return results

    def get_stats(self) -> dict:
        """Return stats about the news archive."""
        col = self.dw.get_collection("news_archive")
        total = col.count() if col else 0
        return {
            "total_articles": total,
            "collection": "news_archive",
        }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="News Archive with Price Outcomes")
    sub = ap.add_subparsers(dest="command", required=True)
    arch = sub.add_parser("archive", help="Archive news for a stock")
    arch.add_argument("symbol")
    q = sub.add_parser("query", help="Find similar past news")
    q.add_argument("headline")
    sub.add_parser("stats", help="Show archive stats")
    args = ap.parse_args()

    na = NewsArchive()
    if args.command == "archive":
        n = na.archive_stock_news(args.symbol)
        print(f"\nArchived {n} articles.")
    elif args.command == "query":
        results = na.find_similar(args.headline)
        print(f"\nSimilar past news ({len(results)} found):")
        for r in results:
            print(f"  [{r['distance']:.3f}] {r['metadata'].get('symbol', '?')} "
                  f"({r['metadata'].get('date', '?')})")
            print(f"    {r['metadata'].get('headline', '?')[:100]}")
            print(f"    Outcome: {r['outcome_summary']}")
    elif args.command == "stats":
        print(json.dumps(na.get_stats(), indent=2))
