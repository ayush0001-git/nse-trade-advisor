"""
mass_backtest.py - Run 1000+ backtest episodes to validate the system.

Runs:
  1. RL agent: 1000 episodes across 15 stocks on random 6-12 month windows
  2. Each of 16 strategies: 1000 episodes each (16,000 total strategy episodes)

Total: 17,000 backtest episodes.

The script is resumable - it appends to existing results and saves progress
every 50 episodes, so you can stop and restart without losing work.

Usage:
    # Run everything (takes ~2-3 hours on CPU)
    python mass_backtest.py --all

    # Run just the RL backtest (1000 episodes, ~1 hour)
    python mass_backtest.py --rl --episodes 1000

    # Run just the strategy backtests (16000 episodes, ~1 hour)
    python mass_backtest.py --strategies

    # Run a smaller batch for testing
    python mass_backtest.py --all --episodes 100
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from rl_agent import (
    MODEL_PATH, RESULTS_PATH as RL_RESULTS_PATH, BACKTEST_STOCKS,
    IndianCostModel, NSETradingEnv, build_features, fetch_stock_data,
)
from strategies import (
    STRATEGIES, StrategyBacktest, RESULTS_PATH as STRAT_RESULTS_PATH,
    fetch_stock_data as fetch_stock_data_strat,
)


def _load_rl_results():
    if RL_RESULTS_PATH.exists():
        with open(RL_RESULTS_PATH) as f:
            return json.load(f)
    return {"episodes": [], "summary": {}}


def _save_rl_results(data):
    with open(RL_RESULTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _load_strat_results():
    if STRAT_RESULTS_PATH.exists():
        with open(STRAT_RESULTS_PATH) as f:
            return json.load(f)
    return {"strategies": {}}


def _save_strat_results(data):
    with open(STRAT_RESULTS_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)


def run_rl_backtest(target_episodes: int = 1000, batch_size: int = 50):
    """Run RL agent backtests until we hit target_episodes total."""
    from stable_baselines3 import PPO

    print(f"\n{'='*70}")
    print(f"  RL Agent Mass Backtest (target: {target_episodes} episodes)")
    print(f"{'='*70}\n")

    if not MODEL_PATH.exists():
        print("ERROR: RL model not trained. Run: python rl_agent.py train --timesteps 100000")
        return

    model = PPO.load(MODEL_PATH, device="cpu")
    cost_model = IndianCostModel()

    # Fetch all stock data once
    print("Fetching stock data...")
    stock_data = {}
    for sym in BACKTEST_STOCKS:
        try:
            df = fetch_stock_data(sym, period="5y")
            stock_data[sym] = df
        except Exception as e:
            print(f"  ! {sym}: {e}")
    print(f"  Got {len(stock_data)} stocks")

    # Load existing results
    data = _load_rl_results()
    existing = data.get("episodes", [])
    starting_count = len(existing)
    print(f"Starting with {starting_count} existing episodes")

    # Run in batches
    batch_num = 0
    while len(existing) < target_episodes:
        batch_num += 1
        this_batch = min(batch_size, target_episodes - len(existing))
        print(f"\n--- Batch {batch_num}: {this_batch} episodes "
              f"(total: {len(existing) + this_batch}/{target_episodes}) ---")

        for i in range(this_batch):
            symbol = random.choice(list(stock_data.keys()))
            df = stock_data[symbol]
            features = build_features(df)

            window_size = random.randint(120, min(252, len(df) - 60))
            start_idx = random.randint(60, len(df) - window_size - 5)
            end_idx = start_idx + window_size

            env = NSETradingEnv(df, features, start_idx=start_idx, end_idx=end_idx,
                                cost_model=cost_model)
            obs, info = env.reset()

            total_reward = 0
            done = False
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                total_reward += reward
                done = terminated or truncated

            final_nw = info["net_worth"]
            initial = env.initial_balance
            return_pct = (final_nw - initial) / initial * 100

            trades = env.trade_history
            n_trades = len(trades)
            wins = [t for t in trades if t["pnl"] > 0]
            losses = [t for t in trades if t["pnl"] <= 0]
            win_rate = len(wins) / n_trades if n_trades > 0 else 0
            profit_factor = (sum(t["pnl"] for t in wins) / abs(sum(t["pnl"] for t in losses))
                             if losses and sum(t["pnl"] for t in losses) != 0 else 0)

            peak = np.maximum.accumulate(env.net_worth_history)
            dd = (peak - env.net_worth_history) / peak
            max_dd = np.max(dd) * 100 if len(dd) > 0 else 0

            bh_start = float(df["close"].iloc[start_idx])
            bh_end = float(df["close"].iloc[end_idx])
            bh_return = (bh_end - bh_start) / bh_start * 100

            existing.append({
                "episode": len(existing) + 1,
                "symbol": symbol,
                "window_days": window_size,
                "start_date": str(df.index[start_idx].date()),
                "end_date": str(df.index[end_idx].date()),
                "initial_balance": initial,
                "final_net_worth": round(final_nw, 2),
                "return_pct": round(return_pct, 2),
                "buy_hold_return_pct": round(bh_return, 2),
                "alpha_vs_buy_hold": round(return_pct - bh_return, 2),
                "n_trades": n_trades,
                "win_rate": round(win_rate * 100, 1),
                "profit_factor": round(profit_factor, 2),
                "max_drawdown_pct": round(max_dd, 2),
                "total_reward": round(total_reward, 3),
            })

        # Update summary and save progress
        returns = [r["return_pct"] for r in existing]
        alphas = [r["alpha_vs_buy_hold"] for r in existing]
        win_rates = [r["win_rate"] for r in existing]
        pfs = [r["profit_factor"] for r in existing if r["profit_factor"] > 0]
        dds = [r["max_drawdown_pct"] for r in existing]

        data["episodes"] = existing
        data["summary"] = {
            "episodes": len(existing),
            "stocks_tested": len(set(r["symbol"] for r in existing)),
            "avg_return_pct": round(np.mean(returns), 2),
            "median_return_pct": round(np.median(returns), 2),
            "std_return_pct": round(np.std(returns), 2),
            "min_return_pct": round(min(returns), 2),
            "max_return_pct": round(max(returns), 2),
            "avg_alpha_vs_buy_hold": round(np.mean(alphas), 2),
            "win_rate_episodes": round(np.mean([1 if r > 0 else 0 for r in returns]) * 100, 1),
            "avg_trade_win_rate": round(np.mean(win_rates), 1),
            "avg_profit_factor": round(np.mean(pfs), 2) if pfs else 0,
            "avg_max_drawdown_pct": round(np.mean(dds), 2),
            "avg_trades_per_episode": round(np.mean([r["n_trades"] for r in existing]), 1),
        }
        _save_rl_results(data)

        s = data["summary"]
        print(f"  Progress: {s['episodes']} episodes | "
              f"avg_ret {s['avg_return_pct']:+.2f}% | "
              f"alpha {s['avg_alpha_vs_buy_hold']:+.2f}% | "
              f"win_eps {s['win_rate_episodes']}% | "
              f"PF {s['avg_profit_factor']}")

    print(f"\n{'='*70}")
    print(f"  RL BACKTEST COMPLETE: {len(existing)} episodes")
    print(f"{'='*70}")
    s = data["summary"]
    print(f"  Avg return:         {s['avg_return_pct']:+.2f}%")
    print(f"  Median return:      {s['median_return_pct']:+.2f}%")
    print(f"  Std dev:            {s['std_return_pct']:.2f}%")
    print(f"  Min / Max:          {s['min_return_pct']:+.2f}% / {s['max_return_pct']:+.2f}%")
    print(f"  Avg alpha vs B&H:   {s['avg_alpha_vs_buy_hold']:+.2f}%")
    print(f"  Episodes profitable:{s['win_rate_episodes']}%")
    print(f"  Avg trade win rate: {s['avg_trade_win_rate']}%")
    print(f"  Avg profit factor:  {s['avg_profit_factor']}")
    print(f"  Avg max drawdown:   {s['avg_max_drawdown_pct']:.2f}%")
    print(f"  Stocks tested:      {s['stocks_tested']}")


def run_strategy_backtests(target_episodes_per_strategy: int = 1000,
                            batch_size: int = 50):
    """Run each strategy on enough stock/window combos to hit target."""
    print(f"\n{'='*70}")
    print(f"  Strategy Lab Mass Backtest")
    print(f"  ({len(STRATEGIES)} strategies x {target_episodes_per_strategy} episodes each")
    print(f"   = {len(STRATEGIES) * target_episodes_per_strategy} total episodes)")
    print(f"{'='*70}\n")

    # Fetch all stock data once
    stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
              "SBIN.NS", "ITC.NS", "LT.NS", "HINDUNILVR.NS", "BHARTIARTL.NS",
              "WIPRO.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "TATAMOTORS.NS"]
    print("Fetching stock data...")
    stock_data = {}
    for sym in stocks:
        try:
            df = fetch_stock_data_strat(sym, period="5y")
            stock_data[sym] = df
        except Exception as e:
            print(f"  ! {sym}: {e}")
    print(f"  Got {len(stock_data)} stocks")

    # Fetch NIFTY for dual momentum
    try:
        nifty = fetch_stock_data_strat("^NSEI", period="5y")
    except Exception:
        nifty = None

    # Load existing results
    data = _load_strat_results()
    if "strategies" not in data:
        data["strategies"] = {}

    # For each strategy, run episodes until target is met
    for strat_key, strat_meta in STRATEGIES.items():
        if strat_key not in data["strategies"]:
            data["strategies"][strat_key] = {
                "name": strat_meta["name"],
                "description": strat_meta["description"],
                "source": strat_meta["source"],
                "stock_results": [],
                "summary": {},
            }
        existing = data["strategies"][strat_key].get("stock_results", [])
        starting_count = len(existing)

        if starting_count >= target_episodes_per_strategy:
            print(f"  [{strat_key}] already has {starting_count} episodes, skipping")
            continue

        print(f"\n  Strategy: {strat_meta['name']} ({starting_count}/{target_episodes_per_strategy})")

        batch_num = 0
        while len(existing) < target_episodes_per_strategy:
            batch_num += 1
            this_batch = min(batch_size, target_episodes_per_strategy - len(existing))

            for _ in range(this_batch):
                symbol = random.choice(list(stock_data.keys()))
                df = stock_data[symbol]

                # Pick a random window
                window_size = random.randint(120, min(252, len(df) - 60))
                start_idx = random.randint(60, len(df) - window_size - 5)
                end_idx = start_idx + window_size
                window = df.iloc[start_idx:end_idx + 1]

                try:
                    bt = StrategyBacktest(strategy_name=strat_key, symbol=symbol)
                    nifty_arg = nifty if strat_meta["needs_nifty"] else None
                    result = bt.run(window, strat_meta["signal_fn"], nifty_arg)
                    # Don't store all trades in the mass results (too big)
                    result["trades"] = result["trades"][-3:]  # keep last 3 only
                    result["window_start"] = str(df.index[start_idx].date())
                    result["window_end"] = str(df.index[end_idx].date())
                    existing.append(result)
                except Exception as e:
                    pass  # skip bad windows

            # Update summary
            data["strategies"][strat_key]["stock_results"] = existing
            data["strategies"][strat_key]["summary"] = _summarize(existing)
            _save_strat_results(data)

            s = data["strategies"][strat_key]["summary"]
            print(f"    batch {batch_num}: {len(existing)}/{target_episodes_per_strategy} | "
                  f"avg_ret {s['avg_return_pct']:+.2f}% | "
                  f"alpha {s['avg_alpha_vs_bh']:+.2f}% | "
                  f"win {s['avg_win_rate']}% | "
                  f"PF {s['avg_profit_factor']}")

    # Print final summary
    print(f"\n{'='*70}")
    print("  STRATEGY LAB MASS BACKTEST COMPLETE")
    print(f"{'='*70}")
    print(f"  {'Strategy':<28} {'Episodes':>8} {'Avg Ret':>9} {'Alpha':>9} "
          f"{'Win%':>6} {'PF':>5}")
    print(f"  {'-'*70}")
    for key, strat in data["strategies"].items():
        s = strat.get("summary", {})
        n = len(strat.get("stock_results", []))
        if s:
            print(f"  {strat['name']:<28} {n:>8} {s['avg_return_pct']:>+8.2f}% "
                  f"{s['avg_alpha_vs_bh']:>+8.2f}% {s['avg_win_rate']:>5.1f}% "
                  f"{s['avg_profit_factor']:>5.2f}")
        else:
            print(f"  {strat['name']:<28} {n:>8} (no data)")


def _summarize(results):
    if not results:
        return {}
    returns = [r["return_pct"] for r in results]
    alphas = [r["alpha_vs_buy_hold"] for r in results]
    win_rates = [r["win_rate_pct"] for r in results]
    pfs = [r["profit_factor"] for r in results if r["profit_factor"] > 0]
    n_trades = [r["n_trades"] for r in results]
    dds = [r["max_drawdown_pct"] for r in results]
    return {
        "n_stocks": len(results),
        "avg_return_pct": round(np.mean(returns), 2),
        "median_return_pct": round(np.median(returns), 2),
        "std_return_pct": round(np.std(returns), 2),
        "min_return_pct": round(min(returns), 2),
        "max_return_pct": round(max(returns), 2),
        "avg_alpha_vs_bh": round(np.mean(alphas), 2),
        "avg_win_rate": round(np.mean(win_rates), 1),
        "avg_profit_factor": round(np.mean(pfs), 2) if pfs else 0,
        "avg_n_trades": round(np.mean(n_trades), 1),
        "avg_max_drawdown_pct": round(np.mean(dds), 2),
        "stocks_profitable": round(np.mean([1 if r > 0 else 0 for r in returns]) * 100, 1),
        "stocks_beating_buyhold": round(np.mean([1 if a > 0 else 0 for a in alphas]) * 100, 1),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Mass backtest 1000+ episodes")
    ap.add_argument("--all", action="store_true", help="Run both RL and strategies")
    ap.add_argument("--rl", action="store_true", help="Run only RL backtest")
    ap.add_argument("--strategies", action="store_true", help="Run only strategy backtests")
    ap.add_argument("--episodes", type=int, default=1000,
                    help="Target episodes per category (default 1000)")
    ap.add_argument("--batch", type=int, default=50,
                    help="Batch size for progress saves (default 50)")
    args = ap.parse_args()

    if args.all or args.rl:
        run_rl_backtest(target_episodes=args.episodes, batch_size=args.batch)
    if args.all or args.strategies:
        run_strategy_backtests(target_episodes_per_strategy=args.episodes,
                                batch_size=args.batch)
