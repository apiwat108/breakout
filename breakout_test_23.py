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

    symbols = config.BREAKOUT_SYMBOLS
    BB_symbols = config.BB_SYMBOLS

    current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
    current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")

    orders = api.list_orders(status='all', after=current_date)
    existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']
    positions = api.list_positions()
    existing_position_symbols = [position.symbol for position in positions]
    print(current_time)

    # AB Strategy
    for symbol in symbols:
        print(symbol)

        ticker = yf.Ticker(symbol)

        minute_5_bars = ticker.history(interval='5m',period='5d')#start=current_date, end=current_date)
        minute_15_bars = ticker.history(interval='15m',period='5d')
        minute_60_bars = ticker.history(interval='60m',period='1mo')

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

        # ## Indicator Setting
        macd_5 = minute_5_bars.ta.macd()
        macd_15 = minute_15_bars.ta.macd()
        macd_60 = minute_60_bars.ta.macd()

        rsi_5 = minute_5_bars.ta.rsi()
        rsi_15 = minute_15_bars.ta.rsi()
        rsi_60 = minute_60_bars.ta.rsi()

        # df = pd.concat([minute_5_bars['Close'], minute_5_bars['Open'], macd_5_bars['MACD_12_26_9'], rsi], axis=1)
        # print(df)

        # Candle Stick
        C_60m_C0 = minute_60_bars['Close'][-1]
        O_60m_C0 = minute_60_bars['Open'][-1]
        C_60m_P1 = minute_60_bars['Close'][-2]
        O_60m_P1 = minute_60_bars['Open'][-2]

        C_15m_C0 = minute_15_bars['Close'][-1]
        O_15m_C0 = minute_15_bars['Open'][-1]
        C_15m_P1 = minute_15_bars['Close'][-2]
        O_15m_P1 = minute_15_bars['Open'][-2]
        C_15m_P2 = minute_15_bars['Close'][-3]
        O_15m_P2 = minute_15_bars['Open'][-3]

        C_5m_C0 = minute_5_bars['Close'][-1]
        O_5m_C0 = minute_5_bars['Open'][-1]
        C_5m_P1 = minute_5_bars['Close'][-2]
        O_5m_P1 = minute_5_bars['Open'][-2]

        decimal_point = 4

        M_60m_C0 = round(macd_60['MACD_12_26_9'][-1], decimal_point)
        M_60m_P1 = round(macd_60['MACD_12_26_9'][-2], decimal_point)
        M_60m_P2 = round(macd_60['MACD_12_26_9'][-3], decimal_point)
        M_60m_P3 = round(macd_60['MACD_12_26_9'][-4], decimal_point)
        H_60m_C0 = round(macd_60['MACDh_12_26_9'][-1], decimal_point)
        limit_60m_H = -0.0040
        
        M_15m_C0 = round(macd_15['MACD_12_26_9'][-1], decimal_point)
        M_15m_P1 = round(macd_15['MACD_12_26_9'][-2], decimal_point)
        M_15m_P2 = round(macd_15['MACD_12_26_9'][-3], decimal_point)
        M_15m_P3 = round(macd_15['MACD_12_26_9'][-4], decimal_point)
        H_15m_C0 = round(macd_15['MACDh_12_26_9'][-1], decimal_point)
        H_15m_P1 = round(macd_15['MACDh_12_26_9'][-2], decimal_point)
        H_15m_P2 = round(macd_15['MACDh_12_26_9'][-3], decimal_point)
        limit_15m_max_M = 0.1500
        limit_15m_min_M = -0.0010
        limit_15m_H = -0.0400
        limit_15m_max_M_case_4 = 0.0090 # (ZAA case for taking profit and CHASE case for not breakout)

        M_5m_C0 = round(macd_5['MACD_12_26_9'][-1], decimal_point)
        M_5m_P1 = round(macd_5['MACD_12_26_9'][-2], decimal_point)
        M_5m_P2 = round(macd_5['MACD_12_26_9'][-3], decimal_point)
        M_5m_P3 = round(macd_5['MACD_12_26_9'][-4], decimal_point)
        H_5m_C0 = round(macd_5['MACDh_12_26_9'][-1], decimal_point)
        H_5m_P1 = round(macd_5['MACDh_12_26_9'][-2], decimal_point)
        H_5m_P2 = round(macd_5['MACDh_12_26_9'][-3], decimal_point)
        H_5m_P3 = round(macd_5['MACDh_12_26_9'][-4], decimal_point)
        S_5m_C0 = round(macd_5['MACDs_12_26_9'][-1], decimal_point)
        S_5m_P1 = round(macd_5['MACDs_12_26_9'][-2], decimal_point)
        limit_5m_M = 0.0200
        limit_5m_Max_Case_2_2 = 0.0800

        RSI_5m_C0 = rsi_5[-1]
        RSI_15m_C0 = rsi_15[-1]
        RSI_60m_C0 = rsi_60[-1]
        V_15m_C0 = minute_15_bars['Volume'][-1]
        V_15m_P1 = minute_15_bars['Volume'][-2]

        market_price = round(minute_5_bars['Close'][-1], 4)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:
            
                # Strategy 1 Based on MCA Model Breakout on 18 Dec and Buy Signal on 20 Dec
                # 60m uptrend with limit of retrace and bullsish reversal candlestick pattern (Bullish Engulfing and One White Soldier)
                    # Added Continuous green candelstick for more 60-m strategy
                if H_60m_C0 > limit_60m_H and C_60m_C0 > C_60m_P1 and C_60m_C0 > O_60m_C0 and 75.0 > RSI_60m_C0 > 50.0: # Could add Bullish Engulfing or One White Soldier

                    # Case-1: 15m-MACD x up Signal with BE/OWS on C0-P1 
                    if H_15m_P1 < 0.0000 and H_15m_C0 > -0.0010 and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0 and 75.0 > RSI_15m_C0 > 55.0 and limit_15m_min_M < M_15m_C0 < limit_15m_max_M and V_15m_C0 > V_15m_P1:
                        print(f'M_15m_P1 = {M_15m_P1}')
                        print(f'M_15m_C0 = {M_15m_C0}')

                        # Case-1-01: 5m-MACD keep rising (NAT 19 Feb 2024: 4:20)                             
                        if M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > H_5m_P1 > 0.0000 and C_5m_C0 > C_5m_P1 and C_5m_C0 > O_5m_C0 and 75.0 > RSI_5m_C0 > 55.0: 
                            print(current_time)
                            print(f'M_5m_P1 = {M_5m_P1}')
                            print(f'M_5m_C0 = {M_5m_C0}')
                            print(f" - It's buy signal for Strategy Case-1-01: 5m-MACD keep rising on the 15m-MACD cross-up")
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

                        # Case-1-02: 5m-MACD x up Signal sync with 15m TF (MCA 20-21 Feb 2024)(MTW 19 Jan 2024 10:00)
                        elif H_5m_P1 < 0.00 and H_5m_C0 > 0.00 and C_5m_C0 > C_5m_P1 and C_5m_C0 > O_5m_C0 and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_M:
                            print(current_time)
                            print(f'H_5m_P1 = {H_5m_P1}')
                            print(f'H_5m_C0 = {H_5m_C0}')
                            print(f" - It's buy signal for Strategy 15m Case-1-02: 5m-MACD cross up Signal on the 15m_BE/OWS bar of the 15m-MACD cross up")
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

                        # Case-1-03: 5m-Signal x up 0-line sync with 15m TF (CHASE 4 Jan 2024 10:35)
                        elif S_5m_P1 < 0.00 and S_5m_C0 > 0.00 and 75.0 > RSI_5m_C0 > 55.0:
                            print(current_time)
                            print(f'S_5m_P1 = {S_5m_P1}')
                            print(f'S_5m_C0 = {S_5m_C0}')
                            print(f" - It's buy signal for Strategy 15m Case-1-02: 5m-Signal cross up 0-line on sync with the 15m-MACD cross up")
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

                        else:
                            print(" - 5m conditions do not pass for Strategy 1, Case-1\n")

                    # Case-2: 15m-MACD x up Signal at 0-line with BE or OWS (TMC 5-8 Jan 2024)
                    elif H_15m_P1 < 0.0000 and H_15m_C0 > 0.0000 and M_15m_P1 < 0.0000 and M_15m_C0 < 0.0005 and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0 and 75.0 > RSI_15m_C0 > 50.0 and -0.0100 < M_15m_C0 < limit_15m_max_M and H_15m_C0 > -0.0050:
                        
                        # Case-2-01: 5m-MACD x up 0-line with BE/OWS on C0-P1 (TMC 5-8 Jan 2024)
                        if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and C_5m_C0 > C_5m_P1 and C_5m_C0 > O_5m_C0 and 75.0 > RSI_5m_C0 > 55.0:
                            print(current_time)
                            print(f'M_5m_P1 = {M_5m_P1}')
                            print(f'M_5m_C0 = {M_5m_C0}')
                            print(f" - It's buy signal for Strategy Case-2-01: 5m-MACD cross up 0-line on the 15m-BE/OWS bar of the 15m-MACD cross up at 0-line")
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
            
                        else:
                            print(" - 5m conditions do not pass for Strategy 1, case-2\n")     

                    else:
                        print(" - 15m conditions do not pass for Strategy 1\n")

                else:
                    print(" - 60m conditions do not pass for Stratergy 1\n")

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
            try:
                # Strategy 1 for taking profit 1
                if market_value > (1.01 * cost):    # 0 < H_5m_C0 < H_5m_P1 < H_5m_P2 and H_5m_P2 > H_5m_P3 and M_5m_P2 > 0 and S_5m_P3 > 0:
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

                # Strategy 2 for cutting loss
                elif market_price < EMA_10d:
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
            except Exception as e:
                print(f"Something went wrong")
        else: 
            print(" - It's already been traded for today.\n")

    # BB Strategy
    for symbol in BB_symbols:
        print(symbol)

        ticker = yf.Ticker(symbol)

        minute_5_bars = ticker.history(interval='5m',period='5d')#start=current_date, end=current_date)
        minute_15_bars = ticker.history(interval='15m',period='5d')
        minute_60_bars = ticker.history(interval='60m',period='1mo')

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

        # ## Indicator Setting
        macd_5 = minute_5_bars.ta.macd()
        macd_15 = minute_15_bars.ta.macd()
        macd_60 = minute_60_bars.ta.macd()

        rsi_5 = minute_5_bars.ta.rsi()
        rsi_15 = minute_15_bars.ta.rsi()
        rsi_60 = minute_60_bars.ta.rsi()

        # df = pd.concat([minute_5_bars['Close'], minute_5_bars['Open'], macd_5_bars['MACD_12_26_9'], rsi], axis=1)
        # print(df)

        # Candle Stick
        C_60m_C0 = minute_60_bars['Close'][-1]
        O_60m_C0 = minute_60_bars['Open'][-1]
        C_60m_P1 = minute_60_bars['Close'][-2]
        O_60m_P1 = minute_60_bars['Open'][-2]
        High_60m_P1 = minute_60_bars['High'][-1]

        C_15m_C0 = minute_15_bars['Close'][-1]
        O_15m_C0 = minute_15_bars['Open'][-1]
        C_15m_P1 = minute_15_bars['Close'][-2]
        O_15m_P1 = minute_15_bars['Open'][-2]
        C_15m_P2 = minute_15_bars['Close'][-3]
        O_15m_P2 = minute_15_bars['Open'][-3]
        High_15m_P1 = minute_15_bars['High'][-1]

        C_5m_C0 = minute_5_bars['Close'][-1]
        O_5m_C0 = minute_5_bars['Open'][-1]
        C_5m_P1 = minute_5_bars['Close'][-2]
        O_5m_P1 = minute_5_bars['Open'][-2]
        High_5m_P1 = minute_5_bars['High'][-1]

        decimal_point = 4

        M_60m_C0 = round(macd_60['MACD_12_26_9'][-1], decimal_point)
        M_60m_P1 = round(macd_60['MACD_12_26_9'][-2], decimal_point)
        M_60m_P2 = round(macd_60['MACD_12_26_9'][-3], decimal_point)
        M_60m_P3 = round(macd_60['MACD_12_26_9'][-4], decimal_point)
        H_60m_C0 = round(macd_60['MACDh_12_26_9'][-1], decimal_point)
        H_60m_P1 = round(macd_60['MACDh_12_26_9'][-2], decimal_point)
        H_60m_P2 = round(macd_60['MACDh_12_26_9'][-3], decimal_point) 
        H_60m_P3 = round(macd_60['MACDh_12_26_9'][-4], decimal_point)
        H_60m_P4 = round(macd_60['MACDh_12_26_9'][-5], decimal_point)
        H_60m_P5 = round(macd_60['MACDh_12_26_9'][-6], decimal_point)         
        limit_60m_H = -0.0040
        
        M_15m_C0 = round(macd_15['MACD_12_26_9'][-1], decimal_point)
        M_15m_P1 = round(macd_15['MACD_12_26_9'][-2], decimal_point)
        M_15m_P2 = round(macd_15['MACD_12_26_9'][-3], decimal_point)
        M_15m_P3 = round(macd_15['MACD_12_26_9'][-4], decimal_point)
        H_15m_C0 = round(macd_15['MACDh_12_26_9'][-1], decimal_point)
        H_15m_P1 = round(macd_15['MACDh_12_26_9'][-2], decimal_point)
        H_15m_P2 = round(macd_15['MACDh_12_26_9'][-3], decimal_point)
        limit_15m_max_M = 0.1000
        limit_15m_min_M = -0.0010
        limit_15m_H = -0.0400
        limit_15m_max_M_case_4 = 0.0090 # (ZAA case for taking profit and CHASE case for not breakout)

        M_5m_C0 = round(macd_5['MACD_12_26_9'][-1], decimal_point)
        M_5m_P1 = round(macd_5['MACD_12_26_9'][-2], decimal_point)
        M_5m_P2 = round(macd_5['MACD_12_26_9'][-3], decimal_point)
        M_5m_P3 = round(macd_5['MACD_12_26_9'][-4], decimal_point)
        H_5m_C0 = round(macd_5['MACDh_12_26_9'][-1], decimal_point)
        H_5m_P1 = round(macd_5['MACDh_12_26_9'][-2], decimal_point)
        H_5m_P2 = round(macd_5['MACDh_12_26_9'][-3], decimal_point)
        H_5m_P3 = round(macd_5['MACDh_12_26_9'][-4], decimal_point)
        limit_5m_M = 0.0200
        limit_5m_Max_Case_2_2 = 0.0800

        RSI_5m_C0 = rsi_5[-1]
        RSI_15m_C0 = rsi_15[-1]
        RSI_60m_C0 = rsi_60[-1]

        market_price = round(minute_5_bars['Close'][-1], 4)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:


                # Model_01A: MACD cross up
                if M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000: # need SBF
                    SCF_60m = (H_60m_P1 - H_60m_C0)/H_60m_P1*100          # Significant Cross-up Factor 5m (CIEN 1 Mar 2024: H_5m_C0 = 0.0247 > H_5m_P1 = -0.0027 --> SCF = 1014%)
                    print(f'SCF_60m = {SCF_60m}')
                    SCF_60m_threshold = 200

                    # Model_01A-01: 15m-MACD keep rising
                    if SCF_60m > SCF_60m_threshold and M_15m_C0 > M_15m_P1 > 0.0000 and H_15m_C0 > H_15m_P1 > 0.0000 and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0: 
                        
                        # Model_01A-01-01
                        if M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > H_5m_P1 > 0.0000:
                            print(f" - It's buy signal for BB_1 Strategy, Model_01A-01-01")
                            print(f'H_60m_C0 = {H_60m_C0}')
                            print(f'H_60m_P1 = {H_60m_P1}')
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

                        # Model_01A-01-02
                        elif M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000:
                            print(f" - It's buy signal for BB_1 Strategy, Model_01-01-02")
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
                        else:
                            print(" - 5m conditions do not pass for Strategy 1\n")

                    # Model_01A-02: 15m-MACD cross up
                    elif O_15m_P1 > C_15m_P1 and C_15m_C0 > O_15m_P1 and 75.0 > RSI_15m_C0 > 55.0 and limit_15m_min_M < M_15m_C0 < limit_15m_max_M:
                        
                        # Case_2_1: 5m x Up Triggered
                        if ((H_5m_C0 > 0.00 and H_5m_P1 < 0.00) or (M_5m_C0 > 0.00 and M_5m_P1 < 0.00)) and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_M:
                            print(f" - It's buy signal for Strategy 15m Case-2_1: 5m x Up Triggered on 15m Bullish Engulfing or One White Soldier")
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

                        # Case_2_2: 5m Bullish Breakout Triggered on 15m Bullish Engulfing or One White Soldier (NVST 22 Jan)
                        elif O_5m_P1 > C_5m_P1 and C_5m_C0 > O_5m_C0 and C_5m_C0 > C_5m_P1 and H_5m_P1 > 0.00 and H_5m_P2 > 0.00 and H_5m_P3 < 0.00 and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_Max_Case_2_2:
                            print(f" - It's buy signal for Strategy 15m Case-2_2: 5m Bullish Breakout Triggered on 15m Bullish Engulfing or One White Soldi")
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

                        else:
                            print(" - 5m conditions do not pass for Strategy 1\n")  

                    # 15m Case-3: 5m x Up Triggered just after 15m Bullish Engulfing or One White Soldier (TMC 5 Jan to 8 Jan)
                    elif O_15m_P2 > C_15m_P2 and C_15m_P1 > O_15m_P2 and 75.0 > RSI_15m_C0 > 50.0 and -0.0100 < M_15m_C0 < limit_15m_max_M and H_15m_C0 > -0.0050:
                        if ((H_5m_C0 > 0.00 and H_5m_P1 < 0.00) or (M_5m_C0 > 0.00 and M_5m_P1 < 0.00)) and 75.0 > RSI_5m_C0 > 55.0 and -0.0100 < M_5m_C0 < limit_5m_M:
                            print(f" - It's buy signal for Strategy 15m Case-3: 5m x Up Triggered just after 15m Bullish Engulfing or One White Soldier")
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

                        elif H_5m_P1 > 0.00 and H_5m_P2 < 0.00 and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_M:
                            print(f" - It's buy signal for Strategy 1.")
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

                        else:
                            print(" - 5m conditions do not pass for Strategy 1\n")  

                    # 15m Case-4: 5m x Up Triggered on Continuous Green Bar (ZAA 5 JAN)
                    elif C_15m_P1 > O_15m_P1 and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0 and 75.0 > RSI_15m_C0 > 50.0 and limit_15m_min_M < M_15m_C0 < limit_15m_max_M_case_4:
                        
                        # 5m Case-4_1: 5m x Up
                        if ((H_5m_C0 > 0.00 and H_5m_P1 < 0.00) or (M_5m_C0 > 0.00 and M_5m_P1 < 0.00)) and 75.0 > RSI_5m_C0 > 50.0 and M_5m_C0 < limit_5m_M:
                            print(f" - It's buy signal for Strategy 15m Case-4: 5m x Up Triggered on Continuous Green Bar (4_1)")
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

                        # 5m Case-4_2: Continuous Green Bar after x up CHASE (4 JAN)
                        elif C_5m_C0 > O_5m_C0 and C_5m_C0 > C_5m_P1 and C_5m_P1 > O_5m_P1 and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_M:
                            print(f" - It's buy signal for Strategy 15m Case-4: 5m x Up Triggered on Continuous Green Bar (4_2)")
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

                        else:
                            print(" - 5m conditions do not pass for Strategy 1\n")   

                    else:
                        print(" - 15m conditions do not pass for Strategy 1\n")

                # Model_01B: Gap up (AVGO)
                if M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000 and O_60m_C0 > High_60m_P1:

                    # Model_01B-01: 15m-MACD cross up and gap up (AVGO)
                    if M_15m_C0 > M_15m_P1 > 0.0000 and H_15m_C0 > 0.0000 and H_15m_P1 < 0.0000 and O_15m_C0 > High_15m_P1:
                        
                        # Model_01B-01-01: 5m-MACD cross up 0-line and gap up (AVGO 1 Mar 2024)
                        if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_5m_C0 > H_5m_P1 > 0.0000 and O_5m_C0 > High_5m_P1:
                            print(f" - It's buy signal for BB_1 Strategy, Model_01-01-01")
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

                # Model_01C: Continuous (CIEN and FIP 1 Mar 2024)                  
                SBF_60m = 1.5                 # Significant Breakout Factor 60m (CIEN 1 Mar 2024: H_60m_C0 = 0.1482 > H_60m_P1 = 0.0216 --> SBF = 6.86)
                                                                            #   (FIP 1 Mar 2024: H_60m_C0 = 0.0310 > H_60m_P1 > 0.0202 --> SBF = 1.55 )
                if M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > (SBF_60m * H_60m_P1):

                    # Model_01C-01: Countinuous (CIEN 1 Mar 2024)
                    SBF_15m = 25            # Significant Breakout Factor 15m (CIEN 1 Mar 2024: H_15m_C0 = 0.0869 > H_60m_P1 = 0.0031 --> SBF = 28.03)
                    if M_15m_C0 > M_15m_P1 > 0.0000 and H_15m_C0 > (SBF_15m * H_15m_P1):
                        
                        # Model_01C-01-01: 5m-MACD cross up (CIEN 1 Mar 2024)
                        SCF_5m = (H_5m_P1 - H_5m_C0)/H_5m_P1*100            # Significant Cross-up Factor 5m (CIEN 1 Mar 2024: H_5m_C0 = 0.0247 > H_5m_P1 = -0.0027 --> SCF = 1014%)
                        SCF_5m_threshold = 500
                        if M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and SCF_5m > SCF_5m_threshold:
                            print(f" - It's buy signal for BB_1 Strategy, Model_01C-01-01")
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

                # # 60m Case-2: Based on CLFD Model Breakout on 2 Feb
                # elif M_60m_C0 > 0.0000 and M_60m_P1 < 0.000 and H_60m_P2 > 0.000 and H_60m_P3 < 0.0000 and 75.0 > RSI_60m_C0 > 50.0:
                
                #     # 15m Case-1: MACD > Signal > 0-line
                #     if M_15m_C0 > 0.0000 and H_15m_C0 > 0.0000 and 75.0 > RSI_15m_C0 > 55.0:
                #         if M_5m_C0 > 0.0000 and H_5m_C0 > - 0.0300 and 75.0 > RSI_5m_C0 > 55.0:
                #             print(f" - It's buy signal for BB Strategy Case-2: CLFD Model")
                #             quantity = calculate_quantity(market_price)
                #             print(f" - Placing buy order for {symbol} at {market_price}.\n")

                #             try:
                #                 api.submit_order(
                #                     symbol=symbol,
                #                     side='buy',
                #                     type='market',
                #                     qty=quantity,
                #                     time_in_force='gtc'
                #                 )
                #             except Exception as e:
                #                 print(f"Could not submit order {e}")    
                #         else:
                #             print(" - 5m conditions do not pass for Strategy 1\n")
                #     else:
                #         print(" - 15m conditions do not pass for Strategy 1\n")

                # # 60m Case-3: Just MACD cross up 0-line
                # elif M_60m_C0 > 0.0000 and M_60m_P1 < 0.000 and 75.0 > RSI_60m_C0 > 50.0:
                
                #     # 15m Case-1: MACD > Signal > 0-line
                #     if M_15m_C0 > 0.0000 and H_15m_C0 > 0.0000 and 75.0 > RSI_15m_C0 > 55.0:
                #         if M_5m_C0 > 0.0000 and H_5m_C0 > - 0.0300 and 75.0 > RSI_5m_C0 > 55.0:
                #             print(f" - It's buy signal for BB Strategy Case-3: 60m MACD cross up 0-line")
                #             quantity = calculate_quantity(market_price)
                #             print(f" - Placing buy order for {symbol} at {market_price}.\n")

                #             try:
                #                 api.submit_order(
                #                     symbol=symbol,
                #                     side='buy',
                #                     type='market',
                #                     qty=quantity,
                #                     time_in_force='gtc'
                #                 )
                #             except Exception as e:
                #                 print(f"Could not submit order {e}")    
                #         else:
                #             print(" - 5m conditions do not pass for Strategy 1\n")
                #     else:
                #         print(" - 15m conditions do not pass for Strategy 1\n")
                
                else:
                    print(" - 60m conditions do not pass for Stratergy 1\n")

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

            # Strategy 1 for taking profit 1
            if market_value > (1.01 * cost):    # 0 < H_5m_C0 < H_5m_P1 < H_5m_P2 and H_5m_P2 > H_5m_P3 and M_5m_P2 > 0 and S_5m_P3 > 0:
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

            # Strategy 2 for cutting loss
            elif market_price < EMA_10d:
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
