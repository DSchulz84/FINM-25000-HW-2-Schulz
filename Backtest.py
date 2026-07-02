#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd

def run_backtest_engine(data, signal_column, initial_capital=100000.0):
    df_engine = data.copy()
    cash = initial_capital
    shares_held = 0.0
    portfolio_values = []
    trades = []
    active_trade = None 

    for i in range(len(df_engine)):
        current_price = df_engine['close'].iloc[i]
        current_date = df_engine.index[i]
        signal = df_engine[signal_column].iloc[i]

        if signal == 1 and shares_held == 0:
            shares_held = cash / current_price
            cash = 0.0
            active_trade = {"Entry Date": current_date, "Entry Price": current_price}
        elif signal == 0 and shares_held > 0:
            cash = shares_held * current_price
            shares_held = 0.0
            active_trade["Exit Date"] = current_date
            active_trade["Exit Price"] = current_price
            active_trade["Raw_ROI"] = (current_price - active_trade['Entry Price']) / active_trade['Entry Price']
            trades.append(active_trade)
            active_trade = None

        current_portfolio_value = cash + (shares_held * current_price)
        portfolio_values.append(current_portfolio_value)

    df_engine[f'{signal_column}_PV'] = portfolio_values
    df_engine[f'{signal_column}_DailyReturn'] = df_engine[f'{signal_column}_PV'].pct_change().fillna(0)
    peak = df_engine[f'{signal_column}_PV'].cummax()
    df_engine[f'{signal_column}_DD'] = (df_engine[f'{signal_column}_PV'] - peak) / peak
    return df_engine, pd.DataFrame(trades)

