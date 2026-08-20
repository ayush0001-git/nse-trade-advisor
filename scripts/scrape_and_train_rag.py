#!/usr/bin/env python3
"""
scrape_and_train_rag.py
=======================
Visits every URL in knowledge/data_sources_master.md, extracts their content
via Firecrawl, chunks it, and loads the resulting knowledge into ChromaDB.

If Groq is available, also runs structured extraction for richer rules.
Otherwise, falls back to direct markdown chunking (better for full-text RAG).

Creates two new collections in the warehouse:
  - market_data_sources     : structured facts + raw chunks
  - live_strategy_briefs    : Groq-extracted rules + strategies (if available)

Usage:
    python scrape_and_train_rag.py            # full run
    python scrape_and_train_rag.py --limit 5  # only first 5 sources (test run)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# --- project paths ---------------------------------------------------------
PROJECT_ROOT = Path("/home/z/my-project/build/nse-trade-advisor")
sys.path.insert(0, str(PROJECT_ROOT))

DATA_SOURCES_MD = PROJECT_ROOT / "knowledge" / "data_sources_master.md"
RAW_DIR         = PROJECT_ROOT / "knowledge" / "scraped_raw"
SUMMARY_DIR     = PROJECT_ROOT / "knowledge" / "scraped_summaries"
RAW_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

# --- API keys (user-provided) ---------------------------------------------
FIRECRAWL_API_KEY = os.environ.get(
    "FIRECRAWL_API_KEY",
    "os.environ.get('FIRECRAWL_API_KEY')",
)
GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY",
    "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",
)

# --- clients (lazy import) -------------------------------------------------
_firecrawl = None
_groq = None
_groq_available: bool | None = None

def get_firecrawl():
    global _firecrawl
    if _firecrawl is None:
        from firecrawl import V1FirecrawlApp
        _firecrawl = V1FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    return _firecrawl

def get_groq():
    global _groq, _groq_available
    if _groq is None and _groq_available is None:
        try:
            from groq import Groq
            _groq = Groq(api_key=GROQ_API_KEY)
            # test the key
            _groq.models.list()
            _groq_available = True
        except Exception as e:
            print(f"  ! Groq unavailable ({e}); using markdown chunking only")
            _groq_available = False
    return _groq if _groq_available else None


# =========================================================================== #
#  1. PARSE URL LIST FROM data_sources_master.md
# =========================================================================== #

URL_REGEX = re.compile(r"https?://[^\s|)]+")

def parse_urls_from_md() -> list[dict]:
    """Parse all (source_name, url, category) tuples from the markdown."""
    sources: list[dict] = []
    current_category = "Uncategorized"

    for line in DATA_SOURCES_MD.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        if line.startswith("## "):
            current_category = line.lstrip("# ").strip()
            continue
        # table row: | Source | URL | What it provides |
        if line.startswith("|") and "http" in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3:
                name = cells[0]
                urls = URL_REGEX.findall(cells[1])
                provides = cells[2]
                for u in urls:
                    if "[TICKER]" in u or "[" in u:
                        continue
                    sources.append({
                        "category": current_category,
                        "name": name,
                        "url": u.rstrip(".,;)"),
                        "provides": provides,
                    })
    return sources


# =========================================================================== #
#  2. FIRECRAWL SCRAPE
# =========================================================================== #

def scrape_url(url: str) -> dict | None:
    """Scrape a single URL with Firecrawl. Returns {markdown, title, url} or None."""
    try:
        fc = get_firecrawl()
        result = fc.scrape_url(
            url,
            formats=["markdown"],
            only_main_content=True,
            wait_for=1000,
            timeout=15000,
        )
        data = getattr(result, "data", None) or result
        markdown = getattr(data, "markdown", None) or (data.get("markdown") if isinstance(data, dict) else "") or ""
        title = getattr(data, "title", None) or (data.get("title") if isinstance(data, dict) else "") or url
        if not markdown or len(markdown.strip()) < 100:
            return None
        return {
            "markdown": markdown,
            "title": title,
            "url": url,
        }
    except Exception as e:
        print(f"    ! firecrawl error for {url}: {e}")
        return None


# =========================================================================== #
#  3. GROQ SUMMARIZATION + RULE EXTRACTION  (optional)
# =========================================================================== #

GROQ_PROMPT = """You are an expert trading knowledge extractor. Below is raw
scraped content from a financial data source. Extract the highest-signal
actionable knowledge a trading bot can use.

SOURCE NAME: {name}
SOURCE URL:  {url}
CATEGORY:    {category}
PROVIDES:    {provides}

RAW CONTENT (first 12000 chars):
---
{content}
---

Produce a strict JSON object with EXACTLY these keys (no other keys, no prose):
{{
  "summary": "2-4 sentence summary of what this source offers",
  "key_facts": ["3-8 concrete facts/data points discovered"],
  "actionable_rules": ["3-8 specific rules a trading bot can encode, e.g. 'Buy when VIX > 30 then mean-revert'"],
  "data_endpoints": ["3-8 specific API endpoints or URL patterns mentioned (with example URLs if any)"],
  "indicators": ["3-8 indicators/metrics/ratios mentioned (RSI, MACD, put/call ratio, etc.)"],
  "strategies": ["3-8 named strategies or playbooks described"],
  "risks": ["1-5 risks/caveats mentioned"]
}}

Respond with ONLY the JSON object, no markdown fences, no commentary.
"""

def extract_with_groq(source: dict, raw_content: str) -> dict | None:
    """Send raw content to Groq Llama-3.3-70B and parse the structured JSON."""
    groq = get_groq()
    if groq is None:
        return None
    try:
        prompt = GROQ_PROMPT.format(
            name=source["name"],
            url=source["url"],
            category=source["category"],
            provides=source["provides"],
            content=raw_content[:12000],
        )
        resp = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1800,
            response_format={"type": "json_object"},
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except Exception as e:
        print(f"    ! groq error: {e}")
        return None


# =========================================================================== #
#  4. CHUNK FOR RAG (ChromaDB)
# =========================================================================== #

def chunk_markdown(text: str, source: dict, max_chunk: int = 1200) -> list[dict]:
    """Split markdown into RAG-friendly chunks by headers and paragraphs."""
    docs: list[dict] = []
    base_meta = {
        "source_name": source["name"],
        "source_url": source["url"],
        "category": source["category"],
        "scraped_at": datetime.utcnow().isoformat(),
    }

    # split on markdown headers
    sections = re.split(r"\n(?=#{1,4}\s)", text)
    section_idx = 0
    for section in sections:
        section = section.strip()
        if not section or len(section) < 60:
            continue
        # extract header for context
        header_match = re.match(r"^(#{1,4}\s+.+?)$", section, re.MULTILINE)
        header = header_match.group(1) if header_match else "General"

        # further split very long sections by paragraphs
        paragraphs = re.split(r"\n\n+", section)
        current_chunk = ""
        para_idx = 0
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if len(current_chunk) + len(p) + 2 > max_chunk and current_chunk:
                # flush
                docs.append({
                    "id": f"raw_{hashlib.md5(source['url'].encode()).hexdigest()[:10]}_{section_idx}_{para_idx}",
                    "text": (
                        f"SOURCE: {source['name']} ({source['category']})\n"
                        f"SECTION: {header}\n"
                        f"URL: {source['url']}\n\n"
                        f"{current_chunk}"
                    ),
                    "metadata": {**base_meta, "chunk_type": "raw_section",
                                 "section": header[:80]},
                })
                current_chunk = p
                para_idx += 1
            else:
                current_chunk = (current_chunk + "\n\n" + p).strip()
        if current_chunk:
            docs.append({
                "id": f"raw_{hashlib.md5(source['url'].encode()).hexdigest()[:10]}_{section_idx}_final",
                "text": (
                    f"SOURCE: {source['name']} ({source['category']})\n"
                    f"SECTION: {header}\n"
                    f"URL: {source['url']}\n\n"
                    f"{current_chunk}"
                ),
                "metadata": {**base_meta, "chunk_type": "raw_section",
                             "section": header[:80]},
            })
        section_idx += 1

    return docs


def groq_chunks(source: dict, extracted: dict) -> list[dict]:
    """Convert the Groq-extracted JSON into multiple RAG documents."""
    base_meta = {
        "source_name": source["name"],
        "source_url": source["url"],
        "category": source["category"],
        "scraped_at": datetime.utcnow().isoformat(),
    }
    docs: list[dict] = []
    url_hash = hashlib.md5(source["url"].encode()).hexdigest()[:10]

    # summary
    docs.append({
        "id": f"groq_sum_{url_hash}",
        "text": (
            f"SOURCE SUMMARY: {source['name']} ({source['category']})\n"
            f"URL: {source['url']}\n"
            f"SUMMARY: {extracted.get('summary', '')}\n"
            f"PROVIDES: {source['provides']}\n"
        ),
        "metadata": {**base_meta, "chunk_type": "summary"},
    })
    # rules
    for i, rule in enumerate(extracted.get("actionable_rules", [])):
        docs.append({
            "id": f"groq_rule_{url_hash}_{i}",
            "text": (
                f"TRADING RULE from {source['name']} ({source['category']}):\n"
                f"  {rule}\nSource: {source['url']}"
            ),
            "metadata": {**base_meta, "chunk_type": "rule"},
        })
    # strategies
    for i, strat in enumerate(extracted.get("strategies", [])):
        docs.append({
            "id": f"groq_strat_{url_hash}_{i}",
            "text": (
                f"STRATEGY from {source['name']} ({source['category']}):\n"
                f"  {strat}\nSource: {source['url']}"
            ),
            "metadata": {**base_meta, "chunk_type": "strategy"},
        })
    # endpoints
    for i, ep in enumerate(extracted.get("data_endpoints", [])):
        docs.append({
            "id": f"groq_ep_{url_hash}_{i}",
            "text": (
                f"DATA ENDPOINT from {source['name']}:\n  {ep}\n"
                f"Category: {source['category']}\nSource: {source['url']}"
            ),
            "metadata": {**base_meta, "chunk_type": "endpoint"},
        })
    # indicators
    for i, ind in enumerate(extracted.get("indicators", [])):
        docs.append({
            "id": f"groq_ind_{url_hash}_{i}",
            "text": f"INDICATOR from {source['name']}:\n  {ind}\nCategory: {source['category']}",
            "metadata": {**base_meta, "chunk_type": "indicator"},
        })
    # facts
    for i, fact in enumerate(extracted.get("key_facts", [])):
        docs.append({
            "id": f"groq_fact_{url_hash}_{i}",
            "text": f"FACT from {source['name']} ({source['category']}):\n  {fact}",
            "metadata": {**base_meta, "chunk_type": "fact"},
        })
    # risks
    for i, risk in enumerate(extracted.get("risks", [])):
        docs.append({
            "id": f"groq_risk_{url_hash}_{i}",
            "text": f"RISK from {source['name']} ({source['category']}):\n  {risk}",
            "metadata": {**base_meta, "chunk_type": "risk"},
        })
    return docs


# =========================================================================== #
#  5. LOAD INTO CHROMADB
# =========================================================================== #

def load_into_chromadb(all_docs: list[dict]) -> tuple[int, int]:
    """Add all docs to two new collections. Returns (n_market, n_strategy)."""
    import chromadb
    db_path = PROJECT_ROOT / "rl_models" / "chromadb"
    db_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db_path))

    market_col = client.get_or_create_collection(
        name="market_data_sources",
        metadata={"hnsw:space": "cosine"},
    )
    strategy_col = client.get_or_create_collection(
        name="live_strategy_briefs",
        metadata={"hnsw:space": "cosine"},
    )

    # market_data_sources: raw sections, endpoints, indicators, facts, summaries
    market_types = {"raw_section", "endpoint", "indicator", "fact", "summary"}
    # live_strategy_briefs: rules, strategies, risks
    strategy_types = {"rule", "strategy", "risk"}

    market_docs = [d for d in all_docs if d["metadata"]["chunk_type"] in market_types]
    strategy_docs = [d for d in all_docs if d["metadata"]["chunk_type"] in strategy_types]

    def batch_add(col, docs):
        added = 0
        for i in range(0, len(docs), 50):
            batch = docs[i:i+50]
            try:
                col.add(
                    documents=[d["text"] for d in batch],
                    metadatas=[d["metadata"] for d in batch],
                    ids=[d["id"] for d in batch],
                )
                added += len(batch)
            except Exception:
                # likely duplicate ids; try one-by-one with timestamp suffix
                ts = int(time.time()*1000)
                for j, d in enumerate(batch):
                    try:
                        col.add(
                            documents=[d["text"]],
                            metadatas=[d["metadata"]],
                            ids=[d["id"] + f"_{ts}_{j}"],
                        )
                        added += 1
                    except Exception:
                        pass
        return added

    n_market = batch_add(market_col, market_docs)
    n_strategy = batch_add(strategy_col, strategy_docs)
    return n_market, n_strategy


# =========================================================================== #
#  6. MAIN PIPELINE
# =========================================================================== #

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="limit N sources (0 = all)")
    args = parser.parse_args()

    print("=" * 70)
    print("  RAG TRAINING PIPELINE — Firecrawl (+ Groq if available) + ChromaDB")
    print("=" * 70)

    # Pre-check Groq
    print("\n[0/5] Pre-checking Groq API...")
    get_groq()
    print(f"      Groq available: {_groq_available}")

    # Step 1: parse URLs
    sources = parse_urls_from_md()
    print(f"\n[1/5] Parsed {len(sources)} data source URLs from data_sources_master.md")
    for s in sources[:5]:
        print(f"      - {s['name']}: {s['url']}")
    print(f"      ... ({len(sources)} total)")

    if args.limit > 0:
        sources = sources[:args.limit]
        print(f"      [limited to first {args.limit}]")

    # Step 2: scrape each URL
    print(f"\n[2/5] Scraping {len(sources)} URLs with Firecrawl...")
    all_docs: list[dict] = []
    ok = 0
    fail = 0
    groq_ok = 0
    groq_fail = 0

    for i, src in enumerate(sources, 1):
        print(f"\n  ({i}/{len(sources)}) {src['name']} — {src['url']}")
        if "[" in src["url"]:
            print("    - skipping template URL")
            continue

        # check cache
        cache_file = RAW_DIR / f"src_{hashlib.md5(src['url'].encode()).hexdigest()[:12]}.json"
        if cache_file.exists():
            print("    - using cached scrape")
            scraped = json.loads(cache_file.read_text())
        else:
            scraped = scrape_url(src["url"])
            if scraped is None or not scraped.get("markdown"):
                fail += 1
                continue
            cache_file.write_text(json.dumps(scraped, ensure_ascii=False, indent=2))
            time.sleep(0.5)  # be polite to Firecrawl
        ok += 1
        print(f"    + scraped {len(scraped['markdown']):,} chars")

        # Step 3: extract with Groq (if available)
        summary_cache = SUMMARY_DIR / f"src_{hashlib.md5(src['url'].encode()).hexdigest()[:12]}.json"
        extracted = None
        if _groq_available:
            if summary_cache.exists():
                print("    - using cached Groq extraction")
                extracted = json.loads(summary_cache.read_text())
                groq_ok += 1
            else:
                print("    - sending to Groq Llama-3.3-70B...")
                extracted = extract_with_groq(src, scraped["markdown"])
                if extracted:
                    summary_cache.write_text(json.dumps(extracted, ensure_ascii=False, indent=2))
                    groq_ok += 1
                else:
                    groq_fail += 1

        # Step 4a: chunk raw markdown for full-text RAG
        docs = chunk_markdown(scraped["markdown"], src)
        all_docs.extend(docs)
        print(f"    + {len(docs)} raw markdown chunks")

        # Step 4b: chunk Groq extraction if available
        if extracted:
            groq_docs = groq_chunks(src, extracted)
            all_docs.extend(groq_docs)
            print(f"    + {len(groq_docs)} Groq-extracted chunks")

    print(f"\n  Scraped OK: {ok} | Failed: {fail}")
    if _groq_available:
        print(f"  Groq OK: {groq_ok} | Groq failed: {groq_fail}")
    print(f"  Total RAG documents ready: {len(all_docs)}")

    if not all_docs:
        print("\nNo documents to load. Exiting.")
        return

    # Step 5: load into ChromaDB
    print(f"\n[5/5] Loading {len(all_docs)} docs into ChromaDB...")
    n_market, n_strategy = load_into_chromadb(all_docs)
    print(f"  + market_data_sources collection: {n_market} docs")
    print(f"  + live_strategy_briefs collection: {n_strategy} docs")

    # Final report
    print("\n" + "=" * 70)
    print("  RAG TRAINING COMPLETE")
    print("=" * 70)
    print(f"  Sources scraped:    {ok}")
    print(f"  Sources failed:     {fail}")
    print(f"  Groq extractions:   {groq_ok if _groq_available else 'n/a (key invalid)'}")
    print(f"  RAG chunks created: {len(all_docs)}")
    print(f"  ChromaDB collections updated:")
    print(f"    - market_data_sources:  {n_market} docs")
    print(f"    - live_strategy_briefs: {n_strategy} docs")
    print(f"  Raw scrapes cached at:  {RAW_DIR}")
    print(f"  Summaries cached at:    {SUMMARY_DIR}")

    # write a manifest the bot can read at startup
    manifest = {
        "trained_at": datetime.utcnow().isoformat(),
        "sources_attempted": len(sources),
        "sources_ok": ok,
        "sources_failed": fail,
        "groq_available": _groq_available,
        "groq_ok": groq_ok if _groq_available else 0,
        "rag_documents_total": len(all_docs),
        "market_data_sources_docs": n_market,
        "live_strategy_briefs_docs": n_strategy,
        "sources": [
            {"name": s["name"], "url": s["url"], "category": s["category"]}
            for s in sources
        ],
    }
    manifest_path = PROJECT_ROOT / "knowledge" / "rag_training_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"  Manifest written to:   {manifest_path}")


if __name__ == "__main__":
    main()
