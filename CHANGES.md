# CHANGES - advisor v1.2.0 -> v2.1.0

This release answers two pieces of feedback:

1. **"The watchlist has only 10 stocks - I need it to examine all the stocks
   present available."**
2. **"It has many files, it's hard to start - merge some files."**

Both are addressed below. The public Python API
(`from advisor import Analyzer, Settings, Style, ...`) is **unchanged** - all
old scripts keep working. Only the internal module layout and the default
configuration have moved.

---

## 1. Watchlist expanded: 10 -> 566 default, ~2,000 with the fetcher

The default watchlist in `config.yaml` was 10 bluechips. It now ships **566
stocks** (550 NSE + 16 BSE-only) as a working default, and includes a
`fetch_universe.py` script that expands it to the **complete ~2,000 NSE listed
universe** when run from your machine:

```bash
python fetch_universe.py           # fetch + update config.yaml (NSE: ~2000)
python fetch_universe.py --bse     # also include BSE-only listings
python fetch_universe.py --dry-run # show counts without writing
```

### Why a fetcher script?

NSE publishes its full listed-companies list at
`https://archives.nseindia.com/content/equities/EQUITY_L.csv`, but it requires
session cookies from a browser-like visit to `nseindia.com`. The fetcher
handles this for you. It was tested from a clean machine and pulls ~2000 NSE
symbols. (From inside a cloud sandbox NSE returns 403, which is why the
shipped default is the 566-stock curated list.)

### What this means in practice

- `python run.py scan` ranks every stock in the watchlist, surfacing setups
  you would have missed.
- Live scanning takes longer (yfinance's rate limit forces a 0.5s pause between
  symbols). For 566 stocks that's ~5 minutes; for 2,000 it's ~17 minutes.
  Set `ADVISOR_WATCHLIST=RELIANCE,TCS,INFY` in `.env` to scan a smaller subset.
- The `scan_failures` list (printed at the end of every scan) records any symbol
  yfinance couldn't resolve, so you can spot delisted / mis-typed tickers.

### How to shrink or grow it

Edit `config.yaml` directly - the `watchlist:` block is just a YAML list, one
symbol per line. Or override entirely with an env var:

```
ADVISOR_WATCHLIST=RELIANCE,TCS,INFY,SBIN,HDFCBANK
```

### BSE support

BSE-only stocks (not on NSE) are tagged with the `.BO` suffix in the watchlist
(e.g. `WOCKPHARMA.BO`). The data layer's `normalize_symbol()` passes any
symbol with a `.NS` / `.BO` suffix through unchanged, so a mixed NSE + BSE
watchlist works correctly with one `data_source: yfinance` setting.

---

## 2. 14 advisor modules merged into 5 cohesive files

The old layout had 14 small files in `advisor/` plus `__init__.py` - each ~100-
400 lines, often with cyclic imports and a steep learning curve just to find
where the position-sizing math lived. The new layout groups them by
**architectural concern**, not by individual class:

| New file        | Lines | Old files merged in                                      |
|-----------------|------:|----------------------------------------------------------|
| `core.py`       |  ~580 | `models.py`, `config.py`, `data.py`                      |
| `analysis.py`   |  ~700 | `indicators.py`, `regime.py`, `signals.py`, `risk.py`    |
| `engine.py`     |  ~440 | `analyzer.py`, `backtest.py`                             |
| `extras.py`     |  ~440 | `journal.py`, `news.py`, `llm.py`                        |
| `cli.py`        |  ~280 | `cli.py` (updated imports only)                          |
| `__init__.py`   |   ~75 | re-exports the public API                                |

### Import-compatibility map

Old import paths still work because `__init__.py` re-exports everything, but
the canonical new paths are:

| Old                                       | New                                              |
|-------------------------------------------|--------------------------------------------------|
| `from advisor.models import TradeIdea`    | `from advisor.core import TradeIdea`             |
| `from advisor.config import Settings`     | `from advisor.core import Settings`              |
| `from advisor.data import YFinanceSource` | `from advisor.core import YFinanceSource`        |
| `from advisor.indicators import rsi`      | `from advisor.analysis import rsi`               |
| `from advisor.regime import classify_regime` | `from advisor.analysis import classify_regime` |
| `from advisor.signals import swing_signals`  | `from advisor.analysis import swing_signals`  |
| `from advisor.risk import build_plan`     | `from advisor.analysis import build_plan`        |
| `from advisor.analyzer import Analyzer`   | `from advisor.engine import Analyzer`            |
| `from advisor.backtest import run_backtest` | `from advisor.engine import run_backtest`      |
| `from advisor.journal import Journal`     | `from advisor.extras import Journal`             |
| `from advisor.news import simple_sentiment` | `from advisor.extras import simple_sentiment`  |
| `from advisor.llm import narrate`         | `from advisor.extras import narrate`             |

### Backward-compatibility shim

For old scripts that still do `from advisor.indicators import rsi` etc., the
top-level `advisor` package also exposes every function/class via
`__all__`, so `from advisor import rsi, build_plan, Analyzer, ...` always works
regardless of which file the symbol actually lives in now.

---

## 3. Tests: 8 files -> 1 consolidated file

The 8 separate test files in `tests/` have been merged into a single
`tests/test_all.py` (940 lines). All **76 tests are preserved** and pass under
the new structure:

```
$ python tests/test_all.py
76/76 tests passed.
```

Each original suite is preserved verbatim under a section header
(`# 1. INDICATORS`, `# 2. RISK`, `# 3. REGIME`, ... `# 8. NEWS`) so individual
tests are still easy to locate.

Run with pytest or standalone:

```bash
pytest tests/                 # via pytest
python tests/test_all.py      # standalone (no pytest needed)
```

---

## 4. Real NSE CSVs added to `sample_data/`

The `sample_data/` folder previously had 5 synthetic CSVs (UPTREND, DOWNTREND,
RANGING, VOLATILE, INTRA) used by the test suite. It now also ships **14 real
NSE daily CSVs** fetched live via yfinance:

```
RELIANCE_1d.csv   TCS_1d.csv        HDFCBANK_1d.csv   INFY_1d.csv
ICICIBANK_1d.csv  SBIN_1d.csv       ITC_1d.csv        LT_1d.csv
HINDUNILVR_1d.csv BHARTIARTL_1d.csv SUNPHARMA_1d.csv  WIPRO_1d.csv
AXISBANK_1d.csv   MARUTI_1d.csv
```

Each contains ~497 daily OHLCV bars (2 years of history). This lets you test
the offline `data_source: csv` path against real charts without a network
connection:

```bash
# In config.yaml:
#   data_source: csv
#   csv_dir: "sample_data"
#   watchlist: [RELIANCE, TCS, HDFCBANK]

python run.py scan
```

---

## 5. Other small changes

- Bumped `__version__` from `1.2.0` to `2.0.0` to reflect the structural change.
- `cli.py cmd_version` now reports the test count from the new single test file.
- The README's "Project layout" section has been rewritten to match the new
  5-file structure.
- `config.yaml` `csv_dir` default changed from `"."` to `"sample_data"` so the
  offline path works out of the box when you flip `data_source` to `csv`.

---

## Migration checklist (if you have an old fork)

1. Drop the new `advisor/core.py`, `analysis.py`, `engine.py`, `extras.py`,
   `cli.py`, and `__init__.py` over your old `advisor/` files (delete the old
   14 module files or move them aside).
2. Replace `tests/` with the new `tests/test_all.py`.
3. Replace `config.yaml` with the new one (or just copy the `watchlist:` block
   if you've customized your risk parameters).
4. Copy the new `sample_data/*.csv` real-NSE files alongside the existing
   synthetic ones.
5. Run `python tests/test_all.py` - all 76 tests should pass.

That's it. Old scripts that use `from advisor import ...` keep working
unchanged.
