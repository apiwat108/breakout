import config, requests
import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from helpers import calculate_quantity
import pytz
from timezone import is_dst
import yfinance as yf

symbols = config.BREAKOUT_SYMBOLS

current_date = datetime.now(pytz.timezone('US/Eastern')).date().isoformat()
print(current_date)