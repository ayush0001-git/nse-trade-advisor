# ULTIMATE TRADING BOT RAG KNOWLEDGE BASE
# Organized: Most Underrated → Most Mainstream | Hedge Fund Grade
# Feed every section as separate RAG chunks with metadata tags

---

# ═══════════════════════════════════════════════════════════
# TIER 1: MOST UNDERRATED — ALMOST NOBODY TALKS ABOUT THESE
# ═══════════════════════════════════════════════════════════

---

## [CHUNK: WYCKOFF_METHOD]
## Wyckoff Market Cycle Method (1930s — Still Works)

Richard Wyckoff's method analyzes price and volume to determine the intentions of large operators (smart money). Almost completely ignored by retail traders.

### Four Phases:
1. **Accumulation** — Large operators buy quietly. Price moves sideways. Volume is irregular.
   - Signs: Selling Climax (SC), Automatic Rally (AR), Secondary Test (ST), Spring (false breakdown to shake out weak hands)
2. **Markup** — Price trends upward. Smart money distributes to retail late.
3. **Distribution** — Smart money sells quietly. Price moves sideways at top.
   - Signs: Buying Climax (BC), Automatic Reaction, Upthrust After Distribution (UTAD)
4. **Markdown** — Price trends downward.

### Wyckoff Laws:
- **Law of Supply and Demand** — Price rises when demand > supply
- **Law of Cause and Effect** — Size of accumulation = size of markup
- **Law of Effort vs. Result** — Volume (effort) should match price movement (result). Divergence = reversal

### Wyckoff Events to Identify:
- PS (Preliminary Support), SC (Selling Climax), AR (Automatic Rally), ST (Secondary Test)
- Spring / Shakeout — false break below support to trigger stops
- SOS (Sign of Strength), LPS (Last Point of Support)
- UTAD (Upthrust After Distribution)

### Trading Rule:
Buy at Spring + SOS confirmation. Sell at UTAD. Use volume as confirmation tool.

**Sources to scrape:**
- https://www.wyckoffanalytics.com
- https://school.stockcharts.com/doku.php?id=market_analysis:the_wyckoff_method

---

## [CHUNK: VOLUME_SPREAD_ANALYSIS]
## Volume Spread Analysis (VSA)

Extension of Wyckoff. Analyzes the spread (high-low range) of a candle versus its volume to detect smart money activity.

### Key VSA Signals:
| Candle Type | Volume | Meaning |
|---|---|---|
| Wide spread up | Ultra-high | Potential distribution (climax) |
| Narrow spread up | High | Hidden selling — bearish |
| Wide spread down | Ultra-high | Selling climax — potential reversal up |
| Narrow spread down | Low | No supply — bullish |
| Up candle closes mid | High | Bearish (supply entering) |
| Down candle closes mid | High | Bullish (demand entering) |

### No Demand Signal: Narrow spread up bar on low volume — no institutional buying
### No Supply Signal: Narrow spread down bar on low volume — no institutional selling

**Sources:**
- https://www.tradeguider.com
- https://www.traderscockpit.com

---

## [CHUNK: MARKET_PROFILE_TPO]
## Market Profile & Time Price Opportunity (TPO)

Developed by J. Peter Steidlmayer at CBOT. Organizes price by TIME spent at each level, not just OHLCV.

### Core Concepts:
- **Value Area (VA)** — 70% of volume traded here. Represents fair value.
- **Point of Control (POC)** — Single price with most time/volume. Strongest support/resistance.
- **Value Area High (VAH)** — Upper edge of value area
- **Value Area Low (VAL)** — Lower edge of value area
- **Initial Balance (IB)** — First hour range. Defines the day.
- **TPO Letters** — Each 30-min period gets a letter (A=9:30, B=10:00, etc.)

### Trading Rules:
- Price returning to POC tends to find support/resistance
- Break above VAH with acceptance = bullish continuation
- Break below VAL with acceptance = bearish continuation
- Single prints (only 1 TPO letter) = area of imbalance — price will return to fill

### Profile Shapes:
- **Normal distribution (bell curve)** — balanced market
- **P-shape profile** — buying tail at bottom, distribution at top
- **b-shape profile** — selling tail at top, accumulation at bottom
- **Double distribution** — two value areas — trend day

**Sources:**
- https://www.cmegroup.com/education/market-profile.html
- https://www.atas.net/volume-analysis/market-profile/

---

## [CHUNK: ORDER_FLOW_TRADING]
## Order Flow & Footprint Charts

Sees the ACTUAL buy/sell orders at each price level inside each candle. Used by professional futures traders.

### Key Metrics:
- **Bid/Ask Volume** — Volume traded at bid (sellers) vs ask (buyers)
- **Delta** — Difference between buying volume and selling volume. Positive delta = buyers winning.
- **Cumulative Delta** — Running total of delta. Divergence with price = reversal signal.
- **Imbalance** — When one side (bid or ask) exceeds other by 300%+. Shows aggression.
- **POC per candle** — Price with most volume inside that specific candle
- **Volume profile per candle** — Distribution of volume inside the candle

### Signals:
- **Absorption** — Large volume absorbed with little price movement. Reversal likely.
- **Exhaustion** — Large delta spike at end of move = trend ending
- **Stacked imbalances** — Multiple consecutive imbalances = strong directional move
- **Failed auction** — Price tests level, volume present but can't move. Reversal imminent.

**Tools:**
- https://www.bookmap.com (heatmap + order flow)
- https://www.volumeprofilertools.com
- https://www.ninjatrader.com (footprint charts)
- https://www.atas.net

---

## [CHUNK: LIQUIDITY_CONCEPTS]
## Liquidity Hunting & Smart Money Concepts (ICT Method)

Inner Circle Trader (ICT) methodology. Describes how institutions hunt retail trader stop losses to fill large orders.

### Core Concepts:
- **Buy-Side Liquidity (BSL)** — Rests above swing highs (retail stop losses for shorts, breakout buyers). Institutions buy HERE by pushing price above to grab liquidity then reverse.
- **Sell-Side Liquidity (SSL)** — Rests below swing lows (retail stop losses for longs). Institutions sell HERE.
- **Fair Value Gap (FVG)** — 3-candle imbalance where middle candle's body doesn't overlap with 1st or 3rd candle's wick. Price returns to fill these.
- **Breaker Block** — Previous order block that was broken. Now acts as opposite S/R.
- **Order Block (OB)** — Last down candle before a strong up move (bullish OB). Last up candle before strong down move (bearish OB). Institutions placed orders here.
- **Optimal Trade Entry (OTE)** — 61.8-79% Fibonacci retracement of a swing. High-probability entry zone.
- **Killzones** — High-probability trading times: London Open (3-5am EST), NY Open (9:30-11am EST), NY Lunch (1-2pm EST), London Close (10-12pm EST)
- **NWOG/NDOG** — New Week/Day Opening Gaps. Price tends to fill these.
- **Consequent Encroachment** — 50% of a Fair Value Gap. First target for price to reach into FVG.
- **Institutional Order Flow Entry Drill (IOFED)** — Sequence: liquidity sweep → displacement → FVG entry → target opposing liquidity

### Power of 3 (AMD Model):
- **Accumulation** — Smart money accumulates at lows (London session)
- **Manipulation** — False move to hunt stops (early NY session)
- **Distribution** — True directional move distributes to retail (NY session)

**Sources:**
- https://www.theinnercircletrader.com
- YouTube: ICT (Michael J. Huddleston) free content

---

## [CHUNK: INTERMARKET_ANALYSIS]
## Intermarket Analysis (John Murphy Method)

Markets don't move in isolation. These relationships are the foundation of macro trading.

### Key Relationships:
- **Bonds UP → Stocks UP** (cheap money = good for equities)
- **Bonds DOWN → Stocks DOWN** (rising rates = bad for growth stocks especially)
- **Dollar UP → Commodities DOWN** (inverse relationship)
- **Dollar DOWN → Gold UP, Oil UP, Emerging Markets UP**
- **Oil UP → Energy stocks UP, Airlines DOWN, Consumer discretionary DOWN**
- **Gold UP → Risk-off signal, often stocks DOWN**
- **Copper UP → Global growth UP (Dr. Copper = economic indicator)**
- **VIX UP → Stocks DOWN (fear = selling)**
- **Junk bonds spread widening → Stocks sell off incoming**
- **10Y-2Y yield spread inverts → Recession in 12-18 months**

### Sector-Commodity Links:
- Gold miners (GDX) follow gold with leverage
- Oil services (OIH) follow crude oil
- Steel (X, NUE) follow iron ore
- Agriculture (MOO ETF) follow corn/wheat/soy

### Global Market Sequencing:
Asia closes → Europe opens → US opens. Watch for:
- Nikkei direction often predicts US futures direction
- EUR/USD direction correlates with Euro Stoxx 50

**Sources:**
- https://fred.stlouisfed.org (macro data)
- https://www.macrotrends.net/assets/php/fundamental_iframe.php
- https://stockcharts.com/freecharts/perf.php (intermarket comparison)

---

## [CHUNK: AUCTION_MARKET_THEORY]
## Auction Market Theory

Markets are auctions. Price moves to find areas where trade can occur (acceptance) or moves away from areas where trade cannot occur (rejection).

### Core Principles:
- **Price seeks the path of least resistance** to find the next area of liquidity
- **Trending markets** — market repeatedly auctions to new highs/lows because no acceptance
- **Ranging markets** — market finds acceptance and oscillates within value area
- **Rotational reference points** — previous day high/low, previous week high/low, monthly open

### Trading with Auction Theory:
- Identify if market is in a **trend auction** or **balance** state
- In balance: fade extremes (buy VAL, sell VAH)
- In trend: buy pullbacks to value, hold through rotation
- **Rule:** Price that auctions above resistance for 2+ days = new value, not a breakout to fade

---

## [CHUNK: GAMMA_EXPOSURE]
## Gamma Exposure (GEX) & Options Market Making

One of the most powerful and most ignored concepts in modern equity markets.

### What is GEX:
Market makers (MMs) sell options to retail. To stay delta-neutral, they must hedge by buying/selling the underlying stock.

- **Positive GEX** — MMs are net long gamma. When price rises, MMs SELL stock (dampens moves). When price falls, MMs BUY stock (dampens moves). **Suppresses volatility. Price gravitates toward "max pain."**
- **Negative GEX** — MMs are net short gamma. When price rises, MMs must BUY stock (amplifies moves). When price falls, MMs must SELL stock (amplifies moves). **Amplifies volatility. Trending/explosive moves happen.**

### Key Levels:
- **Max Pain** — Option strike price where option buyers lose most money. Price gravitates here at expiration.
- **Gamma Flip** — Level where GEX switches from positive to negative. Cross this = volatility regime change.
- **0DTE (Zero Days to Expiration) flows** — Massive influence on intraday moves. SPY/SPX options expiring same day.
- **Strike clustering** — Large open interest at round numbers (e.g., SPX 5000) acts as magnet

### Practical Trading:
- In positive GEX: mean reversion strategies work well
- In negative GEX: momentum/trend following works well
- Watch GEX flip level as key S/R
- Fridays/expirations: pin risk toward max pain strikes

**Sources:**
- https://www.spotgamma.com (paid — best GEX data)
- https://www.squeezemetrics.com (free GEX data)
- https://www.gexbot.com
- https://unusualwhales.com

---

## [CHUNK: DARK_POOL_PRINTS]
## Dark Pool & Off-Exchange Trading

40-50% of all US equity volume trades off-exchange (dark pools, internalization). Institutional accumulation/distribution happens here invisibly.

### What to Look For:
- **Large dark pool prints at a price level** = institutional interest there
- **Repeated dark pool prints building at same price** = accumulation
- **Dark pool prints above current price** = institutional buying ahead of news
- **FINRA ADF volume** — dark pool volume reported with delay

### Dark Pool Levels as S/R:
If a large dark pool print occurs at $150, that level becomes strong support/resistance because institutions defend their cost basis.

### Off-Exchange Data Sources:
- https://www.finra.org/investors/market-data/otc-transparency (free FINRA data)
- https://darkpoollevels.com
- https://unusualwhales.com/dark-pool
- https://www.cboe.com/us/equities/market_statistics/

---

## [CHUNK: TAPE_READING]
## Tape Reading & Time & Sales Analysis

Old technique from Jesse Livermore era. Reading the actual tape (time & sales) to see where big orders are being filled.

### What to Watch:
- **Large lot trades** (10,000+ shares) at bid = institutional selling
- **Large lot trades at ask** = institutional buying
- **Rapid small lots** = algo chasing price (momentum)
- **Trades printing between bid/ask** = dark pool negotiated trades
- **Sudden volume surge with price unchanged** = absorption (large player opposing move)
- **Sweep orders** — taking out all liquidity at multiple price levels instantly = aggressive directional bet

### Level 2 Reading:
- Large size sitting at a price level = potential support/resistance (may be spoofing)
- **Spoofing** — fake large orders placed then cancelled to manipulate price direction (illegal but happens)
- **Iceberg orders** — only show partial size, more refills automatically
- Pulling size = order cancelled, price likely to move through that level

---

## [CHUNK: STATISTICAL_ARBITRAGE]
## Statistical Arbitrage (StatArb)

Hedge fund strategy. Find pairs of stocks that historically move together, trade the spread when it diverges.

### Pairs Trading Steps:
1. Find cointegrated pairs (use Engle-Granger test or Johansen test)
2. Calculate spread: Spread = Stock A - (hedge ratio × Stock B)
3. Calculate Z-score of spread: Z = (Spread - Mean) / StdDev
4. **Buy spread when Z < -2, Sell spread when Z > +2**
5. **Exit when Z returns to 0**
6. Stop loss at Z = ±3

### Cointegrated Pairs Examples:
- Coke (KO) / Pepsi (PEP)
- Gold (GLD) / Silver (SLV)
- ExxonMobil (XOM) / Chevron (CVX)
- Visa (V) / Mastercard (MA)
- Boeing (BA) / Lockheed Martin (LMT)
- WTI Crude / Brent Crude
- S&P 500 (SPY) / S&P 100 (OEF)

### Implementation:
- Lookback window: 60-252 days
- Half-life of mean reversion: use Ornstein-Uhlenbeck process to estimate
- Beta hedge ratio: use OLS regression or Kalman filter (dynamic hedge ratio)

**Sources:**
- https://www.quantconnect.com (pairs trading templates)
- https://finance.yahoo.com (price data for testing)
- Academic: "Pairs Trading: Performance of a Relative Value Arbitrage Rule" — Gatev et al.

---

## [CHUNK: FACTOR_INVESTING]
## Factor Investing (Quant Factors) — What Hedge Funds Actually Use

### The Five Classic Fama-French Factors:
1. **Market Beta** — Excess return of market over risk-free rate
2. **Size (SMB)** — Small caps outperform large caps long-term
3. **Value (HML)** — High book/market outperforms low book/market
4. **Profitability (RMW)** — High operating profitability outperforms
5. **Investment (CMA)** — Conservative investment firms outperform aggressive

### Additional Widely Used Factors:
- **Momentum (MOM)** — Stocks up last 12 months (skip last month) continue outperforming for ~3-12 months
- **Low Volatility** — Low vol stocks outperform high vol on risk-adjusted basis (CAPM anomaly)
- **Quality** — High ROE, low debt, stable earnings outperform
- **Liquidity** — Illiquid stocks offer premium (but hard to trade)
- **Earnings Revision** — Stocks with upward earnings revisions outperform
- **Short Interest** — High short interest = potential squeeze OR valid short signal
- **Insider Buying** — Cluster of insider purchases = bullish signal
- **Accruals** — Low accruals (cash earnings) outperform high accruals (accounting earnings)
- **Gross Profitability** — High gross profit/assets = outperformance (Novy-Marx factor)
- **Piotroski F-Score** — 9-point fundamental score. Score 8-9 = buy. Score 0-1 = short.
- **Altman Z-Score** — Bankruptcy predictor. Z < 1.81 = distress zone.
- **Beneish M-Score** — Earnings manipulation detector. M > -1.78 = likely manipulator.

### Multi-Factor Portfolio Construction:
- Score each stock on each factor (rank 1-100 percentile)
- Combine factor scores with weights
- Go long top quintile, short bottom quintile
- Rebalance monthly or quarterly

**Sources:**
- https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html (free factor data)
- https://www.aqr.com/Insights/Datasets (AQR factor data)
- https://www.factorresearch.com
- https://alphaarchitect.com/factor-investing-tools/

---

## [CHUNK: DISPERSION_TRADING]
## Dispersion Trading

Volatility hedge fund strategy. Trade the difference between index implied volatility and constituent stock implied volatility.

### Logic:
- Index IV is usually LOWER than average IV of components (correlation discount)
- When correlations spike (crisis), index IV spikes more than component IV
- **Short index variance, long component variance** when spread is historically wide
- **Long index variance, short component variance** when spread is historically narrow

### Implementation:
- Buy puts/calls on individual stocks (long single-stock vol)
- Sell straddles/strangles on SPX (short index vol)
- Net premium = zero cost or small debit
- Profit when stocks move independently (low correlation)

---

## [CHUNK: CONVERTIBLE_BOND_ARBITRAGE]
## Convertible Bond Arbitrage

Hedge fund strategy. Exploit mispricing between convertible bonds and underlying equity.

### Setup:
- Buy undervalued convertible bond (has bond + call option embedded)
- Short the underlying stock (delta hedge the equity component)
- Isolate and profit from the cheap optionality

### Why it works:
- Convertible bonds often issued cheap (companies need financing)
- Delta of conversion changes as stock moves — rebalancing generates profit (gamma scalping)
- Bond floor provides downside protection

**Major hedge funds using this:** Calamos, Advent Capital

---

## [CHUNK: VOLATILITY_SURFACE]
## Volatility Surface & Term Structure

Professional options traders trade the shape of the volatility surface, not just direction.

### IV Skew:
- Puts on equities always more expensive than calls (negative skew) — crash protection demand
- Steeper skew = more fear
- Flatter skew = complacency

### Term Structure:
- **Contango** (normal) — near-term IV < long-term IV. Roll-down favors short vol.
- **Backwardation** — near-term IV > long-term IV. Happens in crises.
- VIX futures in contango = short VIX ETFs (XIV/SVXY) profitable slowly

### Volatility Trades:
- **Calendar spread** — exploit term structure differences
- **Diagonal spread** — directional + volatility play
- **Ratio spread** — short more options than long, profits from vol crush
- **Vega-neutral delta hedge** — strip out all directional risk, trade vol itself

### Greeks Summary:
- **Delta** — Price sensitivity (0 to 1 for calls, -1 to 0 for puts)
- **Gamma** — Rate of change of delta. High near expiration and at-the-money.
- **Theta** — Time decay. Option seller benefits.
- **Vega** — Sensitivity to implied volatility changes.
- **Rho** — Sensitivity to interest rate changes.
- **Vanna** — Sensitivity of delta to changes in IV
- **Charm** — Rate of change of delta over time
- **Volga/Vomma** — Sensitivity of vega to changes in IV

---

# ═══════════════════════════════════════════════════════════════
# TIER 2: ADVANCED STRATEGIES — USED BY PROP FIRMS & QUANT FUNDS
# ═══════════════════════════════════════════════════════════════

---

## [CHUNK: MEAN_REVERSION_QUANTITATIVE]
## Quantitative Mean Reversion Strategies

### Ornstein-Uhlenbeck Process:
Models mean-reverting price series. Parameters:
- **Theta (θ)** — Speed of mean reversion
- **Mu (μ)** — Long-run mean
- **Sigma (σ)** — Volatility

Half-life = ln(2) / θ. Trade only if half-life is 1-30 days (practical mean reversion timeframe).

### Bollinger Band Mean Reversion (Full System):
- Entry: Price closes below lower band (2 std devs) for 2 consecutive days
- Confirm: RSI < 30
- Confirm: Volume spike (absorption)
- Entry: Buy next day open
- Target: Middle band (20 SMA)
- Stop: Close below lower band by > 1 ATR
- Position size: 2% risk per trade

### RSI-2 Strategy (Larry Connors):
- Universe: S&P 500 stocks
- Filter: Stock above 200-day SMA
- Entry: RSI(2) drops below 10
- Exit: RSI(2) rises above 70
- Backtest win rate: ~70% historically

### Connors RSI (CRSI):
CRSI = (RSI(3) + RSI(Streak,2) + PercentRank(100)) / 3
- RSI(3) — 3-period RSI
- RSI(Streak,2) — 2-period RSI of up/down streak
- PercentRank(100) — Percentile rank of 1-day return over 100 days
- Buy < 10, Sell > 90

---

## [CHUNK: MOMENTUM_STRATEGIES_QUANT]
## Quantitative Momentum Strategies

### Classic 12-1 Momentum:
- Calculate 12-month return, skip last 1 month (reversal effect)
- Rank universe by this return
- Long top decile, short bottom decile
- Rebalance monthly
- Historical Sharpe: ~0.5-0.8 depending on universe

### Dual Momentum (Gary Antonacci):
- **Absolute momentum:** Is the asset's return > T-Bills? If yes, hold it.
- **Relative momentum:** Which asset has higher return — stocks or bonds?
- Simple 2-asset rotation: If SPY > T-bills = hold SPY. If SPY < T-bills = hold AGG.
- No leverage, minimal trades, historically strong risk-adjusted returns.

### Time Series Momentum (TSMOM):
- Each asset: If return over past 12 months > 0, go long. If < 0, go short.
- Diversify across many asset classes: equities, bonds, commodities, currencies
- Core strategy at AQR, Winton, Man AHL

### Residual Momentum:
- Strip out factor exposures (beta, size, value) from returns
- Momentum of residual (idiosyncratic) return
- Less prone to momentum crashes

### Momentum Crashes:
- Momentum crashes happen in sharp rebounds after crashes (2009, 2020)
- Hedge: Go flat momentum when VIX > 40
- Hedge: Use option protection in high-volatility regimes

---

## [CHUNK: TREND_FOLLOWING_SYSTEMS]
## Systematic Trend Following (CTA/Managed Futures Style)

Used by Winton, Man AHL, Millburn, Chesapeake Capital. Core strategy of commodity trading advisors.

### Core System (Turtle Trading variant):
- **Entry:** 20-day or 55-day Donchian channel breakout
- **Exit:** 10-day or 20-day Donchian channel opposite breakout
- **Position sizing:** 1 ATR = 1% account risk
- **Stop loss:** 2 ATR from entry
- **Portfolio:** Trade 20+ uncorrelated markets simultaneously
- **Markets:** Equities, bonds, currencies, commodities, metals, energy

### Position Sizing Formula (ATR-based):
- Dollar Risk per trade = Account Value × 1%
- Position Size = Dollar Risk / (ATR × Contract Value)

### Trend Filter:
- Only trade longs when 200-day SMA is rising
- Only trade shorts when 200-day SMA is falling
- Use ADX > 25 to confirm trend strength

### Multi-Timeframe Trend:
- Weekly trend filter + Daily entry signal
- If weekly trend up: only take daily long signals
- Reduces whipsaws dramatically

### Key CTA Metrics to Monitor:
- **Calmar Ratio** = CAGR / Max Drawdown. Target > 0.5
- **MAR Ratio** = same as Calmar
- **Sortino Ratio** = Return / Downside deviation. Target > 1.0
- **Maximum Drawdown Duration** — how long to recover

**Sources:**
- https://www.iasg.com/managed-futures/
- https://www.barclayhedge.com/research/indices/cta/
- Academic: "Two Centuries of Trend Following" — AQR Capital

---

## [CHUNK: HIGH_FREQUENCY_MICROSTRUCTURE]
## Market Microstructure (HFT Concepts for Retail)

### Bid-Ask Spread Dynamics:
- **Adverse selection** — Market maker fears trading against informed traders
- **Inventory risk** — Market maker holds position risk
- Wide spread = high uncertainty, high risk
- Narrow spread = competitive, liquid market

### Price Impact:
- Large orders move price against the trader (market impact)
- TWAP (Time Weighted Average Price) — spread order over time equally
- VWAP (Volume Weighted Average Price) — trade proportional to volume profile
- Implementation shortfall — measure of how much worse than decision price you executed

### Queue Position (Limit Order Book):
- First-come-first-served at each price level
- Being early in queue at a price = lower adverse selection
- Queue jumping with price improvement costs spread but ensures fill

### Retail Application:
- Use limit orders not market orders (avoid paying spread)
- Trade in liquid stocks/ETFs (tight spreads)
- Avoid trading first/last 15 minutes of day (wide spreads, manipulation)
- Use VWAP as execution benchmark

---

## [CHUNK: EVENT_DRIVEN_STRATEGIES]
## Event-Driven Trading Strategies

### Merger Arbitrage (Risk Arb):
- When merger announced: Target stock trades at DISCOUNT to deal price (deal risk premium)
- **Setup:** Buy target stock. Optionally short acquirer.
- **Spread = Deal Price - Current Price**
- **Return = Spread / Days to Close × 365**
- **Risk:** Deal breaks = target stock falls 20-40%
- **Signal for break risk:** Rising CDS spreads on acquirer, regulatory concerns, financing markets tightening

**Sources for merger data:**
- https://mergersandacquisitions.com
- https://www.briefing.com/investor/calendars/ma.htm
- https://www.mnainfo.com

### Earnings Drift (PEAD — Post-Earnings Announcement Drift):
- After an earnings beat, stocks continue drifting higher for 60-90 days
- After an earnings miss, stocks continue drifting lower for 60-90 days
- **Why:** Analysts and funds are slow to update models
- **Trade:** Buy stocks that beat estimates + raise guidance, hold 30-60 days
- **Filter:** Only stocks with beat + positive guidance revision + strong price reaction (+3%+ gap up)

### Spin-Off Strategy:
- Spin-offs systematically outperform the market
- Reason: Index funds forced to sell small spin-offs (not in their index)
- Watch for: Insider buying in spin-off shortly after listing
- Hold 12-18 months

### Special Situations:
- **Rights offerings** — Existing shareholders get right to buy new shares at discount
- **Dutch tender offers** — Company buys back shares at fixed price range
- **Stub trades** — Parent company trades at discount to sum of parts
- **ADR/Ordinary share arbitrage** — Same company, different exchanges, price discrepancy

---

## [CHUNK: CARRY_STRATEGIES]
## Carry Trading

### FX Carry:
- Borrow in low interest rate currency (JPY, CHF)
- Invest in high interest rate currency (BRL, TRY, AUD historically)
- Profit from interest rate differential
- **Risk:** Carry currencies crash spectacularly in crises (risk-off unwind)
- **Signal to exit:** VIX rising above 25, risk appetite deteriorating

### Commodity Carry:
- **Roll yield** — profit/loss from rolling futures contracts
- Contango = negative roll yield (cost to hold)
- Backwardation = positive roll yield (earn by holding)
- Long backwardated commodities, short contangoed commodities

### Volatility Carry:
- Implied volatility almost always > realized volatility (VRP — variance risk premium)
- Short options (sell straddles/strangles) to collect this premium
- Expected profit = IV - RV (variance risk premium)
- **Risk:** Short gamma exposure — unlimited loss in crashes
- **Management:** Delta hedge, position size small (1-2% risk), use spreads not naked shorts

### Bond Carry:
- Steep yield curve = positive carry for holding long bonds
- Buy 10-year, fund with 3-month rates. Profit from yield difference.
- Risk: Rates rise = bond price falls

---

## [CHUNK: MACHINE_LEARNING_ALPHA]
## Machine Learning for Alpha Generation

### Feature Engineering for Stock Prediction:
**Price-based features:**
- Rolling returns (1d, 5d, 10d, 21d, 63d, 126d, 252d)
- Volatility (rolling std of returns)
- Skewness of returns
- Distance from 52-week high/low
- Gap size (open vs prev close)
- Intraday range (high-low)/open

**Volume-based features:**
- Turnover ratio (volume/shares outstanding)
- Amihud illiquidity ratio = |return| / dollar volume
- Volume surprise (actual vs 20-day avg)

**Technical features:**
- RSI, MACD signal, Stochastic
- Bollinger Band position
- ATR normalized

**Fundamental features:**
- P/E, P/B, P/S z-scores vs sector
- EPS revision % (3m change in consensus)
- Revenue surprise %
- Free cash flow yield

**Sentiment features:**
- Short interest change
- Insider buying/selling net
- Analyst rating change
- Options put/call ratio

### Model Types Used:
- **Random Forest** — Robust, handles nonlinear interactions, less overfit
- **Gradient Boosting (XGBoost, LightGBM)** — High accuracy, feature importance
- **LSTM / GRU** — Time series patterns in sequence data
- **Transformer models** — Attention over time series + news
- **Linear regression with regularization (Ridge/Lasso)** — Baseline, interpretable
- **Gaussian Process** — Probabilistic predictions with uncertainty

### Cross-Validation for Finance:
- **Walk-forward validation** — Train on past, test on future period, roll forward
- **Purged K-fold** — Remove data around test period to prevent leakage
- **Embargo period** — After each test fold, skip N days before next train to prevent overlap

### Overfitting Prevention:
- Use out-of-sample tests with long history
- Regularization (L1/L2)
- Feature selection (use < 20 features)
- Ensemble methods
- Test on multiple market regimes
- Beware of: data snooping, lookahead bias, survivorship bias

**Sources:**
- https://www.quantconnect.com (algorithmic trading platform)
- https://www.zipline.io (Pythonic backtesting)
- https://www.backtrader.com
- https://github.com/stefan-jansen/machine-learning-for-algorithmic-trading (free book code)
- https://www.quantlib.org (quantitative finance library)

---

## [CHUNK: SENTIMENT_NLP]
## NLP Sentiment Analysis for Trading

### Text Sources to Mine:
- **SEC 8-K filings** — Material events, earnings releases
- **10-K/10-Q MD&A section** — Management tone changes = signal
- **Earnings call transcripts** — Tone, certainty, hedging language
- **News headlines** — Reuters, Bloomberg, AP
- **Analyst notes** — Upgrade/downgrade language
- **Social media** — Twitter/X, Reddit (WallStreetBets, r/stocks)
- **Job postings** — Companies hiring aggressively = growth signal

### NLP Signals:
- **Loughran-McDonald Finance Dictionary** — Finance-specific positive/negative words (not general sentiment dictionaries — they misclassify finance terms like "liability")
- **Tone score** = (positive words - negative words) / total words
- **Uncertainty score** = count of uncertainty words (approximately, might, could)
- **Litigious score** — count of litigation terms = legal risk signal
- **Change in tone** from previous quarter = more powerful than absolute tone

### Earnings Call Signals:
- CFO not on call = bad sign
- CEO uses more past tense = less confident about future
- Analyst questions getting longer/more probing = skepticism
- Management answers shorter = defensive
- Word "headwinds" count rising quarter over quarter = bearish

### BERT/FinBERT for Finance:
- FinBERT — pre-trained BERT model on financial news
- Better than generic sentiment models for finance text
- Available at: https://huggingface.co/ProsusAI/finbert

### Alternative Text Data:
- **Glassdoor reviews** — Employee sentiment = company health indicator
- **Patent filings** — R&D direction and innovation pipeline
- **LinkedIn job posting volume** — Headcount growth by company
- **App store ratings** — Consumer product quality signal

**Sources:**
- https://efts.sec.gov/LATEST/search-index?q= (SEC EDGAR full-text search)
- https://www.sentimenTrade.com
- https://stocktwits.com/api/2 (social sentiment API)
- https://reddit.com/r/wallstreetbets/.json (Reddit API)
- https://www.twitter.com/search?q=%24AAPL (Cashtag sentiment)

---

# ══════════════════════════════════════════════════════════
# TIER 3: MAINSTREAM — WIDELY USED BY PROFESSIONALS & RETAIL
# ══════════════════════════════════════════════════════════

---

## [CHUNK: TECHNICAL_INDICATORS_COMPLETE]
## Complete Technical Indicators Reference

### Trend Indicators:
- **SMA (Simple Moving Average)** — Equal weight to all periods
  - Golden Cross: 50 SMA crosses above 200 SMA = bullish
  - Death Cross: 50 SMA crosses below 200 SMA = bearish
- **EMA (Exponential Moving Average)** — More weight to recent prices. 8, 21, 34, 55, 89 (Fibonacci EMAs)
- **DEMA (Double EMA)** — 2(EMA) - EMA(EMA). Less lag.
- **TEMA (Triple EMA)** — Less lag than DEMA.
- **Kaufman Adaptive Moving Average (KAMA)** — Adjusts to volatility automatically
- **Hull Moving Average (HMA)** — Very low lag moving average
- **ADX (Average Directional Index)** — Trend strength. >25 = strong trend. <20 = no trend.
  - +DI above -DI = uptrend. -DI above +DI = downtrend.
- **Parabolic SAR** — Trailing stop that accelerates. Dots below price = uptrend, above = downtrend.

### Momentum Indicators:
- **RSI (Relative Strength Index 14-period)** — Overbought >70, oversold <30. Divergence = powerful signal.
- **MACD** — 12 EMA - 26 EMA = MACD line. 9 EMA of MACD = Signal line. Histogram = difference.
  - Bullish: MACD crosses above signal, histogram turns positive
  - Bearish: MACD crosses below signal, histogram turns negative
  - Divergence: Price makes new high but MACD doesn't = bearish divergence
- **Stochastic Oscillator** — %K and %D. Overbought >80, oversold <20.
- **Williams %R** — Similar to stochastic. -20 = overbought, -80 = oversold.
- **CCI (Commodity Channel Index)** — Overbought >100, oversold <-100.
- **Rate of Change (ROC)** — Percentage change over N periods. Momentum direction.
- **Momentum Oscillator** — Price - Price(N periods ago). Simple momentum.
- **TSI (True Strength Index)** — Double-smoothed price change.

### Volatility Indicators:
- **Bollinger Bands** — 20 SMA ± 2 standard deviations. Squeeze = low vol before breakout.
- **ATR (Average True Range)** — Average daily range. Position sizing tool.
- **Keltner Channel** — 20 EMA ± 2 ATR. When BB inside Keltner = squeeze (breakout imminent).
- **Donchian Channel** — Highest high / lowest low over N periods. Breakout indicator.
- **Standard Deviation** — Raw measure of price volatility.
- **Chaikin Volatility** — ATR of range relative to previous. Rising = expanding volatility.

### Volume Indicators:
- **OBV (On-Balance Volume)** — Cumulative volume based on price direction. Divergence from price = signal.
- **VWAP** — Volume-weighted average price. Institutional benchmark. Price above = bullish.
- **Volume Profile** — Volume at each price level. See where most trading occurred.
- **Chaikin Money Flow (CMF)** — Measures buying/selling pressure based on close position within range
- **Money Flow Index (MFI)** — Volume-weighted RSI. Overbought >80, oversold <20.
- **Accumulation/Distribution (A/D)** — Where does price close within range × volume.
- **Elder Force Index** — Price change × volume = buying/selling force.

### Support & Resistance Tools:
- **Pivot Points** — PP = (High + Low + Close) / 3. R1, R2, R3, S1, S2, S3.
- **Fibonacci Retracements** — 23.6%, 38.2%, 50%, 61.8%, 78.6%. Key retracement levels.
- **Fibonacci Extensions** — 127.2%, 161.8%, 200%, 261.8%. Targets beyond previous high.
- **Fibonacci Time Zones** — Vertical lines at Fibonacci intervals. Potential turning points.
- **Camarilla Pivots** — Intraday S/R levels calculated from previous day H/L/C.
- **Murrey Math Lines** — Price levels at 1/8 divisions of a major range.

---

## [CHUNK: CANDLESTICK_PATTERNS_COMPLETE]
## Complete Candlestick Patterns Reference

### Single Candle Patterns:
- **Doji** — Open = Close. Indecision. More powerful at extremes.
- **Dragonfly Doji** — Long lower shadow, no upper. Bullish reversal.
- **Gravestone Doji** — Long upper shadow, no lower. Bearish reversal.
- **Hammer** — Small body, long lower shadow. Bullish reversal after downtrend.
- **Hanging Man** — Same as hammer but after uptrend. Bearish reversal.
- **Inverted Hammer** — Small body, long upper shadow. Bullish reversal after downtrend.
- **Shooting Star** — Same as inverted hammer but after uptrend. Bearish reversal.
- **Marubozu** — No shadows, full body. Strong directional conviction.
- **Spinning Top** — Small body, both shadows. Indecision.

### Two-Candle Patterns:
- **Bullish Engulfing** — Second candle completely engulfs first. Strong bullish reversal.
- **Bearish Engulfing** — Second candle completely engulfs first. Strong bearish reversal.
- **Piercing Line** — Down candle followed by up candle closing >50% into first. Bullish.
- **Dark Cloud Cover** — Up candle followed by down candle opening above, closing >50% into first. Bearish.
- **Harami** — Small candle inside large candle. Potential reversal.
- **Tweezer Top/Bottom** — Same high (top) or same low (bottom) on consecutive candles.

### Three-Candle Patterns:
- **Morning Star** — Down candle, small body gap down, strong up candle. Bullish reversal.
- **Evening Star** — Up candle, small body gap up, strong down candle. Bearish reversal.
- **Three White Soldiers** — Three consecutive strong up candles. Strong bullish.
- **Three Black Crows** — Three consecutive strong down candles. Strong bearish.
- **Three Inside Up/Down** — Harami then confirmation candle. Reversal.
- **Abandoned Baby** — Doji gaps completely away from prior and following candles. Reversal.

---

## [CHUNK: CHART_PATTERNS_COMPLETE]
## Complete Chart Patterns Reference

### Reversal Patterns:
- **Head and Shoulders** — Three peaks, middle highest. Neckline break = target: H&S height subtracted from neckline.
- **Inverse Head and Shoulders** — Three troughs, middle lowest. Bullish reversal.
- **Double Top (M pattern)** — Two equal highs. Break of neckline = bearish. Target = height of pattern.
- **Double Bottom (W pattern)** — Two equal lows. Break of neckline = bullish.
- **Triple Top/Bottom** — Three tests of same level. Stronger than double.
- **Rounding Bottom (Saucer)** — Gradual accumulation over months. Bullish.
- **Rounding Top** — Gradual distribution. Bearish.
- **Diamond Top/Bottom** — Expanding then contracting range. Rare but powerful.
- **Rising Wedge** — Higher highs and higher lows but converging. Bearish despite uptrend.
- **Falling Wedge** — Lower highs and lower lows but converging. Bullish despite downtrend.

### Continuation Patterns:
- **Bull Flag** — Sharp uptrend (flagpole) then tight consolidation. Breakout continues up.
- **Bear Flag** — Sharp downtrend then tight consolidation. Breakdown continues down.
- **Bull Pennant** — Flagpole then symmetrical triangle. Breakout continues up.
- **Ascending Triangle** — Flat top, rising bottom. Breakout typically upward.
- **Descending Triangle** — Flat bottom, falling top. Breakdown typically downward.
- **Symmetrical Triangle** — Converging highs and lows. Breakout in prior direction.
- **Rectangle/Channel** — Horizontal consolidation. Breakout in prior direction.
- **Cup and Handle** — Rounding bottom (cup) then small pullback (handle). Breakout = bullish.
- **Measured Move** — After correction, expect continuation equal to prior leg.

---

## [CHUNK: FUNDAMENTAL_ANALYSIS_COMPLETE]
## Complete Fundamental Analysis Reference

### Valuation Ratios:
- **P/E (Price/Earnings)** — Compare to sector average, historical average. <15 = value, >30 = growth premium.
- **Forward P/E** — Uses next 12 months estimated earnings. More predictive than trailing.
- **PEG (P/E to Growth)** — P/E divided by earnings growth rate. < 1 = undervalued.
- **P/B (Price/Book)** — Compare to 1.0 (book value). Useful for banks, financials.
- **P/S (Price/Sales)** — Useful for unprofitable growth companies. < 2 = cheap for growth.
- **EV/EBITDA** — Enterprise value perspective. < 8 = cheap. Better than P/E for leveraged companies.
- **EV/EBIT** — Like EV/EBITDA but includes depreciation.
- **EV/FCF** — Uses free cash flow. Most important for cash generative businesses.
- **Price/Cash Flow** — Operating cash flow basis. Less manipulable than earnings.
- **Dividend Yield** — Annual dividend / price. > 4% = high yield.
- **Earnings Yield** — Inverse of P/E. Compare to bond yields for stock vs bond attractiveness.

### Quality Metrics:
- **ROE (Return on Equity)** = Net Income / Shareholders' Equity. > 15% = strong.
- **ROA (Return on Assets)** = Net Income / Total Assets. > 8% = efficient.
- **ROIC (Return on Invested Capital)** = NOPAT / Invested Capital. ROIC > WACC = value creation.
- **Gross Margin** = Gross Profit / Revenue. Higher = pricing power.
- **Operating Margin** = Operating Income / Revenue. > 15% = strong.
- **Net Margin** = Net Income / Revenue.
- **Free Cash Flow Margin** = FCF / Revenue. FCF > Net Income = quality earnings.
- **Asset Turnover** = Revenue / Total Assets. Efficiency metric.
- **Inventory Turnover** = COGS / Inventory. Rising = improving efficiency.
- **Days Sales Outstanding (DSO)** = Accounts Receivable / (Revenue/365). Rising DSO = collection problem.

### Growth Metrics:
- **Revenue CAGR** (1Y, 3Y, 5Y)
- **EPS CAGR** (1Y, 3Y, 5Y)
- **FCF CAGR**
- **Earnings estimate revision** (% change in consensus over 1/3/6 months)

### Balance Sheet Health:
- **Debt/Equity** — < 0.5 = conservative. > 2 = leveraged.
- **Net Debt/EBITDA** — < 2x = safe. > 4x = concerning.
- **Current Ratio** = Current Assets / Current Liabilities. > 1.5 = safe.
- **Quick Ratio** = (Current Assets - Inventory) / Current Liabilities. > 1.0 = safe.
- **Interest Coverage** = EBIT / Interest Expense. > 5x = comfortable.
- **Cash Conversion Cycle** = DSO + DIO - DPO. Lower = better cash management.

### Piotroski F-Score (9 points):
Profitability (4): ROA > 0, Operating CF > 0, ROA improved, Accruals < 0
Leverage/Liquidity (3): Debt ratio decreased, Current ratio improved, No new shares issued
Operating Efficiency (2): Gross margin improved, Asset turnover improved
Score 8-9 = Strong buy signal. Score 0-2 = Short signal.

### Altman Z-Score:
Z = 1.2(X1) + 1.4(X2) + 3.3(X3) + 0.6(X4) + 1.0(X5)
X1 = Working Capital / Total Assets
X2 = Retained Earnings / Total Assets
X3 = EBIT / Total Assets
X4 = Market Cap / Total Liabilities
X5 = Revenue / Total Assets
Z > 2.99 = Safe. 1.81-2.99 = Grey zone. < 1.81 = Distress.

**Sources:**
- https://stockanalysis.com/stocks/[TICKER]/financials/
- https://macrotrends.net/stocks/charts/[TICKER]/
- https://simplywall.st
- https://www.wisesheets.io
- https://www.gurufocus.com

---

## [CHUNK: SECTOR_ANALYSIS]
## Sector Analysis & Rotation Framework

### GICS Sectors (11):
1. **Energy** — Oil, gas, coal. Cyclical. Lags economic cycle.
2. **Materials** — Metals, mining, chemicals. Early cycle.
3. **Industrials** — Defense, aerospace, machinery, transportation. Mid cycle.
4. **Consumer Discretionary** — Retail, autos, restaurants. Early-mid cycle.
5. **Consumer Staples** — Food, beverages, household products. Defensive.
6. **Healthcare** — Pharma, biotech, devices. Defensive with growth.
7. **Financials** — Banks, insurance, REITs. Early-mid cycle.
8. **Information Technology** — Software, hardware, semiconductors. Mid-late cycle.
9. **Communication Services** — Telecom, media, internet. Mid cycle.
10. **Utilities** — Electric, gas, water. Defensive. Rises with bonds.
11. **Real Estate (REITs)** — Defensive-ish. Sensitive to interest rates.

### Economic Cycle Rotation:
- **Early Expansion:** Financials, Consumer Discretionary, Industrials
- **Mid Expansion:** Technology, Materials, Energy
- **Late Expansion:** Energy, Materials, Consumer Staples
- **Early Recession:** Consumer Staples, Healthcare, Utilities
- **Late Recession:** Financials, Consumer Discretionary (early recovery)

### Sector ETFs for Tracking:
- XLK (Tech), XLF (Financials), XLE (Energy), XLV (Healthcare)
- XLI (Industrials), XLY (Consumer Disc.), XLP (Consumer Staples)
- XLB (Materials), XLU (Utilities), XLRE (Real Estate)
- XLC (Communication Services)

**Relative Strength Signal:**
- Calculate each sector ETF return vs SPY
- If sector > SPY = sector in favor
- Rotate into outperforming sectors, out of underperforming

---

## [CHUNK: MACRO_INDICATORS_COMPLETE]
## Complete Macro Economic Indicators

### Federal Reserve / Interest Rates:
- **Fed Funds Rate** — Benchmark overnight lending rate. Most important number in markets.
- **FOMC Meeting Dates** — 8 per year. Market moves before and after.
- **Fed Dot Plot** — Projections of future rates by each Fed member.
- **Taylor Rule** — Formula for "correct" fed funds rate given inflation and output gap.
- **Neutral Rate (r*)** — Estimated rate that neither stimulates nor restricts.
- **Quantitative Easing (QE)** — Fed buys bonds = more money in system = stocks up.
- **Quantitative Tightening (QT)** — Fed sells bonds = less money = stocks down.
- **Fed Balance Sheet size** — Correlated with stock market level.

**Data Source:** https://www.federalreserve.gov/monetarypolicy/openmarket.htm

### Inflation Indicators:
- **CPI (Consumer Price Index)** — Monthly. Core CPI (ex food/energy) watched by Fed.
- **PCE (Personal Consumption Expenditures)** — Fed's PREFERRED inflation measure.
- **PPI (Producer Price Index)** — Input costs. Leads CPI by 1-3 months.
- **Breakeven Inflation Rate** — 10Y Treasury yield minus 10Y TIPS yield = market's inflation expectation.
- **Michigan Consumer Inflation Expectations** — Survey-based. Rising = hawkish Fed.

**Data Source:** https://www.bls.gov, https://fred.stlouisfed.org

### Growth Indicators:
- **GDP** — Quarterly. >2% = healthy. <0 for 2 quarters = technical recession.
- **ISM Manufacturing PMI** — >50 = expansion. <50 = contraction. Very important.
- **ISM Services PMI** — >50 = expansion. Services = 80% of US economy.
- **Markit/S&P Global PMI** — Alternative PMI. Flash estimate earlier in month.
- **Chicago PMI** — Leading indicator for ISM.
- **Industrial Production** — Monthly factory output.
- **Capacity Utilization** — >80% = tight, inflationary pressure.

### Employment:
- **Non-Farm Payrolls (NFP)** — First Friday of each month. MOST WATCHED data point.
- **Unemployment Rate** — Headline number. 4% = roughly "full employment."
- **U-6 Unemployment** — Broader measure including part-time + discouraged workers.
- **Initial Jobless Claims** — Weekly. < 300K = strong labor market.
- **ADP Employment** — Private payrolls, released 2 days before NFP.
- **JOLTS (Job Openings)** — Job openings, hires, quits. Quits rate = confidence measure.

### Consumer:
- **Retail Sales** — Monthly. Core retail (ex autos, gas) most watched.
- **Consumer Confidence** (Conference Board) — Monthly. 100+ = optimistic.
- **University of Michigan Consumer Sentiment** — Monthly. Forward-looking.
- **Personal Income and Spending** — Monthly. Both important.
- **Savings Rate** — High savings = potential future spending (bullish). Zero savings = fragile.

### Housing:
- **Existing Home Sales** — 90% of all home sales. Monthly.
- **New Home Sales** — 10% but more leading indicator.
- **Housing Starts** — New construction begun. Leads economy by 6-12 months.
- **Building Permits** — Even more leading than starts.
- **Case-Shiller Home Price Index** — Monthly home price changes.
- **MBA Mortgage Applications** — Weekly. Leading indicator for home sales.
- **30-year Fixed Mortgage Rate** — Drives affordability.

### Yield Curve:
- **10Y-2Y Spread** — Most watched. Inversion = recession coming in 12-18 months (historically).
- **10Y-3M Spread** — Alternative measure favored by Fed researchers.
- **30Y-5Y Spread** — Longer-term growth expectations.
- **2Y yield** — Tracks expected Fed rate. Rising 2Y = hawkish expectations.
- **10Y yield** — Long-term growth + inflation expectations.

**All yield data:** https://fred.stlouisfed.org/series/T10Y2Y

### Leading Economic Indicators:
- **Conference Board LEI (Leading Economic Index)** — Composite of 10 leading indicators.
  - Components: Stock prices, building permits, manufacturing hours, jobless claims,
    consumer expectations, ISM new orders, yield curve, credit conditions
- **Consecutive months of declining LEI = recession warning**

**Source:** https://www.conference-board.org/data/bcicountry.cfm

---

## [CHUNK: OPTIONS_STRATEGIES_COMPLETE]
## Complete Options Strategies Reference

### Basic Strategies:
- **Long Call** — Bullish. Limited risk, unlimited reward. Break-even = Strike + Premium.
- **Long Put** — Bearish. Limited risk. Break-even = Strike - Premium.
- **Covered Call** — Own stock + sell call. Income generation. Caps upside.
- **Cash-Secured Put** — Sell put with cash to buy shares. Acquire stock at discount OR collect premium.
- **Protective Put** — Own stock + buy put. Insurance.

### Spread Strategies:
- **Bull Call Spread** — Buy lower call, sell higher call. Defined risk, reduced cost vs long call.
- **Bear Put Spread** — Buy higher put, sell lower put. Defined risk bearish trade.
- **Bull Put Spread** — Sell higher put, buy lower put. Collect premium on bullish outlook.
- **Bear Call Spread** — Sell lower call, buy higher call. Collect premium on bearish outlook.
- **Calendar Spread** — Same strike, different expirations. Exploit time decay differential.
- **Diagonal Spread** — Different strike AND expiration. Directional + time decay play.

### Volatility Strategies:
- **Long Straddle** — Buy call + put same strike. Profit from big move either direction.
- **Short Straddle** — Sell call + put same strike. Profit from low volatility.
- **Long Strangle** — Buy OTM call + OTM put. Cheaper than straddle, needs bigger move.
- **Short Strangle** — Sell OTM call + OTM put. Wider profit zone than short straddle.
- **Iron Condor** — Short strangle + wings. Defined risk, profits in range.
- **Iron Butterfly** — Short straddle + wings. Higher premium, narrower range.
- **Ratio Spread** — Buy 1, sell 2+. Profit from small move, dangerous if large move.

### Advanced:
- **Jade Lizard** — Short put + short call spread. No upside risk.
- **Broken Wing Butterfly** — Asymmetric butterfly. Zero cost with credit.
- **PMCC (Poor Man's Covered Call)** — Deep ITM LEAPS + short call. Leveraged covered call.
- **Synthetic Long Stock** — Long call + short put same strike. Stock-like exposure, less capital.
- **Collar** — Long stock + long put + short call. Defined range.

### IV Percentile & Rank:
- **IV Percentile** — What % of days in past year had lower IV than today. >50% = sell options.
- **IV Rank** — Where today's IV sits between 52-week low and high. >50 = sell options.
- **Sell options when IV Rank > 50, buy options when IV Rank < 20.**

**Sources:**
- https://www.optionsprofitcalculator.com
- https://www.tastytrade.com/learn (best free options education)
- https://www.cboe.com/learncenter/
- https://optionstrat.com

---

## [CHUNK: RISK_MANAGEMENT_COMPLETE]
## Complete Risk Management Framework

### Position Sizing Methods:
1. **Fixed Fractional** — Risk fixed % of account per trade (1-2%)
   - Position size = (Account × Risk%) / (Entry - Stop)

2. **Kelly Criterion** — Optimal mathematical bet size
   - f* = (bp - q) / b
   - b = net odds (profit/loss ratio), p = win rate, q = 1-p
   - Use HALF Kelly in practice (too volatile at full Kelly)

3. **Volatility-Normalized Sizing** — Risk same in volatility units across positions
   - Position size = (Account × Risk%) / (ATR × Price)

4. **Equal Dollar Allocation** — Same dollar amount in each position
   - Simplest method, ignores volatility

5. **Risk Parity** — Equal RISK contribution from each position
   - Used by Ray Dalio's Bridgewater

### Portfolio-Level Risk:
- **Maximum Drawdown Limit** — Stop trading at -10% monthly drawdown
- **Correlation Management** — Avoid holding highly correlated positions simultaneously
- **VAR (Value at Risk)** — 95% or 99% VaR = max expected loss in normal conditions
- **Expected Shortfall (CVaR)** — Average loss beyond VaR level (better tail risk measure)
- **Stress Testing** — Simulate portfolio performance in 2008, 2020, 2022 scenarios
- **Sharpe Ratio** = (Return - Risk Free Rate) / StdDev. Target > 1.0.
- **Sortino Ratio** = (Return - Risk Free Rate) / Downside deviation. Better than Sharpe.
- **Maximum Drawdown** — Peak to trough loss. Lower = better.
- **Calmar Ratio** = CAGR / Max Drawdown. Target > 0.5.

### Stop Loss Types:
- **Percentage stop** — Exit at X% below entry
- **ATR stop** — Exit at N × ATR below entry (most recommended)
- **Swing stop** — Exit below recent swing low
- **Volatility stop** — Exit when price moves X standard deviations
- **Time stop** — Exit if trade doesn't work within N days
- **Mental stop** — No good. Always use hard stops.

### Trade Management:
- **Scale in** — Add to position as it proves itself (only in direction of trade)
- **Scale out** — Take partial profits at targets, trail stop on remainder
- **Break even stop** — Move stop to entry once profit = 1R
- **Trailing stop** — ATR trailing or percentage trailing behind price

### Psychological Risk Management:
- **Pre-trade checklist** — Always validate setup meets criteria before entry
- **Trade journal** — Record every trade with entry reason, exit reason, emotions
- **Revenge trading prevention** — Stop trading after 2 consecutive losses
- **Overtrading prevention** — Maximum N trades per day/week
- **FOMO prevention** — If missed entry, wait for next setup, never chase

---

## [CHUNK: HEDGE_FUND_STRATEGIES]
## Hedge Fund Strategy Types

### Long/Short Equity:
- Most common hedge fund strategy
- Long undervalued stocks, short overvalued stocks
- Net exposure varies: 0% net (market neutral) to 70% net long
- **130/30 funds** — 130% long, 30% short. Gross exposure = 160%.

### Global Macro:
- Trade based on macroeconomic views across all asset classes
- Instruments: currencies, interest rates, equity indices, commodities
- Examples: George Soros (broke Bank of England), Ray Dalio
- Key views: Relative value between country economies, central bank divergence

### Quantitative / Systematic:
- Purely rules-based, no discretion
- Renaissance Technologies (Medallion fund): highest known Sharpe ratio in history
- D.E. Shaw, Two Sigma, Citadel Securities
- Edge: Speed, data, holding periods milliseconds to days

### Distressed Debt:
- Buy debt of bankrupt or near-bankrupt companies
- Become largest creditor, influence restructuring
- Target: Buy at 40 cents on dollar, recover 70+ cents
- Paul Singer (Elliott Management) famous for this

### Activist Investing:
- Take large stake, push for strategic changes
- Carl Icahn, Bill Ackman, Nelson Peltz
- Catalysts: Spinoffs, buybacks, CEO change, strategic sale

### Multi-Strategy:
- Multiple strategies under one roof
- Citadel, Millennium Management, Point72
- Risk managed centrally, allocate capital to best opportunities

---

## [CHUNK: ALTERNATIVE_DATA]
## Alternative Data Sources (Hedge Fund Grade)

These are non-traditional data sources that hedge funds pay millions for. Some have free alternatives:

### Satellite Data:
- Count cars in retail parking lots (predict retail sales)
- Measure oil storage tank shadows (predict inventory data)
- Track ship movements (predict commodity flows)
- Free proxy: https://www.earthdata.nasa.gov (satellite imagery)

### Credit Card Transaction Data:
- Real-time consumer spending by merchant category
- Predict company revenue before earnings
- Services: Quandl (now Nasdaq Data Link), Second Measure
- Free proxy: Mastercard Spending Pulse, Visa data releases

### Web Scraping Signals:
- Job postings on LinkedIn/Indeed by company (growth signal)
- App store ratings and download ranks (consumer product health)
- Price changes on Amazon (inflation, margin pressure)
- Google Trends for product searches
- https://trends.google.com/trends/ (free)

### Mobile Location Data:
- Foot traffic to stores, restaurants, offices
- Remote work adoption rates by city/company
- Free proxy: https://www.safegraph.com (some free data)

### Shipping & Trade Data:
- https://www.maritimeoptional.com (ship tracking)
- https://panjiva.com (import/export data) — now S&P Global
- https://www.freightos.com/freight-resources/freightos-baltic-index/ (shipping rates)
- https://harpex.harperpetersen.com (charter rates)

### Patent & R&D Data:
- https://patents.google.com (patent filing activity)
- https://www.epo.org/searching-for-patents/data.html

### ESG & Non-Financial Data:
- https://www.msci.com/esg-ratings (ESG scores)
- https://www.sustainalytics.com (ESG risk ratings)
- Employee satisfaction → employee retention → productivity → margins
- https://www.glassdoor.com/research/ (Glassdoor workplace data)

### Congressional Trading:
- Members of Congress must disclose trades
- https://efts.house.gov/LATEST/search-index (House filings)
- https://www.senate.gov/reference/Index/FinancialDisclosure.htm (Senate filings)
- https://www.quiverquant.com/congresstrading/ (aggregated data)

### Insider Trading Data:
- https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=4 (Form 4 filings)
- https://openinsider.com (free, best aggregation)
- https://www.insiderscore.com
- Key: Cluster buying (3+ insiders buying simultaneously) = very bullish signal

---

## [CHUNK: BACKTESTING_PRINCIPLES]
## Backtesting Best Practices

### Common Biases to Avoid:
1. **Survivorship Bias** — Only testing on stocks that still exist. Dead companies excluded.
   - Fix: Use point-in-time databases that include delisted stocks
2. **Lookahead Bias** — Using data not available at the time of the signal.
   - Fix: Use only data available at signal time (e.g., earnings announced, not estimated)
3. **Data Snooping / Overfitting** — Testing many parameters, keeping only best.
   - Fix: Reserve out-of-sample data, use walk-forward analysis
4. **Slippage Neglect** — Assuming you trade at exact signal price.
   - Fix: Add 0.05-0.1% slippage per trade for liquid stocks, more for illiquid
5. **Transaction Costs** — Neglecting commissions.
   - Fix: Use realistic costs ($0 commission but 0.01-0.05% bid-ask spread)
6. **Position Sizing Neglect** — Testing P/L in points not in dollar terms.
   - Fix: Always test with realistic position sizing
7. **Liquidity Bias** — Can't actually trade at size in illiquid stocks.
   - Fix: Set minimum ADV (average daily volume) filter. Trade < 1% of ADV.

### Walk-Forward Analysis:
- Split data: 70% in-sample, 30% out-of-sample
- Optimize parameters on in-sample
- Test on out-of-sample (never look at this until done)
- Roll forward: Add new data, re-optimize, test next period
- **If OOS performance < 50% of IS performance, system is overfit**

### Monte Carlo Simulation:
- Randomize sequence of trade returns from backtest
- Simulate 10,000 portfolio paths
- Find 95th percentile worst drawdown
- Find probability of ruin
- More robust than single-path backtesting

### Minimum Criteria for Live Trading:
- Minimum 200+ trades in backtest (statistical significance)
- Positive OOS performance
- Sharpe Ratio > 0.5 (out of sample)
- Max drawdown < 3x expected annual return
- Consistent performance across different market regimes

---

## [CHUNK: CRYPTO_TRADING]
## Cryptocurrency Trading Specific

### On-Chain Metrics (Bitcoin & Ethereum):
- **NVT Ratio** (Network Value to Transactions) — Like P/E for crypto. High = overvalued.
- **MVRV Z-Score** — Market value vs realized value. High = expensive.
- **SOPR (Spent Output Profit Ratio)** — Are holders selling at profit or loss?
- **Exchange Netflows** — Coins moving TO exchanges = potential sell pressure
- **Whale Wallet Movements** — Large wallet transfers to exchanges = sell signal
- **Hash Rate** — Mining difficulty. Rising = bullish long-term.
- **Miner Revenue** — Miners under pressure sell BTC = bearish
- **Realized Price** — Average cost basis of all BTC ever moved. Below = capitulation zone.
- **HODL Waves** — Distribution of coin age. Old coins moving = distribution.
- **Funding Rates** — Perpetual swap funding. Positive = longs paying shorts = crowded long.
- **Open Interest** — Total futures contracts. Rising OI + price rise = strong trend. Rising OI + price fall = shorts building.

**Sources:**
- https://glassnode.com (best on-chain data, free tier available)
- https://look.into.bitcoin.com (NVT, MVRV, etc.)
- https://cryptoquant.com
- https://coinglass.com (futures/liquidations data)
- https://dune.com (custom on-chain queries)
- https://defillama.com (DeFi TVL data)

### Crypto-Specific Technical:
- **Halving cycles** — Every 4 years BTC supply halved. Historically 12-18 months of bull market post-halving.
- **Rainbow chart** — Log-scale price bands showing historical value zones.
- **Stock-to-Flow model** — Scarcity model (controversial but widely watched).
- **Bitcoin dominance** — BTC market cap % of total crypto. Falling dominance = altcoin season.
- **Crypto Fear & Greed Index** — https://alternative.me/crypto/fear-and-greed-index/

### Crypto Arbitrage:
- **Cross-exchange arbitrage** — Same asset, different price on different exchanges
- **Triangular arbitrage** — BTC/USD → BTC/ETH → ETH/USD pricing discrepancy
- **Funding rate arbitrage** — Long spot + short perpetual when funding rate very positive

---

## [CHUNK: FOREX_TRADING]
## Forex Trading

### Major Currency Pairs (Highest Liquidity):
- EUR/USD (Euro/US Dollar) — Most traded
- USD/JPY (US Dollar/Japanese Yen) — Risk barometer
- GBP/USD (British Pound/US Dollar) — "Cable"
- USD/CHF (US Dollar/Swiss Franc) — Safe haven
- AUD/USD (Australian Dollar/US Dollar) — Risk/commodity proxy
- USD/CAD (US Dollar/Canadian Dollar) — Oil correlation
- NZD/USD (New Zealand Dollar/US Dollar)

### Currency Drivers:
- **Interest rate differentials** — Higher rates = stronger currency
- **Inflation differentials** — Higher inflation = weaker currency
- **Current account balance** — Surplus = strong currency
- **Political stability**
- **Risk-on/risk-off** — Risk-on = AUD, NZD, EM up; Risk-off = JPY, CHF, USD up

### Forex-Specific Indicators:
- **COT (Commitment of Traders)** — CFTC weekly report. Shows positioning of commercials, non-commercials, retail.
  - When non-commercials (large speculators) at extreme net long = contrarian sell signal
  - Source: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- **PPP (Purchasing Power Parity)** — Fair value for currencies long-term
- **Real Interest Rate Differential** — Inflation-adjusted rate difference
- **DXY (Dollar Index)** — Basket of USD vs major currencies. Most important single forex indicator.

### Session Times (EST):
- Sydney: 5pm - 2am
- Tokyo: 7pm - 4am
- London: 3am - 12pm (most volume)
- New York: 8am - 5pm
- Best time: London/NY overlap 8am-12pm EST

---

## [CHUNK: DATA_SOURCES_MASTER]
## Master Data Sources Index

### Free Price Data:
- https://finance.yahoo.com/quote/AAPL/history (historical prices)
- https://query1.finance.yahoo.com/v8/finance/chart/AAPL (Yahoo Finance API)
- https://www.alphavantage.co/documentation/ (free API key needed)
- https://polygon.io/docs/stocks (5 calls/min free)
- https://api.nasdaq.com/api/quote/AAPL/historical (NASDAQ API)
- https://stooq.com/q/d/l/?s=aapl.us&i=d (Stooq free download)
- https://iexcloud.io (free tier available)

### Free Fundamental Data:
- https://stockanalysis.com/stocks/AAPL/financials/ (scraped fundamentals)
- https://macrotrends.net/stocks/charts/AAPL/apple/stock-price-history (long history)
- https://www.wsj.com/market-data/quotes/AAPL/financials/annual/income-statement
- https://simplywall.st/stocks/us/tech/nasdaq-aapl/apple (visualized fundamentals)
- https://gurufocus.com/term/pe/AAPL/PE-Ratio/Apple (guru focus ratios)

### Free Economic Data:
- https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS (FRED API)
- https://data.bls.gov/timeseries/LNS14000000 (BLS unemployment)
- https://api.census.gov/data/timeseries/econ/marts (Census retail sales)
- https://www.eia.gov/opendata/v1/qb.php (Energy data API)

### Free News & Sentiment:
- https://newsapi.org/v2/everything?q=AAPL (News API, free tier)
- https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL (Yahoo Finance RSS)
- https://stocktwits.com/api/2/streams/symbol/AAPL.json (social sentiment)
- https://www.reddit.com/r/wallstreetbets/search.json?q=AAPL (Reddit)

### SEC Filings:
- https://efts.sec.gov/LATEST/search-index?q=%22AAPL%22&dateRange=custom (full-text search)
- https://data.sec.gov/submissions/CIK0000320193.json (company submissions API)
- https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json (XBRL facts API — structured financials)
- https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AAPL&type=10-K (10-K filings)

### Options Data:
- https://query2.finance.yahoo.com/v7/finance/options/AAPL (Yahoo options chain)
- https://www.cboe.com/delayed_quotes/spx/quote_table (CBOE options)
- https://unusualwhales.com/options (unusual flow)

### Crypto Data:
- https://api.coingecko.com/api/v3/coins/bitcoin/market_chart (free)
- https://api.glassnode.com/v1/metrics/indicators/sopr (on-chain, limited free)
- https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1d (Binance futures)

### Global Markets:
- https://finance.yahoo.com/world-indices (global index quotes)
- https://markets.ft.com/data/indices/tearsheet/summary?s=INX:IOM (FT Markets)
- https://www.investing.com/indices/major-indices (global overview)

---

## [CHUNK: TRADING_PSYCHOLOGY]
## Trading Psychology & Behavioral Finance

### Cognitive Biases Affecting Traders:
- **Overconfidence bias** — Believe you know more than you do. Over-trade.
- **Confirmation bias** — Only see evidence supporting your existing position.
- **Loss aversion** — Losses feel 2x worse than gains feel good (Kahneman & Tversky).
  - Result: Cut winners too early, let losers run too long.
- **Anchoring bias** — Anchored to purchase price. "It was $200, now $150, it's cheap." (It might be going to $50.)
- **Recency bias** — Overweight recent events. After crash, expect more crashes. After rally, expect more rallies.
- **Disposition effect** — Sell winners (to feel good), hold losers (to avoid realizing loss).
- **Gambler's fallacy** — "It's been down 5 days, must go up soon." Trades are independent.
- **Hindsight bias** — "I knew that would happen." Distorts learning from mistakes.
- **Herd mentality** — Follow the crowd at tops and bottoms.
- **Dunning-Kruger** — Worst traders have most confidence.
- **FOMO (Fear Of Missing Out)** — Chase price after it's already moved.
- **Sunk cost fallacy** — Hold losing positions because "already lost so much."

### Mental Models for Better Trading:
- **Expected Value thinking** — A trade is good if EV positive, regardless of outcome.
- **Probabilistic thinking** — Any individual trade is random; only the distribution matters.
- **Process over outcome** — Follow the system. Bad outcome ≠ bad decision.
- **Premortem** — Before taking trade, ask "What would make me wrong?"
- **Red team** — Argue against your own trade thesis.

### Building a Trading Routine:
- Pre-market routine (market analysis, news, plan)
- During market routine (execute plan, no improvisation)
- Post-market routine (journal all trades, review)
- Weekly review (pattern recognition in mistakes)
- Monthly review (strategy performance vs expectation)

---

## [CHUNK: BACKTEST_PYTHON_TEMPLATE]
## Python Backtesting Template (Feed this to your bot as code)

```python
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# ─── DATA ───────────────────────────────────────────────────
def get_data(ticker, start='2015-01-01', end='2024-01-01'):
    df = yf.download(ticker, start=start, end=end)
    df.dropna(inplace=True)
    return df

# ─── INDICATORS ─────────────────────────────────────────────
def add_indicators(df):
    df['SMA_50']  = df['Close'].rolling(50).mean()
    df['SMA_200'] = df['Close'].rolling(200).mean()
    df['EMA_20']  = df['Close'].ewm(span=20).mean()
    df['ATR']     = (df['High'] - df['Low']).rolling(14).mean()
    df['RSI']     = compute_rsi(df['Close'], 14)
    df['BB_upper'] = df['Close'].rolling(20).mean() + 2 * df['Close'].rolling(20).std()
    df['BB_lower'] = df['Close'].rolling(20).mean() - 2 * df['Close'].rolling(20).std()
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ─── STRATEGY ────────────────────────────────────────────────
def generate_signals(df):
    # Example: Golden Cross + RSI filter
    df['Signal'] = 0
    df.loc[(df['SMA_50'] > df['SMA_200']) & 
           (df['SMA_50'].shift(1) <= df['SMA_200'].shift(1)) &
           (df['RSI'] > 50), 'Signal'] = 1   # BUY
    df.loc[(df['SMA_50'] < df['SMA_200']) & 
           (df['SMA_50'].shift(1) >= df['SMA_200'].shift(1)), 'Signal'] = -1  # SELL
    return df

# ─── BACKTEST ────────────────────────────────────────────────
def backtest(df, initial_capital=100000, risk_per_trade=0.02):
    position = 0
    capital = initial_capital
    entry_price = 0
    trades = []
    equity_curve = [capital]
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        
        if row['Signal'] == 1 and position == 0:
            stop_loss = row['Close'] - 2 * row['ATR']
            risk_amount = capital * risk_per_trade
            shares = int(risk_amount / (row['Close'] - stop_loss))
            position = shares
            entry_price = row['Close']
            trades.append({'type': 'buy', 'price': entry_price, 'shares': shares, 'date': df.index[i]})
            
        elif row['Signal'] == -1 and position > 0:
            exit_price = row['Close']
            pnl = (exit_price - entry_price) * position
            capital += pnl
            trades.append({'type': 'sell', 'price': exit_price, 'shares': position, 'pnl': pnl, 'date': df.index[i]})
            position = 0
            
        equity_curve.append(capital + (position * row['Close'] - position * entry_price if position > 0 else 0))
    
    return pd.Series(equity_curve, index=df.index[:len(equity_curve)]), trades

# ─── METRICS ─────────────────────────────────────────────────
def compute_metrics(equity_curve, trades):
    returns = equity_curve.pct_change().dropna()
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100
    cagr = ((equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (252 / len(equity_curve)) - 1) * 100
    sharpe = returns.mean() / returns.std() * np.sqrt(252)
    max_dd = ((equity_curve - equity_curve.cummax()) / equity_curve.cummax()).min() * 100
    win_trades = [t for t in trades if t.get('pnl', 0) > 0]
    win_rate = len(win_trades) / max(len([t for t in trades if 'pnl' in t]), 1) * 100
    
    print(f"Total Return:  {total_return:.2f}%")
    print(f"CAGR:          {cagr:.2f}%")
    print(f"Sharpe Ratio:  {sharpe:.2f}")
    print(f"Max Drawdown:  {max_dd:.2f}%")
    print(f"Win Rate:      {win_rate:.1f}%")
    print(f"Total Trades:  {len([t for t in trades if 'pnl' in t])}")
    
    return {'total_return': total_return, 'cagr': cagr, 'sharpe': sharpe, 'max_dd': max_dd, 'win_rate': win_rate}

# ─── RUN ─────────────────────────────────────────────────────
if __name__ == '__main__':
    df = get_data('SPY')
    df = add_indicators(df)
    df = generate_signals(df)
    equity, trades = backtest(df)
    metrics = compute_metrics(equity, trades)
    equity.plot(title='Strategy Equity Curve')
    plt.show()
```

---

## [CHUNK: RAG_METADATA_TEMPLATE]
## RAG Chunking & Metadata Template

When loading each chunk into your RAG system, tag with this metadata:

```json
{
  "chunk_id": "WYCKOFF_METHOD_001",
  "topic": "Technical Analysis",
  "subtopic": "Wyckoff Method",
  "asset_classes": ["equities", "crypto", "forex", "futures"],
  "timeframes": ["daily", "weekly"],
  "strategy_type": "volume_analysis",
  "complexity": "advanced",
  "source": "wyckoffanalytics.com",
  "last_updated": "2024-01",
  "keywords": ["accumulation", "distribution", "smart money", "volume", "spring", "upthrust"],
  "hedge_fund_usage": true,
  "popularity": "underrated"
}
```

### Recommended RAG Chunking Strategy:
1. Split by [CHUNK: NAME] tags in this document
2. Each chunk = 1 embedding
3. Add metadata fields above to each chunk
4. Use hybrid search: dense (semantic) + sparse (BM25 keyword)
5. Query with both concept and metadata filters
6. Example query: "What signals should I look for when entering a mean reversion trade on RSI?"
7. Retrieves: RSI_MEAN_REVERSION + CONNORS_RSI + BOLLINGER_BANDS chunks

### Vector DB Options:
- https://www.pinecone.io (managed, easiest)
- https://weaviate.io (open source, feature rich)
- https://www.chromadb.com (local, free, lightweight)
- https://qdrant.tech (Rust-based, fast)
- https://milvus.io (enterprise scale)

---

*Document Version: 2.0 | Created for RAG Training | Total Chunks: 30+*
*Update frequency recommended: Weekly for market data, Monthly for strategy content*
*DISCLAIMER: For educational purposes. Trading involves substantial risk of loss.*