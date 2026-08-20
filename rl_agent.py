"""
rl_agent.py - Reinforcement Learning trading agent adapted for the Indian market.

This module trains a PPO (Proximal Policy Optimization) agent specifically for
NSE/BSE stocks, with the following Indian-market adaptations:

  1. INDIAN COST MODEL
     - STT 0.1% on sell (delivery) / 0.025% (intraday)
     - Stamp duty 0.015% on buy (delivery) / 0.003% (intraday)
     - Exchange txn 0.00345% per side
     - GST 18% on (brokerage + exchange)
     - SEBI fee Rs 10/crore
     - Brokerage 0.03% (capped Rs 20) for intraday, 0 for delivery
     - Slippage 0.05% per side

  2. REGIME-AWARE REWARD
     - Uses the advisor's regime classifier (trending/ranging/volatile)
     - Penalizes counter-trend trades
     - Rewards regime-aligned entries

  3. RISK MANAGEMENT IN THE ENVIRONMENT
     - ATR-based stop-loss (2x ATR, like the advisor)
     - Position sizing capped at 25% of capital per trade
     - Reward includes risk-adjusted return (Sharpe-like)

  4. MULTI-STOCK TRAINING
     - Trains across 10 liquid NSE stocks simultaneously
     - Each episode randomly picks a stock and a 1-year window
     - This prevents overfitting to a single stock's pattern

Usage:
    # Train a new agent (CPU ~30 min for 100k steps)
    python rl_agent.py train --timesteps 100000

    # Run 100+ backtesting episodes
    python rl_agent.py backtest --episodes 100

    # Get a prediction for a single stock
    python rl_agent.py predict RELIANCE.NS

    # Compare RL agent vs advisor strategy
    python rl_agent.py compare
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import random
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback

from advisor.core import Settings, Direction, Regime
from advisor import analysis as an
from advisor.analysis import triple_barrier_labels

# Paths
MODELS_DIR = PROJECT_ROOT / "rl_models"
MODELS_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODELS_DIR / "nse_ppo_agent.zip"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
TRAIN_DATA_DIR = MODELS_DIR / "train_data"
TRAIN_DATA_DIR.mkdir(exist_ok=True)
RESULTS_PATH = MODELS_DIR / "backtest_results.json"

# 10 liquid NSE stocks for training (diversified across sectors)
TRAIN_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "ITC.NS", "LT.NS", "HINDUNILVR.NS", "BHARTIARTL.NS",
]

# Backtest stocks (includes the train stocks + 5 held-out for generalization test)
BACKTEST_STOCKS = TRAIN_STOCKS + [
    "WIPRO.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "TATAMOTORS.NS",
]

# Feature columns the agent sees (must match between training and inference)
FEATURE_COLS = [
    # Price action (normalized)
    "open_norm", "high_norm", "low_norm", "close_norm", "volume_norm",
    # Moving averages (normalized as % from close)
    "sma_20_pct", "sma_50_pct", "sma_200_pct", "ema_20_pct",
    # Momentum
    "rsi_14_norm", "macd_norm", "macd_signal_norm", "macd_hist_norm",
    # Volatility
    "bb_upper_pct", "bb_lower_pct", "bb_width_norm", "atr_pct_norm",
    # Trend strength
    "adx_14_norm", "plus_di_norm", "minus_di_norm",
    # Volume
    "volume_ratio", "obv_norm",
    # Regime (one-hot encoded)
    "regime_trending_up", "regime_trending_down", "regime_ranging",
    "regime_volatile", "regime_unknown",
    # Portfolio state
    "position_pct", "pnl_pct", "days_held_norm",
]
N_FEATURES = len(FEATURE_COLS)
LOOKBACK = 30  # 30-day observation window


# =========================================================================== #
#  Indian cost model (delivery + intraday)
# =========================================================================== #
@dataclass
class IndianCostModel:
    """Representative round-trip frictions for NSE/BSE equities."""
    brokerage_pct: float = 0.0003       # 0.03% intraday (delivery = 0)
    brokerage_cap: float = 20.0         # Rs cap per side
    stt_sell_pct: float = 0.00025       # 0.025% intraday sell
    exch_txn_pct: float = 0.0000345     # NSE transaction per side
    gst_pct: float = 0.18               # on (brokerage + exchange)
    sebi_pct: float = 0.000001          # Rs 10/crore
    stamp_buy_pct: float = 0.00003      # 0.003% intraday buy
    slippage_pct: float = 0.0005        # 0.05% per side

    def round_trip_cost_pct(self) -> float:
        """Total round-trip cost as a fraction of trade value."""
        # Brokerage (capped) on a Rs 10,000 trade ~ 0.2% both sides worst case,
        # but typically 0.03% intraday. We use the typical case.
        b = min(self.brokerage_pct, self.brokerage_cap / 10000) * 2
        return (b + self.stt_sell_pct + self.exch_txn_pct * 2 +
                b * self.gst_pct + self.sebi_pct * 2 +
                self.stamp_buy_pct + self.slippage_pct * 2)

    def cost_for_value(self, value: float, is_buy: bool) -> float:
        """Compute the actual cost in rupees for a trade of `value`."""
        b = min(value * self.brokerage_pct, self.brokerage_cap)
        txn = value * self.exch_txn_pct
        gst = (b + txn) * self.gst_pct
        sebi = value * self.sebi_pct
        stamp = value * self.stamp_buy_pct if is_buy else 0
        stt = 0 if is_buy else value * self.stt_sell_pct
        slip = value * self.slippage_pct
        return b + txn + gst + sebi + stamp + stt + slip


# =========================================================================== #
#  Feature engineering
# =========================================================================== #
def fetch_stock_data(symbol: str, period: str = "5y") -> pd.DataFrame:
    """Fetch OHLCV data from yfinance and compute indicators."""
    cache_path = TRAIN_DATA_DIR / f"{symbol.replace('.', '_')}.csv"
    if cache_path.exists():
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        if len(df) >= 200:
            return df

    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval="1d", auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"No data for {symbol}")
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df = df.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume",
    })
    df = df[["open", "high", "low", "close", "volume"]].dropna()

    # Compute indicators
    df = an.compute_indicators(df, include_vwap=False)
    df.to_csv(cache_path)
    return df


def label_bars_with_triple_barrier(df: pd.DataFrame,
                                   tp_atr: float = 5.0,
                                   sl_atr: float = 2.0,
                                   hold: int = 10) -> pd.Series:
    """Compute triple-barrier labels for each bar (long-direction).

    Uses ``advisor.analysis.triple_barrier_labels`` under the hood. The
    returned Series is aligned to ``df.index`` with values in ``{+1, 0, -1}``:

      * ``+1`` -> would have hit the take-profit barrier
      * ``-1`` -> would have hit the stop-loss barrier
      * ``0``  -> timed out (or no forward data / invalid ATR)

    This is used by ``NSETradingEnv`` to shape the reward: a BUY action on a
    +1 bar earns a small bonus; a BUY on a -1 bar earns a small penalty.
    ``df`` must have an ``atr_14`` column (added by ``compute_indicators``).
    """
    if "atr_14" not in df.columns:
        raise ValueError("df must include 'atr_14' (call compute_indicators first)")
    lbl = triple_barrier_labels(
        prices=df["close"],
        take_profit_atr=tp_atr,
        stop_loss_atr=sl_atr,
        max_hold_bars=hold,
        atr_series=df["atr_14"],
        direction="long",
    )
    return lbl["label"].astype(int)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the feature matrix the RL agent sees.

    All features are normalized to be roughly in [-1, 1] or [0, 1] so the
    neural network can learn stably across stocks of very different prices.
    """
    out = pd.DataFrame(index=df.index)

    # Normalize OHLCV by the 50-day SMA (so a Rs 100 stock and a Rs 10000
    # stock look the same to the network).
    sma50 = df["sma_50"].fillna(df["close"])
    for col in ["open", "high", "low", "close"]:
        out[f"{col}_norm"] = df[col] / sma50 - 1.0
    # Volume normalized by its 50-day average
    vol_avg = df["volume"].rolling(50, min_periods=1).mean()
    out["volume_norm"] = df["volume"] / vol_avg.replace(0, 1) - 1.0

    # MAs as % from close
    for col, name in [("sma_20", "sma_20_pct"), ("sma_50", "sma_50_pct"),
                      ("sma_200", "sma_200_pct"), ("ema_20", "ema_20_pct")]:
        out[name] = (df[col] - df["close"]) / df["close"].replace(0, 1)

    # RSI normalized to [-1, 1]
    out["rsi_14_norm"] = (df["rsi_14"] - 50) / 50

    # MACD normalized by close
    out["macd_norm"] = df["macd"] / df["close"].replace(0, 1)
    out["macd_signal_norm"] = df["macd_signal"] / df["close"].replace(0, 1)
    out["macd_hist_norm"] = df["macd_hist"] / df["close"].replace(0, 1)

    # Bollinger Bands as % from close
    out["bb_upper_pct"] = (df["bb_upper"] - df["close"]) / df["close"].replace(0, 1)
    out["bb_lower_pct"] = (df["bb_lower"] - df["close"]) / df["close"].replace(0, 1)
    out["bb_width_norm"] = df["bb_width"].clip(0, 1)
    out["atr_pct_norm"] = (df["atr_pct"] - 0.02).clip(-0.05, 0.10) / 0.05

    # ADX / DI normalized to [0, 1]
    out["adx_14_norm"] = df["adx_14"] / 100
    out["plus_di_norm"] = df["plus_di"] / 100
    out["minus_di_norm"] = df["minus_di"] / 100

    # Volume ratio (today / 20-day avg)
    out["volume_ratio"] = (df["volume"] / df["avg_volume_20"].replace(0, 1)).clip(0, 5) - 1
    # OBV normalized by 50-day average volume
    obv_norm = df["obv"] / (vol_avg * 50).replace(0, 1)
    out["obv_norm"] = obv_norm.clip(-1, 1)

    # Regime one-hot encoding (computed per-bar to avoid look-ahead)
    regimes = []
    for i in range(len(df)):
        sub = df.iloc[:i+1]
        if len(sub) < 30:
            regimes.append(Regime.UNKNOWN)
        else:
            try:
                regimes.append(an.classify_regime(sub).regime)
            except Exception:
                regimes.append(Regime.UNKNOWN)
    regime_series = pd.Series(regimes, index=df.index)
    for reg in [Regime.TRENDING_UP, Regime.TRENDING_DOWN, Regime.RANGING,
                Regime.VOLATILE, Regime.UNKNOWN]:
        out[f"regime_{reg.value}"] = (regime_series == reg).astype(float)

    # Portfolio state (filled in by the environment)
    out["position_pct"] = 0.0
    out["pnl_pct"] = 0.0
    out["days_held_norm"] = 0.0

    # Fill any NaN with 0
    out = out.fillna(0)
    return out


# =========================================================================== #
#  Indian-market trading environment
# =========================================================================== #
class NSETradingEnv(gym.Env):
    """Custom Gymnasium environment for NSE/BSE stock trading.

    The agent observes a LOOKBACK-day window of features and chooses:
      action[0] (discrete): 0=Hold, 1=Buy, 2=Sell
      action[1] (continuous, [0,1]): position size as fraction of capital

    Reward = risk-adjusted daily return - transaction costs - counter-trend penalty.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, df: pd.DataFrame, features: pd.DataFrame,
                 initial_balance: float = 100_000,
                 max_position_pct: float = 0.25,
                 atr_mult: float = 2.0,
                 cost_model: IndianCostModel | None = None,
                 start_idx: int | None = None,
                 end_idx: int | None = None,
                 tb_labels: Optional[pd.Series] = None,
                 tb_reward_scale: float = 0.005):
        super().__init__()
        self.df = df
        self.features = features
        self.initial_balance = initial_balance
        self.max_position_pct = max_position_pct
        self.atr_mult = atr_mult
        self.cost_model = cost_model or IndianCostModel()
        # Optional triple-barrier labels for reward shaping.
        # Aligned to df.index; values in {+1, 0, -1}.
        self.tb_labels = tb_labels.reindex(df.index) if tb_labels is not None else None
        self.tb_reward_scale = float(tb_reward_scale)

        # Episode window (random slice if not specified)
        n = len(df)
        self.start_idx = start_idx or max(LOOKBACK + 10, 60)
        self.end_idx = end_idx or n - 5
        if self.end_idx <= self.start_idx + 20:
            self.end_idx = min(n - 5, self.start_idx + 100)

        # Action space: Box([0, 0], [2, 1]) - action_type in [0,2], size in [0,1]
        # We discretize action_type in the step() function.
        self.action_space = spaces.Box(low=np.array([0.0, 0.0]),
                                       high=np.array([2.0, 1.0]),
                                       dtype=np.float32)
        # Observation: LOOKBACK x N_FEATURES
        self.observation_space = spaces.Box(
            low=-5, high=5, shape=(LOOKBACK, N_FEATURES), dtype=np.float32
        )

        # State
        self.reset()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        # Pick a random window if not fixed
        if options and "start_idx" in options:
            self.current_start = options["start_idx"]
            self.current_end = options.get("end_idx", min(len(self.df) - 5,
                                                          self.current_start + 200))
        else:
            window_size = random.randint(60, min(252, self.end_idx - self.start_idx))
            self.current_start = random.randint(self.start_idx, self.end_idx - window_size)
            self.current_end = self.current_start + window_size

        self.current_step = self.current_start
        self.balance = self.initial_balance
        self.position = 0  # number of shares held
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.entry_step = 0
        self.net_worth_history = [self.initial_balance]
        self.trade_history = []
        self.peak_net_worth = self.initial_balance
        return self._get_obs(), self._get_info()

    def _get_obs(self) -> np.ndarray:
        """Return the LOOKBACK-day feature window ending at current_step."""
        start = max(self.current_start, self.current_step - LOOKBACK + 1)
        end = self.current_step + 1
        window = self.features.iloc[start:end].copy()

        # Update portfolio state in the features
        current_price = float(self.df["close"].iloc[self.current_step])
        if self.position > 0:
            position_value = self.position * current_price
            position_pct = position_value / (self.balance + position_value)
            pnl_pct = (current_price - self.entry_price) / self.entry_price
            days_held = (self.current_step - self.entry_step) / 30  # normalize to ~1 month
        else:
            position_pct = 0.0
            pnl_pct = 0.0
            days_held = 0.0
        window["position_pct"] = position_pct
        window["pnl_pct"] = pnl_pct
        window["days_held_norm"] = min(days_held, 1.0)

        # Pad if shorter than LOOKBACK
        if len(window) < LOOKBACK:
            pad = pd.DataFrame(0, index=range(LOOKBACK - len(window)),
                               columns=window.columns)
            window = pd.concat([pad, window], ignore_index=True)
        return window[FEATURE_COLS].values.astype(np.float32)

    def _get_info(self) -> dict:
        current_price = float(self.df["close"].iloc[self.current_step])
        net_worth = self.balance + self.position * current_price
        return {
            "step": self.current_step,
            "balance": self.balance,
            "position": self.position,
            "current_price": current_price,
            "net_worth": net_worth,
        }

    def step(self, action):
        action_type = int(np.clip(round(action[0]), 0, 2))
        position_size = float(np.clip(action[1], 0, 1))

        current_price = float(self.df["close"].iloc[self.current_step])
        atr = float(self.df["atr_14"].iloc[self.current_step]) if not pd.isna(
            self.df["atr_14"].iloc[self.current_step]) else current_price * 0.02

        prev_net_worth = self.balance + self.position * current_price

        # ---- Execute the action ------------------------------------------- #
        cost_paid = 0.0
        # Triple-barrier reward shaping (small, additive; see label_bars_with_triple_barrier)
        tb_bonus = 0.0
        if self.tb_labels is not None and action_type == 1 and self.position == 0:
            try:
                lbl = int(self.tb_labels.iloc[self.current_step])
                tb_bonus = self.tb_reward_scale * lbl  # +scale on wins, -scale on losses, 0 on timeout
            except (IndexError, ValueError, TypeError):
                tb_bonus = 0.0

        if action_type == 1 and self.position == 0:  # BUY
            # Cap position size at max_position_pct of capital
            deploy = self.balance * self.max_position_pct * position_size
            shares_to_buy = int(deploy // current_price)
            if shares_to_buy > 0:
                trade_value = shares_to_buy * current_price
                cost_paid = self.cost_model.cost_for_value(trade_value, is_buy=True)
                self.balance -= cost_paid
                self.balance -= trade_value
                self.position += shares_to_buy
                self.entry_price = current_price
                self.stop_price = current_price - self.atr_mult * atr
                self.entry_step = self.current_step

        elif action_type == 2 and self.position > 0:  # SELL
            shares_to_sell = int(self.position * position_size)
            if shares_to_sell > 0:
                trade_value = shares_to_sell * current_price
                cost_paid = self.cost_model.cost_for_value(trade_value, is_buy=False)
                self.balance += trade_value - cost_paid
                self.position -= shares_to_sell
                pnl = (current_price - self.entry_price) * shares_to_sell - cost_paid
                self.trade_history.append({
                    "entry": self.entry_price, "exit": current_price,
                    "shares": shares_to_sell, "pnl": pnl,
                    "step": self.current_step,
                })
                if self.position == 0:
                    self.entry_price = 0.0
                    self.stop_price = 0.0

        # ---- Check stop-loss (gap-aware) --------------------------------- #
        if self.position > 0:
            low = float(self.df["low"].iloc[self.current_step])
            if low <= self.stop_price:
                # Stop-out: fill at stop or low, whichever is worse
                fill_price = min(self.stop_price, low)
                trade_value = self.position * fill_price
                cost_paid = self.cost_model.cost_for_value(trade_value, is_buy=False)
                self.balance += trade_value - cost_paid
                pnl = (fill_price - self.entry_price) * self.position - cost_paid
                self.trade_history.append({
                    "entry": self.entry_price, "exit": fill_price,
                    "shares": self.position, "pnl": pnl,
                    "step": self.current_step, "reason": "stop",
                })
                self.position = 0
                self.entry_price = 0.0
                self.stop_price = 0.0

        # ---- Advance to next bar ----------------------------------------- #
        self.current_step += 1
        next_price = float(self.df["close"].iloc[self.current_step])
        new_net_worth = self.balance + self.position * next_price
        self.net_worth_history.append(new_net_worth)
        self.peak_net_worth = max(self.peak_net_worth, new_net_worth)

        # ---- Compute reward ---------------------------------------------- #
        daily_return = (new_net_worth - prev_net_worth) / prev_net_worth if prev_net_worth > 0 else 0

        # Risk-adjusted reward (Sharpe-like)
        if len(self.net_worth_history) > 10:
            recent_returns = np.diff(self.net_worth_history[-10:]) / self.net_worth_history[-10:-1]
            vol = np.std(recent_returns) if len(recent_returns) > 1 else 0.001
            sharpe_term = daily_return / max(vol, 0.001) * 0.1  # small weight
        else:
            sharpe_term = 0

        # Counter-trend penalty: if holding a position against the regime
        regime_penalty = 0
        if self.position > 0:
            try:
                regime = an.classify_regime(self.df.iloc[:self.current_step+1]).regime
                if regime == Regime.TRENDING_DOWN:
                    regime_penalty = -0.001
            except Exception:
                pass

        # Drawdown penalty
        drawdown = (self.peak_net_worth - new_net_worth) / self.peak_net_worth
        dd_penalty = -0.5 * drawdown if drawdown > 0.1 else 0

        # Final reward
        reward = daily_return + sharpe_term + regime_penalty + dd_penalty + tb_bonus

        # ---- Termination ------------------------------------------------- #
        terminated = self.current_step >= self.current_end or new_net_worth < self.initial_balance * 0.5
        truncated = self.current_step >= len(self.df) - 1

        return self._get_obs(), float(reward), terminated, truncated, self._get_info()


# =========================================================================== #
#  Training
# =========================================================================== #
class TrainingCallback(BaseCallback):
    """Log training progress every N steps."""

    def __init__(self, log_interval: int = 1000, verbose: int = 1,
                 external_cb=None):
        super().__init__(verbose)
        self.log_interval = log_interval
        self.start_time = time.time()
        # Optional external hook: called with (n_calls, last_ep_reward, elapsed_s)
        self.external_cb = external_cb

    def _on_step(self) -> bool:
        if self.n_calls % self.log_interval == 0:
            elapsed = time.time() - self.start_time
            fps = self.n_calls / elapsed if elapsed > 0 else 0
            ep_reward = None
            ep_len = None
            if len(self.model.ep_info_buffer) > 0:
                ep_info = self.model.ep_info_buffer[-1]
                ep_reward = ep_info.get("r", 0)
                ep_len = ep_info.get("l", 0)
                print(f"  step {self.n_calls:>7}  |  {fps:.0f} fps  |  "
                      f"ep_reward {ep_reward:>+8.2f}  |  ep_len {ep_len}")
            if self.external_cb is not None:
                try:
                    self.external_cb(self.n_calls, ep_reward, elapsed)
                except Exception:
                    pass
        return True


def make_env(stock_data: dict, stock_list: list[str], seed: int = 42,
             use_triple_barrier: bool = False,
             tb_labels_cache: dict | None = None):
    """Factory that creates an env picking a random stock each reset."""
    def _env():
        symbol = random.choice(stock_list)
        df = stock_data[symbol]
        features = build_features(df)
        tb = None
        if use_triple_barrier and tb_labels_cache is not None:
            tb = tb_labels_cache.get(symbol)
        env = NSETradingEnv(df, features, tb_labels=tb)
        env.reset(seed=seed)
        return env
    return _env


def train_agent(timesteps: int = 100_000, save_path: Path = MODEL_PATH,
                use_triple_barrier: bool = False,
                progress_cb=None):
    """Train a PPO agent on NSE stocks."""
    print(f"\n{'='*68}")
    print(f"  Training PPO agent on NSE stocks ({timesteps} timesteps)")
    print(f"{'='*68}\n")

    # 1. Fetch training data
    print("Step 1: Fetching training data...")
    stock_data = {}
    for sym in TRAIN_STOCKS:
        try:
            df = fetch_stock_data(sym, period="5y")
            stock_data[sym] = df
            print(f"  + {sym}: {len(df)} bars")
        except Exception as e:
            print(f"  ! {sym}: {e}")
    if not stock_data:
        raise RuntimeError("No training data fetched")

    # 2. (Optional) Compute triple-barrier labels for reward shaping
    tb_labels_cache: dict | None = None
    if use_triple_barrier:
        print("\nStep 2a: Computing triple-barrier labels (TP=5xATR, SL=2xATR, hold=10)...")
        tb_labels_cache = {}
        for sym, df in stock_data.items():
            try:
                tb_labels_cache[sym] = label_bars_with_triple_barrier(df)
                pos = int((tb_labels_cache[sym] > 0).sum())
                neg = int((tb_labels_cache[sym] < 0).sum())
                print(f"  + {sym}: +1={pos}  -1={neg}  0={len(df) - pos - neg}")
            except Exception as e:
                print(f"  ! {sym}: {e}")

    # 2. Build the vectorized environment
    print(f"\nStep 2: Building environment with {len(stock_data)} stocks"
          f"{' (triple-barrier reward shaping ON)' if use_triple_barrier else ''}...")
    env = DummyVecEnv([make_env(stock_data, list(stock_data.keys()),
                                use_triple_barrier=use_triple_barrier,
                                tb_labels_cache=tb_labels_cache)])

    # 3. Initialize PPO
    print("\nStep 3: Initializing PPO agent...")
    model = PPO(
        "MlpPolicy", env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=0,
        seed=42,
        device="cpu",  # CPU is fine for this small network
    )

    # 4. Train
    print(f"\nStep 4: Training for {timesteps} timesteps...")
    log_interval = max(200, min(1000, timesteps // 10))
    callback = TrainingCallback(log_interval=log_interval, external_cb=progress_cb)
    model.learn(total_timesteps=timesteps, callback=callback)

    # 5. Save
    print(f"\nStep 5: Saving model to {save_path}")
    model.save(save_path)

    # Save a feature scaler stub (we use on-the-fly normalization, so this is
    # just for compatibility with the huggingface format).
    scaler = {"features": FEATURE_COLS, "lookback": LOOKBACK}
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    elapsed = time.time() - callback.start_time
    print(f"\nTraining complete in {elapsed:.0f}s.")
    print(f"Model: {save_path}")
    return model


# =========================================================================== #
#  Backtesting (100+ episodes)
# =========================================================================== #
def backtest_agent(model_path: Path = MODEL_PATH, episodes: int = 100,
                   stocks: list[str] | None = None,
                   append: bool = False) -> dict:
    """Run the trained agent on multiple stocks/periods for backtesting.

    If append=True, results are added to any existing backtest_results.json,
    so you can run multiple times to accumulate 100+ episodes.
    """
    print(f"\n{'='*68}")
    print(f"  Backtesting RL agent ({episodes} episodes"
          f"{', appending to existing' if append else ''})")
    print(f"{'='*68}\n")

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run train first.")

    model = PPO.load(model_path, device="cpu")
    stocks = stocks or BACKTEST_STOCKS
    cost_model = IndianCostModel()

    # Fetch all stock data
    print("Fetching stock data...")
    stock_data = {}
    for sym in stocks:
        try:
            df = fetch_stock_data(sym, period="5y")
            stock_data[sym] = df
        except Exception as e:
            print(f"  ! {sym}: {e}")

    # Load existing results if appending
    existing_results = []
    if append and RESULTS_PATH.exists():
        with open(RESULTS_PATH) as f:
            existing_data = json.load(f)
        existing_results = existing_data.get("episodes", [])
        print(f"  loaded {len(existing_results)} existing episodes")

    # Run episodes
    results = list(existing_results)
    starting_ep = len(results)
    print(f"\nRunning {episodes} new backtest episodes across {len(stock_data)} stocks...")
    print(f"(total will be {starting_ep + episodes})\n")

    for i in range(episodes):
        symbol = random.choice(list(stock_data.keys()))
        df = stock_data[symbol]
        features = build_features(df)

        # Random 6-12 month window
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

        # Compute trade stats
        trades = env.trade_history
        n_trades = len(trades)
        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        win_rate = len(wins) / n_trades if n_trades > 0 else 0
        total_pnl = sum(t["pnl"] for t in trades)
        avg_win = np.mean([t["pnl"] for t in wins]) if wins else 0
        avg_loss = np.mean([t["pnl"] for t in losses]) if losses else 0
        profit_factor = (sum(t["pnl"] for t in wins) / abs(sum(t["pnl"] for t in losses))
                         if losses and sum(t["pnl"] for t in losses) != 0 else 0)

        # Max drawdown
        peak = np.maximum.accumulate(env.net_worth_history)
        dd = (peak - env.net_worth_history) / peak
        max_dd = np.max(dd) * 100 if len(dd) > 0 else 0

        # Buy-and-hold benchmark
        bh_start = float(df["close"].iloc[start_idx])
        bh_end = float(df["close"].iloc[end_idx])
        bh_return = (bh_end - bh_start) / bh_start * 100

        ep_num = starting_ep + i + 1
        result = {
            "episode": ep_num,
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
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "total_reward": round(total_reward, 3),
        }
        results.append(result)

        if (i + 1) % 10 == 0:
            avg_ret = np.mean([r["return_pct"] for r in results[-(i+1):]])
            print(f"  [{i+1:>3}/{episodes}]  {symbol:<14}  "
                  f"ret {return_pct:>+7.1f}%  |  batch avg {avg_ret:>+7.1f}%  "
                  f"  (total: {len(results)} eps)")

    # Summary
    print(f"\n{'='*68}")
    print("  BACKTEST SUMMARY")
    print(f"{'='*68}")
    returns = [r["return_pct"] for r in results]
    alphas = [r["alpha_vs_buy_hold"] for r in results]
    win_rates = [r["win_rate"] for r in results]
    pf = [r["profit_factor"] for r in results if r["profit_factor"] > 0]
    dds = [r["max_drawdown_pct"] for r in results]

    summary = {
        "episodes": len(results),
        "stocks_tested": len(set(r["symbol"] for r in results)),
        "avg_return_pct": round(np.mean(returns), 2),
        "median_return_pct": round(np.median(returns), 2),
        "std_return_pct": round(np.std(returns), 2),
        "min_return_pct": round(min(returns), 2),
        "max_return_pct": round(max(returns), 2),
        "avg_alpha_vs_buy_hold": round(np.mean(alphas), 2),
        "win_rate_episodes": round(np.mean([1 if r > 0 else 0 for r in returns]) * 100, 1),
        "avg_trade_win_rate": round(np.mean(win_rates), 1),
        "avg_profit_factor": round(np.mean(pf) if pf else 0, 2),
        "avg_max_drawdown_pct": round(np.mean(dds), 2),
        "avg_trades_per_episode": round(np.mean([r["n_trades"] for r in results]), 1),
    }

    print(f"  Episodes:           {summary['episodes']}")
    print(f"  Stocks tested:      {summary['stocks_tested']}")
    print(f"  Avg return:         {summary['avg_return_pct']:+.2f}%")
    print(f"  Median return:      {summary['median_return_pct']:+.2f}%")
    print(f"  Std dev:            {summary['std_return_pct']:.2f}%")
    print(f"  Min / Max:          {summary['min_return_pct']:+.2f}% / {summary['max_return_pct']:+.2f}%")
    print(f"  Avg alpha vs B&H:   {summary['avg_alpha_vs_buy_hold']:+.2f}%")
    print(f"  Episodes profitable:{summary['win_rate_episodes']}%")
    print(f"  Avg trade win rate: {summary['avg_trade_win_rate']}%")
    print(f"  Avg profit factor:  {summary['avg_profit_factor']}")
    print(f"  Avg max drawdown:   {summary['avg_max_drawdown_pct']:.2f}%")
    print(f"  Avg trades/episode: {summary['avg_trades_per_episode']}")

    # Save results
    output = {"summary": summary, "episodes": results}
    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {RESULTS_PATH}")

    return output


# =========================================================================== #
#  Prediction for a single stock
# =========================================================================== #
def predict(symbol: str, model_path: Path = MODEL_PATH) -> dict:
    """Get the agent's prediction for a single stock."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run train first.")

    model = PPO.load(model_path, device="cpu")
    sym = symbol if "." in symbol else f"{symbol}.NS"

    df = fetch_stock_data(sym, period="1y")
    features = build_features(df)

    env = NSETradingEnv(df, features, start_idx=max(60, len(df) - 100),
                        end_idx=len(df) - 1)
    obs, info = env.reset()
    action, _ = model.predict(obs, deterministic=True)
    action_type = int(np.clip(round(action[0]), 0, 2))
    position_size = float(np.clip(action[1], 0, 1))

    current_price = float(df["close"].iloc[-1])
    action_label = {0: "HOLD", 1: "BUY", 2: "SELL"}[action_type]

    # Get regime
    try:
        regime = an.classify_regime(df).regime.value
    except Exception:
        regime = "unknown"

    return {
        "symbol": sym,
        "action": action_label,
        "action_code": action_type,
        "position_size": round(position_size, 2),
        "current_price": round(current_price, 2),
        "regime": regime,
        "suggested_capital_pct": round(position_size * 25, 1),  # max 25% of capital
        "rupees_to_deploy": round(position_size * 25_000, 0),  # on 1L capital
    }


# =========================================================================== #
#  CLI
# =========================================================================== #
def main():
    ap = argparse.ArgumentParser(description="NSE/BSE RL trading agent")
    sub = ap.add_subparsers(dest="command", required=True)

    t = sub.add_parser("train", help="Train a new PPO agent")
    t.add_argument("--timesteps", type=int, default=100_000)
    t.add_argument("--output", type=Path, default=MODEL_PATH)
    t.add_argument("--use-triple-barrier", action="store_true",
                   help="Add triple-barrier label bonus to the reward (encourages BUYs "
                        "on bars that would have hit TP within the hold window).")

    bt = sub.add_parser("backtest", help="Run backtesting episodes")
    bt.add_argument("--episodes", type=int, default=100)
    bt.add_argument("--model", type=Path, default=MODEL_PATH)
    bt.add_argument("--append", action="store_true",
                    help="Append to existing results (run multiple times for 100+)")

    p = sub.add_parser("predict", help="Predict for a single stock")
    p.add_argument("symbol", help="e.g. RELIANCE.NS or RELIANCE")
    p.add_argument("--model", type=Path, default=MODEL_PATH)

    sub.add_parser("compare", help="Show saved backtest results")

    args = ap.parse_args()

    if args.command == "train":
        train_agent(args.timesteps, args.output,
                    use_triple_barrier=args.use_triple_barrier)
    elif args.command == "backtest":
        backtest_agent(args.model, args.episodes, append=args.append)
    elif args.command == "predict":
        result = predict(args.symbol, args.model)
        print(json.dumps(result, indent=2))
    elif args.command == "compare":
        if not RESULTS_PATH.exists():
            print("No backtest results. Run: python rl_agent.py backtest")
            return
        with open(RESULTS_PATH) as f:
            data = json.load(f)
        print(json.dumps(data["summary"], indent=2))


if __name__ == "__main__":
    main()
