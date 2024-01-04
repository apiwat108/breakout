import config, requests
# import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from helpers import calculate_quantity
import pytz
import yfinance as yf
import pandas_ta as ta
import pandas as pd

symbols = config.BREAKOUT_SYMBOLS

current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

positions = api.list_positions()
existing_position_symbols = [position.symbol for position in positions]
print(current_time)

for symbol in symbols:
    print(symbol)

    ticker = yf.Ticker(symbol)
    minute_5_bars = ticker.history(interval='5m',period='5d')#start=current_date, end=current_date)

    # adx = ta.adx(minute_5_bars['High'], minute_5_bars['Low'], minute_5_bars['Close'])
    adx = minute_5_bars.ta.adx()

    macd = minute_5_bars.ta.macd()

    rsi = minute_5_bars.ta.rsi()

    df = pd.concat([minute_5_bars, adx, macd, rsi], axis=1)

    # last_row = round(df.iloc[-1]['ADX_14'], 2)
    last_row = df.iloc[-1]
    market_price = round(df.iloc[-1]['Close'], 2)
    # print(last_row)

    if symbol not in existing_position_symbols:
        if last_row['ADX_14'] >= 25:
            if last_row['DMP_14'] > last_row['DMN_14']:
                message = f"STRONG UPTREND: The ADX is {last_row['ADX_14']:.2f}"
                print(message)
                quantity = calculate_quantity(market_price)
                print(f" - Placing buy order for {symbol} at {market_price}.\n")

                try:
                    api.submit_order(
                        symbol=symbol,
                        side='buy',
                        type='market',
                        qty=quantity,
                        time_in_force='gtc'
                    )
                except Exception as e:
                    print(f"Could not submit order {e}")    

            elif last_row['DMN_14'] > last_row['DMP_14']:            
                message = f"STRONG DOWNTREND: The ADX is {last_row['ADX_14']:.2f}"
                print(message)
                quantity = calculate_quantity(market_price)
                print(f" - Placing buy order for {symbol} at {market_price}.\n")

                try:
                    api.submit_order(
                        symbol=symbol,
                        side='sell',
                        type='market',
                        qty=quantity,
                        time_in_force='gtc'
                    )
                except Exception as e:
                    print(f"Could not submit order {e}")   

        elif last_row['ADX_14'] < 25:
            message = f"NO TREND: The ADX is {last_row['ADX_14']:.2f}"
            print(message)

    elif symbol in existing_position_symbols:
        print(f" - Already in the position")
        position = api.get_position(symbol)
        quantity = abs(float(position.qty))
        entry_price = float(position.avg_entry_price)
        market_value = abs(float(position.market_value))
        cost = abs(float(position.cost_basis))
        side = position.side

        if market_value > (1.01 * cost):
            print(f" - It's taking-profit signal.")
            print(f" - Placing order for {symbol} at {market_price}.\n")

            if side == "long": 
                try:
                    api.submit_order(
                        symbol=symbol,
                        side='sell',
                        type='market',
                        qty=quantity,
                        time_in_force='gtc'
                    )
                except Exception as e:
                    print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---\n")  

            elif side == "short": 
                try:
                    api.submit_order(
                        symbol=symbol,
                        side='buy',
                        type='market',
                        qty=quantity,
                        time_in_force='gtc'
                    )
                except Exception as e:
                    print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---\n") 

        elif market_value < (1.01 * cost):
            print(f" - It's cut-loss signal.")
            print(f" - Placing sell order for {symbol} at {market_price}.\n")

            if side == "long": 
                try:
                    api.submit_order(
                        symbol=symbol,
                        side='sell',
                        type='market',
                        qty=quantity,
                        time_in_force='gtc'
                    )
                except Exception as e:
                    print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---\n")   

            elif side == "short": 
                try:
                    api.submit_order(
                        symbol=symbol,
                        side='buy',
                        type='market',
                        qty=quantity,
                        time_in_force='gtc'
                    )
                except Exception as e:
                    print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---\n") 
