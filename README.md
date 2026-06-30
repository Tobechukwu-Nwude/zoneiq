# ZoneIQ

A multi-pair forex scanner that detects supply and demand zones, analyses higher timeframe bias, and ranks live trade setups by quality.

Built on the trading methodology of supply and demand zone trading: identifying institutional zones where price is likely to react, aligning trades with the dominant trend, and filtering by risk-to-reward ratio.

## Stack

- **Backend:** Python, FastAPI
- **Data:** yfinance (development), planned migration to OANDA for live trading
- **AI Layer:** Claude API for natural language trade analysis
- **Frontend:** React with TradingView Lightweight Charts (planned)

## Pairs Scanned

EURUSD, GBPUSD, USDJPY, GBPJPY, XAUUSD, AUDUSD, USDCAD, EURCAD

## Timeframes

D1 (bias), H4 (zone identification), H1 (entry refinement)

## Status

In active development.

## Disclaimer

This tool is for educational and informational purposes. Forex trading involves significant risk. Always apply your own analysis before placing any trade.