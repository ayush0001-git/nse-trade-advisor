"""
telegram_bot.py - one-way notifier for the advisor trading assistant.

Wraps the async python-telegram-bot library in a synchronous facade so the
Flask app and CLI can push notifications with a plain function call. If either
`TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is missing, everything degrades
silently (returns False, logs a friendly line) - no crashes.

Env vars (copy into `.env`):
    TELEGRAM_BOT_TOKEN=123456:ABC-DEF...          # from @BotFather
    TELEGRAM_CHAT_ID=123456789                    # your own chat id

CLI:
    python -m advisor.telegram_bot test
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine in a fresh event loop.

    On Windows, the Proactor loop is required for python-telegram-bot's
    networking. This helper creates + tears down its own loop so it is safe
    to call from any synchronous context (Flask request handlers, threads,
    CLI entry points).
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()


class TelegramNotifier:
    """Small synchronous wrapper around telegram.Bot for one-way alerts."""

    def __init__(self, bot_token: Optional[str] = None,
                 chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    def is_configured(self) -> bool:
        return bool(self.bot_token) and bool(self.chat_id)

    def send_message(self, text: str, markdown: bool = True) -> bool:
        """Send a plain message. Returns True on success, False otherwise.

        Never raises: bad token, wrong chat_id, or offline network all become
        a log line + False. That way callers can `if notifier.send(...)` and
        never worry about wrapping in try/except themselves.
        """
        if not self.is_configured():
            log.info("Telegram not configured (missing TELEGRAM_BOT_TOKEN or "
                     "TELEGRAM_CHAT_ID) - skipping notification.")
            return False

        try:
            from telegram import Bot
            from telegram.constants import ParseMode
        except ImportError:
            log.warning("python-telegram-bot not installed; skipping alert.")
            return False

        async def _send():
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN if markdown else None,
                disable_web_page_preview=True,
            )

        try:
            _run_async(_send())
            return True
        except Exception as e:
            log.warning("Telegram send_message failed: %s: %s",
                        type(e).__name__, e)
            return False

    # ------------------------------------------------------------------ #
    #  Formatters
    # ------------------------------------------------------------------ #
    @staticmethod
    def _fmt_row(row: dict) -> str:
        def g(k, default=None):
            try:
                return row[k]
            except (KeyError, IndexError, TypeError):
                return default

        symbol = g("symbol", "?")
        direction = (g("direction") or "").upper() or "—"
        entry = g("entry")
        stop = g("stop_loss")
        target = g("target")
        rr = g("risk_reward")
        qty = g("quantity") or 0
        conf = g("confidence")
        regime = g("regime") or "—"

        expected_profit = None
        if entry is not None and target is not None and qty:
            expected_profit = (float(target) - float(entry)) * int(qty)

        arrow = "▲" if direction == "LONG" else ("▼" if direction == "SHORT" else "•")
        lines = [
            f"*{arrow} {symbol}*  _(TAKE, {direction})_",
            f"Entry `{entry}`  Stop `{stop}`  Target `{target}`",
            f"R:R `{rr:.2f}`" if isinstance(rr, (int, float)) else "R:R —",
        ]
        if qty:
            lines.append(f"Qty `{int(qty)}`")
        if expected_profit is not None:
            lines.append(f"Expected profit ≈ ₹{expected_profit:,.0f}")
        if isinstance(conf, (int, float)):
            lines.append(f"Confidence `{conf:.0f}`  Regime `{regime}`")
        return "\n".join(lines)

    def send_take_alert(self, scan_row: dict) -> bool:
        """Format a single TAKE setup and send it."""
        try:
            body = self._fmt_row(scan_row)
        except Exception as e:
            log.warning("send_take_alert format failed: %s", e)
            return False
        return self.send_message("🚨 *New TAKE setup*\n\n" + body)

    def send_digest(self, scans: list, prefs: dict) -> bool:
        """Send a top-3 TAKE digest in one message."""
        takes = []
        for r in scans or []:
            v = None
            try:
                v = r["verdict"]
            except Exception:
                v = r.get("verdict") if isinstance(r, dict) else None
            if v == "TAKE":
                takes.append(r)

        if not takes:
            return self.send_message(
                "📋 *advisor digest*\nNo TAKE setups today. Sit tight.")

        top = takes[:3]
        target_profit = (prefs or {}).get("target_profit")
        header = "📋 *advisor digest — top TAKE setups*"
        if target_profit:
            header += f"\n_(daily target: ₹{float(target_profit):,.0f})_"

        blocks = [header]
        for i, r in enumerate(top, 1):
            blocks.append(f"\n*{i}.* " + self._fmt_row(r))
        return self.send_message("\n".join(blocks))


# ---------------------------------------------------------------------------- #
#  CLI: python -m advisor.telegram_bot test
# ---------------------------------------------------------------------------- #
def _cli():
    # Load .env the same way the rest of the codebase does
    try:
        from advisor.core import _load_dotenv
        _load_dotenv(Path(".env"))
    except Exception:
        pass

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    args = sys.argv[1:]
    if not args or args[0] not in ("test",):
        print("Usage: python -m advisor.telegram_bot test")
        sys.exit(1)

    n = TelegramNotifier()
    if not n.is_configured():
        missing = []
        if not n.bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not n.chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        print("Telegram not configured. Add these to your .env file:")
        for m in missing:
            print(f"  {m}=<your value>")
        sys.exit(2)

    ok = n.send_message("advisor: connection OK")
    if ok:
        print("Sent. Check your Telegram chat.")
    else:
        print("Send failed. Check the log above for the reason "
              "(bad token, wrong chat_id, or network).")
        sys.exit(3)


if __name__ == "__main__":
    _cli()
