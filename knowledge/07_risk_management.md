# RISK MANAGEMENT — The Discipline That Separates Survivors from Blow-Ups

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
