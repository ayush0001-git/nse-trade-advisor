"""
advisor.cli
===========
Command-line interface. Commands:

    analyze SYMBOL [--intraday] [--llm]   deep-dive one stock
    scan [--intraday] [--llm]             rank the whole watchlist
    backtest SYMBOL                       validate the swing strategy on history
    journal                               show your edge stats + open trades
    log SYMBOL ...                        record a trade you took
    close TRADE_ID EXIT_PRICE             close a logged trade
    news SYMBOL                           headlines + sentiment for a stock
    config                                print the active settings

All output is plain ASCII so it renders the same on Windows, macOS and Linux.
"""
from __future__ import annotations

import argparse

from .core import Settings, Style, TradeIdea, Verdict, load_settings
from .engine import Analyzer, run_backtest
from .extras import Journal, sentiment_for_symbol


BAR = "=" * 68
SUB = "-" * 68


# --------------------------------------------------------------------------- #
#  Pretty-printer
# --------------------------------------------------------------------------- #
def print_idea(idea: TradeIdea, verbose: bool = True) -> None:
    tag = {
        Verdict.TAKE: "[ TAKE ]", Verdict.WATCH: "[ WATCH ]",
        Verdict.AVOID: "[ AVOID ]", Verdict.NO_SETUP: "[ NO SETUP ]",
    }[idea.verdict]

    print("\n" + BAR)
    print(f"{tag}  {idea.symbol}   ({idea.style.value}, {idea.timeframe})")
    print(BAR)
    print(f"Direction   : {idea.direction.value.upper()}")
    print(f"Regime      : {idea.regime.value}")
    print(f"Evidence    : {idea.confidence:.0f}/100   {_conf_bar(idea.confidence)}  "
          f"(a ranking, NOT a win probability)")
    print(f"Confluence  : {idea.confluence_score:+.2f}  (weighted agreement, -1..+1)")
    if idea.expectancy_r is not None:
        print(f"Your edge   : {idea.expectancy_r:+.2f} R/trade (from your journal)")
    if idea.news_sentiment is not None:
        print(f"News mood   : {idea.news_sentiment:+.2f} (-1..+1)")

    p = idea.plan
    if p and idea.verdict in (Verdict.TAKE, Verdict.WATCH):
        print(SUB)
        print("THE PLAN")
        print(f"  Entry       : Rs. {p.entry:,.2f}")
        print(f"  Stop-loss   : Rs. {p.stop_loss:,.2f}   "
              f"(-{p.risk_per_share:,.2f}/sh, via {p.stop_method})")
        print(f"  Target      : Rs. {p.target:,.2f}   (+{p.reward_per_share:,.2f}/sh)")
        print(f"  Quantity    : {p.quantity} shares")
        print(f"  Risk:Reward : {p.risk_reward:.2f} : 1")
        print(f"  Capital risk: Rs. {p.rupees_at_risk:,.0f} at stop  "
              f"({p.risk_pct*100:.1f}% of Rs. {p.capital:,.0f})")
        if p.rupees_at_risk_worst > p.rupees_at_risk:
            print(f"  Worst case  : Rs. {p.rupees_at_risk_worst:,.0f} if the stop "
                  f"gaps/slips (buffer Rs.{p.gap_buffer:,.2f}/sh)")
        print(f"  Deploys     : Rs. {p.position_value:,.0f}  "
              f"({p.position_pct_of_capital:.0f}% of capital)")

    if verbose and idea.signals:
        bull = idea.bullish_signals
        bear = idea.bearish_signals
        if bull:
            print(SUB)
            print("FOR THE TRADE (+)")
            for s in bull[:6]:
                print(f"  + {s.note}")
        if bear:
            print(SUB)
            print("AGAINST THE TRADE (-)")
            for s in bear[:6]:
                print(f"  - {s.note}")

    if verbose and idea.scenarios:
        print(SUB)
        print("SCENARIOS (rough probabilities, not guarantees)")
        for sc in idea.scenarios:
            print(f"  {sc.name.upper():4} ~{sc.probability*100:2.0f}%  "
                  f"-> Rs. {sc.price_target:,.2f} ({sc.move_pct:+.1f}%)  {sc.rationale}")

    if idea.vetoes:
        print(SUB)
        print("RED SIGNALS")
        for v in idea.vetoes:
            mark = "!!" if v.severity == "hard" else "! "
            print(f"  {mark} ({v.severity}) {v.reason}")

    if verbose and idea.notes:
        seen = set()
        uniq = [n for n in idea.notes if not (n in seen or seen.add(n))]
        print(SUB)
        print("ANALYST NOTES")
        for n in uniq:
            print(f"  * {n}")

    if idea.narration:
        print(SUB)
        print("READ")
        for para in idea.narration.split("\n\n"):
            print(f"  {para}")

    print(BAR)


def _conf_bar(conf: float, width: int = 20) -> str:
    filled = int(round(width * max(0.0, min(conf, 100.0)) / 100.0))
    return "[" + "#" * filled + "." * (width - filled) + "]"


# --------------------------------------------------------------------------- #
#  Commands
# --------------------------------------------------------------------------- #
def cmd_analyze(args, settings) -> None:
    journal = Journal(settings.journal_path)
    agent = Analyzer(settings, journal=journal)
    style = Style.INTRADAY if args.intraday else Style.SWING
    idea = agent.analyze(args.symbol, style=style,
                         use_llm=True if args.llm else None)
    print_idea(idea)


def cmd_scan(args, settings) -> None:
    journal = Journal(settings.journal_path)
    agent = Analyzer(settings, journal=journal)
    style = Style.INTRADAY if args.intraday else Style.SWING
    print(f"\nScanning {len(settings.watchlist)} symbols ({style.value})...")

    def _progress(i, n, sym):
        disp = sym.split(".")[0]
        print(f"  [{i}/{n}] {disp}...", flush=True)

    ideas = agent.scan(style=style, progress=_progress)

    print("\n" + BAR)
    print(f"{'SYMBOL':<14}{'VERDICT':<11}{'DIR':<7}{'CONF':>5}{'R:R':>7}"
          f"{'ENTRY':>11}{'STOP':>11}{'TARGET':>11}")
    print(SUB)
    for idea in ideas:
        p = idea.plan
        entry = f"{p.entry:,.1f}" if p else "-"
        stop = f"{p.stop_loss:,.1f}" if p else "-"
        target = f"{p.target:,.1f}" if p else "-"
        rr = f"{p.risk_reward:.1f}" if p else "-"
        disp = idea.symbol.split(".")[0]
        print(f"{disp:<14}{idea.verdict.value:<11}"
              f"{idea.direction.value[:5]:<7}{idea.confidence:>5.0f}{rr:>7}"
              f"{entry:>11}{stop:>11}{target:>11}")
    print(BAR)

    takes = [i for i in ideas if i.verdict == Verdict.TAKE]
    if takes:
        print(f"\n{len(takes)} TAKE candidate(s). Showing the top one in detail:")
        print_idea(takes[0])
    else:
        print("\nNo TAKE candidates right now. Patience is a position.")

    failures = getattr(agent, "scan_failures", [])
    if failures:
        print(SUB)
        print(f"{len(failures)} symbol(s) could not be analyzed:")
        for sym, err in failures:
            print(f"  ! {sym}: {err}")


def cmd_backtest(args, settings) -> None:
    print(f"\nBacktesting {args.symbol} (swing, this may take a moment)...")
    result = run_backtest(args.symbol, settings)
    print("\n" + BAR)
    print(result.summary())
    print(BAR)
    if result.trades:
        print("\nLast 5 trades:")
        for t in result.trades[-5:]:
            print(f"  {t.entry_date:%Y-%m-%d} -> {t.exit_date:%Y-%m-%d}  "
                  f"{t.quantity}sh @ {t.entry:.1f}->{t.exit:.1f}  "
                  f"{t.outcome_r:+.2f}R  Rs.{t.net_pnl:+,.0f}  ({t.reason})")
    print("\nReminder: backtests overstate live results. Paper-trade before going live.")


def cmd_journal(args, settings) -> None:
    j = Journal(settings.journal_path)
    stats = j.stats()
    print("\n" + BAR)
    print("TRADE JOURNAL")
    print(BAR)
    print(f"Closed trades : {stats['closed_trades']}")
    if stats["closed_trades"]:
        print(f"Win rate      : {stats['win_rate']*100:.1f}%")
        print(f"Avg win/loss  : +{stats['avg_win_r']}R / -{stats['avg_loss_r']}R")
        print(f"Payoff (b)    : {stats['payoff_b']}")
        print(f"Expectancy    : {stats['expectancy_r']:+.3f} R/trade")
        print(f"Total P&L     : Rs. {stats['total_pnl']:,.2f}")
        if stats["kelly_quarter"] is not None:
            print(f"1/4-Kelly size: {stats['kelly_quarter']*100:.2f}% of capital/trade")
    print(f"\n{stats['message']}")

    opens = j.open_trades()
    if opens:
        print(SUB)
        print("OPEN TRADES")
        for o in opens:
            print(f"  #{o['id']:<3} {o['symbol']:<14} {o['direction']:<5} "
                  f"qty {o['quantity']}  entry {o['entry']:.1f}  "
                  f"stop {o['stop']:.1f}  target {o['target']:.1f}")
        print("\nClose one with:  python run.py close <id> <exit_price>")
    print(BAR)


def cmd_log(args, settings) -> None:
    """Re-analyze and log the resulting plan as a taken trade."""
    j = Journal(settings.journal_path)
    agent = Analyzer(settings, journal=j)
    style = Style.INTRADAY if args.intraday else Style.SWING
    idea = agent.analyze(args.symbol, style=style)
    if idea.plan is None or idea.plan.quantity <= 0:
        print(f"No tradeable plan for {args.symbol} right now - nothing logged.")
        return
    tid = j.log_idea(idea, notes=args.note or "")
    print(f"Logged trade #{tid}: {idea.symbol} {idea.direction.value} "
          f"{idea.plan.quantity}sh @ {idea.plan.entry} "
          f"(stop {idea.plan.stop_loss}, target {idea.plan.target}).")
    print("When you exit, run:  python run.py close "
          f"{tid} <exit_price>")


def cmd_close(args, settings) -> None:
    j = Journal(settings.journal_path)
    res = j.close_trade(args.trade_id, args.exit_price, notes=args.note or "")
    print(f"Closed trade #{res['id']}: {res['outcome_r']:+.2f}R, "
          f"P&L Rs.{res['pnl']:+,.2f}")


def cmd_news(args, settings) -> None:
    score, headlines = sentiment_for_symbol(settings.news_feeds, args.symbol)
    print("\n" + BAR)
    print(f"NEWS: {args.symbol}")
    print(BAR)
    if not headlines:
        print("No matching headlines (feedparser may be missing, or no recent news).")
        print("Install with:  pip install feedparser")
    else:
        print(f"Sentiment: {score:+.2f} (-1..+1) across {len(headlines)} headlines\n")
        for h in headlines:
            print(f"  - {h}")
    print(BAR)


def cmd_config(args, settings) -> None:
    print("\n" + BAR)
    print("ACTIVE SETTINGS")
    print(BAR)
    for k, v in settings.to_dict().items():
        print(f"  {k:<20}: {v}")
    print(BAR)


def cmd_version(args, settings) -> None:
    from advisor import __version__
    print(f"\nadvisor version {__version__}")
    print("Verify your build: this version ships 1 merged test file (tests/test_all.py).")
    print("Run  pytest tests/  (or python tests/test_all.py) to confirm.\n")


# --------------------------------------------------------------------------- #
#  Argument parser
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="advisor",
        description="Local advisory-only AI trading assistant for NSE/BSE. "
                    "It tells you what it sees - it never places orders.")
    p.add_argument("--config", default="config.yaml", help="path to config.yaml")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="deep-dive one stock")
    a.add_argument("symbol")
    a.add_argument("--intraday", action="store_true")
    a.add_argument("--llm", action="store_true", help="force LLM narration")
    a.set_defaults(func=cmd_analyze)

    sc = sub.add_parser("scan", help="rank the watchlist")
    sc.add_argument("--intraday", action="store_true")
    sc.add_argument("--llm", action="store_true")
    sc.set_defaults(func=cmd_scan)

    bt = sub.add_parser("backtest", help="validate the swing strategy on history")
    bt.add_argument("symbol")
    bt.set_defaults(func=cmd_backtest)

    jn = sub.add_parser("journal", help="show edge stats and open trades")
    jn.set_defaults(func=cmd_journal)

    lg = sub.add_parser("log", help="log a trade you took (re-analyzes now)")
    lg.add_argument("symbol")
    lg.add_argument("--intraday", action="store_true")
    lg.add_argument("--note", default="")
    lg.set_defaults(func=cmd_log)

    cl = sub.add_parser("close", help="close a logged trade")
    cl.add_argument("trade_id", type=int)
    cl.add_argument("exit_price", type=float)
    cl.add_argument("--note", default="")
    cl.set_defaults(func=cmd_close)

    nw = sub.add_parser("news", help="headlines + sentiment for a stock")
    nw.add_argument("symbol")
    nw.set_defaults(func=cmd_news)

    cf = sub.add_parser("config", help="print active settings")
    cf.set_defaults(func=cmd_config)

    ve = sub.add_parser("version", help="print the version (to confirm your build)")
    ve.set_defaults(func=cmd_version)
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.config)
        args.func(args, settings)
    except ValueError as e:
        print(f"\nConfiguration / input error:\n{e}\n")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(130)
