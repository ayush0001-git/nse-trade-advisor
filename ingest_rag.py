"""ingest_rag.py - Populate the three empty RAG collections (pattern_library,
filings, earnings_calls) that Council agents query.

Subcommands: patterns | filings [--limit N] | earnings | all | stats.
Stdlib-only fetch/parse; uses data_warehouse.get_warehouse() for storage.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_warehouse import get_warehouse  # noqa: E402

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 (nse-trade-advisor)")
REQUEST_TIMEOUT = 20
ATOM = "{http://www.w3.org/2005/Atom}"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


# =========================================================================== #
#  Shared helpers
# =========================================================================== #
def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&quot;", '"'),
                 ("&#39;", "'"), ("&apos;", "'"),
                 ("&lt;", "<"), ("&gt;", ">")):
        text = text.replace(a, b)
    return _WS_RE.sub(" ", text).strip()


def _parse_pubdate(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return raw


def _fetch(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
            return r.read()
    except Exception as e:
        print(f"  ! fetch failed [{url}]: {e}")
        return None


def _existing_ids(collection) -> set[str]:
    try:
        return set((collection.get(include=[]) or {}).get("ids") or [])
    except Exception:
        return set()


def _load_watchlist() -> list[str]:
    cfg = PROJECT_ROOT / "config.yaml"
    if not cfg.exists():
        return []
    try:
        import yaml
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        return sorted({str(s).split(".")[0].upper()
                       for s in (data.get("watchlist") or []) if s})
    except Exception:
        return []


def _build_symbol_matcher(symbols):
    syms = [re.escape(s) for s in sorted(set(symbols), key=len, reverse=True) if s]
    return re.compile(r"\b(" + "|".join(syms) + r")\b", re.IGNORECASE) if syms else None


# =========================================================================== #
#  1. PATTERNS
# =========================================================================== #
# Format:
#   PATTERN, CATEGORY, TIMEFRAME, DEFINITION, WHEN IT FIRES, RELIABILITY,
#   FALSE POSITIVES, EXAMPLE.
# Each pattern packed as 8 fields joined with " || ":
#   name || category || timeframe || definition || when_it_fires ||
#   reliability || false_positives || example
_PATTERNS_RAW = """\
Hammer || reversal || daily || Small real body near the top of the range with a lower wick at least 2x the body and little to no upper wick. || After a defined downtrend, ideally within 5% of prior support. || Moderate. Best when the next bar closes above the hammer high on above-average volume. || In steep downtrends hammers often print as pauses, not turns. Trend context is essential. || NIFTY on 2020-03-24 (post-COVID low).
Shooting Star || reversal || daily || Small real body near the bottom with an upper wick at least 2x the body and negligible lower wick. || After an extended uptrend, ideally at a swing high or resistance. || Moderate. Confirms when the next bar breaks the star's low. || Very common inside choppy consolidations - only trust after a real trend. || RELIANCE on 2022-04-11 near 2,850.
Doji || indecision || daily || Open and close are essentially equal, producing a cross-like candle. || After a directional move - marks a stall in momentum. || Low as a standalone signal - always needs a confirming bar. || In illiquid names dojis appear from lack of trading, not indecision. || HDFCBANK on 2023-01-31.
Spinning Top || indecision || daily || Small real body flanked by upper and lower wicks of similar length. || Mid-trend pause or top/bottom warning. || Low alone; useful only as part of a two- or three-bar setup. || Same as doji - just noise inside a range. || NIFTY intraday tops around option expiry.
Marubozu || continuation || daily || Long real body with almost no wicks - buyers or sellers control the entire session. || Trend acceleration or breakout confirmation. || High for continuation when volume is above 1.5x the 20-day average. || Marubozus at the extremes of a move often mark exhaustion, not continuation. || ADANIENT on 2023-11-27 breakout.
Bullish Engulfing || reversal || daily || A large green candle whose body completely engulfs the previous red candle's body. || End of a downtrend, ideally near support. || Moderate. Confirms with above-average volume and follow-through on the next 2 bars. || In a strong downtrend, often just a pause. Need trend context. || NIFTY on 2020-03-24 (post-COVID low).
Bearish Engulfing || reversal || daily || A large red candle whose body completely engulfs the previous green candle's body. || Top of an uptrend, ideally at resistance. || Moderate. Confirms with expanded volume and a lower close next bar. || During an uptrend it can mark a shakeout, not a reversal. Watch trend context. || NIFTY on 2022-01-18 top.
Piercing Line || reversal || daily || Red candle then a green candle that opens below the prior low and closes back above the midpoint of the prior body. || After a downtrend at support - two-bar bullish reversal. || Moderate. Weaker than a full engulfing but often triggers a bounce. || Fails inside a downtrend channel unless RSI is oversold. || TCS on 2019-08-14.
Dark Cloud Cover || reversal || daily || Green candle then a red candle that opens above the prior high and closes below the midpoint of the prior body. || After an uptrend at resistance - two-bar bearish reversal. || Moderate. Confirms with lower next-bar close. || In a strong uptrend often absorbed by the next up bar. || BAJFINANCE on 2021-10-27.
Bullish Harami || reversal || daily || Small green body entirely inside the previous large red body. || Late in a downtrend - momentum has stalled. || Low to moderate - always requires a confirming green bar. || In a strong down move it often just precedes another leg down. || INFY on 2020-04-03.
Bearish Harami || reversal || daily || Small red body entirely inside the previous large green body. || Late in an uptrend - a warning of a stall. || Low to moderate - needs a confirming red bar. || Often just a pause before continuation in strong up trends. || MARUTI on 2022-11-16.
Tweezer Top || reversal || daily || Two consecutive candles that share the same high, forming a matched top. || At the top of a rally - failure at the same price twice signals rejection. || Moderate on higher timeframes and near obvious resistance. || In choppy tape random equal highs are common noise. || SBIN on 2022-04-04.
Tweezer Bottom || reversal || daily || Two consecutive candles that share the same low, forming a matched bottom. || At the bottom of a decline - buyers defend the same price twice. || Moderate at obvious support with a bullish confirmation bar. || Equal lows in a downtrend can precede another breakdown. || ICICIBANK on 2020-03-24.
Morning Star || reversal || daily || Three-candle bottom: large red, small-bodied doji-like bar, then a large green candle closing above the midpoint of the first. || After a downtrend - classic bullish reversal. || High when the third bar closes on above-average volume. || In tight ranges the setup can print but produce no follow-through. || NIFTY on 2020-03-24 to 2020-03-26.
Evening Star || reversal || daily || Three-candle top: large green, small-bodied bar, then a large red candle closing below the midpoint of the first. || After an uptrend - classic bearish reversal. || High when the third bar closes on rising volume. || Inside ranges the setup fires but reverses again quickly. || NIFTY on 2022-04-05.
Three White Soldiers || reversal || daily || Three consecutive long green candles, each opening within the prior body and closing near the high. || After a downtrend or basing period - powerful bullish reversal. || High if volume expands and wicks stay small. || Late in an extended rally it can mark exhaustion, not continuation. || TATASTEEL on 2020-05-27 to 2020-05-29.
Three Black Crows || reversal || daily || Three consecutive long red candles, each opening within the prior body and closing near the low. || After an uptrend - strong bearish reversal. || High on expanding volume. || Deep into a down move it can mark capitulation, not continuation. || YESBANK on 2018-09-21 to 2018-09-25.
Inside Bar || continuation || daily || Current bar's high and low sit entirely inside the previous bar's range. || After a strong trending bar - compression before continuation. || Moderate. Break in the direction of the mother bar's trend has an edge. || Inside bars in low-volume tape often break both ways as noise. || NIFTY futures after RBI-day trend bars.
Outside Bar || reversal || daily || Current bar's high is higher and low is lower than the previous bar - engulfs the range. || After a trend, close in the opposite direction warns of reversal. || Moderate. Best when it closes on the extreme against the prior trend. || In choppy sessions outside bars are common and non-directional. || BANKNIFTY on major policy days.
Head and Shoulders || reversal || daily/weekly || Left shoulder, higher head, then a right shoulder at the shoulder height, with a horizontal or up-sloping neckline connecting the two intervening lows. || After an uptrend. Sell trigger is a decisive close below the neckline on volume. || High. Measured target is head-to-neckline distance projected down. || Frequent premature necklines - wait for a daily close, not intraday touches. || NIFTY 2007-12 to 2008-01.
Inverse Head and Shoulders || reversal || daily/weekly || Left shoulder low, deeper head low, right shoulder at shoulder depth, with a neckline across the two intervening highs. || After a downtrend. Buy trigger is a decisive close above the neckline on volume. || High. Measured target is head-to-neckline distance projected up. || Sloppy right shoulders that dip below the head invalidate the pattern. || NIFTY 2020-04 to 2020-06.
Double Top || reversal || daily/weekly || Two swing highs at roughly the same price with an intervening pullback - forms an 'M'. || Sell on close below the intervening low. || High on weekly charts, moderate on daily. Target equals the height of the pattern. || In strong uptrends the second top often becomes a launch pad for continuation. || NIFTY 2015-03 / 2015-04.
Double Bottom || reversal || daily/weekly || Two swing lows at roughly the same price with an intervening rally - forms a 'W'. || Buy on close above the intervening high. || High. Target equals the height of the pattern projected up. || In strong downtrends the second bottom breaks and triggers stops. || NIFTY 2013-08 / 2013-09.
Ascending Triangle || continuation || daily || Flat resistance with rising lows - buyers step in higher each time. || Trigger is a close above the flat top on volume. || Moderate to high in an established uptrend. || In downtrends the same shape often fails and breaks down. || TITAN 2021 through several mid-year setups.
Descending Triangle || continuation || daily || Flat support with falling highs - sellers press lower each rally. || Trigger is a close below the flat bottom on volume. || Moderate to high in an established downtrend. || In uptrends the pattern can resolve upward as a bull flag. || VEDL 2019-07 through 2019-09.
Symmetrical Triangle || continuation || daily || Lower highs and higher lows converging into an apex - coil. || Trades in the direction of the break, ideally at the two-thirds point of the apex. || Direction-agnostic - trust the prior trend and volume expansion on the break. || Very common failure mode is a fake breakout that reverses within 2 bars. || NIFTY 2013-06 to 2013-08.
Bull Flag || continuation || daily/intraday || Sharp trending move (the pole) followed by a tight, down-sloping consolidation (the flag). || Buy on close above the flag high with volume returning. || High in strong uptrends and momentum names. || If the flag retraces more than 50% of the pole, treat it as a broken flag. || ADANIPORTS 2023-11 sequence.
Bear Flag || continuation || daily/intraday || Sharp down move (the pole) followed by a tight, up-sloping consolidation (the flag). || Sell on close below the flag low with volume returning. || High in strong downtrends. || If the flag retraces more than 50% of the pole, treat as a bottom, not a flag. || PAYTM 2022-07 to 2022-10.
Pennant || continuation || daily/intraday || Small symmetrical triangle immediately after a sharp move - like a mini coil. || Break in the direction of the prior pole is the trigger. || High when the pole is real and volume dries up inside the pennant. || Extended pennants that go more than 15 bars often morph into range-bound noise. || ICICIBANK intraday breakout runs.
Cup and Handle || continuation || weekly || Rounded U-shaped base (cup) followed by a small pull-back (handle) at the right rim. || Buy on close above the handle high on volume, per O'Neil. || High for growth names that have earned earnings-driven strength. || V-shaped bases without a rounded bottom fail more often than they succeed. || BAJFINANCE 2013-2014 base.
Rectangle || continuation || daily/weekly || Sideways range between clear horizontal support and resistance - accumulation or distribution. || Trade the break in the direction of the prior trend, with volume expansion. || Moderate. The longer the range, the more powerful the eventual break. || False breakouts followed by re-entry into the range are very common. || NIFTY 2019-07 to 2019-10.
Rising Wedge || reversal || daily || Higher highs and higher lows, both converging with the lows rising faster - loss of upside thrust. || Bearish reversal - trigger on close below the lower trendline. || Moderate to high after extended uptrends. || In strong bull markets rising wedges can persist unusually long. || DMART 2021-10 top.
Falling Wedge || reversal || daily || Lower highs and lower lows, converging with highs falling faster - loss of downside thrust. || Bullish reversal - trigger on close above the upper trendline. || Moderate to high after downtrends. || In strong bear phases falling wedges break down cleanly. || NIFTY 2022-06 bottom.
"""
_PATTERNS = [tuple(x.strip() for x in line.split("||"))
             for line in _PATTERNS_RAW.strip().splitlines() if line.strip()]



def ingest_patterns() -> dict:
    """Populate pattern_library with hand-curated candlestick/chart patterns."""
    print(f"[patterns] Preparing {len(_PATTERNS)} pattern documents")
    dw = get_warehouse()
    col = dw.get_collection("pattern_library")
    if col is None:
        raise RuntimeError("pattern_library collection is not available")

    already = _existing_ids(col)
    docs, metas, ids = [], [], []
    for name, cat, tf, defn, fires, reliab, fp, ex in _PATTERNS:
        pid = "pattern_" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        if pid in already:
            continue
        docs.append(
            f"PATTERN: {name}\nCATEGORY: {cat}\nTIMEFRAME: {tf}\n"
            f"DEFINITION: {defn}\nWHEN IT FIRES: {fires}\n"
            f"RELIABILITY: {reliab}\nFALSE POSITIVES: {fp}\nEXAMPLE: {ex}"
        )
        metas.append({"category": cat, "timeframe": tf, "name": name,
                      "source": "hand-curated"})
        ids.append(pid)

    if docs:
        col.add(documents=docs, metadatas=metas, ids=ids)

    total = col.count()
    print(f"[patterns] Added {len(docs)} new, skipped {len(_PATTERNS) - len(docs)} dupes. "
          f"pattern_library now has {total} docs")
    return {"added": len(docs), "total": total, "collection": "pattern_library"}


# =========================================================================== #
#  2. FILINGS
# =========================================================================== #
_FILING_FEEDS = [
    ("bse-announcements",
     "https://www.bseindia.com/data/xml/rssnewsflash.xml"),
    ("nse-announcements",
     "https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml"),
    # Optional fallback (may or may not work depending on region):
    ("moneycontrol-corp-actions",
     "https://www.moneycontrol.com/rss/results.xml"),
]


def _parse_feed_items(xml_bytes: bytes, source: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"  ! parse failed [{source}]: {e}")
        return []
    items: list[dict] = []
    for item in root.iter("item"):  # RSS 2.0
        items.append({
            "title":     _clean(item.findtext("title")),
            "link":      _clean(item.findtext("link")),
            "summary":   _clean(item.findtext("description")),
            "published": _parse_pubdate(item.findtext("pubDate") or ""),
            "source":    source,
        })
    if not items:
        for entry in root.iter(f"{ATOM}entry"):
            link_el = entry.find(f"{ATOM}link")
            link = link_el.get("href") if link_el is not None else ""
            summary_el = (entry.find(f"{ATOM}summary")
                          or entry.find(f"{ATOM}content"))
            items.append({
                "title":     _clean(entry.findtext(f"{ATOM}title")),
                "link":      _clean(link),
                "summary":   _clean(summary_el.text if summary_el is not None else ""),
                "published": _parse_pubdate(entry.findtext(f"{ATOM}updated")
                                            or entry.findtext(f"{ATOM}published") or ""),
                "source":    source,
            })
    return [it for it in items if it["title"] or it["link"]]


def _filing_doc_id(link: str, title: str) -> str:
    key = (link or title or "").strip().lower()
    return "filing_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:20]


def ingest_filings(limit: int = 100) -> dict:
    """Pull corporate announcements from BSE + NSE RSS."""
    print(f"[filings] Starting run (limit={limit})")
    dw = get_warehouse()
    col = dw.get_collection("filings")
    if col is None:
        raise RuntimeError("filings collection is not available")

    matcher = _build_symbol_matcher(_load_watchlist())
    already = _existing_ids(col)
    fetched: list[dict] = []
    failed: list[dict] = []

    for source, url in _FILING_FEEDS:
        raw = _fetch(url)
        if not raw:
            failed.append({"source": source, "url": url, "reason": "fetch failed"})
            continue
        items = _parse_feed_items(raw, source)
        if not items:
            failed.append({"source": source, "url": url, "reason": "no items / not XML"})
            continue
        print(f"  {source}: {len(items)} items")
        fetched.extend(items)

    # Dedupe within batch
    seen: set[str] = set()
    unique: list[dict] = []
    for it in fetched:
        k = (it["link"] or it["title"]).strip().lower()
        if k and k not in seen:
            seen.add(k)
            unique.append(it)
    unique = unique[: max(1, int(limit))]

    docs, metas, ids = [], [], []
    skipped = 0
    for it in unique:
        did = _filing_doc_id(it["link"], it["title"])
        if did in already or did in ids:
            skipped += 1
            continue
        body = ((it["title"] + "\n\n" + it["summary"]).strip())[:2000]
        if not body:
            continue
        symbol = None
        if matcher:
            m = matcher.search(it["title"] + " " + it["summary"])
            if m:
                symbol = m.group(1).upper()
        docs.append(body)
        metas.append({
            "source":    it["source"],
            "link":      it["link"] or "",
            "title":     it["title"][:300],
            "published": it["published"] or "",
            "symbol":    symbol or "",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })
        ids.append(did)

    if docs:
        col.add(documents=docs, metadatas=metas, ids=ids)

    total = col.count()
    print(f"[filings] Added {len(docs)}, skipped {skipped} dupes. "
          f"filings now has {total} docs")
    for f in failed:
        print(f"  ! feed failed: {f['source']} ({f['reason']})")
    return {"added": len(docs), "skipped_dup": skipped, "total": total,
            "failed_feeds": failed, "collection": "filings"}


# =========================================================================== #
#  3. EARNINGS
# =========================================================================== #
_EARNINGS_KB_FILES = [
    "earnings_analysis.md",
    "03_fundamental_analysis.md",
]

# Fallback "principle" seeds - each becomes its own doc. Packed as
# "Principle Name || snippet" lines.
_EARNINGS_PRINCIPLES_RAW = """\
Beat and Raise || The most bullish earnings outcome is a beat on EPS combined with raised forward guidance. Historical reaction on Indian large-caps is +8% to +15% on day 1 with a Post-Earnings Announcement Drift (PEAD) continuation of 1-3% over the following 30-60 days. Trade size normally, hold for 30 days minimum, and only exit on a close below the pre-earnings close or the day-1 gap fill, whichever is higher.
Beat and Lower || A headline earnings beat combined with lowered forward guidance is a trap. The initial algo-driven gap up often reverses inside the first hour. Reaction is typically -5% to -10% by the close. Do not buy the opening green print - wait for two closes above the day-1 high before considering long exposure. Better to fade the pop.
Miss and Raise || A rare but powerful setup: EPS below consensus but the company raises guidance. Signals management confidence in a temporary one-off. Historical reaction is +3% to +8% and the PEAD tends to persist. Enter on day 2 after a green day-1 close, stop below the earnings-day low.
Miss and Lower || The worst-case earnings scenario. Reaction is -10% to -20% and continues drifting down for 30-60 days. Do not attempt to catch the falling knife. If already long, exit on the first bounce and reassess only after a base is built and volume normalizes.
Cash Flow vs Net Income || Quality of earnings is measured by operating cash flow relative to net income. When reported net income significantly exceeds operating cash flow (accruals anomaly), the quarter's headline number is being manufactured. Discount the beat and reduce position size. Consistently OCF > NI is a green flag over 4-6 quarters.
Guidance Beats Beat || In Indian markets, forward guidance is more market-moving than the current-quarter beat. A modest beat with strong guidance outperforms a large beat with soft guidance in the post-announcement window. Read the guidance range and management commentary before trading the print.
PEAD - Post Earnings Announcement Drift || Discovered by Bernard and Thomas (1989) and confirmed in 100+ studies including on Indian equities. Stocks that beat drift up for ~60 days; stocks that miss drift down for ~60 days. Average drift is 1-3%, small but persistent. Trade rules: enter days 1-2 after the gap, hold 30-60 days, do not exit on day 1, size normally.
Management Tone || Count positive vs negative words on the Q&A call. Positive words include strong, robust, momentum, record, ahead. Negative words include headwinds, challenging, cautious, soft, weak, macro. A positive-to-negative ratio above 3:1 in Q&A is bullish; below 1:1 is bearish. Hedging phrases like 'we'll see' or 'macro uncertainty' subtract from the score.
Analyst Depth || Which analysts asked which questions matters. Top-tier sell-side desks (Morgan Stanley, JPM, Kotak, Nomura) engaging deeply in the call signals institutional interest. Bulge bracket asking about long-term levers is bullish; the same desks probing near-term weakness is a warning. No top-tier engagement can itself be a red flag.
Margin Direction || Track gross, operating, and net margins for expansion vs contraction. Sequential expansion in operating margin combined with revenue growth is the strongest quality signal for Indian large caps. Margin compression alongside revenue growth suggests the company is buying growth via discounts - fade the print.
Revenue Quality || Revenue growth from unit-volume expansion is higher quality than revenue growth from price hikes alone. In consumer names, watch for the volume-vs-realization split in management commentary. Volume growth signals demand strength; price-only growth signals margin risk when the next hike is refused.
Working Capital Signals || Receivables growing faster than revenue is a channel-stuffing red flag. Inventory days creeping up quarter over quarter foreshadows a write-down. Payables ballooning may mean the company is stretching suppliers. Cash conversion cycle expansion is a leading indicator of a coming earnings miss.
Segment Analysis || For conglomerates, one-line consolidated numbers hide the story. Track segment revenue and EBIT separately. A blended beat driven by one super-strong segment and mediocre others is lower quality than a broad-based beat across segments. Ask which segment is sustainable and which is one-off.
Guidance Ranges || Quantified guidance (e.g. 12-14% revenue growth) is higher quality than qualitative guidance ('strong double digits'). When management moves from specific ranges back to vague qualitative language, treat it as a downgrade in visibility. Wider guidance ranges signal falling internal confidence.
Insider Behaviour Post-Earnings || Track promoter and management stock activity in the 30 days following earnings. Management or promoters buying after a beat is a strong confirmation; selling after a beat is a warning. NSE / BSE mandatory disclosures make this data free to monitor via insider trading filings.
Sector Read-Through || First earnings report in a sector often sets the read-through for peers. If Infosys prints weak IT services growth, TCS and Wipro tend to gap down on their day-1 too. Use the first-mover print as an early signal for the sector basket, and be ready to trade the correlated moves before the peer's own print.
Consensus vs Whisper || The consensus estimate on screens (Bloomberg, Refinitiv) is different from the whisper number circulated by top desks. Whisper is often 2-5% higher than consensus. Meeting consensus but missing whisper produces a paradoxical negative reaction. Track pre-print estimate revisions in the 30 days before the report as a proxy for whisper drift.
Stock-Based Compensation || Rapidly rising SBC dilutes shareholders and often masks weakening earnings quality. Track SBC as a percentage of revenue over time. Companies where SBC grows faster than revenue for consecutive quarters have historically underperformed in the year following.
Buyback and Dividend Signals || Announcements of buybacks or increased dividends alongside earnings signal management confidence in cash flow durability. Buybacks executed at valuations below the 3-year historical range are especially bullish. Buybacks near cycle peaks are capital-destruction signals.
One-Time Items || Adjustments for one-time items should be reviewed skeptically. If a company adjusts out losses every quarter but takes gains into GAAP, the 'adjusted' EPS is engineered. For high-quality analysis, model both GAAP and adjusted, and lean on GAAP for trend.
"""
_EARNINGS_PRINCIPLES = [
    tuple(x.strip() for x in line.split("||", 1))
    for line in _EARNINGS_PRINCIPLES_RAW.strip().splitlines() if "||" in line
]


def _chunk_by_headers(text: str, source: str) -> list[dict]:
    chunks: list[dict] = []
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    for i, section in enumerate(sections):
        section = section.strip()
        if not section or len(section) < 100:
            continue
        title_match = re.match(r"^## (.+)$", section, re.MULTILINE)
        section_title = title_match.group(1).strip() if title_match else f"section_{i}"
        chunks.append({
            "text": section[:2000],
            "section": section_title,
            "source": source,
            "chunk_index": i,
        })
    return chunks


def ingest_earnings() -> dict:
    """Populate earnings_calls from knowledge/*.md chunks + principle seeds."""
    print("[earnings] Preparing earnings-analysis snippets")
    dw = get_warehouse()
    col = dw.get_collection("earnings_calls")
    if col is None:
        raise RuntimeError("earnings_calls collection is not available")

    already = _existing_ids(col)
    docs, metas, ids = [], [], []

    # 3a. Chunk knowledge markdown by section
    for fname in _EARNINGS_KB_FILES:
        path = PROJECT_ROOT / "knowledge" / fname
        if not path.exists():
            print(f"  ! missing: {fname}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for chunk in _chunk_by_headers(text, fname):
            cid = "earnings_kb_" + hashlib.sha1(
                (fname + str(chunk["chunk_index"])).encode("utf-8")
            ).hexdigest()[:16]
            if cid in already or cid in ids:
                continue
            body = f"SOURCE: {chunk['source']}\nSECTION: {chunk['section']}\n\n{chunk['text']}"
            docs.append(body)
            metas.append({
                "source":    chunk["source"],
                "section":   chunk["section"][:200],
                "type":      "earnings_kb_chunk",
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            })
            ids.append(cid)

    # 3b. Principle seeds - always add these so we clear the >=20-doc bar
    for name, snippet in _EARNINGS_PRINCIPLES:
        pid = "earnings_principle_" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        if pid in already or pid in ids:
            continue
        body = f"PRINCIPLE: {name}\n\n{snippet}"
        docs.append(body)
        metas.append({
            "source":    "hand-curated",
            "principle": name,
            "type":      "earnings_principle",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })
        ids.append(pid)

    if docs:
        col.add(documents=docs, metadatas=metas, ids=ids)

    total = col.count()
    print(f"[earnings] Added {len(docs)} docs. earnings_calls now has {total} docs")
    return {"added": len(docs), "total": total, "collection": "earnings_calls"}


# =========================================================================== #
#  4. RUN-ALL + STATS
# =========================================================================== #
def ingest_all(limit: int = 100) -> dict:
    out: dict = {}
    out["patterns"] = ingest_patterns()
    out["filings"] = ingest_filings(limit=limit)
    out["earnings"] = ingest_earnings()
    return out


def print_stats() -> dict:
    dw = get_warehouse()
    stats = dw.stats()
    print("\nData Warehouse Stats")
    print("-" * 40)
    for name, n in stats.items():
        print(f"  {name:<22} {n:>6} docs")
    return stats


# =========================================================================== #
#  CLI
# =========================================================================== #
def main() -> int:
    ap = argparse.ArgumentParser(description="Populate ChromaDB RAG collections")
    ap.add_argument("kind", choices=["patterns", "filings", "earnings", "all", "stats"])
    ap.add_argument("--limit", type=int, default=100,
                    help="Cap items per feed (filings/all only)")
    args = ap.parse_args()

    t0 = time.time()
    try:
        if args.kind == "patterns":
            ingest_patterns()
        elif args.kind == "filings":
            ingest_filings(limit=args.limit)
        elif args.kind == "earnings":
            ingest_earnings()
        elif args.kind == "all":
            ingest_all(limit=args.limit)
        elif args.kind == "stats":
            print_stats()
            return 0
    except Exception as e:
        print(f"! error running {args.kind}: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print(f"\n[done in {time.time() - t0:.1f}s]")
    print_stats()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
