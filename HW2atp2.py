#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().system('pip install alpaca-py pandas data-science-types')


# In[2]:


import datetime
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import pandas as pd

# ==========================================
# 1. CONFIGURATION & AUTHENTICATION
# ==========================================
# Replace these with your actual Alpaca keys from your dashboard
ALPACA_API_KEY = "PKA53G7YAP6BKRPI2GIXTG36HM"
ALPACA_SECRET_KEY = "12uWk6tKDDT1CP6quUxmU1GtVe41xwixMXif59PtVjkR"

# Initialize the historical data client
client = StockHistoricalDataClient(
    api_key=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY
)

# ==========================================
# 2. USER INPUT & 15-MINUTE OFFSET
# ==========================================
ticker_selection = "AAPL"

# FIX: Set the end time to 20 minutes ago to satisfy the 15-minute free-tier delay rule
end_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
    minutes=20
)
start_date = end_date - datetime.timedelta(days=5 * 365)

print(
    f"Fetching 5 years of SIP data for {ticker_selection}..."
)
print(f"Start Date: {start_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
print(f"End Date:   {end_date.strftime('%Y-%m-%d %H:%M:%S')} UTC (Delayed to prevent 403)")

# ==========================================
# 3. FETCH DATA VIA ALPACA API
# ==========================================
request_params = StockBarsRequest(
    symbol_or_symbols=ticker_selection,
    timeframe=TimeFrame.Day,
    start=start_date,
    end=end_date,
)

try:
    bars = client.get_stock_bars(request_params)

    # ==========================================
    # 4. STORE IN PANDAS DATAFRAME
    # ==========================================
    # Convert the raw data into a structured Pandas DataFrame
    df = bars.df

    # Drop the multi-index symbol level to cleanly index by Timestamp
    df = df.reset_index(level=0, drop=True)

    print("\nData successfully stored in Pandas DataFrame!")
    display(df.tail())  # Displays the last 5 rows in Jupyter

except Exception as e:
    print(f"\nAn error occurred: {e}")
    print(
        "If you still hit a 403, try increasing the offset minutes from 20 to 30."
    )


# In[25]:


get_ipython().run_cell_magic('writefile', 'app.py', 'import streamlit as st\nimport datetime\nimport numpy as np\nimport pandas as pd\nimport plotly.graph_objects as go\nfrom alpaca.data.historical import StockHistoricalDataClient\nfrom alpaca.data.requests import StockBarsRequest\nfrom alpaca.data.timeframe import TimeFrame\n\nst.set_page_config(page_title="Alpaca Trading Backtester", layout="wide")\nst.title("Technical Indicators & Strategy Backtesting with Alpaca")\n\n# Configuration & Authentication\nALPACA_API_KEY = "PKA53G7YAP6BKRPI2GIXTG36HM"\nALPACA_SECRET_KEY = "12uWk6tKDDT1CP6quUxmU1GtVe41xwixMXif59PtVjkR"\n\nticker_selection = st.sidebar.selectbox(\n    "Select a Ticker Symbol",\n    ["AAPL", "MSFT", "SPY", "JPM", "BA", "ZM", "KO", "XOM"]\n)\n\ndef run_backtest_engine(data, signal_column, initial_capital=100000.0):\n    df_engine = data.copy()\n    cash = initial_capital\n    shares_held = 0.0\n    portfolio_values = []\n    trades = []\n    active_trade = None \n\n    for i in range(len(df_engine)):\n        current_price = df_engine[\'close\'].iloc[i]\n        current_date = df_engine.index[i]\n        signal = df_engine[signal_column].iloc[i]\n\n        if signal == 1 and shares_held == 0:\n            shares_held = cash / current_price\n            cash = 0.0\n            active_trade = {"Entry Date": current_date, "Entry Price": current_price}\n        elif signal == 0 and shares_held > 0:\n            cash = shares_held * current_price\n            shares_held = 0.0\n            active_trade["Exit Date"] = current_date\n            active_trade["Exit Price"] = current_price\n            active_trade["Raw_ROI"] = (current_price - active_trade[\'Entry Price\']) / active_trade[\'Entry Price\']\n            trades.append(active_trade)\n            active_trade = None\n\n        current_portfolio_value = cash + (shares_held * current_price)\n        portfolio_values.append(current_portfolio_value)\n\n    df_engine[f\'{signal_column}_PV\'] = portfolio_values\n    df_engine[f\'{signal_column}_DailyReturn\'] = df_engine[f\'{signal_column}_PV\'].pct_change().fillna(0)\n    peak = df_engine[f\'{signal_column}_PV\'].cummax()\n    df_engine[f\'{signal_column}_DD\'] = (df_engine[f\'{signal_column}_PV\'] - peak) / peak\n    return df_engine, pd.DataFrame(trades)\n\ndef calculate_performance_metrics(df_vector, portfolio_col, daily_return_col, trades_df, trading_days=252):\n    portfolio_series = df_vector[portfolio_col]\n    daily_returns = df_vector[daily_return_col]\n    total_return = (portfolio_series.iloc[-1] - portfolio_series.iloc[0]) / portfolio_series.iloc[0]\n    years = len(df_vector) / trading_days\n    cagr = (portfolio_series.iloc[-1] / portfolio_series.iloc[0]) ** (1 / years) - 1 if portfolio_series.iloc[-1] > 0 else 0\n    vol = daily_returns.std() * np.sqrt(trading_days)\n    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(trading_days) if daily_returns.std() != 0 else 0\n\n    downside_diffs = daily_returns.copy()\n    downside_diffs[downside_diffs > 0] = 0\n    downside_deviation = np.sqrt(np.mean(downside_diffs ** 2)) * np.sqrt(trading_days)\n    sortino = (daily_returns.mean() * trading_days) / downside_deviation if downside_deviation != 0 else 0\n\n    max_dd = df_vector[portfolio_col.replace(\'_PV\', \'_DD\')].min()\n    win_rate = (trades_df[\'Raw_ROI\'] > 0).sum() / len(trades_df) if not trades_df.empty else 0\n\n    return {\n        "Total Return": f"{total_return * 100:.2f}%",\n        "CAGR": f"{cagr * 100:.2f}%",\n        "Volatility": f"{vol * 100:.2f}%",\n        "Sharpe Ratio": f"{sharpe:.2f}",\n        "Sortino Ratio": f"{sortino:.2f}",\n        "Max Drawdown": f"{max_dd * 100:.2f}%",\n        "Win Rate": f"{win_rate * 100:.2f}%"\n    }\n\nif st.sidebar.button("Run Comprehensive Backtest", type="primary"):\n    with st.spinner(f"Computing historical layers for {ticker_selection}..."):\n        try:\n            client = StockHistoricalDataClient(api_key=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY)\n            end_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=20)\n            start_date = end_date - datetime.timedelta(days=5 * 365)\n\n            bars = client.get_stock_bars(StockBarsRequest(symbol_or_symbols=ticker_selection, timeframe=TimeFrame.Day, start=start_date, end=end_date))\n            df = bars.df.reset_index(level=0, drop=True)\n\n            df[\'EMA_20\'] = df[\'close\'].ewm(span=20, adjust=False).mean()\n            df[\'SMA_14\'] = df[\'close\'].rolling(14).mean()\n            df[\'BB_Upper\'] = df[\'EMA_20\'] + (2 * df[\'close\'].rolling(20).std())\n            df[\'BB_Lower\'] = df[\'EMA_20\'] - (2 * df[\'close\'].rolling(20).std())\n\n            # STRATEGY 2 ENHANCEMENT: Calculate the dynamic halfway line between Lower Bollinger Band and SMA 14\n            df[\'S2_Halfway_Line\'] = (df[\'BB_Lower\'] + df[\'SMA_14\']) / 2\n\n            ema12 = df[\'close\'].ewm(span=12).mean()\n            ema26 = df[\'close\'].ewm(span=26).mean()\n            df[\'MACD\'] = ema12 - ema26\n            df[\'MACD_S\'] = df[\'MACD\'].ewm(span=9).mean()\n\n            tr = pd.concat([df[\'high\']-df[\'low\'], abs(df[\'high\']-df[\'close\'].shift()), abs(df[\'low\']-df[\'close\'].shift())], axis=1).max(axis=1)\n            df[\'ATR\'] = tr.rolling(14).mean()\n            df[\'ATR_SMA\'] = df[\'ATR\'].rolling(20).mean()\n\n            delta = df[\'close\'].diff()\n            gain = (delta.where(delta > 0, 0)).rolling(14).mean()\n            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()\n            df[\'RSI\'] = 100 - (100 / (1 + (gain / loss)))\n            df[\'Williams_R\'] = -100 * ((df[\'high\'].rolling(14).max() - df[\'close\']) / (df[\'high\'].rolling(14).max() - df[\'low\'].rolling(14).min()))\n            df[\'ADX\'] = 100 * (abs(df[\'high\'].diff().clip(lower=0).rolling(14).mean() - df[\'low\'].diff().clip(upper=0).abs().rolling(14).mean()) / df[\'ATR\']).rolling(14).mean()\n\n            s1_signals, s2_signals, s3_signals = [], [], []\n            s1_active, s2_active, s3_active = False, False, False\n\n            for idx in range(len(df)):\n                if idx < 20 or pd.isna(df[\'ADX\'].iloc[idx]) or pd.isna(df[\'RSI\'].iloc[idx]) or pd.isna(df[\'S2_Halfway_Line\'].iloc[idx]):\n                    s1_signals.append(0)\n                    s2_signals.append(0)\n                    s3_signals.append(0)\n                    continue\n\n                close_curr, close_prev = df[\'close\'].iloc[idx], df[\'close\'].iloc[idx-1]\n                adx_curr, rsi_curr = df[\'ADX\'].iloc[idx], df[\'RSI\'].iloc[idx]\n                ema20_curr = df[\'EMA_20\'].iloc[idx]\n                bbu_curr = df[\'BB_Upper\'].iloc[idx]\n                sma14_curr, sma14_prev = df[\'SMA_14\'].iloc[idx], df[\'SMA_14\'].iloc[idx-1]\n                halfway_curr, halfway_prev = df[\'S2_Halfway_Line\'].iloc[idx], df[\'S2_Halfway_Line\'].iloc[idx-1]\n                atr_curr, atr_sma_curr = df[\'ATR\'].iloc[idx], df[\'ATR_SMA\'].iloc[idx]\n                will_r_curr = df[\'Williams_R\'].iloc[idx]\n\n                # --- Strategy 1 ---\n                s1_buy_cond = (adx_curr > 25) and (close_curr > ema20_curr)\n                s1_sell_cond = (close_curr < ema20_curr)\n                if not s1_active and s1_buy_cond: s1_active = True\n                elif s1_active and s1_sell_cond: s1_active = False\n                s1_signals.append(1 if s1_active else 0)\n\n                # --- Strategy 2 (UPDATED ENTRY LOGIC) ---\n                # Check for crossing above the dynamic Halfway Line rather than SMA 14\n                cross_halfway_up = (close_prev <= halfway_prev) and (close_curr > halfway_curr)\n                cross_sma_down = (close_prev >= sma14_prev) and (close_curr < sma14_curr)\n\n                s2_buy_cond = (rsi_curr < 50) and cross_halfway_up\n                s2_sell_cond = (rsi_curr > 70) or (close_curr > bbu_curr) or cross_sma_down\n\n                if not s2_active and s2_buy_cond: s2_active = True\n                elif s2_active and s2_sell_cond: s2_active = False\n                s2_signals.append(1 if s2_active else 0)\n\n                # --- Strategy 3 ---\n                s3_buy_cond = (atr_curr < atr_sma_curr) and (will_r_curr > -50)\n                s3_sell_cond = (will_r_curr < -50) or (close_curr < ema20_curr)\n                if not s3_active and s3_buy_cond: s3_active = True\n                elif s3_active and s3_sell_cond: s3_active = False\n                s3_signals.append(1 if s3_active else 0)\n\n            df[\'S1_Signal\'] = s1_signals\n            df[\'S2_Signal\'] = s2_signals\n            df[\'S3_Signal\'] = s3_signals\n\n            df, s1_t = run_backtest_engine(df, \'S1_Signal\')\n            df, s2_t = run_backtest_engine(df, \'S2_Signal\')\n            df, s3_t = run_backtest_engine(df, \'S3_Signal\')\n\n            df[\'BH_PV\'] = (1 + df[\'close\'].pct_change().fillna(0)).cumprod() * 100000.0\n            df[\'BH_DailyReturn\'] = df[\'BH_PV\'].pct_change().fillna(0)\n            df[\'BH_DD\'] = (df[\'BH_PV\'] - df[\'BH_PV\'].cummax()) / df[\'BH_PV\'].cummax()\n\n            st.success("Analysis Complete!")\n            st.subheader("Performance metrics")\n\n            m_bh = calculate_performance_metrics(df, \'BH_PV\', \'BH_DailyReturn\', pd.DataFrame())\n            m_s1 = calculate_performance_metrics(df, \'S1_Signal_PV\', \'S1_Signal_DailyReturn\', s1_t)\n            m_s2 = calculate_performance_metrics(df, \'S2_Signal_PV\', \'S2_Signal_DailyReturn\', s2_t)\n            m_s3 = calculate_performance_metrics(df, \'S3_Signal_PV\', \'S3_Signal_DailyReturn\', s3_t)\n\n            matrix_summary = {\n                "Analytics Metric": ["Total Return", "CAGR", "Volatility", "Sharpe Ratio", "Sortino Ratio", "Max Drawdown", "Win Rate"],\n                "Buy & Hold (Baseline)": [m_bh["Total Return"], m_bh["CAGR"], m_bh["Volatility"], m_bh["Sharpe Ratio"], m_bh["Sortino Ratio"], m_bh["Max Drawdown"], m_bh["Win Rate"]],\n                "Strategy 1 (Trend Following - EMA20)": [m_s1["Total Return"], m_s1["CAGR"], m_s1["Volatility"], m_s1["Sharpe Ratio"], m_s1["Sortino Ratio"], m_s1["Max Drawdown"], m_s1["Win Rate"]],\n                "Strategy 2 (Enhanced Mean Reversion)": [m_s2["Total Return"], m_s2["CAGR"], m_s2["Volatility"], m_s2["Sharpe Ratio"], m_s2["Sortino Ratio"], m_s2["Max Drawdown"], m_s2["Win Rate"]],\n                "Strategy 3 (Volatility Breakout)": [m_s3["Total Return"], m_s3["CAGR"], m_s3["Volatility"], m_s3["Sharpe Ratio"], m_s3["Sortino Ratio"], m_s3["Max Drawdown"], m_s3["Win Rate"]]\n            }\n            st.table(pd.DataFrame(matrix_summary).set_index("Analytics Metric"))\n            st.markdown("---") \n\n            st.subheader("Charts")\n            fig_price = go.Figure()\n            fig_price.add_trace(go.Scatter(x=df.index, y=df[\'close\'], name=\'Close Price\', line=dict(color=\'#ffffff\', width=1.5)))\n            fig_price.add_trace(go.Scatter(x=df.index, y=df[\'EMA_20\'], name=\'EMA 20 Center\', line=dict(color=\'rgba(255,255,255,0.2)\', dash=\'dash\')))\n            fig_price.add_trace(go.Scatter(x=df.index, y=df[\'SMA_14\'], name=\'SMA 14\', line=dict(color=\'rgba(0,255,100,0.3)\', dash=\'dot\')))\n\n            # Draw the custom Strategy 2 entry threshold line onto the visual chart\n            fig_price.add_trace(go.Scatter(x=df.index, y=df[\'S2_Halfway_Line\'], name=\'S2 Entry Threshold (Halfway)\', line=dict(color=\'#ffaa00\', width=1, dash=\'dashdot\')))\n\n            fig_price.add_trace(go.Scatter(x=df.index, y=df[\'BB_Upper\'], name=\'BB Upper Band\', line=dict(color=\'rgba(0,209,255,0.2)\')))\n            fig_price.add_trace(go.Scatter(x=df.index, y=df[\'BB_Lower\'], name=\'BB Lower Band\', line=dict(color=\'rgba(0,209,255,0.2)\'), fill=\'tonexty\'))\n\n            s2_buys = df[df[\'S2_Signal\'].diff() == 1]\n            s2_sells = df[df[\'S2_Signal\'].diff() == -1]\n            fig_price.add_trace(go.Scatter(x=s2_buys.index, y=s2_buys[\'close\'], mode=\'markers\', name=\'S2 Early Entry\', marker=dict(symbol=\'triangle-up\', size=11, color=\'#ffaa00\')))\n            fig_price.add_trace(go.Scatter(x=s2_sells.index, y=s2_sells[\'close\'], mode=\'markers\', name=\'S2 Exit\', marker=dict(symbol=\'triangle-down\', size=11, color=\'#ff5500\')))\n\n            fig_price.update_layout(height=450, template=\'plotly_dark\', margin=dict(l=20,r=20,t=10,b=20), hovermode=\'x unified\')\n            st.plotly_chart(fig_price, use_container_width=True)\n\n            fig_equity = go.Figure()\n            fig_equity.add_trace(go.Scatter(x=df.index, y=df[\'BH_PV\'], name=\'Buy & Hold Baseline\', line=dict(color=\'gray\', width=1.5)))\n            fig_equity.add_trace(go.Scatter(x=df.index, y=df[\'S1_Signal_PV\'], name=\'Strategy 1: High ADX + Close>EMA20\', line=dict(color=\'#00d1ff\', width=2.5)))\n            fig_equity.add_trace(go.Scatter(x=df.index, y=df[\'S2_Signal_PV\'], name=\'Strategy 2: Enhanced Mean Reversion\', line=dict(color=\'#ffaa00\', width=2.5)))\n            fig_equity.add_trace(go.Scatter(x=df.index, y=df[\'S3_Signal_PV\'], name=\'Strategy 3: Volatility Breakout\', line=dict(color=\'#cc00ff\', width=2.5)))\n            fig_equity.update_layout(height=450, template=\'plotly_dark\', margin=dict(l=20,r=20,t=10,b=20), yaxis_title="Portfolio Capital Value ($)")\n            st.plotly_chart(fig_equity, use_container_width=True)\n\n            fig_dd = go.Figure()\n            fig_dd.add_trace(go.Scatter(x=df.index, y=df[\'BH_DD\']*100, name=\'Buy & Hold Market Drawdown\', fill=\'tozeroy\', line=dict(width=0), fillcolor=\'rgba(128,128,128,0.15)\'))\n            fig_dd.add_trace(go.Scatter(x=df.index, y=df[\'S1_Signal_DD\']*100, name=\'S1 Drawdown\', line=dict(color=\'#00d1ff\', width=1.5)))\n            fig_dd.add_trace(go.Scatter(x=df.index, y=df[\'S2_Signal_DD\']*100, name=\'S2 Drawdown\', line=dict(color=\'#ffaa00\', width=1.5)))\n            fig_dd.add_trace(go.Scatter(x=df.index, y=df[\'S3_Signal_DD\']*100, name=\'S3 Drawdown\', line=dict(color=\'#cc00ff\', width=1.5)))\n            fig_dd.update_layout(height=350, template=\'plotly_dark\', margin=dict(l=20,r=20,t=10,b=20), yaxis_title="Percent Drop from Peak (%)")\n            st.plotly_chart(fig_dd, use_container_width=True)\n\n        except Exception as e:\n            st.error(f"UI Interface Error: {e}")\n')


# In[ ]:


# Cell 2: Run this to launch your interactive dashboard
get_ipython().system('streamlit run app.py')

