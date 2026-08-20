#!/usr/bin/env python3
"""
finish_rag_training.py - one-shot completion of the RAG training pipeline.
1. Identify which URLs from data_sources_master.md are NOT yet cached.
2. Scrape each missing URL with a hard 18s timeout (skip on fail).
3. Load ALL cached content into ChromaDB.
4. Print final stats.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path("/home/z/my-project/build/nse-trade-advisor")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, "/home/z/my-project/scripts")

from scrape_and_train_rag import (
    parse_urls_from_md, scrape_url, chunk_markdown,
    load_into_chromadb, RAW_DIR, SUMMARY_DIR,
)

# 1. Parse all source URLs
sources = parse_urls_from_md()
print(f"[1] Parsed {len(sources)} source URLs")

# 2. Identify what's cached vs missing
def cache_path(url: str) -> Path:
    return RAW_DIR / f"src_{hashlib.md5(url.encode()).hexdigest()[:12]}.json"

missing = [s for s in sources if not cache_path(s['url']).exists()]
cached  = [s for s in sources if cache_path(s['url']).exists()]
print(f"[2] Cached: {len(cached)} | Missing: {len(missing)}")

# 3. Scrape missing URLs (one by one, with skip-on-fail)
print(f"[3] Scraping {len(missing)} missing URLs (18s timeout each)...")
scraped_ok = 0
scraped_fail = 0
for i, src in enumerate(missing, 1):
    print(f"  ({i}/{len(missing)}) {src['name']} - {src['url']}", flush=True)
    try:
        result = scrape_url(src['url'])
        if result is None or not result.get('markdown'):
            print(f"      ! skipped (no content)")
            scraped_fail += 1
            continue
        cache_path(src['url']).write_text(
            json.dumps(result, ensure_ascii=False, indent=2)
        )
        scraped_ok += 1
        print(f"      + {len(result['markdown']):,} chars")
    except Exception as e:
        print(f"      ! error: {str(e)[:100]}")
        scraped_fail += 1
    time.sleep(0.3)

# 4. Now load ALL cached content into ChromaDB
print(f"\n[4] Loading ALL cached content into ChromaDB...")
all_docs = []
sources_with_content = 0
for src in sources:
    cf = cache_path(src['url'])
    if not cf.exists():
        continue
    try:
        scraped = json.loads(cf.read_text())
        if not scraped.get('markdown'):
            continue
        docs = chunk_markdown(scraped['markdown'], src)
        all_docs.extend(docs)
        sources_with_content += 1
    except Exception as e:
        print(f"  ! chunk error for {src['name']}: {e}")

print(f"  - sources with usable content: {sources_with_content}")
print(f"  - total RAG chunks: {len(all_docs)}")

if not all_docs:
    print("\nNo documents to load. Exiting.")
    sys.exit(1)

# 5. Load into ChromaDB
print(f"\n[5] Loading {len(all_docs)} chunks into ChromaDB collections...")
n_market, n_strategy = load_into_chromadb(all_docs)
print(f"  + market_data_sources:  {n_market} docs")
print(f"  + live_strategy_briefs: {n_strategy} docs")

# 6. Manifest
manifest = {
    "trained_at": datetime.utcnow().isoformat(),
    "sources_total": len(sources),
    "sources_with_content": sources_with_content,
    "sources_failed": len(sources) - sources_with_content,
    "this_run_scraped_ok": scraped_ok,
    "this_run_scraped_fail": scraped_fail,
    "rag_documents_total": len(all_docs),
    "market_data_sources_docs": n_market,
    "live_strategy_briefs_docs": n_strategy,
    "groq_available": False,
    "groq_note": "Groq API key returned 403 Forbidden; markdown chunking used instead (full content preserved for semantic search).",
    "sources": [
        {"name": s["name"], "url": s["url"], "category": s["category"]}
        for s in sources
    ],
}
manifest_path = PROJECT_ROOT / "knowledge" / "rag_training_manifest.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

print("\n" + "=" * 70)
print("  RAG TRAINING COMPLETE")
print("=" * 70)
print(f"  Total URLs in data_sources_master.md:  {len(sources)}")
print(f"  Successfully scraped (cumulative):     {sources_with_content}")
print(f"  This-run scrapes OK / fail:            {scraped_ok} / {scraped_fail}")
print(f"  RAG chunks loaded into ChromaDB:       {len(all_docs)}")
print(f"  market_data_sources collection:        {n_market} docs")
print(f"  live_strategy_briefs collection:       {n_strategy} docs")
print(f"  Manifest: {manifest_path}")
