#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as pd
import streamlit as st
import datetime
import pandas as pd
import plotly.graph_objects as go
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Import module layers
from strategies import compute_indicators_and_signals
from backtest_engine import run_backtest_engine
from metrics import calculate_performance_metrics

st.set_page_config(page_title="Alpaca Trading Backtester", layout="wide")
st.title("Technical Indicators & Strategy Backtesting with Alpaca")

# Configuration & Authentication
ALPACA_API_KEY = "PKA53G7YAP6BKRPI2GIXTG36HM"
ALPACA_SECRET_KEY = "12uWk6tKDDT1CP6quUxmU1GtVe41xwixMXif59PtVjkR"

ticker_selection = st.sidebar.selectbox(
    "Select a Ticker Symbol",
    ["AAPL", "MSFT", "SPY", "JPM", "BA", "ZM", "KO", "XOM"]
)

if st.sidebar.button("Run Comprehensive Backtest", type="primary"):
    with st.spinner(f"Computing historical layers for {ticker_selection}..."):
        try:
            client = StockHistoricalDataClient(api_key=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY)
            end_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=20)
            start_date = end_date - datetime.timedelta(days=5 * 365)

            bars = client.get_stock_bars(StockBarsRequest(symbol_or_symbols=ticker_selection, timeframe=TimeFrame.Day, start=start_date, end=end_date))
            df = bars.df.reset_index(level=0, drop=True)

            # 1. Compute strategies/indicators
            df = compute_indicators_and_signals(df)

            # 2. Backtest engines
            df, s1_t = run_backtest_engine(df, 'S1_Signal')
            df, s2_t = run_backtest_engine(df, 'S2_Signal')
            df, s3_t = run_backtest_engine(df, 'S3_Signal')

            # 3. Buy and hold baseline logic
            df['BH_PV'] = (1 + df['close'].pct_change().fillna(0)).cumprod() * 100000.0
            df['BH_DailyReturn'] = df['BH_PV'].pct_change().fillna(0)
            df['BH_DD'] = (df['BH_PV'] - df['BH_PV'].cummax()) / df['BH_PV'].cummax()

            st.success("Analysis Complete!")
            st.subheader("Performance metrics")

            m_bh = calculate_performance_metrics(df, 'BH_PV', 'BH_DailyReturn', pd.DataFrame())
            m_s1 = calculate_performance_metrics(df, 'S1_Signal_PV', 'S1_Signal_DailyReturn', s1_t)
            m_s2 = calculate_performance_metrics(df, 'S2_Signal_PV', 'S2_Signal_DailyReturn', s2_t)
            m_s3 = calculate_performance_metrics(df, 'S3_Signal_PV', 'S3_Signal_DailyReturn', s3_t)

            matrix_summary = {
                "Analytics Metric": ["Total Return", "CAGR", "Volatility", "Sharpe Ratio", "Sortino Ratio", "Max Drawdown", "Win Rate"],
                "Buy & Hold (Baseline)": [m_bh["Total Return"], m_bh["CAGR"], m_bh["Volatility"], m_bh["Sharpe Ratio"], m_bh["Sortino Ratio"], m_bh["Max Drawdown"], m_bh["Win Rate"]],
                "Strategy 1 (Trend Following - EMA20)": [m_s1["Total Return"], m_s1["CAGR"], m_s1["Volatility"], m_s1["Sharpe Ratio"], m_s1["Sortino Ratio"], m_s1["Max Drawdown"], m_s1["Win Rate"]],
                "Strategy 2 (Enhanced Mean Reversion)": [m_s2["Total Return"], m_s2["CAGR"], m_s2["Volatility"], m_s2["Sharpe Ratio"], m_s2["Sortino Ratio"], m_s2["Max Drawdown"], m_s2["Win Rate"]],
                "Strategy 3 (Volatility Breakout)": [m_s3["Total Return"], m_s3["CAGR"], m_s3["Volatility"], m_s3["Sharpe Ratio"], m_s3["Sortino Ratio"], m_s3["Max Drawdown"], m_s3["Win Rate"]]
            }
            st.table(pd.DataFrame(matrix_summary).set_index("Analytics Metric"))
            st.markdown("---") 

            st.subheader("Charts")
            fig_price = go.Figure()
            fig_price.add_trace(go.Scatter(x=df.index, y=df['close'], name='Close Price', line=dict(color='#ffffff', width=1.5)))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], name='EMA 20 Center', line=dict(color='rgba(255,255,255,0.2)', dash='dash')))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['SMA_14'], name='SMA 14', line=dict(color='rgba(0,255,100,0.3)', dash='dot')))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['S2_Halfway_Line'], name='S2 Entry Threshold (Halfway)', line=dict(color='#ffaa00', width=1, dash='dashdot')))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='BB Upper Band', line=dict(color='rgba(0,209,255,0.2)')))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='BB Lower Band', line=dict(color='rgba(0,209,255,0.2)'), fill='tonexty'))

            s2_buys = df[df['S2_Signal'].diff() == 1]
            s2_sells = df[df['S2_Signal'].diff() == -1]
            fig_price.add_trace(go.Scatter(x=s2_buys.index, y=s2_buys['close'], mode='markers', name='S2 Early Entry', marker=dict(symbol='triangle-up', size=11, color='#ffaa00')))
            fig_price.add_trace(go.Scatter(x=s2_sells.index, y=s2_sells['close'], mode='markers', name='S2 Exit', marker=dict(symbol='triangle-down', size=11, color='#ff5500')))
            fig_price.update_layout(height=450, template='plotly_dark', margin=dict(l=20,r=20,t=10,b=20), hovermode='x unified')
            st.plotly_chart(fig_price, use_container_width=True)

            fig_equity = go.Figure()
            fig_equity.add_trace(go.Scatter(x=df.index, y=df['BH_PV'], name='Buy & Hold Baseline', line=dict(color='gray', width=1.5)))
            fig_equity.add_trace(go.Scatter(x=df.index, y=df['S1_Signal_PV'], name='Strategy 1: High ADX + Close>EMA20', line=dict(color='#00d1ff', width=2.5)))
            fig_equity.add_trace(go.Scatter(x=df.index, y=df['S2_Signal_PV'], name='Strategy 2: Enhanced Mean Reversion', line=dict(color='#ffaa00', width=2.5)))
            fig_equity.add_trace(go.Scatter(x=df.index, y=df['S3_Signal_PV'], name='Strategy 3: Volatility Breakout', line=dict(color='#cc00ff', width=2.5)))
            fig_equity.update_layout(height=450, template='plotly_dark', margin=dict(l=20,r=20,t=10,b=20), yaxis_title="Portfolio Capital Value ($)")
            st.plotly_chart(fig_equity, use_container_width=True)

            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(x=df.index, y=df['BH_DD']*100, name='Buy & Hold Market Drawdown', fill='tozeroy', line=dict(width=0), fillcolor='rgba(128,128,128,0.15)'))
            fig_dd.add_trace(go.Scatter(x=df.index, y=df['S1_Signal_DD']*100, name='S1 Drawdown', line=dict(color='#00d1ff', width=1.5)))
            fig_dd.add_trace(go.Scatter(x=df.index, y=df['S2_Signal_DD']*100, name='S2 Drawdown', line=dict(color='#ffaa00', width=1.5)))
            fig_dd.add_trace(go.Scatter(x=df.index, y=df['S3_Signal_DD']*100, name='S3 Drawdown', line=dict(color='#cc00ff', width=1.5)))
            fig_dd.update_layout(height=350, template='plotly_dark', margin=dict(l=20,r=20,t=10,b=20), yaxis_title="Percent Drop from Peak (%)")
            st.plotly_chart(fig_dd, use_container_width=True)

        except Exception as e:
            st.error(f"UI Interface Error: {e}")

