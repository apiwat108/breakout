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
TRAILING_STOP_PERCENTAGE = 0.01  # 1%

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
        print(f" - Placing sell order for {symbol}.\n")
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
        print(f" - Placing buy order for {symbol}.\n")
    except Exception as e:
        print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---\n") 

if clock.is_open:

    symbols_5MX0_AB = config.BREAKOUT_SYMBOLS_5MX0_AB
    symbols_5MX0_BB = config.BREAKOUT_SYMBOLS_5MX0_BB

    current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
    current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")

    orders = api.list_orders(status='all', after=current_date)
    existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']
    positions = api.list_positions()
    existing_position_symbols = [position.symbol for position in positions]
    print(f'{current_time}\n')

    # Track highest price for trailing stop
    highest_prices = {}

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
        Vol_threshold = 1000

        market_price = round(minute_5_bars['Close'][-1], decimal_point)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:

                # Model_5MX0: 
                if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

                    # Check RSI and volume
                    if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and RSI_min < RSI_60m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                        print(f" - It's buy signal for Model 5MX0")         
                        quantity = calculate_quantity(market_price)
                        print(f" - Placing buy order for {symbol} at {market_price}.")
                        place_buy_order(symbol, quantity)

                    else:
                        print(f" - RSI is overbought at RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for Models 5MX0\n")

                # Model_5MX0_END
                else:
                    print(" - One of the conditions do not pass for Models 5MX0\n")
            
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

                # Update the highest price for trailing stop
                if symbol not in highest_prices:
                    highest_prices[symbol] = market_price

                if market_price > highest_prices[symbol]:
                    highest_prices[symbol] = market_price

                # Calculate trailing stop price
                trailing_stop_price = highest_prices[symbol] * (1 - TRAILING_STOP_PERCENTAGE)

                # Check if current market price is below trailing stop price
                if market_price <= trailing_stop_price:
                    print(f" - Trailing stop hit. Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Strategy 1 for taking profit at least 1.0%
                elif market_value > (1.01 * cost) and M_5m_C0 < M_5m_P1 and 0.0000 < H_5m_C0 < H_5m_P1:
                    print(f" - It's taking-profit signal.")
                    print(f" - Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Strategy 2 for cutting loss at 7.5%
                elif market_price < EMA_10d and market_value < (0.925 * cost):
                    print(f" - It's cut-loss signal.")
                    print(f" - Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Strategy 3 for cutting loss should not greater than 7.5%
                elif market_value < (0.9250 * cost):
                    print(f" - It's cut-loss signal.")
                    print(f" - Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Strategy 4 for cutting loss when signal and price are triggered
                elif market_price < EMA_10d and H_1d_C0 < 0.0000:
                    print(f" - It's cut-loss signal.")
                    print(f" - Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)            
            
            except Exception as e:
                print(f"The order may not be filled")

            else:
                print(" - No sell signal yet\n")

        else: 
            print(" - It's already been traded for today.\n")

    # Breakout Strategy Model-5MX0-BB
    for symbol in symbols_5MX0_BB:
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
        ema_1 = day_1_bars['Close'].ewm(span=10, adjust=False).mean()

        # df = pd.concat([minute_5_bars['Close'], minute_5_bars['Open'], macd_5_bars['MACD_12_26_9'], rsi], axis=1)
        # print(df)

        decimal_point = 4
        decimal_point_rsi = 2
        decimal_point_ema = 2

        # Candle Stick
        C_60m_C0 = round(minute_60_bars['Close'][-1], decimal_point)
        C_60m_P1 = round(minute_60_bars['Close'][-2], decimal_point)
        C_60m_P2 = round(minute_60_bars['Close'][-3], decimal_point)

        C_1d_C0 = round(day_1_bars['Close'][-1], decimal_point)
        C_1d_P1 = round(day_1_bars['Close'][-2], decimal_point)
        C_1d_P2 = round(day_1_bars['Close'][-3], decimal_point)

        M_1d_C0 = round(macd_1['MACD_12_26_9'][-1], decimal_point)
        M_1d_P1 = round(macd_1['MACD_12_26_9'][-2], decimal_point)
        H_1d_C0 = round(macd_1['MACDh_12_26_9'][-1], decimal_point)
        H_1d_P1 = round(macd_1['MACDh_12_26_9'][-2], decimal_point)
        E_1d_C0 = round(ema_1[-1], decimal_point_ema)
        V_1d_C0 = day_1_bars['Volume'][-1]
        volume_values = day_1_bars['Volume'][-12:-2]
        volume_values_arr = volume_values.values
        V_1d_P1_P10 = volume_values_arr.tolist()

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
        H_60m_Limit = -0.0050

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
        Vol_threshold = 1000

        market_price = round(minute_5_bars['Close'][-1], decimal_point)

        if symbol not in existing_position_symbols:

            if symbol not in existing_order_symbols:

                # Model_5MX0
                ### Check if 1D Volume Break ###
                if V_1d_C0 > max(V_1d_P1_P10):
                    print(f" - It's Volume Break")

                    # Model 1: Check MACD cross up Signal
                    if H_1d_P1 < 0.0000 and H_1d_C0 > 0.0000 and C_1d_C0 > E_1d_C0:
                        print(f" - Model 1: MACD cross up Signal")
                        SBF_5m = H_5m_C0/H_5m_P1
                        SBF_5m_threshold = 1.5   

                        # Check 60-15-5-Minute Condition to Enter (5MX0)
                        if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and SBF_5m > SBF_5m_threshold and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

                            # Check RSI and volume
                            if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                                print(f" - It's buy signal for Model 5MX0_MACD cross up Signal")         
                                quantity = calculate_quantity(market_price)
                                print(f" - Placing buy order for {symbol} at {market_price}.")
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

                        # Check 60-15-5-Minute Condition to Enter (5MXU)
                        elif H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and H_15m_P1 < H_15m_C0 < 0.0000 and H_60m_C0 > H_60m_Limit:

                            # Check RSI and volume
                            if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                                print(f" - It's buy signal for Model 5MXU_MACD cross up Signal")         
                                quantity = calculate_quantity(market_price)
                                print(f" - Placing buy order for {symbol} at {market_price}.")
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

                        # Check 60-15-5-Minute Condition to Enter (5MKR)
                        elif H_5m_C0 > H_5m_P1 > 0.0000 and SBF_5m > SBF_5m_threshold and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

                            # Check RSI and volume
                            if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                                print(f" - It's buy signal for Model 5MKR_MACD cross up Signal")         
                                quantity = calculate_quantity(market_price)
                                print(f" - Placing buy order for {symbol} at {market_price}.")
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

                        else:
                            print(f" - Please check one of 60-15-5-Minute conditions: H_60m_C0 = {H_60m_C0}, M_15m_C0 = {M_15m_C0}, M_5m_C0 = {M_5m_C0} and M_5m_P1 = {M_5m_P1}")

                    # Model 2: Check MACD cross up 0-line
                    elif M_1d_P1 < 0.0000 and M_1d_C0 > 0.0000 and C_1d_C0 > E_1d_C0:
                        print(f" - Model 2: MACD cross up 0-line")
                        SBF_5m = H_5m_C0/H_5m_P1
                        SBF_5m_threshold = 1.5 

                        # Check 60-15-5-Minute Condition to Enter 
                        if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and SBF_5m > SBF_5m_threshold and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

                            # Check RSI and volume
                            if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                                print(f" - It's buy signal for Model 5MX0_MACD cross up 0-line")         
                                quantity = calculate_quantity(market_price)
                                print(f" - Placing buy order for {symbol} at {market_price}.")
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 2\n")

                        # Check 60-15-5-Minute Condition to Enter (5MXU)
                        elif H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

                            # Check RSI and volume
                            if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                                print(f" - It's buy signal for Model 5MXU_MACD cross up Signal")         
                                quantity = calculate_quantity(market_price)
                                print(f" - Placing buy order for {symbol} at {market_price}.")
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

                        # Check 60-15-5-Minute Condition to Enter (5MKR)
                        elif H_5m_C0 > H_5m_P1 > 0.0000 and SBF_5m > SBF_5m_threshold and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

                            # Check RSI and volume
                            if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                                print(f" - It's buy signal for Model 5MKR_MACD cross up Signal")         
                                quantity = calculate_quantity(market_price)
                                print(f" - Placing buy order for {symbol} at {market_price}.")
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

                        else:
                            print(f" - Please check one of 60-15-5-Minute conditions: H_60m_C0 = {H_60m_C0}, M_15m_C0 = {M_15m_C0}, M_5m_C0 = {M_5m_C0} and M_5m_P1 = {M_5m_P1}")

                    # Model 3: Check MACD keep rising
                    elif H_1d_C0 > H_1d_P1 and C_1d_C0 > E_1d_C0:
                        print(f" - Model 3: MACD keep rising")
                        SBF_5m = H_5m_C0/H_5m_P1
                        SBF_5m_threshold = 1.5 

                        # Check 60-15-5-Minute Condition to Enter (5MX0)
                        if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and SBF_5m > SBF_5m_threshold and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

                            # Check RSI and volume
                            if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                                print(f" - It's buy signal for Model 5MX0_MACD keep rising")         
                                quantity = calculate_quantity(market_price)
                                print(f" - Placing buy order for {symbol} at {market_price}.")
                                place_buy_order(symbol, quantity)                                
                            else:
                                print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 2\n")

                        # Check 60-15-5-Minute Condition to Enter (5MXU)
                        elif H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

                            # Check RSI and volume
                            if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                                print(f" - It's buy signal for Model 5MXU_MACD cross up Signal")         
                                quantity = calculate_quantity(market_price)
                                print(f" - Placing buy order for {symbol} at {market_price}.")
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

                        # Check 60-15-5-Minute Condition to Enter (5MKR)
                        elif H_5m_C0 > H_5m_P1 > 0.0000 and SBF_5m > SBF_5m_threshold and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit:

                            # Check RSI and volume
                            if RSI_min < RSI_5m_C0 < RSI_max and RSI_min < RSI_15m_C0 < RSI_max and Vol_5m_C0 > Vol_threshold: 
                                print(f" - It's buy signal for Model 5MKR_MACD cross up Signal")         
                                quantity = calculate_quantity(market_price)
                                print(f" - Placing buy order for {symbol} at {market_price}.")
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - One of these value is out of range: RSI-5m = {RSI_5m_C0} or RSI-15m = {RSI_15m_C0} for model 1\n")

                        else:
                            print(f" - Please check one of 60-15-5-Minute conditions: H_60m_C0 = {H_60m_C0}, M_15m_C0 = {M_15m_C0}, M_5m_C0 = {M_5m_C0} and M_5m_P1 = {M_5m_P1}")
                
                    # Model_5MX0_END
                    else:
                        print(f" - One of 1D conditions do not pass")

                ### Check if it's possible to enter earlier before volume break ###
                              
                # Case-1: 5MX0-15MXU-60MKR 
                # Input: Breakout-4 (STEP 23-24 May 2024)
                # Input: Breakout-5 (MREO 24-28 May 2024)
                # Input: (RGTI 30-31 False Breakout) Fixed by adding H_60m_C0 > 0.0000 
                # regarding the difference with STEP and MREO, H_60m_C0 and H_60m_P1 > 0.0000
                # if add only H_60m_C0 > 0.0000 for RGTI, it still could be fit in 60MXU.
                # then, it still be False Breakout in the 60MXU case
                # so, how to avoid or at least reduce this False Breakout 
                # one idea is once, it False signal which means H_60m_C0 < 0.0000 and H_60m_P1 < 0.0000 just leave the position for 60MXU
                # for 60MKR just use M_60m_C0 < M_60m_P1 and H_60m_C0 < H_60m_P1 to exit the position 
        
                # # Check Signal
                # elif M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_15m_C0 > 0.0000 and H_15m_P1 < 0.0000 and H_60m_C0 > H_60m_P1 > 0.0000:

                #     # Calculate Significant Factors
                #     # (STEP 23-24 May 2024: H_5m_C0 = 0.1449 > H_5m_P1 = 0.0619 --> 2.34)
                #     # (MREO 24-28 May 2024: H_5m_C0 = 0.0131 > H_5m_P1 = 0.0059 --> 2.22)
                #     SBF_5m = round(H_5m_C0/H_5m_P1, decimal_point) 
                #     SBF_5m_threshold = 1.50

                #     # Check Significant Factors                      
                #     if SBF_5m > SBF_5m_threshold:
                #         print(f" - It's buy signal for Model 5MX0-15MXU-60MKR")         
                #         quantity = calculate_quantity(market_price)
                #         print(f" - Placing buy order for {symbol} at {market_price}.")

                #         # Placing order
                #         try:
                #             api.submit_order(
                #                 symbol=symbol,
                #                 side='buy',
                #                 type='market',
                #                 qty=quantity,
                #                 time_in_force='gtc'
                #             )
                #         except Exception as e:
                #             print(f" - Could not submit order {e}\n")  

                #     else:
                #         print(f" - SBF = {SBF_5m} < the threshold = {SBF_5m_threshold} (Case-1: 5MX0-15MXU-60MKR)\n")

                # # Case-2: 5MXU-15MXU-60MKR 
                # # Input: Breakout-4 (MUX 24-28 May 2024)
                # # Check Signal
                # elif H_5m_C0 > 0.0000 and H_5m_P1 < 0.0000 and M_5m_C0 > 0.0000 and H_15m_C0 > 0.0000 and H_15m_P1 < 0.0000 and H_60m_C0 > H_60m_P1 > 0.0000:

                #     # Calculate Significant Factors
                #     # (MUX 24-28 May 2024: H_5m_C0 = 0.0195 > H_5m_P1 = -0.0062 --> 415%)
                #     SCF_5m = round((H_5m_P1 - H_5m_C0)/H_5m_P1*100, decimal_point)            
                #     SCF_5m_threshold = 100

                #     # Check Significant Factors
                #     if SCF_5m > SCF_5m_threshold:
                #         print(f" - It's buy signal for Model 5MXU-15MXU-60MKR")         
                #         quantity = calculate_quantity(market_price)
                #         print(f" - Placing buy order for {symbol} at {market_price}.")

                #         # Placing order
                #         try:
                #             api.submit_order(
                #                 symbol=symbol,
                #                 side='buy',
                #                 type='market',
                #                 qty=quantity,
                #                 time_in_force='gtc'
                #             )
                #         except Exception as e:
                #             print(f" - Could not submit order {e}\n")  

                #     else:
                #         print(f" - SCF = {SCF_5m} < the threshold = {SCF_5m_threshold} (Case-2: 5MXU-15MXU-60MKR)\n")

                # # Case-3: 5MKR-15MX0-60MKR 
                # # Input: Breakout-6 (QBTS 24-28 May 2024)
                # # Input:
                # # Check Signal
                # elif M_5m_C0 > M_5m_P1 > 0.0000 and M_15m_C0 > 0.0000 and M_15m_P1 < 0.0000 and H_60m_C0 > H_60m_P1 > 0.0000:

                #     # Calculate Significant Factors
                #     # (QBTS 24-28 May 2024: H_5m_C0 = 0.0113 > H_5m_P1 = 0.0043 --> 2.62))
                #     SBF_5m = round(H_5m_C0/H_5m_P1, decimal_point) 
                #     SBF_5m_threshold = 1.50

                #     # Check Significant Factors
                #     if SBF_5m > SBF_5m_threshold:
                #         print(f" - It's buy signal for Model 5MKR-15MX0-60MKR")         
                #         quantity = calculate_quantity(market_price)
                #         print(f" - Placing buy order for {symbol} at {market_price}.")

                #         # Placing order
                #         try:
                #             api.submit_order(
                #                 symbol=symbol,
                #                 side='buy',
                #                 type='market',
                #                 qty=quantity,
                #                 time_in_force='gtc'
                #             )
                #         except Exception as e:
                #             print(f" - Could not submit order {e}\n")  

                #     else:
                #         print(f" - SBF = {SBF_5m} < the threshold = {SBF_5m_threshold} (Case-3: 5MKR-15MX0-60MKR)\n")

                # # Case-4: 60MXU 
                # # Input: Breakout-7 (VZ 29-30 May 2024)
                # # Check Signal
                # elif H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000 and C_60m_C0 > E_60m_C0 and C_60m_P1 < E_60m_P1:

                #     # No Significant Factors Check Yet
                #     print(f" - It's buy signal for Model 60MXU")         
                #     quantity = calculate_quantity(market_price)
                #     print(f" - Placing buy order for {symbol} at {market_price}.")

                #     # Placing order
                #     try:
                #         api.submit_order(
                #             symbol=symbol,
                #             side='buy',
                #             type='market',
                #             qty=quantity,
                #             time_in_force='gtc'
                #         )
                #     except Exception as e:
                #         print(f" - Could not submit order {e}\n")  

                # # Case-5: 60MX0 
                # # Input: Breakout-5 (NABL 28-29 May 2024)
                # # Check Signal
                # elif M_60m_C0 > 0.0000 and M_60m_P1 < 0.0000 and C_60m_C0 > E_60m_C0:
                    
                #     # Calculate Significant Factors
                #     # (NABL 28-29 May 2024: H_60m_C0 = 0.0848 > H_60m_P1 = 0.0123 --> 6.89))
                #     SBF_60m_60MX0 = round(H_60m_C0/H_60m_P1, decimal_point) 
                #     SBF_60m_60MX0_threshold = 1.50

                #     # Check Significant Factors
                #     if SBF_60m_60MX0 > SBF_60m_60MX0_threshold:                    
                #         print(f" - It's buy signal for Model 60MX0")         
                #         quantity = calculate_quantity(market_price)
                #         print(f" - Placing buy order for {symbol} at {market_price}.")

                #         # Placing order
                #         try:
                #             api.submit_order(
                #                 symbol=symbol,
                #                 side='buy',
                #                 type='market',
                #                 qty=quantity,
                #                 time_in_force='gtc'
                #             )
                #         except Exception as e:
                #             print(f" - Could not submit order {e}\n")  

                #     else:
                #         print(f" - SBF_60m_60MX0 = {SBF_60m_60MX0} < the threshold = {SBF_60m_60MX0_threshold} (Case-5: 60MX0)\n")

                # Case-6: 60MX0 (Check Significant of 60MX0)
                # Input: Breakout-8 (EPRT 31 May - 3 Jun 2024)
                # Check Signal
                elif M_60m_C0 > 0.0000 and M_60m_P1 < 0.0000 and H_60m_C0 > 0.0000:
                    
                    # No Significant Factors Check                  
                    print(f" - It's buy signal for Model 60MX0 Purely")         
                    quantity = calculate_quantity(market_price)
                    print(f" - Placing buy order for {symbol} at {market_price}.")
                    place_buy_order(symbol, quantity)

                # Model_5MX0_END
                else:
                    print(f" - Waiting for 60MX0\n")
            
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

                # Update the highest price for trailing stop
                if symbol not in highest_prices:
                    highest_prices[symbol] = market_price

                if market_price > highest_prices[symbol]:
                    highest_prices[symbol] = market_price

                # Calculate trailing stop price
                trailing_stop_price = highest_prices[symbol] * (1 - TRAILING_STOP_PERCENTAGE)

                # Check if current market price is below trailing stop price
                if market_price <= trailing_stop_price:
                    print(f" - Trailing stop hit. Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Strategy 1-5m for taking profit at least 1.0% with open up more profit in 5m TF
                # Some cases not reaching 1.0% then it's change to down size and could lead to 7.5% cut loss
                # Then try to adjust by adding 15m condition in case that the profit is below 1.0% and still open up more profit option.
                # (CDMO 6 Jun 2024)
                elif M_5m_C0 < M_5m_P1 and 0.0000 < H_5m_C0 < H_5m_P1 and M_15m_C0 < M_15m_P1 and 0.0000 < H_15m_C0 < H_15m_P1:
                    print(f" - It's taking-profit signal in 5m TF.")
                    print(f" - Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Strategy 1-5m for the case of the false open gap up
                # (LYFT 6 Jun 2024)
                # Introducing no 1% profit condition
                elif H_5m_C0 < 0.0000 and H_15m_C0 < H_15m_P1:
                    print(f" - It's taking-profit signal in 60m TF.")
                    print(f" - Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Strategy 2 for cutting loss at 7.5%
                elif market_price < EMA_10d and market_value < (0.925 * cost):
                    print(f" - It's cut-loss signal.")
                    print(f" - Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Strategy 3 for cutting loss should not greater than 7.5%
                elif market_value < (0.9250 * cost):
                    print(f" - It's cut-loss signal.")
                    print(f" - Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

                # Strategy 4 for fasle breakout in Case-4: 60MXU
                elif H_60m_C0 < 0.0000 and H_60m_P1 < 0.0000:
                    print(f" - It's cut-loss signal --> False Breakout.")
                    print(f" - Placing sell order for {symbol} at {market_price}.\n")
                    place_sell_order(symbol, quantity)

            except Exception as e:
                print(f"The order may not be filled")

            else:
                print(" - No sell signal yet\n")

        else: 
            print(" - It's already been traded for today.\n")

else:
    print(f"The market is closed")