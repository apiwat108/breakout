import config, requests
import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from helpers import calculate_quantity
import pytz
import yfinance as yf

symbols = config.BREAKOUT_SYMBOLS

current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

orders = api.list_orders(status='all', after=current_date)
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']

for symbol in symbols:
    try:
        ticker = yf.Ticker(symbol)
        minute_5_bars = ticker.history(interval='5m',period='1d')#start=current_date, end=current_date)
        minute_15_bars = ticker.history(interval='15m',period='1d')
        minute_60_bars = ticker.history(interval='60m',period='5d')
    except Exception as e:
        print(e)

    closes_5m = numpy.array(minute_5_bars['Close'])
    closes_15m = numpy.array(minute_15_bars['Close'])
    closes_60m = numpy.array(minute_60_bars['Close'])

    print(closes_5m, closes_15m, closes_60m)