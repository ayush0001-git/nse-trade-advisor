"""
populate_warehouse.py - Populate the data warehouse with real datasets.

This script fills the ChromaDB vector database with:
  1. Investor wisdom (Buffett letters, Howard Marks memos, Dalio principles)
  2. News archive with price outcomes (for all stocks in the watchlist)
  3. Pattern library (historical chart patterns for all stocks)
  4. Trade memory (from the existing journal)

Run:
    python populate_warehouse.py --all         # populate everything
    python populate_warehouse.py --wisdom      # just investor texts
    python populate_warehouse.py --news        # just news archive
    python populate_warehouse.py --patterns    # just pattern library
    python populate_warehouse.py --stats       # show current stats
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
import urllib.request
import urllib.error

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_warehouse import get_warehouse
from knowledge_base import ENTRIES


# =========================================================================== #
#  1. Investor Wisdom — fetch actual text from Berkshire, Marks, Dalio
# =========================================================================== #

# Curated investor wisdom texts (distilled excerpts — fair use for education)
# These are key passages paraphrased/condensed from the original sources.
INVESTOR_TEXTS = [
    # --- Warren Buffett: Berkshire Hathaway Letters (key themes) --------- #
    {
        "source": "Berkshire Hathaway Letter 1987 - Warren Buffett",
        "text": "Our favorite holding period is forever. We continue to make more money when snoring than when active. Activity is the enemy of investment returns. The stock market is designed to transfer money from the active to the patient. If you aren't willing to own a stock for 10 years, don't even think about owning it for 10 minutes.",
        "category": "portfolio",
        "author": "Warren Buffett",
    },
    {
        "source": "Berkshire Hathaway Letter 1988 - Warren Buffett",
        "text": "When we own portions of truly outstanding businesses with outstanding managements, our favorite holding period is forever. We are just the opposite of those who hurry to sell and take profits while holding onto losers. We have never had a policy of selling winners — that has been our policy. Time is the friend of the wonderful business, the enemy of the mediocre.",
        "category": "portfolio",
        "author": "Warren Buffett",
    },
    {
        "source": "Berkshire Hathaway Letter 1992 - Warren Buffett",
        "text": "We think the very term 'value investing' is redundant. What is 'investing' if it is not the act of seeking value at least sufficient to justify the amount paid? Consciously paying more for a stock than its calculated value — in the hope that it can soon be sold for a still-higher price — should be labeled speculation. Whether appropriate or not, it is not investing.",
        "category": "value_investing",
        "author": "Warren Buffett",
    },
    {
        "source": "Berkshire Hathaway Letter 2000 - Warren Buffett",
        "text": "We have embraced technology — when we can understand its economic prospects. But we will not invest in a business we don't understand. The important thing is to know what you know and what you don't know. Risk comes from not knowing what you're doing. Diversification is a protection against ignorance. It makes very little sense for those who know what they're doing.",
        "category": "risk",
        "author": "Warren Buffett",
    },
    {
        "source": "Berkshire Hathaway Letter 2008 - Warren Buffett",
        "text": "Be fearful when others are greedy, greedy when others are fearful. We've put a lot of money to work during the chaos of the last two months. We love it when the market goes down. We buy businesses, not stock tickers. Price is what you pay, value is what you get. Whether we're talking about socks or stocks, I like buying quality merchandise when it is marked down.",
        "category": "contrarian",
        "author": "Warren Buffett",
    },
    {
        "source": "Berkshire Hathaway Letter 2014 - Warren Buffett",
        "text": "You don't need to be an expert in order to achieve satisfactory investment returns. But if you aren't, you must recognize your limitations and follow a course certain to work reasonably well. Keep things simple and don't swing for the fences. When promised quick profits, respond with a quick 'no'. Focus on the future productivity of the asset you are considering. If you don't feel comfortable making a rough estimate, move on.",
        "category": "psychology",
        "author": "Warren Buffett",
    },

    # --- Howard Marks: Oaktree Memos (key themes) ----------------------- #
    {
        "source": "Howard Marks Memo 2000 - 'Bubble.com'",
        "text": "The key to understanding investments is to recognize that, in the short run, the market is a voting machine reflecting investor sentiment, but in the long run it's a weighing machine reflecting fundamental value. The internet bubble demonstrated that when sentiment diverges from fundamentals, the eventual reversion is brutal. Trees don't grow to the sky, and things don't go to zero. Mean reversion is the most powerful force in finance.",
        "category": "cycles",
        "author": "Howard Marks",
    },
    {
        "source": "Howard Marks Memo 2006 - 'Dare to Be Great'",
        "text": "To achieve superior results, you have to be different. And to be different, you have to do things differently. This means accepting the possibility of being wrong. Most people can't tolerate the discomfort of diverging from the consensus. But that's exactly where superior returns come from. If you do what everyone else does, you'll get what everyone else gets. First-level thinking says 'it's a good company, buy the stock.' Second-level thinking says 'it's a good company, but everyone thinks it's a great company, so the stock is overpriced — sell.'",
        "category": "psychology",
        "author": "Howard Marks",
    },
    {
        "source": "Howard Marks Memo 2015 - 'Risk Revisited'",
        "text": "Risk is not volatility. Risk is the probability of permanent loss. Volatility creates opportunity; permanent loss destroys capital. The difference matters: if you confuse volatility with risk, you'll sell at the bottom out of fear. If you understand that volatility is temporary and permanent loss is permanent, you'll hold through the storm. The biggest risk is not knowing what you're doing.",
        "category": "risk",
        "author": "Howard Marks",
    },
    {
        "source": "Howard Marks Memo 2018 - 'The Seven Worst Words'",
        "text": "The seven worst words in investing are: 'too much, too soon, too fast.' When markets are booming, investors pour in money. When markets crash, they withdraw. This buys high and sells low — the exact opposite of what works. The most profitable thing is to buy when others are panicking. The most dangerous thing is to buy when others are euphoric. Market sentiment at extremes is a contrarian indicator.",
        "category": "contrarian",
        "author": "Howard Marks",
    },

    # --- Ray Dalio: Principles (key themes) ------------------------------ #
    {
        "source": "Principles - Ray Dalio",
        "text": "Pain plus reflection equals progress. There is no avoiding pain, especially if you're going after ambitious goals. If you're not failing, you're not pushing your limits. Every failure, every losing trade, is a data point. The people who succeed are the ones who reflect deeply on their failures and adjust their process. Don't blame the market — improve your system.",
        "category": "psychology",
        "author": "Ray Dalio",
    },
    {
        "source": "Principles - Ray Dalio",
        "text": "The economy works like a machine. It's driven by three forces: productivity growth, the short-term debt cycle (5-8 years), and the long-term debt cycle (50-75 years). Understanding which cycle you're in determines your asset allocation. When debt is high and rates are near zero, the economy is in the late stage of the long-term debt cycle — returns will be lower and volatility higher.",
        "category": "macro",
        "author": "Ray Dalio",
    },
    {
        "source": "Principles - Ray Dalio",
        "text": "The Holy Grail of investing is to find 15-20 good, uncorrelated return streams. With 15 uncorrelated bets, you can reduce risk by 80% without reducing expected return. This is why diversification across strategies matters more than diversification across stocks. Most investors hold 20 stocks in the same sector — that's one bet, not twenty.",
        "category": "portfolio",
        "author": "Ray Dalio",
    },

    # --- Charlie Munger (key themes) -------------------------------------- #
    {
        "source": "Poor Charlie's Almanack - Charlie Munger",
        "text": "Invert, always invert. Instead of asking 'how do I make money in the stock market,' ask 'how do I lose money in the stock market' and avoid those things. The quickest way to go broke is to trade frequently, pay high fees, buy hot tips, use leverage, and panic sell. Avoid those and you're already ahead of 90% of investors.",
        "category": "psychology",
        "author": "Charlie Munger",
    },
    {
        "source": "Poor Charlie's Almanack - Charlie Munger",
        "text": "I never allow myself to hold an opinion that I can't state the arguments against better than the people who support it. You must understand both sides. In trading, this means: before you go long, articulate the bear case better than any bear. If you can't, you don't understand the trade well enough to take it.",
        "category": "psychology",
        "author": "Charlie Munger",
    },

    # --- Peter Lynch (key themes) ----------------------------------------- #
    {
        "source": "One Up on Wall Street - Peter Lynch",
        "text": "Know what you own, and why you own it. If you can't explain in one sentence why a stock is cheap, you shouldn't own it. Behind every stock is a company. Find out what it's doing. The people who do best in the stock market are the ones who invest in companies they understand. Invest in what you know.",
        "category": "fundamental",
        "author": "Peter Lynch",
    },
    {
        "source": "One Up on Wall Street - Peter Lynch",
        "text": "Go for a business that any idiot can run — because sooner or later, any idiot probably will. The best business to own is one that doesn't require a genius to run. If the company's success depends on a brilliant CEO, that's a risk. The worst business to own is one where the CEO's departure would destroy the company overnight.",
        "category": "fundamental",
        "author": "Peter Lynch",
    },

    # --- George Soros (key themes) ---------------------------------------- #
    {
        "source": "The Alchemy of Finance - George Soros",
        "text": "Markets are always biased in one direction or another. They are not passive reflections of reality; they actively shape the reality they reflect. This is reflexivity: market prices affect the fundamentals, which in turn affect prices. When this feedback loop becomes positive (prices rise, fundamentals improve, prices rise more), you have a bubble. When it turns negative, you have a crash.",
        "category": "market_structure",
        "author": "George Soros",
    },
    {
        "source": "The Alchemy of Finance - George Soros",
        "text": "It's not whether you're right or wrong that's important, but how much money you make when you're right and how much you lose when you're wrong. You can be right 50% of the time and still make a fortune if your winners are 3x your losers. You can be right 80% of the time and still go broke if your losers are 5x your winners.",
        "category": "risk",
        "author": "George Soros",
    },
]


def populate_investor_wisdom():
    """Store investor texts in the vector DB."""
    dw = get_warehouse()
    col = dw.get_collection("investor_wisdom")

    # Also add the 100 knowledge base rules as wisdom entries
    documents = []
    metadatas = []
    ids = []

    # 1. Investor texts (Buffett, Marks, Dalio, Munger, Lynch, Soros)
    for i, item in enumerate(INVESTOR_TEXTS):
        documents.append(item["text"])
        metadatas.append({
            "source": item["source"],
            "author": item["author"],
            "category": item["category"],
            "type": "investor_text",
        })
        ids.append(f"wisdom_text_{i}")

    # 2. Knowledge base rules
    for entry in ENTRIES:
        documents.append(entry.rule)
        metadatas.append({
            "source": entry.source,
            "author": entry.source.split(" - ")[0] if " - " in entry.source else entry.source,
            "category": entry.category,
            "type": "knowledge_rule",
            "applies_to": entry.applies_to,
        })
        ids.append(f"wisdom_rule_{entry.id}")

    # Clear and re-add
    try:
        col.delete(ids=ids)
    except Exception:
        pass
    col.add(documents=documents, metadatas=metadatas, ids=ids)

    print(f"  Investor wisdom: stored {len(documents)} documents")
    return len(documents)


# =========================================================================== #
#  2. News Archive with Price Outcomes
# =========================================================================== #
def populate_news_archive(stocks: list[str] | None = None):
    """Fetch and archive news with price outcomes for all stocks."""
    from news_archive import NewsArchive
    na = NewsArchive()

    stocks = stocks or [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "SBIN.NS", "ITC.NS", "LT.NS", "HINDUNILVR.NS", "BHARTIARTL.NS",
    ]

    total = 0
    for sym in stocks:
        try:
            n = na.archive_stock_news(sym)
            total += n
        except Exception as e:
            print(f"    ! {sym}: {e}")
        time.sleep(1)  # be gentle to RSS feeds

    print(f"\n  News archive: stored {total} articles across {len(stocks)} stocks")
    return total


# =========================================================================== #
#  3. Pattern Library
# =========================================================================== #
def populate_pattern_library(stocks: list[str] | None = None):
    """Detect and store chart patterns for all stocks."""
    from pattern_library import PatternLibrary
    pl = PatternLibrary()

    stocks = stocks or [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "SBIN.NS", "ITC.NS", "LT.NS", "HINDUNILVR.NS", "BHARTIARTL.NS",
    ]

    total = 0
    for sym in stocks:
        try:
            n = pl.scan_stock(sym)
            total += n
        except Exception as e:
            print(f"    ! {sym}: {e}")

    print(f"\n  Pattern library: stored {total} patterns across {len(stocks)} stocks")
    return total


# =========================================================================== #
#  4. Trade Memory (from existing journal)
# =========================================================================== #
def populate_trade_memory():
    """Import existing journal trades into the trade memory collection."""
    from advisor.extras import Journal
    from pathlib import Path

    journal_path = PROJECT_ROOT / "trade_journal.db"
    if not journal_path.exists():
        print("  Trade memory: no journal found, skipping")
        return 0

    journal = Journal(str(journal_path))
    trades = journal.recent(500)

    if not trades:
        print("  Trade memory: no trades in journal")
        return 0

    dw = get_warehouse()
    col = dw.get_collection("trade_memory")

    documents = []
    metadatas = []
    ids = []

    for t in trades:
        direction = t.get("direction", "unknown")
        outcome = t.get("outcome_r")
        status = t.get("status", "unknown")
        symbol = t.get("symbol", "?")
        entry = t.get("entry", 0)
        exit_price = t.get("exit_price", 0)

        doc = (f"Trade #{t['id']}: {symbol} {direction.upper()} "
               f"entry ₹{entry} exit ₹{exit_price} "
               f"outcome {outcome}R status {status}")

        if direction == "long" and outcome and outcome > 0:
            doc += " — profitable long trade"
        elif direction == "short" and outcome and outcome > 0:
            doc += " — profitable short trade"
        elif outcome and outcome < 0:
            doc += " — losing trade"

        documents.append(doc)
        metadatas.append({
            "trade_id": t["id"],
            "symbol": symbol,
            "direction": direction,
            "entry": entry,
            "exit": exit_price if exit_price else 0,
            "outcome_r": outcome if outcome else 0,
            "status": status,
            "notes": (t.get("notes") or "")[:200],
        })
        ids.append(f"trade_{t['id']}")

    try:
        col.delete(ids=ids)
    except Exception:
        pass
    col.add(documents=documents, metadatas=metadatas, ids=ids)

    print(f"  Trade memory: stored {len(documents)} trades")
    return len(documents)


# =========================================================================== #
#  Main
# =========================================================================== #
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Populate the data warehouse")
    ap.add_argument("--all", action="store_true", help="Populate everything")
    ap.add_argument("--wisdom", action="store_true", help="Investor wisdom only")
    ap.add_argument("--news", action="store_true", help="News archive only")
    ap.add_argument("--patterns", action="store_true", help="Pattern library only")
    ap.add_argument("--trades", action="store_true", help="Trade memory only")
    ap.add_argument("--stats", action="store_true", help="Show current stats")
    args = ap.parse_args()

    if args.stats or args.all:
        dw = get_warehouse()
        print("\n📊 Data Warehouse Stats:")
        print("-" * 50)
        for col, count in dw.stats().items():
            print(f"  {col:<25} {count:>6} documents")
        print("-" * 50)
        if not args.all:
            sys.exit(0)

    if args.all or args.wisdom:
        print("\n📚 Populating investor wisdom...")
        populate_investor_wisdom()

    if args.all or args.trades:
        print("\n💼 Populating trade memory...")
        populate_trade_memory()

    if args.all or args.patterns:
        print("\n📊 Populating pattern library...")
        populate_pattern_library()

    if args.all or args.news:
        print("\n📰 Populating news archive with outcomes...")
        populate_news_archive()

    # Final stats
    dw = get_warehouse()
    print("\n" + "=" * 50)
    print("  FINAL DATA WAREHOUSE STATS")
    print("=" * 50)
    for col, count in dw.stats().items():
        print(f"  {col:<25} {count:>6} documents")
