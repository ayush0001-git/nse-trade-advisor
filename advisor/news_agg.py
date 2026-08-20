"""
advisor/news_agg.py - Aggregate FinBERT-scored news_archive rows by symbol.

Reads sentiment_score metadata written by advisor/score_news.py and returns
a per-symbol summary: mean, headline count, latest headline, most-positive
and most-negative titles.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _parse_iso(s: str):
    if not s:
        return None
    try:
        s2 = s.replace("Z", "+00:00") if s.endswith("Z") else s
        return datetime.fromisoformat(s2)
    except Exception:
        return None


def _to_float(x, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _empty(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "mean_score": 0.0,
        "headline_count": 0,
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
        "most_positive": None,
        "most_negative": None,
        "latest_at": None,
    }


def sentiment_for_symbol(symbol: str, max_age_days: int = 14) -> dict:
    """Aggregate FinBERT sentiment for one symbol from news_archive.

    Filters:
      * metadata.symbol matches (case-insensitive)
      * metadata.published within the last `max_age_days` days
        (rows with unparseable timestamps are included so we don't lose data)
      * metadata.sentiment_score is present and numeric
    """
    from data_warehouse import get_warehouse
    sym = (symbol or "").strip().upper().split(".")[0]
    if not sym:
        return _empty(symbol)

    dw = get_warehouse()
    col = dw.get_collection("news_archive")
    if col is None:
        return _empty(sym)

    try:
        data = col.get(where={"symbol": sym},
                       include=["documents", "metadatas"]) or {}
    except Exception:
        # `where` filter unavailable; fall back to a full scan
        data = col.get(include=["documents", "metadatas"]) or {}

    docs = data.get("documents") or []
    metas = data.get("metadatas") or []
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, int(max_age_days)))

    rows: list[tuple[float, str, str, datetime | None]] = []
    for doc, meta in zip(docs, metas):
        m = meta or {}
        msym = str(m.get("symbol") or "").upper()
        if msym != sym:
            continue
        if "sentiment_score" not in m:
            continue
        pub = _parse_iso(str(m.get("published") or ""))
        if pub is not None and pub < cutoff:
            continue
        score = _to_float(m.get("sentiment_score"), 0.0)
        title = str(m.get("title") or (doc or "")[:120])
        rows.append((score, title, str(m.get("source") or ""), pub))

    if not rows:
        return _empty(sym)

    scores = [r[0] for r in rows]
    mean = sum(scores) / len(scores)
    n_pos = sum(1 for s in scores if s > 0.05)
    n_neg = sum(1 for s in scores if s < -0.05)
    n_neu = len(scores) - n_pos - n_neg

    top_pos = max(rows, key=lambda r: r[0])
    top_neg = min(rows, key=lambda r: r[0])
    dated = [r for r in rows if r[3] is not None]
    latest = max(dated, key=lambda r: r[3]) if dated else None

    return {
        "symbol": sym,
        "mean_score": round(mean, 4),
        "headline_count": len(rows),
        "positive_count": n_pos,
        "negative_count": n_neg,
        "neutral_count": n_neu,
        "most_positive": {"title": top_pos[1], "score": round(top_pos[0], 4),
                          "source": top_pos[2]},
        "most_negative": {"title": top_neg[1], "score": round(top_neg[0], 4),
                          "source": top_neg[2]},
        "latest_at": latest[3].isoformat() if latest else None,
    }


def sentiment_for_symbols(symbols: Iterable[str],
                          max_age_days: int = 14) -> dict[str, dict]:
    """Batch aggregate — one full news_archive scan, then bucket per symbol."""
    from data_warehouse import get_warehouse
    syms = {(s or "").strip().upper().split(".")[0] for s in symbols}
    syms.discard("")
    if not syms:
        return {}

    dw = get_warehouse()
    col = dw.get_collection("news_archive")
    if col is None:
        return {s: _empty(s) for s in syms}

    data = col.get(include=["documents", "metadatas"]) or {}
    docs = data.get("documents") or []
    metas = data.get("metadatas") or []
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, int(max_age_days)))

    buckets: dict[str, list] = {s: [] for s in syms}
    for doc, meta in zip(docs, metas):
        m = meta or {}
        msym = str(m.get("symbol") or "").upper()
        if msym not in buckets:
            continue
        if "sentiment_score" not in m:
            continue
        pub = _parse_iso(str(m.get("published") or ""))
        if pub is not None and pub < cutoff:
            continue
        buckets[msym].append((
            _to_float(m.get("sentiment_score"), 0.0),
            str(m.get("title") or (doc or "")[:120]),
            str(m.get("source") or ""),
            pub,
        ))

    out: dict[str, dict] = {}
    for s, rows in buckets.items():
        if not rows:
            out[s] = _empty(s)
            continue
        scores = [r[0] for r in rows]
        mean = sum(scores) / len(scores)
        n_pos = sum(1 for x in scores if x > 0.05)
        n_neg = sum(1 for x in scores if x < -0.05)
        top_pos = max(rows, key=lambda r: r[0])
        top_neg = min(rows, key=lambda r: r[0])
        dated = [r for r in rows if r[3] is not None]
        latest = max(dated, key=lambda r: r[3]) if dated else None
        out[s] = {
            "symbol": s,
            "mean_score": round(mean, 4),
            "headline_count": len(rows),
            "positive_count": n_pos,
            "negative_count": n_neg,
            "neutral_count": len(scores) - n_pos - n_neg,
            "most_positive": {"title": top_pos[1], "score": round(top_pos[0], 4),
                              "source": top_pos[2]},
            "most_negative": {"title": top_neg[1], "score": round(top_neg[0], 4),
                              "source": top_neg[2]},
            "latest_at": latest[3].isoformat() if latest else None,
        }
    return out
