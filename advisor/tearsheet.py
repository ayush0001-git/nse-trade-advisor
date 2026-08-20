"""
advisor.tearsheet
=================
Convert the trade journal into an institutional-grade QuantStats HTML tearsheet.

Pipeline:
  1. Load CLOSED trades from the journal SQLite DB
  2. Build a daily equity curve starting from `starting_capital`, applying each
     trade's realized P&L on its exit date
  3. Derive a daily pct-change return series
  4. Hand the series to `quantstats.reports.html` with NIFTY (^NSEI) benchmark

The renderer degrades gracefully if the benchmark can't be fetched.
"""
from __future__ import annotations

# Force a headless matplotlib backend BEFORE quantstats imports pyplot,
# otherwise the server tries to open a GUI window and crashes.
import matplotlib
matplotlib.use("Agg")

import sqlite3
import warnings
from contextlib import closing
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def _parse_date(value: str | None) -> date | None:
    """Parse an ISO timestamp (with or without tz) into a naive date."""
    if not value:
        return None
    try:
        # datetime.fromisoformat handles the "+05:30" suffix stored by _now()
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        try:
            dt = datetime.strptime(value[:10], "%Y-%m-%d")
        except Exception:
            return None
    # Strip tz to keep the date index tz-naive (quantstats warns otherwise)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt.date()


def journal_to_returns(journal_db_path: str,
                        starting_capital: float = 100_000.0) -> pd.Series:
    """Build a daily-returns Series from closed trades in the journal.

    - Equity is anchored at `starting_capital` one day before the first
      trade's entry date, so the first day's P&L is kept as a return.
    - On each trade's exit date the P&L is added to equity (multiple trades on
      the same day are summed).
    - Non-trading days are forward-filled so the returns Series is dense.
    - Returns an empty Series when < 3 closed trades exist.
    """
    with closing(sqlite3.connect(journal_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT opened_at, exit_at, exit_price, pnl FROM trades "
            "WHERE status='closed'"
        ).fetchall()

    trades = []
    for r in rows:
        pnl = r["pnl"]
        exit_price = r["exit_price"]
        if pnl is None or exit_price is None:
            continue
        try:
            pnl_f = float(pnl)
        except (TypeError, ValueError):
            continue
        if pnl_f != pnl_f:  # NaN check
            continue
        entry_d = _parse_date(r["opened_at"])
        exit_d = _parse_date(r["exit_at"]) or _parse_date(r["opened_at"])
        if entry_d is None or exit_d is None:
            continue
        trades.append((entry_d, exit_d, pnl_f))

    if len(trades) < 3:
        return pd.Series(dtype=float)

    first_date = min(t[0] for t in trades)
    last_date = max(max(t[1] for t in trades), date.today())

    # Aggregate P&L by exit date
    daily_pnl: dict[date, float] = {}
    for _, exit_d, pnl_f in trades:
        daily_pnl[exit_d] = daily_pnl.get(exit_d, 0.0) + pnl_f

    # Anchor the equity curve one day BEFORE the first trade date so that
    # pct_change() keeps the first day's P&L as a return instead of absorbing
    # it into the base value.
    anchor_date = first_date - timedelta(days=1)
    idx = pd.date_range(start=anchor_date, end=last_date, freq="D", tz=None)
    equity = pd.Series(0.0, index=idx)
    equity.iloc[0] = starting_capital

    running = starting_capital
    for ts in idx:
        d = ts.date()
        if d in daily_pnl:
            running += daily_pnl[d]
        equity.loc[ts] = running

    returns = equity.pct_change().dropna()
    # Drop tz just in case
    if getattr(returns.index, "tz", None) is not None:
        returns.index = returns.index.tz_localize(None)
    returns.name = "strategy"
    return returns


def _fetch_benchmark(returns: pd.Series, symbol: str) -> pd.Series | None:
    """Fetch daily benchmark returns aligned to `returns`. None on any failure."""
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        start = returns.index.min().strftime("%Y-%m-%d")
        end = (returns.index.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        df = yf.Ticker(symbol).history(start=start, end=end, interval="1d",
                                        auto_adjust=True)
        if df is None or len(df) < 2:
            return None
        close = df["Close"].copy()
        if getattr(close.index, "tz", None) is not None:
            close.index = close.index.tz_localize(None)
        bench = close.pct_change().dropna()
        bench.name = symbol
        return bench
    except Exception:
        return None


def render_html_tearsheet(returns: pd.Series, out_path: Path,
                           benchmark_symbol: str = "^NSEI") -> dict:
    """Render a full QuantStats HTML tearsheet to `out_path`.

    Returns a dict describing what was done (trades days, benchmark status).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if returns.empty:
        raise ValueError("Not enough trade data to render a tearsheet "
                         "(need at least 3 closed trades).")

    # Late import so the module can be imported even if quantstats is missing.
    import quantstats as qs

    bench = _fetch_benchmark(returns, benchmark_symbol)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        qs.reports.html(
            returns,
            benchmark=bench,
            output=str(out_path),
            title="advisor . trade journal",
            download_filename=out_path.name,
        )

    return {
        "output": str(out_path),
        "days": int(len(returns)),
        "benchmark": benchmark_symbol if bench is not None else None,
        "benchmark_loaded": bench is not None,
    }
