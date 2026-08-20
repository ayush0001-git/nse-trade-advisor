#!/usr/bin/env python3
"""
run.py - entry point for the advisory trading assistant.

Examples
--------
    python run.py analyze RELIANCE
    python run.py analyze TATAMOTORS --intraday
    python run.py scan
    python run.py backtest INFY
    python run.py journal
    python run.py log SBIN --note "ORB breakout"
    python run.py close 1 845.50
    python run.py news HDFCBANK
    python run.py config

This tool is advisory only. It never connects to your broker and never places
an order. You review its analysis and trade manually. Not investment advice.
"""
from advisor.cli import main

if __name__ == "__main__":
    main()
