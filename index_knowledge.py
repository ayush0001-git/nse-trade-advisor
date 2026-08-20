"""
index_knowledge.py - Index all knowledge/ markdown files into ChromaDB.

Reads every .md and .json file in the knowledge/ directory, splits into
chunks (by section), and stores in the investor_wisdom collection with
metadata about the source file and section.

Usage:
    python index_knowledge.py           # index all files
    python index_knowledge.py --stats   # show current DB stats
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_warehouse import get_warehouse

KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"


def chunk_markdown(text: str, source: str) -> list[dict]:
    """Split a markdown file into chunks by ## sections.

    Each chunk becomes one document in the vector DB, with metadata
    about which section it came from.
    """
    chunks = []
    # Split by ## headers (keep the header with the content)
    sections = re.split(r'(?=^## )', text, flags=re.MULTILINE)
    for i, section in enumerate(sections):
        section = section.strip()
        if not section or len(section) < 50:
            continue
        # Extract section title (first ## line)
        title_match = re.match(r'^## (.+)$', section, re.MULTILINE)
        section_title = title_match.group(1) if title_match else f"section_{i}"
        chunks.append({
            "text": section,
            "metadata": {
                "source": source,
                "section": section_title,
                "type": "knowledge_file",
                "chunk_index": i,
            },
        })
    return chunks


def index_all_files():
    """Read all knowledge files and index them into ChromaDB."""
    dw = get_warehouse()
    col = dw.get_collection("investor_wisdom")

    if not KNOWLEDGE_DIR.exists():
        print(f"Knowledge directory not found: {KNOWLEDGE_DIR}")
        return 0

    files = sorted(KNOWLEDGE_DIR.glob("*.md")) + sorted(KNOWLEDGE_DIR.glob("*.json"))
    print(f"Found {len(files)} knowledge files to index")

    all_documents = []
    all_metadatas = []
    all_ids = []

    for filepath in files:
        print(f"  Indexing: {filepath.name}")
        text = filepath.read_text(encoding="utf-8")

        if filepath.suffix == ".json":
            # For JSON files, store the entire content as one document
            try:
                data = json.loads(text)
                # Store as a formatted string
                doc_text = json.dumps(data, indent=2)
                all_documents.append(doc_text[:5000])  # cap at 5000 chars
                all_metadatas.append({
                    "source": filepath.name,
                    "type": "json_data",
                    "section": "full_file",
                })
                all_ids.append(f"knowledge_json_{filepath.stem}")
            except json.JSONDecodeError:
                # Not valid JSON, treat as text
                chunks = chunk_markdown(text, filepath.name)
                for chunk in chunks:
                    all_documents.append(chunk["text"])
                    all_metadatas.append(chunk["metadata"])
                    all_ids.append(f"knowledge_{filepath.stem}_{chunk['metadata']['chunk_index']}")
        else:
            # Markdown files — chunk by section
            chunks = chunk_markdown(text, filepath.name)
            for chunk in chunks:
                all_documents.append(chunk["text"])
                all_metadatas.append(chunk["metadata"])
                all_ids.append(f"knowledge_{filepath.stem}_{chunk['metadata']['chunk_index']}")

    # Clear old knowledge entries (keep investor texts)
    try:
        # Delete by source filter
        col.delete(where={"type": {"$in": ["knowledge_file", "json_data"]}})
    except Exception:
        pass

    # Add new entries
    if all_documents:
        col.add(documents=all_documents, metadatas=all_metadatas, ids=all_ids)

    print(f"\n✅ Indexed {len(all_documents)} chunks from {len(files)} files")
    return len(all_documents)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Index knowledge files into ChromaDB")
    ap.add_argument("--stats", action="store_true", help="Show current stats")
    args = ap.parse_args()

    if args.stats:
        dw = get_warehouse()
        print("\n📊 Data Warehouse Stats:")
        print("-" * 50)
        for col, count in dw.stats().items():
            print(f"  {col:<25} {count:>6} documents")
    else:
        n = index_all_files()
        print(f"\nFinal count: {n} documents indexed")
        # Show updated stats
        dw = get_warehouse()
        print("\n📊 Updated Stats:")
        for col, count in dw.stats().items():
            print(f"  {col:<25} {count:>6} documents")
