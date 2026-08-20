"""
advisor.extras
==============
The auxiliary layer - everything that's NOT part of the core analysis pipeline
but enhances it with real-world feedback loops:

  1. **Journal** - a dead-simple SQLite trade journal (stdlib only). Logs every
     idea you act on; once closed, computes the only stats that matter (win
     rate, avg win/loss in R, payoff ratio, EXPECTANCY, fractional-Kelly).
     These feed back into the analyzer so it shows your live edge, not a
     generic estimate, after ~30 closed trades.
  2. **News**    - lightweight RSS-sentiment over a finance keyword lexicon.
     `feedparser` is optional - if missing, news is skipped and the rest of
     the agent runs unaffected. Sentiment is an *input* to reasoning, never
     the deciding factor.
  3. **LLM**     - narration layer. CRITICAL DESIGN RULE: the LLM never
     produces a number; every price/size/probability is computed in Python
     and passed to the model as fixed facts. The model only *explains* them.
     Providers (all optional): "none" (template), "ollama", "groq", "gemini".
     Network calls use stdlib urllib only - fails safe to the template.
"""
from __future__ import annotations

import json
import re
import sqlite3
import urllib.request
import urllib.error
from contextlib import closing
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .core import Direction, TradeIdea, Verdict
from . import analysis as an


# =========================================================================== #
#  1.  JOURNAL
# =========================================================================== #
_SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol      TEXT    NOT NULL,
    style       TEXT    NOT NULL,
    direction   TEXT    NOT NULL,
    entry       REAL    NOT NULL,
    stop        REAL    NOT NULL,
    target      REAL    NOT NULL,
    quantity    INTEGER NOT NULL,
    risk_pct    REAL,
    confidence  REAL,
    opened_at   TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'open',   -- open | closed
    exit_price  REAL,
    exit_at     TEXT,
    outcome_r   REAL,
    pnl         REAL,           -- NET of estimated costs
    costs       REAL,           -- estimated round-trip costs deducted
    notes       TEXT
);
"""


class Journal:
    def __init__(self, path: str | Path = "trade_journal.db"):
        self.path = str(path)
        with closing(self._conn()) as c:
            c.execute(_SCHEMA)
            cols = {r["name"] for r in c.execute("PRAGMA table_info(trades)")}
            if "costs" not in cols:
                c.execute("ALTER TABLE trades ADD COLUMN costs REAL")
            c.commit()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    # -- writing -------------------------------------------------------- #
    def log_idea(self, idea: TradeIdea, notes: str = "") -> int:
        """Record a trade you are taking. Returns the new trade id."""
        if idea.plan is None:
            raise ValueError("Cannot log an idea without a position plan.")
        p = idea.plan
        with closing(self._conn()) as c:
            cur = c.execute(
                """INSERT INTO trades
                   (symbol, style, direction, entry, stop, target, quantity,
                    risk_pct, confidence, opened_at, status, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,'open',?)""",
                (idea.symbol, idea.style.value, idea.direction.value,
                 p.entry, p.stop_loss, p.target, p.quantity, p.risk_pct,
                 idea.confidence, _now(), notes),
            )
            c.commit()
            return int(cur.lastrowid)

    def close_trade(self, trade_id: int, exit_price: float, notes: str = "") -> dict:
        """Close a trade at exit_price and compute its R outcome + P&L."""
        with closing(self._conn()) as c:
            row = c.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
            if row is None:
                raise ValueError(f"No trade with id {trade_id}.")
            if row["status"] == "closed":
                raise ValueError(f"Trade {trade_id} is already closed.")

            entry, stop, qty = row["entry"], row["stop"], row["quantity"]
            direction = Direction(row["direction"])
            risk_per_share = abs(entry - stop)

            if direction == Direction.LONG:
                gross_pnl = (exit_price - entry) * qty
            else:
                gross_pnl = (entry - exit_price) * qty

            # Pick the cost model by the trade's style (intraday = lower STT/stamp).
            from .engine import CostModel
            cm = CostModel.intraday() if row["style"] == "intraday" else CostModel()
            costs = cm.entry_cost(entry * qty) + cm.exit_cost(exit_price * qty)
            net_pnl = gross_pnl - costs
            denom = risk_per_share * qty
            outcome_r = (net_pnl / denom) if denom else 0.0

            c.execute(
                """UPDATE trades SET status='closed', exit_price=?, exit_at=?,
                   outcome_r=?, pnl=?, costs=?, notes=COALESCE(NULLIF(?, ''), notes)
                   WHERE id=?""",
                (exit_price, _now(), round(outcome_r, 3), round(net_pnl, 2),
                 round(costs, 2), notes, trade_id),
            )
            c.commit()
            return {"id": trade_id, "outcome_r": round(outcome_r, 3),
                    "pnl": round(net_pnl, 2), "costs": round(costs, 2)}

    # -- reading -------------------------------------------------------- #
    def open_trades(self) -> list[dict]:
        with closing(self._conn()) as c:
            rows = c.execute(
                "SELECT * FROM trades WHERE status='open' ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def recent(self, n: int = 20) -> list[dict]:
        with closing(self._conn()) as c:
            rows = c.execute(
                "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (n,)).fetchall()
            return [dict(r) for r in rows]

    def stats(self) -> dict:
        """Compute the journal's edge metrics from CLOSED trades."""
        with closing(self._conn()) as c:
            rows = c.execute(
                "SELECT outcome_r, pnl FROM trades WHERE status='closed' "
                "AND outcome_r IS NOT NULL").fetchall()

        closed = [r["outcome_r"] for r in rows]
        n = len(closed)
        empty = {
            "closed_trades": 0, "win_rate": None, "avg_win_r": None,
            "avg_loss_r": None, "payoff_b": None, "expectancy_r": None,
            "total_pnl": round(sum(r["pnl"] or 0 for r in rows), 2),
            "kelly_quarter": None, "reliable": False,
            "sharpe": None, "deflated_sharpe": None, "dsr_verdict": None,
            "message": "No closed trades yet - take some trades and close them.",
        }
        if n == 0:
            return empty

        wins = [r for r in closed if r > 0]
        losses = [r for r in closed if r <= 0]
        win_rate = len(wins) / n
        avg_win_r = sum(wins) / len(wins) if wins else 0.0
        avg_loss_r = abs(sum(losses) / len(losses)) if losses else 0.0
        payoff_b = (avg_win_r / avg_loss_r) if avg_loss_r > 0 else float("inf")
        exp_r = an.expectancy_r(win_rate, avg_win_r, avg_loss_r if avg_loss_r else 1.0)
        kelly_q = (an.fractional_kelly(win_rate, payoff_b)
                   if payoff_b not in (0, float("inf")) else None)

        # Sharpe (per-trade, unannualized) and Deflated Sharpe Ratio.
        # DSR asks: given N trades, this variance, this skew/kurtosis, what is the
        # probability the observed Sharpe is NOT just luck? Lopez de Prado, 2014.
        sharpe, dsr, dsr_verdict = _sharpe_and_dsr(closed)

        return {
            "closed_trades": n,
            "win_rate": round(win_rate, 3),
            "avg_win_r": round(avg_win_r, 2),
            "avg_loss_r": round(avg_loss_r, 2),
            "payoff_b": round(payoff_b, 2) if payoff_b != float("inf") else None,
            "expectancy_r": round(exp_r, 3),
            "total_pnl": round(sum(r["pnl"] or 0 for r in rows), 2),
            "kelly_quarter": kelly_q,
            "reliable": n >= 30,
            "sharpe": round(sharpe, 2) if sharpe is not None else None,
            "deflated_sharpe": round(dsr, 3) if dsr is not None else None,
            "dsr_verdict": dsr_verdict,
            "message": (
                "Edge looks positive."
                if exp_r > 0 else
                "Expectancy is non-positive - refine the strategy before sizing up."
            ) + ("" if n >= 30 else f" (Only {n} trades - need ~30+ to trust this.)"),
        }


def _sharpe_and_dsr(returns: list[float]) -> tuple[float | None, float | None, str | None]:
    """Compute per-trade Sharpe and Deflated Sharpe Ratio (Lopez de Prado, 2014).

    DSR is a probability in [0, 1]. Interpret as: chance the observed Sharpe is
    NOT explainable by chance / non-normality. A high DSR (> 0.95) means the
    edge is likely real; a low one means you may just be lucky.
    """
    import math
    n = len(returns)
    if n < 2:
        return None, None, None
    import statistics
    mean = statistics.mean(returns)
    sd = statistics.pstdev(returns)
    if sd == 0:
        return None, None, None
    sharpe = mean / sd

    # Skewness and excess kurtosis (biased but fine for small samples)
    var = sd ** 2
    m3 = sum((x - mean) ** 3 for x in returns) / n
    m4 = sum((x - mean) ** 4 for x in returns) / n
    skew = m3 / (sd ** 3) if sd > 0 else 0.0
    excess_kurt = (m4 / (var ** 2)) - 3.0 if var > 0 else 0.0

    # Standard error of Sharpe under Lo (2002) / Mertens correction:
    # sigma_sr = sqrt((1 - skew*SR + (kurt-1)/4 * SR^2) / (n - 1))
    inner = 1.0 - skew * sharpe + ((excess_kurt + 2.0) / 4.0) * (sharpe ** 2)
    if inner <= 0 or n < 3:
        # Not enough data to deflate reliably
        return sharpe, None, "Too few trades (n < 3) to deflate."
    sigma_sr = math.sqrt(inner / (n - 1))

    # DSR = Phi( SR / sigma_sr ) - assumes null hypothesis SR* = 0
    # (i.e. no adjustment for multiple-testing benchmark — pure single-strategy DSR)
    z = sharpe / sigma_sr if sigma_sr > 0 else 0.0
    dsr = _phi(z)

    if dsr >= 0.95:
        verdict = "Likely real edge"
    elif dsr >= 0.75:
        verdict = "Promising - keep going"
    elif dsr >= 0.5:
        verdict = "Inconclusive - need more trades"
    else:
        verdict = "Likely just luck"
    return sharpe, dsr, verdict


def _phi(z: float) -> float:
    """Standard normal CDF via math.erf. No SciPy dependency."""
    import math
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _now() -> str:
    """Current time in IST (the market's timezone)."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).isoformat(timespec="seconds")


# =========================================================================== #
#  2.  NEWS  -  RSS headlines + keyword sentiment
# =========================================================================== #
_POSITIVE = {
    "surge", "jump", "soar", "rally", "gain", "gains", "rise", "rises", "up",
    "beat", "beats", "record", "high", "profit", "growth", "upgrade", "bullish",
    "outperform", "strong", "boost", "wins", "approval", "expansion", "buy",
}
_NEGATIVE = {
    "fall", "falls", "drop", "drops", "plunge", "slump", "decline", "down",
    "miss", "misses", "loss", "losses", "low", "weak", "downgrade", "bearish",
    "underperform", "cut", "cuts", "probe", "fraud", "ban", "default", "sell",
    "warning", "lawsuit", "fine", "slowdown", "crash", "selloff",
}

_NEGATORS = {"not", "no", "never", "without", "barely", "hardly", "fails", "failed",
             "isn", "aren", "wasn", "weren", "cannot", "lacks", "lacking"}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def simple_sentiment(text: str) -> float:
    """Sentiment score in [-1, +1] from the keyword lexicon, with negation handling."""
    toks = _tokenize(text)
    if not toks:
        return 0.0
    pos = neg = 0
    for i, t in enumerate(toks):
        is_pos = t in _POSITIVE
        is_neg = t in _NEGATIVE
        if not (is_pos or is_neg):
            continue
        window = toks[max(0, i - 2):i]
        negated = any(w in _NEGATORS for w in window)
        if negated:
            is_pos, is_neg = is_neg, is_pos
        pos += int(is_pos)
        neg += int(is_neg)
    if pos + neg == 0:
        return 0.0
    return round((pos - neg) / (pos + neg), 3)


def fetch_headlines(feeds: list[str], limit: int = 40) -> list[str]:
    """Fetch recent headlines across feeds. Returns [] if feedparser missing."""
    try:
        import feedparser  # optional
    except ImportError:
        return []

    titles: list[str] = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:limit]:
                title = getattr(entry, "title", "").strip()
                if title:
                    titles.append(title)
        except Exception:
            continue
    return titles


def mentions(headline: str, symbol: str) -> bool:
    """True if `headline` mentions `symbol` as a WHOLE WORD (word-bounded)."""
    key = symbol.split(".")[0].upper()
    return re.search(rf"\b{re.escape(key)}\b", headline, re.IGNORECASE) is not None


def sentiment_for_symbol(feeds: list[str], symbol: str,
                         limit: int = 60) -> tuple[float | None, list[str]]:
    """Aggregate sentiment for headlines that mention `symbol`."""
    headlines = fetch_headlines(feeds, limit=limit)
    if not headlines:
        return None, []

    matching = [h for h in headlines if mentions(h, symbol)]
    if not matching:
        return None, []

    scores = [simple_sentiment(h) for h in matching]
    mean = round(sum(scores) / len(scores), 3) if scores else 0.0
    return mean, matching[:8]


def market_sentiment(feeds: list[str], limit: int = 60) -> float | None:
    """Overall market mood from all recent headlines (broad context)."""
    headlines = fetch_headlines(feeds, limit=limit)
    if not headlines:
        return None
    scores = [simple_sentiment(h) for h in headlines]
    nonzero = [s for s in scores if s != 0.0]
    if not nonzero:
        return 0.0
    return round(sum(nonzero) / len(nonzero), 3)


# =========================================================================== #
#  3.  LLM  -  narration (template fallback always available)
# =========================================================================== #
SYSTEM_PROMPT = (
    "You are a disciplined trader with decades of experience on Indian equity "
    "markets (NSE/BSE). You are briefing a client on a single trade idea. All "
    "the numbers below are already calculated and FIXED - never change them or "
    "invent new ones. Write a concise, honest rationale (max ~170 words): the "
    "setup, the regime context, the strongest bullish and bearish points, the "
    "plan, and the single biggest risk. If the verdict is AVOID or there are red "
    "signals, lead with that. Never promise profit; speak in probabilities. No "
    "markdown headers, no bullet lists - just a couple of tight paragraphs."
)


def narrate(idea: TradeIdea, provider: str = "none", model: str = "llama3.1",
            *, ollama_host: str = "http://localhost:11434",
            groq_api_key: str | None = None,
            gemini_api_key: str | None = None,
            timeout: int = 60) -> str:
    """Return a narration for the idea, falling back to a template on any error."""
    if provider == "none":
        return template_narration(idea)

    facts = _fact_sheet(idea)
    prompt = f"TRADE FACTS:\n{facts}\n\nWrite the briefing now."

    try:
        if provider == "ollama":
            return _ollama(prompt, model, ollama_host, timeout)
        if provider == "groq":
            return _groq(prompt, model, groq_api_key, timeout)
        if provider == "gemini":
            return _gemini(prompt, model, gemini_api_key, timeout)
    except Exception as e:  # network down, bad key, model missing, etc.
        return template_narration(idea) + f"\n\n(LLM narration unavailable: {e})"
    return template_narration(idea)


def _fact_sheet(idea: TradeIdea) -> str:
    lines = [
        f"Symbol: {idea.symbol}",
        f"Style: {idea.style.value}   Timeframe: {idea.timeframe}",
        f"Verdict: {idea.verdict.value}   Direction: {idea.direction.value}",
        f"Market regime: {idea.regime.value}",
        f"Confidence (0-100): {idea.confidence}",
        f"Confluence score (-1..+1): {idea.confluence_score}",
    ]
    if idea.plan:
        p = idea.plan
        lines += [
            f"Entry: {p.entry}  Stop: {p.stop_loss}  Target: {p.target}",
            f"Quantity: {p.quantity}  Risk:Reward: {p.risk_reward}",
            f"Rupees at risk: {p.rupees_at_risk}  Position value: {p.position_value}",
        ]
    if idea.bullish_signals:
        lines.append("Bullish points: " + "; ".join(s.note for s in idea.bullish_signals[:5]))
    if idea.bearish_signals:
        lines.append("Bearish points: " + "; ".join(s.note for s in idea.bearish_signals[:5]))
    if idea.hard_vetoes:
        lines.append("RED SIGNALS: " + "; ".join(v.reason for v in idea.hard_vetoes))
    if idea.scenarios:
        sc = "; ".join(f"{s.name} p={s.probability} -> {s.price_target}" for s in idea.scenarios)
        lines.append("Scenarios: " + sc)
    if idea.expectancy_r is not None:
        lines.append(f"Your historical expectancy (R/trade): {idea.expectancy_r}")
    if idea.news_sentiment is not None:
        lines.append(f"News sentiment (-1..+1): {idea.news_sentiment}")
    return "\n".join(lines)


def _post_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    headers = {"User-Agent": "advisor/2.1", "Accept": "application/json", **headers}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")[:200]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {body}") from e


def _ollama(prompt: str, model: str, host: str, timeout: int) -> str:
    out = _post_json(
        f"{host.rstrip('/')}/api/chat",
        {"model": model, "stream": False,
         "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": prompt}]},
        {"Content-Type": "application/json"},
        timeout,
    )
    msg = (out.get("message") or {}).get("content", "")
    return msg.strip() or "(empty response)"


def _groq(prompt: str, model: str, api_key: str | None, timeout: int) -> str:
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set.")
    model = model if "/" in model or "-" in model else "llama-3.3-70b-versatile"
    out = _post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        {"model": model,
         "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": prompt}],
         "temperature": 0.4, "max_tokens": 400},
        {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        timeout,
    )
    return out["choices"][0]["message"]["content"].strip()


def _gemini(prompt: str, model: str, api_key: str | None, timeout: int) -> str:
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set.")
    model = model if model.startswith("gemini") else "gemini-2.5-flash"
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    out = _post_json(
        url,
        {"contents": [{"parts": [{"text": prompt}]}]},
        {"Content-Type": "application/json", "x-goog-api-key": api_key},
        timeout,
    )
    return out["candidates"][0]["content"]["parts"][0]["text"].strip()


def template_narration(idea: TradeIdea) -> str:
    """A solid, hand-written narration built from the deterministic facts."""
    parts: list[str] = []

    if idea.verdict == Verdict.AVOID:
        parts.append(
            f"AVOID {idea.symbol} for now. " +
            ("Red signals: " + " ".join(v.reason for v in idea.hard_vetoes)
             if idea.hard_vetoes else
             "The evidence isn't clean enough to justify the risk.")
        )
    elif idea.verdict == Verdict.NO_SETUP:
        parts.append(
            f"No actionable setup on {idea.symbol} right now. The indicators are "
            f"mixed or the market is in a {idea.regime.value} regime that doesn't "
            f"favour a clear directional bet. Patience is a position."
        )
    elif idea.verdict == Verdict.WATCH:
        parts.append(
            f"Put {idea.symbol} on the watchlist. A {idea.direction.value} setup is "
            f"forming but not yet confirmed - wait for a trigger before committing."
        )
    else:  # TAKE
        side = "long" if idea.direction == Direction.LONG else "short"
        parts.append(
            f"{idea.symbol} is a {side} candidate. In a {idea.regime.value} regime, "
            f"the evidence lines up with confidence {idea.confidence:.0f}/100 "
            f"(confluence {idea.confluence_score:+.2f})."
        )

    if idea.bullish_signals:
        parts.append("For it: " + " ".join(s.note for s in idea.bullish_signals[:4]))
    if idea.bearish_signals:
        parts.append("Against it: " + " ".join(s.note for s in idea.bearish_signals[:4]))

    if idea.plan and idea.verdict in (Verdict.TAKE, Verdict.WATCH):
        p = idea.plan
        parts.append(
            f"Plan: enter near Rs.{p.entry}, stop at Rs.{p.stop_loss} "
            f"(risk Rs.{p.risk_per_share}/share), target Rs.{p.target} for a "
            f"{p.risk_reward:.1f}:1 reward-to-risk. Size {p.quantity} shares so a "
            f"stop-out costs about Rs.{p.rupees_at_risk:.0f} "
            f"({p.risk_pct*100:.1f}% of capital). That deploys "
            f"Rs.{p.position_value:.0f} ({p.position_pct_of_capital:.0f}% of capital)."
        )

    if idea.scenarios:
        bear = next((s for s in idea.scenarios if s.name == "bear"), None)
        if bear:
            parts.append(
                f"Biggest risk: roughly a {bear.probability*100:.0f}% chance the "
                f"thesis fails and the stop is hit (-1R). That is a normal, planned "
                f"outcome - the edge comes from many trades, not this one."
            )
    if idea.soft_veto_notes:
        parts.append("Cautions: " + " ".join(idea.soft_veto_notes))

    return "\n\n".join(parts)
