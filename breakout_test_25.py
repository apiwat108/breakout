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
    print(f'{current_time}\n')

    # AB Strategy
    for symbol in symbols:
        print(f'{symbol}_{current_time}')

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
        decimal_point = 4

        C_60m_C0 = round(minute_60_bars['Close'][-1], decimal_point)
        O_60m_C0 = round(minute_60_bars['Open'][-1], decimal_point)
        C_60m_P1 = round(minute_60_bars['Close'][-2], decimal_point)
        O_60m_P1 = round(minute_60_bars['Open'][-2], decimal_point)

        C_15m_C0 = round(minute_15_bars['Close'][-1], decimal_point)
        O_15m_C0 = round(minute_15_bars['Open'][-1], decimal_point)
        C_15m_P1 = round(minute_15_bars['Close'][-2], decimal_point)
        O_15m_P1 = round(minute_15_bars['Open'][-2], decimal_point)
        C_15m_P2 = round(minute_15_bars['Close'][-3], decimal_point)
        O_15m_P2 = round(minute_15_bars['Open'][-3], decimal_point)

        C_5m_C0 = round(minute_5_bars['Close'][-1], decimal_point)
        O_5m_C0 = round(minute_5_bars['Open'][-1], decimal_point)
        C_5m_P1 = round(minute_5_bars['Close'][-2], decimal_point)
        O_5m_P1 = round(minute_5_bars['Open'][-2], decimal_point)

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
                                            
                        # Significant Cross-up Factor 15m
                        # (NAT 19 Feb 2024: 4:20 H_15m_C0 = 0.0359 > H_15m_P1 = -0.0024 --> SCF = 1596%)
                        # (ACB 28 Mar 2024: (11:30) H_15m_C0 = 0.0012 > H_15m_P1 = -0.0115 --> SCF = 110%)
                        SCF_15m_AB_01 = round((H_15m_P1 - H_15m_C0)/H_15m_P1*100, decimal_point)       
                        SCF_15m_AB_01_threshold = 300.0

                        # Case-1-01: 5m-MACD keep rising (NAT 19 Feb 2024: 4:20) 
                        # Need SBF (TALK 1 Mar 11:10 and Case for 15m-MACD cross up 0-line TALK 5 Mar 15:30)                           
                        if SCF_15m_AB_01 > SCF_15m_AB_01_threshold and M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > H_5m_P1 > 0.0000 and C_5m_C0 > C_5m_P1 and C_5m_C0 > O_5m_C0 and 75.0 > RSI_5m_C0 > 55.0: 
                            print(f" - It's buy signal for Strategy Case-1-01: 5m-MACD keep rising on the 15m-MACD cross-up")                            
                            print(f'H_15m_P1 = {H_15m_P1}')
                            print(f'H_15m_C0 = {H_15m_C0}')
                            print(f'SCF_15m_AB_01 = {SCF_15m_AB_01} > SCF_15m_AB_01_threshold = {SCF_15m_AB_01_threshold}')
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
                            print(f" - It's buy signal for Strategy 15m Case-1-02: 5m-MACD cross up Signal on the 15m_BE/OWS bar of the 15m-MACD cross up")
                            print(f'H_15m_P1 = {H_15m_P1}')
                            print(f'H_15m_C0 = {H_15m_C0}')
                            print(f'SCF_15m_AB_01 = {SCF_15m_AB_01} > SCF_15m_AB_01_threshold = {SCF_15m_AB_01_threshold}')
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
                            print(f" - It's buy signal for Strategy 15m Case-1-03: 5m-Signal cross up 0-line on sync with the 15m-MACD cross up")
                            print(f'H_15m_P1 = {H_15m_P1}')
                            print(f'H_15m_C0 = {H_15m_C0}')
                            print(f'SCF_15m_AB_01 = {SCF_15m_AB_01} > SCF_15m_AB_01_threshold = {SCF_15m_AB_01_threshold}')
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

                # Strategy 3 for cutting loss should not greater than 2.5%
                elif market_value < (0.975 * cost):
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
        print(f'{symbol}_{current_time}')

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

        decimal_point = 4

        # Candle Stick
        C_60m_C0 = round(minute_60_bars['Close'][-1], decimal_point)
        O_60m_C0 = round(minute_60_bars['Open'][-1], decimal_point)
        C_60m_P1 = round(minute_60_bars['Close'][-2], decimal_point)
        O_60m_P1 = round(minute_60_bars['Open'][-2], decimal_point)
        High_60m_P1 = round(minute_60_bars['High'][-1], decimal_point)

        C_15m_C0 = round(minute_15_bars['Close'][-1], decimal_point)
        O_15m_C0 = round(minute_15_bars['Open'][-1], decimal_point)
        C_15m_P1 = round(minute_15_bars['Close'][-2], decimal_point)
        O_15m_P1 = round(minute_15_bars['Open'][-2], decimal_point)
        C_15m_P2 = round(minute_15_bars['Close'][-3], decimal_point)
        O_15m_P2 = round(minute_15_bars['Open'][-3], decimal_point)
        High_15m_P1 = round(minute_15_bars['High'][-1], decimal_point)

        C_5m_C0 = round(minute_5_bars['Close'][-1], decimal_point)
        O_5m_C0 = round(minute_5_bars['Open'][-1], decimal_point)
        C_5m_P1 = round(minute_5_bars['Close'][-2], decimal_point)
        O_5m_P1 = round(minute_5_bars['Open'][-2], decimal_point)
        High_5m_P1 = round(minute_5_bars['High'][-1], decimal_point)

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

        # RSI_5m_C0 = rsi_5[-1]
        # RSI_15m_C0 = rsi_15[-1]
        # RSI_60m_C0 = rsi_60[-1]

        market_price = round(minute_5_bars['Close'][-1], decimal_point)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:

                # # Model_01A: 60m-MACD cross up above 0-line
                # if M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000: # need SBF
                #     # Significant Cross-up Factor 60m (DOCN 1 Mar 2024: H_60m_C0 = 0.0544 > H_5m_P1 = -0.0474 --> SCF = 214%)
                #     SCF_60m = round((H_60m_P1 - H_60m_C0)/H_60m_P1*100, decimal_point)      
                #     SCF_60m_threshold = 200

                #     # Model_01A-01: 15m-MACD keep rising
                #     if SCF_60m > SCF_60m_threshold and M_15m_C0 > M_15m_P1 > 0.0000 and H_15m_C0 > H_15m_P1 > 0.0000 and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0: 
                                                
                #         # Significant Breakout Factor 15m (JHG 27 Mar (13:45-14:00) H_15m_C0 = 0.0200 > H_15m_P1 = 0.0175 --> SBF = 1.14)
                #         SBF_15m_01A_01 = round(H_15m_C0/H_15m_P1, decimal_point)       
                #         SBF_15m_01A_01_threshold = 1.12      

                #         # Model_01A-01-01: 5m-MACD keep rising
                #         if SBF_15m_01A_01 > SBF_15m_01A_01_threshold and M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > H_5m_P1 > 0.0000:
                #             print(f" - It's buy signal for BB_1 Strategy, Model_01A-01-01")
                #             print(f' - H_60m_C0 = {H_60m_C0}')
                #             print(f' - H_60m_P1 = {H_60m_P1}')
                #             print(f' - SCF_60m = {SCF_60m} > SCF_60m_threshold = {SCF_60m_threshold}')
                #             print(f' - SBF_15m_01A_01 = {SBF_15m_01A_01} > SBF_15m_01A_01_threshold = {SBF_15m_01A_01_threshold}')                            
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

                #         # Model_01A-01-02: 5m-MACD cross up Signal at 0-line
                #         elif M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000:
                #             print(f" - It's buy signal for BB_1 Strategy, Model_01-01-02")
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

                #     # Model_01A-02: 15m-MACD cross up (DOCN 8 Mar 2024: H_15m_C0 = 0.0368 > H_15m_P1 = -0.0181 --> SCF = 303%)
                #     elif H_15m_C0 > 0.0000 and H_15m_P1 < 0.0000 and C_15m_C0 > O_15m_C0 and C_15m_C0 > C_15m_P1:
                        
                #         # Significant Cross-up Factor 15m (DOCN 8 Mar 2024: H_15m_C0 = 0.0368 > H_15m_P1 = -0.0181 --> SCF = 303%)
                #         SCF_15m_01A_02 = round((H_15m_P1 - H_15m_C0)/H_15m_P1*100, decimal_point)       
                #         SCF_15m_01A_02_threshold = 100.0                        
                        
                #         # Model_01A-02-01: 5m-MACD cross up Signal (DOCN 8 Mar 2024: H_5m_C0 = 0.0134 > H_15m_P1 = -0.0127 --> SCF_5m_01A-02-01 = 205%)
                #         if SCF_15m_01A_02 > SCF_15m_01A_02_threshold and ((H_5m_C0 > 0.000 and H_5m_P1 < 0.000) or (M_5m_C0 > 0.000 and M_15m_P1 < 0.0000)):
                #             print(f" - It's buy signal for BB_1 Strategy, Model_01A-02-01")
                #             print(f' - H_60m_C0 = {H_60m_C0}')
                #             print(f' - H_60m_P1 = {H_60m_P1}')
                #             print(f' - SCF_60m = {SCF_60m} > SCF_60m_threshold = {SCF_60m_threshold}')
                #             print(f' - SCF_15m_01A_02 = {SCF_15m_01A_02} > SCF_15m_01A_02_threshold = {SCF_15m_01A_02_threshold}')
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

                #     # Model_01A-03: 15m-MACD cross up 0-line (BFH 18 Mar 2024: M_15m_C0 = 0.0283 > M_15m_P1 = -0.0236 --> SCF = 219%)
                #     elif M_15m_C0 > 0.0000 and M_15m_P1 < 0.0000 and C_15m_C0 > O_15m_C0 and C_15m_C0 > C_15m_P1:
                        
                #         # Significant Cross-up Factor 15m (BFH 18 Mar 2024: M_15m_C0 = 0.0283 > M_15m_P1 = -0.0236 --> SCF = 219%)
                #         SCF_15m_01A_03 = round((M_15m_P1 - M_15m_C0)/M_15m_P1*100, decimal_point)         
                #         SCF_15m_01A_03_threshold = 100.0                        
                        
                #         # Model_01A-03-01: 5m-MACD keep rising (BFH 18 Mar 2024: M_5m_C0 = 0.0876 > M_5m_P1 = 0.0649 --> SBF_5m_01A-03-01 = 1.35)
                #         if SCF_15m_01A_03 > SCF_15m_01A_03_threshold and M_5m_C0 > M_5m_P1 > 0.000 and H_5m_C0 > H_5m_P1 > 0.0000:
                #             print(f" - It's buy signal for BB_1 Strategy, Model_01A-03-01")
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
                #             print(f' - SCF_15m_01A_03 = {SCF_15m_01A_03} < SCF_15m_01A_03_threshold of {SCF_15m_01A_03_threshold}')
                #             print(f' - Model_01A-03: 15m-MACD cross up 0-line\n')                          

                #     else:
                #         print(" - 15m conditions do not pass for Strategy 1\n") 

                # # Model_01B: 60m-MACD Continue with Gap up (AVGO)
                # elif M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000 and O_60m_C0 > High_60m_P1:

                #     # Model_01B-01: 15m-MACD cross up and gap up (AVGO)
                #     if M_15m_C0 > M_15m_P1 > 0.0000 and H_15m_C0 > 0.0000 and H_15m_P1 < 0.0000 and O_15m_C0 > High_15m_P1:
                        
                #         # Model_01B-01-01: 5m-MACD cross up 0-line and gap up (AVGO 1 Mar 2024)
                #         if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_5m_C0 > H_5m_P1 > 0.0000 and O_5m_C0 > High_5m_P1:
                #             print(f" - It's buy signal for BB_1 Strategy, Model_01B-01-01")
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
                    
                # # Model_01C: 60m-MACD Keep Rising (IBKR 2 Feb, CIEN and FIP 1 Mar 2024)                  
                # elif M_60m_C0 > M_60m_P1 > 0.0000:
                #     print(f" - Checking for Model_01C: 60m_MACD Keep Rising")

                #     # Significant Breakout Factor 60m 
                #     # (CIEN 1 Mar 2024: H_60m_C0 = 0.1482 > H_60m_P1 = 0.0216 --> SBF = 6.86)
                #     # (FIP 1 Mar 2024: H_60m_C0 = 0.0310 > H_60m_P1 = 0.0202 --> SBF = 1.55)
                #     # (IBKR 2 Feb 2024: H_60_C0 = 0.6113 > H_60m_P1 = 0.2449 --> SBF = 2.45)
                #     # (AMG 14 Mar 2024: SBF_60_01C is 0.9 at 15:30 when 15m-MACD Cross Up)
                #     # (PTGX 27-28 Feb 2024: H_60_C0 = 0.0448 > H_60m_P1 = 0.0116 --> SBF = 3.86)
                #     SBF_60m_01C = round(H_60m_C0/H_60m_P1, decimal_point)
                #     SBF_60m_01C_threshold = 1.15

                #     if SBF_60m_01C > SBF_60m_01C_threshold:
                #         print(f' - SBF_60m_01C = {SBF_60m_01C}')                                        
       
                #         # Model_01C-01: 15m-MACD Keep Rising with H > 0 (CIEN 1 Mar 2024)
                #         if M_15m_C0 > M_15m_P1 > 0.0000 and H_15m_C0 > 0.0000:
                #             # Significant Breakout Factor 15m 
                #             # (CIEN 1 Mar 2024 (09:30): H_15m_C0 = 0.0869 > H_15m_P1 = 0.0031 --> SBF = 28.03)
                #             SBF_15m_01C_01 = round(H_15m_C0/H_15m_P1, decimal_point)
                #             SBF_15m_01C_01_threshold = 2.0

                #             if SBF_15m_01C_01 > SBF_15m_01C_01_threshold and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0:

                #                 # Model_01C-01-01: 5m-MACD cross up (CIEN 1 Mar 2024)
                #                 # Significant Cross-up Factor 5m (CIEN 1 Mar 2024 (09:30): H_5m_C0 = 0.0247 > H_5m_P1 = -0.0027 --> SCF = 1014%)
                #                 SCF_5m_01C_01_01 = (H_5m_P1 - H_5m_C0)/H_5m_P1*100            
                #                 SCF_5m_01C_01_01_threshold = 100

                #                 if SCF_5m_01C_01_01 > SCF_5m_01C_01_01_threshold and M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and C_5m_C0 > C_5m_P1 and C_5m_C0 > O_15m_C0:                             
                #                     print(f" - It's buy signal for BB_1 Strategy, Model_01C-01-01")
                #                     print(f' - H_60m_C0 = {H_60m_C0}')
                #                     print(f' - H_60m_P1 = {H_60m_P1}')
                #                     print(f' - SBF_60m = {SBF_60m_01C} > SBF_60m_threshold = {SBF_60m_01C_threshold}')
                #                     print(f' - SBF_15m_01C_01 = {SBF_15m_01C_01} > SBF_15m_01C_01_threshold = {SBF_15m_01C_01_threshold}')                                    
                #                     quantity = calculate_quantity(market_price)
                #                     print(f" - Placing buy order for {symbol} at {market_price}.\n")

                #                     try:
                #                         api.submit_order(
                #                             symbol=symbol,
                #                             side='buy',
                #                             type='market',
                #                             qty=quantity,
                #                             time_in_force='gtc'
                #                         )
                #                     except Exception as e:
                #                         print(f"Could not submit order {e}") 
                #                 else:
                #                     print(" - 5m conditions do not pass for Strategy 1\n")
                #                     print(f' - SCF_5m_01C_01_01 = {SCF_5m_01C_01_01} < SCF_5m_01C_01_01_threshold at {SCF_5m_01C_01_01_threshold}\n') 
                            
                #             else:
                #                 print(f' - SBF_15m_01C_01 = {SBF_15m_01C_01} < SBF_15m_01C_01_threshold of {SBF_15m_01C_01_threshold}\n')

                #         # Model_01C-02: 15m-MACD Countinuous with H < 0 (PTGX 27-28 Feb 2024)
                #         elif M_15m_C0 > M_15m_P1 > 0.0000 and H_15m_C0 < 0.0000:
                #             # Significant Breakout Factor 15m 
                #             # (PTGX 27-28 Feb 2024: H_15m_C0 = -0.0014 > H_15m_P1 = -0.0406 --> SBF = 96%)
                #             SBF_15m_01C_02 = round((H_15m_P1-H_15m_C0)/H_15m_P1*100, decimal_point)
                #             SBF_15m_01C_02_threshold = 50.0
                #             if SBF_15m_01C_02 > SBF_15m_01C_02_threshold and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0:

                #                 # Model_01C-02-01: 5m-MACD cross up at 0-line (PTGX 27-28 Feb 2024)
                #                 # Significant Cross-up Factor 5m (PTGX 27-28 Feb 2024: H_5m_C0 = 0.0205 > H_5m_P1 = -0.0287 --> SCF = 171%)
                #                 SCF_5m_01C_02_01 = (H_5m_P1 - H_5m_C0)/H_5m_P1*100            
                #                 SCF_5m_01C_02_01_threshold = 100
                #                 if SCF_5m_01C_02_01 > SCF_5m_01C_02_01_threshold and M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000:
                #                     print(f" - It's buy signal for BB_1 Strategy, Model_01C-02-01")
                #                     quantity = calculate_quantity(market_price)
                #                     print(f" - Placing buy order for {symbol} at {market_price}.\n")

                #                     try:
                #                         api.submit_order(
                #                             symbol=symbol,
                #                             side='buy',
                #                             type='market',
                #                             qty=quantity,
                #                             time_in_force='gtc'
                #                         )
                #                     except Exception as e:
                #                         print(f"Could not submit order {e}") 
                #                 else:
                #                     print(" - 5m conditions do not pass for Strategy 1\n")
                #                     print(f' - SCF_5m_01C_02_01 = {SCF_5m_01C_02_01} < SCF_5m_01C_02_01_threshold at {SCF_5m_01C_02_01_threshold}\n') 
                #                     print(f' - M_5m_C0 = {M_5m_C0} > 0.0000 and M_5m_P1 = {M_5m_P1} < 0.0000')
                #                     print(f' - H_5m_C0 = {H_5m_C0} > 0.0000 and H_5m_P1 = {H_5m_P1} < 0.0000')
                #             else:
                #                 print(f' - SBF_15m_01C_02 = {SBF_15m_01C_02} < SBF_15m_01C_02_threshold of {SBF_15m_01C_02_threshold}')
                #                 print(f' - Model_01C-02: 15m-MACD Countinuous with H < 0\n')

                #         # Model_01C-03: 15m-MACD Gap Up (IBKR 2 Feb 2024)
                #         elif M_15m_C0 > M_15m_P1 > 0.0000 and O_15m_C0 > High_15m_P1 and C_15m_C0 > O_15m_C0:
                #             # Significant Breakout Factor 15m (IBKR 2 Feb 2024: H_15m_C0 = 0.2964 > H_60m_P1 = 0.0545 --> SBF = 5.44)
                #             SBF_15m_01C_03 = round(H_15m_C0/H_15m_P1, decimal_point)
                #             SBF_15m_01C_03_threshold = 2.0
                #             if SBF_15m_01C_03 > SBF_15m_01C_03_threshold:

                #                 # Model_01C-03-01: 5m-MACD cross up (IBKR 2 Feb 2024)
                #                 # Significant Cross-up Factor 5m 
                #                 # (IBKR 2 Feb 2024: H_5m_C0 = 0.0916 > H_5m_P1 = -0.0296 --> SCF = 409%)
                #                 SCF_5m_01C_03_01 = (H_5m_P1 - H_5m_C0)/H_5m_P1*100            
                #                 SCF_5m_01C_03_01_threshold = 100
                #                 if SCF_5m_01C_03_01 > SCF_5m_01C_03_01_threshold and M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000:
                #                     print(f" - It's buy signal for BB_1 Strategy, Model_01C-03-01")
                #                     quantity = calculate_quantity(market_price)
                #                     print(f" - Placing buy order for {symbol} at {market_price}.\n")

                #                     try:
                #                         api.submit_order(
                #                             symbol=symbol,
                #                             side='buy',
                #                             type='market',
                #                             qty=quantity,
                #                             time_in_force='gtc'
                #                         )
                #                     except Exception as e:
                #                         print(f"Could not submit order {e}")  
                #                 else:
                #                     print(" - 5m conditions do not pass for Strategy 1\n")
                #                     print(f' - SCF_5m_01C_03_01 = {SCF_5m_01C_03_01} < SCF_5m_01C_03_01_threshold at {SCF_5m_01C_03_01_threshold}\n')        
                #             else:
                #                 print(f' - SBF_15m_01C_03 = {SBF_15m_01C_03} < SBF_15m_01C_03_threshold of {SBF_15m_01C_03_threshold}\n')

                #         # Model_01C-04: 15m-MACD Cross Up (DOCN 8 Mar 2024, AMG 14 Mar 2024)
                #         elif H_15m_C0 > 0.0000 and H_15m_P1 < 0.0000 and M_15m_C0 > M_15m_P1 > 0.0000 and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0:

                #             # Significant Cross Up Factor 15m 
                #             # (DOCN 8 Mar 2024: H_15m_C0 = 0.0368 > H_15m_P1 = -0.0181 --> SCF = 303%)
                #             # (AMG 14 Mar 2024: H_15m_C0 = 0.0313 > H_15m_P1 = -0.0108 --> SCF = 389%)
                #             SCF_15m_01C_04 = round((H_15m_P1 - H_15m_C0)/H_15m_P1*100, decimal_point)
                #             SCF_15m_01C_04_threshold = 100.0

                #             if SCF_15m_01C_04 > SCF_15m_01C_04_threshold:
                #                 # Significant Cross-up Factor 5m 
                #                 SCF_5m_01C_04_01 = (H_5m_P1 - H_5m_C0)/H_5m_P1*100            
                #                 SCF_5m_01C_04_01_threshold = 100

                #                 # Significant Cross-up Factor 5m 
                #                 SBF_5m_01C_04_02 = H_5m_C0/H_5m_P1
                #                 SBF_5m_01C_04_02_threshold = 3.0 

                #                 # Model_01C-04-01: 5m-MACD cross up (DOCN 8 Mar 2024)
                #                 # (DOCN 8 Mar 2024: H_5m_C0 = 0.0134 > H_5m_P1 = -0.0127 --> SCF = 205%)
                #                 if SCF_5m_01C_04_01 > SCF_5m_01C_04_01_threshold and H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000:
                #                     print(f" - It's buy signal for BB_1 Strategy, Model_01C-04-01")
                #                     quantity = calculate_quantity(market_price)
                #                     print(f" - Placing buy order for {symbol} at {market_price}.\n")

                #                     try:
                #                         api.submit_order(
                #                             symbol=symbol,
                #                             side='buy',
                #                             type='market',
                #                             qty=quantity,
                #                             time_in_force='gtc'
                #                         )
                #                     except Exception as e:
                #                         print(f"Could not submit order {e}")  

                #                 # Model_01C-04-02: 5m-MACD keep rising (AMG 14 Mar 2024 at 15:40)
                #                 # (AMG 14 Mar 2024 (15:40): H_5m_C0 = 0.0395 > H_5m_P1 = 0.0056 --> SBF = 7.05)
                #                 elif SBF_5m_01C_04_02 > SBF_5m_01C_04_02_threshold and M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > H_5m_P1 > 0.0000 and C_5m_C0 > C_5m_P1 and C_5m_C0 > O_5m_C0:
                #                     print(f" - It's buy signal for BB_1 Strategy, Model_01C-04-02")
                #                     quantity = calculate_quantity(market_price)
                #                     print(f" - Placing buy order for {symbol} at {market_price}.\n")

                #                     try:
                #                         api.submit_order(
                #                             symbol=symbol,
                #                             side='buy',
                #                             type='market',
                #                             qty=quantity,
                #                             time_in_force='gtc'
                #                         )
                #                     except Exception as e:
                #                         print(f"Could not submit order {e}")  
                                
                #                 else:
                #                     print(" - 5m conditions do not pass for Strategy 1\n")
                                           
                #             else:
                #                 print(f' - SCF_15m_01C_04 of {SCF_15m_01C_04} < SCF_5m_01C_04_threshold at {SCF_15m_01C_04_threshold}\n')

                #         # Model_01C-05: 15m-MACD Cruss Up 0-line
                #         # Ongoing
                                
                #         else:
                #             print(" - 15m conditions do not pass for Strategy 1\n")

                #     else:
                #         print(f" - SBF_60m_01C of {SBF_60m_01C} is lower than SBF_60m_01C_threshold {SBF_60m_01C_threshold}\n")
                
                # # Model_01D: 60m_MACD cross up at 0-line
                # elif M_60m_C0 > M_60m_P1 > 0.000 and M_60m_C0 < 0.0100 and H_60m_C0 > 0.000 and H_60m_P1 < 0.0000:
                #     # Significant Cross-up Factor 60m (MMYT 11 Mar 2024: H_60m_C0 = 0.0544 > H_5m_P1 = -0.0255 --> SCF = 313%)
                #     SCF_60m_01D = round((H_60m_P1 - H_60m_C0)/H_60m_P1*100, decimal_point)         
                #     SCF_60m_01D_threshold = 100.0

                #     # Model_01D-01: 15m_MACD cross up 0-line (MMYT 11 Mar 2024: M_15m_C0(13:30) = 0.0293 > M_5m_P1(13:15) = -0.0024)
                #     if SCF_60m_01D > SCF_60m_01D_threshold and M_15m_C0 > 0.0000 and M_15m_P1 < 0.0000 and H_15m_C0 > H_15m_P1 > 0.0000 and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0:
                        
                #         # Model_01D-01-01: 5m-MACD cross up (MMYT 11 Mar 2024: M_5m_C0(13:25) = 0.0064 > M_5m_P1(13:20) = -0.0030)
                #         if M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000:
                #             print(f" - It's buy signal for BB_1 Strategy, Model_01D-01-01")
                #             print(f'H_60m_C0 = {H_60m_C0}')
                #             print(f'H_60m_P1 = {H_60m_P1}')
                #             print(f'SCF_60m = {SCF_60m_01D} > SCF_60m_threshold = {SCF_60m_01D_threshold}')
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


                print(f" - Checking for Model_01E: 60m_MACD cross up 0-line") 

                # Significant Cross-up Factor 60m 
                # (LAB 1 Mar 2024: H_60m_C0(10:30) = 0.0163 > H_60m_P1(11:30) = 0.0063 --> SCF = 2.59)
                # (FRPT 20 Mar 2024: H_60m_C0(13:30) = 0.0499 > H_60m_P1(12:30) = 0.0419 --> SCF = 1.19)
                SCF_60m_01E = round(H_60m_P1/H_60m_P1, decimal_point)         
                SCF_60m_01E_threshold = 1.10
                print(f' - M_60m_C0 = {M_60m_C0} > 0.0000 and M_60m_P1 = {M_60m_P1} < 0.0000')
                print(f' - H_60m_C0 = {H_60m_C0} > H_60m_P1 = {H_60m_P1} > 0.0000')
                print(f' - SCF_60m = {SCF_60m_01E} > SCF_60m_threshold = {SCF_60m_01E_threshold}')

                # Model_01E: 60m_MACD cross up 0-line (LAB 1 Mar (10:30-11:30))
                if M_60m_C0 > 0.0000 and M_60m_P1 < 0.0000 and H_60m_C0 > H_60m_P1 > 0.0000 and SCF_60m_01E > SCF_60m_01E_threshold:

                    print(f" - Checking for Model_01E-01: 15m_MACD Keep Rising") 
                    # Significant Breakout Factor 15m 
                    # (LAB 1 Mar 2024: H_15m_C0(11:30) = 0.0160 > H_15m_P1(11:15) = 0.0129 --> SBF = 1.24)
                    # (FRPT 20 Mar 2024: H_15m_C0(14:15) = 0.0237 > H_15m_P1(14:00) = 0.0121 --> SBF = 1.95 )
                    SBF_15m_01E_01 = round(H_15m_P1/H_15m_P1, decimal_point)         
                    SBF_15m_01E_01_threshold = 1.10
                    print(f' - M_15m_C0 = {M_15m_C0} > M_15m_P1 = {M_15m_P1} > 0.0000')
                    print(f' - H_15m_C0 = {H_15m_C0} > H_15m_P1 = {H_15m_P1} > 0.0000')                    
                    print(f' - SBF_15m = {SBF_15m_01E_01} > SBF_15m_threshold = {SBF_15m_01E_01_threshold}')

                    # Model_01E-01: 15m_MACD Keep Rising (LAB 1 Mar 2024 (11:15-11:30): H_15m_C0(11:30) = 0.0160 > H_5m_P1(11:15) = 0.0129)
                    if  SBF_15m_01E_01 > SBF_15m_01E_01_threshold and M_15m_C0 > M_15m_P1 > 0.0000 and H_15m_C0 > H_15m_P1 > 0.0000 and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0:

                        # Model_01D-01-01: 5m-MACD Keep Rising (LAB 1 Mar 2024: M_5m_C0(11:30) = 0.0302 > M_5m_P1(11:25) = 0.0288)
                        if M_5m_C0 > M_5m_P1 > 0.0000 and H_5m_C0 > H_5m_P1 > 0.0000:
                            print(f" - It's buy signal for BB Strategy, Model_01E-01-01")
                            print(f" - 60m_MACD cross up 0-line (SCF) - 15m_MACD Keep Rising (SBF) - 5m_MACD Keep Rising")
                            print(f' - M_60m_C0 = {H_60m_C0}')
                            print(f' - M_60m_P1 = {H_60m_P1}')
                            print(f' - SCF_60m = {SCF_60m_01E} > SCF_60m_threshold = {SCF_60m_01E_threshold}')
                            print(f' - SBF_15m = {SBF_15m_01E_01} > SBF_15m_threshold = {SBF_15m_01E_01_threshold}')
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

                else:
                    print(" - 60m conditions do not pass for Stratergy 1\n")
            
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

            # Strategy 1 for taking profit 1
            if market_value > (1.025 * cost):    # 0 < H_5m_C0 < H_5m_P1 < H_5m_P2 and H_5m_P2 > H_5m_P3 and M_5m_P2 > 0 and S_5m_P3 > 0:
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

            # Strategy 3 for cutting loss should not greater than 2.5%
            elif market_value < (0.980 * cost):
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
