"""
advisor.core
============
The foundation layer of the advisor package, merging three concerns into one
file so the import graph stays shallow and easy to navigate:

  1. **Models**  - plain dataclasses that define the contracts passed between
     every layer (TradeIdea, Signal, PositionPlan, Scenario, Veto, ...).
  2. **Config**  - Settings dataclass + loader with sensible defaults, optional
     `config.yaml` overlay (PyYAML), and `.env` / env-var overrides for secrets.
  3. **Data**    - OHLCV source interface (`OHLCVSource`) and the two shipped
     implementations: `YFinanceSource` (free, no key) and `CSVSource` (offline).

Precedence for settings:  built-in DEFAULTS  ->  config.yaml  ->  environment.

This file is dependency-light: it only needs `pandas` for the data layer, and
even that is imported lazily inside the source classes so `from advisor.core
import Settings` works on a bare interpreter.
"""
from __future__ import annotations

import os
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import pandas as pd


# =========================================================================== #
#  1.  MODELS  -  typed data containers (no computation here)
# =========================================================================== #
class Style(str, Enum):
    """Trading style. Determines timeframe, indicators and holding period."""
    SWING = "swing"        # daily/weekly charts, hold days-weeks (delivery)
    INTRADAY = "intraday"  # 1/5/15-min charts, square off same day


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"
    NONE = "none"


class Regime(str, Enum):
    """Market regime. Drives which setups are even allowed."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class Verdict(str, Enum):
    """The final call the agent gives you."""
    TAKE = "TAKE"            # high-confluence setup, all vetoes passed
    WATCH = "WATCH"         # setup forming but not confirmed - put on alert
    AVOID = "AVOID"         # red signal(s) fired - do not trade
    NO_SETUP = "NO_SETUP"   # nothing actionable right now


@dataclass
class IndicatorSnapshot:
    """The latest value of every indicator we compute, for one symbol."""
    close: float
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_20: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None      # (upper-lower)/mid -> volatility proxy
    atr_14: Optional[float] = None
    atr_pct: Optional[float] = None       # atr/close, comparable across stocks
    adx_14: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None
    vwap: Optional[float] = None          # intraday only
    obv: Optional[float] = None
    avg_volume_20: Optional[float] = None
    last_volume: Optional[float] = None
    recent_high_20: Optional[float] = None
    recent_low_20: Optional[float] = None
    recent_high_52w: Optional[float] = None
    recent_low_52w: Optional[float] = None

    def volume_ratio(self) -> Optional[float]:
        """Today's volume vs its prior 20-bar average. >1.5 = conviction."""
        if (self.last_volume is not None and self.avg_volume_20 is not None
                and self.avg_volume_20 > 0):
            return round(self.last_volume / self.avg_volume_20, 2)
        return None


@dataclass
class Signal:
    """A single bullish/bearish piece of evidence from one indicator or pattern."""
    name: str                       # e.g. "rsi_oversold", "macd_bull_cross"
    direction: Direction
    weight: float                   # how much this signal counts (0-1)
    note: str                       # human-readable explanation
    value: Optional[float] = None   # the raw number behind it, if useful


@dataclass
class Scenario:
    """One branch of the 'think through all outcomes' analysis."""
    name: str                # "bull", "base", "bear"
    probability: float       # 0-1, rough estimate from regime + confluence
    price_target: float
    move_pct: float          # signed % move from entry to this target
    rationale: str


@dataclass
class PositionPlan:
    """Everything you need to actually place and manage the order."""
    entry: float
    stop_loss: float
    target: float
    quantity: int
    capital: float
    risk_pct: float                 # % of capital risked on this trade
    rupees_at_risk: float
    rupees_to_target: float
    risk_per_share: float           # nominal |entry - stop| (your stop order level)
    reward_per_share: float
    risk_reward: float              # reward/risk, must clear the min to TAKE
    worst_case_risk_per_share: float = 0.0  # incl. gap/slippage buffer
    rupees_at_risk_worst: float = 0.0       # qty * worst_case_risk_per_share
    gap_buffer: float = 0.0                 # the buffer added beyond the stop
    position_value: float = 0.0     # entry * quantity (capital deployed)
    position_pct_of_capital: float = 0.0  # exposure as % of total capital
    stop_method: str = "atr"        # "atr" or "structure"


@dataclass
class Veto:
    """A red signal - a reason a setup is rejected outright."""
    name: str
    reason: str
    severity: str = "hard"   # "hard" blocks the trade, "soft" only warns


@dataclass
class TradeIdea:
    """The complete analysis for one symbol - this is what the agent hands you."""
    symbol: str
    style: Style
    direction: Direction
    verdict: Verdict
    as_of: datetime
    timeframe: str                              # e.g. "1d", "15m"
    regime: Regime
    indicators: IndicatorSnapshot
    signals: list[Signal] = field(default_factory=list)
    confluence_score: float = 0.0               # net weighted evidence (-1..+1)
    confidence: float = 0.0                     # 0-100, derived, NOT a guarantee
    plan: Optional[PositionPlan] = None
    scenarios: list[Scenario] = field(default_factory=list)
    vetoes: list[Veto] = field(default_factory=list)
    expectancy_r: Optional[float] = None        # from your trade journal, if any
    news_sentiment: Optional[float] = None      # -1..+1, if news module ran
    narration: str = ""                         # LLM or template prose
    notes: list[str] = field(default_factory=list)

    # -- convenience -------------------------------------------------------- #
    @property
    def hard_vetoes(self) -> list[Veto]:
        return [v for v in self.vetoes if v.severity == "hard"]

    @property
    def soft_vetoes(self) -> list[Veto]:
        return [v for v in self.vetoes if v.severity == "soft"]

    @property
    def soft_veto_notes(self) -> list[str]:
        return [v.reason for v in self.soft_vetoes]

    @property
    def bullish_signals(self) -> list[Signal]:
        return [s for s in self.signals if s.direction == Direction.LONG]

    @property
    def bearish_signals(self) -> list[Signal]:
        return [s for s in self.signals if s.direction == Direction.SHORT]

    def to_dict(self) -> dict:
        """JSON-friendly dict (enums -> their values, datetime -> iso)."""
        d = asdict(self)
        d["style"] = self.style.value
        d["direction"] = self.direction.value
        d["verdict"] = self.verdict.value
        d["regime"] = self.regime.value
        d["as_of"] = self.as_of.isoformat()
        for s in d["signals"]:
            s["direction"] = s["direction"].value if hasattr(s["direction"], "value") else s["direction"]
        return d


# =========================================================================== #
#  2.  CONFIG  -  Settings + loader
# =========================================================================== #
DEFAULTS: dict[str, Any] = {
    # --- money & risk --------------------------------------------------- #
    "capital": 100000.0,
    "risk_pct": 0.01,
    "max_exposure_pct": 0.25,
    "atr_mult": 2.0,
    "target_rr": 2.5,
    "min_rr": 2.0,
    "min_confidence": 35.0,
    "slippage_pct": 0.0015,
    "gap_buffer_atr": 0.25,
    "scan_delay_sec": 0.5,

    # --- universe ------------------------------------------------------- #
    "exchange": "NSE",
    "data_source": "yfinance",
    "csv_dir": ".",
    "watchlist": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "SBIN", "BHARTIARTL", "ITC", "LT", "AXISBANK",
    ],

    # --- timeframes ----------------------------------------------------- #
    "swing_interval": "1d",
    "swing_period": "2y",
    "intraday_interval": "15m",
    "intraday_period": "1mo",
    "opening_range_bars": 6,

    # --- LLM narration -------------------------------------------------- #
    "llm_provider": "none",
    "llm_model": "llama3.1",
    "ollama_host": "http://localhost:11434",

    # --- news / sentiment ----------------------------------------------- #
    "news_enabled": False,
    "news_feeds": [
        "https://www.moneycontrol.com/rss/marketreports.xml",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    ],

    # --- journal -------------------------------------------------------- #
    "journal_path": "trade_journal.db",
}


@dataclass
class Settings:
    capital: float = DEFAULTS["capital"]
    risk_pct: float = DEFAULTS["risk_pct"]
    max_exposure_pct: float = DEFAULTS["max_exposure_pct"]
    atr_mult: float = DEFAULTS["atr_mult"]
    target_rr: float = DEFAULTS["target_rr"]
    min_rr: float = DEFAULTS["min_rr"]
    min_confidence: float = DEFAULTS["min_confidence"]
    slippage_pct: float = DEFAULTS["slippage_pct"]
    gap_buffer_atr: float = DEFAULTS["gap_buffer_atr"]
    scan_delay_sec: float = DEFAULTS["scan_delay_sec"]

    exchange: str = DEFAULTS["exchange"]
    data_source: str = DEFAULTS["data_source"]
    csv_dir: str = DEFAULTS["csv_dir"]
    watchlist: list[str] = field(default_factory=lambda: list(DEFAULTS["watchlist"]))

    swing_interval: str = DEFAULTS["swing_interval"]
    swing_period: str = DEFAULTS["swing_period"]
    intraday_interval: str = DEFAULTS["intraday_interval"]
    intraday_period: str = DEFAULTS["intraday_period"]
    opening_range_bars: int = DEFAULTS["opening_range_bars"]

    llm_provider: str = DEFAULTS["llm_provider"]
    llm_model: str = DEFAULTS["llm_model"]
    ollama_host: str = DEFAULTS["ollama_host"]

    news_enabled: bool = DEFAULTS["news_enabled"]
    news_feeds: list[str] = field(default_factory=lambda: list(DEFAULTS["news_feeds"]))

    journal_path: str = DEFAULTS["journal_path"]

    # secrets (env only) ------------------------------------------------- #
    groq_api_key: str | None = None
    gemini_api_key: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("groq_api_key", "gemini_api_key"):
            if d.get(k):
                d[k] = "***set***"
        return d


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no python-dotenv dependency required)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def load_settings(config_path: str | Path = "config.yaml",
                  env_path: str | Path = ".env") -> Settings:
    """Build Settings from DEFAULTS <- config.yaml <- environment."""
    merged = dict(DEFAULTS)

    cfg = Path(config_path)
    if cfg.exists():
        try:
            import yaml  # optional
            with cfg.open() as fh:
                user = yaml.safe_load(fh) or {}
            merged.update({k: v for k, v in user.items() if v is not None})
        except ImportError:
            pass  # PyYAML not installed - silently fall back to defaults.

    _load_dotenv(Path(env_path))

    if os.environ.get("ADVISOR_CAPITAL"):
        merged["capital"] = float(os.environ["ADVISOR_CAPITAL"])
    if os.environ.get("ADVISOR_RISK_PCT"):
        merged["risk_pct"] = float(os.environ["ADVISOR_RISK_PCT"])
    if os.environ.get("ADVISOR_LLM_PROVIDER"):
        merged["llm_provider"] = os.environ["ADVISOR_LLM_PROVIDER"]
    if os.environ.get("ADVISOR_DATA_SOURCE"):
        merged["data_source"] = os.environ["ADVISOR_DATA_SOURCE"]
    if os.environ.get("ADVISOR_CSV_DIR"):
        merged["csv_dir"] = os.environ["ADVISOR_CSV_DIR"]
    if os.environ.get("ADVISOR_WATCHLIST"):
        merged["watchlist"] = [s.strip() for s in
                               os.environ["ADVISOR_WATCHLIST"].split(",") if s.strip()]
    if os.environ.get("OLLAMA_HOST"):
        merged["ollama_host"] = os.environ["OLLAMA_HOST"]

    settings = Settings(**{k: merged[k] for k in merged if k in Settings.__annotations__})
    settings.groq_api_key = os.environ.get("GROQ_API_KEY")
    settings.gemini_api_key = os.environ.get("GEMINI_API_KEY")
    validate_settings(settings)
    return settings


def validate_settings(s: Settings) -> None:
    """Catch nonsensical configuration early with a clear message."""
    errors = []
    if s.capital <= 0:
        errors.append(f"capital must be > 0 (got {s.capital}).")
    if not 0 < s.risk_pct <= 0.1:
        errors.append(f"risk_pct must be in (0, 0.10]; {s.risk_pct} is unsafe. "
                      f"1% (0.01) is typical; >10% per trade is reckless.")
    if not 0 < s.max_exposure_pct <= 1.0:
        errors.append(f"max_exposure_pct must be in (0, 1.0] (got {s.max_exposure_pct}).")
    if s.atr_mult <= 0:
        errors.append(f"atr_mult must be > 0 (got {s.atr_mult}).")
    if s.min_rr <= 0 or s.target_rr <= 0:
        errors.append("min_rr and target_rr must be > 0.")
    if s.target_rr < s.min_rr:
        errors.append(f"target_rr ({s.target_rr}) is below min_rr ({s.min_rr}) - "
                      f"every trade would be vetoed.")
    if not 0 <= s.slippage_pct < 0.1:
        errors.append(f"slippage_pct must be in [0, 0.1) (got {s.slippage_pct}).")
    if errors:
        raise ValueError("Invalid configuration:\n  - " + "\n  - ".join(errors))


# =========================================================================== #
#  3.  DATA  -  OHLCV sources
# =========================================================================== #
_INDEX_MAP = {
    "NIFTY": "^NSEI", "NIFTY50": "^NSEI", "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN", "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
}


def normalize_symbol(symbol: str, exchange: str = "NSE") -> str:
    """Turn a user-friendly symbol into a Yahoo ticker."""
    sym = symbol.strip().rstrip("/").strip().upper()
    if sym in _INDEX_MAP:
        return _INDEX_MAP[sym]
    if sym.startswith("^") or sym.endswith((".NS", ".BO")):
        return sym
    suffix = ".BO" if exchange.upper() == "BSE" else ".NS"
    return f"{sym}{suffix}"


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise any source's frame to the canonical OHLCV shape."""
    if df is None or df.empty:
        raise ValueError("No data returned from source.")

    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={"adj_close": "adj_close"})

    needed = ["open", "high", "low", "close", "volume"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Source data missing columns {missing}; got {list(df.columns)}")

    df = df[needed + [c for c in df.columns if c not in needed]]
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.dropna(subset=["open", "high", "low", "close"])
    df["volume"] = df["volume"].fillna(0.0)
    return df


class OHLCVSource(ABC):
    name = "base"

    @abstractmethod
    def get_history(self, symbol: str, interval: str = "1d",
                    period: str | None = None) -> pd.DataFrame:
        ...

    def get_quote(self, symbol: str) -> float | None:
        """Latest price. Default: last close from a short history pull."""
        try:
            df = self.get_history(symbol, interval="1d", period="5d")
            return float(df["close"].iloc[-1])
        except Exception:
            return None


class YFinanceSource(OHLCVSource):
    name = "yfinance"

    _DEFAULT_PERIOD = {
        "1m": "5d", "5m": "1mo", "15m": "2mo", "30m": "2mo",
        "60m": "6mo", "1h": "6mo", "1d": "2y", "1wk": "5y",
    }

    def __init__(self, exchange: str = "NSE"):
        self.exchange = exchange

    def get_history(self, symbol: str, interval: str = "1d",
                    period: str | None = None) -> pd.DataFrame:
        try:
            import yfinance as yf
        except ImportError as e:
            raise ImportError(
                "yfinance is not installed. Run `pip install yfinance`, or use the "
                "CSV source for offline data."
            ) from e

        ticker = normalize_symbol(symbol, self.exchange)
        period = period or self._DEFAULT_PERIOD.get(interval, "1y")

        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            raise ValueError(
                f"No data for '{ticker}' (interval={interval}, period={period}). "
                f"Check the symbol/exchange, or Yahoo may be rate-limiting."
            )
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return clean_frame(df)


class CSVSource(OHLCVSource):
    name = "csv"

    def __init__(self, directory: str | Path = "."):
        self.directory = Path(directory)

    def get_history(self, symbol: str, interval: str = "1d",
                    period: str | None = None) -> pd.DataFrame:
        candidates = [
            self.directory / f"{symbol.upper()}_{interval}.csv",
            self.directory / f"{symbol.upper()}.csv",
            self.directory / f"{symbol}.csv",
        ]
        path = next((p for p in candidates if p.exists()), None)
        if path is None:
            raise FileNotFoundError(
                f"No CSV for '{symbol}' in {self.directory} "
                f"(looked for {[p.name for p in candidates]})."
            )
        df = pd.read_csv(path)
        date_col = next(
            (c for c in df.columns
             if c.lower() in ("date", "datetime", "timestamp", "time")), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col)
        return clean_frame(df)


def get_source(name: str = "yfinance", **kwargs) -> OHLCVSource:
    name = name.lower()
    if name == "yfinance":
        return YFinanceSource(exchange=kwargs.get("exchange", "NSE"))
    if name == "csv":
        return CSVSource(directory=kwargs.get("directory", "."))
    if name == "angel":
        # imported lazily so core.py stays dep-free if angel_source is unused
        from advisor.angel_source import AngelOneSource
        return AngelOneSource(exchange=kwargs.get("exchange", "NSE"))
    raise ValueError(f"Unknown data source '{name}'. Options: yfinance, csv, angel.")
