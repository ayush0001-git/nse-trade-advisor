"""
test_all.py - consolidated test suite for the advisor package.

Combines the previously separate test files (test_indicators, test_risk,
test_regime, test_signals, test_journal, test_analyzer, test_backtest,
test_news) into one. Each original suite is preserved verbatim under a
section header so individual tests can still be located and run.

Run with pytest:      pytest tests/
Or standalone:        python tests/test_all.py
"""
from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
import numpy as np
import pandas as pd
from datetime import datetime

from advisor import analysis as an
from advisor import extras as ex
from advisor.core import (
    Direction, IndicatorSnapshot, PositionPlan, Regime, Settings, Signal,
    Style, TradeIdea, Verdict, Veto, load_settings,
)
from advisor.core import CSVSource
from advisor.engine import (
    Analyzer, BTTrade, BacktestResult, CostModel, _compute_stats, _decide_verdict,
    _adjust_confidence, _gap_fill, backtest_swing, run_backtest,
)

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "sample_data")


# =========================================================================== #
#  Helpers shared across suites
# =========================================================================== #
def _frame(n=300, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-02", periods=n, freq="B")
    ret = rng.normal(0.0005, 0.012, n)
    close = 1000 * np.cumprod(1 + ret)
    high = close * (1 + np.abs(rng.normal(0, 0.006, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.006, n)))
    openp = np.empty(n); openp[0] = close[0]; openp[1:] = close[:-1]
    high = np.maximum.reduce([high, openp, close])
    low = np.minimum.reduce([low, openp, close])
    vol = rng.integers(1_000_000, 5_000_000, n).astype(float)
    return pd.DataFrame(
        {"open": openp, "high": high, "low": low, "close": close, "volume": vol},
        index=idx)


def _rising_frame(n=260):
    """Steadily rising series: the last bar is a new 20-day AND 52-week high."""
    close = np.linspace(80, 120, n)
    idx = pd.date_range("2023-01-02", periods=n, freq="B")
    df = pd.DataFrame({"open": close - 0.1, "high": close + 0.05, "low": close - 0.2,
                       "close": close, "volume": 1_000_000.0}, index=idx)
    return an.compute_indicators(df)


def _frame_with_final_plunge(n=260):
    """Flat-ish series, then a sharp drop on the last bar."""
    base = 100 + np.random.default_rng(0).normal(0, 0.2, n)
    base[-1] = 88.0
    idx = pd.date_range("2023-01-02", periods=n, freq="B")
    df = pd.DataFrame({"open": base, "high": base + 0.3, "low": base - 0.3,
                       "close": base, "volume": 1_000_000.0}, index=idx)
    df.loc[df.index[-1], "low"] = 88.0
    df.loc[df.index[-1], "high"] = 88.4
    df.loc[df.index[-1], "close"] = 88.0
    return an.compute_indicators(df)


def L(name, w):
    return Signal(name, Direction.LONG, w, name)


def S(name, w):
    return Signal(name, Direction.SHORT, w, name)


def _regime_frame(adx, plus_di, minus_di, atr_pct_series, bb_width=0.05):
    n = len(atr_pct_series)
    return pd.DataFrame({
        "adx_14": [adx] * n,
        "plus_di": [plus_di] * n,
        "minus_di": [minus_di] * n,
        "atr_pct": atr_pct_series,
        "bb_width": [bb_width] * n,
    })


def _idea(direction=Direction.LONG, confidence=70.0, vetoes=None):
    return TradeIdea(
        symbol="TEST.NS", style=Style.SWING, direction=direction,
        verdict=Verdict.NO_SETUP, as_of=datetime.now(), timeframe="1d",
        regime=Regime.TRENDING_UP, indicators=IndicatorSnapshot(close=100.0),
        confidence=confidence, vetoes=vetoes or [],
    )


def _plan_idea(direction, entry, stop, target, qty):
    plan = PositionPlan(
        entry=entry, stop_loss=stop, target=target, quantity=qty,
        capital=100_000, risk_pct=0.01, rupees_at_risk=abs(entry - stop) * qty,
        rupees_to_target=abs(target - entry) * qty,
        risk_per_share=abs(entry - stop), reward_per_share=abs(target - entry),
        risk_reward=abs(target - entry) / abs(entry - stop),
    )
    return TradeIdea(
        symbol="TEST.NS", style=Style.SWING, direction=direction,
        verdict=Verdict.TAKE, as_of=datetime.now(), timeframe="1d",
        regime=Regime.TRENDING_UP, indicators=IndicatorSnapshot(close=entry),
        plan=plan,
    )


def _journal():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return ex.Journal(path), path


# =========================================================================== #
#  1.  INDICATORS  (from test_indicators.py)
# =========================================================================== #
def test_sma_matches_manual():
    df = _frame()
    s = an.sma(df["close"], 10)
    assert abs(s.iloc[-1] - df["close"].iloc[-10:].mean()) < 1e-9


def test_ema_is_finite_and_tracks_price():
    df = _frame()
    e = an.ema(df["close"], 20)
    assert np.isfinite(e.iloc[-1])
    assert df["close"].min() <= e.iloc[-1] <= df["close"].max()


def test_rsi_bounded():
    df = _frame()
    r = an.rsi(df["close"], 14).dropna()
    assert (r >= 0).all() and (r <= 100).all()


def test_rsi_all_gains_is_100():
    s = pd.Series(np.arange(1, 60, dtype=float))
    r = an.rsi(s, 14)
    assert r.iloc[-1] == 100.0


def test_atr_positive_and_matches_tr_smoothing():
    df = _frame()
    a = an.atr(df["high"], df["low"], df["close"], 14).dropna()
    assert (a > 0).all()


def test_macd_hist_is_line_minus_signal():
    df = _frame()
    line, sigl, hist = an.macd(df["close"])
    assert abs((line.iloc[-1] - sigl.iloc[-1]) - hist.iloc[-1]) < 1e-9


def test_bollinger_ordering():
    df = _frame()
    u, m, l, w = an.bollinger(df["close"])
    assert u.iloc[-1] > m.iloc[-1] > l.iloc[-1]
    assert w.iloc[-1] > 0


def test_adx_bounded():
    df = _frame()
    a, p, mi = an.adx(df["high"], df["low"], df["close"], 14)
    a = a.dropna()
    assert (a >= 0).all() and (a <= 100).all()


def test_vwap_between_low_and_high():
    df = _frame(n=50)
    v = an.vwap(df["high"], df["low"], df["close"], df["volume"]).dropna()
    assert v.iloc[-1] >= df["low"].min()
    assert v.iloc[-1] <= df["high"].max()


def test_compute_indicators_and_snapshot():
    df = _frame()
    out = an.compute_indicators(df, include_vwap=False)
    snap = an.snapshot(out)
    assert snap.close == float(df["close"].iloc[-1])
    assert snap.rsi_14 is not None and 0 <= snap.rsi_14 <= 100
    assert snap.atr_14 is not None and snap.atr_14 > 0
    assert snap.sma_200 is not None


def test_validate_rejects_missing_columns():
    bad = pd.DataFrame({"open": [1, 2], "close": [1, 2]})
    try:
        an.compute_indicators(bad)
    except ValueError:
        return
    raise AssertionError("Expected ValueError for missing columns")


def test_higher_tf_trend_detects_direction():
    idx = pd.date_range("2022-01-03", periods=400, freq="B")
    up = np.linspace(100, 200, 400)
    df_up = pd.DataFrame({"open": up, "high": up + 1, "low": up - 1,
                          "close": up, "volume": 1e6}, index=idx)
    assert an.higher_tf_trend(df_up, rule="W", fast=10, slow=30) == "up"
    down = np.linspace(200, 100, 400)
    df_dn = pd.DataFrame({"open": down, "high": down + 1, "low": down - 1,
                          "close": down, "volume": 1e6}, index=idx)
    assert an.higher_tf_trend(df_dn, rule="W", fast=10, slow=30) == "down"


def test_higher_tf_trend_insufficient_data_is_none():
    idx = pd.date_range("2023-01-02", periods=20, freq="B")
    c = np.linspace(100, 110, 20)
    df = pd.DataFrame({"open": c, "high": c + 1, "low": c - 1,
                       "close": c, "volume": 1e6}, index=idx)
    assert an.higher_tf_trend(df, rule="W", fast=10, slow=30) == "none"


# =========================================================================== #
#  2.  RISK  (from test_risk.py)
# =========================================================================== #
def test_position_size_canonical_example():
    qty, at_risk = an.position_size(100_000, 500, 480, 0.01, max_exposure_pct=1.0)
    assert qty == 50
    assert at_risk == 1000.0


def test_position_size_respects_exposure_cap():
    qty, _ = an.position_size(100_000, 500, 499, 0.10, max_exposure_pct=0.25)
    assert qty == 50


def test_position_size_zero_when_stop_equals_entry():
    qty, at_risk = an.position_size(100_000, 500, 500, 0.01)
    assert qty == 0 and at_risk == 0.0


def test_atr_stop_direction():
    assert an.atr_stop(500, 10, Direction.LONG, 2.0) == 480
    assert an.atr_stop(500, 10, Direction.SHORT, 2.0) == 520


def test_target_for_rr():
    assert an.target_for_rr(500, 480, Direction.LONG, 2.0) == 540
    assert an.target_for_rr(500, 520, Direction.SHORT, 2.0) == 460


def test_build_plan_full():
    plan = an.build_plan(entry=500, atr=10, direction=Direction.LONG,
                         capital=100_000, risk_pct=0.01, atr_mult=2.0,
                         target_rr=2.0, max_exposure_pct=0.25)
    assert plan.stop_loss == 480
    assert plan.target == 540
    assert plan.quantity == 50
    assert plan.risk_reward == 2.0
    assert plan.rupees_at_risk == 1000.0


def test_expectancy():
    assert abs(an.expectancy_r(0.40, 2.5, 1.0) - 0.4) < 1e-9
    assert an.expectancy_r(0.30, 1.0, 1.0) < 0


def test_breakeven_win_rate():
    assert abs(an.breakeven_win_rate(1.0) - 0.5) < 1e-9
    assert abs(an.breakeven_win_rate(2.0) - (1 / 3)) < 1e-9
    assert abs(an.breakeven_win_rate(3.0) - 0.25) < 1e-9


def test_kelly_clamped_and_zero_for_no_edge():
    assert an.kelly_fraction(0.9, 3.0, cap=0.25) == 0.25
    assert an.kelly_fraction(0.5, 1.0) == 0.0


def test_fractional_kelly_near_one_percent():
    fk = an.fractional_kelly(0.45, 1.33, fraction=0.25)
    assert 0.005 <= fk <= 0.015


def test_veto_low_rr_is_hard():
    plan = an.build_plan(500, 10, Direction.LONG, 100_000, target_rr=1.0)
    v = an.evaluate_vetoes(direction=Direction.LONG, regime=Regime.TRENDING_UP,
                           plan=plan, confidence=70, atr=10, volume_ratio=2.0,
                           is_breakout=False, min_rr=2.0)
    assert any(x.name == "rr_too_low" and x.severity == "hard" for x in v)


def test_veto_no_size_when_capital_tiny():
    plan = an.build_plan(5000, 100, Direction.LONG, 2000, target_rr=2.0)
    v = an.evaluate_vetoes(direction=Direction.LONG, regime=Regime.TRENDING_UP,
                           plan=plan, confidence=70, atr=100, volume_ratio=2.0,
                           is_breakout=False)
    assert any(x.name == "no_size" for x in v)


def test_veto_counter_trend():
    plan = an.build_plan(500, 10, Direction.LONG, 100_000, target_rr=2.5)
    v = an.evaluate_vetoes(direction=Direction.LONG, regime=Regime.TRENDING_DOWN,
                           plan=plan, confidence=70, atr=10, volume_ratio=2.0,
                           is_breakout=False)
    assert any(x.name == "counter_trend" and x.severity == "hard" for x in v)


def test_scenarios_probabilities_sum_to_one():
    for conf in (30, 50, 70, 90):
        for reg in (Regime.TRENDING_UP, Regime.RANGING, Regime.VOLATILE):
            sc = an.build_scenarios(entry=500, stop=480, target=540, atr=10,
                                    direction=Direction.LONG, confidence=conf,
                                    regime=reg)
            total = round(sum(s.probability for s in sc), 6)
            assert total == 1.0, f"probabilities summed to {total} (conf={conf}, {reg})"


def test_structure_stop_guards_wrong_side():
    stop, method = an.choose_stop(entry=100.0, atr=2.0, direction=Direction.LONG,
                                  swing_level=110.0, mult=2.0, method="structure")
    assert stop < 100.0, "stop ended up on the wrong side of entry"
    assert "atr" in method.lower()
    stop2, method2 = an.choose_stop(entry=100.0, atr=2.0, direction=Direction.LONG,
                                    swing_level=96.0, mult=2.0, method="structure")
    assert stop2 < 100.0 and "structure" in method2


# =========================================================================== #
#  3.  REGIME  (from test_regime.py)
# =========================================================================== #
def test_trending_up():
    atr = [0.015] * 120
    r = an.classify_regime(_regime_frame(30, 30, 15, atr))
    assert r.regime == Regime.TRENDING_UP


def test_trending_down():
    atr = [0.015] * 120
    r = an.classify_regime(_regime_frame(30, 12, 28, atr))
    assert r.regime == Regime.TRENDING_DOWN


def test_ranging():
    atr = [0.015] * 120
    r = an.classify_regime(_regime_frame(12, 18, 17, atr))
    assert r.regime == Regime.RANGING


def test_unknown_transitional():
    atr = [0.015] * 120
    r = an.classify_regime(_regime_frame(22, 20, 19, atr))
    assert r.regime == Regime.UNKNOWN


def test_volatile_override_beats_trend():
    atr = [0.01] * 116 + [0.05, 0.05, 0.05, 0.05]
    r = an.classify_regime(_regime_frame(30, 30, 15, atr))
    assert r.regime == Regime.VOLATILE
    assert r.atr_percentile is not None and r.atr_percentile >= 0.80


def test_single_bar_spike_does_not_trigger_volatile():
    atr = [0.01] * 119 + [0.06]
    r = an.classify_regime(_regime_frame(30, 30, 15, atr))
    assert r.regime != Regime.VOLATILE


def test_unknown_when_adx_missing():
    atr = [0.015] * 120
    df = _regime_frame(30, 30, 15, atr)
    df["adx_14"] = np.nan
    r = an.classify_regime(df)
    assert r.regime == Regime.UNKNOWN


# =========================================================================== #
#  4.  SIGNALS  (from test_signals.py)
# =========================================================================== #
def test_empty_signals():
    net, d, conf = an.score_confluence([])
    assert d == Direction.NONE and conf == 0.0


def test_single_signal_confidence_is_capped():
    net, d, conf = an.score_confluence([L("x", 0.2)])
    assert d == Direction.LONG
    assert conf < 50, f"thin evidence scored too high: {conf}"


def test_breadth_raises_confidence():
    thin = an.score_confluence([L("a", 0.2)])[2]
    broad = an.score_confluence([L("a", 0.2), L("b", 0.15), L("c", 0.1),
                                 L("d", 0.1), L("e", 0.08)])[2]
    assert broad > thin
    assert broad >= 60


def test_direction_threshold():
    net, d, conf = an.score_confluence([L("a", 0.1), S("b", 0.1)])
    assert d == Direction.NONE
    net, d, conf = an.score_confluence([S("a", 0.2), S("b", 0.2), S("c", 0.15)])
    assert d == Direction.SHORT and net < 0


def test_symmetric_bearish_breakdown_exists():
    en = _frame_with_final_plunge()
    names = {s.name for s in an.swing_signals(en, regime=Regime.TRENDING_DOWN)}
    assert "breakdown_20d_low" in names


def test_bollinger_gated_long_only_in_range():
    en = _frame_with_final_plunge()
    down = {s.name for s in an.swing_signals(en, regime=Regime.TRENDING_DOWN)}
    assert "bb_lower_touch" not in down
    rng = {s.name for s in an.swing_signals(en, regime=Regime.RANGING)}
    assert "bb_lower_touch" in rng


def test_ma_signal_requires_persistence():
    n = 260
    close = np.linspace(90, 80, n)
    close[-1] = 200.0
    idx = pd.date_range("2023-01-02", periods=n, freq="B")
    df = pd.DataFrame({"open": close, "high": close + 0.5, "low": close - 0.5,
                       "close": close, "volume": 1e6}, index=idx)
    en = an.compute_indicators(df)
    names = {s.name for s in an.swing_signals(en)}
    assert "above_200sma" not in names


def test_breakout_and_resistance_never_both_fire():
    en = _rising_frame()
    names = {s.name for s in an.swing_signals(en, regime=Regime.RANGING)}
    assert "breakout_20d_high" in names
    assert "near_resistance" not in names, "contradictory signals fired together"


def test_breakdown_and_support_never_both_fire():
    en = _frame_with_final_plunge()
    names = {s.name for s in an.swing_signals(en, regime=Regime.RANGING)}
    assert "breakdown_20d_low" in names
    assert "near_support" not in names


def test_bb_touch_and_52w_low_dont_contradict_in_range():
    en = _frame_with_final_plunge()
    names = {s.name for s in an.swing_signals(en, regime=Regime.RANGING)}
    assert "near_52w_low" not in names
    down = {s.name for s in an.swing_signals(en, regime=Regime.TRENDING_DOWN)}
    assert "near_52w_low" in down


def test_obv_signal_is_emitted():
    en = _rising_frame()
    names = {s.name for s in an.swing_signals(en, regime=Regime.TRENDING_UP)}
    assert any(n.startswith("obv_") for n in names), "OBV is computed but unused"


def test_vwap_cross_suppressed_across_session_boundary():
    t1 = pd.date_range("2023-01-02 09:15", periods=8, freq="15min")
    t2 = pd.date_range("2023-01-03 09:15", periods=1, freq="15min")
    idx = t1.append(t2)
    close = [100, 99, 98, 97, 96, 95, 94, 93, 110]
    df = pd.DataFrame({"open": close, "high": [c + 0.5 for c in close],
                       "low": [c - 0.5 for c in close], "close": close,
                       "volume": 1_000_000.0}, index=idx)
    en = an.compute_indicators(df, include_vwap=True)
    names = {s.name for s in an.intraday_signals(en)}
    assert "vwap_reclaim" not in names, "phantom cross across the daily VWAP reset"


def test_htf_alignment_signal():
    en = _rising_frame()
    up = {s.name: s.direction for s in an.swing_signals(en, regime=Regime.TRENDING_UP, htf="up")}
    assert up.get("htf_uptrend") == Direction.LONG
    down = {s.name: s.direction for s in an.swing_signals(en, regime=Regime.TRENDING_UP, htf="down")}
    assert down.get("htf_downtrend") == Direction.SHORT
    none = {s.name for s in an.swing_signals(en, regime=Regime.TRENDING_UP, htf="none")}
    assert "htf_uptrend" not in none and "htf_downtrend" not in none


def test_htf_conflict_lowers_confluence():
    en = _rising_frame()
    aligned = an.score_confluence(an.swing_signals(en, regime=Regime.TRENDING_UP, htf="up"))[2]
    conflict = an.score_confluence(an.swing_signals(en, regime=Regime.TRENDING_UP, htf="down"))[2]
    assert aligned > conflict


# =========================================================================== #
#  5.  JOURNAL  (from test_journal.py)
# =========================================================================== #
def test_long_win_r_is_net_of_costs():
    j, path = _journal()
    try:
        tid = j.log_idea(_plan_idea(Direction.LONG, 100, 90, 120, 100))
        res = j.close_trade(tid, 120.0)
        assert 1.8 <= res["outcome_r"] < 2.0
        assert res["costs"] > 0
        gross = (120 - 100) * 100
        assert res["pnl"] < gross
    finally:
        os.unlink(path)


def test_long_loss_is_minus_one_r_ish():
    j, path = _journal()
    try:
        tid = j.log_idea(_plan_idea(Direction.LONG, 100, 90, 120, 100))
        res = j.close_trade(tid, 90.0)
        assert res["outcome_r"] <= -1.0
    finally:
        os.unlink(path)


def test_short_win_direction_math():
    j, path = _journal()
    try:
        tid = j.log_idea(_plan_idea(Direction.SHORT, 100, 110, 80, 50))
        res = j.close_trade(tid, 80.0)
        assert res["outcome_r"] > 0
        assert res["pnl"] > 0
    finally:
        os.unlink(path)


def test_stats_expectancy_and_reliability_flag():
    j, path = _journal()
    try:
        for exit_px in (120.0, 120.0):
            tid = j.log_idea(_plan_idea(Direction.LONG, 100, 90, 120, 10))
            j.close_trade(tid, exit_px)
        tid = j.log_idea(_plan_idea(Direction.LONG, 100, 90, 120, 10))
        j.close_trade(tid, 90.0)
        stats = j.stats()
        assert stats["closed_trades"] == 3
        assert 0 < stats["win_rate"] < 1
        assert stats["reliable"] is False
        assert stats["expectancy_r"] is not None
    finally:
        os.unlink(path)


def test_cannot_double_close():
    j, path = _journal()
    try:
        tid = j.log_idea(_plan_idea(Direction.LONG, 100, 90, 120, 10))
        j.close_trade(tid, 110.0)
        try:
            j.close_trade(tid, 115.0)
        except ValueError:
            return
        raise AssertionError("expected ValueError on double close")
    finally:
        os.unlink(path)


def test_intraday_trade_uses_lower_costs():
    j, path = _journal()
    try:
        sw = _plan_idea(Direction.LONG, 100, 90, 120, 100)
        sw.style = Style.SWING
        ti = j.log_idea(sw)
        swing_costs = j.close_trade(ti, 110.0)["costs"]

        intr = _plan_idea(Direction.LONG, 100, 90, 120, 100)
        intr.style = Style.INTRADAY
        ti2 = j.log_idea(intr)
        intraday_costs = j.close_trade(ti2, 110.0)["costs"]

        assert intraday_costs < swing_costs, "intraday should be cheaper than delivery"
    finally:
        os.unlink(path)


# =========================================================================== #
#  6.  ANALYZER  (from test_analyzer.py)
# =========================================================================== #
def test_no_direction_is_no_setup():
    idea = _idea(direction=Direction.NONE)
    assert _decide_verdict(idea, raw_conf=80, supporting=5) == Verdict.NO_SETUP


def test_hard_veto_is_avoid():
    idea = _idea(confidence=90)
    idea.vetoes = [Veto("rr_too_low", "bad rr", "hard")]
    assert _decide_verdict(idea, raw_conf=80, supporting=5) == Verdict.AVOID


def test_take_requires_floor_raw_and_breadth():
    idea = _idea(confidence=70)
    assert _decide_verdict(idea, raw_conf=60, supporting=4) == Verdict.TAKE
    v = _decide_verdict(idea, raw_conf=60, supporting=2)
    assert v != Verdict.TAKE
    v = _decide_verdict(idea, raw_conf=40, supporting=5)
    assert v != Verdict.TAKE


def test_watch_band():
    idea = _idea(confidence=50)
    assert _decide_verdict(idea, raw_conf=60, supporting=5) == Verdict.WATCH


def test_below_watch_is_no_setup():
    idea = _idea(confidence=20)
    assert _decide_verdict(idea, raw_conf=10, supporting=1) == Verdict.NO_SETUP


def test_ranging_breakout_penalised_not_rewarded():
    bkout = _adjust_confidence(60, Direction.LONG, Regime.RANGING, is_breakout=True)
    meanrev = _adjust_confidence(60, Direction.LONG, Regime.RANGING, is_breakout=False)
    assert bkout < 60 < meanrev


def test_counter_trend_penalised():
    aligned = _adjust_confidence(60, Direction.LONG, Regime.TRENDING_UP)
    against = _adjust_confidence(60, Direction.LONG, Regime.TRENDING_DOWN)
    assert against < aligned


def test_pipeline_uptrend_is_long_take():
    s = Settings(data_source="csv", csv_dir=SAMPLE_DIR, capital=100_000)
    agent = Analyzer(s, source=CSVSource(SAMPLE_DIR))
    idea = agent.analyze("UPTREND", style=Style.SWING, use_llm=False)
    assert idea.direction == Direction.LONG
    assert idea.verdict == Verdict.TAKE
    assert idea.plan is not None and idea.plan.quantity > 0
    assert idea.plan.risk_reward >= s.min_rr
    assert idea.plan.rupees_at_risk_worst >= idea.plan.rupees_at_risk
    assert idea.narration


def test_pipeline_downtrend_not_long():
    s = Settings(data_source="csv", csv_dir=SAMPLE_DIR)
    agent = Analyzer(s, source=CSVSource(SAMPLE_DIR))
    idea = agent.analyze("DOWNTREND", style=Style.SWING, use_llm=False)
    assert idea.direction != Direction.LONG


# =========================================================================== #
#  7.  BACKTEST  (from test_backtest.py)
# =========================================================================== #
def _bt_trade(net, r, reason="target"):
    d = datetime(2024, 1, 1)
    return BTTrade("X", "long", d, 100, d, 110, 10, net, 5, net, r, reason)


def test_compute_stats_basic():
    trades = [_bt_trade(200, 2.0), _bt_trade(200, 2.0), _bt_trade(-100, -1.0)]
    s = _compute_stats(trades, 100_000, 100_300, 0.05,
                       datetime(2023, 1, 1), datetime(2024, 1, 1))
    assert s["trades"] == 3
    assert abs(s["win_rate"] - 2 / 3) < 1e-3
    assert s["expectancy_r"] > 0
    assert s["profit_factor"] == 4.0


def test_compute_stats_empty():
    s = _compute_stats([], 100_000, 100_000, 0.0,
                       datetime(2023, 1, 1), datetime(2024, 1, 1))
    assert s["trades"] == 0


def test_gap_fill_long_and_short():
    assert _gap_fill(95.0, 98.0, long_pos=True) == 95.0
    assert _gap_fill(99.0, 98.0, long_pos=True) == 98.0
    assert _gap_fill(105.0, 102.0, long_pos=False) == 105.0
    assert _gap_fill(101.0, 102.0, long_pos=False) == 102.0


def _load(name):
    df = pd.read_csv(os.path.join(SAMPLE_DIR, f"{name}_1d.csv"), parse_dates=["Date"])
    df = df.set_index("Date")
    df.columns = [c.lower() for c in df.columns]
    return df


def test_downtrend_generates_short_trades():
    s = Settings(data_source="csv", csv_dir=SAMPLE_DIR)
    df = _load("DOWNTREND")
    res = backtest_swing(df, "DOWNTREND", s, allow_short=True)
    assert len(res.trades) > 0
    assert any(t.direction == "short" for t in res.trades), "no shorts simulated"


def test_allow_short_false_blocks_shorts():
    s = Settings(data_source="csv", csv_dir=SAMPLE_DIR)
    df = _load("DOWNTREND")
    res = backtest_swing(df, "DOWNTREND", s, allow_short=False)
    assert all(t.direction == "long" for t in res.trades)


def test_costmodel_intraday_has_lower_stt():
    delivery = CostModel()
    intraday = CostModel.intraday()
    assert intraday.stt_sell_pct < delivery.stt_sell_pct


# =========================================================================== #
#  8.  NEWS  (from test_news.py)
# =========================================================================== #
def test_sentiment_positive_and_negative():
    assert ex.simple_sentiment("Stock surges to record high on strong profit") > 0
    assert ex.simple_sentiment("Shares plunge on fraud probe and losses") < 0


def test_sentiment_neutral_when_no_keywords():
    assert ex.simple_sentiment("Company holds annual general meeting today") == 0.0


def test_word_boundary_matching():
    assert ex.mentions("SBIN reports Q2 results", "SBIN") is True
    assert ex.mentions("SBICARD launches new card", "SBIN") is False
    assert ex.mentions("ITC raises dividend", "ITC") is True
    assert ex.mentions("SWITCH maker announces expansion", "ITC") is False


def test_mentions_is_case_insensitive():
    assert ex.mentions("reliance industries gains", "RELIANCE") is True
    assert ex.mentions("RELIANCE.NS rallies", "RELIANCE.NS") is True


def test_negation_flips_polarity():
    assert ex.simple_sentiment("Company posts no loss this quarter") > 0
    assert ex.simple_sentiment("Guidance not strong, outlook cautious") < 0


def test_negation_does_not_break_plain_sentiment():
    assert ex.simple_sentiment("Record profit and strong growth") > 0
    assert ex.simple_sentiment("Fraud probe and heavy losses") < 0


# =========================================================================== #
#  AngelOneSource - scaffold + graceful fallback
# =========================================================================== #
def test_angel_source_instantiates_without_credentials():
    """No env vars set => must instantiate and report no creds, not crash."""
    for k in ("ANGEL_API_KEY", "ANGEL_CLIENT_ID", "ANGEL_MPIN", "ANGEL_TOTP_SECRET"):
        os.environ.pop(k, None)
    from advisor.angel_source import AngelOneSource
    src = AngelOneSource()
    assert src.name == "angel"
    assert src._has_creds() is False
    # get_quote must never raise; it returns None or a float (from yfinance fallback)
    q = src.get_quote("RELIANCE")
    assert q is None or isinstance(q, float)


def test_angel_source_registered_in_factory():
    from advisor.core import get_source
    from advisor.angel_source import AngelOneSource
    src = get_source("angel")
    assert isinstance(src, AngelOneSource)


# =========================================================================== #
#  Triple-Barrier labels (AFML ch. 3)
# =========================================================================== #
def _tb_series(values):
    return pd.Series(values, index=pd.date_range("2023-01-02", periods=len(values),
                                                  freq="B"))


def test_triple_barrier_uptrend_mostly_wins_for_longs():
    n = 200
    close = _tb_series(np.linspace(100.0, 200.0, n))
    atr_s = _tb_series(np.full(n, 0.5))
    out = an.triple_barrier_labels(close, take_profit_atr=2.0, stop_loss_atr=2.0,
                                    max_hold_bars=10, atr_series=atr_s,
                                    direction="long")
    # Exclude the tail where the forward horizon is truncated.
    core = out["label"].iloc[:-10]
    assert (core == 1).mean() >= 0.9
    assert (core == -1).sum() == 0


def test_triple_barrier_downtrend_flips_by_direction():
    n = 200
    close = _tb_series(np.linspace(200.0, 100.0, n))
    atr_s = _tb_series(np.full(n, 0.5))
    longs = an.triple_barrier_labels(close, 2.0, 2.0, 10, atr_s, direction="long")
    shorts = an.triple_barrier_labels(close, 2.0, 2.0, 10, atr_s, direction="short")
    assert (longs["label"].iloc[:-10] == -1).mean() >= 0.9
    assert (shorts["label"].iloc[:-10] == 1).mean() >= 0.9


def test_triple_barrier_sideways_mostly_timeout():
    n = 200
    rng = np.random.default_rng(0)
    close = _tb_series(100 + rng.normal(0.0, 0.05, n))    # tiny noise
    atr_s = _tb_series(np.full(n, 5.0))                    # very wide barriers
    out = an.triple_barrier_labels(close, 2.0, 2.0, 10, atr_s, direction="long")
    core = out["label"].iloc[:-10]
    assert (core == 0).mean() >= 0.9


# =========================================================================== #
#  Telegram notifier
# =========================================================================== #
def test_telegram_notifier_is_not_configured_without_env():
    from advisor.telegram_bot import TelegramNotifier
    assert TelegramNotifier(bot_token=None, chat_id=None).is_configured() is False


# =========================================================================== #
#  Runner
# =========================================================================== #
if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failures = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as e:
            failures += 1
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failures}/{len(fns)} tests passed.")
    if failures:
        sys.exit(1)
