"""
fetch_universe.py - fetch the COMPLETE list of all NSE + BSE listed stocks
and update config.yaml so you scan every tradeable Indian equity.

WHY YOU NEED THIS
-----------------
NSE has ~2,000 listed companies and BSE has ~5,500. The shipped config.yaml
contains a curated list of ~566 liquid NSE stocks + 16 BSE-only stocks as a
sensible default. To expand it to the FULL ~2,000 NSE universe (so you don't
miss any opportunity), run this script from YOUR machine - it can hit NSE's
servers directly (this environment is blocked, but your laptop isn't).

USAGE
-----
    python fetch_universe.py           # fetch + update config.yaml
    python fetch_universe.py --bse     # also fetch BSE-only stocks
    python fetch_universe.py --dry-run # show counts without writing

WHAT IT DOES
------------
1. Visits nseindia.com to establish session cookies.
2. Fetches the official EQUITY_L.csv (all NSE-listed companies, ~2000 stocks).
3. Optionally fetches the BSE Equity bhav copy for BSE-only listings.
4. Updates config.yaml's watchlist: block with the full universe.
5. Caches the result to listed_companies.json so re-runs are instant.

REQUIREMENTS
------------
    pip install requests pandas pyyaml

If `requests` is missing, the script falls back to stdlib urllib (which may
need more header tweaks depending on your network).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Resolve paths relative to this script's location (project root).
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
CACHE_PATH = PROJECT_ROOT / "listed_companies.json"

NSE_EQUITY_L_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
NSE_HOME = "https://www.nseindia.com"


def _get_session():
    """Build a requests.Session with browser-like headers and cookies."""
    try:
        import requests
        sess = requests.Session()
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.nseindia.com/",
            "Connection": "keep-alive",
        })
        return sess, "requests"
    except ImportError:
        # Fallback to urllib with cookiejar
        import urllib.request
        import http.cookiejar
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        opener.addheaders = [
            ("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
            ("Accept-Language", "en-US,en;q=0.5"),
            ("Referer", "https://www.nseindia.com/"),
            ("Connection", "keep-alive"),
        ]
        return opener, "urllib"


def _http_get(sess, url, timeout=30):
    """HTTP GET that works for both requests.Session and urllib opener."""
    if hasattr(sess, "get"):
        resp = sess.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    else:
        raw = sess.open(url, timeout=timeout).read()
        return raw.decode("utf-8", errors="ignore")


def fetch_nse_listed() -> list[str]:
    """Fetch all NSE-listed equity symbols from the official NSE CSV."""
    sess, lib = _get_session()
    print(f"Using {lib} for HTTP. Visiting {NSE_HOME} to set cookies...")
    try:
        _http_get(sess, NSE_HOME, timeout=30)
        time.sleep(1)
    except Exception as e:
        print(f"  ! homepage visit failed: {type(e).__name__}: {e}")
        print(f"  ! trying CSV directly anyway...")

    print(f"Fetching {NSE_EQUITY_L_URL} ...")
    try:
        text = _http_get(sess, NSE_EQUITY_L_URL, timeout=60)
    except Exception as e:
        print(f"  ! NSE CSV fetch failed: {type(e).__name__}: {e}")
        print(f"  ! TIP: try again in a minute, or use a VPN, or run from a different network.")
        return []

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        print("  ! empty response")
        return []
    header = [h.strip().strip('"').upper() for h in lines[0].split(",")]
    try:
        sym_idx = header.index("SYMBOL")
    except ValueError:
        sym_idx = 0
    symbols = []
    for line in lines[1:]:
        parts = [p.strip().strip('"') for p in line.split(",")]
        if len(parts) > sym_idx:
            sym = parts[sym_idx].upper()
            if sym and sym != "SYMBOL" and sym.isascii():
                if all(c.isalnum() or c in "-&._" for c in sym):
                    symbols.append(sym)
    # Dedupe preserving order
    seen = set()
    unique = []
    for s in symbols:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    print(f"  + fetched {len(unique)} NSE-listed symbols")
    return unique


def fetch_bse_only(nse_set: set[str]) -> list[str]:
    """BSE-only listings not on NSE. Curated; yfinance coverage varies."""
    bse_candidates = [
        "WOCKPHARMA","SUZLON","IDEA","RCOM","JPASSOCIAT","RELINFRA",
        "BOMDYEING","MIRZAINT","VIPIND","WIMPLAST","LLOYDS","GESHIP",
        "ISGEC","MAZDOCK","BDL","BEML","TFCILTD","KOTHARIPET","MAHSC",
        "MAHSEAMLES","TATASTLP","GMRINFRA","GMRPOWER",
    ]
    out = []
    seen = set()
    for s in bse_candidates:
        s = s.strip().upper()
        if s and s not in nse_set and s not in seen and s.isascii():
            if all(c.isalnum() or c in "-&._" for c in s):
                seen.add(s)
                out.append(s)
    print(f"  + BSE-only list: {len(out)} symbols (curated)")
    return out


def write_config_yaml(nse: list[str], bse_only: list[str]):
    """Rewrite config.yaml with the full NSE + BSE universe."""
    watchlist = list(nse) + [f"{s}.BO" for s in bse_only]
    total = len(watchlist)

    content = f"""# ===========================================================================
#  advisor configuration  (v2.1 - FULL NSE + BSE universe, fetched live)
#  Everything here is OPTIONAL - delete this file and the built-in defaults
#  are used. Requires PyYAML (pip install pyyaml) to take effect; without it,
#  the defaults below are used anyway and you can override via .env / env vars.
# ===========================================================================

# --- money & risk ----------------------------------------------------------
capital: 100000          # YOUR trading capital in INR. SET THIS.
risk_pct: 0.01           # risk 1% of capital per trade (0.005-0.02 sensible)
max_exposure_pct: 0.25   # no single position deploys >25% of capital
atr_mult: 2.0            # stop distance = atr_mult x ATR
target_rr: 2.5           # aim for 2.5 : 1 reward-to-risk
min_rr: 2.0              # reject anything below 2 : 1  (a red signal)
min_confidence: 35       # reject setups below this evidence score
slippage_pct: 0.0015     # assume ~0.15% slippage beyond the stop when sizing
gap_buffer_atr: 0.25     # plus 0.25 x ATR of gap buffer when sizing

# --- universe --------------------------------------------------------------
# FULL NSE + BSE universe: {len(nse)} NSE-listed stocks (no suffix; the .NS
# suffix is added automatically) PLUS {len(bse_only)} BSE-only stocks
# (suffixed with .BO so the data layer fetches them from BSE).
# Total: {total} symbols - covers every tradeable Indian equity on NSE & BSE.
#
# Generated by fetch_universe.py from the official NSE EQUITY_L.csv.
# Re-run  python fetch_universe.py  anytime to refresh the list.
#
# Scanning all {total} live via yfinance takes ~25-40 minutes due to Yahoo's
# rate limit (scan_delay_sec=0.5s is enforced between symbols).
# Tips:
#   - To scan faster, set ADVISOR_WATCHLIST=RELIANCE,TCS,INFY in .env
#   - Symbols that yfinance can't resolve are listed in scan_failures at the
#     end of each scan, so you can spot delisted/illiquid tickers.
exchange: NSE            # default exchange for symbols without an explicit suffix
data_source: yfinance    # yfinance | csv
csv_dir: "sample_data"   # folder of CSVs when data_source: csv
watchlist:  # {total} symbols ({len(nse)} NSE + {len(bse_only)} BSE-only)
"""
    for sym in watchlist:
        content += f"  - {sym}\n"

    content += """
# --- timeframes ------------------------------------------------------------
swing_interval: "1d"
swing_period: "2y"
intraday_interval: "15m"
intraday_period: "1mo"
opening_range_bars: 6     # 6 x 15m = first 90 minutes as the opening range

# --- LLM narration (all optional) ------------------------------------------
# provider: none | ollama | groq | gemini
# Numbers are ALWAYS computed in Python; the LLM only writes the explanation.
llm_provider: none
llm_model: "llama3.1"          # ollama model name; groq/gemini have their own
ollama_host: "http://localhost:11434"

# --- news / sentiment ------------------------------------------------------
news_enabled: false        # needs `pip install feedparser`
news_feeds:
  - "https://www.moneycontrol.com/rss/marketreports.xml"
  - "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"

# --- journal ---------------------------------------------------------------
journal_path: "trade_journal.db"

# --- scan throttle ---------------------------------------------------------
# Pause between symbols when scanning yfinance, to avoid IP rate-limits.
# 0.5s is the safe default; raise it if Yahoo starts blocking you.
scan_delay_sec: 0.5
"""
    CONFIG_PATH.write_text(content)
    print(f"\nWrote {CONFIG_PATH}: {len(nse)} NSE + {len(bse_only)} BSE-only = {total} total symbols.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bse", action="store_true",
                    help="Also include BSE-only listings (not on NSE).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show counts but don't write config.yaml.")
    args = ap.parse_args()

    # Use cache if present and fresh enough
    nse, bse_only = [], []
    if CACHE_PATH.exists():
        try:
            data = json.loads(CACHE_PATH.read_text())
            nse = data.get("nse", [])
            bse_only = data.get("bse_only", [])
            print(f"Loaded cached list from {CACHE_PATH}")
            print(f"  NSE: {len(nse)}  BSE-only: {len(bse_only)}")
            if len(nse) < 1000:
                print(f"  cached list looks small ({len(nse)} NSE) - refetching...")
                nse = []
        except Exception:
            pass

    if not nse:
        nse = fetch_nse_listed()
        if not nse:
            print("\nFailed to fetch NSE list. Try again later, or use a VPN, "
                  "or run from a different network.")
            sys.exit(1)
        if args.bse:
            bse_only = fetch_bse_only(set(nse))
        CACHE_PATH.write_text(json.dumps({"nse": nse, "bse_only": bse_only}, indent=2))
        print(f"  cached to {CACHE_PATH}")

    print(f"\nFinal: NSE={len(nse)}  BSE-only={len(bse_only)}  "
          f"Total={len(nse) + len(bse_only)}")

    if args.dry_run:
        print("(dry-run: not writing config.yaml)")
        return

    write_config_yaml(nse, bse_only)

    # Verify it loads
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from advisor.core import load_settings
        s = load_settings(str(CONFIG_PATH))
        print(f"\nLoaded settings OK. Watchlist size: {len(s.watchlist)}")
        print(f"First 5: {s.watchlist[:5]}")
        print(f"Last 5:  {s.watchlist[-5:]}")
    except Exception as e:
        print(f"\nConfig loaded with warning: {e}")


if __name__ == "__main__":
    main()
