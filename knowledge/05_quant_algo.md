# QUANTITATIVE & ALGO TRADING — Systematic Strategies

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
