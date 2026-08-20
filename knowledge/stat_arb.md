# STATISTICAL ARBITRAGE

## DEFINITION
Trade the spread between two cointegrated stocks. When they diverge, short the outperformer and buy the underperformer. Profit when they reconverge.

## WHY IT WORKS
- **Cointegration**: two stocks in the same sector tend to move together long-term
- **Temporary divergence**: caused by liquidity shocks, news asymmetry, or noise
- **Mean reversion**: spreads revert to their historical mean
- **Market neutral**: no directional bet on the market

## SIGNALS
- **Cointegration test**: Engle-Granger or Johansen test confirms cointegration
- **Z-score**: spread is 2+ standard deviations from mean
- **Half-life**: spread reverts in 5-20 days (not too fast, not too slow)
- **Correlation**: > 0.6 between the two stocks' returns

## ENTRY RULES
1. Two stocks are cointegrated (p-value < 0.05 on Engle-Granger test)
2. Spread z-score exceeds ±2.0
3. Half-life of mean reversion is 5-20 days
4. Both stocks have > 50cr daily turnover (liquidity)
5. No major event (earnings, M&A) in the next 5 days for either stock

## EXIT RULES
- Spread reverts to z-score = 0 (full profit)
- Stop-loss: spread reaches z-score ±4 (divergence is structural, not temporary)
- Time exit: 30 days (if no reversion, thesis is wrong)
- News event: exit before earnings/M&A

## PAIR EXAMPLES (Indian Market)
- HDFCBANK vs ICICIBANK (private banks)
- TCS vs INFY (large-cap IT)
- RELIANCE vs ONGC (energy)
- MARUTI vs M&M (autos)
- ASIANPAINTS vs BERGERPAINT (paints)
- HINDUNILVR vs NESTLEIND (FMCG)

## USED BY
- Renaissance Technologies (Medallion Fund)
- D.E. Shaw
- Citadel
- Two Sigma

## BACKTESTED EDGE
- Sharpe ratio: 1.5-3.0 (very high, market-neutral)
- Win rate: 60-70%
- Low drawdowns (market-neutral)
- But: returns are small per trade (2-5%)
- Requires high frequency (many pairs, many trades)

## RISK MANAGEMENT
- Max 2% risk per pair
- Max 10 pairs simultaneously
- Correlation monitoring — if correlation breaks, exit immediately
- Beta-neutral: adjust share ratios so dollar-beta of long = dollar-beta of short

## COMMON MISTAKES
1. **Using correlation instead of cointegration** — correlation doesn't imply mean reversion
2. **Pairs in different sectors** — they won't cointegrate
3. **Holding through earnings** — earnings break the relationship
4. **Size too large** — slippage eats the edge on small spreads
5. **Ignoring regime change** — if the relationship structurally breaks, exit
