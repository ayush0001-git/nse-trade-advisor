"""
agents/__init__.py - 5 specialized AI agents for professional stock analysis.

Each agent has a single responsibility and returns a structured opinion.
The orchestrator combines them into the final 100-point score.

Agents:
  1. NewsHunter      - news + earnings + filings sentiment
  2. TechnicalAnalyst - price action + indicators + patterns + options flow
  3. QuantResearcher - strategy signals + backtested edge
  4. RiskManager     - R:R, position sizing, vetoes, drawdown control
  5. PortfolioManager - combines all into final score + retrieves RAG rules
"""
from .news_hunter import NewsHunter
from .technical_analyst import TechnicalAnalyst
from .quant_researcher import QuantResearcher
from .risk_manager import RiskManager
from .portfolio_manager import PortfolioManager

__all__ = [
    "NewsHunter",
    "TechnicalAnalyst",
    "QuantResearcher",
    "RiskManager",
    "PortfolioManager",
]
