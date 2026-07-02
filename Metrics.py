#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import numpy as np
import pandas as pd

def calculate_performance_metrics(df_vector, portfolio_col, daily_return_col, trades_df, trading_days=252):
    portfolio_series = df_vector[portfolio_col]
    daily_returns = df_vector[daily_return_col]
    total_return = (portfolio_series.iloc[-1] - portfolio_series.iloc[0]) / portfolio_series.iloc[0]
    years = len(df_vector) / trading_days
    cagr = (portfolio_series.iloc[-1] / portfolio_series.iloc[0]) ** (1 / years) - 1 if portfolio_series.iloc[-1] > 0 else 0
    vol = daily_returns.std() * np.sqrt(trading_days)
    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(trading_days) if daily_returns.std() != 0 else 0

    downside_diffs = daily_returns.copy()
    downside_diffs[downside_diffs > 0] = 0
    downside_deviation = np.sqrt(np.mean(downside_diffs ** 2)) * np.sqrt(trading_days)
    sortino = (daily_returns.mean() * trading_days) / downside_deviation if downside_deviation != 0 else 0

    max_dd = df_vector[portfolio_col.replace('_PV', '_DD')].min()
    win_rate = (trades_df['Raw_ROI'] > 0).sum() / len(trades_df) if not trades_df.empty else 0

    return {
        "Total Return": f"{total_return * 100:.2f}%",
        "CAGR": f"{cagr * 100:.2f}%",
        "Volatility": f"{vol * 100:.2f}%",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Sortino Ratio": f"{sortino:.2f}",
        "Max Drawdown": f"{max_dd * 100:.2f}%",
        "Win Rate": f"{win_rate * 100:.2f}%"
    }

