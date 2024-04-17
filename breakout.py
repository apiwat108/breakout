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

    current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
    current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")

    orders = api.list_orders(status='all', after=current_date)
    existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']
    positions = api.list_positions()
    existing_position_symbols = [position.symbol for position in positions]
    print(f'{current_time}\n')

    # BB Strategy
    for symbol in symbols:
        print(f'{symbol}_{current_time}')

        ticker = yf.Ticker(symbol)

        minute_5_bars = ticker.history(interval='5m',period='5d')
        minute_60_bars = ticker.history(interval='60m',period='1mo')
        day_1_bars = ticker.history(interval='1d',period='3mo')

        ## When running on Linux, activate this part before indicator setting section 

        most_updated_5m_close = minute_5_bars['Close'][-1]
        minute_5_bars.loc[minute_5_bars.index[-2],'Close'] = most_updated_5m_close
        minute_5_bars.drop(index=minute_5_bars.index[-1],axis=0,inplace=True)

        # References
        # https://predictivehacks.com/?all-tips=replace-values-based-on-index-in-pandas-dataframes
        # https://stackoverflow.com/questions/66096734/pandas-df-loc-1-col-sometimes-work-and-sometimes-add-extra-row-with-nan

        most_updated_60m_close = minute_60_bars['Close'][-1]
        minute_60_bars.loc[minute_60_bars.index[-2],'Close'] = most_updated_60m_close
        minute_60_bars.drop(index=minute_60_bars.index[-1],axis=0,inplace=True)

        most_updated_1d_close = day_1_bars['Close'][-1]
        day_1_bars.loc[day_1_bars.index[-2],'Close'] = most_updated_1d_close
        day_1_bars.drop(index=day_1_bars.index[-1],axis=0,inplace=True)

        # Indicator Setting
        macd_60 = minute_60_bars.ta.macd()
        macd_1 = day_1_bars.ta.macd()

        # df = pd.concat([minute_5_bars['Close'], minute_5_bars['Open'], macd_5_bars['MACD_12_26_9'], rsi], axis=1)
        # print(df)

        decimal_point = 4

        # Candle Stick
        # C_60m_C0 = round(minute_60_bars['Close'][-1], decimal_point)
        # O_60m_C0 = round(minute_60_bars['Open'][-1], decimal_point)
        # C_60m_P1 = round(minute_60_bars['Close'][-2], decimal_point)
        # O_60m_P1 = round(minute_60_bars['Open'][-2], decimal_point)

        M_1d_C0 = round(macd_1['MACD_12_26_9'][-1], decimal_point)
        M_1d_P1 = round(macd_1['MACD_12_26_9'][-2], decimal_point)
        H_1d_C0 = round(macd_1['MACDh_12_26_9'][-1], decimal_point)
        H_1d_P1 = round(macd_1['MACDh_12_26_9'][-2], decimal_point)

        M_60m_C0 = round(macd_60['MACD_12_26_9'][-1], decimal_point)
        M_60m_P1 = round(macd_60['MACD_12_26_9'][-2], decimal_point)
        H_60m_C0 = round(macd_60['MACDh_12_26_9'][-1], decimal_point)
        H_60m_P1 = round(macd_60['MACDh_12_26_9'][-2], decimal_point)
        H_60m_P2 = round(macd_60['MACDh_12_26_9'][-3], decimal_point) 

        market_price = round(minute_5_bars['Close'][-1], decimal_point)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:

                # Model_I: 60m-MACD cross up above 0-line and 1d-MACD cross up 0-line
                if M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000: # need SBF
                    
                    # Significant Cross-up Factor 60m 
                    # (AMG 10 Nov 2023: H_60m_C0 = 0.0047 > H_5m_P1 = -0.0673 --> SCF = 107%)
                    SCF_60m_I = round((H_60m_P1 - H_60m_C0)/H_60m_P1*100, decimal_point)      
                    SCF_60m_I_threshold = 50

                    # Keep recoding the proper SCF_60m_threshold
                    if M_1d_C0 > 0.0000 and M_1d_P1 < 0.0000 and H_1d_C0 > H_1d_P1 > 0.0000: 
                        print(f" - It's buy signal for Model I: 60m-MACD cross up above 0-line and 1d-MACD cross up 0-line")
                        print(f" - H_60m_C0 = {H_60m_C0}")
                        print(f" - H_60m_P1 = {H_60m_P1}")
                        print(f" - SCF_60m = {SCF_60m_I} > SCF_60m_threshold = {SCF_60m_I_threshold}")                           
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
                        print(" - Some conditions do not pass for Model I\n")    

                # Model_II: 60m-MACD cross up above 0-line and 1d-MACD cross up Signal above 0-line
                elif M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000:

                    # Significant Cross-up Factor 60m 
                    # (TARS 13 Nov 2023: H_60m_C0 = 0.0065 > H_5m_P1 = -0.0225 --> SCF = 129%)
                    SCF_60m_II = round((H_60m_P1 - H_60m_C0)/H_60m_P1*100, decimal_point)      
                    SCF_60m_II_threshold = 50

                    # Keep recoding the proper SCF_60m_threshold
                    if M_1d_C0 > M_1d_P1 > 0.0000 and H_1d_C0 > 0.0000 and H_1d_P1 < 0.0000:
                        print(f" - It's buy signal for Model II: 60m-MACD cross up above 0-line and 1d-MACD cross up Signal above 0-line")
                        print(f" - H_60m_C0 = {H_60m_C0}")
                        print(f" - H_60m_P1 = {H_60m_P1}")
                        print(f" - SCF_60m = {SCF_60m_II} > SCF_60m_threshold = {SCF_60m_II_threshold}")   
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
                        print(" - Some conditions do not pass for Model II\n")  

                # Model_III: 60m-MACD cross up 0-line and 1d-MACD above Signal and 0-line             
                elif M_60m_C0 > 0.0000 and M_60m_P1 < 0.0000 and H_60m_C0 > H_60m_P1 > 0.0000:
                    
                    # Significant Cross-up Factor 60m 
                    # (SA 1 Mar 2024: M_60m_C0 = 0.0020 > M_60m_P1 = -0.0289 --> SCF = 107%)
                    SCF_60m_III = round((M_60m_P1 - M_60m_C0)/M_60m_P1*100, decimal_point)      
                    SCF_60m_III_threshold = 50

                    # Keep recoding the proper SCF_60m_threshold
                    if M_1d_C0 > M_1d_P1 > 0.0000 and H_1d_C0 > 0.0000:
                        print(f" - It's buy signal for Model III: 60m-MACD cross up 0-line and 1d-MACD above Signal and 0-line")
                        print(f" - M_60m_C0 = {M_60m_C0}")
                        print(f" - M_60m_P1 = {M_60m_P1}")
                        print(f" - SCF_60m = {SCF_60m_III} > SCF_60m_threshold = {SCF_60m_III_threshold}")  
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
                        print(" - Some conditions do not pass for Model III\n")  

                # Model_IV: 60m-MACD keep rising and 1d-MACD cross up 0-line             
                elif M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > H_60m_P1 > 0.0000:

                    # Check 1d condition
                    if M_1d_C0 > 0.0000 and M_1d_P1 < 0.0000 and H_1d_C0 > 0.0000:
                        print(f" - It's buy signal for Model IV: 60m-MACD keep rising and 1d-MACD cross up 0-line")
                        print(f" - M_1d_C0 = {M_1d_C0} > M_1d_P1 = {M_1d_P1}")  
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
                        print(" - Some conditions do not pass for Model IV\n")  

                # Model_V: 60m-MACD keep rising and 1d-MACD cross up Signal above 0-line             
                elif M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > H_60m_P1 > 0.0000:

                    # Check 1d condition
                    if M_1d_C0 > M_1d_P1 > 0.0000 and H_1d_C0 > 0.0000 and H_1d_P1 < 0.0000:
                        print(f" - It's buy signal for Model V: 60m-MACD keep rising and 1d-MACD cross up Signal above 0-line")
                        print(f" - H_1d_C0 = {H_1d_C0} > H_1d_P1 = {H_1d_P1}")  
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
                        print(" - Some conditions do not pass for Model IV\n")  

                else:
                    print(" - 60m conditions do not pass for All Models\n")
            
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
            if market_value > (1.10 * cost):
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
            elif market_price < EMA_10d and market_value < (0.980 * cost):
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
