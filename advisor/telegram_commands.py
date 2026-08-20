"""
telegram_commands.py - long-poll Telegram bot for interactive commands.

Supported slash commands (only the configured chat_id may use them):
    /scan SYMBOL   - live single-stock analysis
    /status        - market open? latest scan? open trades?
    /today         - top-3 TAKE setups from today's scan
    /plan          - current user prefs
    /help          - command list

Run:
    python -m advisor.telegram_commands
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCAN_DB = str(PROJECT_ROOT / "scan_results.db")
JOURNAL_DB = str(PROJECT_ROOT / "trade_journal.db")
PREFS_PATH = PROJECT_ROOT / "user_prefs.json"


def _load_prefs() -> dict:
    if PREFS_PATH.exists():
        try:
            return json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _market_open() -> bool:
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    if ist.weekday() >= 5:
        return False
    hm = ist.hour * 60 + ist.minute
    return (9 * 60 + 15) <= hm <= (15 * 60 + 30)


def _fmt_row(row) -> str:
    d = dict(row) if not isinstance(row, dict) else row
    sym = d.get("symbol", "?")
    direction = (d.get("direction") or "").upper()
    arrow = "▲" if direction == "LONG" else ("▼" if direction == "SHORT" else "•")
    entry = d.get("entry"); stop = d.get("stop_loss"); tgt = d.get("target")
    rr = d.get("risk_reward"); qty = d.get("quantity")
    lines = [f"*{arrow} {sym}*  _(TAKE, {direction or '—'})_",
             f"Entry `{entry}`  Stop `{stop}`  Target `{tgt}`"]
    if isinstance(rr, (int, float)):
        lines.append(f"R:R `{rr:.2f}`  Qty `{int(qty or 0)}`")
    return "\n".join(lines)


def _authorized(update, allowed_chat_id: str) -> bool:
    try:
        cid = str(update.effective_chat.id)
    except Exception:
        return False
    return cid == str(allowed_chat_id)


def build_application():
    """Build the telegram.ext.Application with all handlers wired up.

    Returns None if env vars are missing so the caller can print a friendly
    message instead of crashing.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return None

    from telegram import Update
    from telegram.constants import ParseMode
    from telegram.ext import (
        Application, CommandHandler, ContextTypes, MessageHandler, filters,
    )

    async def cmd_help(update, ctx):
        if not _authorized(update, chat_id):
            return
        await update.message.reply_text(
            "*advisor bot commands*\n"
            "/scan SYMBOL — live analysis of one stock\n"
            "/today — top-3 TAKE setups from today's scan\n"
            "/status — market state + latest scan + open trades\n"
            "/plan — your current capital/risk plan\n"
            "/help — this message",
            parse_mode=ParseMode.MARKDOWN)

    async def cmd_status(update, ctx):
        if not _authorized(update, chat_id):
            return
        open_n = 0
        try:
            with closing(sqlite3.connect(JOURNAL_DB)) as c:
                cur = c.execute(
                    "SELECT COUNT(*) FROM trades WHERE status = 'open'")
                open_n = cur.fetchone()[0]
        except Exception:
            pass

        last_scan = "—"
        try:
            with closing(sqlite3.connect(SCAN_DB)) as c:
                cur = c.execute(
                    "SELECT MAX(scan_time) FROM scan_results")
                r = cur.fetchone()
                if r and r[0]:
                    last_scan = r[0]
        except Exception:
            pass

        await update.message.reply_text(
            f"*advisor status*\n"
            f"Market: {'🟢 OPEN' if _market_open() else '🔴 CLOSED'}\n"
            f"Latest scan: `{last_scan}`\n"
            f"Open trades: `{open_n}`",
            parse_mode=ParseMode.MARKDOWN)

    async def cmd_today(update, ctx):
        if not _authorized(update, chat_id):
            return
        today = datetime.now().strftime("%Y-%m-%d")
        rows = []
        try:
            with closing(sqlite3.connect(SCAN_DB)) as c:
                c.row_factory = sqlite3.Row
                rows = c.execute(
                    "SELECT * FROM scan_results WHERE scan_date = ? "
                    "AND verdict = 'TAKE' ORDER BY confidence DESC LIMIT 3",
                    (today,)).fetchall()
        except Exception as e:
            await update.message.reply_text(f"DB error: {e}")
            return
        if not rows:
            await update.message.reply_text("No TAKE setups today.")
            return
        blocks = ["*Top TAKE setups — today*"]
        for i, r in enumerate(rows, 1):
            blocks.append(f"\n*{i}.* " + _fmt_row(r))
        await update.message.reply_text("\n".join(blocks),
                                        parse_mode=ParseMode.MARKDOWN)

    async def cmd_plan(update, ctx):
        if not _authorized(update, chat_id):
            return
        p = _load_prefs()
        if not p:
            await update.message.reply_text("No plan saved yet. Open the "
                                            "dashboard to set one.")
            return
        cap = p.get("capital", 0)
        risk = p.get("risk_pct", 0)
        await update.message.reply_text(
            f"*Your plan*\n"
            f"Capital `₹{float(cap):,.0f}`\n"
            f"Risk per trade `{float(risk) * 100:.2f}%`\n"
            f"Daily target `₹{float(p.get('target_profit', 0)):,.0f}`\n"
            f"Holding days `{p.get('hold_days', '—')}`\n"
            f"Style `{p.get('style', '—')}`  Cash-only `{p.get('cash_only', True)}`",
            parse_mode=ParseMode.MARKDOWN)

    async def cmd_scan(update, ctx):
        if not _authorized(update, chat_id):
            return
        args = ctx.args
        if not args:
            await update.message.reply_text("Usage: /scan SYMBOL "
                                            "(e.g. /scan RELIANCE)")
            return
        symbol = args[0].strip().upper()
        await update.message.reply_text(f"Analyzing {symbol}…")
        try:
            from advisor.core import Style, load_settings, get_source
            from advisor.engine import Analyzer
            from advisor.extras import Journal
            settings = load_settings(str(PROJECT_ROOT / "config.yaml"))
            source = get_source(settings.data_source,
                                exchange=settings.exchange,
                                directory=settings.csv_dir)
            agent = Analyzer(settings, source=source,
                             journal=Journal(JOURNAL_DB))
            idea = agent.analyze(symbol, style=Style.SWING,
                                 use_llm=False, use_news=False)
        except Exception as e:
            await update.message.reply_text(
                f"Analysis failed: {type(e).__name__}: {e}")
            return

        plan = idea.plan
        lines = [
            f"*{idea.symbol}* — {idea.verdict.value} "
            f"({idea.direction.value.upper()})",
            f"Confidence `{idea.confidence:.0f}`  "
            f"Regime `{idea.regime.value}`",
        ]
        if plan:
            lines += [
                f"Entry `{plan.entry}`  Stop `{plan.stop_loss}`  "
                f"Target `{plan.target}`",
                f"R:R `{plan.risk_reward:.2f}`  Qty `{plan.quantity}`",
            ]
        await update.message.reply_text("\n".join(lines),
                                        parse_mode=ParseMode.MARKDOWN)

    async def ignore_unauthorized(update, ctx):
        # Silent drop for anyone who isn't the configured owner.
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("plan", cmd_plan))
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(MessageHandler(filters.ALL, ignore_unauthorized))
    return app


def _cli():
    try:
        from advisor.core import _load_dotenv
        _load_dotenv(Path(".env"))
    except Exception:
        pass

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    app = build_application()
    if app is None:
        print("Telegram not configured. Add TELEGRAM_BOT_TOKEN and "
              "TELEGRAM_CHAT_ID to your .env file.")
        sys.exit(2)

    print("advisor telegram bot: long-polling. Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    _cli()
