# advisor — a local, advisory-only trading assistant for NSE/BSE

This is a personal trading assistant you run on your own PC. You give it a stock;
it analyses the chart like a careful, experienced trader and tells you what it
sees: a direction, an entry price, a stop-loss, a target, a position size matched
to your capital, the reward-to-risk, a confidence score, the likely scenarios,
and the **red signals** that say "don't take this trade."

It is **advisory only**. It never connects to your broker and never places an
order. You read its analysis and decide for yourself, then trade manually in
Groww (or wherever you trade). Think of it as a disciplined second opinion, not
an autopilot. *This is software, not investment advice.*

---

## Read this first: honest expectations

No trading system is "90% profitable." Anyone who tells you otherwise is selling
something. What actually makes money is **positive expectancy over many trades**
plus strict risk management. A system that wins 40% of the time at 2.5-to-1
reward-to-risk makes more money than one that wins 70% of the time at 1-to-1.

So this tool does **not** promise win rates. Instead it gives you:

- an **evidence score (0-100)** — an *ordinal ranking* of how clean a setup is,
  **not** a calibrated win probability. A 70 is "stronger evidence than a 55,"
  not "70% chance of profit." (True probability calibration would require
  backtesting across hundreds of real symbols; that's deliberately not faked.)
- the **reward-to-risk** of every setup, and it refuses trades below 2:1,
- **expectancy in R-multiples** once you've logged enough trades,
- **multi-scenario reasoning** (bull / base / bear, with rough probabilities),
- **red signals** that veto low-quality setups before you risk money.

The score demands real breadth: a single indicator can't push it high, and a
TAKE needs at least three independent signals agreeing plus a clean risk plan.
The real edge it gives you is consistency: it never skips the stop-loss, never
oversizes a position, and never lets you talk yourself into a 1:1 trade. Use the
backtester and paper-trade before risking a rupee.

---

## Methodology & accuracy notes

A few choices worth knowing so the numbers don't surprise you:

- **Indicators use exact Wilder smoothing** (the SMA-seeded recursion), so RSI,
  ATR, and ADX match what you see on TradingView/ChartIQ rather than drifting by
  a few points on early bars.
- **Signals are regime-aware.** A lower-Bollinger tag is a *buy* only in a range;
  in a downtrend it produces nothing (no catching a falling knife). Breakout
  signals are penalized in ranges, where breakouts most often fail. Bullish and
  bearish signals are symmetric (there are breakdown/52-week-low/resistance
  signals to mirror the bullish ones), so the engine isn't biased long.
- **Support/resistance zones are mutually exclusive.** "At/through the 20-day
  extreme" is a breakout/breakdown; "merely approaching it" is a range
  mean-reversion candidate - the two can't fire together and cancel each other.
  52-week-high/low signals only fire in the aligned trend, for the same reason.
- **Multi-timeframe alignment.** For swing setups the engine derives the weekly
  trend from your daily data (a moving-average stack on resampled bars) and adds
  it as a signal, so a daily setup that agrees with the weekly trend scores
  higher and one fighting it scores lower - one of the most robust edges in
  systematic trading. The backtester computes this per bar from the data
  available at that point, so it carries no look-ahead.
- **Volume isn't just decoration.** On-Balance Volume is turned into real signals:
  it confirms a move when OBV and price agree, and flags a divergence (an early
  warning) when price makes a new extreme that volume doesn't support.
- **Trend direction needs a real margin.** The regime classifier only calls a
  side when +DI and −DI are clearly separated; borderline cases report UNKNOWN
  instead of flip-flopping between TAKE and AVOID day to day.
- **Volatility detection is smoothed and persistence-gated**, so a single bad
  data point or one gap bar won't flip the whole read to "volatile."
- **The evidence score is a ranking, not a probability** (see above). Calibrating
  it to true win rates would need a large multi-symbol backtest study, which is
  left as honest future work rather than faked with hand-picked numbers.

---

## Setup

You need Python 3.10+ (developed on 3.12).

```bash
# 1) (optional) create a virtual environment
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 2) install dependencies
pip install -r requirements.txt

# 3) set your capital — copy the template and edit it
cp .env.example .env          # then set ADVISOR_CAPITAL, ADVISOR_RISK_PCT
#   (or edit config.yaml if you installed PyYAML)
```

The only hard dependencies are `pandas`, `numpy`, and `yfinance`. Everything
else is optional and the tool runs without it.

---

## Quick start

```bash
python run.py analyze RELIANCE            # deep-dive one stock (swing)
python run.py analyze TATAMOTORS --intraday
python run.py scan                        # rank your whole watchlist
python run.py backtest INFY               # validate the strategy on history
python run.py journal                     # your edge stats + open trades
python run.py log SBIN --note "ORB"       # log a trade you took
python run.py close 1 845.50              # close logged trade #1 at 845.50
python run.py news HDFCBANK               # headlines + sentiment
python run.py config                      # show active settings
```

### Web interface (dashboard in your browser)

For a visual dashboard with **today's trades**, **previous trades history**, and a
**P&L calculator**, run the Flask web app:

```bash
pip install flask                 # one-time
python webapp.py                  # then open http://localhost:5000
```

The dashboard has four sections:

1. **Today's Trades** — cards showing every TAKE / WATCH setup from the latest
   scan, with entry / stop / target / quantity / R:R / confidence.
2. **Previous & Open Trades** — table of trades you've logged in the journal
   (open positions in blue, closed P&L in green/red).
3. **P&L Calculator** — enter any symbol, quantity, and buy price; the app
   fetches the live price via yfinance and shows your unrealized P&L in
   rupees and percent, plus the advisor's current verdict on that stock.
4. **Stock Detail** (`/stock/SYMBOL`) — full analysis page for any stock:
   verdict, regime, indicators, the trade plan, all signals (for/against),
   bull/base/bear scenarios, red signals, analyst notes, and an inline
   P&L calculator. Includes a "Log This Trade" button.
5. **Run Scan** (`/scan`) — trigger a background scan of your watchlist with
   live progress bar. Results are cached in `scan_results.db` and shown on
   the dashboard.
6. **Trade History** (`/history`) — full journal with stats (win rate,
   expectancy, total P&L) and a form to close open trades at their exit price.

A symbol like `RELIANCE` is automatically mapped to Yahoo's `RELIANCE.NS` (NSE)
or `RELIANCE.BO` (BSE, if you set `exchange: BSE`). Indices: `NIFTY`, `BANKNIFTY`,
`SENSEX`. To mix NSE and BSE stocks in one watchlist, suffix BSE-only symbols
explicitly (e.g. `WOCKPHARMA.BO`) — the data layer passes them through unchanged.

### Full NSE + BSE universe (don't miss any opportunity)

The shipped `config.yaml` has **566 stocks** (550 NSE + 16 BSE-only) as a
sensible default. To expand it to the **complete ~2,000 NSE listed universe**
so you don't miss any opportunity, run the included fetcher from your machine:

```bash
python fetch_universe.py           # fetch + update config.yaml
python fetch_universe.py --bse     # also fetch BSE-only stocks
python fetch_universe.py --dry-run # show counts without writing
```

This visits `nseindia.com` to set session cookies, fetches the official
`EQUITY_L.csv` (all NSE-listed companies, ~2,000 stocks), and rewrites the
`watchlist:` block in `config.yaml`. Re-run it anytime to refresh. Requires
`pip install requests pyyaml`.

### What an analysis looks like

`analyze` prints the verdict (`TAKE` / `WATCH` / `AVOID` / `NO SETUP`), the
regime, a confidence bar, the full plan (entry, stop, target, quantity sized to
your capital, reward-to-risk, rupees at risk), the bullish and bearish evidence,
the bull/base/bear scenarios, any red signals, analyst notes, and a plain-English
"read." `scan` runs that across your watchlist and prints a ranked table with the
best `TAKE` candidate expanded.

---

## How it sizes positions (the one formula that matters)

```
rupees_at_risk = capital × risk_pct          (e.g. 100000 × 0.01 = ₹1000)
risk_per_share = |entry − stop|              (stop is ATR-based by default)
quantity       = floor(rupees_at_risk / risk_per_share)   # then capped by exposure
```

So a stop-out always costs about the same fixed slice of your capital (1% by
default), no matter the stock's price or volatility. The stop distance is set by
**ATR** (volatility), which means volatile stocks automatically get smaller
positions. No position is allowed to deploy more than `max_exposure_pct` (25%) of
your capital.

Because Indian stocks **gap and stops slip**, the live analyzer sizes against a
*worst-case* fill (stop minus a small slippage + gap buffer, configurable via
`slippage_pct` and `gap_buffer_atr`). The plan shows both your nominal risk at
the stop and the worst-case risk if it gaps — so real risk stays inside your
budget rather than blowing through it. (The textbook formula above is what runs
with the buffer turned off, and it's what the unit tests check.)

---

## Configuration

Two ways, both optional:

- **`.env`** (no extra install needed) — good for secrets and the few settings
  you change often: `ADVISOR_CAPITAL`, `ADVISOR_RISK_PCT`, LLM keys, and the
  offline-data overrides.
- **`config.yaml`** (needs `pip install pyyaml`) — the full set: risk parameters,
  watchlist, timeframes, news feeds, LLM provider.

Precedence is: built-in defaults → `config.yaml` → environment / `.env`.

---

## Data sources and their limits

By default the tool uses **yfinance** (Yahoo Finance), which is free and needs no
account or API key. Be aware of the real limits:

- Quotes are **delayed** (Yahoo marks NSE data ~15 minutes delayed) — fine for
  swing analysis and end-of-day decisions, not for to-the-second intraday timing.
- Intraday history is limited (1-minute ≈ last 7 days; 5/15-minute ≈ 60 days).
- Yahoo occasionally rate-limits or returns gaps; if a symbol fails, try again.

For **offline use or your own data**, set `data_source: csv` and point
`csv_dir` at a folder of files named `SYMBOL_1d.csv` (with Date, Open, High, Low,
Close, Volume columns). The included `sample_data/` folder shows the format - it
ships 5 synthetic regime-CSVs (UPTREND/DOWNTREND/RANGING/VOLATILE/INTRA) plus 14
real NSE daily CSVs (RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, ITC, LT,
HINDUNILVR, BHARTIARTL, SUNPHARMA, WIPRO, AXISBANK, MARUTI) so you can test the
engine against real charts without a network connection.

To upgrade to **true real-time data** later, open a free broker developer account
(Angel One SmartAPI is fully free) and add a new source class implementing the
same `get_history()` / `get_quote()` interface in `advisor/core.py` — nothing
else needs to change.

---

## Optional: AI narration with a local or free LLM

Out of the box, the "read" paragraphs are written by a built-in template — no LLM
required, and honestly it covers most of the value. If you want richer,
trader-style commentary, point the tool at an LLM. **The LLM only writes the
explanation; every number is computed in Python**, so it can't hallucinate a
price.

- **Ollama (local, free):** install Ollama, `ollama pull llama3.1`, then set
  `llm_provider: ollama` (or `ADVISOR_LLM_PROVIDER=ollama`). Runs entirely on
  your machine.
- **Groq (free tier, very fast):** set `GROQ_API_KEY` and `llm_provider: groq`.
- **Google Gemini (free tier):** set `GEMINI_API_KEY` and `llm_provider: gemini`.

If the LLM is unreachable or a key is missing, the tool silently falls back to
the template. No SDKs are needed — it calls these services over plain HTTP.

---

## Backtesting

`python run.py backtest SYMBOL` runs the swing strategy over historical daily
bars using the **same** signal and risk logic as the live analyzer (same
regime-aware signals, the same TAKE gates, the same gap-buffered sizing), so what
you test is what you'd trade. It **simulates both long and short** setups (the
short side stands in for a futures/proxy, since NSE cash has no overnight shorts).
It avoids look-ahead bias (decide on one bar, enter on the next), models
**stop-outs that gap through your stop at the worse fill**, flags **ambiguous
bars** that hit both stop and target, applies a **max-hold exit** and a
**breakeven trail** after +1R, and reports a **mark-to-market** drawdown that
includes open risk. Costs (brokerage, STT, exchange charges, GST, SEBI fee, stamp
duty, slippage) are subtracted so returns are net, not gross.

Treat backtest results with suspicion: live markets slip, gap, and change
character. A backtest that looks too good usually is. Use it to reject bad ideas,
not to predict profits.

---

## The trade journal

Every trade you `log` goes into a local SQLite file (`trade_journal.db`). When you
`close` it at your exit price, the tool records the outcome in R-multiples
**net of estimated costs** (brokerage/STT/slippage), timestamps it in **IST**, and
updates your real statistics: win rate, average win/loss, payoff ratio,
**expectancy**, and a fractional-Kelly position-size suggestion. After ~30 closed
trades these numbers start to mean something; the analyzer then shows your live
edge instead of a generic estimate. This is how the tool "learns" what actually
works for you.

---

## Project layout (v2.1 - merged for easier navigation + full NSE/BSE universe)

```
advisor/
  __init__.py   public API re-export + version
  core.py       models + config + data sources  (foundation layer)
  analysis.py   indicators + regime + signals + risk  (TA & money math)
  engine.py     analyzer + backtest  (the orchestrator)
  extras.py     journal + news + llm  (auxiliary enhancements)
  cli.py        command-line interface and pretty-printer
run.py            entry point
fetch_universe.py fetch ALL NSE + BSE listed stocks -> updates config.yaml
tests/
  test_all.py   consolidated test suite (76 tests, was 8 separate files)
config.yaml     sample configuration (566 stocks default; expand via fetch_universe.py)
sample_data/    synthetic CSVs (UPTREND/DOWNTREND/RANGING/VOLATILE/INTRA)
                + 14 real NSE daily CSVs (RELIANCE, TCS, HDFCBANK, ...)
```

The package was refactored from 14 small modules into 5 cohesive files
(~300-700 lines each), grouped by architectural concern rather than by
individual class. The public API (`from advisor import Analyzer, Settings,
Style, ...`) is unchanged - all old imports still work. See `CHANGES.md`
for the full mapping.

Run the tests with `pytest tests/` (or `python tests/test_all.py`).

---

## A sane way to roll this out

1. **Paper first.** Run `scan` daily for a few weeks. For each `TAKE`, write down
   what you *would* have done and track it. No real money.
2. **Backtest** the names you care about. If expectancy is negative after costs,
   the strategy isn't ready — tune it, don't trade it.
3. **Go small.** Start at 0.5–1% risk per trade. Log every trade and close it in
   the journal so your real expectancy accumulates.
4. **Scale slowly.** Only consider larger risk per trade after 100+ logged trades
   of genuinely positive expectancy. Most people never need more than 1%.

---


