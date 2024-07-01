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

# Define the trailing stop percentage
TRAILING_STOP_PERCENTAGE = 0.02  # 1%

# Dictionary to store the list of high prices of each 5m candlestick for each symbol
high_prices = {}

# Function to place sell order
def place_sell_order(symbol, quantity):
    try:
        api.submit_order(
            symbol=symbol,
            side='sell',
            type='market',
            qty=quantity,
            time_in_force='gtc'
        )
        print(f" - Placing sell order for {symbol} at {market_price}.\n")
    except Exception as e:
        print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---\n")

# Function to place buy order
def place_buy_order(symbol, quantity):
    try:
        api.submit_order(
            symbol=symbol,
            side='buy',
            type='market',
            qty=quantity,
            time_in_force='gtc'
        )
        print(f" - Placing buy order for {symbol} at {market_price}.\n")
    except Exception as e:
        print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---\n") 

if clock.is_open:

    symbols_5MX0_AB = config.BREAKOUT_SYMBOLS_5MX0_AB
    # symbols_5MX0_BB = config.BREAKOUT_SYMBOLS_5MX0_BB

    current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
    current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")

    orders = api.list_orders(status='all', after=current_date)
    existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']
    positions = api.list_positions()
    existing_position_symbols = [position.symbol for position in positions]
    print(f'{current_time}\n')

    # Breakout Strategy Model-5MX0-AB
    for symbol in symbols_5MX0_AB:
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

        ema_60 = minute_60_bars['Close'].ewm(span=10, adjust=False).mean()

        # df = pd.concat([minute_5_bars['Close'], minute_5_bars['Open'], macd_5_bars['MACD_12_26_9'], rsi], axis=1)
        # print(df)

        decimal_point = 4
        decimal_point_rsi = 2
        decimal_point_ema = 2

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
        E_60m_C0 = round(ema_60[-1], decimal_point_ema)
        E_60m_P1 = round(ema_60[-2], decimal_point_ema)
        H_60m_Limit = -0.0030

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
        RSI_min = 55.00
        RSI_max = 75.00

        Vol_5m_C0 = minute_5_bars['Volume'][-1]
        Vol_threshold = 900

        market_price = round(minute_5_bars['Close'][-1], decimal_point)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:

                # Entry Position 0: 5MX0
                if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_5m_C0 > 0.0000 and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit and Vol_5m_C0 > Vol_threshold:
                    # Add volume condition to avoid false 5MX0 due to 5m low volatility
                    print(f" - It's buy signal for Entry Position 0: 5MX0")         
                    quantity = calculate_quantity(market_price)
                    place_buy_order(symbol, quantity)

                # # Entry Position 1: 60MX0
                # elif M_60m_C0 > 0.0000 and M_60m_P1 < 0.0000 and H_60m_C0 > 0.0000:
                #     # (SA 1 Mar 2024)

                #     # Significant Cross-up Factor 60m PROFIT (ARMK 17 Jun 2024: H_60m_C0 = 0.0119 > H_60m_P1 = -0.0082 --> SCF = 245%)
                #     # Significant Cross-up Factor 60m LOSS (ENVX 18 Jun 2024: H_60m_C0 = 0.0068 > H_60m_P1 = -0.0145 --> SCF = 147%)                    
                #     SCF_60MX0 = round((H_60m_P1 - H_60m_C0)/H_60m_P1*100, decimal_point)         
                #     SCF_60MX0_threshold = 150.0
                #     print(f" - SCF_60MX0 = {SCF_60MX0} compare to SCF_60MX0_threshold = {SCF_60MX0_threshold}\n")

                #     # Check 1D condition
                #     if M_1d_C0 > 0.0000 and H_1d_C0 > 0.0000 and SCF_60MX0 > SCF_60MX0_threshold: 
                #         print(f" - It's buy signal for Entry Position 1: 60MX0")         
                #         quantity = calculate_quantity(market_price)
                #         place_buy_order(symbol, quantity)

                #     else:
                #         print(f" - 1D Condition False for Entry Position 1: 60MX0\n")

                # # Entry Position 2: 60MXU
                # elif H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000 and M_60m_C0 > 0.0000:
                #     # (TARS 13 Dec 2023)

                #     # Significant Cross-up Factor 60m (MMYT 11 Mar 2024: H_60m_C0 = 0.0544 > H_60m_P1 = -0.0255 --> SCF = 313%)
                #     # Significant Cross-up Factor 60m (NSA 18 Jun 2024: H_60m_C0 = 0.0100 > H_60m_P1 = -0.0169 --> SCF = 159%)                     
                #     SCF_60MXU = round((H_60m_P1 - H_60m_C0)/H_60m_P1*100, decimal_point)         
                #     SCF_60MXU_threshold = 150.0
                #     print(f" - SCF_60MXU = {SCF_60MXU} compare to SCF_60MXU_threshold = {SCF_60MXU_threshold}\n")

                #     # Check 1D condition
                #     if M_1d_C0 > 0.0000 and H_1d_C0 > 0.0000 and SCF_60MXU > SCF_60MXU_threshold: 
                #         print(f" - It's buy signal for Entry Position 2: 60MXU")         
                #         quantity = calculate_quantity(market_price)
                #         place_buy_order(symbol, quantity)

                #     else:
                #         print(f" - 1D Condition False for Entry Position 2: 60MXU\n")                        

                # # Entry Position 3: 15MX0
                # elif M_15m_C0 > 0.0000 and M_15m_P1 < 0.0000:
                    
                #     # Sample
                #     # (AMG 14 Nov 2023 09:30)

                #     # Add M_60m_C0 > M_60m_P1 to avoid weak 15MX0
                #     # (FPI 20 Jun 2024 14:00, which M_60m_C0 < M_60m_P1, then the 15MX0 is weak)
                #     # compared to FPI 17 Jun 2024 13:00, which M_60m_C0 < M_60m_P1 and the 15MX0 looks strong to take the profit

                #     # Add M_60m_C0 > 0.0000 to avoid another weak 15MX0
                #     # (RPAY 21 Jun 2024 10:15)
                #     # Check 1D and 60M conditions

                #     # Add H_60m_Limit_15MX0 to avoid another weak 15MX0
                #     # (CNK 24 Jun 2024 (09:30) PROFIT H_60m_C0 = -0.0133)
                #     # (ESI 24 Jun 2024 (09:30) LOSS H_60m_C0 = -0.0823)
                #     H_60m_Limit_15MX0 = -0.0500
                #     if M_1d_C0 > 0.0000 and H_1d_C0 > 0.0000 and M_60m_C0 > M_60m_P1 and M_60m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit_15MX0: 
                #         print(f" - It's buy signal for Entry Position 3: 15MX0")         
                #         quantity = calculate_quantity(market_price)
                #         place_buy_order(symbol, quantity)

                #     else:
                #         print(f" - 1D Condition False for Entry Position 3: 15MX0\n")                        

                # # Entry Position 4: 5MX0+15MX0
                # elif M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and M_15m_C0 > 0.0000 and M_15m_P1 < 0.0000:
                    
                #     # Sample
                #     # (FPI 13 Jun 2024 09:30)
                #     # Check 1D and 60M conditions
                #     if M_1d_C0 > 0.0000 and H_1d_C0 > 0.0000 and M_60m_C0 > 0.0000 and H_60m_C0 > 0.0000: 
                #         print(f" - It's buy signal for Entry Position 4: 5MX0+15MX0")         
                #         quantity = calculate_quantity(market_price)
                #         place_buy_order(symbol, quantity)

                #     else:
                #         print(f" - 1D or 60m Conditions False for Entry Position 4: 5MX0+15MX0\n")                        

                # Model_XX_END
                else:
                    print(" - No conditions fit for all three Entry Positions\n")
            
            else:
                print(f' - The order of stock {symbol} is placed\n')

        elif symbol in existing_position_symbols:
            try:
                print(f" - Already in the position")
                position = api.get_position(symbol)
                quantity = position.qty
                entry_price = float(position.avg_entry_price)
                entry_date = position.lastday  # get the entry date
                market_value = abs(float(position.market_value))
                cost = abs(float(position.cost_basis))

                # Convert the entry date to the required format
                entry_date = datetime.strptime(entry_date, "%Y-%m-%d").replace(tzinfo=pytz.timezone('America/New_York'))
                print(f" - Entry DATE-TIME for {symbol} is {entry_date}")

                # Get new 5-minute bars since entry date-time
                new_bars = ticker.history(start=entry_date, interval='5m')
                high_prices = new_bars['High'].tolist()
                print(f" - High prices since entry: {high_prices}")

                day_bars = ticker.history(interval='1d',period='1mo')
                EMA_10d_bars = day_bars['Close'].ewm(span=10, adjust=False).mean()
                EMA_10d = EMA_10d_bars[-1]         

                # Calculate the highest price in the list
                highest_price = max(high_prices)
                print(f" - The highest price for {symbol} so far is {highest_price}")

                # Calculate trailing stop price
                trailing_stop_price = highest_price * (1 - TRAILING_STOP_PERCENTAGE)

                # Check if current market price is below trailing stop price
                if market_price <= trailing_stop_price and market_value > (1.0075 * cost):
                    print(f" - Trailing stop hit. Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Exit Position 0: Taking profit at least 0.75%
                elif market_value > (1.0075 * cost):
                    print(f" - It's taking-profit signal with min of 0.75% profit.")
                    place_sell_order(symbol, quantity)

                # # Exit Position 1 If Entry Position 1: 60MX0 False
                # elif M_60m_C0 < 0.0000:
                #     print(f" - It's cut-loss signal Entry Positon 1: 60MX0 False.")
                #     place_sell_order(symbol, quantity)   

                # # Exit Position 2 If Entry Position 2: 60MXU False
                # elif H_60m_C0 < 0.0000 and H_60m_P1 < 0.0000 and H_15m_C0 < 0.0000:
                #     # Add H_15m_P1 > 0.0000 to avoid conflict with Entry Position 3
                #     # (AUPH 20 Jun 2024: 13:35 Entry Position 3: 15MX0)
                #     # (13:40 Exit with 60MXU False)

                #     # Change H_15m_P1 > 0.0000 to H_15m_C0 < 0.0000 
                #     # Avoid high fluctuation at the early hour
                #     # (AUPH 21 Jun 2024 09:40)
                #     # Avoid conflict with Entry Position 3 for the 2nd case
                #     # (EVCM 21 Jun 2024 11:10)
                #     print(f" - It's cut-loss signal Entry Positon 2: 60MXU False.")
                #     place_sell_order(symbol, quantity)  

                # # Exit Position 3
                # # Strategy 1 for taking profit at least 1.0%
                # # Avoid exit to early without a chance to take profit (HRZN )
                # # Consider to add 15m condition like the BB case (RPAY 11 Jun 2024)
                # elif market_value > (1.005 * cost) and M_5m_C0 < M_5m_P1 and 0.0000 < H_5m_C0 < H_5m_P1 and M_15m_C0 < M_15m_P1 and H_15m_C0 < H_15m_P1:
                #     print(f" - It's taking-profit signal with min of 1% profit.")
                #     place_sell_order(symbol, quantity)

                # Strategy 2 for cutting loss at 5%
                elif market_price < EMA_10d and market_value < (0.95 * cost):
                    print(f" - It's cut-loss signal with Strategy 2.")
                    place_sell_order(symbol, quantity)

                # Strategy 3 for cutting loss should not greater than 5%
                elif market_value < (0.95 * cost):
                    print(f" - It's cut-loss signal with Strategy 3.")
                    place_sell_order(symbol, quantity)

                # Strategy 4 for cutting loss when signal and price are triggered
                elif market_price < EMA_10d and H_1d_C0 < 0.0000:
                    print(f" - It's cut-loss signal with Strategy 4.")
                    place_sell_order(symbol, quantity)            

            except Exception as e:
                print(f"The order may not be filled")

            else:
                print(" - No sell signal yet\n")

        else: 
            print(" - It's already been traded for today.\n")

    # # Breakout Strategy Model-5MX0-BB
    # for symbol in symbols_5MX0_BB:
    #     print(f'{symbol}_{current_time}\n')

    #     ticker = yf.Ticker(symbol)

    #     minute_5_bars = ticker.history(interval='5m',period='5d')
    #     minute_15_bars = ticker.history(interval='15m',period='5d')
    #     minute_60_bars = ticker.history(interval='60m',period='1mo')
    #     day_1_bars = ticker.history(interval='1d',period='6mo')

    #     ## When running on Linux, activate this part before indicator setting section 

    #     most_updated_5m_close = minute_5_bars['Close'][-1]
    #     minute_5_bars.loc[minute_5_bars.index[-2],'Close'] = most_updated_5m_close
    #     minute_5_bars.drop(index=minute_5_bars.index[-1],axis=0,inplace=True)

    #     # References
    #     # https://predictivehacks.com/?all-tips=replace-values-based-on-index-in-pandas-dataframes
    #     # https://stackoverflow.com/questions/66096734/pandas-df-loc-1-col-sometimes-work-and-sometimes-add-extra-row-with-nan

    #     most_updated_15m_close = minute_15_bars['Close'][-1]
    #     minute_15_bars.loc[minute_15_bars.index[-2],'Close'] = most_updated_15m_close
    #     minute_15_bars.drop(index=minute_15_bars.index[-1],axis=0,inplace=True)

    #     most_updated_60m_close = minute_60_bars['Close'][-1]
    #     minute_60_bars.loc[minute_60_bars.index[-2],'Close'] = most_updated_60m_close
    #     minute_60_bars.drop(index=minute_60_bars.index[-1],axis=0,inplace=True)

    #     # most_updated_1d_close = day_1_bars['Close'][-1]
    #     # day_1_bars.loc[day_1_bars.index[-2],'Close'] = most_updated_1d_close
    #     # day_1_bars.drop(index=day_1_bars.index[-1],axis=0,inplace=True)

    #     # Indicator Setting
    #     macd_5 = minute_5_bars.ta.macd()
    #     macd_15 = minute_15_bars.ta.macd()
    #     macd_60 = minute_60_bars.ta.macd()
    #     macd_1 = day_1_bars.ta.macd()

    #     rsi_5 = minute_5_bars.ta.rsi()
    #     rsi_15 = minute_15_bars.ta.rsi()
    #     rsi_60 = minute_60_bars.ta.rsi()

    #     ema_60 = minute_60_bars['Close'].ewm(span=10, adjust=False).mean()
    #     ema_1 = day_1_bars['Close'].ewm(span=10, adjust=False).mean()

    #     # df = pd.concat([minute_5_bars['Close'], minute_5_bars['Open'], macd_5_bars['MACD_12_26_9'], rsi], axis=1)
    #     # print(df)

    #     decimal_point = 4
    #     decimal_point_rsi = 2
    #     decimal_point_ema = 2

    #     # Candle Stick
    #     C_60m_C0 = round(minute_60_bars['Close'][-1], decimal_point)
    #     C_60m_P1 = round(minute_60_bars['Close'][-2], decimal_point)
    #     C_60m_P2 = round(minute_60_bars['Close'][-3], decimal_point)

    #     C_1d_C0 = round(day_1_bars['Close'][-1], decimal_point)
    #     C_1d_P1 = round(day_1_bars['Close'][-2], decimal_point)
    #     C_1d_P2 = round(day_1_bars['Close'][-3], decimal_point)

    #     M_1d_C0 = round(macd_1['MACD_12_26_9'][-1], decimal_point)
    #     M_1d_P1 = round(macd_1['MACD_12_26_9'][-2], decimal_point)
    #     H_1d_C0 = round(macd_1['MACDh_12_26_9'][-1], decimal_point)
    #     H_1d_P1 = round(macd_1['MACDh_12_26_9'][-2], decimal_point)
    #     E_1d_C0 = round(ema_1[-1], decimal_point_ema)
    #     E_1d_P1 = round(ema_1[-2], decimal_point_ema)
    #     V_1d_C0 = day_1_bars['Volume'][-1]
    #     volume_values = day_1_bars['Volume'][-12:-2]
    #     volume_values_arr = volume_values.values
    #     V_1d_P1_P10 = volume_values_arr.tolist()

    #     M_60m_C0 = round(macd_60['MACD_12_26_9'][-1], decimal_point)
    #     M_60m_P1 = round(macd_60['MACD_12_26_9'][-2], decimal_point)
    #     H_60m_C0 = round(macd_60['MACDh_12_26_9'][-1], decimal_point)
    #     H_60m_P1 = round(macd_60['MACDh_12_26_9'][-2], decimal_point)
    #     H_60m_P2 = round(macd_60['MACDh_12_26_9'][-3], decimal_point)
    #     S_60m_C0 = round(macd_60['MACDs_12_26_9'][-1], decimal_point)
    #     S_60m_P1 = round(macd_60['MACDs_12_26_9'][-2], decimal_point)
    #     S_60m_P2 = round(macd_60['MACDs_12_26_9'][-3], decimal_point)
    #     E_60m_C0 = round(ema_60[-1], decimal_point_ema)
    #     E_60m_P1 = round(ema_60[-2], decimal_point_ema)
    #     H_60m_Limit = -0.0050

    #     M_15m_C0 = round(macd_15['MACD_12_26_9'][-1], decimal_point)
    #     M_15m_P1 = round(macd_15['MACD_12_26_9'][-2], decimal_point)
    #     H_15m_C0 = round(macd_15['MACDh_12_26_9'][-1], decimal_point)
    #     H_15m_P1 = round(macd_15['MACDh_12_26_9'][-2], decimal_point)

    #     M_5m_C0 = round(macd_5['MACD_12_26_9'][-1], decimal_point)
    #     M_5m_P1 = round(macd_5['MACD_12_26_9'][-2], decimal_point)
    #     H_5m_C0 = round(macd_5['MACDh_12_26_9'][-1], decimal_point)
    #     H_5m_P1 = round(macd_5['MACDh_12_26_9'][-2], decimal_point)

    #     RSI_5m_C0 = round(rsi_5[-1], decimal_point_rsi)
    #     RSI_15m_C0 = round(rsi_15[-1], decimal_point_rsi)
    #     RSI_60m_C0 = round(rsi_60[-1], decimal_point_rsi)
    #     RSI_min = 55.00
    #     RSI_max = 75.00

    #     Vol_5m_C0 = minute_5_bars['Volume'][-1]
    #     Vol_threshold = 1000

    #     market_price = round(minute_5_bars['Close'][-1], decimal_point)

    #     if symbol not in existing_position_symbols:

    #         if symbol not in existing_order_symbols:

    #             # Check 1DVB
    #             if V_1d_C0 > max(V_1d_P1_P10):
    #                 print(f" - It's Volume Break")
    #                 print(f" - Check parameters to develop the trading model")
    #                 print(f" - H_1d_P1 = {H_1d_P1} < 0.0000 and H_1d_C0 = {H_1d_C0} > 0.0000 and C_1d_C0 = {C_1d_C0} > E_1d_C0 = {E_1d_C0}")

    #                 # Check 1DXU and 1DPXE
    #                 if H_1d_P1 < 0.0000 and H_1d_C0 > 0.0000 and C_1d_C0 > E_1d_C0:
    #                     print(f" - MACD cross up Signal")
    #                     SBF_5m = H_5m_C0/H_5m_P1
    #                     SBF_5m_threshold = 1.5   

    #                     # Check 60-15-5-Minute Condition to Enter (5MX0)
    #                     if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

    #                         # Add H_15m_C0 > 0.0000 to avoid weak 5MX0
    #                         # (CLOV 21 Jun 2024: 14:10)
    #                         # Check RSI and volume
    #                         if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
    #                             print(f" - It's buy signal for Model 5MX0_MACD cross up Signal")         
    #                             quantity = calculate_quantity(market_price)
    #                             print(f" - Placing buy order for {symbol} at {market_price}.")
    #                             place_buy_order(symbol, quantity)
    #                         else:
    #                             print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

    #                     # Check 60-15-5-Minute Condition to Enter (5MXU)
    #                     # (MUX 28 May 2024: 11:05)
    #                     elif H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and M_15m_C0 > M_15m_P1 > 0.0000 and H_15m_C0 > H_15m_P1 > 0.0000 and M_60m_C0 > M_60m_P1 > 0.0000 and H_60m_C0 > H_60m_P1 > 0.0000:

    #                         # Check RSI and volume
    #                         if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
    #                             print(f" - It's buy signal for Model 5MXU_MACD cross up Signal")         
    #                             quantity = calculate_quantity(market_price)
    #                             place_buy_order(symbol, quantity)
    #                         else:
    #                             print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

    #                     # Check 60-15-5-Minute Condition to Enter (5MXU)
    #                     # (VZ 30 May 2024)
    #                     elif H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and M_15m_C0 > 0.0000 and H_15m_C0 > 0.0000 and M_60m_C0 > M_60m_P1 and H_60m_C0 > H_60m_P1 > H_60m_Limit:
    #                         print(f" - It's buy signal for Model 5MXU_MACD cross up Signal (VZ)")         
    #                         quantity = calculate_quantity(market_price)
    #                         place_buy_order(symbol, quantity)

    #                     # Check 60-15-5-Minute Condition to Enter (5MKR)
    #                     elif H_5m_C0 > H_5m_P1 > 0.0000 and SBF_5m > SBF_5m_threshold and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

    #                         # Check RSI and volume
    #                         if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
    #                             print(f" - It's buy signal for Model 5MKR_MACD cross up Signal")         
    #                             quantity = calculate_quantity(market_price)
    #                             place_buy_order(symbol, quantity)
    #                         else:
    #                             print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

    #                     # No 60-15-5-Minute Condition to Enter
    #                     else:
    #                         print(f" - Please check one of 60-15-5-Minute conditions: H_60m_C0 = {H_60m_C0}, M_15m_C0 = {M_15m_C0}, M_5m_C0 = {M_5m_C0} and M_5m_P1 = {M_5m_P1}")

    #                 # Check 1DPXE
    #                 elif C_1d_C0 > E_1d_C0 and C_1d_P1 < E_1d_P1:
    #                     print(f" - Price cross up EMA-10")
    #                     SBF_5m = H_5m_C0/H_5m_P1
    #                     SBF_5m_threshold = 1.5   

    #                     # Check 60-15-5-Minute Condition to Enter (5MX0)
    #                     # (TGS 13 Jun 2024 13:35)
    #                     if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and M_15m_C0 > 0.0000 and M_60m_C0 > M_60m_P1 and H_60m_C0 > H_60m_Limit:

    #                         # Check RSI and volume
    #                         if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
    #                             print(f" - It's buy signal for Model 5MX0_1DPXE")         
    #                             quantity = calculate_quantity(market_price)
    #                             place_buy_order(symbol, quantity)
    #                         else:
    #                             print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

    #                     # Check 60-15-5-Minute Condition to Enter (5MXU)
    #                     elif H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and H_15m_P1 < H_15m_C0 < 0.0000 and H_60m_C0 > H_60m_Limit:

    #                         # Check RSI and volume
    #                         if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
    #                             print(f" - It's buy signal for Model 5MXU_1DPXE")         
    #                             quantity = calculate_quantity(market_price)
    #                             place_buy_order(symbol, quantity)
    #                         else:
    #                             print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

    #                     # Check 60-15-5-Minute Condition to Enter (5MXU)
    #                     # (VZ 30 May 2024)
    #                     elif H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and M_15m_C0 > 0.0000 and H_15m_C0 > 0.0000 and M_60m_C0 > M_60m_P1 and H_60m_C0 > H_60m_P1 > H_60m_Limit:
    #                         print(f" - It's buy signal for Model 5MXU_1DPXE")         
    #                         quantity = calculate_quantity(market_price)
    #                         place_buy_order(symbol, quantity)

    #                     # Check 60-15-5-Minute Condition to Enter (5MKR)
    #                     elif H_5m_C0 > H_5m_P1 > 0.0000 and SBF_5m > SBF_5m_threshold and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

    #                         # Check RSI and volume
    #                         if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
    #                             print(f" - It's buy signal for Model 5MKR_1DPXE")         
    #                             quantity = calculate_quantity(market_price)
    #                             place_buy_order(symbol, quantity)
    #                         else:
    #                             print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

    #                     # No 60-15-5-Minute Condition to Enter
    #                     else:
    #                         print(f" - Please check one of 60-15-5-Minute conditions: H_60m_C0 = {H_60m_C0}, M_15m_C0 = {M_15m_C0}, M_5m_C0 = {M_5m_C0} and M_5m_P1 = {M_5m_P1}")
       
    #                 # No 1DXU or 1DPXE
    #                 else:
    #                     print(f" - Waiting for 1DXU or 1DPXE signale\n")

    #             # No 1DVB
    #             else:
    #                 print(f" - Waiting for VB\n")
            
    #         else:
    #             print(f' - The order of stock {symbol} is placed\n')

    #     elif symbol in existing_position_symbols:
    #         try:
    #             print(f" - Already in the position")
    #             position = api.get_position(symbol)
    #             quantity = position.qty
    #             entry_price = float(position.avg_entry_price)
    #             market_value = abs(float(position.market_value))
    #             cost = abs(float(position.cost_basis))

    #             day_bars = ticker.history(interval='1d',period='1mo')
    #             EMA_10d_bars = day_bars['Close'].ewm(span=10, adjust=False).mean()
    #             EMA_10d = EMA_10d_bars[-1]

    #             # Initialize or update the list of high prices for trailing stop
    #             if symbol not in high_prices:
    #                 high_prices[symbol] = list(minute_5_bars['High'][-1:])
    #                 print(f" - Initializing high_prices for {symbol}")

    #             high_prices[symbol].append(minute_5_bars['High'][-1])
    #             print(f" - Updated high_prices for {symbol}: {high_prices[symbol]}")

    #             # Calculate the highest price in the list
    #             highest_price = round(max(high_prices[symbol]), decimal_point)
    #             print(f" - The highest price for {symbol} so far is {highest_price}")

    #             # Calculate trailing stop price
    #             trailing_stop_price = highest_price * (1 - TRAILING_STOP_PERCENTAGE)

    #             # Check if current market price is below trailing stop price
    #             if market_price <= trailing_stop_price:
    #                 print(f" - Trailing stop hit. Placing sell order for {symbol} at {market_price}.\n")
    #                 place_sell_order(symbol, quantity)

    #             # Exit Position 0: Taking profit at least 0.75%
    #             elif market_value > (1.0075 * cost):
    #                 print(f" - It's taking-profit signal with min of 0.75% profit.")
    #                 place_sell_order(symbol, quantity)

    #             # Strategy 1 for taking profit at least 1.0% with open up more profit in 5m TF
    #             # Some cases not reaching 1.0% then it's change to down size and could lead to 7.5% cut loss
    #             # Then try to adjust by adding 15m condition in case that the profit is below 1.0% and still open up more profit option.
    #             # Another option is these would be valid when it happens on the area where M_60m_C0 < M_60m_P1 and H_60m_C0 < H_60m_P1
    #             # (CDMO 6 Jun 2024)
    #             # Example case for not reaching 1.0%
    #             # (VIRT 10 Jun 2024 12:15-12:30 
    #             # 5m TF --> 12:30-12:35 H_5m_C0 = -0.0033 < H_5m_P1 = 0.0032 and H_5m_C0 < 0.0000
    #             # 15m TF --> M_15m_C0 0.5852 < M_15m_P1 = 0.5872)
    #             # the condition is adjusted from 0.0000 < H_5m_C0 < H_5m_P1 to H_5m_C0 < H_5m_P1
    #             elif market_value > (1.005 * cost) and M_5m_C0 < M_5m_P1 and H_5m_C0 < H_5m_P1 and M_15m_C0 < M_15m_P1 and H_15m_C0 < H_15m_P1 and M_60m_C0 < M_60m_P1 and H_60m_C0 < H_60m_P1:
    #                 print(f" - It's exit signal in 5m TF.")
    #                 place_sell_order(symbol, quantity)

    #             # Strategy 1 for taking profit at least 1.0%
    #             # Avoid exit to early without a chance to take profit (HRZN 3 Jun 2024 )
    #             elif market_value > (1.005 * cost) and M_5m_C0 < M_5m_P1 and 0.0000 < H_5m_C0 < H_5m_P1 and M_15m_C0 < M_15m_P1 and H_15m_C0 < H_15m_P1:
    #                 # (RKLB 18 Jun 2024: 15:15 (4.93) instead of 14:50 (4.89))
    #                 # (Add M_15m_C0 < M_15m_P1 and H_15m_C0 < H_15m_P1)
    #                 print(f" - It's taking-profit signal with min of 1% profit.")
    #                 place_sell_order(symbol, quantity)

    #             # Strategy 2 for cutting loss at 5%
    #             elif market_price < EMA_10d and market_value < (0.95 * cost):
    #                 print(f" - It's cut-loss signal at -5% and C_1D < EMA_10.")
    #                 place_sell_order(symbol, quantity)

    #             # Strategy 3 for cutting loss should not greater than 5%
    #             elif market_value < (0.95 * cost):
    #                 print(f" - It's cut-loss signal at -5%.")
    #                 place_sell_order(symbol, quantity)

    #             # Stratergy END for exit position
    #             else:
    #                 print(" - No sell signal yet\n")

    #         except Exception as e:
    #             print(f"The order may not be filled")

    #     else: 
    #         print(" - It's already been traded for today.\n")

else:
    print(f"The market is closed")