# FINM-25000-HW-2-Schulz
Built streamlit application to backtest different investment strategies against historical data for a variety of stocks. Analysed performence metrics for all stratigies, and created price chart, equity curve, and drawdown chart for visual analysis. Code was written with the assistance of Gemini.Google AI.

## Features

* **Streamlit backtester:** Connects to Alpaca via API, pulls historical stock data, and backtests using trading strategies.
* **Performance metrics:** Produces a table of metrics including total return, volitility, Sharpe ratio, and win rate.
* **Graphical Representation:** Creates plotly charts graphing buy/sell signals, indicators, portfolio performance, and drawdown.

```bash
pip install alpaca-py pandas data-science-types streamlit numpy plotly
