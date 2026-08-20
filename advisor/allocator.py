"""
allocator.py - Portfolio allocation via Hierarchical Risk Parity (HRP).

Given today's TAKE picks, this module computes how much of the trader's
capital should sit in each name so that a single sector move can't sink
the whole book. Uses PyPortfolioOpt's HRPOpt, which builds a covariance
tree from 60-day return co-movements and splits capital along the
dendrogram.

Public API:
    fetch_returns(symbols, lookback_days) -> DataFrame
    hrp_weights(returns)                  -> Series
    equal_weights(symbols)                -> Series
    allocate(symbols, capital, lookback)  -> dict

Everything else in this file is a private helper. The webapp only ever
calls `allocate()`.
"""
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd

# yfinance is already a project dependency.
import yfinance as yf

# PyPortfolioOpt gives us HRP for free — do not hand-roll it.
from pypfopt.hierarchical_portfolio import HRPOpt


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #
def _yf_symbol(symbol: str) -> str:
    """Append .NS if the symbol has no exchange suffix (matches yfinance NSE)."""
    s = symbol.strip().upper()
    if "." in s:
        return s
    return f"{s}.NS"


def _base_symbol(symbol: str) -> str:
    """Strip any .NS / .BO suffix so the payload keys stay tidy for the UI."""
    return symbol.split(".")[0]


# --------------------------------------------------------------------------- #
#  Data
# --------------------------------------------------------------------------- #
def fetch_returns(symbols: list[str], lookback_days: int = 60) -> pd.DataFrame:
    """Daily close-to-close returns for `symbols` over the last `lookback_days`.

    Returned frame is indexed by trading date, one column per input symbol
    (base symbol, .NS stripped). Rows with any NaN are dropped so the
    covariance matrix is well-defined.

    Symbols that yfinance can't resolve are silently omitted from the frame;
    callers should compare `frame.columns` against the input list to detect
    drops.
    """
    if not symbols:
        return pd.DataFrame()

    # Give ourselves headroom — yfinance's calendar excludes weekends/holidays,
    # so 60 calendar days ~ 42 trading days. Ask for 2x + a buffer.
    period_days = max(30, int(lookback_days * 2) + 10)

    yf_syms = [_yf_symbol(s) for s in symbols]
    base_map = {_yf_symbol(s): _base_symbol(s) for s in symbols}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        raw = yf.download(
            tickers=yf_syms,
            period=f"{period_days}d",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )

    if raw is None or len(raw) == 0:
        return pd.DataFrame()

    # yfinance returns a MultiIndex (ticker, field) when multiple tickers pass;
    # a single-level frame for a single ticker. Normalise both to a Close frame.
    closes: dict[str, pd.Series] = {}
    if isinstance(raw.columns, pd.MultiIndex):
        for sym in yf_syms:
            if sym in raw.columns.get_level_values(0):
                col = raw[sym].get("Close")
                if col is not None and col.dropna().size > 0:
                    closes[base_map[sym]] = col.dropna()
    else:
        # Single ticker
        col = raw.get("Close")
        if col is not None and col.dropna().size > 0:
            closes[base_map[yf_syms[0]]] = col.dropna()

    if not closes:
        return pd.DataFrame()

    price_df = pd.DataFrame(closes).sort_index()
    # Trim to the requested lookback window
    price_df = price_df.tail(lookback_days + 1)
    returns = price_df.pct_change().dropna(how="any")
    return returns


# --------------------------------------------------------------------------- #
#  Weight schemes
# --------------------------------------------------------------------------- #
def hrp_weights(returns: pd.DataFrame) -> pd.Series:
    """Hierarchical Risk Parity weights via PyPortfolioOpt.

    Weights sum to 1.0. Returns a Series indexed by column name.
    """
    if returns is None or returns.empty:
        raise ValueError("returns frame is empty")
    if returns.shape[1] < 2:
        raise ValueError("HRP needs at least 2 symbols")

    hrp = HRPOpt(returns=returns)
    weights = hrp.optimize()  # dict {symbol: weight}
    return pd.Series(weights, name="hrp_weight").reindex(returns.columns).fillna(0.0)


def equal_weights(symbols: list[str]) -> pd.Series:
    """Trivial 1/N baseline for comparison against HRP."""
    if not symbols:
        return pd.Series(dtype=float, name="equal_weight")
    w = 1.0 / len(symbols)
    return pd.Series({_base_symbol(s): w for s in symbols}, name="equal_weight")


# --------------------------------------------------------------------------- #
#  Orchestrator
# --------------------------------------------------------------------------- #
def allocate(
    symbols: list[str],
    capital: float,
    lookback_days: int = 60,
) -> dict:
    """Compute HRP + equal-weight allocations for `symbols` given `capital`.

    Payload shape is documented in the /portfolio route contract. Handles the
    three edge cases explicitly:
      * < 2 symbols                -> equal-weight only, HRP omitted, warning set.
      * some symbols fail to fetch -> reported in `dropped_symbols`.
      * < 20 bars of overlap       -> shrink lookback and warn.
    """
    symbols = [s for s in (symbols or []) if s]
    capital = float(capital or 0.0)

    payload: dict = {
        "symbols": [_base_symbol(s) for s in symbols],
        "hrp_weights": {},
        "hrp_amounts": {},
        "equal_amounts": {},
        "concentration_ratio": None,
        "diversification_ratio": None,
        "lookback_days": lookback_days,
        "bars_used": 0,
        "correlation_matrix": [],
        "correlation_labels": [],
        "dropped_symbols": [],
        "warning": None,
    }

    if len(symbols) < 2:
        eq = equal_weights(symbols)
        payload["equal_amounts"] = {k: round(float(v) * capital, 2) for k, v in eq.items()}
        payload["warning"] = (
            "Need at least 2 symbols to run HRP. Showing equal-weight only."
        )
        return payload

    # Fetch returns; if some symbols don't come back we still proceed with the rest.
    try:
        returns = fetch_returns(symbols, lookback_days=lookback_days)
    except Exception as e:
        payload["warning"] = f"Could not fetch price data: {e}"
        eq = equal_weights(symbols)
        payload["equal_amounts"] = {k: round(float(v) * capital, 2) for k, v in eq.items()}
        return payload

    requested = [_base_symbol(s) for s in symbols]
    got = list(returns.columns) if not returns.empty else []
    dropped = [s for s in requested if s not in got]
    payload["dropped_symbols"] = dropped

    if len(got) < 2:
        eq = equal_weights(symbols)
        payload["equal_amounts"] = {k: round(float(v) * capital, 2) for k, v in eq.items()}
        payload["warning"] = (
            f"Only {len(got)} symbol(s) had usable price history — HRP needs 2+. "
            "Falling back to equal weight."
        )
        return payload

    bars = int(len(returns))
    payload["bars_used"] = bars

    # If overlap is very short, HRP's covariance estimate is noise. Warn but
    # still compute — the alternative is a blank page, which is worse.
    short_history_warning: Optional[str] = None
    if bars < 20:
        short_history_warning = (
            f"Only {bars} overlapping bars of history — HRP weights are noisy at "
            "this sample size. Treat the output as directional, not exact."
        )

    # Recompute equal weight on the *surviving* set so the two schemes are
    # comparable and the amounts sum to the same capital.
    surviving = list(returns.columns)
    eq = equal_weights(surviving)
    payload["equal_amounts"] = {k: round(float(v) * capital, 2) for k, v in eq.items()}

    try:
        hrp = hrp_weights(returns)
    except Exception as e:
        payload["warning"] = f"HRP failed ({e}); falling back to equal weight."
        return payload

    # Normalise (HRPOpt already sums to 1.0, but round-trip safety)
    hrp = hrp / hrp.sum() if hrp.sum() > 0 else hrp

    payload["hrp_weights"] = {k: round(float(v), 4) for k, v in hrp.items()}
    payload["hrp_amounts"] = {k: round(float(v) * capital, 2) for k, v in hrp.items()}
    payload["concentration_ratio"] = round(float(hrp.max()), 4)
    # 1 - Herfindahl gives an "effective N" style diversification score in [0,1).
    payload["diversification_ratio"] = round(float(1.0 - (hrp ** 2).sum()), 4)

    # Correlation matrix for the heatmap — 2-decimal rounding keeps the JSON small.
    corr = returns.corr().round(2)
    payload["correlation_labels"] = list(corr.columns)
    payload["correlation_matrix"] = corr.values.tolist()

    warnings_list = []
    if short_history_warning:
        warnings_list.append(short_history_warning)
    if dropped:
        warnings_list.append(
            f"Dropped {len(dropped)} symbol(s) with no usable price history: "
            f"{', '.join(dropped)}."
        )
    if warnings_list:
        payload["warning"] = " ".join(warnings_list)

    return payload
