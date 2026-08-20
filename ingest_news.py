"""
ingest_news.py - Populate the ChromaDB `news_archive` collection with fresh
Indian-market headlines from free RSS feeds. Stdlib-only fetch + parse.

Usage:
    python ingest_news.py               # ingest up to 200 items (default)
    python ingest_news.py --limit 20    # cap items per run
    python ingest_news.py --stats       # count + last 5 headlines
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_warehouse import get_warehouse  # noqa: E402

FEEDS = [
    ("moneycontrol",      "https://www.moneycontrol.com/rss/marketreports.xml"),
    ("business-standard", "https://www.business-standard.com/rss/markets-106.rss"),
    ("livemint",          "https://www.livemint.com/rss/markets"),
]
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 (nse-trade-advisor)")
REQUEST_TIMEOUT = 15
ATOM = "{http://www.w3.org/2005/Atom}"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE  = re.compile(r"\s+")


# --------------------------------------------------------------------------- #
def load_watchlist() -> list[str]:
    """Bare symbols from config.yaml (no .NS/.BO suffix)."""
    cfg = PROJECT_ROOT / "config.yaml"
    if not cfg.exists():
        return []
    try:
        import yaml
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        return sorted({str(s).split(".")[0].upper()
                       for s in (data.get("watchlist") or []) if s})
    except Exception as e:
        print(f"  ! watchlist load failed: {e}")
        return []


def build_symbol_matcher(symbols: Iterable[str]) -> re.Pattern | None:
    syms = [re.escape(s) for s in sorted(set(symbols), key=len, reverse=True) if s]
    return re.compile(r"\b(" + "|".join(syms) + r")\b", re.IGNORECASE) if syms else None


def detect_symbol(text: str, matcher: re.Pattern | None) -> str | None:
    if not matcher or not text:
        return None
    m = matcher.search(text)
    return m.group(1).upper() if m else None


# --------------------------------------------------------------------------- #
def fetch_feed(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
            return r.read()
    except Exception as e:
        print(f"  ! fetch failed [{url}]: {e}")
        return None


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&quot;", '"'),
                 ("&#39;", "'"), ("&lt;", "<"), ("&gt;", ">")):
        text = text.replace(a, b)
    return _WS_RE.sub(" ", text).strip()


def _parse_pubdate(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return raw


def parse_rss(xml_bytes: bytes, source: str) -> list[dict]:
    """Parse RSS 2.0 or Atom into a list of {title, link, summary, published, source}."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"  ! parse failed [{source}]: {e}")
        return []

    items: list[dict] = []
    for item in root.iter("item"):  # RSS 2.0
        items.append({
            "title":     _clean(item.findtext("title")),
            "link":      _clean(item.findtext("link")),
            "summary":   _clean(item.findtext("description")),
            "published": _parse_pubdate(item.findtext("pubDate") or ""),
            "source":    source,
        })
    if not items:
        for entry in root.iter(f"{ATOM}entry"):  # Atom
            link_el = entry.find(f"{ATOM}link")
            link = link_el.get("href") if link_el is not None else ""
            summary_el = (entry.find(f"{ATOM}summary")
                          or entry.find(f"{ATOM}content"))
            items.append({
                "title":     _clean(entry.findtext(f"{ATOM}title")),
                "link":      _clean(link),
                "summary":   _clean(summary_el.text if summary_el is not None else ""),
                "published": _parse_pubdate(entry.findtext(f"{ATOM}updated")
                                            or entry.findtext(f"{ATOM}published") or ""),
                "source":    source,
            })
    return [it for it in items if it["title"] or it["link"]]


# --------------------------------------------------------------------------- #
def _doc_id(link: str, title: str) -> str:
    key = (link or title or "").strip().lower()
    return "news_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:20]


def _existing_ids(collection) -> set[str]:
    try:
        return set((collection.get(include=[]) or {}).get("ids") or [])
    except Exception as e:
        print(f"  ! could not read existing ids: {e}")
        return set()


def run(limit: int = 200) -> dict:
    """Fetch feeds, dedupe by URL, add fresh items to news_archive."""
    print(f"[ingest_news] Starting run (limit={limit})")
    dw = get_warehouse()
    col = dw.get_collection("news_archive")
    if col is None:
        raise RuntimeError("news_archive collection is not available")

    matcher = build_symbol_matcher(load_watchlist())
    already = _existing_ids(col)
    failed: list[dict] = []
    fetched: list[dict] = []

    for source, url in FEEDS:
        raw = fetch_feed(url)
        if not raw:
            failed.append({"source": source, "url": url, "reason": "fetch failed"})
            continue
        items = parse_rss(raw, source)
        if not items:
            failed.append({"source": source, "url": url, "reason": "no items / not XML"})
            continue
        print(f"  {source}: {len(items)} items")
        fetched.extend(items)

    # Dedupe within this batch by URL (or title if no URL).
    seen: set[str] = set()
    unique = []
    for it in fetched:
        k = (it["link"] or it["title"]).strip().lower()
        if k and k not in seen:
            seen.add(k)
            unique.append(it)
    unique = unique[: max(1, int(limit))]

    docs, metas, ids = [], [], []
    skipped = 0
    for it in unique:
        did = _doc_id(it["link"], it["title"])
        if did in already or did in ids:
            skipped += 1
            continue
        body = ((it["title"] + "\n\n" + it["summary"]).strip())[:2000]
        if not body:
            continue
        sym = detect_symbol(it["title"] + " " + it["summary"], matcher)
        docs.append(body)
        metas.append({
            "source": it["source"], "link": it["link"] or "",
            "title": it["title"][:300], "published": it["published"] or "",
            "symbol": sym or "",  # Chroma metadata can't hold None
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })
        ids.append(did)

    if docs:
        col.add(documents=docs, metadatas=metas, ids=ids)

    summary = {
        "added": len(docs), "skipped_dup": skipped,
        "total_in_batch": len(unique), "failed_feeds": failed,
        "total_after": col.count(),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    print(f"[ingest_news] Added {summary['added']}, skipped {skipped} dupes, "
          f"news_archive now has {summary['total_after']} docs")
    for f in failed:
        print(f"  ! feed failed: {f['source']} ({f['reason']})")
    return summary


# --------------------------------------------------------------------------- #
def get_stats(n_recent: int = 5) -> dict:
    dw = get_warehouse()
    col = dw.get_collection("news_archive")
    if col is None:
        return {"count": 0, "recent": []}
    count = col.count()
    recent: list[dict] = []
    if count > 0:
        try:
            metas = (col.get(include=["metadatas"]) or {}).get("metadatas") or []
            metas.sort(key=lambda m: str(m.get("ingested_at")
                                         or m.get("published") or ""),
                       reverse=True)
            for m in metas[:n_recent]:
                recent.append({
                    "title":     m.get("title", ""),
                    "source":    m.get("source", ""),
                    "link":      m.get("link", ""),
                    "published": m.get("published", ""),
                    "symbol":    (m.get("symbol") or None),
                })
        except Exception as e:
            print(f"  ! could not read metadatas: {e}")
    return {"count": count, "recent": recent}


# --------------------------------------------------------------------------- #
def _print_stats(stats: dict) -> None:
    print(f"\nnews_archive count: {stats['count']}")
    print("Recent 5 headlines:")
    if not stats["recent"]:
        print("  (none)")
        return
    for i, item in enumerate(stats["recent"], 1):
        sym = f"[{item['symbol']}] " if item["symbol"] else ""
        print(f"  {i}. {sym}{item['title']}  ({item['source']})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest fresh news into ChromaDB")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    if args.stats:
        _print_stats(get_stats(5))
        return 0

    t0 = time.time()
    run(limit=args.limit)
    print(f"[ingest_news] Done in {time.time() - t0:.1f}s")
    _print_stats(get_stats(5))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
