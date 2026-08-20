"""
knowledge_base.py - RAG knowledge base distilled from professional trading literature.

This module contains a curated database of trading rules, principles, and
patterns distilled from the books recommended by professional traders:

  Market Structure:
    - "Trading and Exchanges" by Larry Harris (market microstructure)
    - "Market Wizards" by Jack Schwager (interviews with top traders)
    - "Reminiscences of a Stock Operator" (Jesse Livermore's principles)

  Quantitative Trading:
    - "Advances in Financial Machine Learning" by Marcos López de Prado
    - "Quantitative Trading" by Ernest Chan

  Portfolio Management:
    - "Active Portfolio Management" by Grinold & Kahn
    - "The Intelligent Investor" by Benjamin Graham

  Options:
    - "Option Volatility & Pricing" by Sheldon Natenberg
    - "Volatility Trading" by Euan Sinclair

  Psychology:
    - "Trading in the Zone" by Mark Douglas
    - "The Daily Trading Coach" by Ari Kiev

Each entry is a RULE (not a quote) — a distilled, actionable principle that
the AI agents can retrieve and apply. This is educational fair use: the rules
are paraphrased principles, not copyrighted text.

The knowledge base is searched by keyword/score using a simple TF-IDF-like
relevance ranking. For production, upgrade to a vector DB (FAISS, Chroma).
"""
from __future__ import annotations

import re
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KnowledgeEntry:
    """A single trading rule or principle."""
    id: int
    rule: str                          # the distilled principle
    source: str                        # book title + author
    category: str                      # "market_structure", "quant", "risk", etc.
    keywords: list[str]                # for retrieval
    applies_to: str                    # "bullish", "bearish", "neutral", "all"


# =========================================================================== #
#  The Knowledge Base (100+ distilled rules from professional literature)
# =========================================================================== #
ENTRIES: list[KnowledgeEntry] = [
    # === MARKET STRUCTURE (Larry Harris, Market Wizards, Livermore) ======== #
    KnowledgeEntry(1,
        "The trend is your friend. Never fight the primary trend. If the market is in a downtrend, the odds of a long position working are severely diminished regardless of how good the individual stock looks.",
        "Reminiscences of a Stock Operator - Jesse Livermore",
        "market_structure", ["trend", "downtrend", "uptrend", "primary", "fight", "counter"], "all"),
    KnowledgeEntry(2,
        "Markets are driven by the actions of informed traders, liquidity seekers, and noise traders. Identify which group is dominant before committing capital.",
        "Trading and Exchanges - Larry Harris",
        "market_structure", ["informed", "liquidity", "noise", "dominant", "trader"], "all"),
    KnowledgeEntry(3,
        "Volume precedes price. A breakout without volume is suspect. Volume confirms conviction; lack of volume signals a fake-out.",
        "Market Wizards - Jack Schwager",
        "market_structure", ["volume", "breakout", "confirm", "fake", "conviction"], "all"),
    KnowledgeEntry(4,
        "Support and resistance are zones, not lines. The more times a level is tested, the weaker it becomes. The third test of a support level is more likely to break than the first.",
        "The Art and Science of Technical Analysis - Adam Grimes",
        "market_structure", ["support", "resistance", "zone", "tested", "break", "level"], "all"),
    KnowledgeEntry(5,
        "Gaps are significant. A gap-up on high volume that holds above the gap is bullish. A gap-up that fills is a trap. Gap-downs that fill are recovery; those that don't are distribution.",
        "Reminiscences of a Stock Operator - Jesse Livermore",
        "market_structure", ["gap", "gap-up", "gap-down", "fill", "hold", "distribution"], "all"),

    # === QUANTITATIVE TRADING (López de Prado, Chan) ====================== #
    KnowledgeEntry(6,
        "Backtests overstate live returns. The more parameters a strategy has, the more likely it is overfit. Prefer strategies with fewer rules that work across many instruments.",
        "Advances in Financial Machine Learning - Marcos López de Prado",
        "quant", ["backtest", "overfit", "parameter", "overstate", "strategy"], "all"),
    KnowledgeEntry(7,
        "Cross-validation on time series must respect temporal order. Never shuffle time series data — use walk-forward or purged k-fold to avoid look-ahead bias.",
        "Advances in Financial Machine Learning - Marcos López de Prado",
        "quant", ["cross-validation", "time series", "look-ahead", "walk-forward", "shuffle"], "all"),
    KnowledgeEntry(8,
        "Momentum works. Assets that have outperformed over 3-12 months tend to continue outperforming. The edge is small but persistent across markets and decades.",
        "Quantitative Trading - Ernest Chan",
        "quant", ["momentum", "outperform", "3-month", "12-month", "persistent"], "bullish"),
    KnowledgeEntry(9,
        "Mean reversion works on short timeframes (1-5 days) for liquid stocks. RSI below 10 or Z-score below -2 often precedes a bounce. Exit on return to mean, not on a target.",
        "Quantitative Trading - Ernest Chan",
        "quant", ["mean reversion", "rsi", "z-score", "bounce", "short", "liquid"], "bullish"),
    KnowledgeEntry(10,
        "Sharpe ratio above 2.0 with a backtest is a red flag. Real strategies rarely exceed 1.5. If your backtest shows 3.0+, you almost certainly have a data error or look-ahead bias.",
        "Advances in Financial Machine Learning - Marcos López de Prado",
        "quant", ["sharpe", "backtest", "red flag", "data error", "look-ahead"], "all"),
    KnowledgeEntry(11,
        "Position sizing matters more than entry timing. A strategy with 40% win rate and 2.5:1 reward/risk is more profitable than one with 70% win rate and 1:1.",
        "Quantitative Trading - Ernest Chan",
        "risk", ["position sizing", "win rate", "reward", "risk", "profitable"], "all"),

    # === PORTFOLIO MANAGEMENT (Grinold & Kahn, Graham) ==================== #
    KnowledgeEntry(12,
        "The Information Ratio (IR) = expected active return / tracking error. A good active manager achieves IR of 0.5-1.0. Above 1.0 is exceptional.",
        "Active Portfolio Management - Grinold & Kahn",
        "portfolio", ["information ratio", "active return", "tracking error", "manager"], "all"),
    KnowledgeEntry(13,
        "Diversification across uncorrelated strategies reduces risk more than diversification across correlated stocks. Hold strategies, not just stocks.",
        "Active Portfolio Management - Grinold & Kahn",
        "portfolio", ["diversification", "uncorrelated", "strategy", "risk", "correlated"], "all"),
    KnowledgeEntry(14,
        "Margin of safety: buy when price is significantly below intrinsic value. A 30%+ discount provides a buffer against analytical error and bad luck.",
        "The Intelligent Investor - Benjamin Graham",
        "portfolio", ["margin of safety", "intrinsic value", "discount", "buffer", "fundamental"], "bullish"),
    KnowledgeEntry(15,
        "Mr. Market is bipolar. Some days he's euphoric, some days depressed. Take advantage of his mood swings — sell to him when euphoric, buy from him when depressed.",
        "The Intelligent Investor - Benjamin Graham",
        "psychology", ["mr market", "bipolar", "euphoric", "depressed", "mood", "swing"], "all"),

    # === OPTIONS (Natenberg, Sinclair) ==================================== #
    KnowledgeEntry(16,
        "Implied volatility is the only unknown in options pricing. When IV is above historical volatility, options are 'expensive' — consider selling. When IV is below HV, options are 'cheap' — consider buying.",
        "Option Volatility & Pricing - Sheldon Natenberg",
        "options", ["implied volatility", "iv", "historical", "hv", "expensive", "cheap", "sell", "buy"], "all"),
    KnowledgeEntry(17,
        "Put/Call Ratio above 1.3 indicates excessive bearishness — a contrarian bullish signal. Below 0.7 indicates excessive bullishness — a contrarian bearish signal.",
        "Volatility Trading - Euan Sinclair",
        "options", ["put call", "pcr", "ratio", "contrarian", "bearish", "bullish", "excessive"], "all"),
    KnowledgeEntry(18,
        "Long buildup: price rises + OI rises = new long positions being built (bullish). Short buildup: price falls + OI rises = new short positions (bearish). Short covering: price rises + OI falls (bullish). Long unwinding: price falls + OI falls (bearish).",
        "Option Volatility & Pricing - Sheldon Natenberg",
        "options", ["long buildup", "short buildup", "short covering", "long unwinding", "oi", "open interest"], "all"),
    KnowledgeEntry(19,
        "Max pain: the strike price at which the total value of options is minimized for holders. Price tends to gravitate toward max pain on expiry day, especially in the last hour.",
        "Volatility Trading - Euan Sinclair",
        "options", ["max pain", "expiry", "strike", "gravitate", "expiry day"], "all"),

    # === RISK MANAGEMENT (universal across all books) ===================== #
    KnowledgeEntry(20,
        "Never risk more than 1-2% of capital on a single trade. With 1% risk, you can lose 20 trades in a row and still have 80% of your capital. Survival comes first.",
        "Market Wizards - Jack Schwager",
        "risk", ["risk", "1%", "2%", "capital", "survival", "single trade"], "all"),
    KnowledgeEntry(21,
        "Cut losses short, let profits run. The asymmetric payoff (small losses, large gains) is what makes trend-following profitable despite low win rates.",
        "Reminiscences of a Stock Operator - Jesse Livermore",
        "risk", ["cut losses", "let profits run", "asymmetric", "trend-following", "payoff"], "all"),
    KnowledgeEntry(22,
        "Risk/Reward must be at least 1:2. If you risk ₹100, your target must be at least ₹200. This ensures you're profitable even with a 40% win rate.",
        "Market Wizards - Jack Schwager",
        "risk", ["risk reward", "1:2", "target", "profitable", "win rate"], "all"),
    KnowledgeEntry(23,
        "The stop-loss is not optional. Every trade must have a predefined exit before entry. Moving a stop-loss further away to avoid being stopped out is the #1 way traders blow up accounts.",
        "Trading in the Zone - Mark Douglas",
        "risk", ["stop-loss", "stop", "exit", "predefined", "blow up", "moving"], "all"),
    KnowledgeEntry(24,
        "Volatility-based position sizing beats fixed-share sizing. Use ATR to set stop distance, then size the position so a stop-out costs exactly your risk budget (1% of capital).",
        "Advances in Financial Machine Learning - Marcos López de Prado",
        "risk", ["volatility", "position sizing", "atr", "stop distance", "risk budget"], "all"),

    # === PSYCHOLOGY (Douglas, Kiev) ======================================= #
    KnowledgeEntry(25,
        "Think in probabilities, not certainties. No single trade matters. What matters is the series of trades executed consistently according to your edge.",
        "Trading in the Zone - Mark Douglas",
        "psychology", ["probability", "certainty", "series", "edge", "consistent"], "all"),
    KnowledgeEntry(26,
        "Accept the risk before entering. If you haven't fully accepted that this trade can lose, you will hesitate to cut the loss when it comes. Pre-acceptance enables decisive action.",
        "Trading in the Zone - Mark Douglas",
        "psychology", ["accept", "risk", "hesitate", "cut loss", "pre-acceptance", "decisive"], "all"),
    KnowledgeEntry(27,
        "Revenge trading after a loss is the most destructive behavior. The market doesn't know you lost. It doesn't owe you anything. Each trade is independent.",
        "The Daily Trading Coach - Ari Kiev",
        "psychology", ["revenge", "loss", "destructive", "independent", "market"], "all"),
    KnowledgeEntry(28,
        "Your worst enemy is not the market; it's your own emotions. Fear makes you exit winners too early. Greed makes you hold losers too long. Discipline is the antidote.",
        "Trading in the Zone - Mark Douglas",
        "psychology", ["enemy", "emotion", "fear", "greed", "discipline", "winner", "loser"], "all"),

    # === INDIAN MARKET SPECIFICS (distilled from practice) ================ #
    KnowledgeEntry(29,
        "Indian stocks gap. Overnight positions face gap risk. Size positions assuming the stop will slip by 0.25 ATR on a gap-down. Plan for worst-case fill, not nominal stop.",
        "Indian market practice",
        "risk", ["gap", "overnight", "indian", "slip", "gap-down", "worst-case"], "all"),
    KnowledgeEntry(30,
        "NSE cash segment has no overnight short selling. A swing 'short' signal means 'avoid longs' or use futures/options. Don't try to short in delivery.",
        "Indian market practice",
        "market_structure", ["short", "nse", "cash", "delivery", "overnight", "futures"], "bearish"),
    KnowledgeEntry(31,
        "FII (Foreign Institutional Investor) flows drive Indian markets. When FIIs are net buyers for 3+ consecutive days, the market tends to rise. Sustained FII selling precedes corrections.",
        "Indian market practice",
        "institutional", ["fii", "foreign", "institutional", "buyer", "seller", "correction"], "all"),
    KnowledgeEntry(32,
        "Delivery percentage above 60% with above-average volume indicates genuine accumulation (investors buying to hold). Below 35% with high volume indicates intraday speculation or distribution.",
        "Indian market practice",
        "institutional", ["delivery", "percentage", "accumulation", "distribution", "volume", "intraday"], "all"),
    KnowledgeEntry(33,
        "Turn of the month effect in India: SIP flows from salary credits push indices up in the first 3-5 trading days of each month. This is a persistent seasonal edge.",
        "Indian market practice",
        "seasonal", ["turn of month", "sip", "salary", "seasonal", "first", "edge"], "bullish"),
    KnowledgeEntry(34,
        "Sector rotation: when a sector index outperforms NIFTY by 5%+ over 1 month, stocks in that sector tend to continue outperforming. Lead sectors often lead by 2-3 months.",
        "Zerodha Varsity - Top-down vs Bottom-up",
        "market_structure", ["sector", "rotation", "outperform", "nifty", "lead"], "all"),

    # === ADDITIONAL QUANT RULES =========================================== #
    KnowledgeEntry(35,
        "Earnings announcement drift: stocks that beat earnings expectations tend to continue drifting upward for 30-60 days. Those that miss drift downward. The drift is the edge.",
        "Quantitative finance research",
        "quant", ["earnings", "beat", "miss", "drift", "expectation", "30-day"], "all"),
    KnowledgeEntry(36,
        "Pairs trading: when two historically correlated stocks diverge, short the outperformer and buy the underperformer. Profit when they reconverge. Edge comes from cointegration, not correlation.",
        "Advances in Financial Machine Learning - López de Prado",
        "quant", ["pairs", "cointegration", "correlation", "diverge", "reconverge", "short", "buy"], "all"),
    KnowledgeEntry(37,
        "Volatility clustering: high volatility today predicts high volatility tomorrow. Use this for options selling — after a spike, IV is elevated and tends to mean-revert.",
        "Volatility Trading - Euan Sinclair",
        "options", ["volatility", "clustering", "spike", "elevated", "mean-revert", "iv"], "all"),
    KnowledgeEntry(38,
        "Drawdown control: if portfolio drawdown exceeds 10%, halve all position sizes until equity recovers to a new high. This prevents a 10% drawdown from becoming a 30% one.",
        "Advances in Financial Machine Learning - López de Prado",
        "risk", ["drawdown", "control", "halve", "position size", "recover", "equity"], "all"),
    KnowledgeEntry(39,
        "Correlation between positions matters. Two 'TAKE' signals on correlated stocks (e.g., HDFCBANK and ICICIBANK) is effectively one bet. Count unique bets, not positions.",
        "Active Portfolio Management - Grinold & Kahn",
        "portfolio", ["correlation", "correlated", "position", "unique", "bet", "count"], "all"),
    KnowledgeEntry(40,
        "Regime detection first, strategy second. A momentum strategy fails in ranging markets. A mean-reversion strategy fails in trending markets. Always check the regime before deploying a strategy.",
        "Advances in Financial Machine Learning - López de Prado",
        "market_structure", ["regime", "momentum", "mean reversion", "ranging", "trending", "check"], "all"),

    # === TIER 1: BERKSHIRE HATHAWAY LETTERS (Warren Buffett) ============== #
    KnowledgeEntry(41,
        "Price is what you pay, value is what you get. Focus on intrinsic value, not market price. The market is a voting machine in the short run, a weighing machine in the long run.",
        "Berkshire Hathaway Letters - Warren Buffett",
        "value_investing", ["price", "value", "intrinsic", "market", "voting", "weighing"], "all"),
    KnowledgeEntry(42,
        "Be fearful when others are greedy, greedy when others are fearful. Sentiment extremes mark turning points. Buy when blood is in the streets (metaphorically).",
        "Berkshire Hathaway Letters - Warren Buffett",
        "contrarian", ["fearful", "greedy", "sentiment", "extreme", "contrarian", "blood"], "all"),
    KnowledgeEntry(43,
        "Our favorite holding period is forever. Quality businesses compound over decades. Frequent trading incurs taxes, fees, and decision fatigue. Trade less, hold longer.",
        "Berkshire Hathaway Letters - Warren Buffett",
        "portfolio", ["holding period", "forever", "quality", "compound", "trade less", "hold"], "bullish"),
    KnowledgeEntry(44,
        "Risk comes from not knowing what you're doing. Understand the business model, competitive moat, and management before investing. If you can't explain it in one sentence, don't buy it.",
        "Berkshire Hathaway Letters - Warren Buffett",
        "fundamental", ["risk", "knowing", "business model", "moat", "management", "understand"], "all"),
    KnowledgeEntry(45,
        "Diversification is protection against ignorance. It makes little sense if you know what you're doing. Concentrate in your best ideas, but cap single-stock risk at 25% of capital.",
        "Berkshire Hathaway Letters - Warren Buffett",
        "portfolio", ["diversification", "ignorance", "concentrate", "best ideas", "cap"], "all"),
    KnowledgeEntry(46,
        "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price. Quality compounds; cheap deteriorates. Pay up for moats.",
        "Berkshire Hathaway Letters - Warren Buffett",
        "value_investing", ["wonderful company", "fair price", "quality", "moat", "compound", "cheap"], "bullish"),
    KnowledgeEntry(47,
        "Accounting is the language of business. Read financial statements before price charts. If the balance sheet is deteriorating, no indicator pattern will save you.",
        "Berkshire Hathaway Letters - Warren Buffett",
        "fundamental", ["accounting", "financial statements", "balance sheet", "read", "fundamental"], "all"),
    KnowledgeEntry(48,
        "Capital allocation is the CEO's most important job. Watch what management does with cash: reinvest, buyback, dividend, or acquisitions. Buybacks below intrinsic value create value; above destroy it.",
        "Berkshire Hathaway Letters - Warren Buffett",
        "fundamental", ["capital allocation", "ceo", "cash", "reinvest", "buyback", "dividend", "acquisition"], "all"),

    # === TIER 1: HOWARD MARKS MEMOS ====================================== #
    KnowledgeEntry(49,
        "You can't predict the future, but you can prepare for it. Risk is not volatility — it's the probability of permanent loss. Most 'risk models' measure the wrong thing.",
        "Howard Marks Memos - Oaktree",
        "risk", ["predict", "prepare", "risk", "volatility", "permanent loss", "model"], "all"),
    KnowledgeEntry(50,
        "Markets are cyclical. Trees don't grow to the sky, and things don't go to zero. When everyone says 'this time is different,' it almost never is. Mean reversion is gravity.",
        "Howard Marks Memos - Oaktree",
        "cycles", ["cyclical", "trees", "sky", "zero", "this time is different", "mean reversion", "gravity"], "all"),
    KnowledgeEntry(51,
        "Second-level thinking: 'It's a good company, but everyone thinks it's a great company — so it's overpriced.' First-level thinks only about quality; second-level thinks about expectations vs reality.",
        "Howard Marks Memos - Oaktree",
        "psychology", ["second-level", "expectations", "reality", "overpriced", "thinking"], "all"),
    KnowledgeEntry(52,
        "The most profitable thing is to buy when others are panicking. The most dangerous thing is to buy when others are euphoric. Market sentiment is a contrarian indicator at extremes.",
        "Howard Marks Memos - Oaktree",
        "contrarian", ["panicking", "euphoric", "contrarian", "sentiment", "extreme"], "all"),
    KnowledgeEntry(53,
        "Risk control is not about avoiding risk — it's about avoiding losses you can't recover from. Asymmetric risk: never risk 100% to make 20%. Risk 1% to make 3%.",
        "Howard Marks Memos - Oaktree",
        "risk", ["risk control", "avoiding", "losses", "recover", "asymmetric", "1%"], "all"),
    KnowledgeEntry(54,
        "Being too far ahead of your time is indistinguishable from being wrong. Even a correct thesis can take years to play out. Have enough capital to survive until you're proven right.",
        "Howard Marks Memos - Oaktree",
        "risk", ["ahead", "time", "wrong", "thesis", "years", "capital", "survive"], "all"),

    # === TIER 1: RAY DALIO PRINCIPLES ==================================== #
    KnowledgeEntry(55,
        "Pain + Reflection = Progress. Every losing trade is a data point. After a loss, ask: was the thesis wrong, or the execution? Don't blame the market — improve the process.",
        "Principles - Ray Dalio",
        "psychology", ["pain", "reflection", "progress", "loss", "thesis", "execution", "process"], "all"),
    KnowledgeEntry(56,
        "All economic activity is driven by productivity growth, the short-term debt cycle (5-8 years), and the long-term debt cycle (50-75 years). Understanding which cycle you're in determines asset allocation.",
        "Principles - Ray Dalio",
        "macro", ["economic", "productivity", "debt cycle", "short-term", "long-term", "asset allocation"], "all"),
    KnowledgeEntry(57,
        "Diversify across uncorrelated return streams, not just asset classes. 15-20 uncorrelated bets can reduce risk by 80% without reducing return. This is the Holy Grail of investing.",
        "Principles - Ray Dalio",
        "portfolio", ["diversify", "uncorrelated", "return streams", "asset class", "15", "20", "holy grail"], "all"),
    KnowledgeEntry(58,
        "Don't trust your gut — trust the process. Build decision-making systems that aggregate data, not emotions. The best investors are systematic, not intuitive.",
        "Principles - Ray Dalio",
        "psychology", ["gut", "process", "decision", "system", "data", "emotion", "systematic"], "all"),

    # === TIER 2: DAMODARAN VALUATION ===================================== #
    KnowledgeEntry(59,
        "Intrinsic value = discounted cash flows. Every asset's value is the present value of its future cash flows. If you can't forecast cash flows, you can't value the company.",
        "Aswath Damodaran - NYU Stern",
        "valuation", ["intrinsic", "discounted", "cash flow", "present value", "forecast", "value"], "all"),
    KnowledgeEntry(60,
        "Growth is valuable only if it generates excess returns (ROIC > cost of capital). Companies growing at 20% with 8% ROIC destroy value. Check ROIC, not just growth rate.",
        "Aswath Damodaran - NYU Stern",
        "fundamental", ["growth", "excess return", "roic", "cost of capital", "destroy", "value"], "all"),
    KnowledgeEntry(61,
        "P/E ratio is meaningless without context. A P/E of 40 with 30% growth is cheap; a P/E of 10 with declining earnings is expensive. Always use PEG ratio or forward P/E.",
        "Aswath Damodaran - NYU Stern",
        "valuation", ["p/e", "pe", "context", "growth", "peg", "forward", "cheap", "expensive"], "all"),
    KnowledgeEntry(62,
        "Beta does not measure risk. A stock with low beta can be risky (leverage, fundamentals). A stock with high beta can be safe (volatility from liquidity, not fundamental risk).",
        "Aswath Damodaran - NYU Stern",
        "risk", ["beta", "risk", "leverage", "liquidity", "fundamental"], "all"),
    KnowledgeEntry(63,
        "Margin of safety = intrinsic value - market price. For equities, demand at least 25% margin of safety. For distressed assets, 50%+. The bigger the uncertainty, the bigger the margin.",
        "Aswath Damodaran - NYU Stern",
        "valuation", ["margin of safety", "intrinsic", "market", "25%", "50%", "uncertainty"], "bullish"),

    # === TIER 3: QUANTPEDIA STRATEGIES =================================== #
    KnowledgeEntry(64,
        "12-1 momentum: buy the top 20% of stocks by 12-month return (excluding the most recent month). Rebalance monthly. Captures persistent momentum while avoiding short-term reversal.",
        "Quantpedia - 12-1 Momentum",
        "quant", ["momentum", "12-month", "rebalance", "monthly", "reversal", "top 20"], "bullish"),
    KnowledgeEntry(65,
        "Earnings revision momentum: analysts revise estimates upward before they revise ratings. Track estimate revisions, not ratings. 3+ upward revisions in 30 days is a strong signal.",
        "Quantpedia - Earnings Revisions",
        "quant", ["earnings", "revision", "analyst", "estimate", "rating", "3+", "30 days"], "bullish"),
    KnowledgeEntry(66,
        "Low volatility anomaly: low-beta stocks outperform high-beta stocks on a risk-adjusted basis. Bet against beta — long low-vol, short high-vol. This contradicts the CAPM.",
        "Quantpedia - Betting Against Beta",
        "quant", ["low volatility", "anomaly", "beta", "risk-adjusted", "capm", "betting against beta"], "all"),
    KnowledgeEntry(67,
        "Quality factor (gross profitability): companies with high gross profitability (gross profit / assets) outperform. Buy the top 30% by this metric, rebalance annually.",
        "Quantpedia - Quality Factor",
        "fundamental", ["quality", "gross profitability", "gross profit", "assets", "top 30", "annual"], "bullish"),
    KnowledgeEntry(68,
        "Seasonality: November-April is historically the strongest 6-month period for equities ('Sell in May and go away'). For India, the Diwali to Holi period (Nov-Mar) tends to be strong.",
        "Quantpedia - Seasonality",
        "seasonal", ["seasonality", "november", "april", "sell in may", "diwali", "holi", "india"], "bullish"),
    KnowledgeEntry(69,
        "Accrual anomaly: companies with high accruals (earnings not backed by cash flow) underperform. Cash flow is harder to manipulate than earnings. Always check CFO/net income ratio.",
        "Quantpedia - Accrual Anomaly",
        "fundamental", ["accrual", "cash flow", "cfo", "net income", "manipulate", "underperform"], "all"),
    KnowledgeEntry(70,
        "Net stock issues: companies that buy back shares (negative net issuance) outperform those that issue shares. Share count change is a powerful signal. Look for decreasing share count YoY.",
        "Quantpedia - Net Stock Issues",
        "fundamental", ["buyback", "issuance", "share count", "decreasing", "net stock"], "bullish"),

    # === TIER 4: MARKET MICROSTRUCTURE =================================== #
    KnowledgeEntry(71,
        "The bid-ask spread is a hidden tax. For high-frequency strategies, spread cost can exceed 50% of gross P&L. Trade liquid stocks (avg daily volume > 10cr) to minimize spread impact.",
        "Trading and Exchanges - Larry Harris",
        "microstructure", ["bid-ask", "spread", "hidden tax", "high-frequency", "liquid", "volume"], "all"),
    KnowledgeEntry(72,
        "Market impact scales with sqrt(order size / ADV). A trade worth 1% of ADV moves price ~0.1%. A trade worth 10% moves price ~0.3%. Size positions to stay under 1% ADV for minimal impact.",
        "Market Microstructure Theory - O'Hara",
        "microstructure", ["market impact", "sqrt", "adv", "order size", "liquid"], "all"),
    KnowledgeEntry(73,
        "Informed traders prefer limit orders (hide their information). Liquidity traders use market orders (need immediate execution). A surge in limit orders at a level often precedes a move.",
        "Trading and Exchanges - Larry Harris",
        "microstructure", ["informed", "limit order", "liquidity", "market order", "execution", "surge"], "all"),
    KnowledgeEntry(74,
        "Order flow imbalance (OFI) predicts short-term price moves. If buy-side volume exceeds sell-side by 2x for 15+ minutes, price tends to continue in that direction for the next hour.",
        "Algorithmic Trading and DMA - Johnson",
        "microstructure", ["order flow", "imbalance", "ofi", "buy-side", "sell-side", "15 minutes", "predict"], "all"),
    KnowledgeEntry(75,
        "Liquidity cascades: when one large order triggers stop-losses, which trigger more stops, price overshoots. These 'liquidity vacuums' are buying/selling opportunities — the snap-back is fast.",
        "Market Microstructure Theory - O'Hara",
        "microstructure", ["liquidity", "cascade", "stop-loss", "overshoot", "vacuum", "snap-back"], "all"),

    # === TIER 5: EARNINGS CALL ANALYSIS ================================== #
    KnowledgeEntry(76,
        "Management tone analysis: count positive vs negative words in the earnings call Q&A. A 3:1 positive ratio in the Q&A (not the prepared remarks) predicts positive returns for 30 days.",
        "Earnings call research - academic",
        "earnings", ["management tone", "earnings call", "qa", "positive", "negative", "30 days", "predict"], "bullish"),
    KnowledgeEntry(77,
        "Guidance changes matter more than earnings beats. A company that beats by 5% but lowers guidance drops 10%+. A company that misses by 2% but raises guidance rises 8%+. Track guidance.",
        "Earnings call research - academic",
        "earnings", ["guidance", "beat", "miss", "raise", "lower", "drop", "rise"], "all"),
    KnowledgeEntry(78,
        "Listen for hedging language in the Q&A: 'we'll see,' 'challenging,' 'headwinds,' 'cautiously optimistic.' These phrases often precede guidance cuts within 1-2 quarters.",
        "Earnings call research - academic",
        "earnings", ["hedging", "challenging", "headwinds", "cautiously", "guidance cut", "quarter"], "bearish"),
    KnowledgeEntry(79,
        "Analyst question depth signals interest. If top-tier analysts (Goldman, Morgan Stanley) ask detailed operational questions, they're building models — often precedes upgrade. If they ask generic questions, they've moved on.",
        "Earnings call research - academic",
        "earnings", ["analyst", "question", "depth", "goldman", "morgan stanley", "upgrade", "model"], "bullish"),

    # === TIER 6: SEC/FILINGS ANALYSIS ==================================== #
    KnowledgeEntry(80,
        "Insider buying is bullish; insider selling is noisy. Three or more insiders buying in the open market within 30 days is a strong signal. CEOs buying with personal funds (not options) is the strongest.",
        "SEC insider filing research",
        "filings", ["insider", "buying", "selling", "ceo", "personal", "30 days", "open market"], "bullish"),
    KnowledgeEntry(81,
        "10-K risk factors: when a company adds NEW risk factors (especially 'going concern,' 'material weakness,' 'cybersecurity'), it's a red flag. Compare this year's risk section to last year's.",
        "SEC 10-K analysis",
        "filings", ["10-k", "risk factor", "new", "going concern", "material weakness", "cybersecurity", "red flag"], "bearish"),
    KnowledgeEntry(82,
        "Footnotes hide the truth. Revenue recognition changes, off-balance-sheet entities, and related-party transactions are buried in footnotes. Read them before investing.",
        "SEC filing analysis",
        "filings", ["footnote", "revenue recognition", "off-balance", "related party", "buried", "read"], "all"),
    KnowledgeEntry(83,
        "Audit opinion matters. 'Unqualified' is normal. 'Qualified' or 'adverse' means the auditor disagrees with management — a massive red flag. Watch for auditor changes (often signal problems).",
        "SEC filing analysis",
        "filings", ["audit", "unqualified", "qualified", "adverse", "auditor", "change", "red flag"], "bearish"),

    # === TIER 7: ALTERNATIVE DATA ======================================== #
    KnowledgeEntry(84,
        "Google Trends for branded search: rising search volume for a company's product name precedes revenue growth by 1-2 quarters. Falling search volume warns of demand decline.",
        "Alternative data research",
        "alt_data", ["google trends", "search", "branded", "revenue", "quarter", "demand"], "all"),
    KnowledgeEntry(85,
        "App download rankings: for consumer-tech companies, rising App Store/Play Store rankings predict user growth. Sensor Tower data can give you a 60-day edge on earnings.",
        "Alternative data research",
        "alt_data", ["app", "download", "ranking", "consumer", "user growth", "sensor tower", "60 day"], "bullish"),
    KnowledgeEntry(86,
        "Job postings: companies aggressively hiring (LinkedIn, Indeed) are usually growing. Sudden hiring freezes or layoffs (Glassdoor, LinkedIn) precede weak earnings by 1-2 quarters.",
        "Alternative data research",
        "alt_data", ["job", "posting", "hiring", "linkedin", "indeed", "layoff", "freeze", "quarter"], "all"),
    KnowledgeEntry(87,
        "Web traffic (Similarweb): declining unique visitors to a company's website often precedes revenue decline. For e-commerce, traffic + conversion rate = revenue. Track both.",
        "Alternative data research",
        "alt_data", ["web traffic", "similarweb", "visitor", "revenue", "e-commerce", "conversion"], "all"),

    # === TIER 9: ACADEMIC PAPERS ========================================= #
    KnowledgeEntry(88,
        "Fama-French 3-factor: market, size (small beats large), and value (high book-to-market beats low) explain most stock returns. Add momentum (Carhart) for a 4-factor model. Build portfolios tilted to these factors.",
        "Fama-French academic research",
        "factors", ["fama-french", "3-factor", "market", "size", "value", "book-to-market", "momentum", "carhart"], "all"),
    KnowledgeEntry(89,
        "Post-Earnings Announcement Drift (PEAD): stocks that beat earnings drift upward for 60 days; those that miss drift down. The drift is the edge — don't exit on day 1, hold for 30-60 days.",
        "PEAD academic research - Bernard & Thomas",
        "earnings", ["post-earnings", "drift", "pead", "beat", "miss", "60 days", "30 days", "edge"], "all"),
    KnowledgeEntry(90,
        "Statistical arbitrage: pairs trading works when two stocks are cointegrated (not just correlated). Test cointegration with the Engle-Granger test. Trade the spread when it exceeds 2 standard deviations.",
        "Statistical arbitrage research",
        "quant", ["statistical arbitrage", "pairs", "cointegration", "engle-granger", "spread", "standard deviation"], "all"),
    KnowledgeEntry(91,
        "Volatility forecasting: GARCH(1,1) models capture volatility clustering and outperform simple historical volatility. Use GARCH for option pricing and position sizing.",
        "Volatility forecasting research",
        "options", ["volatility", "garch", "clustering", "historical", "forecast", "option pricing"], "all"),
    KnowledgeEntry(92,
        "Reinforcement learning for trading: PPO and SAC algorithms outperform DQN for continuous action spaces (position sizing). Reward must be risk-adjusted (Sharpe), not absolute return.",
        "RL trading research - FinRL",
        "quant", ["reinforcement learning", "ppo", "sac", "dqn", "position sizing", "reward", "sharpe", "risk-adjusted"], "all"),
    KnowledgeEntry(93,
        "Regime-switching models: Hidden Markov Models (HMM) detect regime changes 2-3 bars earlier than ADX-based classifiers. Use HMM with 3-4 states (bull, bear, chop, volatile) for regime detection.",
        "Regime detection research",
        "market_structure", ["regime", "hmm", "hidden markov", "switching", "adx", "state", "bull", "bear"], "all"),
    KnowledgeEntry(94,
        "Lead-lag effect: small-cap stocks tend to lead large-cap stocks within the same sector. When a small-cap peer makes a sharp move, the sector large-cap often follows within 2-5 days.",
        "Lead-lag academic research",
        "market_structure", ["lead-lag", "small-cap", "large-cap", "sector", "peer", "2-5 days", "follow"], "all"),
    KnowledgeEntry(95,
        "Liquidity premium: illiquid stocks earn higher returns (compensation for liquidity risk). But this premium disappears in crises when liquidity dries up. Size positions inversely to illiquidity.",
        "Liquidity premium research",
        "risk", ["liquidity", "premium", "illiquid", "compensation", "crisis", "size", "inverse"], "all"),
    KnowledgeEntry(96,
        "Currency effect: for Indian IT stocks (TCS, INFY, WIPRO), a 1% INR depreciation vs USD adds ~0.5% to margins. Track USDINR — a falling rupee is bullish for IT exporters, bearish for importers (oil, chemicals).",
        "FX impact research",
        "macro", ["currency", "usdinr", "rupee", "depreciation", "it", "exporter", "importer", "oil"], "all"),
    KnowledgeEntry(97,
        "Crude oil correlation: Indian paint companies (Asian Paints, Berger) track crude with a 30-day lag (oil is 40% of raw material cost). Falling crude = margin expansion for paints.",
        "Commodity correlation research",
        "macro", ["crude", "oil", "paint", "asian paints", "berger", "lag", "raw material", "margin"], "all"),
    KnowledgeEntry(98,
        "Interest rate sensitivity: rate hikes hurt rate-sensitive sectors (real estate, autos, NBFCs) within 60 days. Rate cuts help them. Track RBI policy dates and position accordingly.",
        "Rate sensitivity research",
        "macro", ["interest rate", "hike", "cut", "real estate", "auto", "nbfc", "rbi", "60 days"], "all"),
    KnowledgeEntry(99,
        "FII flow correlation: NIFTY moves track FII net flows with 0.7 correlation. When FIIs sell 2000+ cr for 3 consecutive days, NIFTY tends to drop 2-3% within a week. Position defensively.",
        "FII flow research",
        "institutional", ["fii", "flow", "nifty", "correlation", "2000", "consecutive", "defensive"], "bearish"),
    KnowledgeEntry(100,
        "Delivery-based accumulation: track 10-day average delivery %. If it rises from 40% to 60%+ with price rising, smart money is accumulating. If delivery falls while price rises, it's speculative.",
        "Delivery analysis research",
        "institutional", ["delivery", "accumulation", "10-day", "average", "smart money", "speculative", "40%", "60%"], "all"),
]


# =========================================================================== #
#  Retrieval — TF-IDF weighted vector similarity (upgrade from keyword match)
# =========================================================================== #
# Build a simple TF-IDF index once at module load.
import math
from collections import Counter

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())

# Build document frequency for IDF
_ALL_DOCS = [_tokenize(e.rule + " " + " ".join(e.keywords)) for e in ENTRIES]
_N_DOCS = len(_ALL_DOCS)
_DF = Counter()
for doc in _ALL_DOCS:
    for word in set(doc):
        _DF[word] += 1

def _idf(word: str) -> float:
    df = _DF.get(word, 0)
    if df == 0:
        return 0
    return math.log((_N_DOCS + 1) / (df + 1)) + 1

def _tfidf_vector(text: str) -> dict[str, float]:
    toks = _tokenize(text)
    if not toks:
        return {}
    tf = Counter(toks)
    return {word: count * _idf(word) for word, count in tf.items()}

# Precompute entry vectors
_ENTRY_VECTORS = [_tfidf_vector(e.rule + " " + " ".join(e.keywords)) for e in ENTRIES]

def _cosine_sim(v1: dict, v2: dict) -> float:
    if not v1 or not v2:
        return 0
    dot = sum(v1.get(w, 0) * v2.get(w, 0) for w in v1 if w in v2)
    mag1 = math.sqrt(sum(x * x for x in v1.values()))
    mag2 = math.sqrt(sum(x * x for x in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0
    return dot / (mag1 * mag2)


def search(query: str, top_k: int = 5) -> list[dict]:
    """Search the knowledge base using TF-IDF cosine similarity.

    This is a proper vector-space retrieval (upgrade from keyword matching).
    For production, replace with FAISS + sentence embeddings.
    """
    query_vec = _tfidf_vector(query)
    if not query_vec:
        return []
    scored = []
    for i, entry_vec in enumerate(_ENTRY_VECTORS):
        score = _cosine_sim(query_vec, entry_vec)
        scored.append((ENTRIES[i], score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [
        {
            "id": entry.id,
            "rule": entry.rule,
            "source": entry.source,
            "category": entry.category,
            "applies_to": entry.applies_to,
            "relevance": round(score, 3),
        }
        for entry, score in scored[:top_k] if score > 0
    ]


def get_rules_for_context(verdict: str = "", direction: str = "",
                          regime: str = "", risk_reward: float = 0,
                          has_news: bool = False) -> list[dict]:
    """Get the most relevant rules for a specific trade context.

    This is what the Portfolio Manager agent calls before making its final
    decision — it retrieves the relevant wisdom from the knowledge base.
    """
    context_parts = []
    if direction:
        context_parts.append(direction)
    if regime:
        context_parts.append(regime)
        if "trend" in regime.lower():
            context_parts.append("momentum trend")
        if "rang" in regime.lower():
            context_parts.append("mean reversion ranging")
    if risk_reward > 0:
        context_parts.append(f"risk reward {risk_reward}")
    if has_news:
        context_parts.append("news earnings")
    context = " ".join(context_parts) if context_parts else "trading risk management"
    return search(context, top_k=8)


def get_stats() -> dict:
    """Return stats about the knowledge base."""
    categories = {}
    for e in ENTRIES:
        categories[e.category] = categories.get(e.category, 0) + 1
    return {
        "total_rules": len(ENTRIES),
        "categories": categories,
        "sources": len(set(e.source for e in ENTRIES)),
    }


if __name__ == "__main__":
    print(f"Knowledge base: {get_stats()}")
    print("\n--- Search: 'trend momentum breakout' ---")
    for r in search("trend momentum breakout", top_k=5):
        print(f"  [{r['relevance']:.2f}] {r['source']}")
        print(f"    {r['rule'][:120]}...")
    print("\n--- Search: 'risk stop loss position sizing' ---")
    for r in search("risk stop loss position sizing", top_k=5):
        print(f"  [{r['relevance']:.2f}] {r['source']}")
        print(f"    {r['rule'][:120]}...")
