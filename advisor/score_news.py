"""
advisor/score_news.py - Score every news_archive doc with FinBERT and
write the sentiment back into its metadata.

CLI:
    python advisor/score_news.py score            # score unscored docs (batched)
    python advisor/score_news.py score --limit 32 # cap items per run
    python advisor/score_news.py stats            # counts + per-source means

Idempotent: only items whose metadata lacks a numeric 'sentiment_score'
are (re)scored.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

BATCH_SIZE = 32


def _fetch_all():
    from data_warehouse import get_warehouse
    dw = get_warehouse()
    col = dw.get_collection("news_archive")
    if col is None:
        return None, None, None
    data = col.get(include=["documents", "metadatas"]) or {}
    ids = data.get("ids") or []
    docs = data.get("documents") or []
    metas = data.get("metadatas") or []
    return col, list(zip(ids, docs, metas)), dw


def _needs_score(meta: dict) -> bool:
    v = meta.get("sentiment_score") if meta else None
    try:
        float(v)  # any numeric value counts as already scored
        return False
    except (TypeError, ValueError):
        return True


# --------------------------------------------------------------------------- #
def score_all(limit: Optional[int] = None) -> dict:
    """Score every unscored news_archive document; write back via col.update."""
    from advisor.sentiment import get_scorer
    col, rows, _ = _fetch_all()
    if col is None:
        return {"error": "news_archive collection unavailable", "scored": 0}

    todo = [(i, d, m or {}) for i, d, m in rows if _needs_score(m or {})]
    total_present = len(rows)
    total_todo = len(todo)
    if limit is not None and limit > 0:
        todo = todo[:limit]
    print(f"[score_news] news_archive has {total_present} docs; "
          f"{total_todo} need scoring; running {len(todo)}")

    if not todo:
        return {"scored": 0, "total": total_present, "already_scored": total_present}

    scorer = get_scorer()
    written = 0
    t0 = time.time()
    for start in range(0, len(todo), BATCH_SIZE):
        batch = todo[start:start + BATCH_SIZE]
        texts = [d or "" for _, d, _ in batch]
        results = scorer.score_batch(texts)

        ids_out, metas_out = [], []
        for (doc_id, _doc, meta), r in zip(batch, results):
            new_meta = dict(meta)
            new_meta["sentiment_label"] = r.get("label", "neutral")
            new_meta["sentiment_score"] = float(r.get("score", 0.0))
            new_meta["sentiment_conf"]  = float(r.get("confidence", 0.0))
            new_meta["sentiment_model"] = "finbert"
            if r.get("error"):
                new_meta["sentiment_error"] = str(r["error"])[:200]
            ids_out.append(doc_id)
            metas_out.append(new_meta)

        try:
            col.update(ids=ids_out, metadatas=metas_out)
            written += len(ids_out)
            print(f"  batch {start // BATCH_SIZE + 1}: "
                  f"scored {len(ids_out)} (running total {written})")
        except Exception as e:
            print(f"  ! update failed on batch {start}: {e}")

    dt = time.time() - t0
    print(f"[score_news] Wrote sentiment for {written} docs in {dt:.1f}s "
          f"({written / dt:.1f}/s)" if dt > 0 else f"[score_news] Wrote {written}")
    return {"scored": written, "total": total_present, "elapsed_s": round(dt, 2)}


# --------------------------------------------------------------------------- #
def print_stats() -> dict:
    """Print totals, per-source mean sentiment, top/bottom symbols."""
    col, rows, _ = _fetch_all()
    if col is None:
        print("news_archive collection unavailable")
        return {}

    total = len(rows)
    scored_rows = [(i, d, m) for i, d, m in rows if not _needs_score(m or {})]
    scored = len(scored_rows)
    unscored = total - scored

    src_scores: dict[str, list[float]] = defaultdict(list)
    sym_scores: dict[str, list[float]] = defaultdict(list)
    for _i, _d, m in scored_rows:
        m = m or {}
        try:
            s = float(m.get("sentiment_score", 0.0))
        except (TypeError, ValueError):
            continue
        src_scores[str(m.get("source") or "?")].append(s)
        sym = str(m.get("symbol") or "").strip()
        if sym:
            sym_scores[sym].append(s)

    print(f"news_archive: total={total}  scored={scored}  unscored={unscored}")
    print("\nMean sentiment by source:")
    if not src_scores:
        print("  (none scored yet)")
    for src, arr in sorted(src_scores.items()):
        mean = sum(arr) / len(arr)
        print(f"  {src:<20} n={len(arr):>3}  mean={mean:+.3f}")

    sym_means = [(s, sum(v) / len(v), len(v)) for s, v in sym_scores.items()]
    sym_means.sort(key=lambda x: x[1], reverse=True)
    print("\nTop 5 most-positive symbols:")
    for s, m, n in sym_means[:5]:
        print(f"  {s:<15} mean={m:+.3f}  headlines={n}")
    print("\nTop 5 most-negative symbols:")
    for s, m, n in sym_means[-5:][::-1]:
        print(f"  {s:<15} mean={m:+.3f}  headlines={n}")

    return {"total": total, "scored": scored, "unscored": unscored,
            "by_source": {k: sum(v) / len(v) for k, v in src_scores.items()}}


# --------------------------------------------------------------------------- #
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Score news_archive with FinBERT")
    ap.add_argument("cmd", choices=("score", "stats"))
    ap.add_argument("--limit", type=int, default=None, help="Cap items per run.")
    args = ap.parse_args(argv)

    if args.cmd == "score":
        score_all(limit=args.limit)
    else:
        print_stats()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
