# OPTIONS & DERIVATIVES — Leverage, Hedging & Income

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
