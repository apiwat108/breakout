import sqlite3
import config, requests
import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from helpers import calculate_quantity
import pytz
from timezone import is_dst
import yfinance as yf
import psycopg2
import psycopg2.extras

# connection = sqlite3.connect(config.DB_FILE)
# connection.row_factory = sqlite3.Row
# cursor = connection.cursor()

connection = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME, user=config.DB_USER, password=config.DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor) # tuple --> dictionary

cursor.execute("""
    select id from strategy where name = 'breakout'
""")

strategy_id = cursor.fetchone()['id']

cursor.execute("""
    select symbol, name
    from stock
    join stock_strategy on stock_strategy.stock_id = stock.id
    where stock_strategy.strategy_id = %s
""", (strategy_id,))

stocks = cursor.fetchall()
symbols = [stock['symbol'] for stock in stocks]

current_date = datetime.now(pytz.timezone('US/Eastern')).date().isoformat()
# current_date = '2023-09-12'

start_minute_bar = f"{current_date} 09:30:00-04:00"
end_minute_bar = f"{current_date} 15:25-04:00"

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

orders = api.list_orders(status='all', after=current_date)
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']

for symbol in symbols:

    # # Alpaca Version
    # minute_bars = api.get_bars(symbol, TimeFrame.Minute, start=current_date, end=current_date).df
    # minute_5_bars = api.get_bars(symbol, TimeFrame(5, TimeFrameUnit.Minute), start=current_date, end=current_date).df

    # Yahoo Version
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

    short_period = 12
    long_period = 26
    signal_period = 9
    
    if len(minute_60_bars) >= 30 and len(minute_15_bars) >= 30:
        (macd_all_60m, macd_signal_all_60m, macd_histogram_all_60m) = tulipy.macd(numpy.array(closes_60m), short_period=short_period , long_period=long_period, signal_period=signal_period)
        macd_60m = macd_all_60m[-1]
        macd_signal_60m = macd_signal_all_60m[-1]
        macd_histogram_60m = macd_histogram_all_60m[-1]
        (macd_all_15m, macd_signal_all_15m, macd_histogram_all_15m) = tulipy.macd(numpy.array(closes_15m), short_period=short_period , long_period=long_period, signal_period=signal_period)
        macd_15m = macd_all_15m[-1]
        macd_signal_15m = macd_signal_all_15m[-1]
        macd_histogram_15m = macd_histogram_all_15m[-1]

        if macd_60m > macd_signal_60m and macd_15m > 0:
            (macd_all_5m, macd_signal_all_5m, macd_histogram_all_5m) = tulipy.macd(numpy.array(closes_5m), short_period=short_period , long_period=long_period, signal_period=signal_period)
            current_macd_5m = macd_all_5m[-1]
            current_macd_signal_5m = macd_signal_all_5m[-1]
            current_macd_histogram_5m = macd_histogram_all_5m[-1]
            previous_macd_5m = macd_all_5m[-2]
            previous_macd_signal_5m = macd_signal_all_5m[-2]
            previous_macd_histogram_5m = macd_histogram_all_5m[-2]

            if (current_macd_histogram_5m > 0 and previous_macd_histogram_5m < 0 and current_macd_5m > 0) or (current_macd_5m > 0 and previous_macd_5m < 0 and current_macd_5m > current_macd_signal_5m):
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


    # market_open_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
    # market_open_bars = minute_bars.loc[market_open_mask]

    # if len(market_open_bars) >= 20:
    #     closes = market_open_bars.close.values
    #     lower, middle, upper = tulipy.bbands(closes, 20, 2)

    #     current_candle = market_open_bars.iloc[-1]
    #     previous_candle_raw = market_open_bars.iloc[-2]
    #     previous_candle = round(previous_candle_raw, 2)
    #     previous_candle_low = previous_candle.low

    #     if current_candle.close > lower[-1] and previous_candle.close < lower[-2]:
    #         print(f"{symbol} closed above lower bollinger band")
    #         print(current_candle)

    #         if symbol not in existing_order_symbols:
    #             limit_price_raw = current_candle.close
    #             limit_price = round(limit_price_raw, 2)

    #             candle_range_raw = current_candle.high - current_candle.low
    #             candle_range = round(candle_range_raw, 2)

    #             print(f"placing order for {symbol} at {limit_price}")

    #             try:
    #                 api.submit_order(
    #                     symbol=symbol,
    #                     side='buy',
    #                     type='limit',
    #                     qty=calculate_quantity(limit_price),
    #                     time_in_force='day',
    #                     order_class='bracket',
    #                     limit_price=limit_price,
    #                     take_profit=dict(
    #                         limit_price=limit_price + (candle_range),
    #                     ),
    #                     stop_loss=dict(
    #                         stop_price=previous_candle_low,
    #                     )
    #                 )
    #             except Exception as e:
    #                 print(f"could not submit order {e}")            
    #         else:
    #             print(f"Already an order for {symbol}, skipping")
