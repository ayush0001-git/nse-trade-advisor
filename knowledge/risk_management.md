# RISK MANAGEMENT

## CORE PRINCIPLE
Survival comes first. You can't trade if you're broke. The goal is not to make money — it's to avoid losing money you can't recover from. Returns follow survival.

## THE 1% RULE

### Rule
Never risk more than 1-2% of capital on a single trade.

### Math
- Capital: ₹10,00,000
- Risk per trade: 1% = ₹10,000
- Max loss per trade: ₹10,000
- Can lose 20 trades in a row and still have ₹8,00,000 (80% of capital)
- At 2% risk, 20 losses leaves ₹6,60,000 (66%)
- At 5% risk, 20 losses leaves ₹3,60,000 (36%) — near wipeout
- At 10% risk, 20 losses leaves ₹1,20,000 (12%) — game over

### Position Sizing Formula
```
rupees_at_risk = capital × risk_pct          (e.g. 100000 × 0.01 = ₹1000)
risk_per_share = |entry − stop|              (stop is ATR-based)
quantity       = floor(rupees_at_risk / risk_per_share)
```

### Example
- Capital: ₹1,00,000
- Risk: 1% = ₹1,000
- Entry: ₹500
- Stop: ₹480 (2x ATR)
- Risk per share: ₹20
- Quantity: ₹1,000 / ₹20 = 50 shares
- Position value: ₹25,000 (25% of capital)
- Max loss if stopped: ₹1,000 (1%)

## RISK/REWARD

### Minimum R:R = 1:2
- Risk ₹1 to make ₹2
- At 40% win rate: 0.4 × 2 - 0.6 × 1 = +0.2R per trade (profitable)
- At 1:1 R:R, you need > 50% win rate to profit (hard)
- At 1:3 R:R, you need only 25% win rate to profit (easy)

### Reject Trades If
- R:R < 1:2 (hard veto)
- R:R < 1:1.5 (even with high confidence, skip)
- Stop is too tight (< 0.5x ATR — will get stopped by noise)
- Stop is on wrong side of entry (data error)

## STOP-LOSS RULES

### Never Move a Stop Further Away
- This is the #1 way traders blow up accounts
- A stop can only move in the direction of profit (trailing)
- If you find yourself wanting to widen the stop, the thesis is wrong — exit

### Stop Types
- **ATR Stop** (default): 2x ATR below entry (long) or above entry (short)
- **Structure Stop**: below recent swing low (long) or above swing high (short)
- **Wider Stop**: max(ATR, structure) — use in volatile regimes
- **Trailing Stop**: once +1R, trail at breakeven; once +2R, trail at 1R profit

### Gap Risk (Indian Market)
- Indian stocks gap. Your stop is not guaranteed.
- Plan for slippage: assume stop fills 0.25 ATR worse than the stop level
- Position size for worst-case fill, not nominal stop
- Avoid holding overnight into earnings (gap risk is extreme)

## DRAWDOWN CONTROL

### The 10% Rule
- If portfolio drawdown exceeds 10%, HALVE all position sizes
- Stay at half size until equity recovers to a new high
- This prevents a 10% drawdown from becoming a 30% drawdown

### The 20% Rule
- If drawdown exceeds 20%, STOP TRADING for 1 week
- Review every trade — what went wrong?
- Paper trade until confidence returns
- This is the circuit breaker that saves your career

## CORRELATION RISK

### Rule
- Don't count positions — count bets
- 5 bank stocks = 1 bet (they're correlated)
- Max 2 stocks per sector
- Max 25% of capital in any single sector

### Diversification Math
- 15-20 uncorrelated bets reduce risk by 80% (Dalio's Holy Grail)
- 5 correlated bets reduce risk by maybe 20% (fake diversification)
- Count unique bets, not positions

## REGIME-BASED RISK

### Bull Market
- Full position sizes (1% risk)
- Trail winners
- Max 80% invested

### Bear Market
- Halve positions (0.5% risk)
- Tighten stops
- Max 30% invested (raise cash)

### High Volatility
- Halve positions (0.5% risk)
- Widen stops (3x ATR)
- No pyramiding

### Unknown/Transitional
- 0.5% risk
- Wait for clarity
- Cash is a position

## VETO CHECKLIST (BEFORE EVERY TRADE)

- [ ] R:R ≥ 2:1?
- [ ] Stop on correct side of entry?
- [ ] Position size ≤ 1% risk?
- [ ] Not counter-trend (no longs in downtrend)?
- [ ] Not in earnings within 5 days?
- [ ] Not correlated with existing positions (> 0.7)?
- [ ] Regime supports the strategy type?
- [ ] Drawdown < 10% (or position size halved)?

If ANY veto fails, DO NOT TAKE THE TRADE.

## PSYCHOLOGICAL RISK

### Revenge Trading
- After a loss, the urge to "win it back" is overwhelming
- This is the most destructive behavior in trading
- Rule: after a loss, take a 10-minute break before the next trade
- Each trade is independent — the market doesn't know you lost

### FOMO (Fear of Missing Out)
- "The stock is up 10% today, I need to buy"
- This is how you buy the top
- Rule: if you missed the entry, wait for the next setup
- There's always another trade

### Overconfidence
- After 3 wins in a row, you feel invincible
- This is when you size up and blow up
- Rule: position size is based on the system, not your mood
- Never increase size after a win streak — the edge doesn't change
