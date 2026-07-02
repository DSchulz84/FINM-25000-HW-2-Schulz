#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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

