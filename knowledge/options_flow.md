# OPTIONS FLOW ANALYSIS

## DEFINITION
Options flow reveals where smart money is positioning. Options markets attract sophisticated traders (institutions, hedge funds), so their positioning is a signal.

## KEY METRICS

### Put/Call Ratio (PCR)
- **PCR < 0.7**: Excessive bullishness — contrarian bearish signal
- **PCR 0.7-1.0**: Mild bullish bias
- **PCR 1.0-1.3**: Mild bearish bias
- **PCR > 1.3**: Excessive bearishness — contrarian bullish signal
- **PCR > 2.0**: Extreme fear — strong buy signal (capitulation)

### Open Interest (OI) Buildup
| Price | OI | Signal | Meaning |
|---|---|---|---|
| ↑ | ↑ | **Long Buildup** | New long positions (bullish) |
| ↓ | ↑ | **Short Buildup** | New short positions (bearish) |
| ↑ | ↓ | **Short Covering** | Shorts buying back (bullish) |
| ↓ | ↓ | **Long Unwinding** | Longs selling (bearish) |

### Max Pain
- The strike where total option holder loss is maximized
- Price tends to gravitate toward max pain on expiry day
- Especially strong in the last 2 hours of expiry
- Use: if price is 5%+ from max pain on expiry day, expect drift toward it

### Implied Volatility (IV) vs Historical Volatility (HV)
- **IV > HV**: Options are "expensive" — consider selling (straddles, strangles)
- **IV < HV**: Options are "cheap" — consider buying
- IV percentile > 80: elevated, likely to mean-revert down
- IV percentile < 20: depressed, likely to mean-revert up

### Gamma Levels
- Dealer gamma positioning affects price stability
- Positive gamma: dealers hedge against the trend (stabilizes price)
- Negative gamma: dealers hedge with the trend (amplifies moves)
- Gamma flips near key strikes — expect volatility there

## SIGNAL INTERPRETATION

### Strong Bullish
- PCR > 1.5 (extreme fear)
- Long buildup at ATM calls
- IV percentile < 30 (cheap options)
- Max pain below current price

### Strong Bearish
- PCR < 0.5 (extreme greed)
- Short buildup at ATM puts
- IV percentile > 80 (expensive options, expect crash)
- Max pain above current price

## INDIAN OPTIONS MARKET
- NIFTY and BANKNIFTY are the most liquid option chains
- Stock options are less liquid — wider spreads
- Weekly expiries on NIFTY (Thursday), BANKNIFTY (Wednesday)
- Monthly expiry on last Thursday of the month
- Use NSE option chain data (free)

## USED BY
- Susquehanna International
- Citadel Securities
- Optiver
- Jane Street

## RISK MANAGEMENT
- Never sell naked options (unlimited risk)
- Use spreads (bull call spread, bear put spread) to define risk
- Position size: max 2% of capital per options trade
- Close positions before expiry week (gamma risk spikes)

## COMMON MISTAKES
1. **Buying out-of-the-money options** — they expire worthless 80% of the time
2. **Ignoring IV** — buying when IV is high guarantees a loss even if direction is right
3. **Holding through expiry** — gamma risk can wipe you out
4. **Selling naked calls** — unlimited risk, one bad trade can blow the account
5. **Trading illiquid stock options** — wide spreads eat the edge
