"""
data_warehouse.py - Central data infrastructure for the advisor.

Manages a local ChromaDB vector database with collections for:
  - investor_wisdom: Buffett letters, Howard Marks memos, Dalio principles, etc.
  - news_archive: News headlines with 1d/5d/30d price outcomes
  - pattern_library: Historical chart patterns (bull flags, breakouts, gaps, etc.)
  - trade_memory: Every trade the system has ever recommended/taken
  - earnings_calls: Earnings call transcripts and analysis
  - filings: SEC/NSE corporate filings
  - market_data: Cached OHLCV for all stocks (20yr history)

The Portfolio Manager agent queries this warehouse via the RAG interface
to retrieve relevant historical context before making decisions.

Usage:
    from data_warehouse import DataWarehouse
    dw = DataWarehouse()
    dw.initialize()  # creates collections, populates with seed data
    results = dw.query("bull flag breakout high volume", collection="pattern_library", n=5)
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "rl_models" / "chromadb"
DB_PATH.parent.mkdir(exist_ok=True)


class DataWarehouse:
    """Central manager for the local vector database."""

    COLLECTIONS = [
        "investor_wisdom",    # Buffett, Marks, Dalio, Munger texts
        "news_archive",       # News with price outcomes
        "pattern_library",    # Historical chart patterns
        "trade_memory",       # Past trades and outcomes
        "earnings_calls",     # Earnings transcripts/analysis
        "filings",            # SEC/NSE filings
        "market_data_cache",  # Cached OHLCV metadata
    ]

    def __init__(self, path: Path = DB_PATH):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.path))
        self._collections = {}

    def initialize(self):
        """Create all collections if they don't exist."""
        for name in self.COLLECTIONS:
            try:
                self._collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as e:
                print(f"  ! collection {name}: {e}")
        return self

    def get_collection(self, name: str):
        """Get a collection by name, initializing if needed."""
        if name not in self._collections:
            self.initialize()
        return self._collections.get(name)

    def add(self, collection: str, documents: list[str],
            metadatas: list[dict] | None = None,
            ids: list[str] | None = None):
        """Add documents to a collection."""
        col = self.get_collection(collection)
        if col is None:
            raise ValueError(f"Collection {collection} not found")
        if ids is None:
            ids = [f"{collection}_{int(time.time()*1000)}_{i}" for i in range(len(documents))]
        if metadatas is None:
            metadatas = [{} for _ in documents]
        col.add(documents=documents, metadatas=metadatas, ids=ids)

    def query(self, query_text: str, collection: str = "investor_wisdom",
              n: int = 5, where: dict | None = None) -> list[dict]:
        """Query a collection and return top-n results with metadata."""
        col = self.get_collection(collection)
        if col is None:
            return []
        try:
            kwargs = {"query_texts": [query_text], "n_results": n}
            if where:
                kwargs["where"] = where
            results = col.query(**kwargs)
            output = []
            for i in range(len(results["documents"][0])):
                output.append({
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "id": results["ids"][0][i] if results["ids"] else "",
                })
            return output
        except Exception as e:
            print(f"  ! query error: {e}")
            return []

    def count(self, collection: str) -> int:
        """Count documents in a collection."""
        col = self.get_collection(collection)
        if col is None:
            return 0
        try:
            return col.count()
        except Exception:
            return 0

    def stats(self) -> dict:
        """Return stats for all collections."""
        self.initialize()
        return {name: self.count(name) for name in self.COLLECTIONS}

    # -- High-level queries for the Portfolio Manager ----------------- #

    def get_relevant_wisdom(self, context: str, n: int = 5) -> list[dict]:
        """Retrieve relevant investor wisdom for a trade context."""
        return self.query(context, collection="investor_wisdom", n=n)

    def get_similar_patterns(self, description: str, n: int = 5) -> list[dict]:
        """Find historical chart patterns similar to the current setup."""
        return self.query(description, collection="pattern_library", n=n)

    def get_similar_news(self, headline: str, n: int = 5) -> list[dict]:
        """Find past news events similar to current news, with their outcomes."""
        return self.query(headline, collection="news_archive", n=n)

    def get_similar_trades(self, description: str, n: int = 5) -> list[dict]:
        """Find past trades similar to the current setup, with their outcomes."""
        return self.query(description, collection="trade_memory", n=n)

    def get_earnings_context(self, query: str, n: int = 3) -> list[dict]:
        """Find relevant earnings call history."""
        return self.query(query, collection="earnings_calls", n=n)


# =========================================================================== #
#  Singleton instance
# =========================================================================== #
_warehouse: Optional[DataWarehouse] = None
_warehouse_lock = threading.Lock()


def get_warehouse() -> DataWarehouse:
    """Get the singleton DataWarehouse instance (thread-safe)."""
    global _warehouse
    if _warehouse is None:
        with _warehouse_lock:
            if _warehouse is None:
                _warehouse = DataWarehouse().initialize()
    return _warehouse


if __name__ == "__main__":
    dw = get_warehouse()
    print("Data Warehouse Stats:")
    for col, count in dw.stats().items():
        print(f"  {col:<25} {count:>6} documents")
    print(f"\nDatabase path: {DB_PATH}")
