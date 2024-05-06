import config, requests
import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from helpers import calculate_quantity
import pytz
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import alpaca_trade_api as tradeapi

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
clock = api.get_clock()

if clock.is_open:

    symbols_DX0 = config.BREAKOUT_SYMBOLS_DX0
    symbols_DR1 = config.BREAKOUT_SYMBOLS_DR1
    symbols_DX1 = config.BREAKOUT_SYMBOLS_DX1

    current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
    current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")

    orders = api.list_orders(status='all', after=current_date)
    existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']
    positions = api.list_positions()
    existing_position_symbols = [position.symbol for position in positions]
    print(f'{current_time}\n')

    # Breakout Strategy Model-DX0
    for symbol in symbols_DX0:
        print(f'{symbol}_{current_time}\n')

        ticker = yf.Ticker(symbol)

        minute_5_bars = ticker.history(interval='5m',period='5d')
        minute_15_bars = ticker.history(interval='15m',period='5d')
        minute_60_bars = ticker.history(interval='60m',period='1mo')
        day_1_bars = ticker.history(interval='1d',period='6mo')

        ## When running on Linux, activate this part before indicator setting section 

        most_updated_5m_close = minute_5_bars['Close'][-1]
        minute_5_bars.loc[minute_5_bars.index[-2],'Close'] = most_updated_5m_close
        minute_5_bars.drop(index=minute_5_bars.index[-1],axis=0,inplace=True)

        # References
        # https://predictivehacks.com/?all-tips=replace-values-based-on-index-in-pandas-dataframes
        # https://stackoverflow.com/questions/66096734/pandas-df-loc-1-col-sometimes-work-and-sometimes-add-extra-row-with-nan

        most_updated_15m_close = minute_15_bars['Close'][-1]
        minute_15_bars.loc[minute_15_bars.index[-2],'Close'] = most_updated_15m_close
        minute_15_bars.drop(index=minute_15_bars.index[-1],axis=0,inplace=True)

        most_updated_60m_close = minute_60_bars['Close'][-1]
        minute_60_bars.loc[minute_60_bars.index[-2],'Close'] = most_updated_60m_close
        minute_60_bars.drop(index=minute_60_bars.index[-1],axis=0,inplace=True)

        # most_updated_1d_close = day_1_bars['Close'][-1]
        # day_1_bars.loc[day_1_bars.index[-2],'Close'] = most_updated_1d_close
        # day_1_bars.drop(index=day_1_bars.index[-1],axis=0,inplace=True)

        # Indicator Setting
        macd_5 = minute_5_bars.ta.macd()
        macd_15 = minute_15_bars.ta.macd()
        macd_60 = minute_60_bars.ta.macd()
        macd_1 = day_1_bars.ta.macd()

        rsi_5 = minute_5_bars.ta.rsi()
        rsi_15 = minute_15_bars.ta.rsi()
        rsi_60 = minute_60_bars.ta.rsi()

        # df = pd.concat([minute_5_bars['Close'], minute_5_bars['Open'], macd_5_bars['MACD_12_26_9'], rsi], axis=1)
        # print(df)

        decimal_point = 4
        decimal_point_rsi = 2

        # Candle Stick
        C_60m_C0 = round(minute_60_bars['Close'][-1], decimal_point)
        # O_60m_C0 = round(minute_60_bars['Open'][-1], decimal_point)
        C_60m_P1 = round(minute_60_bars['Close'][-2], decimal_point)
        # O_60m_P1 = round(minute_60_bars['Open'][-2], decimal_point)
        C_60m_P2 = round(minute_60_bars['Close'][-3], decimal_point)

        C_1d_C0 = round(day_1_bars['Close'][-1], decimal_point)
        C_1d_P1 = round(day_1_bars['Close'][-2], decimal_point)
        C_1d_P2 = round(day_1_bars['Close'][-3], decimal_point)

        M_1d_C0 = round(macd_1['MACD_12_26_9'][-1], decimal_point)
        M_1d_P1 = round(macd_1['MACD_12_26_9'][-2], decimal_point)
        H_1d_C0 = round(macd_1['MACDh_12_26_9'][-1], decimal_point)
        H_1d_P1 = round(macd_1['MACDh_12_26_9'][-2], decimal_point)

        M_60m_C0 = round(macd_60['MACD_12_26_9'][-1], decimal_point)
        M_60m_P1 = round(macd_60['MACD_12_26_9'][-2], decimal_point)
        H_60m_C0 = round(macd_60['MACDh_12_26_9'][-1], decimal_point)
        H_60m_P1 = round(macd_60['MACDh_12_26_9'][-2], decimal_point)
        H_60m_P2 = round(macd_60['MACDh_12_26_9'][-3], decimal_point)
        S_60m_C0 = round(macd_60['MACDs_12_26_9'][-1], decimal_point)
        S_60m_P1 = round(macd_60['MACDs_12_26_9'][-2], decimal_point)
        S_60m_P2 = round(macd_60['MACDs_12_26_9'][-3], decimal_point) 

        M_15m_C0 = round(macd_15['MACD_12_26_9'][-1], decimal_point)
        M_15m_P1 = round(macd_15['MACD_12_26_9'][-2], decimal_point)
        H_15m_C0 = round(macd_15['MACDh_12_26_9'][-1], decimal_point)
        H_15m_P1 = round(macd_15['MACDh_12_26_9'][-2], decimal_point)

        M_5m_C0 = round(macd_5['MACD_12_26_9'][-1], decimal_point)
        M_5m_P1 = round(macd_5['MACD_12_26_9'][-2], decimal_point)
        H_5m_C0 = round(macd_5['MACDh_12_26_9'][-1], decimal_point)
        H_5m_P1 = round(macd_5['MACDh_12_26_9'][-2], decimal_point)

        RSI_5m_C0 = round(rsi_5[-1], decimal_point_rsi)
        RSI_15m_C0 = round(rsi_15[-1], decimal_point_rsi)
        RSI_60m_C0 = round(rsi_60[-1], decimal_point_rsi)
        RSI_min = 50.00
        RSI_max = 75.00

        Vol_5m_C0 = minute_5_bars['Volume'][-1]
        Vol_threshold = 1000

        market_price = round(minute_5_bars['Close'][-1], decimal_point)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:

                # Model_DX0: RSI too sharp on the cross up (POR at 3 May at 09:30 RSI = 67.73 and 2 May at 15:55 RSI = 20.09 --> SCF = 3.37 and Volume is very low)
                if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_15m_C0 > 0.0000 and M_60m_C0 > M_60m_P1 and S_60m_C0 > S_60m_P1 and H_60m_C0 > 0.0000:

                    # Check RSI and volume
                    if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                        print(f" - It's buy signal for Model DX0")         
                        quantity = calculate_quantity(market_price)
                        print(f" - Placing buy order for {symbol} at {market_price}.")

                        # Placing order
                        try:
                            api.submit_order(
                                symbol=symbol,
                                side='buy',
                                type='market',
                                qty=quantity,
                                time_in_force='gtc'
                            )
                        except Exception as e:
                            print(f" - Could not submit order {e}\n")  
                    else:
                        print(f" - RSI is overbought at RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for Models DX0\n")

                # Model_DX0_END
                else:
                    print(" - One of the conditions do not pass for Models DX0\n")
            
            else:
                print(f' - The order of stock {symbol} is placed\n')

        elif symbol in existing_position_symbols:
            try:
                print(f" - Already in the position")
                position = api.get_position(symbol)
                quantity = position.qty
                entry_price = float(position.avg_entry_price)
                market_value = abs(float(position.market_value))
                cost = abs(float(position.cost_basis))

                day_bars = ticker.history(interval='1d',period='1mo')
                EMA_10d_bars = day_bars['Close'].ewm(span=10, adjust=False).mean()
                EMA_10d = EMA_10d_bars[-1]

            except Exception as e:
                print(f"The order may not be filled")

            # Strategy 1 for taking profit at 1.0%
            if market_value > (1.01 * cost):
                print(f" - It's taking-profit signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

            # Strategy 2 for cutting loss at 7.5%
            elif market_price < EMA_10d and market_value < (0.925 * cost):
                print(f" - It's cut-loss signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

            # Strategy 3 for cutting loss should not greater than 7.5%
            elif market_value < (0.9250 * cost):
                print(f" - It's cut-loss signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

            else:
                print(" - No sell signal yet\n")

        else: 
            print(" - It's already been traded for today.\n")

    # Breakout Strategy Model-DR1
    for symbol in symbols_DR1:
        print(f'{symbol}_{current_time}\n')

        ticker = yf.Ticker(symbol)

        minute_5_bars = ticker.history(interval='5m',period='5d')
        minute_15_bars = ticker.history(interval='15m',period='5d')
        minute_60_bars = ticker.history(interval='60m',period='1mo')
        day_1_bars = ticker.history(interval='1d',period='6mo')

        ## When running on Linux, activate this part before indicator setting section 

        most_updated_5m_close = minute_5_bars['Close'][-1]
        minute_5_bars.loc[minute_5_bars.index[-2],'Close'] = most_updated_5m_close
        minute_5_bars.drop(index=minute_5_bars.index[-1],axis=0,inplace=True)

        # References
        # https://predictivehacks.com/?all-tips=replace-values-based-on-index-in-pandas-dataframes
        # https://stackoverflow.com/questions/66096734/pandas-df-loc-1-col-sometimes-work-and-sometimes-add-extra-row-with-nan

        most_updated_15m_close = minute_15_bars['Close'][-1]
        minute_15_bars.loc[minute_15_bars.index[-2],'Close'] = most_updated_15m_close
        minute_15_bars.drop(index=minute_15_bars.index[-1],axis=0,inplace=True)

        most_updated_60m_close = minute_60_bars['Close'][-1]
        minute_60_bars.loc[minute_60_bars.index[-2],'Close'] = most_updated_60m_close
        minute_60_bars.drop(index=minute_60_bars.index[-1],axis=0,inplace=True)

        # most_updated_1d_close = day_1_bars['Close'][-1]
        # day_1_bars.loc[day_1_bars.index[-2],'Close'] = most_updated_1d_close
        # day_1_bars.drop(index=day_1_bars.index[-1],axis=0,inplace=True)

        # Indicator Setting
        macd_5 = minute_5_bars.ta.macd()        
        macd_15 = minute_15_bars.ta.macd()
        macd_60 = minute_60_bars.ta.macd()
        macd_1 = day_1_bars.ta.macd()

        rsi_5 = minute_5_bars.ta.rsi()
        rsi_15 = minute_15_bars.ta.rsi()
        rsi_60 = minute_60_bars.ta.rsi()

        # df = pd.concat([minute_5_bars['Close'], minute_5_bars['Open'], macd_5_bars['MACD_12_26_9'], rsi], axis=1)
        # print(df)

        decimal_point = 4
        decimal_point_rsi = 2

        # Candle Stick
        C_60m_C0 = round(minute_60_bars['Close'][-1], decimal_point)
        # O_60m_C0 = round(minute_60_bars['Open'][-1], decimal_point)
        C_60m_P1 = round(minute_60_bars['Close'][-2], decimal_point)
        # O_60m_P1 = round(minute_60_bars['Open'][-2], decimal_point)
        C_60m_P2 = round(minute_60_bars['Close'][-3], decimal_point)

        C_1d_C0 = round(day_1_bars['Close'][-1], decimal_point)
        C_1d_P1 = round(day_1_bars['Close'][-2], decimal_point)
        C_1d_P2 = round(day_1_bars['Close'][-3], decimal_point)

        M_1d_C0 = round(macd_1['MACD_12_26_9'][-1], decimal_point)
        M_1d_P1 = round(macd_1['MACD_12_26_9'][-2], decimal_point)
        H_1d_C0 = round(macd_1['MACDh_12_26_9'][-1], decimal_point)
        H_1d_P1 = round(macd_1['MACDh_12_26_9'][-2], decimal_point)

        M_60m_C0 = round(macd_60['MACD_12_26_9'][-1], decimal_point)
        M_60m_P1 = round(macd_60['MACD_12_26_9'][-2], decimal_point)
        H_60m_C0 = round(macd_60['MACDh_12_26_9'][-1], decimal_point)
        H_60m_P1 = round(macd_60['MACDh_12_26_9'][-2], decimal_point)
        H_60m_P2 = round(macd_60['MACDh_12_26_9'][-3], decimal_point)
        S_60m_C0 = round(macd_60['MACDs_12_26_9'][-1], decimal_point)
        S_60m_P1 = round(macd_60['MACDs_12_26_9'][-2], decimal_point)
        S_60m_P2 = round(macd_60['MACDs_12_26_9'][-3], decimal_point) 

        M_15m_C0 = round(macd_15['MACD_12_26_9'][-1], decimal_point)
        M_15m_P1 = round(macd_15['MACD_12_26_9'][-2], decimal_point)
        H_15m_C0 = round(macd_15['MACDh_12_26_9'][-1], decimal_point)
        H_15m_P1 = round(macd_15['MACDh_12_26_9'][-2], decimal_point)

        M_5m_C0 = round(macd_5['MACD_12_26_9'][-1], decimal_point)
        M_5m_P1 = round(macd_5['MACD_12_26_9'][-2], decimal_point)
        H_5m_C0 = round(macd_5['MACDh_12_26_9'][-1], decimal_point)
        H_5m_P1 = round(macd_5['MACDh_12_26_9'][-2], decimal_point)

        RSI_5m_C0 = round(rsi_5[-1], decimal_point_rsi)
        RSI_15m_C0 = round(rsi_15[-1], decimal_point_rsi)
        RSI_60m_C0 = round(rsi_60[-1], decimal_point_rsi)
        RSI_min = 50.00
        RSI_max = 75.00

        Vol_5m_C0 = minute_5_bars['Volume'][-1]
        Vol_threshold = 1000

        market_price = round(minute_5_bars['Close'][-1], decimal_point)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:

                # Model_DR1: 
                if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_15m_C0 > 0.0000 and M_60m_C0 > M_60m_P1 and S_60m_C0 > S_60m_P1 and H_60m_C0 > 0.0000:

                    # Check RSI and volume
                    if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                        print(f" - It's buy signal for Model DR1")         
                        quantity = calculate_quantity(market_price)
                        print(f" - Placing buy order for {symbol} at {market_price}.")

                        # Placing order
                        try:
                            api.submit_order(
                                symbol=symbol,
                                side='buy',
                                type='market',
                                qty=quantity,
                                time_in_force='gtc'
                            )
                        except Exception as e:
                            print(f" - Could not submit order {e}\n")  
                    else:
                        print(f" - RSI is overbought at RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for Models DR1\n")
                
                # Model_DR1_END
                else:
                    print(" - One of the conditions do not pass for Models DR1\n")
            
            else:
                print(f' - The order of stock {symbol} is placed\n')

        elif symbol in existing_position_symbols:
            try:
                print(f" - Already in the position")
                position = api.get_position(symbol)
                quantity = position.qty
                entry_price = float(position.avg_entry_price)
                market_value = abs(float(position.market_value))
                cost = abs(float(position.cost_basis))

                day_bars = ticker.history(interval='1d',period='1mo')
                EMA_10d_bars = day_bars['Close'].ewm(span=10, adjust=False).mean()
                EMA_10d = EMA_10d_bars[-1]

            except Exception as e:
                print(f"The order may not be filled")

            # Strategy 1 for taking profit at 1.0%
            if market_value > (1.01 * cost):
                print(f" - It's taking-profit signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

            # Strategy 2 for cutting loss at 7.5%
            elif market_price < EMA_10d and market_value < (0.925 * cost):
                print(f" - It's cut-loss signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

            # Strategy 3 for cutting loss should not greater than 7.5%
            elif market_value < (0.925 * cost):
                print(f" - It's cut-loss signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

                print(f" - It's cut-loss signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

            else:
                print(" - No sell signal yet\n")

        else: 
            print(" - It's already been traded for today.\n")
  
    # Breakout Strategy Model-DX1
    for symbol in symbols_DX1:
        print(f'{symbol}_{current_time}\n')

        ticker = yf.Ticker(symbol)

        minute_5_bars = ticker.history(interval='5m',period='5d')
        minute_15_bars = ticker.history(interval='15m',period='5d')
        minute_60_bars = ticker.history(interval='60m',period='1mo')
        day_1_bars = ticker.history(interval='1d',period='6mo')

        ## When running on Linux, activate this part before indicator setting section 

        most_updated_5m_close = minute_5_bars['Close'][-1]
        minute_5_bars.loc[minute_5_bars.index[-2],'Close'] = most_updated_5m_close
        minute_5_bars.drop(index=minute_5_bars.index[-1],axis=0,inplace=True)

        # References
        # https://predictivehacks.com/?all-tips=replace-values-based-on-index-in-pandas-dataframes
        # https://stackoverflow.com/questions/66096734/pandas-df-loc-1-col-sometimes-work-and-sometimes-add-extra-row-with-nan

        most_updated_15m_close = minute_15_bars['Close'][-1]
        minute_15_bars.loc[minute_15_bars.index[-2],'Close'] = most_updated_15m_close
        minute_15_bars.drop(index=minute_15_bars.index[-1],axis=0,inplace=True)

        most_updated_60m_close = minute_60_bars['Close'][-1]
        minute_60_bars.loc[minute_60_bars.index[-2],'Close'] = most_updated_60m_close
        minute_60_bars.drop(index=minute_60_bars.index[-1],axis=0,inplace=True)

        # most_updated_1d_close = day_1_bars['Close'][-1]
        # day_1_bars.loc[day_1_bars.index[-2],'Close'] = most_updated_1d_close
        # day_1_bars.drop(index=day_1_bars.index[-1],axis=0,inplace=True)

        # Indicator Setting
        macd_5 = minute_5_bars.ta.macd()        
        macd_15 = minute_15_bars.ta.macd()
        macd_60 = minute_60_bars.ta.macd()
        macd_1 = day_1_bars.ta.macd()

        rsi_5 = minute_5_bars.ta.rsi()
        rsi_15 = minute_15_bars.ta.rsi()
        rsi_60 = minute_60_bars.ta.rsi()

        # df = pd.concat([minute_5_bars['Close'], minute_5_bars['Open'], macd_5_bars['MACD_12_26_9'], rsi], axis=1)
        # print(df)

        decimal_point = 4
        decimal_point_rsi = 2

        # Candle Stick
        C_60m_C0 = round(minute_60_bars['Close'][-1], decimal_point)
        # O_60m_C0 = round(minute_60_bars['Open'][-1], decimal_point)
        C_60m_P1 = round(minute_60_bars['Close'][-2], decimal_point)
        # O_60m_P1 = round(minute_60_bars['Open'][-2], decimal_point)
        C_60m_P2 = round(minute_60_bars['Close'][-3], decimal_point)

        C_1d_C0 = round(day_1_bars['Close'][-1], decimal_point)
        C_1d_P1 = round(day_1_bars['Close'][-2], decimal_point)
        C_1d_P2 = round(day_1_bars['Close'][-3], decimal_point)

        M_1d_C0 = round(macd_1['MACD_12_26_9'][-1], decimal_point)
        M_1d_P1 = round(macd_1['MACD_12_26_9'][-2], decimal_point)
        H_1d_C0 = round(macd_1['MACDh_12_26_9'][-1], decimal_point)
        H_1d_P1 = round(macd_1['MACDh_12_26_9'][-2], decimal_point)

        M_60m_C0 = round(macd_60['MACD_12_26_9'][-1], decimal_point)
        M_60m_P1 = round(macd_60['MACD_12_26_9'][-2], decimal_point)
        H_60m_C0 = round(macd_60['MACDh_12_26_9'][-1], decimal_point)
        H_60m_P1 = round(macd_60['MACDh_12_26_9'][-2], decimal_point)
        H_60m_P2 = round(macd_60['MACDh_12_26_9'][-3], decimal_point) 
        S_60m_C0 = round(macd_60['MACDs_12_26_9'][-1], decimal_point)
        S_60m_P1 = round(macd_60['MACDs_12_26_9'][-2], decimal_point)
        S_60m_P2 = round(macd_60['MACDs_12_26_9'][-3], decimal_point) 

        M_15m_C0 = round(macd_15['MACD_12_26_9'][-1], decimal_point)
        M_15m_P1 = round(macd_15['MACD_12_26_9'][-2], decimal_point)
        H_15m_C0 = round(macd_15['MACDh_12_26_9'][-1], decimal_point)
        H_15m_P1 = round(macd_15['MACDh_12_26_9'][-2], decimal_point)

        M_5m_C0 = round(macd_5['MACD_12_26_9'][-1], decimal_point)
        M_5m_P1 = round(macd_5['MACD_12_26_9'][-2], decimal_point)
        H_5m_C0 = round(macd_5['MACDh_12_26_9'][-1], decimal_point)
        H_5m_P1 = round(macd_5['MACDh_12_26_9'][-2], decimal_point)

        RSI_5m_C0 = round(rsi_5[-1], decimal_point_rsi)
        RSI_15m_C0 = round(rsi_15[-1], decimal_point_rsi)
        RSI_60m_C0 = round(rsi_60[-1], decimal_point_rsi)
        RSI_min = 50.00
        RSI_max = 75.00

        Vol_5m_C0 = minute_5_bars['Volume'][-1]
        Vol_threshold = 1000

        market_price = round(minute_5_bars['Close'][-1], decimal_point)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:

                # Model_DX1: 
                if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_15m_C0 > 0.0000 and M_60m_C0 > M_60m_P1 and S_60m_C0 > S_60m_P1 and H_60m_C0 > 0.0000:

                    # Check RSI and volume
                    if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                        print(f" - It's buy signal for Model DX1")         
                        quantity = calculate_quantity(market_price)
                        print(f" - Placing buy order for {symbol} at {market_price}.")

                        # Placing order
                        try:
                            api.submit_order(
                                symbol=symbol,
                                side='buy',
                                type='market',
                                qty=quantity,
                                time_in_force='gtc'
                            )
                        except Exception as e:
                            print(f" - Could not submit order {e}\n")  
                    else:
                        print(f" - RSI is overbought at RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for Models DX1\n")
 
                # Model_DX1_END
                else:
                    print(" - One of the conditions do not pass for Models DX1\n")
            
            else:
                print(f' - The order of stock {symbol} is placed\n')

        elif symbol in existing_position_symbols:
            try:
                print(f" - Already in the position")
                position = api.get_position(symbol)
                quantity = position.qty
                entry_price = float(position.avg_entry_price)
                market_value = abs(float(position.market_value))
                cost = abs(float(position.cost_basis))

                day_bars = ticker.history(interval='1d',period='1mo')
                EMA_10d_bars = day_bars['Close'].ewm(span=10, adjust=False).mean()
                EMA_10d = EMA_10d_bars[-1]

            except Exception as e:
                print(f"The order may not be filled")

            # Strategy 1 for taking profit at 1.0%
            if market_value > (1.01 * cost):
                print(f" - It's taking-profit signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

            # Strategy 2 for cutting loss at 7.5%
            elif market_price < EMA_10d and market_value < (0.925 * cost):
                print(f" - It's cut-loss signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

            # Strategy 3 for cutting loss should not greater than 7.5%
            elif market_value < (0.925 * cost):
                print(f" - It's cut-loss signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

                print(f" - It's cut-loss signal.")
                print(f" - Placing sell order for {symbol} at {market_price}.\n")

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

            else:
                print(" - No sell signal yet\n")

        else: 
            print(" - It's already been traded for today.\n")

else:
    print(f"The market is closed")
