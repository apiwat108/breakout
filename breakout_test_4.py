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
        minute_5_bars = ticker.history(interval='5m',period='2d')#start=current_date, end=current_date)
        minute_15_bars = ticker.history(interval='15m',period='2d')
        minute_60_bars = ticker.history(interval='60m',period='5d')
    except Exception as e:
        print(e)

    closes_5m = numpy.array(minute_5_bars['Close'])
    closes_15m = numpy.array(minute_15_bars['Close'])
    closes_60m = numpy.array(minute_60_bars['Close'])

    short_period = 12
    long_period = 26
    signal_period = 9
    decimal_point = 4

    (macd_all_60m, macd_signal_all_60m, macd_histogram_all_60m) = tulipy.macd(numpy.array(closes_60m), short_period=short_period , long_period=long_period, signal_period=signal_period)
    macd_60m = round(macd_all_60m[-1], decimal_point)
    macd_signal_60m = round(macd_signal_all_60m[-1], decimal_point)
    macd_histogram_60m = round(macd_histogram_all_60m[-1], decimal_point)
    (macd_all_15m, macd_signal_all_15m, macd_histogram_all_15m) = tulipy.macd(numpy.array(closes_15m), short_period=short_period , long_period=long_period, signal_period=signal_period)
    macd_15m = round(macd_all_15m[-1], decimal_point)
    macd_signal_15m = round(macd_signal_all_15m[-1], decimal_point)
    macd_histogram_15m = round(macd_histogram_all_15m[-1], decimal_point)

    if macd_60m > macd_signal_60m and macd_15m > 0:
        (macd_all_5m, macd_signal_all_5m, macd_histogram_all_5m) = tulipy.macd(numpy.array(closes_5m), short_period=short_period , long_period=long_period, signal_period=signal_period)
        current_macd_5m = round(macd_all_5m[-1], decimal_point)
        current_macd_signal_5m = round(macd_signal_all_5m[-1], decimal_point)
        current_macd_histogram_5m = round(macd_histogram_all_5m[-1], decimal_point)
        previous_macd_5m = round(macd_all_5m[-2], decimal_point)
        previous_macd_signal_5m = round(macd_signal_all_5m[-2], decimal_point)
        previous_macd_histogram_5m = round(macd_histogram_all_5m[-2], decimal_point)
    
        print(f"{symbol} is passed 60m and 15m condition")
        print(f"    - Current_macd_histogram_5m at {current_macd_histogram_5m}.")
        print(f"    - Previous_macd_histogram_5m at {previous_macd_histogram_5m}.")

        if (current_macd_histogram_5m > 0 and previous_macd_histogram_5m < 0 and current_macd_5m > 0):
            print(f"{symbol} 5m-macd cross up signal line and 0-line. It's buy signal and the order can be placed.")

            if symbol not in existing_order_symbols:
                market_price = round(closes_5m[-1], 1)

                print(f"placing order for {symbol} at {market_price}")

                try:
                    api.submit_order(
                        symbol=symbol,
                        side='buy',
                        type='market',
                        qty=calculate_quantity(market_price),
                        time_in_force='gtc'
                    )
                except Exception as e:
                    print(f"could not submit order {e}")            
            else:
                print(f"Already an order for {symbol}, skipping")

        elif current_macd_histogram_5m < 0 and previous_macd_histogram_5m > 0:
            print(f"{symbol} 5m-macd cross down signal line. It's sell signal and the order can be placed.")

            if symbol in existing_order_symbols:

                print(f"sell for {symbol} at the best bid")

                try:
                    api.submit_order(
                        symbol=symbol,
                        side='sell',
                        type='market',
                        qty=calculate_quantity(market_price),
                        time_in_force='gtc'
                    )
                except Exception as e:
                    print(f"could not submit order {e}")