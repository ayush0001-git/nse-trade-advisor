"""
build_complete_knowledge.py - Build the complete structured knowledge base.

Creates 9 category files from the uploaded trading_knowledge_complete_guide.html
plus a 100-book database organized into 15 categories, then indexes everything
into ChromaDB for RAG queries.

Structure:
  knowledge/
  ├── 01_foundations.md           Market mechanics, order types, asset classes
  ├── 02_technical_analysis.md    Candlesticks, patterns, indicators, advanced TA
  ├── 03_fundamental_analysis.md  Financials, valuation, moats, management
  ├── 04_options_derivatives.md   Options, Greeks, volatility, strategies
  ├── 05_quant_algo.md            Python, backtesting, ML, factor models
  ├── 06_advanced_strategies.md   Macro, event-driven, L/S, vol trading
  ├── 07_risk_management.md       Position sizing, stops, drawdowns, hedging
  ├── 08_psychology.md            Biases, discipline, drawdown management
  ├── 09_resources.md             Books, platforms, certifications
  ├── books_database.json         100 books in 15 categories
  ├── top20_priority_books.md     The 20 most important books (distilled)
  └── (existing files from before)
"""
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
KNOWLEDGE_DIR.mkdir(exist_ok=True)

# =========================================================================== #
#  1. FOUNDATIONS
# =========================================================================== #
FOUNDATIONS = """# FOUNDATIONS — Market Mechanics & Core Structure

> Years 1-3 · Beginner
> Market mechanics, vocabulary, and core structure — the bedrock every trader must know.

## Market Structure — How Markets Actually Work

- **Exchanges (NSE, BSE, NYSE, NASDAQ):** Centralized platforms matching buyers and sellers. NSE is India's largest (order-driven), BSE is oldest (Asia's first, 1875).
- **OTC markets vs exchange-traded:** OTC = bilateral, no central counterparty. Exchange = CCP guarantees. Always prefer exchange-traded for retail.
- **Dark pools and ATS:** Private exchanges for large institutional orders. Prevents market impact. ~30% of US volume is dark.
- **Bid-ask spread and market depth:** Spread = hidden cost. Liquid stocks: 1-5 paise. Illiquid: 50+ paise. Depth = how much you can trade without moving price.
- **Market makers and specialists:** Provide liquidity by quoting both sides. Profit from spread. In India: proprietary firms, not designated specialists.
- **Level 1, 2, and 3 quotes:** L1 = best bid/ask. L2 = full order book depth. L3 = ability to enter orders. Most retail gets L1 only.
- **Settlement cycles (T+1, T+2):** India moved to T+1 (Jan 2023). US is T+1 (May 2024). Faster settlement = less counterparty risk.
- **Circuit breakers and trading halts:** India: 10%/15%/20% index movement triggers halts. Stock-specific: 2%/5%/10%/20% depending on category.

## Order Types — Execution Mechanics

- **Market order (instant fill):** Guaranteed execution at best available price. Risk: slippage on illiquid stocks.
- **Limit order (price control):** Guaranteed price, not execution. Risk: missed fill if price doesn't reach limit.
- **Stop and stop-limit orders:** Stop = triggers market order at trigger price. Stop-limit = triggers limit order. Use stop-limit in volatile stocks to control fill price.
- **Trailing stop (% or Rs/$):** Moves with price. Locks profits while letting winners run. Essential for trend-following.
- **MOC / LOC / MOO orders:** Market-on-close, limit-on-close, market-on-open. Used by institutions for benchmark tracking.
- **IOC, FOK, GTC, DAY, GTD:** Immediate-or-cancel, fill-or-kill, good-till-cancelled, day, good-till-date. IOC most common for partial fills.
- **OCO (one-cancels-other):** Bracket orders — profit target and stop linked. When one fills, the other cancels.
- **Iceberg / reserve orders:** Large orders split to hide size. Only shows small visible quantity. Used by institutions.

## Asset Classes — What You Can Trade

- **Equities (stocks, ADRs):** Ownership shares. Common (voting) vs preferred (dividend priority). ADRs = foreign stocks traded in USD.
- **Fixed income (bonds, G-secs, T-bills):** Government bonds (G-secs, risk-free), corporate bonds (credit risk), T-bills (< 1 year). Safety vs yield tradeoff.
- **Commodities (gold, crude, agri):** MCX in India. Gold = safe haven. Crude = inflation proxy. Agri = seasonal/weather-driven.
- **Forex (currency pairs):** USDINR most traded in India. Spot, forwards, futures. Central bank intervention matters.
- **Derivatives (options, futures):** Contracts deriving value from underlying. Leverage tool. Most retail loses money here (SEBI data: 90%).
- **ETFs and index funds:** Basket of stocks in one ticker. NIFTYBEES, GOLDBEES. Low-cost diversification.
- **REITs and InvITs:** Real estate and infrastructure trusts. Income from rent/toll. New in India (2019+).
- **Crypto and digital assets:** Unregulated in India (30% tax, no offset). High volatility. Not for risk-averse.

## Market Participants — Who Trades and Why

- **Retail traders:** Individual investors. Growing fast in India (Zerodha, Groww). Often emotional, undercapitalized.
- **HNI and family offices:** High net worth individuals. Longer timeframes, diversified, use advisors.
- **FIIs and DIIs (India):** Foreign (FII) and Domestic (DII) Institutional Investors. FIIs drive trends; DIIs provide stability. Track daily flows.
- **Mutual and pension funds:** Long-only, benchmark-hugging. SIP flows = structural support for Indian markets.
- **Hedge funds (L/S, macro, quant):** Flexible mandates. Can short, use leverage, trade derivatives. Alpha-seekers.
- **Market makers:** Provide liquidity, profit from spread. HFT-adjacent. Essential for market health.
- **HFT and algo firms:** Latency-sensitive. Co-located servers at NSE. Profit from micro-inefficiencies.
- **Proprietary trading desks:** Trade firm's own capital. Investment banks, brokerages. Can take more risk than client-facing desks.

## Macro Indicators — Data That Moves Markets

- **GDP growth rate and revisions:** India 6-8% = strong. Revisions matter more than initial print. Rising GDP = bullish equities.
- **CPI / WPI (inflation):** CPI > 6% = RBI rate hike risk. WPI = wholesale. Rising inflation = bearish bonds, mixed for equities.
- **Non-Farm Payrolls (US):** First Friday of every month. Moves global markets including India. Strong NFP = USD strengthens, EM outflows.
- **RBI / FOMC rate decisions:** Rate cuts = bullish equities (cheaper capital). Rate hikes = bearish rate-sensitive sectors (NBFC, realty).
- **PMI (manufacturing + services):** > 50 = expansion. < 50 = contraction. Leading indicator for GDP.
- **IIP and core sector data:** Index of Industrial Production. Core sector = 8 key industries. Monthly data.
- **Current account deficit / fiscal:** CAD > 3% of GDP = rupee pressure. Fiscal deficit = government borrowing. Both affect sovereign rating.
- **Yield curve (2Y-10Y spread):** Inverted curve (2Y > 10Y) = recession signal. India: G-sec curve shape indicates rate expectations.

## Trading Costs — What Erodes Your Returns

- **Brokerage commissions:** Discount brokers (Zerodha, Groww): ₹0 delivery, ₹20/intraday F&O. Full-service: 0.1-0.5%.
- **STT / CTT (India-specific):** Securities Transaction Tax. Equity delivery: 0.1% sell. Intraday: 0.025% sell. Options: 0.0625% sell. Futures: 0.0125% sell.
- **Exchange and SEBI fees:** NSE transaction charge: 0.00297%. SEBI: ₹10/crore. Small but adds up.
- **Bid-ask spread (impact cost):** Hidden cost. Liquid stocks: 0.02%. Illiquid: 0.5%+. Always check spread before trading.
- **Slippage on large orders:** Market impact = price moves against you. Rule of thumb: stay under 1% of ADV per order.
- **Margin interest rates:** Funding cost for leveraged positions. MTF: 12-18% p.a. Overnight futures: ~9% implied.
- **Short-term vs long-term tax:** India: STCG (< 1 year) = 15%. LTCG (> 1 year) = 10% above ₹1L. Hold > 1 year for tax efficiency.
- **Currency conversion costs:** For US stocks: 1-2% spread + remittance fee. Use low-cost remittance (Vested, Winvesta).
"""

# =========================================================================== #
#  2. TECHNICAL ANALYSIS
# =========================================================================== #
TECHNICAL = """# TECHNICAL ANALYSIS — Price Action, Patterns & Indicators

> Years 2-10 · Intermediate
> Price action, patterns, and indicators — the language of market psychology encoded in charts.

## Candlestick Patterns — Single and Multi-Candle Signals

### Single Candle
- **Doji (indecision):** Open = close. Signals equilibrium. Context-dependent: at top = bearish, at bottom = bullish.
- **Hammer and hanging man:** Small body at top, long lower wick (≥2x body). Hammer at bottom = bullish reversal. Hanging man at top = bearish.
- **Shooting star and inverted hammer:** Small body at bottom, long upper wick (≥2x body). Shooting star at top = bearish. Inverted hammer at bottom = potential bullish.
- **Marubozu (strong conviction):** No wicks. Full body. Green marubozu = extreme bullish. Red = extreme bearish. Trend continuation signal.

### Two Candle
- **Bullish and bearish engulfing:** Current candle body completely engulfs prior. Strong reversal signal. Volume confirms.
- **Piercing line and dark cloud cover:** Opens beyond prior, closes at midpoint. Piercing = bullish. Dark cloud = bearish.
- **Harami (inside candle):** Small body inside prior large body. Indicates indecision/consolidation. Often precedes reversal.

### Three Candle
- **Morning star and evening star:** 3-candle reversal. Red → small body → large green (morning). Green → small → large red (evening). Strong reversal.
- **Three white soldiers and black crows:** 3 consecutive large candles same direction. Soldiers = bullish. Crows = bearish. Strong continuation.

## Chart Patterns — Multi-Bar Price Structures

### Reversal Patterns
- **Head and shoulders (+ inverse):** 3 peaks, middle highest. Neckline break confirms. Target = height below neckline. Inverse = bottom reversal.
- **Double top and double bottom:** Two peaks/troughs at same level. "M" = bearish. "W" = bullish. Volume should decline on second peak.
- **Rounding bottom and top:** Saucer shape. Slow reversal. Takes weeks/months. Volume increases with curvature.

### Continuation Patterns
- **Cup and handle:** U-shape + small pullback. Bullish continuation. Handle volume dries up. Breakout from handle = buy.
- **Bull and bear flags and pennants:** Sharp move + consolidation. Flag = rectangular. Pennant = triangular. Breakout in direction of prior move.
- **Ascending and descending wedge:** Converging trendlines. Ascending = bearish. Descending = bullish. Volume declines into apex.

### Other Patterns
- **Rectangle consolidation:** Price ranges between horizontal S/R. Breakout direction determines next move. Can be continuation or reversal.
- **Gap patterns (breakaway, runaway, exhaustion):** Breakaway = start of trend. Runaway = mid-trend (measuring gap). Exhaustion = end of trend. Gaps act as S/R.

## Moving Averages — Trend-Following Tools

- **SMA: 20, 50, 200-day:** Most watched. 200DMA = bull/bear dividing line. Golden cross (50 over 200) = bullish. Death cross = bearish.
- **EMA (exponential):** Faster reaction to recent prices. 12/26 EMA used in MACD. 20-EMA popular for short-term trend.
- **WMA, DEMA, TEMA:** Weighted MA, double/triple EMA. Reduced lag. DEMA popular for intraday.
- **Hull MA (HMA):** Lowest lag of all MAs. Smooth but responsive. Good for trend direction without whipsaws.
- **VWAP (volume-weighted):** Intraday benchmark. Price above VWAP = bullish intraday. Institutional reference point.
- **Anchored VWAP:** VWAP from a specific event (earnings, gap, IPO). Shows average cost since event. Strong S/R.
- **Golden cross and death cross:** 50DMA crosses 200DMA. Golden = bull. Death = bear. Lagging but psychologically significant.
- **MA ribbons for trend strength:** Multiple MAs stacked. Width indicates trend strength. Tight ribbon = consolidation.

## Momentum Oscillators — Overbought/Oversold Gauges

- **RSI (14-period): 70/30 levels:** > 70 = overbought. < 30 = oversold. But in strong trends, RSI can stay > 70 for weeks. Use divergence for signals.
- **RSI divergence (regular and hidden):** Regular = price higher high, RSI lower high (bearish). Hidden = price higher low, RSI higher low (bullish continuation).
- **MACD line, signal, histogram:** MACD = 12EMA - 26EMA. Signal = 9EMA of MACD. Histogram = MACD - Signal. Crossover = signal.
- **Stochastic %K and %D:** Oscillator 0-100. > 80 = overbought. < 20 = oversold. %K crossing %D = signal. Better in ranges than trends.
- **CCI (commodity channel index):** Measures deviation from MA. > +100 = overbought. < -100 = oversold. Good for identifying cycles.
- **Williams %R:** Similar to stochastic. -20 to 0 = overbought. -100 to -80 = oversold. Fast oscillator.
- **Rate of change (ROC):** Momentum = price change over N periods. Rising ROC = accelerating momentum.
- **Money flow index (MFI):** RSI with volume. > 80 = overbought. < 20 = oversold. Volume-weighted = more reliable than RSI alone.

## Volume Analysis — Smart Money Footprints

- **OBV (on-balance volume):** Cumulative volume. Rising OBV = accumulation. Falling = distribution. Divergence with price = warning.
- **Volume Profile (VAH, VAL, POC):** Volume by price level. POC = Point of Control (highest volume). VAH/VAL = Value Area High/Low. Strong S/R.
- **VWAP bands:** Standard deviation bands around VWAP. Upper band = overbought intraday. Lower = oversold. Mean reversion to VWAP.
- **Accumulation / distribution:** Rising price + rising volume = accumulation. Rising price + falling volume = distribution (warning).
- **Chaikin Money Flow (CMF):** > 0 = accumulation. < 0 = distribution. 20-period default. Confirms price action.
- **Unusual volume detection:** Volume > 3x average = institutional activity. Investigate for catalysts (news, earnings, block deals).
- **Order flow and delta analysis:** Buy volume vs sell volume per bar. Positive delta = aggressive buyers. Negative = aggressive sellers.
- **Footprint charts:** Bar-by-bar volume at each price. Shows where buyers/sellers are most active. Advanced tool.

## Volatility Indicators — Range and Explosion Tools

- **ATR (average true range):** Average daily range. Used for stop placement (2x ATR standard) and position sizing.
- **Bollinger Bands (2 SD):** 20SMA ± 2 standard deviations. Squeeze = low vol before breakout. Band tags = mean reversion in ranges.
- **BB squeeze:** When BB width narrows to 6-month low, breakout is imminent. Direction unknown — trade the breakout.
- **Keltner Channels:** ATR-based bands. Tighter than Bollinger. Good for trend following.
- **Donchian Channels (20/55 day):** Highest high / lowest low. Turtle Trading used 20-day breakout. Simple but effective.
- **Historical vs implied vol:** HV = realized past volatility. IV = option-implied expected vol. IV > HV = options expensive.
- **VIX / India VIX:** Fear gauge. > 30 = high fear (often bottoms). < 15 = complacency (often tops). Contrarian indicator.

## Support, Resistance and Fibonacci

- **Horizontal S/R levels:** Price memory. More times tested = stronger. Round numbers (1000, 1500) act as psychological S/R.
- **Dynamic S/R (MA as support):** Rising 50DMA acts as dynamic support in uptrend. Falling 50DMA = dynamic resistance in downtrend.
- **Pivot points (standard, Camarilla, Woodie):** Calculated from prior day H/L/C. R1/R2/R3 = resistance. S1/S2/S3 = support. Popular for intraday.
- **Fib 38.2%, 50%, 61.8% retracements:** Golden ratio. 61.8% = deepest pullback buyers accept. Beyond = trend change likely.
- **Fib extensions 127.2%, 161.8%, 261.8%:** Price targets beyond prior high/low. 161.8% = common target.
- **Fibonacci fans and arcs:** Diagonal S/R lines from Fib ratios. Less reliable than horizontal Fibs but useful for trend analysis.
- **Supply and demand zones:** Institutional order zones. Wider than S/R lines. Base = consolidation before sharp move. Trade = retest of base.

## Advanced Techniques — Professional-Grade Analysis

- **Elliott Wave (5-wave impulse, ABC correction):** 5 waves with trend (1,3,5 impulse; 2,4 correction). 3 waves against (A,B,C). Subjective = hard to trade mechanically.
- **Ichimoku Cloud (tenkan, kijun, kumo, chikou):** Japanese system. Cloud = support/resistance. Tenkan/Kijun cross = signal. Comprehensive but complex.
- **Wyckoff method (accumulation/distribution):** 4-phase cycle: Accumulation → Markup → Distribution → Markdown. Spring (false breakdown) = buy signal. Upthrust (false breakout) = sell.
- **Harmonic patterns (Gartley, Bat, Crab, Cypher):** Fibonacci-based geometric patterns. Precise entry/exit. Gartley most common. Requires patience.
- **Market Profile and TPO charts:** Time-Price Opportunity. Shows where market spent most time. Value area = 70% of volume. POC = fairest price.
- **Point and Figure charting:** Price-only, no time. X = up, O = down. Filters noise. Box size = sensitivity. Good for S/R identification.
- **Renko charts:** Brick-based. New brick only when price moves by brick size. Excellent for trend following. Eliminates time noise.
- **Heikin-Ashi candles:** Modified candles. HA close = (O+H+L+C)/4. Smooths price action. Good for trend identification. Doji = potential reversal.
"""

# =========================================================================== #
#  3. FUNDAMENTAL ANALYSIS
# =========================================================================== #
FUNDAMENTAL = """# FUNDAMENTAL ANALYSIS — Business Value & Quality

> Years 3-15 · Intermediate-Advanced
> Understand what a business is actually worth and whether the market is mispricing it.

## Financial Statements — Reading the Three Core Reports

### P&L (Income Statement)
- **Revenue:** Top line. Growth rate matters more than absolute number. Watch for one-time revenue boosts.
- **EBITDA:** Earnings before interest, tax, depreciation, amortization. Operating cash proxy. Margin trend = pricing power.
- **PAT (Profit After Tax):** Bottom line. But can be manipulated via accounting. Always cross-check with cash flow.
- **Margins:** Gross margin (revenue - COGS), operating margin (revenue - opex), net margin (PAT/revenue). Expanding margins = moat strengthening.

### Balance Sheet
- **Assets:** Current (cash, receivables, inventory) + Non-current (PPE, goodwill, intangibles). Watch intangibles/goodwill buildup (acquisition risk).
- **Liabilities:** Current (payables, short-term debt) + Non-current (long-term debt, deferred tax). Debt/equity < 0.5 = safe.
- **Equity:** Share capital + reserves. Book value = equity/shares. Negative equity = distress signal.
- **Working capital cycle:** Inventory days + receivable days - payable days. Shorter = better cash conversion.

### Cash Flow Statement
- **Operating cash flow (OCF):** Cash from core business. OCF > PAT = high quality earnings. OCF < PAT = accruals risk.
- **Investing cash flow:** CapEx + acquisitions. Negative = investing in growth. Positive = selling assets (could be distress).
- **Financing cash flow:** Debt raised/repaid + equity issued/bought back + dividends. Consistent buybacks = shareholder-friendly.
- **Free cash flow = OCF - CapEx:** The ultimate value metric. Positive and growing FCF = compounding machine.

### Quality Checks
- **Working capital cycle:** Shorter = better. Negative working capital (payables > receivables + inventory) = excellent (float).
- **Debt structure (secured vs unsecured):** Secured = assets pledged. Unsecured = higher rate but more flexibility. Watch refinancing risk.
- **Notes to accounts (hidden details):** Read footnotes! Related party transactions, contingent liabilities, off-balance-sheet items. Where the truth hides.
- **Restated vs reported numbers:** Restated = comparable after splits/bonuses. Always use restated for trend analysis.

## Valuation Multiples — Relative Pricing Tools

- **P/E ratio (trailing and forward):** Price/Earnings. Trailing = historical. Forward = consensus estimate. Forward P/E < trailing = growth expected.
- **PEG ratio (P/E ÷ earnings growth):** PEG < 1 = cheap relative to growth. PEG > 2 = expensive. Adjust for sustainability of growth.
- **EV/EBITDA (enterprise value basis):** Capital-structure neutral. Better than P/E for comparing leveraged vs unleveraged companies. EV = market cap + debt - cash.
- **EV/Sales (high-growth companies):** For companies with no earnings. < 2 = reasonable. > 10 = priced for perfection.
- **P/Book (asset-heavy industries):** Banks, insurance, capital goods. P/B < 1 = trading below book value (could be value trap).
- **P/FCF (quality check):** Price/Free Cash Flow. More reliable than P/E (earnings can be manipulated). < 15 = reasonable.
- **Sector-specific: P/AUM, EV/bbl, EV/bed:** Asset managers (P/AUM), oil (EV/barrel), hospitals (EV/bed). Use the right metric for the sector.

## DCF and Intrinsic Value — Absolute Valuation

- **WACC calculation (cost of debt + equity):** Weighted Average Cost of Capital. Cost of equity via CAPM: Rf + β(Rm-Rf). India: Rf ≈ 7%, Rm ≈ 12%.
- **Free cash flow projections:** Project 5-10 years of FCF. Revenue growth × margin × CapEx. Sensitivity analysis essential.
- **Terminal value (Gordon Growth, exit multiple):** TV = FCF(n+1) / (WACC - g). g = perpetual growth (2-3%). Exit multiple = EV/EBITDA at year n.
- **Sensitivity tables (WACC vs growth):** Small changes in WACC or growth = huge changes in intrinsic value. Always show range, not point estimate.
- **Reverse DCF (what is priced in?):** Start from current price, solve for growth rate. If implied growth > industry growth = overvalued.
- **DDM (dividend discount model):** For mature dividend payers. P = D1 / (r - g). Works for ITC, HINDUNILVR, coal companies.
- **Sum-of-the-parts (SOTP):** For conglomerates (RELIANCE, TATA). Value each business separately, sum up. Conglomerate discount = 15-25%.
- **NAV for real estate and asset-heavy:** Net Asset Value. Market value of all assets - liabilities. Used for REITs, real estate companies.

## Quality Metrics — Profitability and Capital Efficiency

- **ROE = Net profit / Equity:** Return on Equity. > 15% = good. > 25% = excellent. But watch leverage (high debt inflates ROE).
- **ROCE = EBIT / Capital employed:** Return on Capital Employed. Capital-structure neutral. > 15% = quality. Compare to cost of capital.
- **ROIC = NOPAT / Invested capital:** Return on Invested Capital. The ultimate quality metric. ROIC > WACC = value creation. ROIC < WACC = value destruction.
- **Gross, operating, net margins:** Trend matters more than level. Expanding margins = pricing power or cost efficiency.
- **Asset turnover ratio:** Revenue / Assets. Higher = more efficient. Low = capital-intensive. Compare within sector.
- **DuPont decomposition of ROE:** ROE = Net margin × Asset turnover × Equity multiplier. Identifies whether ROE comes from profitability, efficiency, or leverage.
- **Cash conversion cycle:** Days inventory + days receivable - days payable. Shorter = better. Negative = excellent (Amazon model).
- **Accruals ratio (earnings quality):** (PAT - OCF) / Assets. High accruals = low quality earnings. Low/negative accruals = high quality.

## Economic Moats — Competitive Advantage Sources

- **Network effects (more users = more value):** Exchanges (NSE), payments (Paytm), platforms (Zomato). Winner-take-all dynamics.
- **Cost advantages (scale, process, location):** RELIANCE (scale), Pidilite (process, brand), port companies (location). Hard to replicate.
- **Switching costs (customer lock-in):** ERP software, banks (account number change pain), Tally. High switching cost = sticky customers.
- **Intangibles (brands, patents, licenses):** ITC (brands), Sun Pharma (patents), BSE/NSE (licenses). Regulatory moats are strongest in India.
- **Efficient scale (natural monopoly):** One profitable player in a market. Exchanges, toll roads, pipelines. New entrants would destroy profitability for all.
- **Porter's Five Forces framework:** Threat of entry, supplier power, buyer power, substitutes, competitive rivalry. Score each 1-5 to assess moat.
- **Narrow vs wide moat durability:** Wide moat = lasts 20+ years (Coca-Cola). Narrow = 5-10 years (tech). Moat erosion = sell signal.
- **Moat erosion early warning signals:** Margin compression, market share loss, new entrants gaining, disruption. Act early.

## Management Analysis — Judging Leadership Quality

- **Promoter stake and pledging %:** High stake = aligned. Pledging = red flag (financial stress). > 25% pledged = high risk.
- **Capital allocation track record:** What do they do with cash? Reinvest (growth), buyback (value), dividend (income), acquisitions (empire-building). Track ROIC on each.
- **Related party transactions:** Deals with promoter entities. Should be arms-length. Excessive RPTs = wealth transfer red flag.
- **Annual report letter analysis:** Read the MD&A (Management Discussion & Analysis). Tone matters. "Cautiously optimistic" = worried. Specific numbers = confident.
- **Insider buying and selling patterns:** Cluster buying (3+ insiders in 30 days) = very bullish. CEO selling = watch but not automatic sell.
- **Corporate governance scores:** Proxy advisory firms (ISS, IiAS). Check for independent directors, audit quality, board composition.
- **Management guidance vs actual delivery:** Do they deliver what they promise? Consistent underdelivery = unreliable. Consistent beat = conservative (good).
- **Compensation vs performance:** CEO pay should correlate with shareholder returns. Excessive pay with poor returns = misaligned.

## Macro and Sector Rotation — Top-Down Investment Framework

- **Business cycle phases:** Expansion → Peak → Contraction → Trough. Different sectors outperform in each phase.
- **Sector rotation model:** Early cycle: discretionary, industrials, financials. Mid: tech, materials. Late: energy, staples. Recession: utilities, healthcare, staples.
- **Interest rate sensitivity by sector:** Rate hikes hurt: NBFCs, realty, autos, infra. Rate hikes help: banks (NIM), IT (USD).
- **Currency impact on exports / imports:** INR depreciation helps: IT, pharma, textiles. Hurts: oil importers, chemicals, electronics.
- **Credit cycle and liquidity analysis:** Easy credit = bull market. Tight credit = bear market. Track RBI liquidity measures, M3 growth.
- **FII / DII flow interpretation:** FII selling + DII buying = market holds up (SIP support). FII selling + DII selling = market crashes.
- **Commodity cycle impacts:** Crude up = paint, aviation, OMCs suffer. Crude down = paint, aviation benefit. Gold up = jewelers benefit.
- **Regulatory tailwinds and headwinds:** PLI schemes = manufacturing boost. Crypto ban = fintech affected. Track policy changes.
"""

# =========================================================================== #
#  4. OPTIONS & DERIVATIVES
# =========================================================================== #
OPTIONS = """# OPTIONS & DERIVATIVES — Leverage, Hedging & Income

> Years 5-20 · Advanced
> Most retail traders stop here. HNI traders master it. 90% of retail F&O traders lose money (SEBI).

## Options Basics — Fundamental Mechanics

- **Calls vs puts (rights, not obligations):** Call = right to BUY at strike. Put = right to SELL. Buyer pays premium. Seller receives premium.
- **Strike price, expiry, and premium:** Strike = exercise price. Expiry = last valid date. Premium = option price = intrinsic + time value.
- **ITM, ATM, OTM moneyness:** In-the-money = has intrinsic value. ATM = strike = spot. OTM = no intrinsic value. OTM options = lottery tickets (mostly expire worthless).
- **Intrinsic value vs extrinsic (time) value:** Intrinsic = max(0, spot-strike) for calls. Time value = premium - intrinsic. Time value decays (theta).
- **Option chain reading:** All strikes + premiums + OI + volume. Compare put OI vs call OI at each strike. High OI = S/R level.
- **Put-call ratio (PCR):** PCR > 1.3 = excessive fear (contrarian bullish). PCR < 0.7 = excessive greed (contrarian bearish). Track at index level.
- **Max pain theory:** Strike where option holders lose most. Price gravitates to max pain on expiry day. Especially strong in last 2 hours.
- **SEBI lot sizes (India F&O):** Each stock has a fixed lot size. NIFTY lot = 50 (was 25, changed multiple times). Check current lot sizes before trading.

## The Greeks — Sensitivity Metrics

- **Delta (Δ) — price sensitivity:** Call delta: 0 to 1. Put delta: 0 to -1. ATM call ≈ 0.50. Delta also ≈ probability of expiring ITM.
- **Gamma (Γ) — delta rate of change:** How fast delta changes. Highest for ATM options. Gamma risk = large near expiry. Long gamma = want volatility.
- **Theta (Θ) — time decay per day:** Negative for option buyers. Positive for sellers. Accelerates in last 2 weeks. Theta = enemy of buyers.
- **Vega (ν) — IV sensitivity:** How much option price changes with 1% IV change. High vega = sensitive to volatility. Long vega = want IV to rise.
- **Rho (ρ) — interest rate sensitivity:** Rarely matters for short-dated options. More relevant for LEAPS. Usually ignored.
- **Charm (delta decay over time):** How delta changes as time passes. Important for delta hedging over multiple days.
- **Vanna (delta vs IV cross):** How delta changes with IV. Matters for positions hedged on both delta and vega.
- **Volga / Vomma (vega convexity):** How vega changes with IV. Matters for vol-of-vol trading. Advanced.

## Volatility Concepts — The True Edge in Options

- **Historical vs implied volatility:** HV = realized past vol (from price data). IV = expected future vol (from option prices). IV > HV = options expensive.
- **IV rank (IVR) and IV percentile:** IVR = where current IV sits in 52-week range. IV percentile = % of days IV was lower. Both > 50 = elevated.
- **VIX / India VIX:** 30-day implied volatility of NIFTY options. Fear gauge. VIX > 30 = high fear. VIX < 15 = complacency. Mean-reverting.
- **Volatility skew (put skew, call skew):** OTM puts have higher IV than OTM calls (crash protection demand). Skew steepening = fear rising.
- **Volatility smile (index vs equity):** Equity options: smile (both wings high IV). Index options: skew (only put wing high). Smile = crash risk priced.
- **Vol surface (across strikes and dates):** 3D plot of IV by strike and expiry. Surface shape reveals market expectations. Trade vol surface dislocations.
- **Mean reversion of implied vol:** IV tends to revert to its average. Sell high IV, buy low IV. IV crush after earnings = classic mean reversion.
- **Event-driven IV crush after earnings:** IV rises before earnings (uncertainty). Drops after (certainty). Long options lose on IV crush even if direction is right.

## Basic Strategies — Starting Options Plays

- **Long call (bullish directional):** Max loss = premium. Max gain = unlimited. Breakeven = strike + premium. For high-conviction bullish views.
- **Long put (bearish directional):** Max loss = premium. Max gain = strike - premium. Breakeven = strike - premium. For high-conviction bearish views.
- **Covered call (income on holdings):** Sell call against stock you own. Income = premium. Caps upside. Good for flat/slightly bullish view on stock you hold.
- **Cash-secured put (income):** Sell put, hold cash to buy if assigned. Income = premium. Good for stocks you want to buy at lower price anyway.
- **Protective put (portfolio hedge):** Buy put against stock you own. Insurance against downside. Cost = premium. Good before events.
- **Collar (cap gains, limit loss):** Buy put + sell call (same stock). Zero-cost if premiums match. Caps upside, floors downside. Good for concentrated positions.
- **Bull and bear call spreads:** Buy lower strike call, sell higher strike call. Lower cost than naked call. Caps gain. Defined risk.
- **Bull and bear put spreads:** Buy higher strike put, sell lower strike put. Lower cost than naked put. Caps gain. Defined risk.

## Advanced Multi-Leg Strategies — Complex Structured Positions

- **Iron condor (range-bound markets):** Sell OTM put + call, buy further OTM put + call. Profit if price stays in range. Max profit = net premium. Good for high IV.
- **Iron butterfly (tight range):** Sell ATM straddle + buy OTM strangle. Higher premium than condor but narrower profit zone. Best for very stable stocks.
- **Long and short straddle:** Long = buy ATM call + put (profit from big move, direction unknown). Short = sell both (profit if no move). Short straddle = unlimited risk.
- **Long and short strangle:** Same as straddle but OTM. Cheaper to buy, lower probability. Short strangle = slightly safer than short straddle.
- **Calendar spread (time spread):** Sell near-month, buy far-month same strike. Profit from time decay differential. Good for range-bound stocks.
- **Diagonal spread:** Different strike + different expiry. Combines vertical and calendar. More flexible but complex.
- **Jade lizard:** Sell put + sell call spread. No upside risk. Profit if stock stays above put strike. Good for high-IV stocks you're neutral-bullish on.
- **Broken-wing butterfly:** Butterfly with skewed strikes. One side has no risk. Asymmetric risk/reward. Advanced.
- **Ratio spread and backspread:** Unequal number of longs and shorts. Ratio (e.g., 1:2) = sell 1, buy 2. Backspread = buy more than sell. Volatility plays.

## Futures and Other Derivatives — Beyond Options

- **Futures: margin and mark-to-market:** Margin = ~15-30% of contract value. MTM = daily P&L settled. If MTM loss exceeds margin, margin call.
- **Rollover (near to next month):** Exit near-month, enter next-month. Cost = spread + brokerage. Do before expiry week to avoid gamma risk.
- **Basis (futures - spot):** Futures usually trade at premium (cost of carry). Negative basis = backwardation (signals supply tightness or dividend).
- **Contango vs backwardation:** Contango = futures > spot (normal). Backwardation = futures < spot (scarcity). Gold often in backwardation.
- **Index futures for portfolio hedge:** Short NIFTY futures to hedge long equity portfolio. Beta-weight the hedge. Cheaper than buying puts.
- **Currency futures (USDINR, EURINR):** Trade on NSE. Used for hedging forex exposure or speculation. USDINR most liquid.
- **Commodity futures (MCX: gold, crude):** Gold = safe haven. Crude = inflation + geopolitics. MCX futures for hedging or speculation.
- **LEAPS (long-dated options):** 1+ year to expiry. Lower theta decay. Good for long-term views. Expensive in absolute terms but cheaper per day.
"""

# =========================================================================== #
#  5. QUANTITATIVE & ALGO TRADING
# =========================================================================== #
QUANT = """# QUANTITATIVE & ALGO TRADING — Systematic Strategies

> Years 8-25 · Advanced
> Build systematic strategies, automate execution, and replace emotion with math.

## Python Stack — Core Libraries to Master

- **pandas:** Data wrangling, time series. DataFrame = table. Series = column. Essential for any data work.
- **numpy:** Numerical computing. Arrays, matrices, math functions. Foundation for all other libraries.
- **matplotlib / plotly:** Charting. matplotlib = static. plotly = interactive. Use plotly for analysis, matplotlib for reports.
- **ta-lib / pandas-ta:** Technical indicators. ta-lib = C-based (fast but hard to install). pandas-ta = pure Python (easier).
- **scikit-learn:** ML models. Random Forest, XGBoost, SVM. For classification (up/down) and regression (return prediction).
- **statsmodels:** Econometrics. OLS regression, ARIMA, cointegration tests. For statistical validation.
- **scipy:** Statistical testing. t-test, KS test, correlation. For verifying edge is real (not luck).
- **vectorbt:** Vectorized backtesting. 100x faster than event-driven. Good for parameter sweeps.
- **alpaca-trade-api / ib_insync:** Execution APIs. Alpaca = US paper trading. IB = global. For live trading.

## Data Sources and APIs

- **yfinance (free, Yahoo Finance):** Free, no key. Good for research. 15-min delayed. Rate-limited. Not for live trading.
- **Alpha Vantage (free tier):** 25 requests/day free. Real-time + historical. API key required.
- **Polygon.io (real-time + historical):** Paid but excellent quality. Tick-level data. Good for US markets.
- **NASDAQ Data Link (Quandl):** Premium data. Economic, fundamental, alternative. Good for research.
- **NSE / BSE bhavcopy data:** Free. End-of-day. Official Indian data. Download from NSE archives.
- **Zerodha Kite Connect API (India):** Most popular Indian broker API. Real-time + historical + execution. ₹2000/month.
- **Upstox / Angel One APIs (India):** Alternative Indian broker APIs. Similar to Kite. Compare features and pricing.
- **Alpaca (US, free paper trading):** US broker with free paper trading API. Good for testing live execution.
- **CCXT (crypto, 100+ exchanges):** Unified API for 100+ crypto exchanges. Good for crypto algo trading.

## Backtesting — Testing Strategies on History

- **Vectorbt (vectorized, very fast):** 100x faster than event-driven. Good for parameter sweeps. But less realistic (no intrabar fills).
- **Backtrader (event-driven):** More realistic. Handles intrabar stops, partial fills. Slower but more accurate.
- **QuantConnect cloud (Lean engine):** Cloud-based. Free tier. Multi-asset. Good for institutional-grade backtests.
- **Zipline Reloaded:** Original Quantopian engine. Now community-maintained. Good for US equities.
- **Walk-forward optimization:** Split data into in-sample + out-of-sample. Optimize on IS, test on OOS. Roll forward. Prevents overfitting.
- **In-sample vs out-of-sample split:** Always hold out 30% of data for testing. Never optimize on test data. If results differ → overfit.
- **Overfitting and curve-fitting pitfalls:** More parameters = more overfit. Prefer simple strategies. If it doesn't work with 2 rules, 10 rules won't help.
- **Slippage and costs in backtest:** Always include: brokerage, STT, spread, slippage. Backtest without costs = fantasy. 0.1% per trade minimum.
- **Survivorship bias correction:** Only including current index members = survivorship bias. Include delisted companies for accurate backtest.

## Signal Generation — Alpha Ideas That Consistently Work

- **Momentum (12-1 month, weekly):** Buy top 20% by 12-month return (skip last month). Rebalance monthly. 2-4% annual alpha over 100 years.
- **Mean reversion (Z-score, RSI extremes):** Buy when Z-score < -2 or RSI(2) < 10. Sell at Z=0 or RSI > 50. Works on 1-5 day timeframe.
- **Breakout (Donchian, ATR-based):** Buy when price > 20-day high. Sell when < 10-day low. Turtle Trading classic. Trend-following.
- **Trend following (CTA-style, multi-timeframe):** Follow trends across multiple timeframes. Risk parity sizing. Crisis alpha (performs in crashes).
- **PEAD (post-earnings announcement drift):** Buy earnings beats, sell misses. Hold 30-60 days. Small but persistent edge. 1-3% drift.
- **Quality + momentum combo:** Buy high-ROIC stocks with positive momentum. Quality filter prevents value traps. Best combined strategy.
- **Seasonal and calendar effects:** Turn-of-month (buy last 4 days). Holiday effect (buy before holidays). Friday-to-Monday. Small but consistent.
- **Insider filing signals:** Buy after cluster insider buying (3+ in 30 days). 2-3% excess returns over 90 days. Track via SEC/NSE filings.

## Factor Models — Systematic Stock Selection

- **CAPM (single-factor, beta):** Expected return = Rf + β(Rm-Rf). Beta = market sensitivity. But beta doesn't fully explain returns.
- **Fama-French 3-factor (market, size, value):** Small beats large. High book-to-market beats low. Explains most return variation.
- **Carhart 4-factor (+ momentum):** Add momentum. 12-1 month momentum is persistent. The 4-factor model is industry standard.
- **AQR 6-factor model:** Add quality and low volatility. Quality (ROE, low debt) and low-beta both generate alpha. Comprehensive model.
- **Value factor (P/B, P/E, EV/EBITDA):** Cheap stocks outperform expensive stocks. But value can underperform for years (2010-2020 in US).
- **Momentum factor (12-1 month return):** Winners keep winning. Strongest factor in emerging markets. Crash risk (momentum crashes in V-shaped recoveries).
- **Quality factor (ROE, low debt):** High quality beats low quality. Most consistent factor. Combine with value for best results.
- **Low volatility factor (beta):** Low-beta stocks outperform on risk-adjusted basis. Contradicts CAPM. Anomaly persists globally.

## Statistical Arbitrage — Market-Neutral Quant Strategies

- **Pairs trading (co-integrated stocks):** Find 2 stocks that move together. Trade the spread when it diverges. Market-neutral.
- **Cointegration tests (Engle-Granger, Johansen):** Test if 2 stocks are cointegrated (long-term relationship). p < 0.05 = cointegrated. Not the same as correlation!
- **Z-score entry and exit rules:** Enter when spread Z > 2 (short outperformer, buy underperformer). Exit at Z = 0. Stop at Z = 4.
- **ETF vs component arbitrage:** ETF price vs sum of components. Mispricings are small and fleeting. Requires HFT infrastructure.
- **Index rebalancing arbitrage:** Buy before index inclusion, sell after. Front-running index funds. Works for NIFTY inclusions.
- **Calendar spread arbitrage:** Near vs far month futures. Trade the calendar spread. Low risk but small edge.
- **Cross-exchange arbitrage:** Same asset on 2 exchanges. Buy cheaper, sell expensive. Requires low latency.
- **Triangular arbitrage (forex):** USD → EUR → GBP → USD. Profit from pricing inconsistency. Requires HFT.

## ML for Trading — Machine Learning Applications

- **Feature engineering from OHLCV:** Create features: returns, volatility, RSI, MACD, volume ratios, patterns. Good features > good models.
- **Classification: up/down next day:** Binary classification. Accuracy > 55% = edge. But 55% with 2:1 R:R = profitable.
- **Regression: return magnitude:** Predict actual return. Harder than classification but more useful for position sizing.
- **XGBoost and Random Forest (tree ensemble):** Best for tabular data. Handle non-linear relationships. Robust to outliers. Feature importance = interpretability.
- **LSTM / GRU for sequences:** Recurrent neural networks for time series. Capture sequential patterns. But prone to overfitting on financial data.
- **Transformer models for time series:** Attention-based. State-of-art for sequence modeling. But need lots of data. Overkill for most trading.
- **NLP for earnings call sentiment:** Parse transcripts. Tone analysis. Management confidence score. Combine with fundamental data.
- **Reinforcement learning trading agents:** PPO, SAC, DQN. Agent learns by trading in simulated environment. Reward = risk-adjusted return.
- **Alternative data (satellite, credit card):** Satellite images of retail parking lots. Credit card transaction data. Web scraping. Edge before data becomes public.

## Trading Bot Architecture — End-to-End System Design

- **Data ingestion (live WebSocket feed):** Real-time tick data. WebSocket protocol. Buffer and clean. Handle disconnections.
- **Feature calculation layer:** Compute indicators on incoming data. Vectorized for speed. Cache historical values.
- **Signal / prediction module:** Apply strategy rules or ML model. Generate BUY/SELL/HOLD signals. Include confidence score.
- **Order management system (OMS):** Track orders from signal to fill. Handle rejections, partial fills, modifications. Idempotent.
- **Pre-trade risk checks (limits, drawdown):** Before every order: check position limits, daily loss limit, correlation exposure, drawdown circuit breaker.
- **Smart execution engine (TWAP / VWAP):** Split large orders. TWAP = time-sliced. VWAP = volume-weighted. Minimize market impact.
- **Position and PnL tracker:** Real-time P&L. Mark-to-market. Track R-multiples. Feed to risk manager.
- **Monitoring and alerting (Telegram / Slack):** Real-time alerts on fills, errors, drawdowns, signal generation. Mobile notifications.
- **Deployment: Docker on AWS or GCP:** Containerized for portability. Cloud for uptime. Auto-scaling for compute-intensive tasks.
"""

# =========================================================================== #
#  6. ADVANCED PROFESSIONAL STRATEGIES
# =========================================================================== #
ADVANCED = """# ADVANCED PROFESSIONAL STRATEGIES

> Years 15-40 · Expert
> Strategies used by hedge funds, prop desks, and long-tenured professionals.

## Global Macro — Top-Down World View Trades

- **Carry trade (borrow low, invest high yield):** Borrow in low-rate currency (JPY), invest in high-yield (INR, BRL). Profit from rate differential. Risk: currency reversal.
- **Currency devaluation plays:** Short currencies of countries with high debt, high CAD, falling reserves. Soros broke the Bank of England this way.
- **Commodity-linked currency correlations:** AUD = iron ore. CAD = crude. RUB = oil. BRL = iron/soy. Trade currency when commodity diverges.
- **Yield curve steepener / flattener trades:** Steepener = long short-end, short long-end (when curve will steepen). Flatten = opposite. Macro view on rates.
- **EM macro plays (India, Brazil, etc.):** Long EM when: USD weak, commodities rising, risk-on. Short EM when: USD strong, Fed hiking, risk-off.
- **Interest rate differential analysis:** Rate differential = currency driver. Widening differential favors higher-rate currency. Track central bank divergence.
- **Capital flow and positioning analysis:** Track FII flows, CFTC positioning, fund flows. Extreme positioning = contrarian signal.
- **Druckenmiller / Soros macro framework:** Top-down. Identify the single most important macro variable. Take large positions when conviction is high. Risk management is paramount.

## Event-Driven — Catalyst-Based Opportunities

- **Merger arbitrage (deal spread trading):** Buy target after deal announced. Profit = deal spread. Risk: deal breaks. Annualized returns: 8-12%.
- **Spin-offs and demergers:** Parent + spinoff often worth more separately (conglomerate discount). Buy parent before spinoff. Hold spinoff post-distribution.
- **Earnings surprise strategies:** Buy beats (hold 30-60 days for PEAD). Short misses. Position before earnings = gamble. Position after = strategy.
- **FDA / regulatory approval plays:** Pharma: buy before approval if you have edge (clinical trial data). Or buy after approval (momentum). India: USFDA approvals.
- **Rights issues and buybacks:** Rights issue = dilution (bearish unless at deep discount). Buyback = accretive (bullish if below intrinsic value).
- **Index inclusions and exclusions:** Buy before NIFTY inclusion (index funds must buy). Sell before exclusion. Front-running window: 2-4 weeks.
- **Block deals and bulk deal signals:** Large institutional trades. Direction depends on buyer/seller identity. FII buying = bullish. FII selling = bearish.
- **Distressed and special situations:** Bankruptcies, restructurings, NCLT cases. High risk, high reward. Need legal expertise. Howard Marks territory.

## Long / Short Equity — Institutional Hedge Fund Style

- **Gross vs net exposure management:** Gross = long + short. Net = long - short. 100/50 = 150 gross, 50 net. Higher net = more directional.
- **Sector-neutral L/S pairs:** Long HDFCBANK, short ICICIBANK (same sector). Removes sector risk. Pure stock-picking alpha.
- **Factor-neutral book construction:** Match factor exposures (size, value, momentum, beta) between long and short books. Pure alpha, no factor risk.
- **Short selling mechanics (borrowing):** Need to borrow shares. Borrow cost = fee. Hard-to-borrow = expensive. Recall risk = lender takes shares back.
- **Identifying frauds and accounting risks:** Red flags: receivables > revenue growth, frequent restructuring, auditor changes, related party transactions.
- **Mosaic theory research:** Combine public info from multiple sources. No single piece is material, but the mosaic is. Legal (not insider trading).
- **Alpha generation vs beta neutrality:** Alpha = skill. Beta = market. L/S aims for high alpha, low beta. Information Ratio = alpha / tracking error.
- **Portfolio beta management:** Target beta (e.g., 0.3). Adjust long/short ratio to hit target. Rebalance when beta drifts.

## Volatility as an Asset Class — Trading Vol Itself

- **Long volatility (buy before events):** Buy straddles before earnings, elections, policy decisions. Profit from IV rise + move. Risk: IV crush after event.
- **Short volatility (sell after IV spike):** Sell straddles when VIX > 30. IV mean-reverts. Profit from crush. Risk: tail event (unlimited loss).
- **VRP (volatility risk premium) harvesting:** IV > HV persistently. Sell vol (short straddles, short VIX futures). Collect VRP. Risk: vol spikes.
- **VIX futures term structure trades:** Contango (normal) = short front, long back. Backwardation = long front. Roll yield = profit source.
- **Dispersion trading (index vs single stocks):** Short index vol, long single stock vol. Profit when single stock vol > index vol (correlation decreases).
- **Correlation trading:** Trade implied correlation. Low correlation = index vol cheap vs single stock vol. High correlation = reverse.
- **Variance swaps:** OTC instrument. Pay fixed, receive realized variance. Pure vol trade. No delta/gamma management needed.
- **SVIX / VVIX analysis:** Vol of vol. VVIX > 100 = vol market stressed. Indicator of vol regime change.

## Fixed Income and Relative Value — Debt Market Strategies

- **Duration management:** Duration = interest rate sensitivity. Long duration = bet on rates falling. Short duration = bet on rates rising.
- **Yield curve trades:** Steepener = long short-end, short long-end. Flattener = opposite. Express view on curve shape change.
- **Credit spread trading:** Long corporate, short G-sec (bet spread narrows). Or reverse. Credit risk vs sovereign risk.
- **Convertible bond arbitrage:** Buy convertible, short stock (delta hedge). Profit from gamma + coupon. Classic hedge fund strategy.
- **G-sec vs corporate spread plays:** Spread widening = sell corporate, buy G-sec. Spread narrowing = reverse. Track credit cycle.
- **Repo / reverse repo carry:** Borrow via repo (short-term), invest in higher-yielding paper. Carry trade in fixed income.
- **Inflation-linked bond strategies:** Real vs nominal yield divergence. Buy inflation-linked when inflation expectations rising.
- **Mortgage-backed and ABS analysis:** Prepayment risk. Negative convexity (when rates fall, prepayments increase, duration shortens). Complex.

## CTA / Systematic Trend — Managed Futures Style

- **Trend following across asset classes:** Trade futures across equities, bonds, commodities, FX. Don't predict, follow. Cut losses, let profits run.
- **Time-series vs cross-sectional momentum:** TS = absolute momentum (vs own past). CS = relative momentum (vs peers). Most CTAs use both.
- **Lookback period optimization:** 1-3 months (fast) to 12 months (slow). Multi-period = more robust. Don't optimize too hard (overfitting).
- **Risk parity allocation:** Equal risk per market, not equal capital. Vol-scaled positions. More markets = more diversification.
- **AHL, Man Investments, Winton approach:** Systematic. 50+ markets. Trend + carry + value. Long volatility (crisis alpha).
- **Crisis alpha properties:** CTAs profit in crashes (2008, 2020). Negative correlation to equities in tails. Portfolio diversifier.
- **Managed futures as portfolio hedge:** 10-20% allocation to CTA reduces portfolio drawdown. Insurance that pays in crashes.
- **CTA as uncorrelated return stream:** Low correlation to stocks and bonds. Pure alpha (if trend persists). Sharpe ~0.5-0.8.
"""

# =========================================================================== #
#  7. RISK MANAGEMENT
# =========================================================================== #
RISK_MGMT = """# RISK MANAGEMENT — The Discipline That Separates Survivors from Blow-Ups

> Throughout career · Non-negotiable
> Most traders fail here, not in their strategy. Risk management is the real alpha.

## Position Sizing — How Much to Risk Per Trade

- **Fixed fractional (1-2% rule):** Risk 1-2% of capital per trade. 20 consecutive losses at 1% still leaves 80% of capital. Survival first.
- **Kelly criterion (full and fractional):** f* = (bp - q) / b. b = odds, p = win prob, q = 1-p. Full Kelly too volatile. Quarter-Kelly = professional standard.
- **Optimal F (Ralph Vince):** Maximize geometric growth. More aggressive than Kelly. Sensitive to parameter estimation. For advanced traders.
- **Volatility-adjusted sizing (ATR-based):** rupees_at_risk / (ATR × multiplier) = quantity. Higher ATR = smaller position. Normalizes risk across stocks.
- **Equal weight vs risk-parity weight:** Equal weight = simple but risky (volatile stocks dominate risk). Risk parity = equal risk per position (better).
- **Conviction-based sizing:** Scale up for high-conviction (80+ score) trades. Scale down for low-conviction. Cap at 2% risk even for highest conviction.
- **Max position limit (concentration risk):** Max 25% of capital in one stock. Max 5 positions in one sector. Diversify across uncorrelated bets.
- **Correlation-adjusted sizing:** If 2 stocks have 0.8 correlation, holding both = 1.8 bets not 2. Reduce size when correlation is high. Count bets, not positions.

## Stop Loss Framework — Define Max Pain Before Entry

- **Hard stop (structural technical level):** Below recent swing low (long) or above swing high (short). Structural = market-validated level.
- **ATR-based stop (2× or 3× ATR):** 2× ATR = standard. 3× ATR = wider (for volatile regimes). Normalizes stop distance to stock's own volatility.
- **Trailing stop (lock in profits):** Move stop up as price rises. At +1R: trail to breakeven. At +2R: trail to +1R. Let winners run, cut losers.
- **Time-based stop (eject slow trades):** If no progress in 20 bars, exit. Dead money = opportunity cost. Free capital for better setups.
- **Volatility-adjusted stop:** Wider stops in high-vol regime (3× ATR). Tighter in low-vol (1.5× ATR). Adapt to regime.
- **Support / resistance stop placement:** Place stop just below support (long). Not at round numbers (too obvious). Avoid clusters where everyone's stop is.
- **Mental stop vs hard order (discipline):** Mental stop = requires discipline. Hard order = guaranteed execution. Use hard orders unless you're very disciplined.
- **Stop-limit vs stop-market on gap risk:** Stop-market = guaranteed fill, maybe bad price. Stop-limit = guaranteed price, maybe no fill. Gap risk: prefer stop-market.

## Risk Metrics — Measuring Your Edge Statistically

- **Sharpe ratio (return / vol):** (Return - Rf) / Std(Return). > 1 = good. > 2 = excellent. > 3 = suspicious (probably overfit or data error).
- **Sortino ratio (downside vol only):** Like Sharpe but only penalizes downside vol. Better for asymmetric returns. > 1.5 = good.
- **Calmar ratio (return / max drawdown):** Annual return / max drawdown. > 1 = good. > 3 = excellent. Measures recovery speed.
- **Max drawdown (peak-to-trough):** Largest peak-to-trough decline. The number that matters most psychologically. > 20% = hard to recover from.
- **VaR: 95% / 99% confidence:** Value at Risk. "With 99% confidence, I won't lose more than ₹X in one day." But tail risk beyond VaR = the real danger.
- **CVaR / Expected shortfall:** Average loss when VaR is breached. Better than VaR (captures tail). The "worst case" beyond the "bad case."
- **Win rate × reward:risk = expectancy:** E[R] = Win% × AvgWin - Loss% × AvgLoss. Positive expectancy = profitable system. Track in R-multiples.
- **Omega ratio:** Gain-weighted / loss-weighted ratio. Captures full distribution. > 1 = profitable. Better than Sharpe for non-normal returns.

## Portfolio Construction — Building a Well-Diversified Book

- **Modern Portfolio Theory (MPT):** Diversify to reduce risk without reducing return. Efficient frontier = max return per unit risk.
- **Efficient frontier and Sharpe optimization:** Find portfolio with highest Sharpe ratio. But sensitive to input estimates (garbage in, garbage out).
- **Black-Litterman model:** Combines market views with investor views. More robust than pure MPT. Used by institutional investors.
- **Correlation matrix management:** Monitor pairwise correlations. In crises, correlations → 1 (everything falls together). Diversification fails when needed most.
- **Factor exposure control:** Decompose portfolio into factor exposures (market, size, value, momentum, vol). Avoid unintended factor bets.
- **Risk parity (equal risk, not equal weight):** Allocate so each position contributes equal risk. Vol-scaled. Better than equal weight for diversification.
- **Rebalancing frequency:** Monthly or quarterly. Too frequent = transaction costs. Too infrequent = drift. Tax-loss harvesting in December.
- **Liquidity bucketing:** Bucket positions by liquidity (T+1, T+5, T+30). Ensure you can exit 30% of book in 1 day. Don't get trapped in illiquid positions.

## Drawdown Management — Surviving Losing Streaks

- **Account-level max drawdown limits:** If account DD > 20%, stop trading. Review everything. Paper trade until confidence returns.
- **Daily loss limits (kill switch):** Max loss per day = 3% of capital. Hit it → close all positions, stop for the day. Prevents tilt.
- **Reduce size progressively in drawdown:** At 5% DD: reduce to 0.75% risk. At 10% DD: 0.5% risk. At 15% DD: stop. Prevents death spiral.
- **Monte Carlo simulation (worst case):** Simulate 10,000 random trade sequences. What's the worst possible DD? If > 50%, the system is too risky.
- **Consecutive loss rules:** 5 losses in a row → halve size. 7 losses → stop for 1 week. 10 losses → review entire system. Prevents catastrophic tilt.
- **Tilt detection in systematic systems:** If live performance deviates > 2σ from backtest expectation, system may be broken. Investigate.
- **Recovery time analysis (R-multiple):** How long to recover from DD? 1R DD = 1 winning trade. 5R DD = 5 winners. Track recovery, not just drawdown.
- **Avoiding revenge trading:** After a loss, take 10-minute break. After 3 losses, take 1-hour break. After 5 losses, stop for the day. Rule = non-negotiable.

## Hedging Techniques — Portfolio Insurance

- **Put options as portfolio insurance:** Buy NIFTY puts. Cost = premium. But floors downside. Like insurance: hope you don't need it, glad you have it.
- **Index futures short hedge:** Short NIFTY futures. Beta-weight the hedge. Cheaper than puts but no convexity (linear hedge).
- **Delta hedging options positions:** Adjust underlying position to keep delta neutral. Eliminates directional risk. But gamma/theta remain.
- **Short sector ETF as sector hedge:** Long bank stocks + short BANK NIFTY futures. Removes sector risk. Pure stock-picking alpha.
- **Currency hedge (for international holdings):** Short USDINR futures to hedge US stock exposure. Eliminates currency P&L. Cost = hedging premium.
- **VIX / India VIX calls as tail hedge:** Buy VIX calls. Profit from fear spikes. Small cost. Pays off in crashes (negative correlation to equity).
- **Gold as portfolio hedge:** Gold has low correlation to equities. 5-10% allocation. Safe haven in crises. No yield = opportunity cost.
- **Negatively correlated asset allocation:** Allocate to assets that rise when equities fall (long bonds, gold, VIX). Structural diversification.
"""

# =========================================================================== #
#  8. PSYCHOLOGY
# =========================================================================== #
PSYCHOLOGY = """# TRADING PSYCHOLOGY & DISCIPLINE — The Real Edge

> Throughout career · The real edge
> A perfect strategy is worthless if you can't execute it consistently.

## Cognitive Biases — Enemies of Rational Trading

- **Confirmation bias (cherry-picking data):** Seeking info that confirms existing view. Solution: actively seek counter-arguments. Bear case for longs, bull case for shorts.
- **Loss aversion (holding losers too long):** Losses hurt 2x more than gains feel good. Leads to: holding losers (hoping they come back), selling winners too early.
- **Overconfidence (after win streaks):** 3 wins → feel invincible → size up → blow up. Position size is based on system, not mood. Never increase size after wins.
- **Anchoring (to entry price):** Fixating on entry price. "I'll sell when it gets back to my entry." Market doesn't care about your entry. Trade the current setup, not your P&L.
- **Recency bias (last event = new norm):** Recent crash = "market always crashes." Recent bull = "stocks only go up." Use 20-year data, not 20-day.
- **Sunk cost fallacy:** "I've already lost so much, I can't sell now." Wrong. The money is gone. The question is: would you buy at current price? If no, sell.
- **Availability heuristic:** Overweighting easily-recalled events. Big crash = think crashes are common. They're not. Use base rates, not vivid memories.
- **Herding and social proof:** Following the crowd. "Everyone is buying, so it must be good." The crowd is wrong at extremes. Be contrarian at sentiment extremes.
- **Hindsight bias:** "I knew it!" You didn't. Keep a trading journal to see what you actually predicted vs what you think you predicted.

## Behavioral Finance — Academic Frameworks to Know

- **Prospect theory (Kahneman and Tversky):** How people actually make decisions under risk (not rationally). Key insight: losses hurt 2x more than gains feel good.
- **Mental accounting (separate pots):** Treating money differently based on source. "House money" effect = gambling with profits. All money is the same.
- **Disposition effect (sell winners, hold losers):** Most common trading bias. Sell winners to "lock in" gains. Hold losers to "avoid realizing" losses. Kills returns.
- **Endowment effect:** Valuing what you own more than what you don't. "My stock is worth more." No, it's worth the market price. Trade objectively.
- **Status quo and inertia bias:** Preference for current state. Don't rebalance. Don't sell. Don't change strategy. Inertia = death in markets.
- **Framing effect:** Same info, different presentation → different decision. "90% survival" vs "10% mortality" = same thing, different feeling. Frame in absolutes.
- **Regret theory:** Anticipated regret drives decisions. "If I sell and it goes up, I'll regret it." But opportunity cost of holding is real. Trade the setup.
- **Animal spirits (Keynes):** Markets driven by emotion, not just reason. Confidence, fear, greed, hope. These create trends and reversals. Can't be modeled purely rationally.

## Discipline Systems — Routines That Enforce Rules

- **Written trading plan (pre-trade):** Before entering: why? What's the setup? What's the stop? What's the target? What's the size? Write it down. No plan = no trade.
- **Daily trading journal (post-trade):** After every trade: was it a win/loss? Was the plan followed? What did I learn? Review weekly. Patterns emerge.
- **Pre-market routine (watchlists, levels):** 15 min before open: scan overnight news, check global markets, mark S/R levels, identify setups. Be prepared.
- **Post-market review (wins and losses):** 15 min after close: review all trades. Did I follow rules? What would I do differently? Honest self-assessment.
- **Weekly performance review:** Every weekend: P&L, win rate, R-multiple, mistakes. Track trends. Are you improving? What needs work?
- **Rules-based trading (remove discretion):** The more rules, the less emotion. If X then Y. No "I think." No "maybe." Mechanical execution of a tested system.
- **Accountability partner:** Someone who reviews your trades. Calls out your BS. Keeps you honest. Trading is lonely — find a partner or mentor.
- **Meditation and stress management:** Trading is stressful. Meditation = better decision-making under stress. Even 10 min/day improves clarity. Exercise, sleep, nutrition matter.

## Managing Drawdowns Mentally — Survive and Come Back Stronger

- **Normalize losing trades as part of process:** Losing is part of trading. Even the best lose 40% of trades. Focus on process, not outcome. A good loss (plan followed) > a bad win (plan broken).
- **Separate outcome from process quality:** Good process + bad outcome = fine. Bad process + good outcome = lucky (will revert). Judge yourself on process adherence, not P&L.
- **FOMO management protocol:** "I missed the 20% move." There's always another trade. Missing a move costs nothing. Chasing a move costs everything. Have a FOMO protocol: wait for setup, don't chase.
- **Reduce risk when in emotional tilt:** Tilt = emotional state where you make bad decisions. After 3 losses, reduce size 50%. After 5 losses, stop for the day. Tilt = the enemy.
- **Take time off after large losses:** Big loss = emotional shock. Don't trade the next day. Take 2-3 days. Review. Come back fresh. Markets will be there.
- **Simulated trading after blow-ups:** After a big loss, paper trade for 1-2 weeks. Rebuild confidence without risk. Transition back to real money gradually.
- **Process goals vs result goals:** Bad: "I want to make ₹50,000 this month." Good: "I will follow my trading plan on 100% of trades." Process goals are controllable. Result goals create pressure.
- **Flow state and zone trading:** Flow = total absorption in the task. No emotion, no thinking, just execution. Achieved through: clear rules, immediate feedback, challenge matches skill. The zone = peak performance.

## Building a Trader's Edge — Long-Term Development Framework

- **Specialize in 1-2 instruments and setups:** Don't trade everything. Pick 1-2 setups (e.g., earnings breakout, support bounce). Master them. 1 setup traded 1000 times > 100 setups traded 10 times.
- **Pattern recognition through repetition:** Screen time = experience. 500 trades in a setup = you see patterns others don't. 50 trades = still learning. Put in the reps.
- **Deliberate practice (10,000-hour model):** Not just screen time, but DELIBERATE practice. Review trades. Identify mistakes. Drill corrections. Focused improvement.
- **Review 500+ trades in journal retrospectively:** After 500 trades, patterns emerge. Your most profitable setup. Your biggest leak. Your tilt triggers. Data > intuition.
- **Mentor or mastermind groups:** Learn from someone who's done it. Or peer group of traders. Share trades, review each other, hold accountable. Accelerates learning 5-10x.
- **Screen time accumulation (reps):** No substitute. Watch markets for thousands of hours. See thousands of setups. Build intuition that can't be taught, only earned.
- **Measure performance, not just P&L:** Track: win rate, R-multiple, expectancy, Sharpe, max DD, average hold time, plan adherence rate. P&L is a lagging indicator. Process metrics are leading.
- **Continuous learning system:** Markets evolve. What worked in 2020 may not work in 2025. Read, study, adapt. But don't chase every new idea. Core principles don't change.
"""

# =========================================================================== #
#  9. RESOURCES
# =========================================================================== #
RESOURCES = """# RESOURCES & TOOLS — The Definitive Reading List

> All levels
> The complete professional toolkit: books, platforms, data tools, and certifications.

## Essential Books (by category)

### Psychology · Must-read
- **Trading in the Zone** — Mark Douglas | All levels | The psychology bible. Think in probabilities, not certainties.

### Psychology · Classics
- **Market Wizards series (4 books)** — Jack D. Schwager | Beginner-Expert | Interviews with top traders. Timeless wisdom.

### Classic memoir
- **Reminiscences of a Stock Operator** — Edwin Lefèvre (Jesse Livermore) | Classic | Price action principles still relevant 100 years later.

### Technical analysis
- **Technical Analysis of Financial Markets** — John J. Murphy | Technical bible | Comprehensive TA reference.

### Options
- **Options as a Strategic Investment** — Lawrence G. McMillan | Options | Comprehensive options strategies.
- **Option Volatility and Pricing** — Sheldon Natenberg | Volatility, Greeks | The options pricing bible.

### Quantitative trading
- **Quantitative Trading** — Ernest P. Chan | Algo, Python | Practical quant trading with Python.
- **Advances in Financial ML** — Marcos López de Prado | ML, Expert | Advanced ML for finance. Overfitting, cross-validation.

### Fundamental / Value
- **The Intelligent Investor** — Benjamin Graham | Value, Must-read | The foundation of value investing.
- **Competition Demystified** — Bruce Greenwald | Moats | How to identify competitive advantages.

### Risk and position sizing
- **The New Money Management** — Ralph Vince | Kelly, Optimal F | Mathematical position sizing.

### Systematic / trend following
- **Following the Trend** — Andreas Clenow | CTA, Systematic | How trend-following CTAs actually work.

### Global macro
- **The Alchemy of Finance** — George Soros | Macro, Reflexivity | Soros's framework: reflexivity.

### India markets
- **Coffee Can Portfolio** — Saurabh Mukherjea | India, Quality investing | Long-term quality investing in India.

### Wyckoff / Price action
- **Trades About to Happen** — David H. Weis | Wyckoff, Volume | Modern Wyckoff method.

### Market microstructure
- **Trading and Exchanges** — Larry Harris | Microstructure, Expert | How markets actually work.

## Platforms and Charting Tools

- **TradingView** | Charting (global) | Best-in-class charts + Pine Script alerts | Free tier, all devices
- **Sensibull / Opstra** | Options analytics (India) | Option chain, Greeks, P&L diagrams | India F&O
- **Screener.in / Ticker.finology** | India fundamental screener | India-specific fundamental screening | Free
- **Finviz / Stock Analysis** | US screener | Technical + fundamental filter combo | US markets
- **QuantConnect (Lean engine)** | Backtesting / quant | Cloud algo testing with free tier | Python
- **Sierra Chart / Bookmap** | Order flow (advanced) | Footprint charts, order flow analysis | Pro

## Certifications and Courses

- **CMT (Chartered Market Technician)** | Technical | CMT Association, 3 levels | Gold standard TA
- **CFA (Chartered Financial Analyst)** | Finance | CFA Institute, 3 levels | Fundamental
- **CQF (Certificate in Quantitative Finance)** | Quant | Wilmott, 6 months | Quant, Derivatives
- **FRM (Financial Risk Manager)** | Risk | GARP, 2 parts | Risk
- **NISM Series VIII** | India, SEBI mandatory | Equity Derivatives certification | Mandatory for F&O
- **QuantInsti EPAT** | India, Algo trading | Executive Programme in Algo Trading | India-focused, Python

## Free Online Resources

- **Zerodha Varsity** — Free comprehensive modules on markets, technicals, fundamentals, options, risk
- **Investopedia** — Definitions and tutorials for every term
- **ASX Online Courses** — Free courses by Australian Securities Exchange
- **Coursera/edX Finance** — University-level courses (MIT, Yale, NYU)
- **YouTube: Ray Dalio, Howard Marks, Warren Buffett** — Principles from the masters

## Indian Market Specific Resources

- **Screener.in** — Best Indian fundamental screener (free)
- **Trendlyne** — DVM scores, alerts, screeners
- **Moneycontrol** — News, financials, results
- **TradingView** — Indian stocks with NSE/BSE data
- **Sensibull** — Options analytics for Indian F&O
- **NSE India** — Official data, corporate filings, FII/DII
- **BSE India** — Official data, bulk deals
- **SEBI** — Regulatory filings, investor education
"""

# =========================================================================== #
#  100 BOOKS DATABASE
# =========================================================================== #
BOOKS = {
    "investing_classics": [
        {"title": "The Intelligent Investor", "author": "Benjamin Graham", "category": "Value Investing"},
        {"title": "Security Analysis", "author": "Benjamin Graham & David Dodd", "category": "Value Investing"},
        {"title": "Common Stocks and Uncommon Profits", "author": "Philip Fisher", "category": "Growth Investing"},
        {"title": "One Up On Wall Street", "author": "Peter Lynch", "category": "Growth Investing"},
        {"title": "Beating The Street", "author": "Peter Lynch", "category": "Growth Investing"},
        {"title": "The Essays of Warren Buffett", "author": "Warren Buffett (ed. Cunningham)", "category": "Value Investing"},
        {"title": "Margin of Safety", "author": "Seth Klarman", "category": "Value Investing"},
        {"title": "Poor Charlie's Almanack", "author": "Charlie Munger", "category": "Mental Models"},
        {"title": "The Most Important Thing", "author": "Howard Marks", "category": "Risk & Cycles"},
        {"title": "You Can Be A Stock Market Genius", "author": "Joel Greenblatt", "category": "Special Situations"},
    ],
    "market_wizards": [
        {"title": "Market Wizards", "author": "Jack Schwager", "category": "Trader Interviews"},
        {"title": "The New Market Wizards", "author": "Jack Schwager", "category": "Trader Interviews"},
        {"title": "Stock Market Wizards", "author": "Jack Schwager", "category": "Trader Interviews"},
        {"title": "Unknown Market Wizards", "author": "Jack Schwager", "category": "Trader Interviews"},
        {"title": "Reminiscences of a Stock Operator", "author": "Edwin Lefèvre", "category": "Classic Memoir"},
    ],
    "technical_analysis": [
        {"title": "Technical Analysis of the Financial Markets", "author": "John Murphy", "category": "TA Reference"},
        {"title": "Encyclopedia of Chart Patterns", "author": "Thomas Bulkowski", "category": "Chart Patterns"},
        {"title": "The Art and Science of Technical Analysis", "author": "Adam Grimes", "category": "TA"},
        {"title": "Japanese Candlestick Charting Techniques", "author": "Steve Nison", "category": "Candlesticks"},
        {"title": "Trading Price Action Trends", "author": "Al Brooks", "category": "Price Action"},
        {"title": "Trading Price Action Trading Ranges", "author": "Al Brooks", "category": "Price Action"},
        {"title": "Trading Price Action Reversals", "author": "Al Brooks", "category": "Price Action"},
        {"title": "How to Make Money in Stocks", "author": "William O'Neil", "category": "CANSLIM"},
        {"title": "Mastering the Trade", "author": "John Carter", "category": "Day Trading"},
        {"title": "High Probability Trading", "author": "Marcel Link", "category": "Trading"},
    ],
    "quantitative_finance": [
        {"title": "Advances in Financial Machine Learning", "author": "Marcos López de Prado", "category": "ML for Finance"},
        {"title": "Machine Learning for Asset Managers", "author": "Marcos López de Prado", "category": "ML for Finance"},
        {"title": "Algorithmic Trading", "author": "Ernest Chan", "category": "Algo Trading"},
        {"title": "Quantitative Trading", "author": "Ernest Chan", "category": "Quant Trading"},
        {"title": "Inside the Black Box", "author": "Rishi Narang", "category": "Quant Funds"},
        {"title": "Expected Returns", "author": "Antti Ilmanen", "category": "Asset Returns"},
        {"title": "Active Portfolio Management", "author": "Grinold & Kahn", "category": "Portfolio Mgmt"},
        {"title": "Systematic Trading", "author": "Robert Carver", "category": "Systematic"},
        {"title": "Evidence-Based Technical Analysis", "author": "David Aronson", "category": "TA Validation"},
        {"title": "Algorithmic and High-Frequency Trading", "author": "Cartea, Jaimungal, Penalva", "category": "HFT"},
    ],
    "market_microstructure": [
        {"title": "Trading and Exchanges", "author": "Larry Harris", "category": "Microstructure"},
        {"title": "Market Microstructure Theory", "author": "Maureen O'Hara", "category": "Microstructure"},
        {"title": "Algorithmic Trading and DMA", "author": "Barry Johnson", "category": "Execution"},
        {"title": "The Microstructure Approach to Exchange Rates", "author": "Richard Lyons", "category": "FX Microstructure"},
        {"title": "Trades Quotes and Prices", "author": "Hasbrouck", "category": "Microstructure"},
    ],
    "options_volatility": [
        {"title": "Option Volatility and Pricing", "author": "Sheldon Natenberg", "category": "Options"},
        {"title": "Trading Option Greeks", "author": "Dan Passarelli", "category": "Greeks"},
        {"title": "Volatility Trading", "author": "Euan Sinclair", "category": "Vol Trading"},
        {"title": "Positional Option Trading", "author": "Euan Sinclair", "category": "Options"},
        {"title": "Options Futures and Other Derivatives", "author": "John Hull", "category": "Derivatives"},
    ],
    "risk_management": [
        {"title": "Against the Gods", "author": "Peter Bernstein", "category": "Risk History"},
        {"title": "Fooled by Randomness", "author": "Nassim Taleb", "category": "Probability"},
        {"title": "The Black Swan", "author": "Nassim Taleb", "category": "Tail Risk"},
        {"title": "Antifragile", "author": "Nassim Taleb", "category": "Antifragility"},
        {"title": "Dynamic Hedging", "author": "Nassim Taleb", "category": "Options Risk"},
    ],
    "psychology": [
        {"title": "Trading in the Zone", "author": "Mark Douglas", "category": "Trading Psychology"},
        {"title": "The Disciplined Trader", "author": "Mark Douglas", "category": "Trading Psychology"},
        {"title": "The Daily Trading Coach", "author": "Ari Kiev", "category": "Trading Psychology"},
        {"title": "Enhancing Trader Performance", "author": "Brett Steenbarger", "category": "Trading Psychology"},
        {"title": "Thinking Fast and Slow", "author": "Daniel Kahneman", "category": "Behavioral Finance"},
    ],
    "economics_macro": [
        {"title": "Principles for Dealing with the Changing World Order", "author": "Ray Dalio", "category": "Macro"},
        {"title": "Principles", "author": "Ray Dalio", "category": "Decision Making"},
        {"title": "Manias Panics and Crashes", "author": "Charles Kindleberger", "category": "Financial Crises"},
        {"title": "The Alchemy of Finance", "author": "George Soros", "category": "Macro"},
        {"title": "Big Debt Crises", "author": "Ray Dalio", "category": "Debt Cycles"},
    ],
    "financial_history": [
        {"title": "Extraordinary Popular Delusions and the Madness of Crowds", "author": "Charles Mackay", "category": "Bubbles"},
        {"title": "Devil Take the Hindmost", "author": "Edward Chancellor", "category": "Speculation History"},
        {"title": "Lords of Finance", "author": "Liaquat Ahamed", "category": "Central Banking"},
        {"title": "When Genius Failed", "author": "Roger Lowenstein", "category": "LTCM"},
        {"title": "Too Big to Fail", "author": "Andrew Ross Sorkin", "category": "2008 Crisis"},
    ],
    "hedge_funds": [
        {"title": "More Money Than God", "author": "Sebastian Mallaby", "category": "Hedge Fund History"},
        {"title": "The Man Who Solved the Market", "author": "Gregory Zuckerman", "category": "Jim Simons/Renaissance"},
        {"title": "The Quants", "author": "Scott Patterson", "category": "Quant Crash 2007"},
        {"title": "Dark Pools", "author": "Scott Patterson", "category": "HFT"},
        {"title": "Flash Boys", "author": "Michael Lewis", "category": "HFT"},
    ],
    "ai_data_science": [
        {"title": "Hands-On Machine Learning", "author": "Aurélien Géron", "category": "ML Practical"},
        {"title": "Deep Learning", "author": "Ian Goodfellow", "category": "Deep Learning"},
        {"title": "Pattern Recognition and Machine Learning", "author": "Christopher Bishop", "category": "ML Theory"},
        {"title": "Probabilistic Machine Learning", "author": "Kevin Murphy", "category": "ML Theory"},
        {"title": "Reinforcement Learning: An Introduction", "author": "Sutton & Barto", "category": "RL"},
    ],
    "portfolio_construction": [
        {"title": "The Little Book of Common Sense Investing", "author": "John Bogle", "category": "Indexing"},
        {"title": "A Random Walk Down Wall Street", "author": "Burton Malkiel", "category": "Efficient Markets"},
        {"title": "Asset Management", "author": "Ang", "category": "Factor Investing"},
        {"title": "Portfolio Construction and Analytics", "author": "Drobetz", "category": "Portfolio"},
        {"title": "Quantitative Equity Portfolio Management", "author": "Qian, Hua, Sorensen", "category": "Quant Portfolio"},
    ],
    "advanced_phd": [
        {"title": "Asset Pricing", "author": "John Cochrane", "category": "Asset Pricing"},
        {"title": "Investment Science", "author": "David Luenberger", "category": "Finance"},
        {"title": "Financial Calculus", "author": "Baxter & Rennie", "category": "Derivatives Math"},
        {"title": "Stochastic Calculus for Finance I", "author": "Shreve", "category": "Stochastic"},
        {"title": "Stochastic Calculus for Finance II", "author": "Shreve", "category": "Stochastic"},
    ],
    "elite_picks": [
        {"title": "Competition Demystified", "author": "Bruce Greenwald", "category": "Strategy"},
        {"title": "Quality Investing", "author": "Thornton", "category": "Quality"},
        {"title": "Financial Shenanigans", "author": "Howard Schilit", "category": "Fraud Detection"},
        {"title": "The Outsiders", "author": "William Thorndike", "category": "CEO Capital Allocation"},
        {"title": "Common Sense on Mutual Funds", "author": "John Bogle", "category": "Indexing"},
        {"title": "The Psychology of Money", "author": "Morgan Housel", "category": "Behavioral Finance"},
        {"title": "The Dhandho Investor", "author": "Mohnish Pabrai", "category": "Value"},
        {"title": "The Warren Buffett Way", "author": "Robert Hagstrom", "category": "Buffett"},
        {"title": "The Education of a Value Investor", "author": "Guy Spier", "category": "Value"},
        {"title": "The Big Short", "author": "Michael Lewis", "category": "2008 Crisis"},
        {"title": "Boomerang", "author": "Michael Lewis", "category": "European Debt Crisis"},
        {"title": "The Undoing Project", "author": "Michael Lewis", "category": "Behavioral Finance"},
        {"title": "Adaptive Markets", "author": "Andrew Lo", "category": "Market Theory"},
        {"title": "The Little Book That Still Beats the Market", "author": "Joel Greenblatt", "category": "Magic Formula"},
    ],
}

# =========================================================================== #
#  TOP 20 PRIORITY BOOKS
# =========================================================================== #
TOP_20 = """# TOP 20 PRIORITY BOOKS — For Building a Stock Analysis AI

> If storage/time is limited, these 20 books will teach the AI more useful
> market knowledge than the average retail trader learns in decades.

## Priority Order

1. **Trading and Exchanges** — Larry Harris | How markets actually work (microstructure)
2. **Market Microstructure Theory** — Maureen O'Hara | Academic microstructure framework
3. **Advances in Financial Machine Learning** — Marcos López de Prado | ML for finance (overfitting, CV)
4. **Machine Learning for Asset Managers** — Marcos López de Prado | ML applied to portfolios
5. **Active Portfolio Management** — Grinold & Kahn | The quant portfolio management bible
6. **Expected Returns** — Antti Ilmanen | How different asset classes generate returns
7. **Security Analysis** — Graham & Dodd | Fundamental analysis foundation
8. **The Intelligent Investor** — Benjamin Graham | Value investing principles
9. **Market Wizards** — Jack Schwager | What top traders actually do
10. **Reminiscences of a Stock Operator** — Edwin Lefèvre | Price action wisdom (Livermore)
11. **Option Volatility and Pricing** — Sheldon Natenberg | Options pricing and Greeks
12. **Volatility Trading** — Euan Sinclair | Vol as an asset class
13. **Systematic Trading** — Robert Carver | How to build a systematic system
14. **Algorithmic Trading** — Ernest Chan | Practical quant trading with Python
15. **The Most Important Thing** — Howard Marks | Risk, cycles, and second-level thinking
16. **Fooled by Randomness** — Nassim Taleb | Probability and luck in markets
17. **The Black Swan** — Nassim Taleb | Tail risk and extreme events
18. **Manias Panics and Crashes** — Kindleberger | Financial crisis patterns
19. **The Man Who Solved the Market** — Zuckerman | Jim Simons and Renaissance Technologies
20. **Principles for Dealing with the Changing World Order** — Ray Dalio | Macro cycles

## Key Wisdom from Each (for RAG ingestion)

1. **Trading and Exchanges**: Markets are mechanisms for matching informed and uninformed traders. Spread = compensation for providing liquidity. Order types reveal information.

2. **Market Microstructure Theory**: Price discovery happens through order flow. Market makers set prices based on inventory risk. Liquidity is not free.

3. **Advances in FML**: Backtests overstate live returns. More parameters = more overfit. Use purged k-fold cross-validation. Labeling matters more than models.

4. **Machine Learning for Asset Managers**: Diversification is the only free lunch. Correlations are unstable. Mean-variance optimization is unstable. Use hierarchical risk parity.

5. **Active Portfolio Management**: Information Ratio = expected active return / tracking error. Fundamental Law: IR = IC × sqrt(breadth). Skill × opportunities.

6. **Expected Returns**: Returns come from: risk premium, behavioral, structural, and value-collecting. Understand the source of your edge.

7. **Security Analysis**: Intrinsic value = discounted cash flows. Margin of safety = buffer against error. Balance sheet > income statement for safety.

8. **The Intelligent Investor**: Mr. Market is bipolar. Buy when depressed, sell when euphoric. Price is what you pay, value is what you get.

9. **Market Wizards**: Risk management is the #1 differentiator. Cut losses, let profits run. The best traders are humble and adaptive.

10. **Reminiscences**: The trend is your friend. Don't fight the tape. Volume confirms price. Patience is a position.

11. **Option Volatility and Pricing**: IV is the only unknown. When IV > HV, options are expensive (sell). When IV < HV, options are cheap (buy).

12. **Volatility Trading**: VRP (vol risk premium) = persistent IV > HV. Sell vol to harvest VRP. But manage tail risk (black swans).

13. **Systematic Trading**: Rules-based > discretionary. Backtest everything. Position size by volatility. Diversify across uncorrelated systems.

14. **Algorithmic Trading**: Start simple. Mean reversion on liquid stocks. RSI < 10 = buy. Exit at RSI > 50. 2:1 R:R minimum.

15. **The Most Important Thing**: Risk ≠ volatility. Risk = permanent loss. Second-level thinking: "it's a good company but everyone knows it, so it's overpriced."

16. **Fooled by Randomness**: Survivorship bias = we see winners, not losers. Luck > skill in short term. Don't confuse luck with skill.

17. **The Black Swan**: Extreme events dominate history. Normal distribution underestimates tails. Barbell strategy: 90% safe, 10% aggressive.

18. **Manias Panics and Crashes**: Bubbles follow a pattern: displacement → boom → euphoria → distress → panic. Recognize the stage.

19. **The Man Who Solved the Market**: Simons used pure data + ML. No economic theory. Ensemble of weak signals. Continuous refinement. Renaissance = 66% annual before fees.

20. **Changing World Order**: Empires rise and fall in cycles: education → innovation → productivity → wealth → debt → decline. Track the cycle position.
"""


def build_all():
    """Write all knowledge files to the knowledge/ directory."""
    files = {
        "01_foundations.md": FOUNDATIONS,
        "02_technical_analysis.md": TECHNICAL,
        "03_fundamental_analysis.md": FUNDAMENTAL,
        "04_options_derivatives.md": OPTIONS,
        "05_quant_algo.md": QUANT,
        "06_advanced_strategies.md": ADVANCED,
        "07_risk_management.md": RISK_MGMT,
        "08_psychology.md": PSYCHOLOGY,
        "09_resources.md": RESOURCES,
        "top20_priority_books.md": TOP_20,
    }

    for filename, content in files.items():
        path = KNOWLEDGE_DIR / filename
        path.write_text(content)
        print(f"  ✅ {filename}: {len(content)} chars")

    # Write books database
    books_path = KNOWLEDGE_DIR / "books_database.json"
    total_books = sum(len(books) for books in BOOKS.values())
    with open(books_path, "w") as f:
        json.dump({
            "total_books": total_books,
            "categories": len(BOOKS),
            "books_by_category": BOOKS,
        }, f, indent=2)
    print(f"  ✅ books_database.json: {total_books} books in {len(BOOKS)} categories")

    # Also write as a searchable markdown
    books_md = "# COMPLETE BOOKS DATABASE — 100 Books in 15 Categories\n\n"
    for category, books in BOOKS.items():
        cat_title = category.replace("_", " ").title()
        books_md += f"## {cat_title} ({len(books)} books)\n\n"
        for i, book in enumerate(books, 1):
            books_md += f"{i}. **{book['title']}** — {book['author']} ({book['category']})\n"
        books_md += "\n"
    (KNOWLEDGE_DIR / "books_database.md").write_text(books_md)
    print(f"  ✅ books_database.md: searchable markdown version")

    print(f"\n📊 Total: {len(files) + 2} knowledge files written")
    print(f"📚 Total books: {total_books} across {len(BOOKS)} categories")
    return total_books


if __name__ == "__main__":
    total = build_all()
    print(f"\n✅ Complete knowledge base built: {total} books, 9 category files + top-20 priority list")
