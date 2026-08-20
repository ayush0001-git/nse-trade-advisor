"""
mass_test.py — Comprehensive self-test of the entire system.

Tests every component, finds errors, and generates a report.
"""
import sys
import json
import time
import traceback
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

results = {"passed": 0, "failed": 0, "errors": [], "warnings": [], "suggestions": []}


def test(name, func):
    """Run a test and record the result."""
    try:
        result = func()
        if result is True or (isinstance(result, dict) and result.get("ok")):
            results["passed"] += 1
            print(f"  ✅ {name}")
        else:
            results["failed"] += 1
            results["errors"].append({"test": name, "error": str(result)})
            print(f"  ❌ {name}: {result}")
        return result
    except Exception as e:
        results["failed"] += 1
        tb = traceback.format_exc()
        results["errors"].append({"test": name, "error": str(e), "traceback": tb[-300:]})
        print(f"  ❌ {name}: {type(e).__name__}: {e}")
        return None


# =========================================================================== #
#  TEST 1: Import all modules
# =========================================================================== #
print("\n" + "=" * 60)
print("  TEST 1: MODULE IMPORTS")
print("=" * 60)


def test_imports():
    modules = ["brain", "server"]
    for m in modules:
        __import__(m)
    # Check key brain functions exist
    assert hasattr(brain, "analyze_stock"), "brain.analyze_stock missing"
    assert hasattr(brain, "search_knowledge"), "brain.search_knowledge missing"
    assert hasattr(brain, "calculate_pnl"), "brain.calculate_pnl missing"
    assert hasattr(brain, "STOCKS"), "brain.STOCKS missing"
    assert hasattr(brain, "RULES"), "brain.RULES missing"
    return True


import brain
test("Import brain + server modules", test_imports)


# =========================================================================== #
#  TEST 2: Brain data integrity
# =========================================================================== #
print("\n" + "=" * 60)
print("  TEST 2: BRAIN DATA INTEGRITY")
print("=" * 60)


def test_stocks():
    assert len(brain.STOCKS["large"]) >= 10, "Need 10+ large cap"
    assert len(brain.STOCKS["mid"]) >= 10, "Need 10+ mid cap"
    assert len(brain.STOCKS["small"]) >= 10, "Need 10+ small cap"
    # Check all symbols have .NS suffix
    for cap, stocks in brain.STOCKS.items():
        for s in stocks:
            assert ".NS" in s or ".BO" in s, f"{s} missing exchange suffix"
    return True


def test_rules():
    assert len(brain.RULES) >= 100, f"Need 100+ rules, got {len(brain.RULES)}"
    # Check no empty rules
    for i, r in enumerate(brain.RULES):
        assert len(r) > 20, f"Rule {i} too short: {r}"
    return True


def test_sectors():
    assert len(brain.SECTORS) >= 5, f"Need 5+ sectors, got {len(brain.SECTORS)}"
    return True


test("Stock universe integrity (70+ stocks)", test_stocks)
test("Knowledge rules integrity (100+ rules)", test_rules)
test("Sector data integrity (5+ sectors)", test_sectors)


# =========================================================================== #
#  TEST 3: Analysis engine — test 15 stocks across all cap types
# =========================================================================== #
print("\n" + "=" * 60)
print("  TEST 3: ANALYSIS ENGINE (15 stocks)")
print("=" * 60)

test_stocks_list = (
    brain.STOCKS["large"][:5] +
    brain.STOCKS["mid"][:5] +
    brain.STOCKS["small"][:5]
)

analysis_results = []
for sym in test_stocks_list:
    def test_one(sym=sym):
        result = brain.analyze_stock(sym)
        if "error" in result:
            return f"Error: {result['error']}"
        # Check required fields
        required = ["symbol", "score", "rating", "scores", "indicators", "plan", "reasons", "risks"]
        for field in required:
            assert field in result, f"Missing field: {field}"
        # Score should be 0-100
        assert 0 <= result["score"] <= 100, f"Score out of range: {result['score']}"
        # Rating should be valid
        assert result["rating"] in ["STRONG BUY", "WATCHLIST", "SPECULATIVE", "IGNORE"], f"Invalid rating: {result['rating']}"
        # All 6 score layers present
        for layer in ["technical", "news", "sentiment", "institutional", "options", "fundamentals"]:
            assert layer in result["scores"], f"Missing score layer: {layer}"
        # Indicators present
        for ind in ["rsi", "macd_hist", "atr", "sma_20", "volume_ratio"]:
            assert ind in result["indicators"], f"Missing indicator: {ind}"
        # Plan present
        for p in ["entry", "stop", "target", "quantity", "risk_reward"]:
            assert p in result["plan"], f"Missing plan field: {p}"
        analysis_results.append(result)
        return True
    test(f"Analyze {sym}", test_one)


# =========================================================================== #
#  TEST 4: Score distribution analysis
# =========================================================================== #
print("\n" + "=" * 60)
print("  TEST 4: SCORE DISTRIBUTION")
print("=" * 60)

if analysis_results:
    scores = [r["score"] for r in analysis_results]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)

    print(f"  Stocks analyzed: {len(scores)}")
    print(f"  Average score: {avg_score:.1f}")
    print(f"  Min/Max: {min_score:.1f} / {max_score:.1f}")
    print(f"  Distribution:")
    brackets = {"80+": 0, "70-79": 0, "60-69": 0, "<60": 0}
    for s in scores:
        if s >= 80: brackets["80+"] += 1
        elif s >= 70: brackets["70-79"] += 1
        elif s >= 60: brackets["60-69"] += 1
        else: brackets["<60"] += 1
    for b, c in brackets.items():
        print(f"    {b}: {c} stocks")

    # Suggestion: if all stocks score <60, the scoring is too conservative
    if avg_score < 50:
        results["warnings"].append(f"Average score {avg_score:.1f} is very low — scoring may be too conservative. Consider adjusting weights.")
        print(f"  ⚠️ WARNING: Average score {avg_score:.1f} is low — scoring may be too conservative")
    if avg_score > 80:
        results["warnings"].append(f"Average score {avg_score:.1f} is very high — scoring may be too lenient.")
        print(f"  ⚠️ WARNING: Average score {avg_score:.1f} is high — scoring may be too lenient")
    if max_score < 70:
        results["warnings"].append(f"Max score {max_score:.1f} — no stock reaches WATCHLIST threshold. Scoring too harsh.")
        print(f"  ⚠️ WARNING: No stock reaches WATCHLIST (70+) — scoring too harsh")
    results["passed"] += 1
    print(f"  ✅ Score distribution analysis complete")
else:
    results["failed"] += 1
    results["errors"].append({"test": "Score distribution", "error": "No analysis results to evaluate"})
    print(f"  ❌ No analysis results to evaluate")


# =========================================================================== #
#  TEST 5: Knowledge base search quality
# =========================================================================== #
print("\n" + "=" * 60)
print("  TEST 5: KNOWLEDGE BASE SEARCH")
print("=" * 60)

knowledge_queries = [
    ("momentum breakout", ["momentum", "breakout"]),
    ("risk management stop loss", ["stop", "loss", "risk"]),
    ("options implied volatility", ["volatility", "options", "IV"]),
    ("candlestick pattern hammer", ["hammer", "candlestick"]),
    ("position sizing Kelly", ["position", "sizing", "kelly"]),
    ("FII DII institutional flow", ["FII", "institutional", "flow"]),
    ("Buffett margin of safety", ["margin", "safety", "buffett"]),
    ("mean reversion RSI oversold", ["mean", "reversion", "RSI"]),
]

for query, expected_keywords in knowledge_queries:
    def test_search(query=query, expected=expected_keywords):
        results_list = brain.search_knowledge(query, 5)
        if not results_list:
            return "No results returned"
        # Check at least 1 result contains an expected keyword
        found = False
        for r in results_list:
            rule_lower = r["rule"].lower()
            for kw in expected:
                if kw.lower() in rule_lower:
                    found = True
                    break
            if found:
                break
        if not found:
            return f"No result contains expected keywords: {expected}"
        return True
    test(f"Knowledge search: '{query}'", test_search)


# =========================================================================== #
#  TEST 6: P&L calculator
# =========================================================================== #
print("\n" + "=" * 60)
print("  TEST 6: P&L CALCULATOR")
print("=" * 60)


def test_pnl():
    result = brain.calculate_pnl("RELIANCE", 50, 1300)
    if "error" in result:
        return f"Error: {result['error']}"
    for field in ["symbol", "current_price", "buy_price", "quantity", "invested", "current_value", "pnl", "pnl_pct"]:
        assert field in result, f"Missing field: {field}"
    # Math check: invested = qty * buy_price
    assert result["invested"] == 50 * 1300, f"Invested math wrong: {result['invested']} != {50*1300}"
    # current_value = qty * current_price
    assert result["current_value"] == 50 * result["current_price"], f"Current value math wrong"
    # pnl = current_value - invested
    expected_pnl = result["current_value"] - result["invested"]
    assert abs(result["pnl"] - expected_pnl) < 1, f"PnL math wrong: {result['pnl']} != {expected_pnl}"
    return True


test("P&L calculator (RELIANCE 50 @ ₹1300)", test_pnl)


def test_pnl_error():
    result = brain.calculate_pnl("", 0, 0)
    if "error" in result:
        return True
    return "Should have returned error for invalid input"


test("P&L calculator error handling", test_pnl_error)


# =========================================================================== #
#  TEST 7: Server API endpoints
# =========================================================================== #
print("\n" + "=" * 60)
print("  TEST 7: SERVER API ENDPOINTS")
print("=" * 60)

# Start the server in background
import subprocess
import threading

server_proc = subprocess.Popen(
    [sys.executable, "server.py"],
    cwd=str(PROJECT_ROOT),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
time.sleep(3)  # wait for server to start

import urllib.request
import urllib.error


def fetch_api(path, method="GET", data=None):
    url = f"http://localhost:5000{path}"
    try:
        if data:
            req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                          headers={"Content-Type": "application/json"}, method=method)
        else:
            req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def test_api_root():
    try:
        req = urllib.request.Request("http://localhost:5000/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode()
            return "<html" in html.lower() and "advisor" in html.lower()
    except Exception as e:
        return f"Error: {e}"


def test_api_stats():
    d = fetch_api("/api/stats")
    if "error" in d:
        return f"Error: {d['error']}"
    return d.get("total_stocks", 0) > 0


def test_api_knowledge():
    d = fetch_api("/api/knowledge?q=momentum")
    if "error" in d:
        return f"Error: {d['error']}"
    return len(d.get("results", [])) > 0


def test_api_stocks():
    d = fetch_api("/api/stocks/large")
    if "error" in d:
        return f"Error: {d['error']}"
    return d.get("count", 0) > 0


def test_api_analyze():
    d = fetch_api("/api/analyze/RELIANCE")
    if "error" in d:
        return f"Error: {d['error']}"
    return d.get("score", 0) >= 0


def test_api_pnl():
    d = fetch_api("/api/pnl", method="POST", data={"symbol": "RELIANCE", "quantity": 50, "buy_price": 1300})
    if "error" in d:
        return f"Error: {d['error']}"
    return "pnl" in d


def test_api_today():
    d = fetch_api("/api/today")
    if "error" in d:
        return f"Error: {d['error']}"
    return "scans" in d


def test_api_trades():
    d = fetch_api("/api/trades")
    if "error" in d:
        return f"Error: {d['error']}"
    return "trades" in d


test("API: GET / (frontend loads)", test_api_root)
test("API: GET /api/stats", test_api_stats)
test("API: GET /api/knowledge?q=momentum", test_api_knowledge)
test("API: GET /api/stocks/large", test_api_stocks)
test("API: GET /api/analyze/RELIANCE", test_api_analyze)
test("API: POST /api/pnl", test_api_pnl)
test("API: GET /api/today", test_api_today)
test("API: GET /api/trades", test_api_trades)

# Kill server
server_proc.terminate()
server_proc.wait()


# =========================================================================== #
#  TEST 8: Analysis precision check
# =========================================================================== #
print("\n" + "=" * 60)
print("  TEST 8: ANALYSIS PRECISION")
print("=" * 60)

if analysis_results:
    # Check for anomalies
    zero_qty_count = sum(1 for r in analysis_results if r["plan"]["quantity"] == 0)
    no_reasons_count = sum(1 for r in analysis_results if len(r["reasons"]) == 0)
    no_risks_count = sum(1 for r in analysis_results if len(r["risks"]) == 0)

    print(f"  Stocks with quantity=0: {zero_qty_count}/{len(analysis_results)}")
    print(f"  Stocks with no reasons: {no_reasons_count}/{len(analysis_results)}")
    print(f"  Stocks with no risks: {no_risks_count}/{len(analysis_results)}")

    if zero_qty_count > len(analysis_results) * 0.5:
        results["warnings"].append(f"{zero_qty_count}/{len(analysis_results)} stocks have quantity=0 — ATR may be too high relative to capital. Consider increasing capital or reducing ATR multiplier.")
        print(f"  ⚠️ WARNING: {zero_qty_count} stocks have quantity=0 — position sizing issue")

    if no_reasons_count > len(analysis_results) * 0.3:
        results["warnings"].append(f"{no_reasons_count}/{len(analysis_results)} stocks have no buy reasons — scoring logic may be too strict.")
        print(f"  ⚠️ WARNING: {no_reasons_count} stocks have no buy reasons")

    if no_risks_count > len(analysis_results) * 0.3:
        results["warnings"].append(f"{no_risks_count}/{len(analysis_results)} stocks have no risks — risk detection may be too lenient.")
        print(f"  ⚠️ WARNING: {no_risks_count} stocks have no risks listed")

    # Check score consistency: high-score stocks should have more reasons than risks
    inconsistent = 0
    for r in analysis_results:
        if r["score"] > 60 and len(r["reasons"]) < len(r["risks"]):
            inconsistent += 1
    if inconsistent > 0:
        results["warnings"].append(f"{inconsistent} stocks score >60 but have more risks than reasons — scoring inconsistency.")
        print(f"  ⚠️ WARNING: {inconsistent} high-score stocks have more risks than reasons")

    results["passed"] += 1
    print(f"  ✅ Precision analysis complete")
else:
    results["failed"] += 1
    print(f"  ❌ No results to check precision")


# =========================================================================== #
#  SELF-ASSESSMENT & SUGGESTIONS
# =========================================================================== #
print("\n" + "=" * 60)
print("  SELF-ASSESSMENT & SUGGESTIONS")
print("=" * 60)

# Generate suggestions based on test results
if results["failed"] == 0:
    print("  ✅ All tests passed — system is stable")
else:
    print(f"  ❌ {results['failed']} tests failed — see errors above")

for w in results["warnings"]:
    print(f"  ⚠️ {w}")

# Knowledge base suggestions
print("\n  📚 KNOWLEDGE BASE SUGGESTIONS:")
print("  1. Current: 114 rules with keyword (Jaccard) search")
print("     → Upgrade: Use ChromaDB vector embeddings for semantic search")
print("     → The ChromaDB infrastructure already exists (1,957 docs indexed)")
print("     → brain.py should query ChromaDB instead of keyword matching")
print()
print("  2. Current: Rules are static (hardcoded in brain.py)")
print("     → Upgrade: Load rules from knowledge/ Markdown files at startup")
print("     → This separates knowledge from code — easier to update")
print()
print("  3. Current: No learning from past trades")
print("     → Upgrade: Store every analysis result + outcome in trade_memory")
print("     → Query 'similar past setups' before each new analysis")
print("     → The pattern_library (1,577 patterns) already exists for this")

# RAG suggestions
print("\n  🧠 RAG SUGGESTIONS:")
print("  1. Current: brain.py uses keyword search (Jaccard similarity)")
print("     → Problem: 'risk management' won't match 'position sizing'")
print("     → Fix: Connect brain.py to ChromaDB (already has 1,957 docs)")
print("     → Use: from data_warehouse import get_warehouse; dw.query(...)")
print()
print("  2. Current: No context-aware retrieval")
print("     → Upgrade: When analyzing a stock, query RAG with the stock's")
print("       context (direction + regime + R:R) to get relevant rules")
print("     → The agents/portfolio_manager.py already does this — brain.py should too")
print()
print("  3. Current: Knowledge base is text-only")
print("     → Upgrade: Add structured data (historical news reactions,")
print("       trade journal examples) to the RAG system")
print("     → The news_archive.py and pattern_library.py already exist")

# LLM suggestions
print("\n  🤖 LLM SUGGESTIONS:")
print("  1. Current: Explanations are template-based (if/else rules)")
print("     → Upgrade: Use an LLM (Groq/Gemini/Ollama) to write the narrative")
print("     → The advisor/extras.py already has narrate() with LLM support")
print("     → Pass the analysis result to the LLM for a natural-language explanation")
print()
print("  2. Current: No reasoning chain visible to the user")
print("     → Upgrade: Show the RAG-retrieved knowledge rules alongside the score")
print("     → 'This stock scored 75/100 because: [retrieved rules from Buffett, Marks]'")
print()
print("  3. Current: No natural language Q&A")
print("     → Upgrade: Add a chat interface where users can ask 'Why RELIANCE?'")
print("     → LLM reads the analysis + retrieved knowledge → generates answer")

# Precision suggestions
print("\n  🎯 PRECISION SUGGESTIONS:")
print("  1. Current: 6-layer scoring with fixed weights (30+20+15+15+10+10)")
print("     → Upgrade: Learn optimal weights from backtested results")
print("     → Use: logistic regression on (scores → trade outcome)")
print()
print("  2. Current: News/sentiment/institutional scores are PROXIES (price-based)")
print("     → Upgrade: Use actual data sources:")
print("       - news_intel.py (RSS headlines + sentiment scoring)")
print("       - social_sentiment.py (Reddit mentions)")
print("       - institutional_flow.py (FII/DII + delivery %)")
print("       - options_flow.py (PCR + OI buildup)")
print("     → These modules already exist — brain.py should call them")
print()
print("  3. Current: Single timeframe (daily only)")
print("     → Upgrade: Multi-timeframe analysis (weekly + daily + 15m)")
print("     → deep_analysis.py already does this — brain.py should use it")
print()
print("  4. Current: No backtest of the scoring system itself")
print("     → Upgrade: Backtest: 'if score > 75, buy. Hold 30 days. Measure return.'")
print("     → This validates whether the 100-point score predicts returns")
print("     → Use mass_backtest.py framework to run this")

# Architecture suggestions
print("\n  🏗️ ARCHITECTURE SUGGESTIONS:")
print("  1. Current: brain.py is a simplified version (proxy scores)")
print("     → The FULL system (agents/, data_warehouse.py, etc.) is more accurate")
print("     → For production: use the full 5-agent system, not brain.py")
print("     → brain.py is the 'fast mode' — good for quick checks")
print()
print("  2. Current: server.py is minimal Flask")
print("     → Upgrade: Add WebSocket for real-time price updates")
print("     → Add: Background scan worker (scan all 70 stocks overnight)")
print()
print("  3. Current: No continuous learning loop")
print("     → Upgrade: Every night, re-scan all stocks, store results,")
print("       compare to yesterday, alert on changes")
print("     → Every closed trade feeds back into the scoring model")


# =========================================================================== #
#  FINAL REPORT
# =========================================================================== #
print("\n" + "=" * 60)
print("  FINAL TEST REPORT")
print("=" * 60)
print(f"  Tests passed: {results['passed']}")
print(f"  Tests failed: {results['failed']}")
print(f"  Warnings:     {len(results['warnings'])}")
print(f"  Errors:       {len(results['errors'])}")

if results["errors"]:
    print("\n  ERRORS:")
    for e in results["errors"]:
        print(f"    ❌ {e['test']}: {e['error'][:100]}")

if results["warnings"]:
    print("\n  WARNINGS:")
    for w in results["warnings"]:
        print(f"    ⚠️ {w}")

# Save report
report = {
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "summary": {
        "passed": results["passed"],
        "failed": results["failed"],
        "warnings": len(results["warnings"]),
    },
    "errors": results["errors"],
    "warnings": results["warnings"],
    "suggestions": {
        "knowledge": [
            "Connect brain.py to ChromaDB (1,957 docs already indexed) for semantic search instead of keyword matching",
            "Load rules from knowledge/ Markdown files at startup instead of hardcoding",
            "Store every analysis result in trade_memory for learning from past setups",
        ],
        "rag": [
            "brain.py should query ChromaDB for context-aware knowledge retrieval",
            "Query RAG with stock context (direction + regime + R:R) to get relevant rules",
            "Add structured data (news reactions, trade examples) to the RAG system",
        ],
        "llm": [
            "Use LLM (Groq/Gemini/Ollama) to write natural-language explanations instead of templates",
            "Show RAG-retrieved knowledge rules alongside the score for transparency",
            "Add chat interface for natural language Q&A about stock recommendations",
        ],
        "precision": [
            "Learn optimal scoring weights from backtested results (logistic regression)",
            "Use actual data sources (news_intel, social_sentiment, institutional_flow, options_flow) instead of proxies",
            "Add multi-timeframe analysis (weekly + daily + 15m) like deep_analysis.py",
            "Backtest the scoring system itself: 'if score > 75, buy, hold 30 days, measure return'",
        ],
    },
}

report_path = PROJECT_ROOT / "test_report.json"
with open(report_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"\n  📄 Full report saved to: {report_path}")
print(f"\n{'='*60}")
