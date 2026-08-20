"""
advisor.angel_source
====================
Angel One SmartAPI OHLCV source. Optional real-time NSE feed for users with
an Angel One demat account. Falls back to YFinanceSource transparently when
credentials are missing or the API errors, so the calling code never crashes.

Credentials (all read from environment, all optional at import time):
    ANGEL_API_KEY        - "trading" API key from https://smartapi.angelbroking.com
    ANGEL_CLIENT_ID      - your Angel One client code (e.g. "A123456")
    ANGEL_MPIN           - 4-digit login MPIN (or password)
    ANGEL_TOTP_SECRET    - Base32 secret shown when you enable 2FA

Endpoints used (see https://smartapi.angelbroking.com/docs):
    POST /rest/auth/angelbroking/user/v1/loginByPassword   -> JWT tokens
    POST /rest/secure/angelbroking/historical/v1/getCandleData -> OHLCV candles
    POST /rest/secure/angelbroking/order/v1/getLtpData      -> latest tick

Pure stdlib: uses urllib for HTTP and hmac/hashlib for TOTP. No new deps.
Network calls happen ONLY inside get_history/get_quote, never at import time.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import struct
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd

from advisor.core import OHLCVSource, YFinanceSource, clean_frame, normalize_symbol

log = logging.getLogger(__name__)

_BASE = "https://apiconnect.angelone.in"
_SCRIP_MASTER_URL = (
    "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPI_ScripMaster.json"
)

_INTERVAL_MAP = {
    "1m": "ONE_MINUTE", "3m": "THREE_MINUTE", "5m": "FIVE_MINUTE",
    "10m": "TEN_MINUTE", "15m": "FIFTEEN_MINUTE", "30m": "THIRTY_MINUTE",
    "60m": "ONE_HOUR", "1h": "ONE_HOUR", "1d": "ONE_DAY",
}

_PERIOD_DAYS = {  # rough calendar-day windows if caller passes a period string
    "1d": 2, "5d": 7, "1mo": 30, "2mo": 60, "3mo": 90, "6mo": 180,
    "1y": 365, "2y": 730, "5y": 1825, "10y": 3650, "max": 3650,
}


# --------------------------------------------------------------------------- #
#  TOTP (RFC 6238) - stdlib only, avoids the pyotp dependency.
# --------------------------------------------------------------------------- #
def _totp(secret: str, digits: int = 6, step: int = 30) -> str:
    key = base64.b32decode(secret.strip().replace(" ", "").upper() + "=" * (-len(secret) % 8))
    counter = int(time.time() // step)
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[-1] & 0x0F
    code = (struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)


# --------------------------------------------------------------------------- #
#  Minimal HTTP helper (POST/GET JSON with headers).
# --------------------------------------------------------------------------- #
def _http_json(url: str, method: str = "GET", body: Optional[dict] = None,
               headers: Optional[dict] = None, timeout: int = 15) -> Any:
    data = None
    hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --------------------------------------------------------------------------- #
#  AngelOneSource
# --------------------------------------------------------------------------- #
class AngelOneSource(OHLCVSource):
    name = "angel"

    _scrip_cache: dict[str, dict] | None = None  # class-level cache

    def __init__(self, exchange: str = "NSE"):
        self.exchange = exchange
        self.api_key = os.environ.get("ANGEL_API_KEY")
        self.client_id = os.environ.get("ANGEL_CLIENT_ID")
        self.mpin = os.environ.get("ANGEL_MPIN")
        self.totp_secret = os.environ.get("ANGEL_TOTP_SECRET")
        self._jwt: Optional[str] = None
        self._jwt_ts: float = 0.0
        self._fallback = YFinanceSource(exchange=exchange)

    # -- credential + auth ------------------------------------------------- #
    def _has_creds(self) -> bool:
        return all([self.api_key, self.client_id, self.mpin, self.totp_secret])

    def _headers(self, auth: bool = False) -> dict:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "X-PrivateKey": self.api_key or "",
        }
        if auth and self._jwt:
            h["Authorization"] = f"Bearer {self._jwt}"
        return h

    def _login(self) -> bool:
        """POST loginByPassword. Returns True on success, False on failure."""
        if not self._has_creds():
            return False
        # cache token for ~6h
        if self._jwt and (time.time() - self._jwt_ts) < 6 * 3600:
            return True
        try:
            body = {
                "clientcode": self.client_id,
                "password": self.mpin,
                "totp": _totp(self.totp_secret),  # type: ignore[arg-type]
            }
            resp = _http_json(
                _BASE + "/rest/auth/angelbroking/user/v1/loginByPassword",
                method="POST", body=body, headers=self._headers(),
            )
            if not resp.get("status") or not resp.get("data"):
                log.warning("Angel login failed: %s", resp.get("message"))
                return False
            self._jwt = resp["data"].get("jwtToken")
            self._jwt_ts = time.time()
            return bool(self._jwt)
        except Exception as e:
            log.warning("Angel login exception: %s", e)
            return False

    # -- scrip master (symbol -> token lookup) ----------------------------- #
    def _load_scrip_master(self) -> dict[str, dict]:
        if AngelOneSource._scrip_cache is not None:
            return AngelOneSource._scrip_cache
        try:
            raw = _http_json(_SCRIP_MASTER_URL, timeout=30)
        except Exception as e:
            log.warning("Angel scrip master fetch failed: %s", e)
            AngelOneSource._scrip_cache = {}
            return {}
        idx: dict[str, dict] = {}
        for row in raw or []:
            sym = str(row.get("symbol", "")).upper()
            if sym.endswith("-EQ") and row.get("exch_seg") == "NSE":
                idx[sym[:-3]] = row  # store under bare NSE symbol
        AngelOneSource._scrip_cache = idx
        return idx

    def _symbol_token(self, symbol: str) -> Optional[tuple[str, str]]:
        bare = symbol.strip().upper().rstrip("/").replace(".NS", "").replace(".BO", "")
        row = self._load_scrip_master().get(bare)
        if not row:
            return None
        return str(row["symbol"]), str(row["token"])

    # -- period -> date range --------------------------------------------- #
    @staticmethod
    def _period_to_range(period: Optional[str], interval: str) -> tuple[datetime, datetime]:
        now = datetime.now()
        days = _PERIOD_DAYS.get(period or "", 365)
        if interval != "1d" and days > 60:  # SmartAPI caps intraday windows
            days = 30
        return now - timedelta(days=days), now

    # -- OHLCVSource interface -------------------------------------------- #
    def get_history(self, symbol: str, interval: str = "1d",
                    period: Optional[str] = None) -> pd.DataFrame:
        if not self._has_creds():
            log.info("Angel credentials missing; using yfinance fallback for %s", symbol)
            return self._fallback.get_history(symbol, interval=interval, period=period)
        try:
            if not self._login():
                raise RuntimeError("Angel login failed")
            tok = self._symbol_token(symbol)
            if not tok:
                raise RuntimeError(f"Symbol '{symbol}' not found in Angel scrip master")
            tsym, token = tok
            frm, to = self._period_to_range(period, interval)
            body = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": _INTERVAL_MAP.get(interval, "ONE_DAY"),
                "fromdate": frm.strftime("%Y-%m-%d %H:%M"),
                "todate": to.strftime("%Y-%m-%d %H:%M"),
            }
            resp = _http_json(
                _BASE + "/rest/secure/angelbroking/historical/v1/getCandleData",
                method="POST", body=body, headers=self._headers(auth=True),
            )
            rows = (resp or {}).get("data") or []
            if not rows:
                raise RuntimeError(f"Angel returned no candles: {resp.get('message')}")
            df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            return clean_frame(df)
        except Exception as e:
            log.warning("AngelOneSource failed (%s); falling back to yfinance", e)
            return self._fallback.get_history(symbol, interval=interval, period=period)

    def get_quote(self, symbol: str) -> Optional[float]:
        if not self._has_creds():
            return self._fallback.get_quote(symbol)
        try:
            if not self._login():
                raise RuntimeError("login failed")
            tok = self._symbol_token(symbol)
            if not tok:
                raise RuntimeError("symbol not found")
            tsym, token = tok
            body = {"exchange": "NSE", "tradingsymbol": tsym, "symboltoken": token}
            resp = _http_json(
                _BASE + "/rest/secure/angelbroking/order/v1/getLtpData",
                method="POST", body=body, headers=self._headers(auth=True),
            )
            ltp = ((resp or {}).get("data") or {}).get("ltp")
            if ltp is None:
                raise RuntimeError("no ltp in response")
            return float(ltp)
        except Exception as e:
            log.warning("Angel quote failed (%s); falling back to yfinance", e)
            return self._fallback.get_quote(symbol)


# --------------------------------------------------------------------------- #
#  CLI entrypoint: `python -m advisor.angel_source`
# --------------------------------------------------------------------------- #
def _main() -> int:
    # honour .env for convenience
    from advisor.core import _load_dotenv
    from pathlib import Path
    _load_dotenv(Path(".env"))
    src = AngelOneSource()
    if not src._has_creds():
        print("SKIPPED (no credentials) - set ANGEL_API_KEY, ANGEL_CLIENT_ID, "
              "ANGEL_MPIN, ANGEL_TOTP_SECRET in .env to activate.")
        return 0
    ok = src._login()
    print("OK" if ok else "FAILED (see log)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_main())
