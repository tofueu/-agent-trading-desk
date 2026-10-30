# Current status and acceptance plan

## Published state
Remote PR #10 is at `76b01c1aaf804b21d49b5dad2b7a3195c2d1b6c0`. It strengthens parsing and five-year-span validation in the trading dashboard.

## Not accepted
A dashboard plus fixtures is not evidence of real historical results. No complete, traceable production backtest import or final ranking has been verified.

## Required next delivery
1. Ingest only source-traceable backtest CSVs and fail closed when data is incomplete.
2. Display date range, source, fees/slippage, trades, return, CAGR, max drawdown, win rate and profit factor without fabricated fallbacks.
3. Run end-to-end tests and publish exact SHA/PR. Never enable live trading, modify main or merge.
