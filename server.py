"""
server.py — Single backend file. Serves the frontend and API.

Run:  python server.py
Open: http://localhost:5000
"""
from __future__ import annotations

import json
import os
import sys
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import brain

app = Flask(__name__, static_folder=".", static_url_path="")
app.config["SECRET_KEY"] = "advisor-local"

JOURNAL_DB = str(PROJECT_ROOT / "trade_journal.db")


# =========================================================================== #
#  DATABASE
# =========================================================================== #
def init_db():
    with closing(sqlite3.connect(JOURNAL_DB)) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL, direction TEXT, entry REAL,
                stop REAL, target REAL, quantity INTEGER, score INTEGER,
                rating TEXT, opened_at TEXT, status TEXT DEFAULT 'open',
                exit_price REAL, exit_at TEXT, pnl REAL, notes TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL, scan_date TEXT NOT NULL, verdict TEXT,
                direction TEXT, score INTEGER, entry REAL, stop REAL,
                target REAL, quantity INTEGER, reasons TEXT,
                UNIQUE(symbol, scan_date)
            )
        """)
        c.commit()


# =========================================================================== #
#  FRONTEND — serve index.html
# =========================================================================== #
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# =========================================================================== #
#  API — analyze a stock
# =========================================================================== #
@app.route("/api/analyze/<symbol>")
def api_analyze(symbol):
    try:
        result = brain.analyze_stock(symbol)
        # Save to scans DB
        if "error" not in result:
            today = datetime.now().strftime("%Y-%m-%d")
            with closing(sqlite3.connect(JOURNAL_DB)) as c:
                c.execute("""INSERT OR REPLACE INTO scans
                    (symbol, scan_date, verdict, direction, score, entry, stop,
                     target, quantity, reasons)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (result["symbol"], today, result["rating"],
                     result.get("scores", {}).get("technical", 0) > 15 and "long" or "neutral",
                     result["score"],
                     result.get("plan", {}).get("entry"),
                     result.get("plan", {}).get("stop"),
                     result.get("plan", {}).get("target"),
                     result.get("plan", {}).get("quantity"),
                     json.dumps(result.get("reasons", []))))
                c.commit()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================================== #
#  API — P&L calculator
# =========================================================================== #
@app.route("/api/pnl", methods=["POST"])
def api_pnl():
    data = request.get_json() or {}
    symbol = data.get("symbol", "").strip().upper()
    qty = int(data.get("quantity", 0))
    buy_price = float(data.get("buy_price", 0))
    if not symbol or qty <= 0 or buy_price <= 0:
        return jsonify({"error": "Provide symbol, quantity (>0), buy_price (>0)"}), 400
    return jsonify(brain.calculate_pnl(symbol, qty, buy_price))


# =========================================================================== #
#  API — knowledge search
# =========================================================================== #
@app.route("/api/knowledge")
def api_knowledge():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"results": [], "query": q})
    return jsonify({"results": brain.search_knowledge(q, 10), "query": q})


# =========================================================================== #
#  API — Gem Scanner (find underrated stocks)
# =========================================================================== #
@app.route("/api/gems")
def api_gems():
    """Scan for underrated gem stocks."""
    from gem_scanner import scan_all_gems
    scan_list = brain.STOCKS["large"][:5] + brain.STOCKS["mid"][:5] + brain.STOCKS["small"][:5]
    gems = scan_all_gems(scan_list, 10)
    return jsonify({"gems": gems, "count": len(gems)})


@app.route("/api/gems/<symbol>")
def api_gem_detail(symbol):
    """Get detailed gem analysis for a specific stock."""
    from gem_scanner import find_gem
    result = find_gem(symbol if "." in symbol else f"{symbol}.NS")
    if result:
        return jsonify(result)
    return jsonify({"error": "Could not analyze this stock"}), 404


# =========================================================================== #
#  API — stock universe
# =========================================================================== #
@app.route("/api/stocks/<cap_type>")
def api_stocks(cap_type):
    stocks = brain.STOCKS.get(cap_type, [])
    return jsonify({"cap_type": cap_type, "stocks": stocks, "count": len(stocks)})


# =========================================================================== #
#  API — brain stats
# =========================================================================== #
@app.route("/api/stats")
def api_stats():
    return jsonify(brain.get_stats())


@app.route("/api/rag")
def api_rag():
    """Return RAG training manifest + collection stats."""
    import json as _json
    from pathlib import Path as _Path
    manifest_path = _Path(__file__).resolve().parent / "knowledge" / "rag_training_manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = _json.loads(manifest_path.read_text())
        except Exception:
            pass
    return jsonify({
        "manifest": manifest,
        "stats": brain.rag_stats(),
    })


# =========================================================================== #
#  API — today's scans (from DB)
# =========================================================================== #
@app.route("/api/today")
def api_today():
    today = datetime.now().strftime("%Y-%m-%d")
    with closing(sqlite3.connect(JOURNAL_DB)) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT * FROM scans WHERE scan_date = ? ORDER BY score DESC", (today,)
        ).fetchall()
    return jsonify({"date": today, "scans": [dict(r) for r in rows]})


# =========================================================================== #
#  API — trade journal
# =========================================================================== #
@app.route("/api/trades")
def api_trades():
    with closing(sqlite3.connect(JOURNAL_DB)) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 100").fetchall()
    return jsonify({"trades": [dict(r) for r in rows]})


@app.route("/api/trades/log", methods=["POST"])
def api_log_trade():
    data = request.get_json() or {}
    with closing(sqlite3.connect(JOURNAL_DB)) as c:
        cur = c.execute("""INSERT INTO trades
            (symbol, direction, entry, stop, target, quantity, score, rating,
             opened_at, status, notes)
            VALUES (?,?,?,?,?,?,?,?,?,'open',?)""",
            (data.get("symbol"), data.get("direction"), data.get("entry"),
             data.get("stop"), data.get("target"), data.get("quantity"),
             data.get("score"), data.get("rating"),
             datetime.now().isoformat(timespec="seconds"),
             data.get("notes", "")))
        c.commit()
        return jsonify({"id": cur.lastrowid, "status": "logged"})


@app.route("/api/trades/close/<int:tid>", methods=["POST"])
def api_close_trade(tid):
    data = request.get_json() or {}
    exit_price = float(data.get("exit_price", 0))
    with closing(sqlite3.connect(JOURNAL_DB)) as c:
        c.row_factory = sqlite3.Row
        row = c.execute("SELECT * FROM trades WHERE id=?", (tid,)).fetchone()
        if not row:
            return jsonify({"error": "Trade not found"}), 404
        entry = row["entry"]
        qty = row["quantity"]
        direction = row["direction"]
        if direction == "long":
            pnl = (exit_price - entry) * qty
        else:
            pnl = (entry - exit_price) * qty
        c.execute("""UPDATE trades SET status='closed', exit_price=?, exit_at=?,
                     pnl=? WHERE id=?""",
                  (exit_price, datetime.now().isoformat(timespec="seconds"), pnl, tid))
        c.commit()
        return jsonify({"id": tid, "pnl": round(pnl, 2), "status": "closed"})


# =========================================================================== #
#  MAIN
# =========================================================================== #
if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 50)
    print("  advisor — Trading AI")
    print("  Open: http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
