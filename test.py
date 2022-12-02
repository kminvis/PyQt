import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

url = "https://api.upbit.com/v1/candles/minutes/1?market=KRW-BTC&count=50"
df = pd.read_json(url)

df = df.rename(columns={'candle_date_time_kst':'Date', 'opening_price':'Open', 'high_price':'High', 'low_price':'Low', 'trade_price':'Close', 'candle_acc_trade_volume': 'Volume'})
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S', errors='raise')
df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

print(df)