# DATA SOURCES MASTER INDEX

> Complete list of all free and paid data sources for the trading bot.
> Use these to expand the bot's data coverage.

## Price & Market Data (Free)

| Source | URL | What it provides |
|---|---|---|
| Yahoo Finance | https://finance.yahoo.com | Historical prices, fundamentals, news (used by bot) |
| Alpha Vantage | https://www.alphavantage.co | OHLCV data, technical indicators, forex, crypto |
| Polygon.io | https://polygon.io | Real-time & historical US stocks, options, forex |
| NASDAQ API | https://api.nasdaq.com | NASDAQ listings, earnings, dividends |
| Stooq | https://stooq.com | Free EOD historical data |
| IEX Cloud | https://iexcloud.io | Stock quotes, financials, news |
| Finnhub | https://finnhub.io | Real-time quotes, earnings, sentiment |

## News & Sentiment (Free)

| Source | URL | What it provides |
|---|---|---|
| NewsAPI | https://newsapi.org | Financial news aggregator (free tier) |
| Yahoo RSS | https://feeds.finance.yahoo.com/rss/2.0/headline | Yahoo Finance RSS |
| Reuters | https://www.reuters.com/finance | Breaking financial news |
| Bloomberg | https://www.bloomberg.com/markets | Market news |
| Seeking Alpha | https://seekingalpha.com | Stock analysis & earnings commentary |
| Benzinga | https://benzinga.com | Fast-moving market news |
| Stock Analysis | https://stockanalysis.com | Earnings, revenue, analyst ratings |
| Reddit WSB | https://www.reddit.com/r/wallstreetbets/.json | Retail sentiment |

## Fundamental Data (Free)

| Source | URL | What it provides |
|---|---|---|
| Stock Analysis | https://stockanalysis.com/stocks/[TICKER]/financials/ | Scraped fundamentals |
| Macrotrends | https://macrotrends.net/stocks/charts/[TICKER]/ | 20+ years of fundamental data |
| Simply Wall St | https://simplywall.st | Visualized fundamentals |
| GuruFocus | https://www.gurufocus.com | Value investing ratios |
| SEC EDGAR | https://www.sec.gov/cgi-bin/browse-edgar | 10-K, 10-Q, 8-K filings |

## Macro & Economic Data (Free)

| Source | URL | What it provides |
|---|---|---|
| FRED | https://fred.stlouisfed.org | Fed Funds Rate, CPI, GDP, yield curve (CRITICAL) |
| BLS | https://www.bls.gov | Jobs, CPI, unemployment |
| Census | https://www.census.gov/economic-indicators/ | Retail sales, housing |
| EIA | https://www.eia.gov/opendata/ | Oil/gas energy data |

## Fear, Greed & Sentiment

| Source | URL | What it provides |
|---|---|---|
| CNN Fear & Greed | https://money.cnn.com/data/fear-and-greed/ | Fear & Greed Index |
| VIX | https://markets.businessinsider.com/indices/vix | Volatility index |
| AAII Sentiment | https://www.aaii.com/sentimentsurvey | Investor sentiment survey |
| Put/Call Ratio | https://www.putcallratio.com | Options sentiment |

## Options Flow & Dark Pool

| Source | URL | What it provides |
|---|---|---|
| Unusual Whales | https://unusualwhales.com | Unusual options flow |
| CBOE | https://www.cboe.com/delayed_quotes/ | Options chains |
| Finviz | https://finviz.com/screener.ashx | Stock screener with filters |
| Dark Pool Levels | https://darkpoollevels.com | Dark pool prints |
| SqueezeMetrics | https://www.squeezemetrics.com | Free GEX data |

## Insider & Congressional Trading

| Source | URL | What it provides |
|---|---|---|
| OpenInsider | https://openinsider.com | Insider trading (free, best) |
| SEC Form 4 | https://www.sec.gov/cgi-bin/browse-edgar?type=4 | Form 4 filings |
| QuiverQuant | https://www.quiverquant.com/congresstrading/ | Congressional trades |
| House Filings | https://efts.house.gov/LATEST/search-index | House disclosure |

## Earnings & Events Calendar

| Source | URL | What it provides |
|---|---|---|
| Earnings Whispers | https://earningswhispers.com | Earnings dates + whisper numbers |
| Yahoo Calendar | https://finance.yahoo.com/calendar/earnings | Earnings calendar |
| Forex Factory | https://www.forexfactory.com/calendar | Economic calendar |

## Alternative Data

| Source | URL | What it provides |
|---|---|---|
| Google Trends | https://trends.google.com | Search demand (free) |
| Glassdoor | https://www.glassdoor.com/research/ | Employee satisfaction |
| Google Patents | https://patents.google.com | Patent filing activity |
| CoinGecko | https://api.coingecko.com/api/v3 | Crypto data (free) |
| SafeGraph | https://www.safegraph.com | Foot traffic data (some free) |

## Strategy Documents for RAG

1. **Trend Following**: Buy when price > 200 EMA, sell when below. ATR stop-loss.
2. **Mean Reversion**: RSI <30 buy, >70 sell. Bollinger squeeze entries.
3. **Momentum**: Buy top 10% momentum stocks monthly. Hold 1 month.
4. **Earnings Play**: Buy 2 weeks before earnings, sell day before. Or straddle.
5. **Sector Rotation**: Early=Financials, Mid=Tech, Late=Energy, Recession=Utilities.
6. **Risk Management**: Never risk >1-2% per trade. Max DD halt at -10% monthly.
7. **Kelly Criterion**: f* = (bp-q)/b. Use half Kelly in practice.

## RAG Chunking Strategy

- Split documents by topic + ticker + date
- Add metadata: ticker, date, source, data_type
- Use hybrid search: dense (semantic) + sparse (BM25 keyword)
- Vector DB: ChromaDB (local, free, lightweight)

## Disclaimer

A trading bot cannot guarantee profits. Markets are inherently unpredictable.
Always backtest strategies before live trading, use paper trading first, and
never risk money you can't afford to lose.
