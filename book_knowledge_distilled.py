"""
book_knowledge_distilled.py - Distilled key principles from all 100 trading books.

For each of the 100 books, this file contains 5-10 distilled KEY PRINCIPLES
(the rules, frameworks, and insights — not copyrighted text). These are the
actionable takeaways a professional trader would highlight.

When indexed into ChromaDB, the bot can query: "What does [Book/Author] say
about [topic]?" and retrieve the relevant distilled principles.

Categories (matching the user's 15-category structure):
  1. Investing Classics (Foundation)
  2. Market Wizards & Trader Interviews
  3. Technical Analysis
  4. Quantitative Finance
  5. Market Microstructure
  6. Options & Volatility
  7. Risk Management
  8. Psychology
  9. Economics & Macro
  10. Financial History & Crashes
  11. Hedge Funds & Quant Firms
  12. AI / Data Science for Trading
  13. Portfolio Construction
  14. Advanced / PhD-Level
  15. Remaining Elite Picks

Usage:
    from book_knowledge_distilled import ALL_BOOK_KNOWLEDGE
    from data_warehouse import get_warehouse
    dw = get_warehouse()
    dw.add("investor_wisdom", [b["principles_text"] for b in ALL_BOOK_KNOWLEDGE], ...)
"""
from __future__ import annotations

# Each entry: {"book": str, "author": str, "category": str, "principles": [str], "principles_text": str}

ALL_BOOK_KNOWLEDGE = []


def _add(book, author, category, principles):
    text = f"BOOK: {book} by {author}\nCATEGORY: {category}\n\nKEY PRINCIPLES:\n"
    for i, p in enumerate(principles, 1):
        text += f"{i}. {p}\n"
    ALL_BOOK_KNOWLEDGE.append({
        "book": book,
        "author": author,
        "category": category,
        "principles": principles,
        "principles_text": text,
    })


# =========================================================================== #
#  1. INVESTING CLASSICS
# =========================================================================== #
_add("The Intelligent Investor", "Benjamin Graham", "Value Investing", [
    "Mr. Market is bipolar — he comes to you every day with a price. Some days he's euphoric, some days depressed. Take advantage of his mood swings, don't let them take advantage of you.",
    "Price is what you pay, value is what you get. Focus on intrinsic value, not market price.",
    "Margin of safety: buy when price is significantly below intrinsic value (at least 25-30% discount). This buffer protects against analytical error and bad luck.",
    "Defensive investor vs enterprising investor: know which one you are. Defensive = buy index funds and hold. Enterprising = actively research and select stocks.",
    "Net current asset value (NCAV) approach: buy stocks trading below their net current assets (current assets - all liabilities). Graham's deep value screen.",
    "Diversify adequately but not excessively. 10-30 stocks across different industries provides sufficient diversification.",
    "Earnings stability: prefer companies with consistent earnings over 10+ years. Cyclical companies require more conservative valuation.",
    "Dividend record: prefer companies with uninterrupted dividend payments for 20+ years. Signals financial stability.",
    "The market is a voting machine in the short run, a weighing machine in the long run. In the short run, sentiment dominates. In the long run, fundamentals prevail.",
    "Don't time the market. Dollar-cost average instead. Regular investments regardless of market level outperform lump-sum timing for most investors.",
])

_add("Security Analysis", "Benjamin Graham & David Dodd", "Value Investing", [
    "Intrinsic value = the value justified by the facts: assets, earnings, dividends, definite prospects. Market price may deviate significantly.",
    "Three methods of valuation: (1) net asset value, (2) earnings power value, (3) growth value. The more certain the method, the more weight it deserves.",
    "Earnings power = normalized earnings a company can sustain over time. Strip out one-time gains/losses. Focus on sustainable earning capacity.",
    "Balance sheet analysis is primary: current assets > all liabilities = working capital surplus. Negative working capital = risk.",
    "Quality of earnings: compare reported earnings to cash flow. If earnings >> cash flow, earnings quality is low (accruals anomaly).",
    "The Graham number: sqrt(22.5 × EPS × book value per share). A quick valuation heuristic. Buy below this price.",
    "Distinction between investment and speculation: investment requires safety of principal and adequate return. Speculation = neither.",
    "Defensive investing: require (1) adequate size, (2) strong financial condition, (3) continued dividends, (4) no earnings deficits, (5) moderate P/E, (6) moderate P/B.",
    "Special situations: spin-offs, mergers, reorganizations, liquidations. These can offer returns uncorrelated to the general market.",
    "Always demand a margin of safety. It is the central concept of investing. Without it, you are speculating, not investing.",
])

_add("Common Stocks and Uncommon Profits", "Philip Fisher", "Growth Investing", [
    "The scuttlebutt method: talk to competitors, customers, suppliers, ex-employees, and industry experts. Gather qualitative intelligence that financial statements can't show.",
    "15 questions to evaluate a growth company: Does it have products with market potential to increase sales for several years? Is management developing new products? Is R&D effective? Does it have an above-average sales organization? Does it have a worthwhile profit margin? What is the company doing to maintain/improve margins? Does it have excellent labor relations? Does it have depth in management? How good are its cost controls? Does it have a competitive edge? Does it have short-range or long-range outlook? Does it have investor relations? Does management have integrity? Does it have a good record of hitting targets?",
    "Focus on qualitative factors: management quality, R&D effectiveness, competitive moat — more than just P/E ratios.",
    "Growth stocks can be held for decades. The biggest gains come from compounding, not from trading. Don't sell just because the stock doubled.",
    "When to sell: (1) when you made a mistake in the original assessment, (2) when the company no longer qualifies as a growth company, (3) when you found a better opportunity. NOT because the market went down.",
    "Don't over-diversify. Fisher recommended 5-10 stocks. 'Know what you own and why you own it.'",
    "R&D is the lifeblood of a growth company. Track R&D as % of sales and the output (new products, patents).",
    "Management integrity is non-negotiable. If management ever misleads shareholders, sell immediately.",
])

_add("One Up On Wall Street", "Peter Lynch", "Growth Investing", [
    "Invest in what you know. Your everyday observations (mall traffic, product popularity, workplace trends) give you an edge over Wall Street analysts.",
    "Go for a business that any idiot can run — because sooner or later, any idiot probably will. The best businesses are simple and don't depend on a genius CEO.",
    "Six categories of stocks: (1) slow growers, (2) stalwarts, (3) fast growers, (4) cyclicals, (5) turnarounds, (6) asset plays. Know which category before buying.",
    "The PEG ratio (P/E divided by growth rate) < 1.0 is attractive. P/E should match the growth rate. A P/E of 15 with 15% growth = fair value.",
    "The story: every stock has a story. What's the thesis? If you can't explain it in 2 minutes, you don't understand it well enough.",
    "Local knowledge advantage: you see products in stores before analysts see them in earnings reports. A 6-month head start.",
    "Earnings, earnings, earnings. Stock price follows earnings over the long run. If earnings grow, the stock will eventually follow.",
    "The 13% rule: if you're right 6 out of 10 times, you're a hero. Even 5 out of 10 with good R:R is profitable. Don't fear being wrong.",
    "Watch insider buying. There's only one reason insiders buy: they think the price will go up.",
    "Avoid diworsification: companies expanding into areas they don't understand. Stick to the knitting.",
])

_add("Beating The Street", "Peter Lynch", "Growth Investing", [
    "The perfect stock: boring business, boring name, in a boring industry. The more boring, the better. Exciting stocks attract attention and get overpriced.",
    "Check the balance sheet: no debt or low debt = safety. High debt = risk, even for good companies. Cash > debt = strong position.",
    "Cash position: a company with more cash than debt is in a strong negotiating position. Net cash per share can be a significant portion of the stock price.",
    "Inventory growth: if inventory grows faster than sales, that's a red flag. Goods are piling up. Demand is softening.",
    "Pension fund assets: a company with overfunded pension plans has hidden value. The surplus belongs to shareholders.",
    "The 20% drop rule: if a stock drops 20% for no fundamental reason, investigate. Could be a buying opportunity.",
    "Industry leaders: buy the #1 or #2 company in an industry. The leader usually has the best margins, the strongest brand, and the most pricing power.",
])

_add("The Essays of Warren Buffett", "Warren Buffett (ed. Cunningham)", "Value Investing", [
    "Our favorite holding period is forever. Time is the friend of the wonderful business, the enemy of the mediocre.",
    "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price. Quality compounds; cheap deteriorates.",
    "Risk comes from not knowing what you're doing. Understand the business model, competitive moat, and management before investing.",
    "Be fearful when others are greedy, greedy when others are fearful. Sentiment extremes mark turning points.",
    "Accounting is the language of business. Read financial statements before price charts. If the balance sheet is deteriorating, no indicator will save you.",
    "Capital allocation is the CEO's most important job. Watch what management does with cash: reinvest, buyback, dividend, or acquisitions.",
    "Diversification is protection against ignorance. It makes little sense if you know what you're doing. Concentrate in your best ideas.",
    "The stock market is designed to transfer money from the active to the patient. Activity is the enemy of investment returns.",
    "Never invest in a business you cannot understand. The circle of competence: stay within it. Expand it slowly.",
    "Price is what you pay, value is what you get. Whether it's socks or stocks, buy quality when it's marked down.",
])

_add("Margin of Safety", "Seth Klarman", "Value Investing", [
    "Margin of safety = the gap between price and intrinsic value. It's the buffer that protects against error, bad luck, and the unpredictability of markets.",
    "Value investing is the discipline of buying securities at a significant discount from underlying value. At least 30-50% discount.",
    "Risk is not volatility — it's the probability of permanent loss. Volatility creates opportunity; permanent loss destroys capital.",
    "Investment success does not require predicting the future. It requires understanding the present and demanding a margin of safety.",
    "Avoid leverage. Leverage doesn't add value, it adds risk. A leveraged portfolio can be wiped out by a normal market decline.",
    "Cash is an option on future opportunities. Holding cash when no bargains exist is a valid strategy, not a drag on performance.",
    "Catalysts: look for events that will close the gap between price and value — spin-offs, restructurings, management changes, buybacks.",
    "Contrarian by necessity: value investing requires going against the crowd. When everyone is selling, bargains appear. When everyone is buying, they don't.",
    "The financial markets are not efficient. They are driven by emotion, institutional constraints, and short-term thinking. This creates opportunities for patient investors.",
])

_add("Poor Charlie's Almanack", "Charlie Munger", "Mental Models", [
    "Invert, always invert. Instead of asking how to make money, ask how to lose money — and avoid those things. Quick wealth destroyers: trading frequently, paying high fees, buying hot tips, using leverage, panic selling.",
    "I never allow myself to hold an opinion I can't state the arguments against better than the people who support it. You must understand both sides.",
    "A latticework of mental models: don't just learn finance. Learn psychology, physics, biology, history, mathematics. The best decisions come from multi-disciplinary thinking.",
    "The psychology of human misjudgment: understand cognitive biases (confirmation bias, loss aversion, social proof, incentive-caused bias). These cause investors to make systematic errors.",
    "Circle of competence: know the edge of your knowledge. Most investment disasters come from venturing outside your circle.",
    "Avoid stupidity: most successful people are not brilliant, they just avoid stupid things. Don't drink, don't smoke, don't gamble, don't leverage, don't trade on tips.",
    "The multiple is not the math. Just because you can calculate a DCF doesn't mean it's right. Garbage in, garbage out. Focus on the quality of inputs.",
    "Patience + preparation: wait for the fat pitch. You don't need to swing at every opportunity. The best investors make very few, very large bets.",
])

_add("The Most Important Thing", "Howard Marks", "Risk & Cycles", [
    "Second-level thinking: 'It's a good company, but everyone thinks it's a great company — so it's overpriced.' First-level thinks about quality. Second-level thinks about expectations vs reality.",
    "Risk is not volatility. Risk is the probability of permanent loss. Most 'risk models' measure volatility, not risk.",
    "Markets are cyclical. Trees don't grow to the sky, and things don't go to zero. Mean reversion is the most powerful force in finance.",
    "The most profitable thing is to buy when others are panicking. The most dangerous thing is to buy when others are euphoric.",
    "You can't predict the future, but you can prepare for it. Assess where we are in the cycle and position accordingly.",
    "Risk control is not about avoiding risk — it's about avoiding losses you can't recover from. Asymmetric risk: never risk 100% to make 20%.",
    "Being too far ahead of your time is indistinguishable from being wrong. Even a correct thesis can take years. Have enough capital to survive until you're proven right.",
    "Investing is not about buying good things. It's about buying things well. A great company at too high a price is a bad investment.",
    "The pendulum swings between greed and fear. At the extremes, the crowd is always wrong. Recognize where the pendulum is and position against the extreme.",
])

_add("You Can Be A Stock Market Genius", "Joel Greenblatt", "Special Situations", [
    "Special situations: spin-offs, mergers, restructurings, rights offerings, reorganizations. These offer returns uncorrelated to the general market.",
    "Spin-offs are the best hunting ground: institutional investors often dump the spinoff (wrong size, wrong sector), creating temporary mispricing. Investigate the spinoff, not the parent.",
    "The key question for any special situation: what is the catalyst? What event will close the gap between price and value?",
    "Merger arbitrage: buy the target after deal announcement. Annualized returns 15-25%. Risk = deal breaks. Assess: (1) antitrust risk, (2) financing risk, (3) shareholder vote risk.",
    "Restructurings: companies emerging from bankruptcy or major reorganization. New management, clean balance sheet, low expectations. High upside if turnaround succeeds.",
    "Rights offerings: existing shareholders get the right to buy new shares at a discount. Sometimes creates forced selling = opportunity.",
    "Don't look for needles in a haystack. Look for haystacks with only a few needles. Special situations are underfollowed = less competition.",
    "Do your own work. Special situations are where independent research pays off. Wall Street doesn't cover them well.",
])


# =========================================================================== #
#  2. MARKET WIZARDS & TRADER INTERVIEWS
# =========================================================================== #
_add("Market Wizards", "Jack Schwager", "Trader Interviews", [
    "The #1 differentiator of successful traders is risk management, not strategy. Cut losses, let profits run. Position sizing matters more than entry timing.",
    "Top traders have a methodology they believe in and execute consistently. They don't second-guess their system on every trade.",
    "Discipline: the best traders are not necessarily the smartest. They are the most disciplined. They follow their rules even when it hurts.",
    "Losses are part of the game. Even the best lose 40%+ of trades. The key is keeping losses small and letting winners run.",
    "Adaptability: markets change. What worked last year may not work this year. The best traders evolve their approach.",
    "Patience: wait for your setup. Most traders overtrade. The best traders do nothing most of the time.",
    "Know yourself: trade a style that fits your personality. Day trading is not for everyone. Swing trading is not for everyone. Find your edge.",
    "Confidence without arrogance: believe in your edge but stay humble. The market can humble you at any time.",
])

_add("Reminiscences of a Stock Operator", "Edwin Lefèvre (Jesse Livermore)", "Classic Memoir", [
    "The trend is your friend. Never fight the primary trend. If the market is in a downtrend, the odds of a long position working are severely diminished.",
    "Volume precedes price. A breakout without volume is suspect. Volume confirms conviction.",
    "Cut losses short, let profits run. The asymmetric payoff (small losses, large gains) is what makes trend-following profitable.",
    "Don't average down. Adding to a losing position is the most common way traders go broke. The market doesn't know your entry price.",
    "Patience: wait for the line of least resistance to be established before entering. The market will tell you when it's ready.",
    "Human nature doesn't change. The same emotions (fear, greed, hope, denial) drive markets today as they did 100 years ago.",
    "Speculation is a business, not a gamble. Treat it with the same discipline you'd apply to any business. Keep records. Analyze your results.",
    "The big money is not in the buying and selling, but in the waiting. Hold winners. Don't cut your profits short.",
])

_add("The New Market Wizards", "Jack Schwager", "Trader Interviews", [
    "Victor Sperandeo: track the 2B rule — if a high is tested and fails, short. If a low is tested and holds, buy. False breakouts are signals.",
    "Stan Druckenmiller: when you have conviction, go big. Don't diversify for the sake of it. Put your money where your best ideas are.",
    "Richard Driehaus: the trend is your friend. Buy stocks making new highs. Don't try to catch falling knives.",
    "Bill Lipschutz: risk management is everything. Position size so that even the worst case is survivable. Never risk more than you can afford to lose.",
    "The best traders have a process, not just a strategy. They review every trade. They learn from mistakes. They constantly improve.",
])

_add("Stock Market Wizards", "Jack Schwager", "Trader Interviews", [
    "Different paths to success: there is no single 'right' way to trade. Some are fundamental, some technical, some quantitative. The key is finding YOUR edge.",
    "Information edge vs analytical edge vs behavioral edge: most individual investors can't compete on information. Compete on behavior (patience, discipline).",
    "The importance of a trading journal: review your trades. Identify patterns. What setups work for you? What doesn't? Data > intuition.",
    "Position sizing is more important than entry timing. A 40% win rate with 2.5:1 R:R is more profitable than 70% win rate with 1:1 R:R.",
])

_add("Unknown Market Wizards", "Jack Schwager", "Trader Interviews", [
    "Hidden edges: some of the best traders are unknown. They don't seek publicity. They quietly compound returns.",
    "Niche markets: look where others don't. Small caps, micro caps, OTC markets, international. Less competition = more edge.",
    "Adapt or die: the traders who survived decades are the ones who adapted. Markets change. Strategies decay. Constant learning is required.",
])


# =========================================================================== #
#  3. TECHNICAL ANALYSIS
# =========================================================================== #
_add("Technical Analysis of the Financial Markets", "John Murphy", "TA Reference", [
    "The three assumptions of TA: (1) market action discounts everything, (2) prices move in trends, (3) history repeats itself (patterns are driven by human psychology).",
    "Trend is the most important concept. An uptrend = higher highs and higher lows. A downtrend = lower highs and lower lows. No trend = range.",
    "Support and resistance: prior highs act as resistance, prior lows act as support. The more times tested, the more significant.",
    "Volume confirms trend. Rising prices + rising volume = healthy. Rising prices + falling volume = divergence (warning).",
    "The longer the timeframe, the more reliable the signal. Weekly signals > daily > hourly. Use multiple timeframes for confirmation.",
    "Moving averages: 200-day MA is the bull/bear dividing line. 50-day MA is the intermediate trend. 20-day MA is the short-term trend.",
    "RSI > 70 = overbought (not necessarily sell). RSI < 30 = oversold (not necessarily buy). Use RSI divergence for signals.",
    "MACD: the histogram is the most useful part. Histogram rising = momentum increasing. Histogram falling = momentum waning.",
    "Bollinger Bands: squeeze (narrow bands) precedes expansion (breakout). Band tags are S/R in ranging markets.",
])

_add("Encyclopedia of Chart Patterns", "Thomas Bulkowski", "Chart Patterns", [
    "Pattern performance varies: some patterns work better than others. Bulkowski tested them all. Use the data, not the myth.",
    "Head and shoulders: 89% accurate in bear markets, 60% in bull markets. The most reliable reversal pattern.",
    "Double bottoms: 65% accurate. Second bottom should have lower volume than the first. Buy on breakout above the between-peak high.",
    "Ascending triangles: 83% accurate in bull markets. The most reliable continuation pattern. Buy on breakout.",
    "Symmetrical triangles: 71% accurate. Direction uncertain — trade the breakout, not the pattern.",
    "Flags and pennants: continuation patterns. 75% accurate. Short duration (1-3 weeks). Buy on breakout from the flag.",
    "Volume matters: breakouts on high volume are 2x more likely to succeed than breakouts on low volume.",
    "Measure rule: for most patterns, the target = pattern height projected from the breakout point.",
])

_add("Japanese Candlestick Charting Techniques", "Steve Nison", "Candlesticks", [
    "Candlesticks show the emotional state of the market: the battle between buyers and sellers in each session.",
    "Doji = indecision. At the top of an uptrend = potential reversal. At the bottom of a downtrend = potential reversal. In the middle = continuation.",
    "Hammer (bullish) and hanging man (bearish): small body at the top, long lower wick. Must have volume confirmation.",
    "Engulfing patterns are among the most reliable: bullish engulfing at a bottom, bearish engulfing at a top.",
    "Morning star and evening star: 3-candle reversal patterns. The star (middle candle) gaps away, the third candle confirms.",
    "Context matters: a hammer in a downtrend is bullish. The same hammer in an uptrend is meaningless. Pattern + context = signal.",
    "Volume confirms candlesticks: a bullish engulfing on 3x average volume is much more reliable than on average volume.",
    "Candlesticks are short-term signals (1-10 sessions). Use them for entry timing, not for long-term trend direction.",
])

_add("Trading Price Action Trends", "Al Brooks", "Price Action", [
    "Every tick matters. Read every bar. The market is constantly giving you information about who is in control — buyers or sellers.",
    "A bar has 5 pieces of data: open, high, low, close, and how it relates to the prior bar. All 5 matter.",
    "Strong trend bar: large body, small wicks, closes near its extreme. Weak trend bar: small body, large wicks, closes in the middle.",
    "The 20-bar EMA is the most important moving average for intraday. Above = bull mode. Below = bear mode. At the EMA = decision point.",
    "Always-in long vs always-in short: if you HAD to be in the market, would you be long or short? That's the current bias.",
    "Bar count: in a strong trend, count the consecutive bars in one direction. 5+ bars = strong. 10+ = very strong (but also overextended).",
    "The higher the timeframe, the more reliable the signal. What looks like a reversal on a 1-min chart might be a pullback on a daily chart.",
])

_add("How to Make Money in Stocks", "William O'Neil", "CANSLIM", [
    "CANSLIM: C = Current quarterly earnings (up 25%+ YoY). A = Annual earnings (up 25%+ over 3 years). N = New product/service/management. S = Supply and demand (float, buybacks). L = Leader or laggard (RS rating). I = Institutional sponsorship. M = Market direction (the most important factor).",
    "Buy when the market is in a confirmed uptrend. 3 out of 4 stocks follow the market. If the market is falling, 75% of stocks will fall too.",
    "The cup and handle pattern: the most reliable bullish continuation pattern. Buy on breakout from the handle.",
    "Volume matters: buy on volume 50%+ above average. Volume confirms conviction.",
    "Cut losses at 7-8%. No exceptions. The 7-8% rule has saved more investors from ruin than any other.",
    "Take profits at 20-25%. You don't need to catch the entire move. 20-25% with consistent risk control compounds.",
    "Relative strength (RS) ranking: buy stocks in the top 10% by 12-month price performance. Leaders keep leading.",
])

_add("Mastering the Trade", "John Carter", "Day Trading", [
    "Market internals: TICK, TRIN, advance/decline. These tell you the market's internal strength, not just the index level.",
    "The opening range: the first 30-60 minutes set the tone for the day. Breakout from the opening range = directional bias.",
    "TTM Squeeze: Bollinger Bands inside Keltner Channels = compression. Breakout from squeeze = expansion. Volatility cycle.",
    "Trade with the trend on your timeframe. Intraday: use 5-min trend. Swing: use daily trend. Position: use weekly trend.",
    "Gap fills: 70% of gaps fill on the same day. Fade the gap if it's at a resistance/support level and the market is not in a strong trend.",
    "Market profile: the POC (Point of Control) is the most traded price. Price tends to revisit it. Use POC as S/R.",
])

_add("High Probability Trading", "Marcel Link", "Trading", [
    "High probability vs low probability: only take trades where the odds are in your favor. Wait for the setup. Patience > activity.",
    "Multiple timeframe alignment: the daily, hourly, and 15-min trends should all align in the same direction. If they conflict, stand aside.",
    "The best trades work immediately. If a trade doesn't move in your favor within 1-3 bars, the thesis may be wrong. Consider exiting.",
    "Trend is your friend until the end when it bends. Trend-following works, but know the signs of a trend change: lower highs, higher lows, volume divergence.",
    "Don't trade the first 30 minutes. The opening range is being established. Let the market show its hand before committing.",
])


# =========================================================================== #
#  4. QUANTITATIVE FINANCE
# =========================================================================== #
_add("Advances in Financial Machine Learning", "Marcos López de Prado", "ML for Finance", [
    "Backtests overstate live returns. The more parameters a strategy has, the more likely it is overfit. Prefer strategies with fewer rules.",
    "Cross-validation on time series must respect temporal order. Never shuffle. Use walk-forward or purged k-fold to avoid look-ahead bias.",
    "Labeling matters more than models. Use the triple-barrier method: (1) upper barrier = take profit, (2) lower barrier = stop loss, (3) vertical barrier = time limit. Label based on which barrier is hit first.",
    "Feature importance > feature selection. Use MDI (Mean Decreased Impurity) and MDA (Mean Decreased Accuracy) to identify the most important features. Drop the rest.",
    "The Sharpe ratio above 2.0 with a backtest is a red flag. Real strategies rarely exceed 1.5. If your backtest shows 3.0+, you have a data error or look-ahead.",
    "Position sizing matters more than entry timing. 40% win rate at 2.5:1 R:R is more profitable than 70% win rate at 1:1.",
    "Fractional differentiation: standard differencing (d=1) removes all memory. No differencing (d=0) is non-stationary. Fractional (0<d<1) preserves some memory while achieving stationarity.",
    "Meta-labeling: first model predicts direction (buy/sell). Second model predicts whether to take the trade (yes/no). This improves precision without hurting recall.",
])

_add("Machine Learning for Asset Managers", "Marcos López de Prado", "ML for Finance", [
    "Diversification is the only free lunch. But correlation matrices are unstable. Use hierarchical risk parity (HRP) instead of mean-variance optimization.",
    "Mean-variance optimization is unstable: small changes in inputs → large changes in output. It maximizes estimation error.",
    "HRP: group assets by correlation hierarchy. Allocate equal risk within each cluster. More robust than Markowitz.",
    "Feature importance: financial data is noisy. Most features are useless. Use MDI/MDA to find the few that matter.",
    "Backtest overfitting: the deflated Sharpe ratio adjusts for multiple testing. If you test 100 strategies, the best will have an inflated Sharpe. Deflate it.",
    "Optimal clustering: use silhouette scores to determine the number of clusters. Don't guess. Let the data decide.",
    "Information theory: use mutual information (not correlation) to measure feature-target relationships. MI captures non-linear relationships.",
])

_add("Algorithmic Trading", "Ernest Chan", "Algo Trading", [
    "Mean reversion works on short timeframes (1-5 days) for liquid stocks. RSI below 10 or Z-score below -2 often precedes a bounce.",
    "Momentum works on longer timeframes (1-12 months). Assets that have outperformed tend to continue outperforming.",
    "Cointegration ≠ correlation. Two stocks can be correlated but not cointegrated. Test with Engle-Granger or Johansen.",
    "The Sharpe ratio of a strategy should be > 1.0 after costs. Below 1.0 = marginal. Below 0.5 = not worth trading.",
    "Maximum drawdown should be < 20% for a single strategy. If a strategy's backtest shows > 30% DD, it's too risky.",
    "Position sizing: use Kelly criterion or fixed fractional (1-2% risk per trade). Volatility-adjusted sizing is essential for portfolio-level risk parity.",
    "Backtesting pitfalls: (1) look-ahead bias, (2) survivorship bias, (3) overfitting, (4) ignoring costs, (5) data snooping.",
    "Always walk-forward test: optimize on period A, test on period B, roll forward. If performance degrades in B, the strategy is overfit.",
])

_add("Quantitative Trading", "Ernest Chan", "Quant Trading", [
    "Find your edge: a quant edge can come from (1) better data, (2) better model, (3) better execution, (4) better risk management. Most retail quants compete on models, but the real edge is often in execution and risk management.",
    "The Sharpe ratio is the single most important metric. SR > 1 = tradable. SR > 2 = excellent. SR > 3 = suspicious.",
    "Backtesting: always include transaction costs. 0.1% per trade minimum (brokerage + spread + slippage). Without costs, any strategy looks good.",
    "Correlation between strategies matters more than correlation between stocks. 5 uncorrelated strategies = better than 50 correlated stocks.",
    "Kelly criterion: f* = (b*p - q) / b. Full Kelly is too volatile. Use 0.25x Kelly (quarter-Kelly) for safety.",
    "The maximum drawdown is the number that will make you abandon the strategy. If your backtest shows 30% DD, ask: can I survive a 40% DD live?",
])

_add("Inside the Black Box", "Rishi Narang", "Quant Funds", [
    "Alpha model: the part of the system that predicts future returns. Two types: (1) trend-following (momentum), (2) mean-reversion (counter-trend).",
    "Risk model: limits how much to trade. Includes position limits, sector limits, leverage limits, drawdown circuit breakers.",
    "Transaction cost model: estimates the cost of trading. Includes spread, market impact, commission, slippage. Essential for high-frequency strategies.",
    "Portfolio construction model: combines alpha, risk, and cost models to decide final positions. The optimizer.",
    "Execution model: how to actually place orders. TWAP, VWAP, implementation shortfall. The difference between backtest and live performance.",
    "Data is the most important input. Bad data = bad decisions. Spend more on data than on models.",
    "The best quants are skeptical of their own results. They look for reasons their strategy might fail, not reasons it might work.",
])

_add("Expected Returns", "Antti Ilmanen", "Asset Returns", [
    "Returns come from four sources: (1) risk premium, (2) behavioral, (3) structural, (4) value-collecting. Understand the source of your edge.",
    "The equity risk premium: stocks beat bonds by 3-5% annually over 20+ years. But equity premium is not guaranteed in any single decade.",
    "The volatility risk premium: implied vol > realized vol persistently. Sell options to harvest VRP. But manage tail risk.",
    "The term premium: long bonds yield more than short bonds (upward sloping yield curve). But the premium varies over time.",
    "The credit premium: corporate bonds yield more than government bonds. Compensates for default risk. But default clustering in recessions.",
    "The liquidity premium: illiquid assets yield more than liquid assets. But liquidity dries up when you need it most.",
    "Momentum premium: winners keep winning. 1-3% annual excess return. But momentum crashes (V-shaped reversals) are brutal.",
    "Value premium: cheap stocks beat expensive stocks. 1-4% annual. But value can underperform for a decade (2010-2020 US).",
])

_add("Active Portfolio Management", "Grinold & Kahn", "Portfolio Management", [
    "The Fundamental Law of Active Management: IR = IC × sqrt(breadth). Information Ratio = Information Coefficient × sqrt(number of independent bets).",
    "IC (Information Coefficient): correlation between forecast and actual returns. IC > 0.05 = useful. IC > 0.10 = excellent.",
    "Breadth: the number of independent investment decisions per year. More breadth = higher IR. 100 stocks × 4 rebalances = 400 decisions.",
    "Alpha = expected active return. Beta = market exposure. Active management = seeking alpha while controlling beta.",
    "The transfer coefficient: how well forecasts are translated into actual portfolio weights. Constraints (no shorting, sector limits) reduce TC.",
    "Risk decomposition: decompose portfolio risk into systematic (market, sector, style) and idiosyncratic (stock-specific). Manage each separately.",
    "The optimal portfolio maximizes IR, not absolute return. Higher IR = more consistent alpha.",
])

_add("Systematic Trading", "Robert Carver", "Systematic", [
    "Rules-based trading removes emotion. The system makes the decision, not you. You just execute.",
    "Trend following: buy when price > 200-day MA, sell when < 200-day MA. Simple but effective. Captures the big moves.",
    "Carry: buy high-yield assets, sell low-yield. Persistent across asset classes. The carry factor.",
    "Value: buy cheap, sell expensive. Use P/E, P/B, or yield rank. Value is a slow factor — takes years to play out.",
    "Multi-strategy: combine trend + carry + value. Uncorrelated strategies reduce portfolio risk without reducing return.",
    "Position sizing: use expected return / expected risk. Higher conviction = larger position. But cap at 2% risk per trade.",
    "Backtesting: include costs. Use out-of-sample testing. Walk-forward optimization. If it doesn't work out-of-sample, it's overfit.",
    "The system should be simple enough to explain in one paragraph. Complexity = overfitting risk.",
])

_add("Evidence-Based Technical Analysis", "David Aronson", "TA Validation", [
    "Most TA patterns have no statistical edge. Test them. If they don't pass a significance test, they're noise.",
    "Data mining bias: if you test 100 patterns, 5 will appear significant by pure chance (at 5% level). Adjust for multiple testing.",
    "White's Reality Check: a statistical method to determine if a strategy's performance is real or an artifact of data mining.",
    "The best evidence: large sample, out-of-sample test, multiple markets, multiple timeframes. If it works everywhere, it's real.",
    "TA is not magic. It's a set of statistical regularities. Some work, most don't. Be skeptical.",
])

_add("Algorithmic and High-Frequency Trading", "Cartea, Jaimungal, Penalva", "HFT", [
    "Market making: provide liquidity on both sides. Profit from the spread. Risk: adverse selection (informed traders hit your quotes).",
    "Optimal execution: TWAP (time-weighted), VWAP (volume-weighted), implementation shortfall (minimize total cost including impact).",
    "Order book dynamics: the limit order book reveals supply and demand. Imbalance = directional pressure.",
    "Latency: in HFT, microseconds matter. Co-location, direct feeds, FPGA. The fastest wins.",
    "Adverse selection: when your order is filled, it might be because someone knows something you don't. The 'winner's curse' of market making.",
])


# =========================================================================== #
#  5. MARKET MICROSTRUCTURE
# =========================================================================== #
_add("Trading and Exchanges", "Larry Harris", "Microstructure", [
    "Markets are mechanisms for matching buyers and sellers. The bid-ask spread is the price of immediacy.",
    "Informed traders have an edge. Liquidity traders need to trade (for non-information reasons). Market makers provide liquidity and profit from the spread.",
    "Adverse selection: market makers lose to informed traders. They widen spreads to compensate. The lemons problem in market making.",
    "The spread has three components: (1) order processing cost, (2) inventory cost, (3) adverse selection cost. The last is the largest.",
    "Limit orders vs market orders: limit orders provide liquidity (and earn the spread). Market orders take liquidity (and pay the spread).",
    "Quote-driven vs order-driven markets: NYSE = specialist (quote-driven). NSE = pure order-driven. Each has different dynamics.",
    "Block trading: large orders face market impact. The square root law: impact ∝ sqrt(order size / ADV).",
    "Informed traders prefer limit orders (hide their information). Liquidity traders use market orders (need immediate execution).",
])

_add("Market Microstructure Theory", "Maureen O'Hara", "Microstructure", [
    "Price discovery: how prices incorporate information. Not instantaneous — it happens through the trading process.",
    "The order book is a record of supply and demand at every price level. Depth = liquidity. Thin = dangerous.",
    "Dealer markets vs auction markets: dealers set quotes (NASDAQ). Auction markets match orders (NYSE, NSE). Hybrid models exist.",
    "Liquidity is not free. It has a price (spread) and a quantity (depth). Both can change instantly.",
    "Information asymmetry: when some traders know more than others, spreads widen. The market becomes less liquid.",
    "The Glosten-Milgrom model: spreads compensate for adverse selection. The more informed traders, the wider the spread.",
    "The Kyle model: a single informed trader manipulates price to extract profit slowly. Their trading reveals information gradually.",
])

_add("Algorithmic Trading and DMA", "Barry Johnson", "Execution", [
    "Market impact: your order moves the price against you. Impact ∝ sqrt(order size / ADV). Stay under 1% of ADV for minimal impact.",
    "Implementation shortfall: the difference between the decision price and the execution price. Includes both market impact and opportunity cost.",
    "TWAP (Time-Weighted Average Price): split order evenly over time. Simple but ignores volume patterns.",
    "VWAP (Volume-Weighted Average Price): weight by historical volume. Better than TWAP. Matches the institutional benchmark.",
    "Smart order routing: send orders to the venue with the best price/liquidity. Essential in fragmented markets.",
    "Dark pools: hidden liquidity. No pre-trade transparency. Good for large orders. Risk: information leakage.",
    "The trade-off: trade fast = high market impact. Trade slow = high risk of price moving. Find the optimal speed.",
])


# =========================================================================== #
#  6. OPTIONS & VOLATILITY
# =========================================================================== #
_add("Option Volatility and Pricing", "Sheldon Natenberg", "Options", [
    "Implied volatility is the only unknown in options pricing. When IV > HV, options are expensive (sell). When IV < HV, options are cheap (buy).",
    "Delta = price sensitivity + approximate probability of expiring ITM. ATM call delta ≈ 0.50. Deep ITM → 1.00. Deep OTM → 0.00.",
    "Gamma = rate of delta change. Highest for ATM options. Gamma risk spikes near expiry. Long gamma = want volatility.",
    "Theta = time decay. Negative for buyers. Positive for sellers. Accelerates in last 2 weeks. The enemy of option buyers.",
    "Vega = IV sensitivity. Long vega = want IV to rise. Short vega = want IV to fall. IV mean-reverts.",
    "The volatility skew: OTM puts have higher IV than OTM calls (crash protection demand). Skew steepening = fear rising.",
    "Max pain: the strike where option holders lose most. Price gravitates toward max pain on expiry day.",
    "Option pricing models: Black-Scholes for Europeans. Binomial for Americans. Both assume log-normal returns (wrong but useful).",
    "Dynamic hedging: adjust delta hedge as price moves. But gamma makes this imperfect. Rehedging costs = the price of gamma.",
])

_add("Trading Option Greeks", "Dan Passarelli", "Greeks", [
    "Delta-neutral trading: eliminate directional risk. Profit from volatility (gamma/theta) or time decay (theta).",
    "Gamma scalping: long gamma, delta hedge repeatedly. Profit from realized volatility. But theta is the cost.",
    "Theta-gamma trade-off: long options = long gamma (good) but short theta (bad). Short options = short gamma (bad) but long theta (good).",
    "Vega plays: long vega when IV is low (expect rise). Short vega when IV is high (expect fall). IV is mean-reverting.",
    "Charm = delta decay over time. Important for multi-day delta hedging. Delta drifts even if price doesn't move.",
    "Vanna = delta vs IV cross-sensitivity. Matters when both delta and vega are being managed.",
    "Volga = vega convexity. How vega changes with IV. Matters for vol-of-vol trading.",
])

_add("Volatility Trading", "Euan Sinclair", "Vol Trading", [
    "The volatility risk premium (VRP): implied vol > realized vol persistently. Sell options to harvest VRP. This is the edge in vol selling.",
    "But VRP is not free money. Tail risk = occasional massive losses. 2008, 2020, 2018 (VIX spike). Manage tail risk.",
    "IV rank (IVR) and IV percentile: IVR > 50 = elevated (sell vol). IVR < 20 = depressed (buy vol).",
    "Dispersion trading: short index vol, long single stock vol. Profit when single stock vol > index vol (correlation falls).",
    "Variance swaps: pure vol trade. Pay fixed, receive realized variance. No delta/gamma management. OTC instrument.",
    "Volatility clustering: high vol today → high vol tomorrow. Use GARCH(1,1) for forecasting. Vol is autocorrelated.",
    "The best vol trades: sell after a vol spike (VIX > 30), buy before an event (earnings, elections). But sizing is key — tail risk is real.",
    "Delta hedging frequency: more frequent = better gamma capture but higher costs. Find the optimal frequency.",
])

_add("Options Futures and Other Derivatives", "John Hull", "Derivatives", [
    "Black-Scholes formula: C = S*N(d1) - K*e^(-rT)*N(d2). Assumes: log-normal returns, constant vol, no dividends, continuous trading.",
    "The Greeks: delta (ΔS), gamma (Δdelta), theta (Δt), vega (Δσ), rho (Δr). Each measures sensitivity to one variable.",
    "Put-call parity: C - P = S - K*e^(-rT). If violated, arbitrage exists. The foundation of options pricing.",
    "Binomial trees: discretize time. At each step, price goes up or down. More flexible than Black-Scholes (handles American options, dividends).",
    "Interest rate swaps: exchange fixed for floating. Used for hedging rate exposure. The largest derivatives market by notional.",
    "Credit derivatives: CDS (credit default swap) = insurance against default. CDO = basket of debt. The 2008 crisis was a credit derivative crisis.",
    "Value at Risk (VaR): the maximum expected loss at a given confidence level. But VaR doesn't capture tail risk beyond the threshold. Use CVaR.",
])


# =========================================================================== #
#  7. RISK MANAGEMENT
# =========================================================================== #
_add("Against the Gods", "Peter Bernstein", "Risk History", [
    "The history of risk: from dice games to modern finance. Understanding probability transformed civilization.",
    "Pascal's wager and the birth of probability theory. Expected value = probability × payoff. The foundation of all risk assessment.",
    "Bernoulli's utility theory: humans don't maximize expected value, they maximize expected utility. Diminishing marginal utility = risk aversion.",
    "The normal distribution: most financial models assume it. But financial returns have fat tails. The normal distribution underestimates extreme events.",
    "Bayesian thinking: update beliefs as new information arrives. Prior + new data = posterior. Don't ignore base rates.",
    "Risk management is not about avoiding risk — it's about taking the right risks. The edge in investing is risk selection, not risk avoidance.",
])

_add("Fooled by Randomness", "Nassim Taleb", "Probability", [
    "Survivorship bias: we see winners, not losers. The successful trader may just be lucky. Don't confuse luck with skill.",
    "Hindsight bias: 'I knew it!' You didn't. Keep a journal to see what you actually predicted.",
    "The problem of induction: no amount of white swans proves all swans are white. One black swan falsifies the theory.",
    "Asymmetry: a strategy that makes small gains 99% of the time but has a massive loss 1% of the time looks great — until it blows up.",
    "Lucky fools: traders who got lucky but attribute their success to skill. Time reveals the truth. 'Time is the friend of the wonderful business, the enemy of the mediocre.'",
    "Don't confuse probability with outcome. A 90% probability can still result in the 10% outcome. One event doesn't validate or invalidate a strategy.",
    "The narrative fallacy: we create stories to explain random events. 'The market fell because...' No, the market fell. The 'because' is a story.",
])

_add("The Black Swan", "Nassim Taleb", "Tail Risk", [
    "Black swans: extreme, unexpected, and retrospectively predictable events. They dominate history. 9/11, 2008, COVID. Normal distributions can't model them.",
    "Fat tails: financial returns are not normally distributed. Extreme events are much more likely than the normal distribution predicts.",
    "The turkey problem: the turkey is fed every day for 1000 days. Each day confirms the belief that humans are benevolent. On day 1001, Thanksgiving. Past data can't predict regime changes.",
    "Barbell strategy: 90% in ultra-safe assets, 10% in ultra-aggressive. The safe 90% protects against black swans. The aggressive 10% profits from them.",
    "Antifragility: some systems benefit from shocks. Don't just be robust (survive shocks). Be antifragile (improve from shocks).",
    "Don't forecast. Build systems that survive any forecast. Robustness > prediction.",
    "The ludic fallacy: real life is not a casino. Casino odds are known; real-world odds are unknown. Don't apply casino math to real life.",
])

_add("Antifragile", "Nassim Taleb", "Antifragility", [
    "Antifragility: the opposite of fragility. Fragile things break under stress. Robust things survive stress. Antifragile things get stronger from stress.",
    "Skin in the game: don't trust advice from people who don't bear the consequences. If they don't have skin in the game, their incentives are misaligned.",
    "Via negativa: instead of adding things to improve, remove things that harm. Stop smoking > take vitamins. Avoid stupidity > seek brilliance.",
    "Optionality: having options = antifragile. You can choose the good outcomes and discard the bad. Asymmetric payoff.",
    "Small is beautiful: small entities are more antifragile. Large entities are fragile (too big to fail = too big to manage). Prefer small caps to mega caps.",
    "The turkey fallacy: stability breeds fragility. Long periods of calm → complacency → larger crash when it comes. Volatility is information.",
    "Tinkering > planning: evolutionary progress comes from trial and error, not top-down design. Try many things, keep what works.",
])

_add("Dynamic Hedging", "Nassim Taleb", "Options Risk", [
    "Delta hedging is not risk-free. Gamma means your delta changes as price moves. Rehedging costs = the price of gamma.",
    "The gamma-theta trade-off: long options = long gamma (profit from movement) but short theta (lose time value). You need movement to exceed theta.",
    "Gap risk: your delta hedge works continuously — until the market gaps. Then your hedge is wrong and you take the full gap loss.",
    "Volatility surface: IV varies by strike and expiry. Don't assume flat vol. The surface has structure (skew, term structure).",
    "Stress test your book: what happens if the market drops 10%? If vol spikes to 50? If correlation goes to 1? Know your worst case.",
])


# =========================================================================== #
#  8. PSYCHOLOGY
# =========================================================================== #
_add("Trading in the Zone", "Mark Douglas", "Trading Psychology", [
    "Think in probabilities, not certainties. No single trade matters. What matters is the series of trades executed consistently.",
    "Accept the risk before entering. If you haven't fully accepted that this trade can lose, you will hesitate to cut the loss.",
    "The 5 fundamental truths: (1) anything can happen, (2) you don't need to know what will happen to make money, (3) any set of variables has an edge, (4) an edge is just higher probability, (5) every moment is unique.",
    "The 7 principles of consistency: (1) I objectively identify my edges, (2) I predefine risk, (3) I accept the risk, (4) I act on the edge without hesitation, (5) I pay myself as the market makes money available, (6) I monitor my susceptibility to errors, (7) I understand the absolute truth of these principles.",
    "Fear of missing out (FOMO) and fear of loss are the two emotions that destroy traders. Both come from not accepting risk.",
    "The zone: a state of flow where you execute without thinking. Achieved through: (1) a tested system, (2) predefined risk, (3) no attachment to outcome.",
    "Self-sabotage: we undermine ourselves because of deep-seated beliefs about money, success, and self-worth. Identify and challenge these beliefs.",
])

_add("The Disciplined Trader", "Mark Douglas", "Trading Psychology", [
    "The market is never wrong. If you lose, it's because your analysis was wrong or your execution was flawed — not because 'the market is manipulated.'",
    "Discipline is a habit, not a personality trait. Build it through repetition. Every time you follow your rules, you strengthen the habit.",
    "The pain of a loss is psychological, not financial. A ₹10,000 loss feels worse than a ₹10,000 gain feels good. This asymmetry (loss aversion) causes bad decisions.",
    "Don't trade to make money. Trade to execute your system perfectly. The money follows the execution.",
    "The market doesn't know you. It doesn't care about your P&L. It's not out to get you. It's just a mechanism.",
])

_add("The Daily Trading Coach", "Ari Kiev", "Trading Psychology", [
    "Revenge trading after a loss is the most destructive behavior. After a loss, take a break. The market doesn't owe you anything.",
    "Process goals > result goals. 'I will follow my plan' is a process goal. 'I will make ₹50,000' is a result goal. Process goals are controllable.",
    "Tilt detection: are you breathing fast? Checking the screen every 10 seconds? Increasing position size? These are signs of tilt. Stop trading.",
    "The coaching relationship: having someone review your trades accelerates learning. Trading is lonely — find a coach or accountability partner.",
    "Visualization: mentally rehearse your trading day before it happens. Visualize following your rules, cutting losses, letting winners run.",
    "Stress management: meditation, exercise, sleep. Trading under stress = bad decisions. Manage your physiology.",
])

_add("Enhancing Trader Performance", "Brett Steenbarger", "Trading Psychology", [
    "Deliberate practice: not just screen time, but focused improvement. Review 100 trades. Identify your most common mistake. Drill the correction.",
    "Pattern recognition: expertise comes from seeing thousands of patterns. You can't shortcut this. Put in the reps.",
    "The 10,000-hour rule: true expertise requires ~10,000 hours of deliberate practice. There are no shortcuts.",
    "Mentorship: learn from someone who's done it. A good mentor saves you years of trial and error.",
    "Metrics: track not just P&L, but process metrics: plan adherence rate, average hold time, R-multiple per trade, max consecutive losses.",
    "Fatigue: trading when tired = bad decisions. Know your optimal trading hours. Stop when you're not sharp.",
])

_add("Thinking Fast and Slow", "Daniel Kahneman", "Behavioral Finance", [
    "System 1 (fast, intuitive) vs System 2 (slow, analytical). Most trading decisions are System 1 — quick, emotional, error-prone. Force System 2 engagement.",
    "Anchoring: we fixate on the first number we see. Your entry price is an anchor. The market doesn't care about your entry.",
    "Loss aversion: losses hurt 2x more than gains feel good. This causes: holding losers (hoping they come back), selling winners too early.",
    "Confirmation bias: we seek information that confirms our beliefs. Actively seek counter-arguments. The bear case for longs, the bull case for shorts.",
    "Overconfidence: we overestimate our ability to predict. 80% of drivers think they're above average. 80% of traders think they're profitable.",
    "The availability heuristic: we overestimate the probability of events we can easily recall. A recent crash feels more likely than it is.",
    "Regression to the mean: extreme performance tends to revert. A stock that's up 200% is likely to underperform going forward.",
    "Framing: '90% survival rate' vs '10% mortality rate' — same data, different decision. Always reframe to see the full picture.",
])


# =========================================================================== #
#  9. ECONOMICS & MACRO
# =========================================================================== #
_add("Principles for Dealing with the Changing World Order", "Ray Dalio", "Macro", [
    "The big cycle: empires rise and fall in a predictable pattern: (1) new rules/new system, (2) peace/prosperity, (3) debt expansion, (4) bubble, (5) top, (6) decline, (7) revolution/war, (8) reset.",
    "The 8 key measures of a country's power: (1) education, (2) competitiveness, (3) innovation/technology, (4) economic output, (5) share of world trade, (6) military strength, (7) financial center strength, (8) reserve currency status.",
    "Reserve currency status lags economic decline by 20-50 years. The US economy peaked relative to the world in 1950, but the USD is still the reserve currency.",
    "Debt crises: when debt can't be serviced, there are two options: (1) austerity (painful, deflationary), (2) money printing (inflationary, currency devaluation). Governments always choose printing.",
    "Internal conflict: widening wealth gaps + economic stress → populism → internal conflict → revolution or civil war. The precursor to empire decline.",
    "External conflict: a rising power challenges the existing power (Thucydides trap). War is the typical outcome. US vs China is the current dynamic.",
    "The cycle takes 250-300 years. We're in the late stage of the US cycle. Position for: (1) currency devaluation, (2) inflation, (3) geopolitical conflict.",
])

_add("Principles", "Ray Dalio", "Decision Making", [
    "Radical transparency: don't hide mistakes. Expose them. Learn from them. A culture of honesty > a culture of politeness.",
    "Pain + reflection = progress. Every loss is a data point. Don't blame the market — improve the process.",
    "Believability-weighted decision making: not all opinions are equal. Weight opinions by the person's track record on that topic.",
    "The 5-step process: (1) have clear goals, (2) identify problems, (3) diagnose root causes, (4) design solutions, (5) execute.",
    "Don't trust your gut — trust the process. Build decision-making systems that aggregate data, not emotions.",
    "Diversify across uncorrelated return streams. 15-20 uncorrelated bets can reduce risk by 80% without reducing return. The Holy Grail.",
    "Ego and blind spots are the two biggest barriers to good decisions. Ego prevents admitting you're wrong. Blind spots prevent seeing the truth.",
])

_add("Manias Panics and Crashes", "Charles Kindleberger", "Financial Crises", [
    "The Minsky model: (1) displacement (a new opportunity), (2) boom (credit expansion), (3) euphoria (prices decouple from fundamentals), (4) distress (insiders sell), (5) panic (everyone sells).",
    "Credit is the fuel. Without credit expansion, bubbles can't form. Watch credit growth — when it accelerates rapidly, a bubble may be forming.",
    "The bigger the bubble, the bigger the crash. And the longer the boom, the more painful the bust.",
    "Bubbles always burst. The only question is when. Don't try to time the top — just don't participate in the euphoria phase.",
    "Government intervention can delay but not prevent the crash. And intervention often makes the eventual crash worse (moral hazard).",
    "After the crash, regulation tightens. Then it loosens over time. Then the cycle repeats. Financial memory lasts ~20 years (one generation).",
])

_add("The Alchemy of Finance", "George Soros", "Macro", [
    "Reflexivity: market prices affect the fundamentals, which in turn affect prices. This feedback loop can create bubbles and crashes.",
    "Positive feedback loop: rising prices → improved fundamentals (easier financing, confidence) → more buying → higher prices. This is how bubbles form.",
    "Negative feedback loop: falling prices → deteriorating fundamentals → more selling → lower prices. This is how crashes happen.",
    "Far-from-equilibrium conditions: when prices diverge significantly from fundamentals, the market is in a reflexive feedback loop. These are the biggest opportunities.",
    "Soros's test: find the assumption behind the market consensus. If that assumption is wrong, bet against it. The bigger the consensus, the bigger the opportunity.",
    "Survival first: 'I'm only rich because I know when I'm wrong.' Cut losses immediately when the thesis breaks. Survival > being right.",
    "It's not whether you're right or wrong, but how much you make when you're right and how much you lose when you're wrong. Asymmetric payoffs.",
])

_add("Big Debt Crises", "Ray Dalio", "Debt Cycles", [
    "The debt cycle: (1) debt is good (finances productive investment), (2) debt becomes excessive (finances speculation), (3) debt crisis (can't be serviced), (4) deleveraging (debt is reduced), (5) recovery.",
    "Deleveraging can happen 4 ways: (1) austerity (cut spending), (2) default/restructuring, (3) wealth redistribution (tax), (4) money printing. The best deleveragings use all 4 in balance.",
    "Deflationary deleveraging: austerity + default = depression. Money printing is not used. Painful but eventually recovery occurs.",
    "Inflationary deleveraging: money printing = currency devaluation. Debt is inflated away. Less painful in nominal terms but destroys savings.",
    "The beautiful deleveraging: 3-4% nominal growth, 0-1% real growth, 2-3% inflation. Debt/GDP ratio falls. This is the optimal path.",
    "Timing: debt crises typically take 5-10 years from peak to recovery. Be patient. Don't catch falling knives in the early stages.",
])


# =========================================================================== #
#  10. FINANCIAL HISTORY & CRASHES
# =========================================================================== #
_add("Extraordinary Popular Delusions and the Madness of Crowds", "Charles Mackay", "Bubbles", [
    "Tulip mania (1637): tulip bulb prices rose 20x in 3 months, then crashed 99%. The first recorded financial bubble.",
    "South Sea Bubble (1720): stock rose 10x, then crashed 90%. Even Isaac Newton lost money. 'I can calculate the motion of heavenly bodies, but not the madness of people.'",
    "Mississippi Bubble (1720): John Law's scheme to finance French government debt with shares. Rose 20x, crashed to zero.",
    "The pattern: (1) new opportunity, (2) speculation, (3) mania, (4) crash, (5) recrimination. Every bubble follows this pattern.",
    "Crowd madness: people in groups think differently than individuals. The crowd amplifies both greed and fear. Don't follow the crowd at extremes.",
    "No one is immune: even the smartest people get caught. Newton, Keynes (initially), modern quant funds. Humility is essential.",
])

_add("Devil Take the Hindmost", "Edward Chancellor", "Speculation History", [
    "Speculation is as old as markets themselves. It serves a purpose (price discovery, liquidity) but also creates instability.",
    "Every era has its speculative mania. The instruments change (tulips, canals, railroads, internet, crypto), but the psychology doesn't.",
    "The role of credit: speculation requires leverage. Easy credit = bigger bubbles. Tight credit = no bubbles.",
    "The social function of speculation: it transfers risk from hedgers to speculators. But when speculators dominate, the market becomes a casino.",
    "Regulation follows crisis: after every crash, new rules are written. But rules decay over time. The cycle: boom → bust → regulate → forget → boom.",
])

_add("Lords of Finance", "Liaquat Ahamed", "Central Banking", [
    "The 4 central bankers who caused the Great Depression: Montagu Norman (Bank of England), Benjamin Strong (Fed), Hjalmar Schacht (Reichsbank), Émile Moreau (Banque de France).",
    "The gold standard forced deflation: countries couldn't print money, so prices fell, debt became heavier, economies collapsed.",
    "Competitive devaluations: countries devalued their currencies to boost exports. But when everyone devalues, no one benefits. A race to the bottom.",
    "War reparations: Germany's crushing reparations (Treaty of Versailles) destabilized Europe. Economic hardship → political extremism → WWII.",
    "The lesson: central bankers are fallible. Their decisions can make crises worse. Don't blindly trust 'the adults in the room.'",
])

_add("When Genius Failed", "Roger Lowenstein", "LTCM", [
    "LTCM: Long-Term Capital Management. Nobel laureates (Scholes, Merton) + Wall Street's best. 40% annual returns. Then it blew up in 1998.",
    "The strategy: convergence arbitrage. Find small mispricings, leverage them 25:1. Small edge × huge leverage = big returns. But also big risk.",
    "Russia defaulted. Markets panicked. Correlations went to 1. Every LTCM trade moved against them simultaneously. Leverage amplified the losses.",
    "The Fed organized a bailout. LTCM's counterparties (the major banks) were at risk. 'Too big to fail' before the term existed.",
    "The lesson: leverage kills. A good strategy with 25x leverage = a bomb. Risk models based on normal times fail in crises. Fat tails matter.",
    "Greed + arrogance = disaster. LTCM's partners believed their models were infallible. The market disagreed.",
])

_add("Too Big to Fail", "Andrew Ross Sorkin", "2008 Crisis", [
    "The 2008 crisis: subprime mortgages → CDOs → bank failures → global financial crisis. The chain of events that almost brought down the system.",
    "Lehman Brothers: the one they let fail. 158-year-old firm, gone in a weekend. The decision not to bail out Lehman triggered the panic.",
    "AIG: the one they had to save. $182 billion bailout. AIG insured CDOs. If AIG failed, every bank that bought insurance would take the loss.",
    "TARP: $700 billion to buy toxic assets. The government became the buyer of last resort. Stabilized the system.",
    "The lesson: interconnectedness = systemic risk. When every bank owes every other bank, one failure can cascade. Contagion is the real danger.",
])


# =========================================================================== #
#  11. HEDGE FUNDS & QUANT FIRMS
# =========================================================================== #
_add("More Money Than God", "Sebastian Mallaby", "Hedge Fund History", [
    "A.W. Jones: invented the hedge fund (1949). Long/short equity. 'Hedged' = market neutral. The original model.",
    "Soros: used reflexivity to identify bubbles. Shorted the British pound (1992) — 'broke the Bank of England.' $1B profit in one day.",
    "Paul Tudor Jones: predicted the 1987 crash. Used technical analysis + macro. 'The most important rule is to play great defense, not great offense.'",
    "Steinhardt: the original macro trader. Used leverage aggressively. 'I never liked the market. I liked making money.'",
    "The hedge fund model: 2% management fee + 20% performance fee. Aligns manager with investor. But also encourages risk-taking.",
    "The best hedge funds are contrarian. They go against the crowd. They take positions that are uncomfortable. That's where the edge is.",
])

_add("The Man Who Solved the Market", "Gregory Zuckerman", "Jim Simons/Renaissance", [
    "Jim Simons: mathematician, not financier. Used pure data + ML. No economic theory. Pattern recognition on price data.",
    "Renaissance's Medallion Fund: 66% annual returns (before fees) for 30+ years. 39% after fees. The best track record in history.",
    "The approach: ensemble of weak signals. No single model was great. But combining hundreds of small edges created a massive edge.",
    "Hire scientists, not traders. Physicists, mathematicians, statisticians. Fresh perspectives > Wall Street experience.",
    "Short holding periods: Medallion holds positions for days, not months. High frequency = more data = more edge.",
    "Continuous refinement: the team constantly tweaks models. Markets change. Models decay. Adapt or die.",
    "Never share the secret. Renaissance is notoriously secretive. No external investors since 2005. They don't need outside money.",
    "The lesson: data > theory. Simons didn't try to understand WHY prices moved. He just found patterns that predicted movement.",
])

_add("The Quants", "Scott Patterson", "Quant Crash 2007", [
    "The quant crisis of August 2007: quant funds lost billions in a week. Not because their models were wrong, but because everyone had the same models.",
    "Crowded trades: when everyone is doing the same trade, the exit is blocked. A fund forced to unwind → everyone's positions move → more unwinding → death spiral.",
    "The counterfactual risk: models based on historical data assume the future will resemble the past. When it doesn't, models fail catastrophically.",
    "Morgan Stanley's Process Driven Trading (PDT) lost $300M in a single day. Not from bad positions, but from everyone unwinding the same positions.",
    "The lesson: crowding kills. If your strategy is popular, it's already losing its edge. The best strategies are the ones no one else is doing.",
])

_add("Dark Pools", "Scott Patterson", "HFT", [
    "Dark pools: private exchanges where large institutions trade without revealing their orders. ~30% of US volume.",
    "The original dark pool: Island ECN (1990s). Allowed anonymous trading. Attracted HFT firms who could see the order flow.",
    "HFT front-running: HFT firms see your order (via dark pool or exchange), then race ahead to buy the stock before you, selling it back at a higher price.",
    "Flash crash (May 6, 2010): the Dow dropped 1000 points in minutes, then recovered. HFT algorithms amplified the selling.",
    "Payment for order flow: brokers sell your order to HFT firms. The HFT firm trades against you. This is how Robinhood makes money.",
    "The lesson: the market is not fair. The little guy is at a disadvantage. Use limit orders, not market orders. Don't trade against HFT.",
])

_add("Flash Boys", "Michael Lewis", "HFT", [
    "HFT firms pay exchanges for faster data. They see your order milliseconds before the rest of the market. They front-run you.",
    "Co-location: HFT firms put their servers in the same building as the exchange. Milliseconds matter.",
    "The Brad Katsuyama story: he discovered that the market was fragmented. His order arrived at different exchanges at different times. HFT front-ran him.",
    "IEX: the exchange Katsuyama built. A 'speed bump' (350 microsecond delay) prevents HFT front-running. Fair markets.",
    "The lesson: the stock market is rigged in favor of the fastest. Retail traders can't compete on speed. Compete on patience instead.",
])


# =========================================================================== #
#  12. AI / DATA SCIENCE FOR TRADING
# =========================================================================== #
_add("Hands-On Machine Learning", "Aurélien Géron", "ML Practical", [
    "Feature engineering > model selection. Good features with a simple model beat bad features with a complex model.",
    "Cross-validation: never test on training data. Use k-fold CV. For time series, use walk-forward (not random k-fold).",
    "Regularization: L1 (Lasso) for feature selection. L2 (Ridge) for shrinking coefficients. Elastic Net = both. Prevents overfitting.",
    "Ensemble methods: Random Forest = bagging (reduce variance). XGBoost = boosting (reduce bias). Both > single decision trees.",
    "Hyperparameter tuning: Grid Search (exhaustive), Random Search (faster), Bayesian optimization (smartest). Always use CV.",
    "Dimensionality reduction: PCA for linear. t-SNE/UMAP for non-linear. Use when you have too many features.",
    "Don't use deep learning by default. For tabular data, XGBoost usually wins. DL is for images, text, sequences.",
])

_add("Deep Learning", "Ian Goodfellow", "Deep Learning", [
    "Deep learning works when you have LOTS of data. For financial data (limited), simpler models often outperform.",
    "Overfitting is the #1 enemy. Use dropout, batch normalization, early stopping, weight decay. All prevent overfitting.",
    "Vanishing gradients: deeper networks are harder to train. Use ReLU activation, batch norm, residual connections.",
    "Sequence models: RNN → LSTM → GRU → Transformer. For time series, Transformers are state-of-art but need lots of data.",
    "Transfer learning: don't train from scratch. Use pre-trained models and fine-tune. Especially for NLP (earnings call analysis).",
    "For trading: DL is overkill for most problems. Use it for: (1) NLP on earnings calls, (2) alternative data (satellite images), (3) very high-frequency data.",
])

_add("Pattern Recognition and Machine Learning", "Christopher Bishop", "ML Theory", [
    "Bayesian inference: update beliefs as data arrives. Prior + likelihood = posterior. The principled way to handle uncertainty.",
    "The bias-variance tradeoff: high bias = underfit (too simple). High variance = overfit (too complex). Find the sweet spot.",
    "Generative vs discriminative models: generative (Bayes) models the joint distribution. Discriminative (logistic regression) models the boundary. Discriminative usually wins for classification.",
    "Model selection: use cross-validation. But also consider: simplicity, interpretability, computational cost. The best model is the simplest one that works.",
    "The curse of dimensionality: as features increase, data becomes sparse. Need exponentially more data. Use feature selection.",
])

_add("Probabilistic Machine Learning", "Kevin Murphy", "ML Theory", [
    "Probabilistic thinking: don't give point estimates. Give distributions. 'I think the stock will go up 3% ± 5%.' More honest.",
    "Bayesian optimization: for hyperparameter tuning. More efficient than grid/random search. Builds a surrogate model.",
    "Gaussian processes: a distribution over functions. For time series forecasting with uncertainty estimates. Better than point forecasts.",
    "Hidden Markov Models: for regime detection. States (bull/bear/range) are hidden. Observations are price data. Transition probabilities between states.",
    "Variational inference: approximate complex posterials with simpler distributions. Faster than MCMC for large datasets.",
    "For trading: probabilistic models give you confidence intervals, not just point forecasts. This enables better position sizing.",
])

_add("Reinforcement Learning: An Introduction", "Sutton & Barto", "RL", [
    "RL: an agent learns by interacting with an environment. State → action → reward → next state. The agent maximizes cumulative reward.",
    "Q-learning: learn the value of each (state, action) pair. Off-policy. Can learn from any experience, even random.",
    "Policy gradient: directly optimize the policy (action distribution). On-policy. Better for continuous action spaces.",
    "PPO (Proximal Policy Optimization): the go-to RL algorithm for trading. Stable, sample-efficient, works well in practice.",
    "Reward shaping: the reward function determines what the agent learns. For trading: use risk-adjusted return (Sharpe), not absolute return.",
    "Exploration vs exploitation: the agent must try new actions (explore) while exploiting known good actions. Epsilon-greedy or UCB.",
    "For trading: RL is promising but hard. Reward is noisy. The environment is non-stationary (markets change). Sim-to-real transfer is the bottleneck.",
])


# =========================================================================== #
#  13. PORTFOLIO CONSTRUCTION
# =========================================================================== #
_add("The Little Book of Common Sense Investing", "John Bogle", "Indexing", [
    "Buy the whole market via a low-cost index fund. You get the market return at minimal cost. No stock picking, no market timing.",
    "Costs matter: 1% annual fee = 28% of your wealth over 40 years. Index funds charge 0.03%. The difference compounds.",
    "Don't look for the needle. Buy the haystack. The probability of picking the best stock is near zero. Buy all of them.",
    "Reversion to the mean: 80% of active managers underperform the index over 10+ years. Past outperformance doesn't predict future outperformance.",
    "Time in the market > timing the market. The best days often follow the worst days. Miss the 10 best days in 20 years → half your returns.",
    "Stay the course. The market will crash. It always has. It always recovers. Don't sell at the bottom. Don't buy at the top. Just keep buying.",
])

_add("A Random Walk Down Wall Street", "Burton Malkiel", "Efficient Markets", [
    "The efficient market hypothesis: stock prices reflect all known information. You can't consistently beat the market.",
    "Random walk: short-term price movements are random. Technical analysis is useless. Fundamental analysis is already priced in.",
    "The weak form: prices reflect all past price data. TA doesn't work. (Mostly true.)",
    "The semi-strong form: prices reflect all public information. Fundamental analysis doesn't work. (Partly true — but value/momentum factors exist.)",
    "The strong form: prices reflect ALL information (including insider). Nothing works. (False — insiders do profit.)",
    "The smartest strategy for most investors: buy and hold a diversified index fund. Don't trade. Don't time. Just hold.",
    "Behavioral finance: markets are not perfectly efficient. There are anomalies (momentum, value, low-vol). But exploiting them is hard and costly.",
])

_add("Asset Management", "Andrew Ang", "Factor Investing", [
    "Factors are the building blocks of returns. Just as nutrients are to food, factors are to portfolios. Understand the factors you're exposed to.",
    "The 5 main factors: (1) market (equity risk premium), (2) size (small beats large), (3) value (cheap beats expensive), (4) momentum (winners keep winning), (5) low volatility (low-beta outperforms).",
    "Factor timing is hard. Don't try to time factors. Just hold a diversified portfolio of factors. Rebalance annually.",
    "Factors can underperform for a decade. Value underperformed 2010-2020. Momentum crashed in 2009. Patience is required.",
    "Smart beta: factor-tilted index funds. Low cost. Transparent. Rules-based. Better than active management for most investors.",
    "Factor decay: when everyone knows about a factor, it weakens. The value factor has weakened since 2000. Monitor factor efficacy.",
])

_add("Quantitative Equity Portfolio Management", "Qian, Hua, Sorensen", "Quant Portfolio", [
    "Alpha signal: the prediction of future returns. The core of quant equity. Combine multiple signals for robustness.",
    "Risk model: the covariance matrix of returns. Essential for portfolio optimization. Use factor models (Barra) to decompose risk.",
    "Optimization: maximize alpha subject to risk constraints. Mean-variance, Black-Litterman, or robust optimization.",
    "Constraints: real portfolios have constraints (no shorting, sector limits, turnover limits, position limits). These reduce performance but are necessary.",
    "Transaction costs: model them explicitly. Market impact ∝ sqrt(trade size / ADV). Include in the optimizer.",
    "Backtesting: walk-forward. Out-of-sample. Multiple regimes. Include costs. If it doesn't work out-of-sample, it's overfit.",
    "The quant equity process: (1) data, (2) alpha signals, (3) risk model, (4) optimizer, (5) execution, (6) performance attribution.",
])


# =========================================================================== #
#  14. ADVANCED / PhD-LEVEL
# =========================================================================== =
_add("Asset Pricing", "John Cochrane", "Asset Pricing", [
    "Asset pricing: the price of any asset = expected discounted payoff. P = E[m × x], where m is the stochastic discount factor.",
    "The consumption CAPM: the discount factor is related to consumption growth. Assets that pay off when consumption is low (bad times) are valuable.",
    "The Hansen-Jagannathan bound: the Sharpe ratio of any asset is bounded by the volatility of the discount factor. This limits achievable risk-adjusted returns.",
    "Factor models: any asset's expected return = risk-free rate + sum of (factor risk premium × factor exposure). The art is identifying the right factors.",
    "The equity premium puzzle: stocks have historically returned 6% more than bonds. This is too high to be explained by reasonable risk aversion. Either investors are extremely risk-averse, or the premium will be lower going forward.",
    "Time-varying expected returns: expected returns are not constant. They vary with business cycle, valuation, volatility. Buy when expected returns are high (cheap, scary).",
])

_add("Investment Science", "David Luenberger", "Finance", [
    "Present value: PV = CF / (1+r)^n. The foundation of all valuation. The discount rate r = opportunity cost of capital.",
    "Duration: the weighted average time to cash flows. Measures interest rate sensitivity. Duration × Δy ≈ ΔP/P.",
    "Convexity: the second derivative of price w.r.t. yield. Positive convexity = good (price rises more when rates fall than it falls when rates rise).",
    "Portfolio optimization: maximize expected return for a given risk (Markowitz). The efficient frontier. But sensitive to input errors.",
    "CAPM: E[R] = Rf + β(E[Rm] - Rf). The simplest asset pricing model. Beta = covariance with market / variance of market.",
    "Arbitrage pricing theory (APT): E[R] = Rf + sum of (factor risk premium × factor beta). More general than CAPM. Multiple factors.",
    "Option pricing: Black-Scholes is a special case of no-arbitrage pricing. The key insight: replicate the option with stock + bond.",
])

_add("Financial Calculus", "Baxter & Rennie", "Derivatives Math", [
    "Stochastic calculus: Ito's lemma is the chain rule for stochastic processes. df = (∂f/∂t)dt + (∂f/∂S)dS + 0.5(∂²f/∂S²)(dS)².",
    "Geometric Brownian motion: dS = μSdt + σSdW. The standard model for stock prices. Assumes constant drift and volatility.",
    "Risk-neutral pricing: the trick that makes option pricing possible. Under the risk-neutral measure, all assets grow at the risk-free rate.",
    "Girsanov's theorem: the mathematical foundation of risk-neutral pricing. Changes the drift of a Brownian motion by changing the measure.",
    "Martingale: a process whose expected future value = current value. Under the risk-neutral measure, discounted stock prices are martingales.",
    "The Feynman-Kac formula: links PDEs (like Black-Scholes) to expectations. Option price = E[risk-neutral payoff] discounted at risk-free rate.",
])

_add("Stochastic Calculus for Finance I & II", "Steven Shreve", "Stochastic", [
    "Binomial model: the simplest model of stock price evolution. At each step, up or down. Converges to Black-Scholes as steps → ∞.",
    "No-arbitrage: the fundamental principle. If two portfolios have the same payoff, they must have the same price. Otherwise, arbitrage.",
    "The Black-Scholes PDE: ∂V/∂t + 0.5σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0. Solved with boundary conditions to get the option price.",
    "The Greeks from Black-Scholes: delta = N(d1), gamma = N'(d1)/(Sσ√T), theta = -SN'(d1)σ/(2√T) - rKe^(-rT)N(d2), vega = S√T N'(d1).",
    "Martingale representation theorem: any derivative can be replicated by trading the stock and bond. The foundation of dynamic hedging.",
    "Jump-diffusion models: stock prices can jump (not just diffuse). More realistic than pure Brownian motion. Merton's jump-diffusion model.",
    "Stochastic volatility models: volatility is not constant. Heston model: dσ = κ(θ-σ)dt + ξσdW₂. Captures vol clustering and skew.",
])


# =========================================================================== #
#  15. REMAINING ELITE PICKS
# =========================================================================== =
_add("Competition Demystified", "Bruce Greenwald", "Strategy", [
    "The only two barriers to entry: (1) competitive advantage (moat), (2) government protection. Without one of these, competition drives returns to cost of capital.",
    "Three types of moats: (1) supply (cost advantage — scale, process, location), (2) demand (customer captivity — switching costs, habit, search costs), (3) economies of scale (larger = cheaper per unit).",
    "Elephant vs ant: if the incumbent (elephant) has economies of scale, the entrant (ant) cannot win on price. The elephant can always undercut.",
    "Local dominance: a company can have scale advantage in a local market even if it's small globally. Think regional banks, local newspapers (historically).",
    "Moat erosion: watch for (1) new technology (disrupts cost advantage), (2) new business model (disrupts demand captivity), (3) market growth (dilutes scale advantage).",
    "Porter's Five Forces: simplify — the only force that matters is barriers to entry. If barriers are high, the incumbent wins. If low, competition wins.",
])

_add("Quality Investing", "Thornton", "Quality", [
    "Quality = high ROIC + low debt + stable earnings + strong cash flow. Quality companies compound capital for decades.",
    "The quality factor: high-quality stocks outperform low-quality stocks on a risk-adjusted basis. Documented across markets and decades.",
    "Quality + value: the best combination. Buy high-quality stocks when they're cheap. Avoid value traps (low quality + low price = value destruction).",
    "Quality + momentum: another powerful combo. Buy high-quality stocks with positive momentum. The momentum confirms the quality thesis.",
    "Quality signals: ROE > 15%, ROIC > WACC, debt/equity < 0.5, positive free cash flow, stable margins (low coefficient of variation).",
    "Indian quality stocks: HINDUNILVR, NESTLEIND, ASIANPAINT, PIDILITIND. High ROE, low debt, stable margins, strong brands.",
])

_add("Financial Shenanigans", "Howard Schilit", "Fraud Detection", [
    "Earnings manipulation techniques: (1) revenue recognition (recognize too early), (2) expense capitalization (defer expenses), (3) one-time charges (hide recurring problems), (4) off-balance-sheet entities.",
    "Red flags: (1) earnings >> cash flow, (2) receivables growing faster than revenue, (3) inventory growing faster than sales, (4) frequent restructuring charges, (5) auditor changes.",
    "Revenue recognition: the most common manipulation. Channel stuffing (ship more than ordered), bill-and-hold (recognize before delivery), round-tripping (swap revenue with partners).",
    "Expense capitalization: capitalize what should be expensed (WorldCom capitalized line costs). Inflates current earnings, defers to future.",
    "Cash flow is king: if net income is growing but operating cash flow is flat or declining, earnings quality is deteriorating. The accruals anomaly.",
    "Read the 10-K footnotes: related party transactions, off-balance-sheet entities, contingent liabilities. Where the truth hides.",
    "Satyam (India): the 'Indian Enron.' Faked ₹7,136 crore of cash and bank balances. Red flag: promoter pledging + auditor concerns + inconsistent margins.",
])

_add("The Outsiders", "William Thorndike", "CEO Capital Allocation", [
    "The CEO's most important job: capital allocation. How they deploy cash (reinvest, buyback, dividend, acquire) determines shareholder returns.",
    "The outsider CEOs: Tom Murphy (Capital Cities), Henry Singleton (Teledyne), Warren Buffett (Berkshire), John Malone (TCI), Katharine Graham (Washington Post).",
    "Decentralized operations: let business unit managers run their businesses. HQ = capital allocation only. Don't micromanage operations.",
    "Buybacks vs dividends: buybacks when stock is cheap (below intrinsic value). Dividends when stock is expensive. Don't buy back overvalued stock.",
    "Acquisitions: most destroy value (synergy rarely materializes). The outsiders acquired rarely but boldly, only when prices were depressed.",
    "The key metric: book value growth per share, not revenue growth. Focus on per-share value, not empire-building.",
])

_add("The Psychology of Money", "Morgan Housel", "Behavioral Finance", [
    "Doing well with money has little to do with how smart you are and a lot to do with how you behave. Behavior > intelligence.",
    "Time is the most powerful force in investing. Warren Buffett's fortune = 99% of the compounding happened after age 50. Start early, be patient.",
    "Getting wealthy vs staying wealthy: getting wealthy requires risk-taking and optimism. Staying wealthy requires humility and fear. They require opposite mindsets.",
    "The tail event: a small number of events drive most outcomes. 1% of VC investments = 50% of returns. Don't try to catch every winner. Just don't miss the few that matter.",
    "Room for error: the most important part of every plan is planning for the plan not going according to plan. Margin of safety in everything.",
    "Enough: know when you have enough. The hardest financial skill is getting the goalposts to stop moving. Greed destroys.",
    "Risk is what you don't see: the biggest risks are the ones no one is talking about. If everyone is worried about it, it's already priced in.",
    "Savings rate > income rate. How much you keep > how much you make. Frugality compounds. Lifestyle inflation destroys wealth.",
])

_add("The Dhandho Investor", "Mohnish Pabrai", "Value", [
    "Dhandho = low-risk, high-return investing. The Indian business philosophy of 'heads I win, tails I don't lose much.'",
    "Buy simple businesses in industries with slow change. Complexity = risk. Simplicity = predictability.",
    "Buy businesses with durable moats. The moat should be visible and understandable. If you can't explain the moat in one sentence, it's not strong enough.",
    "Buy at a discount to intrinsic value. Demand a 50% margin of safety. The wider the moat, the narrower the discount can be.",
    "Bet big on high-conviction ideas. Pabrai holds 10-15 stocks. 'Few bets, big bets, infrequent bets.' Kelly criterion thinking.",
    "Patience: wait for the fat pitch. Most of the time, do nothing. When the opportunity comes, swing hard.",
    "Learn from mistakes — especially others'. Read about failed businesses, frauds, blowups. Cheaper than making the mistakes yourself.",
])

_add("The Warren Buffett Way", "Robert Hagstrom", "Buffett", [
    "Buffett's 12 tenets: (1) understandable business, (2) consistent operating history, (3) favorable long-term prospects, (4) rational management, (5) candid management, (6) institutional imperative resistance, (7) focus on ROE, (8) owner earnings, (9) profit margins, (10) $1 test (retained earnings create >$1 of value), (11) economic goodwill, (12) margin of safety.",
    "Owner earnings = net income + depreciation - CapEx - working capital changes. Better than EPS or EBITDA. The true cash generated for owners.",
    "Economic goodwill vs accounting goodwill: economic goodwill = brand, moat, pricing power. Accounting goodwill = premium paid in acquisition. Buffett buys economic goodwill.",
    "The $1 test: for every $1 retained, does the company create >$1 in market value? If yes, management is allocating capital well. If no, they should pay dividends.",
    "Circle of competence: stay within it. Don't invest in tech if you don't understand tech. The size of the circle doesn't matter. Knowing its boundaries does.",
    "Mr. Market: the market is your servant, not your master. Take advantage of his moods. Buy when he's depressed, sell when he's euphoric.",
])

_add("The Education of a Value Investor", "Guy Spier", "Value", [
    "The environment matters: who you surround yourself with determines your behavior. Move to where value investors are. Avoid the noise of Wall Street.",
    "Slow down: the best decisions are made slowly. Don't react to news instantly. Wait 24 hours before acting on any impulse.",
    "Checklists: use them. Before buying: Is it understandable? Is there a moat? Is management honest? Is it cheap? Is there a margin of safety?",
    "Avoid the casino: don't check stock prices constantly. Price fluctuations create emotional reactions. Check weekly, not hourly.",
    "Your reputation is your most valuable asset. Protect it. Never compromise integrity for profit. The long-term cost of a damaged reputation > any short-term gain.",
    "Invest in yourself: the best investment is in your own education. Read, learn, improve. Your earning power is your biggest asset.",
])

_add("The Big Short", "Michael Lewis", "2008 Crisis", [
    "Michael Burry: the doctor who saw the subprime crisis coming. Analyzed individual mortgage loans. Found that borrowers couldn't repay. Bet against CDOs.",
    "The credit default swap: Burry's instrument. Insurance against mortgage bonds defaulting. Paid 100:1 when the bonds collapsed.",
    "The system was rigged: rating agencies gave AAA to junk. Banks didn't care because they sold the bonds. Regulators didn't understand the products.",
    "The importance of independent research: Wall Street analysts missed it. Burry read the actual loan documents. The truth was in the data, not in the consensus.",
    "The emotional cost: being early = being wrong for a long time. Burry's investors wanted to pull money. He had to lock them in. Conviction is painful.",
    "The lesson: when everyone agrees, something is wrong. The best trades are the most uncomfortable. If it feels easy, you're probably wrong.",
])

_add("Boomerang", "Michael Lewis", "European Debt Crisis", [
    "Iceland: fishermen became bankers. Borrowed in foreign currency. When the króna collapsed, the banks collapsed. The country went bankrupt.",
    "Greece: the government lied about its deficit. Goldman Sachs helped hide the debt with currency swaps. When the truth came out, the crisis began.",
    "Ireland: the government guaranteed all bank debt. The banks were insolvent. The taxpayer took the loss. Ireland's debt tripled overnight.",
    "Germany: the disciplined ones. They profited by lending to the undisciplined (Greece, Ireland). When the debt went bad, German banks were exposed.",
    "The lesson: debt doesn't disappear. It just moves. From banks to governments to taxpayers to the next generation. Until someone takes the loss.",
])

_add("The Undoing Project", "Michael Lewis", "Behavioral Finance", [
    "Kahneman and Tversky: the partnership that created behavioral economics. Prospect theory, loss aversion, framing effects.",
    "Prospect theory: humans don't evaluate outcomes rationally. We weight losses 2x more than gains. We overweight small probabilities. We're risk-seeking for losses, risk-averse for gains.",
    "The representativeness heuristic: we judge probability by similarity. 'This stock looks like a winner' = representativeness. But similarity ≠ probability.",
    "The availability heuristic: we judge frequency by ease of recall. Vivid events (crashes) seem more likely than they are. Boring events (slow grinding) seem less likely.",
    "Anchoring and adjustment: we start from an anchor (entry price) and adjust insufficiently. The market doesn't care about your anchor.",
    "The hot hand fallacy: we see patterns in random sequences. 'This stock is hot.' But past returns don't predict future returns (in the short term).",
])

_add("Adaptive Markets", "Andrew Lo", "Market Theory", [
    "The adaptive markets hypothesis: markets are not always efficient, but they adapt. Like evolution, strategies that work proliferate, then become crowded, then stop working.",
    "Efficiency is a spectrum, not a binary. Some markets are highly efficient (large-cap US equities). Others are less efficient (small-cap emerging markets, crypto).",
    "The evolutionary cycle: (1) new strategy discovered, (2) profits attract capital, (3) capital crowds the trade, (4) edge disappears, (5) capital leaves, (6) new strategy discovered.",
    "Behavioral biases are not bugs — they're features. They evolved for survival in a different environment. In modern markets, they cause errors. But they're not going away.",
    "Risk preferences change: investors are more risk-averse after losses, more risk-seeking after gains. This creates momentum and mean reversion.",
    "The implication: don't rely on a single strategy. Diversify across strategies. Monitor for crowding. Adapt as markets evolve.",
])

_add("The Little Book That Still Beats the Market", "Joel Greenblatt", "Magic Formula", [
    "The Magic Formula: rank stocks by (1) earnings yield (EBIT/EV) and (2) return on capital (EBIT/(net working capital + net fixed assets)). Buy the top-ranked stocks. Rebalance annually.",
    "Why it works: it buys cheap stocks (high earnings yield) that are also high quality (high return on capital). Value + quality combo.",
    "Earnings yield > P/E: EV-based (not price-based). Adjusts for debt and cash. More accurate than P/E for comparing leveraged and unleveraged companies.",
    "Return on capital > ROE: uses EBIT and tangible capital (not equity). Adjusts for leverage and intangibles. More accurate measure of operational efficiency.",
    "The catch: the formula can underperform for 2-3 years at a time. Most investors can't stick with it through the underperformance. Discipline > intelligence.",
    "Diversify: hold 20-30 stocks from the formula. Individual stocks can blow up. The portfolio smooths it out.",
    "The lesson: simple, systematic, and disciplined beats complex, discretionary, and emotional. The magic formula is not magic — it's patience.",
])


# =========================================================================== #
#  Print stats
# =========================================================================== #
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  BOOK KNOWLEDGE DISTILLED")
    print(f"{'='*60}")
    print(f"Total books: {len(ALL_BOOK_KNOWLEDGE)}")
    total_principles = sum(len(b["principles"]) for b in ALL_BOOK_KNOWLEDGE)
    print(f"Total principles: {total_principles}")

    # By category
    cats = {}
    for b in ALL_BOOK_KNOWLEDGE:
        cats[b["category"]] = cats.get(b["category"], 0) + 1
    print(f"\nBy category:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:<30} {count:>3} books")

    # Sample
    print(f"\nSample entry:")
    b = ALL_BOOK_KNOWLEDGE[0]
    print(f"  Book: {b['book']}")
    print(f"  Author: {b['author']}")
    print(f"  Category: {b['category']}")
    print(f"  Principles: {len(b['principles'])}")
    print(f"  First principle: {b['principles'][0][:100]}...")
