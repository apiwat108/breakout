import config, requests
import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from helpers import calculate_quantity
import pytz
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import alpaca_trade_api as tradeapi
import datetime as dt

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
clock = api.get_clock()

# Define the trailing stop percentage
TRAILING_STOP_PERCENTAGE = 0.080  # -8.0%

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

# Function to place sell order due to market condition is not good to trade
def place_sell_order_market(symbol, quantity):
    try:
        api.submit_order(
            symbol=symbol,
            side='sell',
            type='market',
            qty=quantity,
            time_in_force='gtc'
        )
        print(f" - Placing sell order for {symbol} due to market condition is not good to trade.\n")
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

# Function to get entry date
def get_entry_date(symbol):
    orders = api.list_orders(status='all', limit=500)
    for order in orders:
        if order.symbol == symbol and order.side == 'buy' and order.filled_at is not None:
            return order.filled_at
    return None

if clock.is_open:

    # Check Market Condition
    ticker_market = yf.Ticker('SPY')
    day_1_bars_market = ticker_market.history(interval='1d',period='6mo')    
    EMA_10d_bars_market = day_1_bars_market['Close'].ewm(span=10, adjust=False).mean()
    EMA_10d_market = EMA_10d_bars_market[-1]
    macd_1_market = day_1_bars_market.ta.macd()
    decimal_point = 4
    C_1d_C0_market = round(day_1_bars_market['Close'][-1], decimal_point)
    H_1d_C0_market = round(macd_1_market['MACDh_12_26_9'][-1], decimal_point)

    positions = api.list_positions()
    existing_position_symbols = [position.symbol for position in positions]

    # Market is not good to trade
    if C_1d_C0_market < EMA_10d_market and H_1d_C0_market < 0.0000:
        print(f"SPY is below EMA_10 ({C_1d_C0_market} < {EMA_10d_market}) and H_1d_C0_market ({H_1d_C0_market}) < 0.0000.")
        print("Market is not good to trades.")

        # Liquidate all existing positions
        if existing_position_symbols:
            print("Liquidating all positions and skipping trades.\n")
            for symbol in existing_position_symbols:
                position = api.get_position(symbol)
                quantity = position.qty
                place_sell_order_market(symbol, quantity)
        else:
            print("No existing positions. Waiting for good market conditions to trade.\n")
            
    # Market is good to trade
    else:
        print("Market is good to trade.")
        print(f"SPY is above EMA_10 ({C_1d_C0_market} > {EMA_10d_market}) and H_1d_C0_market ({H_1d_C0_market}) > 0.0000.\n")
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

            EMA_10d_bars = day_1_bars['Close'].ewm(span=10, adjust=False).mean()
            EMA_10d = EMA_10d_bars[-1]

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
            M_60m_P2 = round(macd_60['MACD_12_26_9'][-3], decimal_point)
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
            Vol_threshold = 50

            market_price = round(minute_5_bars['Close'][-1], decimal_point)

            ## -- ENTRY -- ##
            if symbol not in existing_position_symbols:

                if symbol not in existing_order_symbols:

                    # Set Entry Limit not over 10.0% above EMA
                    # LUNR 30 Aug 2024 (Entry price = 5.68, EMA = 4.97 --> 14.3% above EMA --> potential profit -2.3%)
                    # CHWY 28 Aug 2024 (Entry price = 28.89, EMA = 26.45 --> 9.22% above EMA --> potential profit 5.2%)
                    # VRAX 28 Aug 2024 (Entry price = 6.11, EMA = 5.02 --> 21.7% above EMA --> potential profit 18.5%)

                    Entry_Limit_60m = E_60m_C0*1.10

                    # Entry Position 0: 60MX0 for Breakout-5
                    if M_60m_C0 > 0.0000 and M_60m_P1 < 0.0000 and H_60m_C0 > 0.0000:
                        # JMIA (22 Jul 2024_09:30)
                        print(f" - It's buy signal for Entry Position 0: 60MX0")  

                        # Check Entry Position Limit
                        if C_60m_C0 < Entry_Limit_60m:
                            print(f" - The entry price is in the Entry Limit")         
                            quantity = calculate_quantity(market_price)
                            place_buy_order(symbol, quantity)
                        else:
                            print(f" - The entry price is over the Entry Limit") 

                    # Entry Position 0: 60MX0 Special
                    elif M_60m_P1 > 0.0000 and M_60m_P2 < 0.0000 and H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000:
                        print(f" - It's buy signal for Entry Position 0: 60MX0 Special")   

                        # Check Entry Position Limit
                        if C_60m_C0 < Entry_Limit_60m:
                            print(f" - The entry price is in the Entry Limit")         
                            quantity = calculate_quantity(market_price)
                            place_buy_order(symbol, quantity)
                        else:
                            print(f" - The entry price is over the Entry Limit") 

                    # Entry Position 0: 60MX0 on M_1d_C0 < 0.0000 for Breakout-6
                    elif M_60m_C0 > 0.0000 and M_60m_P1 < 0.0000 and H_60m_C0 > 0.0000 and C_1d_C0 > EMA_10d:
                        # JMIA (2 Jul 2024_14:30, 28 May 2024_09:30)
                        print(f" - It's buy signal for Entry Position 0: on H_1d_C0 < 0.0000")

                        # Check Entry Position Limit
                        if C_60m_C0 < Entry_Limit_60m:
                            print(f" - The entry price is in the Entry Limit")         
                            quantity = calculate_quantity(market_price)
                            place_buy_order(symbol, quantity)
                        else:
                            print(f" - The entry price is over the Entry Limit") 

                    # Entry Position 0: 60MXU for Breakout-4
                    elif M_60m_C0 > 0.0000 and H_60m_C0 > 0.0000 and H_60m_P1 > 0.0000 and H_60m_P2 < 0.0000 and H_1d_C0 > 0.0000:
                        # LAAC 24 Oct 2024: False and cut loss at -5.0%
                        # Based on the analysis of LAAC (24 Oct 2024), AEVA (24 Oct 2024), MTA (21 Oct 2024)
                        # NCV (18 Oct 2024), MTTR (03 Oct 2024). Most of them were cut loss due to 60MXU entry point.
                        # So, the cut-loss with -5.0% can be kept as it is and the 60MXU can be cancelled.
                        # With more review on 13 Nov 2024, it the breakout is valid, most of them show 60MXU and then keep going up
                        # To avoid false 60MXU, just need to confirm 60MXU by addiing H_60m_P2 < 0.0000 and change H_60m_P1 > 0.0000

                        # Also add M_60_P1 limit to set area that 60MXU sometime happened just above 0-line, which seem to be a valid point
                        limit_60MXU = 0.0200
                        if M_60m_P1 < limit_60MXU:
                            print(f" - It's buy signal for Entry Position 0: 60MXU")
                            print(f" H_60m_P2 = {H_60m_P2} < 0.0000")
                            print(f" H_60m_P1 = {H_60m_P1} > 0.0000")
                            print(f" H_60m_C0 = {H_60m_C0} > 0.0000")
                            print(f" M_60m_P1 = {M_60m_P1} < 0.0200")

                            # Check Entry Position Limit
                            if C_60m_C0 < Entry_Limit_60m:
                                print(f" - The entry price is in the Entry Limit")         
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The entry price is over the Entry Limit") 

                        else:
                            print(f" M_60m_P1 = {M_60m_P1} is obove the limit of {limit_60MXU}")
                            print(f" It's too far from the 0-line")    

                    # Extend H_1d_P4 to H_1D_P5 for the case of H_1d_C0 > 0 (BFH)
                    # Active model in breakout_symbol for JMIA and PLSE for 60MX0 before 1DXU (M_1D_C0 > 0, H_1D_C0 < 0, M_60m_C0 < 0)
                    # Active model in breakout_symbol for SLRN for 60MX0 before 1DXU (M_1D_C0 < 0, H_1D_C0 > 0, M_60m_C0 < 0)
                    # Active model in breakout_symbol for CIM before 1DXU but could be conflict with the existing condition (H_1D_P5) due to more days on H_1D_P8
                    # Should keep H_60m_C0 > 0 in entering position (NBBK 8 Jul (09:30) and 9 Jul (09:30) cases)(NKTR 2 Jul)
                    # Should add special case for EVGO H_60m_C0 > 0, H_60m_P1 < 0, M_60m_P1 > 0, M_60m_P2 < 0

                    # # Entry Position 0: 5MX0
                    # if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_5m_C0 > 0.0000 and M_15m_C0 > 0.0000 and H_60m_C0 > H_60m_Limit and Vol_5m_C0 > Vol_threshold:
                    #     print(f" - It's buy signal for Entry Position 0: 5MX0")         
                    #     quantity = calculate_quantity(market_price)
                    #     place_buy_order(symbol, quantity)

                    else:
                        print(" - Waiting for the Buy Signal\n")
                
                else:
                    print(f' - The order of stock {symbol} is placed\n')

            ## -- EXIT -- ##
            elif symbol in existing_position_symbols:

                if symbol not in existing_order_symbols:

                    # Strategy 0 for taking profit with Trailing Stop
                    try:
                        # Getting Data and Testing Trailing Stop
                        print(f" - Already in the position")
                        position = api.get_position(symbol)
                        quantity = position.qty
                        entry_price = float(position.avg_entry_price)
                        market_value = abs(float(position.market_value))
                        cost = abs(float(position.cost_basis))
                        entry_date_g = get_entry_date(symbol)
                        entry_d = entry_date_g.astimezone(pytz.timezone('America/New_York')).date()
                        current_date = dt.datetime.now(pytz.timezone('America/New_York')).date()
                        # print(f" - entry_date:{entry_date} (type:{type(entry_date)}), current_date:{current_date} (type:{type(entry_date)})")

                        # Trailing Stop for 60MX0
                        entry_date = get_entry_date(symbol)
                        if entry_date is not None:
                            # Round the entry_date to the nearest 5-minute interval in New York time
                            entry_date = entry_date.astimezone(pytz.timezone('America/New_York'))
                            entry_date = entry_date - timedelta(minutes=entry_date.minute % 5,
                                                                seconds=entry_date.second,
                                                                microseconds=entry_date.microsecond)
                            print(f" - Entry DATE-TIME for {symbol} is {entry_date.strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            print(f" - Could not find entry date for {symbol}")
                            continue

                        # Use existing minute_5_bars to get high prices since entry date-time
                        new_bars = minute_5_bars[minute_5_bars.index >= entry_date]
                        new_high_prices = [round(price, 4) for price in new_bars['High'].tolist()]
                        # print(f" - High prices since entry: {new_high_prices}")

                        # Update the high prices dictionary
                        if symbol not in high_prices:
                            high_prices[symbol] = []
                            high_prices[symbol].extend(new_high_prices)                       

                        # Calculate the highest price in the list
                        highest_price = round(max(high_prices[symbol]), decimal_point)
                        print(f" - The highest price for {symbol} so far is {highest_price}")

                        # Calculate trailing stop price at -8.0%
                        trailing_stop_price = highest_price * (1 - TRAILING_STOP_PERCENTAGE)

                        # Check if current market price is below trailing stop price
                        # Initially set trailing stop price at -5.0%
                        # NIO 24 Sep 2024 -7.25% from high missed 19.5% in on 27 Sep --> add M_60m_C0 < 0.0000        
                        # However, VERI 11 Oct 2024 -35% but M_60m_C0 > 0.0000
                        # To optimize the signal (relative) + percentage (absolute), the trailing stop change to -8.0%
                        # and the M_60m_C0 < 0.0000 is removed
                        if market_price <= trailing_stop_price and market_value > cost:
                            print(f" - Trailing stop hit. Placing sell order for {symbol} at {market_price}.\n")
                            place_sell_order(symbol, quantity)   

                    except Exception as e:
                        print(f" - The error as {e}")

                    # Strategy 1 for taking whatever profit asap and avoiding day trade
                    print(f" current date = {current_date}, type current date = {type(current_date)}")
                    print(f" entry date = {entry_d}, type entry date = {type(entry_d)}")
                    if current_date != entry_d and market_price > (1.001 * cost):
                        print(f" - It's taking-profit whatever profit asap and avoiding day trade")
                        place_sell_order(symbol, quantity)

                    # Strategy 2 for taking profit by signal (relative) + percentage (absolute)             
                    elif M_60m_C0 < 0.0000 and H_60m_C0 < 0.0000 and market_value > cost:
                        # VRAX 29 Aug 2024 turn 20% profit down to 5% cut loss (not updated) --> Fixed by using Trailing Stop
                        # IONQ 18 Oct 2024 sold when the profit over 50% but stock keep going up to 95% 
                        # It's need to be the room to fully taking the big win
                        # Change from market_value > (1.50 * cost) to M60X0-
                        print(f" - It's taking-profit signal with M60X0-.")
                        place_sell_order(symbol, quantity)

                    # Strategy 3 for cutting loss should not greater than 5%
                    elif market_value < (0.95 * cost):
                        # LAAC 24 Oct 2024 Swing lower than -5% at -6.9% then return to profit 4% 
                        # This is invalid due to lack of daily update, which allow 60MXU execute when H_1d_C0 < 0.0000
                        # So, the in the entry condition, the H_1d_C0 > 0.0000 is added.
                        # Try to adjust to relative signal cut loss instead of absolute cut-loss percentage
                        # The idea of optimization on cut loss is on hold, but try to stick with -5.0% whatever reason
                        # The modification of the cut loss should based on the valid trading results and analysis
                        # It's ongoing... (11 Nov 2024) ... as a result,
                        # Based on the analysis of LAAC (24 Oct 2024), AEVA (24 Oct 2024), MTA (21 Oct 2024)
                        # NCV (18 Oct 2024), MTTR (03 Oct 2024). Most of them were cut loss due to 60MXU entry point.
                        # So, the cut-loss with -5.0% can be kept as it is and the 60MXU can be cancelled.
                        print(f" - It's cut-loss signal with Strategy 3 (-5.0%.")
                        place_sell_order(symbol, quantity)

                    # Strategy 4 for false 60MX0 and allow 3% for variation (F60MX0)
                    elif M_60m_C0 < 0.0000 and H_60m_C0 > 0.0000 and market_value < (0.97 * cost):
                        print(f" - It's cut-loss signal with Strategy 4 (F60MX0).")
                        print(f" - M_60m_C0 = {M_60m_C0} < 0.0000")
                        print(f" - H_60m_C0 = {H_60m_C0} > 0.0000")                
                        place_sell_order(symbol, quantity)

                    # Strategy 5 for weak up trend: price below ema_10
                    elif C_1d_C0 < EMA_10d:
                        # NCV 18-23 Oct 2024
                        # Entry with 60MXU
                        print(f" - It's cut-loss signal with Strategy 5 (Price below EMA).")
                        place_sell_order(symbol, quantity)

                    # Strategy 6 for weak up trend: 60MX0-
                    elif M_60m_C0 < 0.0000 and H_60m_C0 < 0.0000 and market_value < cost:
                        # NCV 18-23 Oct 2024
                        # Entry with 60MXU
                        print(f" - It's cut-loss signal with Strategy 6 (60MX0-).")
                        place_sell_order(symbol, quantity)

                    # Strategy 7 for weak up trend: H_1d_C0 < 0.0000 and allow 3% for variation (F1DXD)
                    elif H_1d_C0 < 0.0000 and market_value < (0.97 * cost):
                        # NCV 18-23 Oct 2024
                        # Entry with 60MXU
                        print(f" - It's cut-loss signal with Strategy 7 (1DXD).")
                        place_sell_order(symbol, quantity)

                    # Strategy END
                    else:
                        print(" - No sell signal yet\n")

                else:
                    print(f" - The order of stock {symbol} is placed\n")

            else: 
                print(" - It's already been traded for today.\n")

else:
    print(f"The market is closed")



### TESTING BEFORE -- ONE and ONLY 5MX0 with 0.75% Profit -- ###

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
            # elif market_value > (1.005 * cost) and M_5m_C0 < M_5m_P1 and 0.0000 < H_5m_C0 < H_5m_P1 and M_15m_C0 < M_15m_P1 and H_15m_C0 < H_15m_P1:
            #     # Strategy 1 for taking profit at least 1.0%
            #     # Avoid exit to early without a chance to take profit (HRZN )
            #     # Consider to add 15m condition like the BB case (RPAY 11 Jun 2024)
            #     print(f" - It's taking-profit signal with min of 1% profit.")
            #     place_sell_order(symbol, quantity)

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

