"""
advisor.engine
==============
The orchestrator layer, merging two closely-coupled modules:

  1. **Analyzer** - the brain. `Analyzer.analyze()` runs the full pipeline for
     one symbol and returns a complete `TradeIdea`:
         data -> indicators -> regime -> signals -> confluence ->
         position plan -> scenarios -> red-signal vetoes ->
         (journal expectancy + news sentiment) -> narration -> VERDICT
  2. **Backtest** - a small, correct backtester that reuses the exact same
     signal + risk logic as the live analyzer (no look-ahead), models Indian
     equity costs (brokerage/STT/exchange/GST/SEBI/stamp/slippage), and
     reports a mark-to-market drawdown.

Verdict logic (deterministic):
    direction is NONE                          -> NO_SETUP
    a hard veto fired                          -> AVOID
    adjusted confidence >= TAKE_FLOOR          -> TAKE
    adjusted confidence >= WATCH_FLOOR         -> WATCH
    otherwise                                  -> NO_SETUP
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from . import analysis as an
from . import extras as ex
from .core import (
    Direction, OHLCVSource, Regime, Settings, Style, TradeIdea, Verdict,
    get_source, normalize_symbol,
)


# =========================================================================== #
#  1.  ANALYZER
# =========================================================================== #
TAKE_FLOOR = 60.0          # raised: TAKE should mean a genuinely clean setup
WATCH_FLOOR = 45.0
MIN_RAW_CONF_FOR_TAKE = 50.0   # the pre-adjustment evidence must be solid too
MIN_SIGNALS_FOR_TAKE = 3       # at least 3 distinct signals must agree

# Breakout-type signal names (used for the volume-confirmation veto and the
# range-breakout veto). Includes the symmetric bearish breakdowns.
_BREAKOUT_SIGNALS = {
    "breakout_20d_high", "near_52w_high", "breakdown_20d_low", "near_52w_low",
    "orb_breakout_up", "orb_breakout_down",
}


class Analyzer:
    def __init__(self, settings: Settings | None = None,
                 source: OHLCVSource | None = None,
                 journal: "ex.Journal | None" = None):
        self.settings = settings or Settings()
        self.source = source or get_source(self.settings.data_source,
                                           exchange=self.settings.exchange,
                                           directory=self.settings.csv_dir)
        self.journal = journal
        # Scan-scoped memo of journal.stats(): populated by scan() so a
        # watchlist scan does one SQLite pass instead of one per symbol.
        # None means "no memo - read fresh" (direct analyze() calls stay fresh).
        self._journal_stats_memo: dict | None = None

    # ------------------------------------------------------------------ #
    def analyze(self, symbol: str, style: Style = Style.SWING,
                use_news: bool | None = None, use_llm: bool | None = None) -> TradeIdea:
        s = self.settings
        intraday = style == Style.INTRADAY
        interval = s.intraday_interval if intraday else s.swing_interval
        period = s.intraday_period if intraday else s.swing_period

        # 1) DATA -------------------------------------------------------- #
        df = self.source.get_history(symbol, interval=interval, period=period)
        if len(df) < 30:
            raise ValueError(
                f"Only {len(df)} bars for {symbol} - need >=30 for a useful read.")

        # 2) INDICATORS -------------------------------------------------- #
        enriched = an.compute_indicators(df, include_vwap=intraday)
        snap = an.snapshot(enriched)

        # 3) REGIME ------------------------------------------------------ #
        regime_read = an.classify_regime(enriched)
        regime = regime_read.regime

        # 4) SIGNALS + 5) CONFLUENCE ------------------------------------ #
        if intraday:
            signals = an.intraday_signals(enriched, s.opening_range_bars)
        else:
            htf = an.higher_tf_trend(enriched, rule="W", fast=10, slow=30)
            signals = an.swing_signals(enriched, regime=regime, htf=htf)
        confluence, direction, raw_conf = an.score_confluence(signals)

        _ts = enriched.index[-1]
        if hasattr(_ts, "to_pydatetime"):
            as_of = _ts.to_pydatetime()
            if as_of.tzinfo is not None:
                as_of = as_of.replace(tzinfo=None)
        else:
            as_of = datetime.now()

        idea = TradeIdea(
            symbol=normalize_symbol(symbol, s.exchange),
            style=style, direction=direction, verdict=Verdict.NO_SETUP,
            as_of=as_of,
            timeframe=interval, regime=regime,
            indicators=snap, signals=signals, confluence_score=confluence,
        )
        idea.notes.append(regime_read.explanation)

        if direction == Direction.NONE:
            idea.verdict = Verdict.NO_SETUP
            idea.confidence = raw_conf
            idea.narration = _maybe_narrate(idea, s, use_llm)
            return idea

        # 6) POSITION PLAN ---------------------------------------------- #
        entry = snap.close
        atr = snap.atr_14
        if not atr or atr <= 0:
            rng = (enriched["high"] - enriched["low"]).tail(14)
            atr = float(rng.mean()) if len(rng) else 0.01 * entry
            if not atr or atr <= 0:
                atr = 0.01 * entry
            idea.notes.append(
                "ATR was unavailable; using a fallback range estimate, so the stop "
                "distance is approximate - double-check before trading.")
        swing_level = (snap.recent_low_20 if direction == Direction.LONG
                       else snap.recent_high_20)
        plan = an.build_plan(
            entry=entry, atr=atr, direction=direction, capital=s.capital,
            risk_pct=s.risk_pct, atr_mult=s.atr_mult, target_rr=s.target_rr,
            max_exposure_pct=s.max_exposure_pct, swing_level=swing_level,
            stop_method="atr", slippage_pct=s.slippage_pct,
            gap_buffer_atr=s.gap_buffer_atr,
        )
        idea.plan = plan

        # 7) SCENARIOS --------------------------------------------------- #
        idea.scenarios = an.build_scenarios(
            entry=plan.entry, stop=plan.stop_loss, target=plan.target,
            atr=atr, direction=direction, confidence=raw_conf, regime=regime,
        )

        # 8) CONFIDENCE ADJUSTMENT -------------------------------------- #
        is_breakout = any(x.name in _BREAKOUT_SIGNALS for x in signals)
        conf = _adjust_confidence(raw_conf, direction, regime, is_breakout)

        # 9) VETOES ------------------------------------------------------ #
        idea.vetoes = an.evaluate_vetoes(
            direction=direction, regime=regime, plan=plan, confidence=conf,
            atr=atr, volume_ratio=snap.volume_ratio(), is_breakout=is_breakout,
            min_rr=s.min_rr, min_confidence=s.min_confidence,
        )
        conf -= 5.0 * len(_soft_only(idea.vetoes))

        # 10) JOURNAL EXPECTANCY ---------------------------------------- #
        if self.journal is not None:
            stats = (self._journal_stats_memo if self._journal_stats_memo is not None
                     else self.journal.stats())
            if stats.get("closed_trades", 0) > 0:
                idea.expectancy_r = stats.get("expectancy_r")

        # 11) NEWS SENTIMENT -------------------------------------------- #
        run_news = s.news_enabled if use_news is None else use_news
        if run_news:
            score, _ = ex.sentiment_for_symbol(s.news_feeds, idea.symbol)
            if score is not None:
                idea.news_sentiment = score
                supports = ((direction == Direction.LONG and score >= 0.4) or
                            (direction == Direction.SHORT and score <= -0.4))
                opposes = ((direction == Direction.LONG and score <= -0.4) or
                           (direction == Direction.SHORT and score >= 0.4))
                if opposes:
                    conf -= 5.0
                    idea.notes.append("Headlines clearly oppose the trade - tempering confidence.")
                elif supports:
                    conf += 5.0
                    idea.notes.append("Headlines clearly support the trade.")

        idea.confidence = round(max(0.0, min(conf, 100.0)), 1)

        # 12) VERDICT ---------------------------------------------------- #
        supporting = sum(1 for x in signals if x.direction == direction)
        idea.verdict = _decide_verdict(idea, raw_conf=raw_conf, supporting=supporting)

        if direction == Direction.SHORT and style == Style.SWING:
            idea.notes.append(
                "Note: NSE/BSE cash segment does not allow overnight short selling. "
                "A swing short means intraday-only, or via futures/options (separate "
                "risk profile). Treat this as 'avoid longs' rather than 'go short'.")
        if direction == Direction.SHORT and style == Style.INTRADAY:
            idea.notes.append(
                "Intraday short: requires a margin (MIS) product and MUST be squared "
                "off before the 3:30 PM close, or the broker auto-squares it. "
                "Borrow/availability and margin rules apply.")

        # 13) NARRATION -------------------------------------------------- #
        idea.narration = _maybe_narrate(idea, s, use_llm)
        return idea

    # ------------------------------------------------------------------ #
    def scan(self, symbols: list[str] | None = None,
             style: Style = Style.SWING,
             progress=None) -> list[TradeIdea]:
        """Analyze a whole watchlist and return ideas sorted best-first."""
        import time
        syms = symbols or self.settings.watchlist
        ideas: list[TradeIdea] = []
        self.scan_failures: list[tuple[str, str]] = []
        n = len(syms)
        throttle = self.settings.data_source == "yfinance" and self.settings.scan_delay_sec > 0
        if self.journal is not None:
            # One stats read for the whole scan instead of one per symbol.
            self._journal_stats_memo = self.journal.stats()
        try:
            for i, sym in enumerate(syms, 1):
                if progress is not None:
                    progress(i, n, sym)
                try:
                    ideas.append(self.analyze(sym, style=style))
                except Exception as e:  # noqa: BLE001 - we want to continue the scan
                    self.scan_failures.append((sym, str(e)))
                if throttle and i < n:
                    time.sleep(self.settings.scan_delay_sec)
        finally:
            self._journal_stats_memo = None
        return sorted(ideas, key=_rank_key, reverse=True)


# --------------------------------------------------------------------------- #
#  Verdict & confidence helpers
# --------------------------------------------------------------------------- #
def _adjust_confidence(raw: float, direction: Direction, regime: Regime,
                       is_breakout: bool = False) -> float:
    """Nudge the evidence score by regime context (ORDINAL, not probability)."""
    conf = raw
    if regime == Regime.TRENDING_UP:
        conf += 6.0 if direction == Direction.LONG else -12.0
    elif regime == Regime.TRENDING_DOWN:
        conf += 6.0 if direction == Direction.SHORT else -12.0
    elif regime == Regime.RANGING:
        conf += -6.0 if is_breakout else 3.0   # breakouts fail in ranges
    elif regime == Regime.VOLATILE:
        conf -= 6.0
    return conf


def _decide_verdict(idea: TradeIdea, raw_conf: float = 0.0,
                    supporting: int = 0) -> Verdict:
    if idea.direction == Direction.NONE:
        return Verdict.NO_SETUP
    if idea.hard_vetoes:
        return Verdict.AVOID
    if (idea.confidence >= TAKE_FLOOR and raw_conf >= MIN_RAW_CONF_FOR_TAKE
            and supporting >= MIN_SIGNALS_FOR_TAKE):
        return Verdict.TAKE
    if idea.confidence >= WATCH_FLOOR:
        return Verdict.WATCH
    return Verdict.NO_SETUP


def _rank_key(idea: TradeIdea):
    """Sort TAKE > WATCH > others, then by confidence, then by R:R."""
    order = {Verdict.TAKE: 3, Verdict.WATCH: 2, Verdict.NO_SETUP: 1, Verdict.AVOID: 0}
    rr = idea.plan.risk_reward if idea.plan else 0.0
    return (order[idea.verdict], idea.confidence, rr)


def _maybe_narrate(idea: TradeIdea, s: Settings, use_llm: bool | None) -> str:
    provider = s.llm_provider if use_llm is None else ("ollama" if use_llm else "none")
    if use_llm is False:
        provider = "none"
    return ex.narrate(
        idea, provider=provider, model=s.llm_model,
        ollama_host=s.ollama_host, groq_api_key=s.groq_api_key,
        gemini_api_key=s.gemini_api_key,
    )


def _soft_only(vetoes):
    """Count soft vetoes excluding low_confidence (routed via thresholds)."""
    return [v for v in vetoes if v.severity == "soft" and v.name != "low_confidence"]


# =========================================================================== #
#  2.  BACKTEST
# =========================================================================== #
@dataclass
class CostModel:
    """Approximate round-trip frictions for NSE/BSE equities."""
    brokerage_pct: float = 0.0
    brokerage_cap: float = 20.0
    stt_sell_pct: float = 0.001
    exch_txn_pct: float = 0.0000345
    gst_pct: float = 0.18
    sebi_pct: float = 0.000001
    stamp_buy_pct: float = 0.00015
    slippage_pct: float = 0.0005

    @classmethod
    def intraday(cls) -> "CostModel":
        return cls(brokerage_pct=0.0003, stt_sell_pct=0.00025, stamp_buy_pct=0.00003)

    def _brokerage(self, value: float) -> float:
        return min(value * self.brokerage_pct, self.brokerage_cap)

    def entry_cost(self, value: float) -> float:
        b = self._brokerage(value)
        txn = value * self.exch_txn_pct
        gst = (b + txn) * self.gst_pct
        return b + txn + gst + value * self.sebi_pct + value * self.stamp_buy_pct \
            + value * self.slippage_pct

    def exit_cost(self, value: float) -> float:
        b = self._brokerage(value)
        txn = value * self.exch_txn_pct
        gst = (b + txn) * self.gst_pct
        return b + txn + gst + value * self.sebi_pct + value * self.stt_sell_pct \
            + value * self.slippage_pct


@dataclass
class BTTrade:
    symbol: str
    direction: str
    entry_date: datetime
    entry: float
    exit_date: datetime
    exit: float
    quantity: int
    gross_pnl: float
    costs: float
    net_pnl: float
    outcome_r: float
    reason: str          # "target" | "stop" | "signal_flip" | "eod_close"


@dataclass
class BacktestResult:
    symbol: str
    start: datetime
    end: datetime
    trades: list[BTTrade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def summary(self) -> str:
        s = self.stats
        if not self.trades:
            return f"No trades generated for {self.symbol} in this period."
        return (
            f"Backtest: {self.symbol}  ({self.start:%Y-%m-%d} -> {self.end:%Y-%m-%d})\n"
            f"  Trades            : {s['trades']}\n"
            f"  Win rate          : {s['win_rate']*100:.1f}%\n"
            f"  Expectancy        : {s['expectancy_r']:+.2f} R per trade\n"
            f"  Profit factor     : {s['profit_factor']}\n"
            f"  Avg win / avg loss: +{s['avg_win_r']:.2f}R / -{s['avg_loss_r']:.2f}R\n"
            f"  Net return        : {s['total_return_pct']:+.1f}%  "
            f"(CAGR {s['cagr_pct']:+.1f}%)\n"
            f"  Max drawdown      : {s['max_drawdown_pct']:.1f}% (mark-to-market)\n"
            f"  Costs paid         : Rs.{s['costs_paid']:,.0f}\n"
            f"  Ambiguous bars    : {s.get('ambiguous_exits', 0)} "
            f"(stop & target hit same day - counted as stop)\n"
            f"  Final equity      : Rs.{s['final_equity']:,.0f} "
            f"(from Rs.{s['start_equity']:,.0f})"
        )


def backtest_swing(df: pd.DataFrame, symbol: str, settings: Settings,
                   costs: CostModel | None = None, *, allow_short: bool = True,
                   max_hold_bars: int = 40) -> BacktestResult:
    """Event-driven swing backtest on a daily OHLCV frame (already cleaned)."""
    costs = costs or CostModel()
    enriched = an.compute_indicators(df, include_vwap=False)

    equity = start_equity = peak = settings.capital
    max_dd = 0.0
    trades: list[BTTrade] = []
    curve: list[float] = []
    ambiguous = 0

    in_pos = False
    side = Direction.LONG
    entry_px = stop_px = target_px = 0.0
    init_stop = 0.0
    atr_at_entry = 0.0
    qty = 0
    entry_idx = None
    entry_cost_paid = 0.0

    start_i = min(200, max(30, len(enriched) - 20))

    for i in range(start_i, len(enriched) - 1):
        today = enriched.iloc[i]
        nxt = enriched.iloc[i + 1]
        date_next = enriched.index[i + 1]
        long_pos = side == Direction.LONG

        # ---- manage an open position on the next bar -------------------- #
        if in_pos:
            exit_now = False
            exit_px = None
            reason = ""

            hit_stop = (nxt["low"] <= stop_px) if long_pos else (nxt["high"] >= stop_px)
            hit_target = (nxt["high"] >= target_px) if long_pos else (nxt["low"] <= target_px)

            if hit_stop and hit_target:
                ambiguous += 1
                exit_px = _gap_fill(nxt["open"], stop_px, long_pos)
                reason, exit_now = "stop_ambiguous", True
            elif hit_stop:
                exit_px = _gap_fill(nxt["open"], stop_px, long_pos)
                reason, exit_now = "stop", True
            elif hit_target:
                exit_px, reason, exit_now = target_px, "target", True
            elif (i + 1) - entry_idx >= max_hold_bars:
                exit_px, reason, exit_now = float(nxt["open"]), "max_hold", True
            else:
                sub = enriched.iloc[: i + 1]
                reg = an.classify_regime(sub).regime
                htf = an.higher_tf_trend(sub, rule="W", fast=10, slow=30)
                _, d, _ = an.score_confluence(an.swing_signals(sub, regime=reg, htf=htf))
                if (long_pos and d == Direction.SHORT) or (not long_pos and d == Direction.LONG):
                    exit_px, reason, exit_now = float(nxt["open"]), "signal_flip", True

            if exit_now:
                sgn = 1 if long_pos else -1
                gross = (exit_px - entry_px) * qty * sgn
                exit_cost_paid = costs.exit_cost(exit_px * qty)
                net = gross - entry_cost_paid - exit_cost_paid
                rps = abs(entry_px - init_stop)
                outcome_r = (net / (rps * qty)) if rps > 0 and qty > 0 else 0.0
                equity += net
                trades.append(BTTrade(
                    symbol=symbol, direction="long" if long_pos else "short",
                    entry_date=enriched.index[entry_idx], entry=round(entry_px, 2),
                    exit_date=date_next, exit=round(exit_px, 2), quantity=qty,
                    gross_pnl=round(gross, 2),
                    costs=round(entry_cost_paid + exit_cost_paid, 2),
                    net_pnl=round(net, 2), outcome_r=round(outcome_r, 3),
                    reason=reason,
                ))
                in_pos = False
            else:
                rps = abs(entry_px - init_stop)
                if rps > 0 and atr_at_entry > 0:
                    trail_dist = settings.atr_mult * atr_at_entry
                    if long_pos and nxt["high"] >= entry_px + rps:
                        trail = max(entry_px, float(nxt["high"]) - trail_dist)
                        stop_px = max(stop_px, trail)
                    elif not long_pos and nxt["low"] <= entry_px - rps:
                        trail = min(entry_px, float(nxt["low"]) + trail_dist)
                        stop_px = min(stop_px, trail)

        # ---- look for a new entry (flat only) --------------------------- #
        if not in_pos:
            sub = enriched.iloc[: i + 1]
            reg = an.classify_regime(sub).regime
            htf = an.higher_tf_trend(sub, rule="W", fast=10, slow=30)
            sigs = an.swing_signals(sub, regime=reg, htf=htf)
            _, direction, raw_conf = an.score_confluence(sigs)
            is_bkout = any(x.name in _BREAKOUT_SIGNALS for x in sigs)
            conf = _adjust_confidence(raw_conf, direction, reg, is_bkout)
            supporting = sum(1 for x in sigs if x.direction == direction)

            tradeable = direction in (Direction.LONG, Direction.SHORT)
            if direction == Direction.SHORT and not allow_short:
                tradeable = False
            if direction == Direction.LONG and reg == Regime.TRENDING_DOWN:
                tradeable = False
            if direction == Direction.SHORT and reg == Regime.TRENDING_UP:
                tradeable = False

            if (tradeable and conf >= TAKE_FLOOR and raw_conf >= MIN_RAW_CONF_FOR_TAKE
                    and supporting >= MIN_SIGNALS_FOR_TAKE):
                atr = today.get("atr_14")
                if atr and atr > 0:
                    swing_level = (today.get("recent_low_20") if direction == Direction.LONG
                                   else today.get("recent_high_20"))
                    plan = an.build_plan(
                        entry=float(nxt["open"]), atr=float(atr), direction=direction,
                        capital=equity, risk_pct=settings.risk_pct,
                        atr_mult=settings.atr_mult, target_rr=settings.target_rr,
                        max_exposure_pct=settings.max_exposure_pct,
                        swing_level=swing_level, stop_method="atr",
                        slippage_pct=settings.slippage_pct,
                        gap_buffer_atr=settings.gap_buffer_atr)
                    if plan.quantity > 0 and plan.risk_reward >= settings.min_rr:
                        in_pos = True
                        side = direction
                        entry_px = plan.entry
                        stop_px = init_stop = plan.stop_loss
                        target_px = plan.target
                        qty = plan.quantity
                        atr_at_entry = float(atr)
                        entry_idx = i + 1
                        entry_cost_paid = costs.entry_cost(entry_px * qty)

        # ---- mark-to-market equity ------------------------------------- #
        mtm = equity
        if in_pos:
            sgn = 1 if side == Direction.LONG else -1
            close_px = float(nxt["close"])
            unreal = (close_px - entry_px) * qty * sgn
            mtm = equity - entry_cost_paid + unreal - costs.exit_cost(close_px * qty)
        curve.append(mtm)
        peak = max(peak, mtm)
        dd = (peak - mtm) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    result = BacktestResult(
        symbol=symbol, start=enriched.index[start_i], end=enriched.index[-1],
        trades=trades, equity_curve=curve,
    )
    result.stats = _compute_stats(trades, start_equity, equity, max_dd,
                                  enriched.index[start_i], enriched.index[-1])
    result.stats["ambiguous_exits"] = ambiguous
    return result


def _gap_fill(open_px: float, stop_px: float, long_pos: bool) -> float:
    """Stop-out fill price: if the bar GAPPED through the stop, you fill at the
    worse open, not the stop level."""
    if long_pos:
        return min(open_px, stop_px)
    return max(open_px, stop_px)


def run_backtest(symbol: str, settings: Settings | None = None,
                 source: OHLCVSource | None = None,
                 costs: CostModel | None = None,
                 allow_short: bool = True) -> BacktestResult:
    """Convenience: fetch data and backtest the swing strategy for one symbol."""
    settings = settings or Settings()
    source = source or get_source(settings.data_source, exchange=settings.exchange,
                                  directory=settings.csv_dir)
    df = source.get_history(symbol, interval=settings.swing_interval,
                            period=settings.swing_period)
    return backtest_swing(df, symbol, settings, costs, allow_short=allow_short)


def _compute_stats(trades, start_equity, final_equity, max_dd, start_dt, end_dt) -> dict:
    n = len(trades)
    if n == 0:
        return {"trades": 0, "final_equity": round(final_equity, 2),
                "start_equity": round(start_equity, 2)}

    wins = [t for t in trades if t.net_pnl > 0]
    losses = [t for t in trades if t.net_pnl <= 0]
    win_rate = len(wins) / n
    avg_win_r = sum(t.outcome_r for t in wins) / len(wins) if wins else 0.0
    avg_loss_r = abs(sum(t.outcome_r for t in losses) / len(losses)) if losses else 0.0
    gross_win = sum(t.net_pnl for t in wins)
    gross_loss = abs(sum(t.net_pnl for t in losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    total_return = (final_equity - start_equity) / start_equity
    years = max((end_dt - start_dt).days / 365.25, 0.01)
    cagr = (final_equity / start_equity) ** (1 / years) - 1 if final_equity > 0 else -1
    costs_paid = sum(t.costs for t in trades)
    exp_r = an.expectancy_r(win_rate, avg_win_r, avg_loss_r if avg_loss_r else 1.0)

    return {
        "trades": n,
        "win_rate": round(win_rate, 3),
        "avg_win_r": round(avg_win_r, 2),
        "avg_loss_r": round(avg_loss_r, 2),
        "expectancy_r": round(exp_r, 3),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else None,
        "total_return_pct": round(total_return * 100, 2),
        "cagr_pct": round(cagr * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "costs_paid": round(costs_paid, 2),
        "final_equity": round(final_equity, 2),
        "start_equity": round(start_equity, 2),
    }
