#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd

def compute_indicators_and_signals(df):
    df = df.copy()

    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['SMA_14'] = df['close'].rolling(14).mean()
    df['BB_Upper'] = df['EMA_20'] + (2 * df['close'].rolling(20).std())
    df['BB_Lower'] = df['EMA_20'] - (2 * df['close'].rolling(20).std())

    # STRATEGY 2 ENHANCEMENT
    df['S2_Halfway_Line'] = (df['BB_Lower'] + df['SMA_14']) / 2

    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_S'] = df['MACD'].ewm(span=9).mean()

    tr = pd.concat([df['high']-df['low'], abs(df['high']-df['close'].shift()), abs(df['low']-df['close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['ATR_SMA'] = df['ATR'].rolling(20).mean()

    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    df['Williams_R'] = -100 * ((df['high'].rolling(14).max() - df['close']) / (df['high'].rolling(14).max() - df['low'].rolling(14).min()))
    df['ADX'] = 100 * (abs(df['high'].diff().clip(lower=0).rolling(14).mean() - df['low'].diff().clip(upper=0).abs().rolling(14).mean()) / df['ATR']).rolling(14).mean()

    s1_signals, s2_signals, s3_signals = [], [], []
    s1_active, s2_active, s3_active = False, False, False

    for idx in range(len(df)):
        if idx < 20 or pd.isna(df['ADX'].iloc[idx]) or pd.isna(df['RSI'].iloc[idx]) or pd.isna(df['S2_Halfway_Line'].iloc[idx]):
            s1_signals.append(0)
            s2_signals.append(0)
            s3_signals.append(0)
            continue

        close_curr, close_prev = df['close'].iloc[idx], df['close'].iloc[idx-1]
        adx_curr, rsi_curr = df['ADX'].iloc[idx], df['RSI'].iloc[idx]
        ema20_curr = df['EMA_20'].iloc[idx]
        bbu_curr = df['BB_Upper'].iloc[idx]
        sma14_curr, sma14_prev = df['SMA_14'].iloc[idx], df['SMA_14'].iloc[idx-1]
        halfway_curr, halfway_prev = df['S2_Halfway_Line'].iloc[idx], df['S2_Halfway_Line'].iloc[idx-1]
        atr_curr, atr_sma_curr = df['ATR'].iloc[idx], df['ATR_SMA'].iloc[idx]
        will_r_curr = df['Williams_R'].iloc[idx]

        # --- Strategy 1 ---
        s1_buy_cond = (adx_curr > 25) and (close_curr > ema20_curr)
        s1_sell_cond = (close_curr < ema20_curr)
        if not s1_active and s1_buy_cond: s1_active = True
        elif s1_active and s1_sell_cond: s1_active = False
        s1_signals.append(1 if s1_active else 0)

        # --- Strategy 2 (UPDATED ENTRY LOGIC) ---
        cross_halfway_up = (close_prev <= halfway_prev) and (close_curr > halfway_curr)
        cross_sma_down = (close_prev >= sma14_prev) and (close_curr < sma14_curr)

        s2_buy_cond = (rsi_curr < 50) and cross_halfway_up
        s2_sell_cond = (rsi_curr > 70) or (close_curr > bbu_curr) or cross_sma_down

        if not s2_active and s2_buy_cond: s2_active = True
        elif s2_active and s2_sell_cond: s2_active = False
        s2_signals.append(1 if s2_active else 0)

        # --- Strategy 3 ---
        s3_buy_cond = (atr_curr < atr_sma_curr) and (will_r_curr > -50)
        s3_sell_cond = (will_r_curr < -50) or (close_curr < ema20_curr)
        if not s3_active and s3_buy_cond: s3_active = True
        elif s3_active and s3_sell_cond: s3_active = False
        s3_signals.append(1 if s3_active else 0)

    df['S1_Signal'] = s1_signals
    df['S2_Signal'] = s2_signals
    df['S3_Signal'] = s3_signals

    return df

