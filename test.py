import matplotlib.pyplot as plt
import pandas as pd
from fbprophet import Prophet
import yfinance as yf


data = yf.download('AAPL',start = '2020-01-01')

data = data.rename(columns={'Close':'y'})
data['ds'] = data.index 
data = data[['ds', 'y']]

m = Prophet(daily_seasonality = True)
m.fit(data)

future = m.make_future_dataframe(periods=100)
prediction = m.predict(future)
m.plot(prediction)

print(prediction)