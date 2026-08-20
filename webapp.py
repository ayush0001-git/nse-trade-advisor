"""
webapp.py - Flask web interface for the advisor trading assistant.

Provides a browser-based dashboard with three sections:
  1. Today's Trades   - live scan results showing TAKE/WATCH setups
  2. Previous Trades  - history of past recommendations from the journal
  3. P&L Calculator   - current price + profit/loss for any stock you enter

Run:
    python webapp.py
    # then open http://localhost:5000 in your browser

Requires: pip install flask yfinance pandas numpy pyyaml
"""
from __future__ import annotations

import os
import sqlite3
import threading
import time
import json
from datetime import datetime, timedelta
from contextlib import closing
from pathlib import Path

from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file, abort

# Add project root to path so we can import the advisor package
PROJECT_ROOT = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from advisor.core import (
    Settings, Style, Direction, Verdict, Regime, load_settings,
    YFinanceSource, CSVSource, get_source, normalize_symbol,
)
from advisor.engine import Analyzer
from advisor.extras import Journal
from advisor.telegram_bot import TelegramNotifier

app = Flask(__name__)
app.config["SECRET_KEY"] = "advisor-local-secret"


def _warm_warehouse():
    """Preload ChromaDB + the ONNX embedding model in the background so the
    first request that touches the warehouse doesn't stall for ~a minute."""
    try:
        from data_warehouse import get_warehouse
        dw = get_warehouse()
        # A throwaway query forces the lazy ONNX embedder to load now.
        dw.query("warmup", collection="investor_wisdom", n=1)
    except Exception as e:
        # Warmup is best-effort; never let it break the app.
        print(f"warehouse warmup skipped: {e}")


# Warm the warehouse at startup (daemon thread: never blocks app startup).
threading.Thread(target=_warm_warehouse, name="warehouse-warmup",
                 daemon=True).start()

# Databases
JOURNAL_DB = str(PROJECT_ROOT / "trade_journal.db")
SCAN_DB = str(PROJECT_ROOT / "scan_results.db")
PREFS_PATH = PROJECT_ROOT / "user_prefs.json"


_prefs_lock = threading.Lock()


def load_prefs() -> dict:
    with _prefs_lock:
        if PREFS_PATH.exists():
            try:
                return json.loads(PREFS_PATH.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}


def save_prefs(prefs: dict) -> None:
    with _prefs_lock:
        tmp = PREFS_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(prefs, indent=2), encoding="utf-8")
        os.replace(tmp, PREFS_PATH)


def style_for(hold_days: int) -> Style:
    return Style.INTRADAY if int(hold_days or 0) <= 1 else Style.SWING

# Global state for RL background training
_rl_train_lock = threading.Lock()
_rl_train_state = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "elapsed_s": 0.0,
    "timesteps_target": 0,
    "timesteps": 0,
    "last_reward": None,
    "error": None,
    "use_triple_barrier": False,
    "model_path": None,
}


# Global state for background scan progress
_scan_lock = threading.Lock()
_scan_state = {
    "running": False,
    "progress": 0,
    "total": 0,
    "current_symbol": "",
    "completed": 0,
    "failures": [],
    "started_at": None,
    "finished_at": None,
    "error": None,
}


# =========================================================================== #
#  Database initialization
# =========================================================================== #
def init_scan_db():
    """Create the scan results database if it doesn't exist."""
    with closing(sqlite3.connect(SCAN_DB)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol      TEXT NOT NULL,
                scan_date   TEXT NOT NULL,
                scan_time   TEXT NOT NULL,
                verdict     TEXT,
                direction   TEXT,
                confidence  REAL,
                confluence  REAL,
                regime      TEXT,
                entry       REAL,
                stop_loss   REAL,
                target      REAL,
                risk_reward REAL,
                quantity    INTEGER,
                rupees_at_risk REAL,
                position_value REAL,
                narration   TEXT,
                signals_count INTEGER,
                UNIQUE(symbol, scan_date)
            )
        """)
        conn.commit()


def get_scan_db():
    conn = sqlite3.connect(SCAN_DB)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================================== #
#  Settings helper
# =========================================================================== #
def get_settings() -> Settings:
    config_path = PROJECT_ROOT / "config.yaml"
    settings = load_settings(str(config_path))
    prefs = load_prefs()
    if prefs.get("capital"):
        settings.capital = float(prefs["capital"])
    if prefs.get("risk_pct"):
        settings.risk_pct = float(prefs["risk_pct"])
    return settings


# =========================================================================== #
#  Routes - pages
# =========================================================================== #
@app.route("/")
def dashboard():
    """Main dashboard: today's trades + previous trades + quick P&L."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Today's scan results
    with closing(get_scan_db()) as conn:
        today_scans = conn.execute(
            "SELECT * FROM scan_results WHERE scan_date = ? "
            "ORDER BY CASE verdict "
            "  WHEN 'TAKE' THEN 0 WHEN 'WATCH' THEN 1 "
            "  WHEN 'NO_SETUP' THEN 2 WHEN 'AVOID' THEN 3 END, "
            "confidence DESC",
            (today,)
        ).fetchall()

    # Previous trades from journal
    journal = Journal(JOURNAL_DB)
    open_trades = journal.open_trades()
    recent_closed = journal.recent(10)
    stats = journal.stats()

    # Scan status
    scan_status = dict(_scan_state)
    prefs = load_prefs()

    # Filter out non-actionable SHORTs when the user only trades cash equity
    # and can't square off same-day (hold_days > 1). Everything else stays.
    hidden_shorts = 0
    if prefs.get("cash_only", True) and int(prefs.get("hold_days", 1)) > 1:
        filtered = [s for s in today_scans if s["direction"] != "short"]
        hidden_shorts = len(today_scans) - len(filtered)
        today_scans = filtered

    return render_template("dashboard.html",
                           today_scans=today_scans,
                           hidden_shorts=hidden_shorts,
                           open_trades=open_trades,
                           recent_closed=recent_closed,
                           stats=stats,
                           scan_status=scan_status,
                           prefs=prefs,
                           today=today)


@app.route("/api/prefs", methods=["GET", "POST"])
def api_prefs():
    if request.method == "GET":
        return jsonify(load_prefs())

    data = request.get_json() or {}
    try:
        capital = float(data.get("capital", 0))
        risk_pct = float(data.get("risk_pct", 0))
        target_profit = float(data.get("target_profit", 0))
        hold_days = int(data.get("hold_days", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid number in form."}), 400

    if capital < 1000:
        return jsonify({"error": "Capital must be at least ₹1,000."}), 400
    if not (0 < risk_pct <= 0.10):
        return jsonify({"error": "Risk % must be between 0.1 and 10."}), 400
    if target_profit <= 0:
        return jsonify({"error": "Target profit must be > 0."}), 400
    if hold_days < 1 or hold_days > 60:
        return jsonify({"error": "Holding days must be 1-60."}), 400

    cash_only = bool(data.get("cash_only", True))

    prefs = {
        "capital": capital,
        "risk_pct": risk_pct,
        "target_profit": target_profit,
        "hold_days": hold_days,
        "style": "intraday" if hold_days <= 1 else "swing",
        "cash_only": cash_only,
    }
    save_prefs(prefs)
    return jsonify({"status": "saved", "prefs": prefs})


_ticker_cache = {"at": 0.0, "data": None}


@app.route("/api/ticker")
def api_ticker():
    """Live-ish index quotes (NIFTY, SENSEX, BANKNIFTY), cached 30s."""
    import yfinance as yf
    now_ts = time.time()
    if _ticker_cache["data"] and (now_ts - _ticker_cache["at"] < 30):
        return jsonify(_ticker_cache["data"])

    tickers = {"NIFTY": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK"}
    out = {}
    for label, yf_sym in tickers.items():
        try:
            t = yf.Ticker(yf_sym)
            hist = t.history(period="2d", interval="1d")
            if len(hist) >= 1:
                last = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else last
                chg = last - prev
                pct = (chg / prev * 100) if prev else 0.0
                out[label] = {"price": round(last, 2), "chg": round(chg, 2), "pct": round(pct, 2)}
        except Exception:
            out[label] = None

    # Market open? IST 09:15 - 15:30, Mon-Fri
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    is_weekday = ist.weekday() < 5
    hm = ist.hour * 60 + ist.minute
    is_open = is_weekday and (9 * 60 + 15) <= hm <= (15 * 60 + 30)

    payload = {"indices": out, "market_open": is_open, "at": now_ts}
    _ticker_cache["at"] = now_ts
    _ticker_cache["data"] = payload
    return jsonify(payload)


@app.route("/api/prefs/reset", methods=["POST"])
def api_prefs_reset():
    if PREFS_PATH.exists():
        try:
            PREFS_PATH.unlink()
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"status": "cleared"})


# =========================================================================== #
#  Telegram integration
# =========================================================================== #
@app.route("/api/telegram/status")
def api_telegram_status():
    """Return whether Telegram is configured (both env vars present)."""
    n = TelegramNotifier()
    return jsonify({"configured": n.is_configured()})


@app.route("/api/telegram/test", methods=["POST"])
def api_telegram_test():
    """Send a test message. Returns {ok, sent, error}."""
    n = TelegramNotifier()
    if not n.is_configured():
        return jsonify({"ok": False, "sent": False,
                        "error": "not configured"}), 412
    sent = n.send_message("advisor test")
    return jsonify({"ok": bool(sent), "sent": bool(sent),
                    "error": None if sent else "send failed"})


@app.route("/api/telegram/digest", methods=["POST"])
def api_telegram_digest():
    """Send the morning digest (top-3 TAKE from today's scan) on demand.

    Point Windows Task Scheduler at this endpoint to get a scheduled push.
    Query for scan_date=YYYY-MM-DD to override today.
    """
    n = TelegramNotifier()
    if not n.is_configured():
        return jsonify({"ok": False, "sent": False,
                        "error": "not configured"}), 412

    scan_date = (request.args.get("scan_date")
                 or (request.get_json(silent=True) or {}).get("scan_date")
                 or datetime.now().strftime("%Y-%m-%d"))
    with closing(get_scan_db()) as conn:
        rows = conn.execute(
            "SELECT * FROM scan_results WHERE scan_date = ? "
            "AND verdict = 'TAKE' ORDER BY confidence DESC",
            (scan_date,)
        ).fetchall()

    sent = n.send_digest([dict(r) for r in rows], load_prefs())
    return jsonify({"ok": bool(sent), "sent": bool(sent),
                    "count": len(rows), "scan_date": scan_date,
                    "error": None if sent else "send failed"})


@app.route("/history")
def history():
    """Full trade history from the journal."""
    journal = Journal(JOURNAL_DB)
    all_trades = journal.recent(200)
    stats = journal.stats()
    open_trades = journal.open_trades()
    return render_template("history.html",
                           trades=all_trades,
                           stats=stats,
                           open_trades=open_trades)


@app.route("/stock/<symbol>")
def stock_detail(symbol):
    """Deep analysis of a single stock with P&L calculator.

    Served from today's scan_results row when one exists (fast path — no
    yfinance re-analysis). Add ?live=1 to force a fresh live analysis.
    """
    settings = get_settings()
    force_live = request.args.get("live") == "1"

    # Try to get current scan result from today's DB first (fast path).
    # scan_results stores suffixed symbols (RELIANCE.NS) while in-app links
    # strip the suffix, so match both forms.
    today = datetime.now().strftime("%Y-%m-%d")
    with closing(get_scan_db()) as conn:
        cached = conn.execute(
            "SELECT * FROM scan_results WHERE symbol IN (?, ?, ?) AND scan_date = ?",
            (symbol, f"{symbol}.NS", f"{symbol}.BO", today)
        ).fetchone()

    # Fast path: build the page from today's cached scan row. NO_SETUP rows
    # have no price levels (entry is NULL), so those still go live.
    if cached and cached["entry"] is not None and not force_live:
        entry = float(cached["entry"])
        # One cheap live quote so the header price isn't the stale scan price;
        # the plan levels legitimately stay as scanned.
        live_px = None
        try:
            live_px = YFinanceSource(exchange=settings.exchange).get_quote(symbol)
        except Exception:
            pass
        idea_data = {
            "symbol": cached["symbol"],
            "verdict": cached["verdict"],
            "direction": cached["direction"],
            "confidence": cached["confidence"] or 0,
            "confluence": cached["confluence"],
            "regime": cached["regime"],
            "current_price": float(live_px) if live_px else entry,
            "rsi": None,
            "atr": None,
            "adx": None,
            "signals": [],
            "vetoes": [],
            "plan": None,
            "scenarios": [],
            "narration": cached["narration"],
            "notes": [f"Served from today's scan ({cached['scan_time']})"
                      + ("" if live_px else " — price shown is the scan-time entry")
                      + ". Add ?live=1 to the URL for a fresh live analysis."],
        }
        if (cached["stop_loss"] is not None and cached["target"] is not None
                and cached["quantity"] is not None):
            idea_data["plan"] = {
                "entry": entry,
                "stop_loss": cached["stop_loss"],
                "target": cached["target"],
                "quantity": cached["quantity"],
                "risk_reward": cached["risk_reward"],
                "rupees_at_risk": cached["rupees_at_risk"],
                "position_value": cached["position_value"],
                "risk_per_share": abs(entry - float(cached["stop_loss"])),
                "reward_per_share": abs(float(cached["target"]) - entry),
            }
        return render_template("stock.html",
                               symbol=symbol,
                               idea=idea_data,
                               error=None,
                               cached=cached,
                               prefs=load_prefs())

    # Fetch live data and run analysis
    try:
        source = get_source(settings.data_source, exchange=settings.exchange,
                            directory=settings.csv_dir)
        agent = Analyzer(settings, source=source, journal=Journal(JOURNAL_DB))
        idea = agent.analyze(symbol, style=Style.SWING, use_llm=False, use_news=False)
        idea_data = {
            "symbol": idea.symbol,
            "verdict": idea.verdict.value,
            "direction": idea.direction.value,
            "confidence": idea.confidence,
            "confluence": idea.confluence_score,
            "regime": idea.regime.value,
            "current_price": idea.indicators.close,
            "rsi": idea.indicators.rsi_14,
            "atr": idea.indicators.atr_14,
            "adx": idea.indicators.adx_14,
            "signals": [{"name": s.name, "direction": s.direction.value,
                         "note": s.note, "weight": s.weight}
                        for s in idea.signals],
            "vetoes": [{"name": v.name, "reason": v.reason, "severity": v.severity}
                       for v in idea.vetoes],
            "plan": None,
            "scenarios": [{"name": s.name, "probability": s.probability,
                           "target": s.price_target, "move_pct": s.move_pct,
                           "rationale": s.rationale}
                          for s in idea.scenarios],
            "narration": idea.narration,
            "notes": idea.notes,
        }
        if idea.plan:
            idea_data["plan"] = {
                "entry": idea.plan.entry,
                "stop_loss": idea.plan.stop_loss,
                "target": idea.plan.target,
                "quantity": idea.plan.quantity,
                "risk_reward": idea.plan.risk_reward,
                "rupees_at_risk": idea.plan.rupees_at_risk,
                "position_value": idea.plan.position_value,
                "risk_per_share": idea.plan.risk_per_share,
                "reward_per_share": idea.plan.reward_per_share,
            }
        error = None
    except Exception as e:
        idea_data = None
        error = f"{type(e).__name__}: {e}"

    return render_template("stock.html",
                           symbol=symbol,
                           idea=idea_data,
                           error=error,
                           cached=cached,
                           prefs=load_prefs())


@app.route("/scan")
def scan_page():
    """Scan runner page with progress."""
    return render_template("scan.html", scan_status=dict(_scan_state))


# =========================================================================== #
#  API endpoints
# =========================================================================== #
@app.route("/api/scan/start", methods=["POST"])
def api_scan_start():
    """Start a background scan of the watchlist."""
    with _scan_lock:
        if _scan_state["running"]:
            return jsonify({"status": "already_running",
                            "progress": _scan_state["progress"],
                            "total": _scan_state["total"]})
        _scan_state["running"] = True

    try:
        # Decide which symbols to scan
        data = request.get_json(silent=True) or {}
        symbols = data.get("symbols")
        if not symbols:
            settings = get_settings()
            symbols = settings.watchlist

        # Limit for safety (scanning 2000 stocks takes 17+ minutes)
        if len(symbols) > 100:
            symbols = symbols[:100]

        thread = threading.Thread(target=_scan_worker, args=(symbols,), daemon=True)
        thread.start()
    except Exception:
        _scan_state["running"] = False
        raise
    return jsonify({"status": "started", "total": len(symbols)})


@app.route("/api/scan/status")
def api_scan_status():
    """Poll the scan progress."""
    return jsonify(dict(_scan_state))


@app.route("/api/pnl", methods=["POST"])
def api_pnl():
    """Calculate P&L for a given stock, quantity, and buy price."""
    data = request.get_json() or {}
    symbol = data.get("symbol", "").strip().upper()
    try:
        qty = int(data.get("quantity", 0))
        buy_price = float(data.get("buy_price", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Quantity and buy_price must be numbers."}), 400

    if not symbol or qty <= 0 or buy_price <= 0:
        return jsonify({"error": "Please provide symbol, quantity (>0), and buy_price (>0)."}), 400

    settings = get_settings()
    try:
        source = YFinanceSource(exchange=settings.exchange)
        current_price = source.get_quote(symbol)
    except Exception as e:
        return jsonify({"error": f"Could not fetch price: {e}"}), 500

    if current_price is None:
        return jsonify({"error": f"Could not fetch current price for {symbol}. "
                                  "Check the symbol or try again later."}), 404

    invested = qty * buy_price
    current_value = qty * current_price
    pnl = current_value - invested
    pnl_pct = (pnl / invested * 100) if invested > 0 else 0

    # Also fetch the advisor's recommendation if we have data
    recommendation = None
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        with closing(get_scan_db()) as conn:
            row = conn.execute(
                "SELECT * FROM scan_results WHERE symbol IN (?, ?) AND scan_date = ?",
                (symbol, f"{symbol}.NS", today)
            ).fetchone()
        if row:
            recommendation = dict(row)
    except Exception:
        pass

    return jsonify({
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "buy_price": buy_price,
        "quantity": qty,
        "invested": round(invested, 2),
        "current_value": round(current_value, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "recommendation": recommendation,
    })


@app.route("/api/analyze/<symbol>", methods=["POST"])
def api_analyze(symbol):
    """Run live analysis on a single symbol and cache the result."""
    settings = get_settings()
    try:
        source = get_source(settings.data_source, exchange=settings.exchange,
                            directory=settings.csv_dir)
        agent = Analyzer(settings, source=source, journal=Journal(JOURNAL_DB))
        idea = agent.analyze(symbol, style=Style.SWING, use_llm=False, use_news=False)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Save to scan DB
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().isoformat(timespec="seconds")
    plan = idea.plan
    with closing(get_scan_db()) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO scan_results
            (symbol, scan_date, scan_time, verdict, direction, confidence,
             confluence, regime, entry, stop_loss, target, risk_reward,
             quantity, rupees_at_risk, position_value, narration, signals_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            idea.symbol, today, now, idea.verdict.value, idea.direction.value,
            idea.confidence, idea.confluence_score, idea.regime.value,
            plan.entry if plan else None, plan.stop_loss if plan else None,
            plan.target if plan else None,
            plan.risk_reward if plan else None,
            plan.quantity if plan else None,
            plan.rupees_at_risk if plan else None,
            plan.position_value if plan else None,
            idea.narration, len(idea.signals),
        ))
        conn.commit()

    return jsonify({
        "symbol": idea.symbol,
        "verdict": idea.verdict.value,
        "direction": idea.direction.value,
        "confidence": idea.confidence,
        "current_price": idea.indicators.close,
        "entry": plan.entry if plan else None,
        "stop_loss": plan.stop_loss if plan else None,
        "target": plan.target if plan else None,
        "quantity": plan.quantity if plan else None,
        "risk_reward": plan.risk_reward if plan else None,
    })


@app.route("/api/journal/log", methods=["POST"])
def api_journal_log():
    """Log a trade into the journal."""
    data = request.get_json() or {}
    symbol = data.get("symbol", "").strip()
    if not symbol:
        return jsonify({"error": "symbol required"}), 400

    settings = get_settings()
    try:
        source = get_source(settings.data_source, exchange=settings.exchange,
                            directory=settings.csv_dir)
        agent = Analyzer(settings, source=source, journal=Journal(JOURNAL_DB))
        idea = agent.analyze(symbol, style=Style.SWING, use_llm=False, use_news=False)
        if idea.plan is None or idea.plan.quantity <= 0:
            return jsonify({"error": "No tradeable plan for this stock right now."}), 400

        # Allow the caller to override the advisor's suggested quantity.
        qty_override = data.get("quantity")
        if qty_override is not None:
            try:
                qty_override = int(qty_override)
            except (TypeError, ValueError):
                return jsonify({"error": "Quantity must be a whole number."}), 400
            if qty_override <= 0:
                return jsonify({"error": "Quantity must be at least 1."}), 400
            idea.plan.quantity = qty_override

        journal = Journal(JOURNAL_DB)
        tid = journal.log_idea(idea, notes=data.get("note", ""))
        return jsonify({
            "id": tid,
            "symbol": idea.symbol,
            "direction": idea.direction.value,
            "quantity": idea.plan.quantity,
            "entry": idea.plan.entry,
            "stop_loss": idea.plan.stop_loss,
            "target": idea.plan.target,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/journal/close", methods=["POST"])
def api_journal_close():
    """Close a trade in the journal."""
    data = request.get_json() or {}
    try:
        trade_id = int(data.get("trade_id", 0))
        exit_price = float(data.get("exit_price", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "trade_id and exit_price must be numbers"}), 400
    if trade_id <= 0 or exit_price <= 0:
        return jsonify({"error": "trade_id and exit_price required"}), 400
    try:
        journal = Journal(JOURNAL_DB)
        res = journal.close_trade(trade_id, exit_price, notes=data.get("note", ""))
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


TEARSHEET_PATH = PROJECT_ROOT / "static" / "tearsheet.html"


@app.route("/tearsheet")
def tearsheet_page():
    """QuantStats institutional tearsheet built from the journal."""
    journal = Journal(JOURNAL_DB)
    closed = [t for t in journal.recent(500) if t.get("status") == "closed"
              and t.get("pnl") is not None and t.get("exit_price") is not None]
    n_closed = len(closed)
    exists = TEARSHEET_PATH.exists()
    fresh = False
    generated_at = None
    if exists:
        mtime = TEARSHEET_PATH.stat().st_mtime
        generated_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        fresh = (time.time() - mtime) < 3600
    return render_template("tearsheet.html",
                           n_closed=n_closed,
                           exists=exists,
                           fresh=fresh,
                           generated_at=generated_at)


@app.route("/api/tearsheet/generate")
def api_tearsheet_generate():
    """Regenerate the QuantStats tearsheet from the journal. Returns JSON."""
    from advisor.tearsheet import journal_to_returns, render_html_tearsheet
    prefs = load_prefs()
    starting_capital = float(prefs.get("capital") or 100_000.0)
    try:
        returns = journal_to_returns(JOURNAL_DB, starting_capital=starting_capital)
        if returns.empty:
            return jsonify({
                "status": "insufficient_data",
                "error": "Need at least 3 closed trades to build a tearsheet.",
                "trades_used": 0,
            }), 400
        info = render_html_tearsheet(returns, TEARSHEET_PATH)
        return jsonify({
            "status": "ok",
            "path": str(TEARSHEET_PATH),
            "trades_used": int(len(returns)),
            "days": info["days"],
            "benchmark_loaded": info["benchmark_loaded"],
            "benchmark": info["benchmark"],
        })
    except Exception as e:
        app.logger.exception("tearsheet generation failed")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/tearsheet/view")
def tearsheet_view():
    """Serve the generated tearsheet HTML file directly."""
    if not TEARSHEET_PATH.exists():
        abort(404, "No tearsheet generated yet. Hit /api/tearsheet/generate first.")
    return send_file(str(TEARSHEET_PATH), mimetype="text/html")


@app.route("/api/chart/<symbol>")
def api_chart(symbol: str):
    """Daily OHLCV + indicators for the stock-page chart.

    Fetches 2y so the 200-SMA is warm, returns the last ~250 visible bars.
    """
    from advisor.analysis import sma, rsi, bollinger
    import pandas as pd
    sym_full = symbol if "." in symbol else f"{symbol}.NS"
    try:
        import yfinance as yf
        df = yf.Ticker(sym_full).history(period="2y", interval="1d")
        if df is None or len(df) < 30:
            return jsonify({"error": f"Not enough data for {sym_full}"}), 404

        close = df["Close"]
        s20 = sma(close, 20)
        s200 = sma(close, 200)
        r14 = rsi(close, 14)
        bb_u, bb_m, bb_l, _ = bollinger(close)

        view = df.iloc[-250:]

        def ts(idx):
            return idx.strftime("%Y-%m-%d")

        candles, volume = [], []
        for idx, row in view.iterrows():
            t = ts(idx)
            candles.append({"time": t, "open": round(float(row["Open"]), 2),
                            "high": round(float(row["High"]), 2),
                            "low": round(float(row["Low"]), 2),
                            "close": round(float(row["Close"]), 2)})
            volume.append({"time": t, "value": float(row.get("Volume", 0) or 0),
                           "up": bool(row["Close"] >= row["Open"])})

        def series(s):
            out = []
            for idx in view.index:
                v = s.get(idx)
                if v is not None and not pd.isna(v):
                    out.append({"time": ts(idx), "value": round(float(v), 2)})
            return out

        return jsonify({
            "symbol": symbol,
            "candles": candles,
            "volume": volume,
            "sma20": series(s20),
            "sma200": series(s200),
            "bb_upper": series(bb_u),
            "bb_lower": series(bb_l),
            "rsi": series(r14),
        })
    except Exception as e:
        app.logger.exception("chart data failed for %s", sym_full)
        return jsonify({"error": str(e)}), 500


@app.route("/backtest/<symbol>")
def backtest_page(symbol):
    """Interactive backtest of the swing strategy on one stock."""
    return render_template("backtest.html", symbol=symbol.upper(),
                           prefs=load_prefs())


# Shared 5y-daily-bars cache for the three backtest endpoints so
# backtest -> optimize -> walkforward on the same symbol downloads once.
_bt_data_lock = threading.Lock()
_bt_data_cache: dict = {}   # sym_full -> (fetched_at, DataFrame)
_BT_DATA_TTL_S = 3600       # 1 hour


def _get_backtest_df(sym_full: str):
    """Return 5y of daily bars for sym_full, cached in memory for 1 hour."""
    now = time.time()
    with _bt_data_lock:
        hit = _bt_data_cache.get(sym_full)
        if hit and (now - hit[0]) < _BT_DATA_TTL_S:
            return hit[1].copy()

    import yfinance as yf
    df = yf.Ticker(sym_full).history(period="5y", interval="1d")
    if df is not None and len(df) > 0:
        with _bt_data_lock:
            _bt_data_cache[sym_full] = (time.time(), df)
            # Bound the cache: evict oldest entries beyond 30 symbols
            # (~10MB each x 30 is a sane ceiling for a long-running server).
            while len(_bt_data_cache) > 30:
                oldest = min(_bt_data_cache, key=lambda k: _bt_data_cache[k][0])
                del _bt_data_cache[oldest]
        return df.copy()
    return df


@app.route("/api/backtest/<symbol>")
def api_backtest(symbol: str):
    """Run the SwingLong backtest on the last 5 years of daily data."""
    from advisor.bt_engine import run_backtest
    settings = get_settings()
    prefs = load_prefs()
    cash = float(prefs.get("capital") or settings.capital or 100000)
    sym_full = symbol if "." in symbol else f"{symbol}.NS"
    try:
        df = _get_backtest_df(sym_full)
        if df is None or len(df) == 0:
            return jsonify({"error": f"No data for {sym_full}"}), 404
        result = run_backtest(df, cash=cash)
        result["symbol"] = symbol
        return jsonify(result)
    except Exception as e:
        app.logger.exception("backtest failed for %s", sym_full)
        return jsonify({"error": str(e)}), 500


@app.route("/backtest/optimize/<symbol>")
def backtest_optimize_page(symbol):
    """Parameter-sweep page: find best RSI/ADX combo for this stock."""
    return render_template("backtest_optimize.html", symbol=symbol.upper(),
                           prefs=load_prefs())


@app.route("/api/backtest/optimize/<symbol>")
def api_backtest_optimize(symbol: str):
    """Sweep RSI/ADX thresholds against 5 years of daily data."""
    from advisor.bt_engine import run_optimize
    settings = get_settings()
    prefs = load_prefs()
    cash = float(prefs.get("capital") or settings.capital or 100000)
    sym_full = symbol if "." in symbol else f"{symbol}.NS"
    try:
        df = _get_backtest_df(sym_full)
        if df is None or len(df) == 0:
            return jsonify({"error": f"No data for {sym_full}"}), 404
        result = run_optimize(df, cash=cash)
        result["symbol"] = symbol
        return jsonify(result)
    except Exception as e:
        app.logger.exception("backtest failed for %s", sym_full)
        return jsonify({"error": str(e)}), 500


@app.route("/backtest/walkforward/<symbol>")
def backtest_walkforward_page(symbol):
    """Walk-forward validation page: rolling IS/OOS folds so we get an honest
    out-of-sample Sharpe (not the overfitted in-sample number)."""
    return render_template("backtest_walkforward.html", symbol=symbol.upper(),
                           prefs=load_prefs())


@app.route("/api/backtest/walkforward/<symbol>")
def api_backtest_walkforward(symbol: str):
    """Rolling 1y-train / 3mo-test walk-forward over 5 years of daily data."""
    from advisor.bt_engine import run_walk_forward
    settings = get_settings()
    prefs = load_prefs()
    cash = float(prefs.get("capital") or settings.capital or 100000)
    sym_full = symbol if "." in symbol else f"{symbol}.NS"
    try:
        df = _get_backtest_df(sym_full)
        if df is None or len(df) == 0:
            return jsonify({"error": f"No data for {sym_full}"}), 404
        result = run_walk_forward(df, cash=cash)
        result["symbol"] = symbol
        return jsonify(result)
    except Exception as e:
        app.logger.exception("backtest failed for %s", sym_full)
        return jsonify({"error": str(e)}), 500


@app.route("/api/journal/delete", methods=["POST"])
def api_journal_delete():
    """Delete a trade (open OR closed) from the journal."""
    data = request.get_json() or {}
    try:
        trade_id = int(data.get("trade_id", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "trade_id must be a number"}), 400
    if trade_id <= 0:
        return jsonify({"error": "trade_id required"}), 400
    try:
        with sqlite3.connect(JOURNAL_DB) as conn:
            cur = conn.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
            conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": f"No trade with id {trade_id}"}), 404
        return jsonify({"status": "deleted", "id": trade_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/journal/stats")
def api_journal_stats():
    """Get journal stats."""
    journal = Journal(JOURNAL_DB)
    return jsonify(journal.stats())


@app.route("/portfolio")
def portfolio_page():
    """HRP-based portfolio allocation across today's TAKE-LONG setups."""
    today = datetime.now().strftime("%Y-%m-%d")
    prefs = load_prefs()
    with closing(get_scan_db()) as conn:
        rows = conn.execute(
            "SELECT symbol FROM scan_results "
            "WHERE scan_date = ? AND verdict = 'TAKE' AND direction = 'long' "
            "ORDER BY confidence DESC",
            (today,)
        ).fetchall()
    take_symbols = [r["symbol"] for r in rows]
    return render_template("portfolio.html",
                           take_symbols=take_symbols,
                           prefs=prefs,
                           today=today)


@app.route("/api/portfolio/allocate")
def api_portfolio_allocate():
    """Return HRP allocation JSON for today's TAKE-LONG symbols.

    Query params:
        limit: max number of symbols to feed HRP (default 8, capped at 20).
        lookback_days: return-window used for covariance (default 60).
    """
    try:
        limit = int(request.args.get("limit", 8))
    except (TypeError, ValueError):
        limit = 8
    limit = max(2, min(limit, 20))

    try:
        lookback = int(request.args.get("lookback_days", 60))
    except (TypeError, ValueError):
        lookback = 60
    lookback = max(20, min(lookback, 250))

    today = datetime.now().strftime("%Y-%m-%d")
    with closing(get_scan_db()) as conn:
        rows = conn.execute(
            "SELECT symbol FROM scan_results "
            "WHERE scan_date = ? AND verdict = 'TAKE' AND direction = 'long' "
            "ORDER BY confidence DESC LIMIT ?",
            (today, limit)
        ).fetchall()
    symbols = [r["symbol"] for r in rows]

    prefs = load_prefs()
    capital = float(prefs.get("capital") or get_settings().capital or 100_000.0)

    # Optional sector labels — best effort, don't fail the allocation if sector
    # data isn't loaded.
    sectors: dict = {}
    try:
        from sector_rotation import SectorRotation
        sr = SectorRotation()
        if sr.load_cached():
            for sym in symbols:
                ctx = sr.get_context(sym)
                if ctx.get("available"):
                    sectors[sym.split(".")[0]] = ctx.get("sector")
    except Exception:
        sectors = {}

    try:
        from advisor.allocator import allocate
        result = allocate(symbols, capital=capital, lookback_days=lookback)
        result["capital"] = capital
        result["limit"] = limit
        result["sectors"] = sectors
        return jsonify(result)
    except Exception as e:
        app.logger.exception("portfolio allocation failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rl_opinion/<symbol>")
def api_rl_opinion(symbol):
    """Get the RL agent's second opinion on a stock.

    Loads the trained PPO model from rl_models/ and runs it on the latest
    100 days of data for the given symbol. Returns the action (HOLD/BUY/SELL),
    position size, and current price. Falls back gracefully if the model
    isn't trained yet.
    """
    try:
        from rl_agent import predict as rl_predict, MODEL_PATH
    except ImportError as e:
        return jsonify({"error": f"RL module not available: {e}", "available": False}), 500

    if not MODEL_PATH.exists():
        return jsonify({
            "available": False,
            "error": "RL agent not trained yet. Run: python rl_agent.py train --timesteps 100000"
        }), 404

    try:
        result = rl_predict(symbol)
        result["available"] = True
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "available": False}), 500


@app.route("/api/rl_backtest")
def api_rl_backtest():
    """Return the saved RL backtest results (120+ episodes)."""
    from rl_agent import RESULTS_PATH
    if not RESULTS_PATH.exists():
        return jsonify({"available": False,
                        "error": "No backtest results. Run: python rl_agent.py backtest --episodes 100"})
    try:
        with open(RESULTS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({"available": False, "error": str(e)})
    return jsonify({"available": True, **data})


def _rl_train_worker(timesteps: int, use_triple_barrier: bool):
    """Background worker that trains the PPO agent and updates _rl_train_state."""
    try:
        from rl_agent import train_agent, MODEL_PATH as _RL_MODEL_PATH
        started = time.time()
        _rl_train_state.update({
            "running": True,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "finished_at": None,
            "elapsed_s": 0.0,
            "timesteps_target": int(timesteps),
            "timesteps": 0,
            "last_reward": None,
            "error": None,
            "use_triple_barrier": bool(use_triple_barrier),
            "model_path": str(_RL_MODEL_PATH),
        })

        def _progress(n_calls, ep_reward, elapsed):
            _rl_train_state["timesteps"] = int(n_calls)
            _rl_train_state["elapsed_s"] = round(float(elapsed), 1)
            if ep_reward is not None:
                _rl_train_state["last_reward"] = float(ep_reward)

        train_agent(timesteps=int(timesteps),
                    use_triple_barrier=bool(use_triple_barrier),
                    progress_cb=_progress)
        _rl_train_state["timesteps"] = int(timesteps)
        _rl_train_state["elapsed_s"] = round(time.time() - started, 1)
    except Exception as e:
        _rl_train_state["error"] = f"{type(e).__name__}: {e}"
    finally:
        _rl_train_state["running"] = False
        _rl_train_state["finished_at"] = datetime.now().isoformat(timespec="seconds")


@app.route("/api/rl/train", methods=["POST"])
def api_rl_train():
    """Kick off a background RL training run."""
    with _rl_train_lock:
        if _rl_train_state["running"]:
            return jsonify({
                "status": "already_running",
                "timesteps": _rl_train_state["timesteps"],
                "timesteps_target": _rl_train_state["timesteps_target"],
            })
        _rl_train_state["running"] = True

    try:
        try:
            timesteps = int(request.args.get("timesteps") or (request.get_json(silent=True) or {}).get("timesteps") or 10000)
        except (TypeError, ValueError):
            timesteps = 10000
        timesteps = max(500, min(timesteps, 500_000))
        use_tb_raw = request.args.get("use_triple_barrier") or (request.get_json(silent=True) or {}).get("use_triple_barrier") or ""
        use_tb = str(use_tb_raw).lower() in ("1", "true", "yes", "on")

        thread = threading.Thread(target=_rl_train_worker,
                                  args=(timesteps, use_tb), daemon=True)
        thread.start()
    except Exception:
        _rl_train_state["running"] = False
        raise
    return jsonify({"status": "started", "timesteps_target": timesteps,
                    "use_triple_barrier": use_tb})


@app.route("/api/rl/train_status")
def api_rl_train_status():
    """Poll RL training progress."""
    return jsonify(dict(_rl_train_state))


@app.route("/api/strategy_lab")
def api_strategy_lab():
    """Return the saved strategy backtest results."""
    from strategies import RESULTS_PATH
    if not RESULTS_PATH.exists():
        return jsonify({"available": False,
                        "error": "No strategy results. Run: python strategies.py backtest"})
    try:
        with open(RESULTS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({"available": False, "error": str(e)})
    return jsonify({"available": True, **data})


@app.route("/api/strategy_signals/<symbol>")
def api_strategy_signals(symbol):
    """Get current signals from all 6 strategies for a single stock."""
    try:
        from strategies import get_all_signals
        result = get_all_signals(symbol)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sector_context/<symbol>")
def api_sector_context(symbol):
    """Get the sector rotation context for a stock."""
    try:
        from sector_rotation import SectorRotation
        sr = SectorRotation()
        if not sr.load_cached():
            return jsonify({"available": False,
                            "error": "No sector data. Run: python sector_rotation.py refresh"}), 404
        context = sr.get_context(symbol)
        return jsonify(context)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sector_rankings")
def api_sector_rankings():
    """Get the full sector rankings."""
    try:
        from sector_rotation import SectorRotation
        sr = SectorRotation()
        if not sr.load_cached():
            return jsonify({"available": False,
                            "error": "No sector data. Run: python sector_rotation.py refresh"}), 404
        all_sectors = sorted(sr.sectors.values(), key=lambda s: s.rank)
        return jsonify({
            "available": True,
            "last_refresh": sr.last_refresh,
            "sectors": [s.__dict__ for s in all_sectors],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/strategy-lab")
def strategy_lab_page():
    """Strategy Lab page: backtest results + sector rankings."""
    return render_template("strategy_lab.html")


@app.route("/api/consensus/<symbol>")
def api_consensus(symbol):
    """Get the full consensus score (all 5 engines combined) for a stock.

    Aggregates: advisor + RL + sector + 16 strategies + 10 candlestick patterns
    into a single 0-100 conviction score with bias and agreement %.
    """
    try:
        from consensus import get_full_consensus
        result = get_full_consensus(symbol)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "consensus": {"available": False}}), 500


@app.route("/api/patterns/<symbol>")
def api_patterns(symbol):
    """Detect candlestick patterns for a stock."""
    try:
        from patterns import detect_with_context
        from strategies import fetch_stock_data
        sym = symbol if "." in symbol else f"{symbol}.NS"
        df = fetch_stock_data(sym, period="1y")
        result = detect_with_context(df)
        result["symbol"] = sym
        result["current_price"] = round(float(df["close"].iloc[-1]), 2)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/consensus")
def consensus_page():
    """Consensus dashboard - the ultimate multi-engine conviction view."""
    return render_template("consensus.html")


# In-memory cache of council results keyed by (symbol, date); the pipeline is
# expensive (5 agents, 10-20 network calls) so repeat views serve from here.
_council_lock = threading.Lock()
_council_cache: dict = {}   # (SYMBOL, "YYYY-MM-DD") -> result dict


@app.route("/api/agent_council/<symbol>")
def api_agent_council(symbol):
    """Run the full 5-agent pipeline and return the 100-point score.

    This is the professional hedge-fund-style multi-agent system:
      Agent 1: News Hunter (news + social)
      Agent 2: Technical Analyst (TA + patterns + sector + options)
      Agent 3: Quant Researcher (strategies + RL)
      Agent 4: Risk Manager (vetoes + position sizing)
      Agent 5: Portfolio Manager (final 100-point score + RAG rules)

    Results are cached per (symbol, date); pass ?refresh=1 to force a re-run.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = (symbol.upper(), today)
    if request.args.get("refresh") != "1":
        with _council_lock:
            cached = _council_cache.get(cache_key)
        if cached is not None:
            return jsonify(cached)

    try:
        from agents.portfolio_manager import PortfolioManager
        pm = PortfolioManager()
        result = pm.analyze(symbol)
        with _council_lock:
            # Drop stale (previous-day) entries so the cache stays small.
            for key in [k for k in _council_cache if k[1] != today]:
                _council_cache.pop(key, None)
            _council_cache[cache_key] = result
        return jsonify(result)
    except Exception as e:
        app.logger.exception("agent council failed for %s", symbol)
        return jsonify({
            "error": str(e),
            "final_score": 0,
            "rating": "ERROR",
        }), 500


@app.route("/council")
def agent_council_page():
    """The 5-Agent Council page - professional multi-agent scoring."""
    return render_template("agent_council.html")


@app.route("/discover")
def discover_page():
    """Discover stocks by type (large/mid/small cap) with explanations."""
    return render_template("discover.html")


# Stock universe by market cap (used by the Discover feature)
DISCOVER_UNIVERSE = {
    "large": [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "AXISBANK.NS",
        "HINDUNILVR.NS", "MARUTI.NS", "KOTAKBANK.NS", "BAJFINANCE.NS",
        "ASIANPAINT.NS", "HCLTECH.NS", "WIPRO.NS", "SUNPHARMA.NS",
    ],
    "mid": [
        "PIDILITIND.NS", "DABUR.NS", "GODREJCP.NS", "MARICO.NS", "COLPAL.NS",
        "HAVELLS.NS", "BANKBARODA.NS", "PNB.NS", "IOC.NS", "VEDL.NS",
        "NMDC.NS", "SAIL.NS", "JINDALSTEL.NS", "APLAPOLLO.NS",
        "TORNTPHARM.NS", "AUROPHARMA.NS", "ALKEM.NS", "LAURUSLABS.NS",
        "BIOCON.NS", "ZYDUSLIFE.NS", "GLENMARK.NS", "IPCALAB.NS",
        "MAXHEALTH.NS", "ABFRL.NS", "TATACONSUM.NS",
    ],
    "small": [
        "ZOMATO.NS", "NYKAA.NS", "PAYTM.NS", "POLICYBZR.NS", "CARTRADE.NS",
        "EASEMYTRIP.NS", "DELHIVERY.NS", "LATENTVIEW.NS", "TANLA.NS",
        "CDSL.NS", "MCX.NS", "IEX.NS", "BSE.NS", "ANGELONE.NS",
        "SBFCFIN.NS", "KFINTECH.NS", "RATEGAIN.NS", "TBOBDK.NS",
        "AFFLE.NS", "INDIAMART.NS", "NAUKRI.NS", "JUSTDIAL.NS",
        "NEWGEN.NS", "CEINFO.NS", "INTELLECT.NS",
    ],
}

_DISCOVER_CAP_TYPES = ("large", "mid", "small", "all")

# Background discover run state + per-(cap_type, date) results cache
# (mirrors the _scan_state pattern: the pipeline takes minutes, so it runs in
# a daemon thread and the UI polls /api/discover/status).
_discover_lock = threading.Lock()
_discover_state = {
    "running": False,
    "cap_type": None,
    "progress": 0,
    "total": 0,
    "current_symbol": "",
    "started_at": None,
    "finished_at": None,
    "error": None,
}
_discover_cache: dict = {}   # (cap_type, "YYYY-MM-DD") -> results payload


def _discover_symbols(cap_type: str) -> list[str]:
    if cap_type == "all":
        return (DISCOVER_UNIVERSE["large"][:6] + DISCOVER_UNIVERSE["mid"][:4]
                + DISCOVER_UNIVERSE["small"][:3])
    return DISCOVER_UNIVERSE[cap_type][:10]


def _discover_worker(cap_type: str, symbols: list[str]):
    """Run the agent council on each symbol in the background, then cache."""
    global _discover_state
    # Reset under the lock so a status poll between start() and this line
    # never sees the previous run's progress with running=True.
    with _discover_lock:
        _discover_state.update({
            "running": True,
            "cap_type": cap_type,
            "progress": 0,
            "total": len(symbols),
            "current_symbol": "",
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "finished_at": None,
            "error": None,
        })
    try:
        from agents.portfolio_manager import PortfolioManager
        pm = PortfolioManager()

        results = []
        for i, sym in enumerate(symbols, 1):
            _discover_state["current_symbol"] = sym
            _discover_state["progress"] = i
            try:
                analysis = pm.analyze(sym)
                results.append({
                    "symbol": sym,
                    "score": analysis["final_score"],
                    "rating": analysis["rating"],
                    "scores": analysis["scores"],
                    "recommendation": analysis["recommendation"],
                })
            except Exception as e:
                results.append({
                    "symbol": sym,
                    "score": 0,
                    "rating": "ERROR",
                    "error": str(e),
                })

        # Sort by score descending
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        today = datetime.now().strftime("%Y-%m-%d")
        payload = {
            "cap_type": cap_type,
            "count": len(results),
            "stocks": results,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }
        with _discover_lock:
            # Drop stale (previous-day) entries so the cache stays small.
            for key in [k for k in _discover_cache if k[1] != today]:
                _discover_cache.pop(key, None)
            _discover_cache[(cap_type, today)] = payload
        _discover_state["finished_at"] = datetime.now().isoformat(timespec="seconds")
    except Exception as e:
        _discover_state["error"] = str(e)
    finally:
        _discover_state["running"] = False


@app.route("/api/discover/start", methods=["POST"])
def api_discover_start():
    """Kick off a background discover run for one cap_type."""
    cap_type = (request.args.get("cap_type")
                or (request.get_json(silent=True) or {}).get("cap_type")
                or "large")
    if cap_type not in _DISCOVER_CAP_TYPES:
        return jsonify({"error": f"invalid cap_type: {cap_type}"}), 400

    with _discover_lock:
        if _discover_state["running"]:
            return jsonify({"status": "already_running",
                            "cap_type": _discover_state["cap_type"],
                            "progress": _discover_state["progress"],
                            "total": _discover_state["total"]})
        _discover_state["running"] = True
        _discover_state["cap_type"] = cap_type

    try:
        symbols = _discover_symbols(cap_type)
        thread = threading.Thread(target=_discover_worker,
                                  args=(cap_type, symbols), daemon=True)
        thread.start()
    except Exception:
        _discover_state["running"] = False
        raise
    return jsonify({"status": "started", "cap_type": cap_type,
                    "total": len(symbols)})


@app.route("/api/discover/status")
def api_discover_status():
    """Poll the discover run progress."""
    return jsonify(dict(_discover_state))


@app.route("/api/discover/<cap_type>")
def api_discover(cap_type: str):
    """Return today's cached discover results for a cap type.

    cap_type: 'large', 'mid', 'small', or 'all'
    Returns the ranked stocks if a run finished today, else 202 telling the
    caller to POST /api/discover/start and poll /api/discover/status.
    """
    if cap_type not in _DISCOVER_CAP_TYPES:
        return jsonify({"error": f"invalid cap_type: {cap_type}"}), 400

    today = datetime.now().strftime("%Y-%m-%d")
    with _discover_lock:
        cached = _discover_cache.get((cap_type, today))
    if cached:
        return jsonify(cached)
    return jsonify({"status": "run /api/discover/start first",
                    "cap_type": cap_type,
                    "running": _discover_state["running"]}), 202


# =========================================================================== #
#  News ingestion (background) + stats
# =========================================================================== #
_news_lock = threading.Lock()
_news_state = {
    "running": False,
    "last_run_at": None,
    "last_result": None,
    "error": None,
}


def _news_refresh_worker(limit: int):
    global _news_state
    _news_state["running"] = True
    _news_state["error"] = None
    try:
        import ingest_news
        summary = ingest_news.run(limit=limit)
        _news_state["last_result"] = summary
        _news_state["last_run_at"] = datetime.now().isoformat(timespec="seconds")
    except Exception as e:
        _news_state["error"] = str(e)
    finally:
        _news_state["running"] = False


@app.route("/api/news/refresh", methods=["POST"])
def api_news_refresh():
    """Kick off a background news ingest and return immediately."""
    with _news_lock:
        if _news_state["running"]:
            return jsonify({"status": "already_running"})
        _news_state["running"] = True
    try:
        data = request.get_json(silent=True) or {}
        try:
            limit = int(data.get("limit", 100))
        except (TypeError, ValueError):
            limit = 100
        limit = max(1, min(500, limit))
        t = threading.Thread(target=_news_refresh_worker, args=(limit,), daemon=True)
        t.start()
    except Exception:
        _news_state["running"] = False
        raise
    return jsonify({"status": "started", "limit": limit})


@app.route("/api/news/stats")
def api_news_stats():
    """Return the count of docs in news_archive plus the 5 most recent."""
    try:
        import ingest_news
        stats = ingest_news.get_stats(5)
        return jsonify({
            "count":       stats["count"],
            "recent":      stats["recent"],
            "running":     _news_state["running"],
            "last_run_at": _news_state["last_run_at"],
            "last_error":  _news_state["error"],
        })
    except Exception as e:
        return jsonify({"error": str(e), "count": 0, "recent": []}), 500


# =========================================================================== #
#  FinBERT sentiment (news_archive)
# =========================================================================== #
_sentiment_state = {"running": False, "last_run_at": None, "last_result": None,
                    "error": None}


def _sentiment_score_worker(limit):
    _sentiment_state["running"] = True
    _sentiment_state["error"] = None
    try:
        from advisor.score_news import score_all
        result = score_all(limit=limit)
        _sentiment_state["last_result"] = result
        _sentiment_state["last_run_at"] = datetime.now().isoformat(timespec="seconds")
    except Exception as e:
        _sentiment_state["error"] = str(e)
    finally:
        _sentiment_state["running"] = False


def _parse_age(default: int = 14) -> int:
    try:
        return max(1, min(3650, int(request.args.get("age_days", default))))
    except (TypeError, ValueError):
        return default


@app.route("/api/sentiment/<symbol>")
def api_sentiment_symbol(symbol: str):
    """Return the aggregate FinBERT sentiment for one symbol."""
    try:
        from advisor.news_agg import sentiment_for_symbol
        return jsonify(sentiment_for_symbol(symbol, max_age_days=_parse_age()))
    except Exception as e:
        return jsonify({"symbol": symbol, "error": str(e),
                        "mean_score": 0.0, "headline_count": 0}), 500


@app.route("/api/sentiment/batch")
def api_sentiment_batch():
    """Return aggregate sentiment for many symbols in one call.

    Query: /api/sentiment/batch?symbols=RELIANCE,TCS,INFY[&age_days=14]
    """
    try:
        from advisor.news_agg import sentiment_for_symbols
        raw = request.args.get("symbols", "") or ""
        syms = [s.strip() for s in raw.split(",") if s.strip()]
        out = sentiment_for_symbols(syms, max_age_days=_parse_age())
        return jsonify({"sentiment": out, "count": len(out)})
    except Exception as e:
        return jsonify({"error": str(e), "sentiment": {}}), 500


@app.route("/api/sentiment/score", methods=["POST"])
def api_sentiment_score():
    """Kick off a background FinBERT scoring pass over news_archive."""
    if _sentiment_state["running"]:
        return jsonify({"status": "already_running"})
    try:
        limit = int((request.get_json(silent=True) or {}).get("limit", 0)) or None
    except (TypeError, ValueError):
        limit = None
    t = threading.Thread(target=_sentiment_score_worker, args=(limit,), daemon=True)
    t.start()
    return jsonify({"status": "started", "limit": limit})


@app.route("/api/sentiment/status")
def api_sentiment_status():
    return jsonify(_sentiment_state)


# =========================================================================== #
#  RAG collections (patterns, filings, earnings) - background refresh + stats
# =========================================================================== #
_rag_lock = threading.Lock()
_rag_state = {
    "running": {},          # kind -> bool
    "last_run_at": {},      # kind -> iso timestamp
    "last_result": {},      # kind -> summary dict
    "error": {},            # kind -> str
}


def _rag_refresh_worker(kind: str, limit: int):
    _rag_state["running"][kind] = True
    _rag_state["error"][kind] = None
    try:
        import ingest_rag
        if kind == "patterns":
            result = ingest_rag.ingest_patterns()
        elif kind == "filings":
            result = ingest_rag.ingest_filings(limit=limit)
        elif kind == "earnings":
            result = ingest_rag.ingest_earnings()
        elif kind == "all":
            result = ingest_rag.ingest_all(limit=limit)
        else:
            raise ValueError(f"unknown kind: {kind}")
        _rag_state["last_result"][kind] = result
        _rag_state["last_run_at"][kind] = datetime.now().isoformat(timespec="seconds")
    except Exception as e:
        _rag_state["error"][kind] = str(e)
    finally:
        _rag_state["running"][kind] = False


@app.route("/api/rag/refresh", methods=["POST"])
def api_rag_refresh():
    """Kick off a background RAG ingest and return immediately.

    Accepts kind via query string (?kind=patterns) or JSON body.
    """
    kind = (request.args.get("kind")
            or (request.get_json(silent=True) or {}).get("kind")
            or "all")
    if kind not in ("patterns", "filings", "earnings", "all"):
        return jsonify({"status": "error", "error": f"invalid kind: {kind}"}), 400
    with _rag_lock:
        if _rag_state["running"].get(kind):
            return jsonify({"status": "already_running", "kind": kind})
        _rag_state["running"][kind] = True
    try:
        try:
            limit = int((request.get_json(silent=True) or {}).get("limit", 100))
        except (TypeError, ValueError):
            limit = 100
        limit = max(1, min(500, limit))
        t = threading.Thread(target=_rag_refresh_worker, args=(kind, limit), daemon=True)
        t.start()
    except Exception:
        _rag_state["running"][kind] = False
        raise
    return jsonify({"status": "started", "kind": kind, "limit": limit})


@app.route("/api/rag/stats")
def api_rag_stats():
    """Return doc counts across the RAG collections."""
    try:
        from data_warehouse import get_warehouse
        dw = get_warehouse()
        stats = dw.stats()
        return jsonify({
            "collections": {
                "news_archive":    stats.get("news_archive", 0),
                "investor_wisdom": stats.get("investor_wisdom", 0),
                "pattern_library": stats.get("pattern_library", 0),
                "filings":         stats.get("filings", 0),
                "earnings_calls":  stats.get("earnings_calls", 0),
            },
            "running":     _rag_state["running"],
            "last_run_at": _rag_state["last_run_at"],
            "last_error":  _rag_state["error"],
        })
    except Exception as e:
        return jsonify({"error": str(e), "collections": {}}), 500


@app.route("/api/explain/<symbol>")
def api_explain(symbol: str):
    """Generate a full 'why buy' explanation for a stock."""
    try:
        from explanation_engine import explain_stock
        result = explain_stock(symbol)
        return jsonify({
            "symbol": result["symbol"],
            "score": result["score"],
            "rating": result["rating"],
            "narrative": result["narrative"],
            "key_reasons": result["key_reasons"],
            "risks": result["risks"],
            "recommendation": result["recommendation"],
        })
    except Exception as e:
        app.logger.exception("explain failed for %s", symbol)
        return jsonify({"error": str(e)}), 500


# =========================================================================== #
#  Background scan worker
# =========================================================================== #
def _scan_worker(symbols: list[str]):
    """Run the scan in a background thread, updating _scan_state as it goes."""
    global _scan_state
    _scan_state.update({
        "running": True,
        "progress": 0,
        "total": len(symbols),
        "current_symbol": "",
        "completed": 0,
        "failures": [],
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "finished_at": None,
        "error": None,
    })

    try:
        settings = get_settings()
        source = get_source(settings.data_source, exchange=settings.exchange,
                            directory=settings.csv_dir)
        agent = Analyzer(settings, source=source, journal=Journal(JOURNAL_DB))
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().isoformat(timespec="seconds")
        prefs = load_prefs()
        style = style_for(prefs.get("hold_days", 5))

        for i, sym in enumerate(symbols, 1):
            _scan_state["current_symbol"] = sym
            _scan_state["progress"] = i
            try:
                idea = agent.analyze(sym, style=style, use_llm=False, use_news=False)
                plan = idea.plan
                with closing(get_scan_db()) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO scan_results
                        (symbol, scan_date, scan_time, verdict, direction, confidence,
                         confluence, regime, entry, stop_loss, target, risk_reward,
                         quantity, rupees_at_risk, position_value, narration, signals_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        idea.symbol, today, now, idea.verdict.value, idea.direction.value,
                        idea.confidence, idea.confluence_score, idea.regime.value,
                        plan.entry if plan else None, plan.stop_loss if plan else None,
                        plan.target if plan else None,
                        plan.risk_reward if plan else None,
                        plan.quantity if plan else None,
                        plan.rupees_at_risk if plan else None,
                        plan.position_value if plan else None,
                        idea.narration, len(idea.signals),
                    ))
                    conn.commit()
                _scan_state["completed"] = i
            except Exception as e:
                _scan_state["failures"].append({"symbol": sym, "error": str(e)})

            # Throttle to avoid Yahoo rate limits
            if settings.data_source == "yfinance" and i < len(symbols):
                time.sleep(settings.scan_delay_sec)

        _scan_state["finished_at"] = datetime.now().isoformat(timespec="seconds")

        # Push a Telegram digest of today's TAKE setups (if configured).
        try:
            notifier = TelegramNotifier()
            if notifier.is_configured():
                with closing(get_scan_db()) as conn:
                    rows = conn.execute(
                        "SELECT * FROM scan_results WHERE scan_date = ? "
                        "AND verdict = 'TAKE' ORDER BY confidence DESC",
                        (today,)
                    ).fetchall()
                if rows:
                    notifier.send_digest([dict(r) for r in rows], prefs)
        except Exception as e:
            # Never let notification failures break the scan
            print(f"telegram digest skipped: {e}")
    except Exception as e:
        _scan_state["error"] = str(e)
    finally:
        _scan_state["running"] = False


# =========================================================================== #
#  Template filters
# =========================================================================== #
@app.template_filter("verdict_color")
def verdict_color(verdict):
    return {
        "TAKE": "green",
        "WATCH": "yellow",
        "AVOID": "red",
        "NO_SETUP": "gray",
    }.get(verdict, "gray")


@app.template_filter("direction_arrow")
def direction_arrow(direction):
    return {"long": "▲ LONG", "short": "▼ SHORT", "none": "— NONE"}.get(direction, "—")


@app.template_filter("fmt_price")
def fmt_price(val):
    if val is None:
        return "—"
    try:
        return f"₹{float(val):,.2f}"
    except (ValueError, TypeError):
        return "—"


@app.template_filter("fmt_pct")
def fmt_pct(val):
    if val is None:
        return "—"
    try:
        return f"{float(val):.1f}%"
    except (ValueError, TypeError):
        return "—"


@app.template_filter("fmt_int")
def fmt_int(val):
    if val is None:
        return "—"
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return "—"


# =========================================================================== #
#  Main
# =========================================================================== #
if __name__ == "__main__":
    init_scan_db()
    # Also init the journal DB
    Journal(JOURNAL_DB)
    # Safe defaults: no Werkzeug debugger, localhost only.
    # Set ADVISOR_DEBUG=1 to enable debug mode; ADVISOR_HOST=0.0.0.0 to expose
    # on the LAN (use a real WSGI server like waitress/gunicorn for that).
    debug = os.getenv("ADVISOR_DEBUG") == "1"
    host = os.getenv("ADVISOR_HOST", "127.0.0.1")
    print("\n" + "=" * 60)
    print("  advisor Web Interface")
    print("  Open http://localhost:5000 in your browser")
    print("  Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    app.run(debug=debug, host=host, port=5000)
