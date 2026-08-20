"""
advisor
=======
A local, advisory-only AI trading assistant for the Indian market (NSE/BSE).

It analyses a stock and tells you what it sees: a direction, an entry, a
stop-loss, a target, a position size matched to your capital, the reward-to-risk,
a confidence score, the bull/base/bear scenarios, and the red signals to avoid a
bad trade. It NEVER places an order - you execute manually in your broker.

Quick start
-----------
    from advisor import Analyzer, Settings, Style

    settings = Settings(capital=100_000, risk_pct=0.01)
    agent = Analyzer(settings)
    idea = agent.analyze("RELIANCE", style=Style.SWING)
    print(idea.verdict, idea.confidence)
    print(idea.narration)

Honest expectations: no system is "90% profitable". The edge is positive
EXPECTANCY over many trades plus strict risk management. Treat "confidence" as a
probability estimate, never a promise. Validate with the backtester before
risking real money, and start with paper trades.

Project layout (refactored)
---------------------------
The package is now organized into five merged modules:

    core.py       - models + config + data sources (foundation layer)
    analysis.py   - indicators + regime + signals + risk (TA & money math)
    engine.py     - analyzer + backtest (the orchestrator)
    extras.py     - journal + news + llm (auxiliary enhancements)
    cli.py        - command-line interface and pretty-printer

This refactoring collapses the previous 14-file package into 5 cohesive files,
each ~300-700 lines, grouped by architectural concern rather than by individual
class. The public API (everything re-exported below) is unchanged.
"""
from __future__ import annotations

from .core import (
    Settings, load_settings, validate_settings,
    OHLCVSource, YFinanceSource, CSVSource, get_source, normalize_symbol, clean_frame,
    Direction, IndicatorSnapshot, PositionPlan, Regime, Scenario,
    Signal, Style, TradeIdea, Verdict, Veto,
)
from .analysis import (
    # indicators
    sma, ema, rsi, macd, true_range, atr, bollinger, adx, obv, vwap,
    compute_indicators, snapshot, resample_ohlc, higher_tf_trend,
    # regime
    RegimeRead, classify_regime,
    # signals
    swing_signals, intraday_signals, score_confluence,
    # risk
    atr_stop, structure_stop, choose_stop, target_for_rr,
    position_size, build_plan, build_scenarios, evaluate_vetoes,
    expectancy_r, breakeven_win_rate, kelly_fraction, fractional_kelly,
)
from .engine import (
    Analyzer,
    CostModel, BTTrade, BacktestResult,
    backtest_swing, run_backtest, _compute_stats, _gap_fill,
    _adjust_confidence, _decide_verdict, _BREAKOUT_SIGNALS,
    TAKE_FLOOR, WATCH_FLOOR, MIN_RAW_CONF_FOR_TAKE, MIN_SIGNALS_FOR_TAKE,
)
from .extras import (
    Journal,
    simple_sentiment, fetch_headlines, mentions, sentiment_for_symbol, market_sentiment,
    narrate, template_narration,
)

__version__ = "2.0.0"

__all__ = [
    # core
    "Settings", "load_settings", "validate_settings",
    "get_source", "OHLCVSource", "YFinanceSource", "CSVSource",
    "normalize_symbol", "clean_frame",
    "TradeIdea", "Style", "Direction", "Verdict", "Regime",
    "Signal", "Scenario", "PositionPlan", "Veto", "IndicatorSnapshot",
    # analysis
    "sma", "ema", "rsi", "macd", "true_range", "atr", "bollinger", "adx",
    "obv", "vwap", "compute_indicators", "snapshot", "resample_ohlc",
    "higher_tf_trend",
    "RegimeRead", "classify_regime",
    "swing_signals", "intraday_signals", "score_confluence",
    "atr_stop", "structure_stop", "choose_stop", "target_for_rr",
    "position_size", "build_plan", "build_scenarios", "evaluate_vetoes",
    "expectancy_r", "breakeven_win_rate", "kelly_fraction", "fractional_kelly",
    # engine
    "Analyzer",
    "CostModel", "BTTrade", "BacktestResult",
    "backtest_swing", "run_backtest",
    "TAKE_FLOOR", "WATCH_FLOOR", "MIN_RAW_CONF_FOR_TAKE", "MIN_SIGNALS_FOR_TAKE",
    # extras
    "Journal",
    "simple_sentiment", "fetch_headlines", "mentions", "sentiment_for_symbol",
    "market_sentiment", "narrate", "template_narration",
    "__version__",
]
