import config, requests
import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame  # Use the correct TimeFrame
from helpers import calculate_quantity
import pytz
import pandas_ta as ta
import pandas as pd
import alpaca_trade_api as tradeapi
import datetime as dt

# Updated get_alpaca_bars: expects start and end as datetime.date or datetime.datetime objects

def get_alpaca_bars(symbol, timeframe, start, end=None):
    try:
        import pandas as pd
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.timeframe import TimeFrame
        from alpaca.data.requests import StockBarsRequest
        # Use config.py credentials for authentication
        ALPACA_API_KEY = config.API_KEY
        ALPACA_SECRET_KEY = config.SECRET_KEY
        client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start,  # pass as date/datetime
            end=end if end else None
        )
        bars = client.get_stock_bars(request_params).df
        if bars.empty:
            return bars
        # Normalize columns
        bars.columns = [col.title() if col.lower() in ['open','close','volume'] else col for col in bars.columns]
        return bars
    except Exception as e:
        print(f"Error fetching bars for {symbol}: {e}")
        return pd.DataFrame()

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
clock = api.get_clock()

# Define the trailing stop percentage
TRAILING_STOP_PERCENTAGE = 0.75  # -75.0%

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

def is_bearish_pin_bar(o, h, l, c):
    """
    Determines if a 5-min candle is a bearish pin bar.
    
    Conditions for a bearish pin bar (one common set of rules):
      - The candle is bearish (close < open).
      - The upper wick is at least 2 times the body.
      - The lower wick is very small relative to the total range.
      
    Parameters:
      o (float): Open price.
      h (float): High price.
      l (float): Low price.
      c (float): Close price.
      
    Returns:
      bool: True if the candle qualifies as a bearish pin bar.
    """
    body = abs(c - o)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l

    # To avoid division by zero if h==l
    total_range = h - l if h - l != 0 else 1

    # Conditions:
    # - Bearish candle: close is below open.
    # - Long upper wick: at least 2 times the body.
    # - Small lower wick: less than 25% of the total range.
    if c < o and upper_wick >= 2 * body and lower_wick <= 0.25 * total_range:
        return True
    return False


if clock.is_open:
    # Check Market Condition
    spy_start_date = datetime.now() - timedelta(days=60)  # pass as datetime, ensure enough rows for MACD
    day_1_bars_market = get_alpaca_bars('SPY', TimeFrame.Day, start=spy_start_date)
    if day_1_bars_market.empty or 'Close' not in day_1_bars_market.columns:
        print('No SPY daily data returned or missing Close column.')
        EMA_10d_market = None
        C_1d_C0_market = None
        H_1d_C0_market = None
    else:
        EMA_10d_bars_market = day_1_bars_market['Close'].ewm(span=10, adjust=False).mean()
        decimal_point = 4
        EMA_10d_market = round(EMA_10d_bars_market.iloc[-1], decimal_point)
        # --- Diagnostics for MACD calculation ---
        # print(f"SPY DataFrame shape: {day_1_bars_market.shape}")
        # print(f"SPY DataFrame columns: {list(day_1_bars_market.columns)}")
        # print(f"SPY DataFrame tail:\n{day_1_bars_market.tail(3)}")
        # --- Fix for pandas_ta: set columns to lowercase before indicator calculation ---
        day_1_bars_market.columns = [col.lower() for col in day_1_bars_market.columns]
        # Ensure 'close' column exists and enough rows for MACD
        if 'close' in day_1_bars_market.columns and len(day_1_bars_market) >= 35:
            macd_1_market = day_1_bars_market.ta.macd()
        else:
            if 'close' not in day_1_bars_market.columns:
                print(f"'close' column missing. Columns present: {list(day_1_bars_market.columns)}")
            if len(day_1_bars_market) < 35:
                print(f"Insufficient rows for MACD: {len(day_1_bars_market)} rows (need >= 35)")
            print("Insufficient data or missing 'close' column for MACD calculation on SPY.")
            macd_1_market = None
        # Restore Title Case for rest of code
        day_1_bars_market.columns = [col.title() for col in day_1_bars_market.columns]
        C_1d_C0_market = round(day_1_bars_market['Close'].iloc[-1], decimal_point)
        if macd_1_market is not None and not macd_1_market.empty and 'MACDh_12_26_9' in macd_1_market.columns:
            H_1d_C0_market = round(macd_1_market['MACDh_12_26_9'].iloc[-1], decimal_point)
        else:
            available_cols = list(macd_1_market.columns) if macd_1_market is not None else []
            print(f"MACD columns available: {available_cols}")
            print("Warning: 'MACDh_12_26_9' not found in MACD DataFrame or MACD calculation failed. Skipping H_1d_C0_market calculation.")
            H_1d_C0_market = None
    positions = api.list_positions()
    existing_position_symbols = [position.symbol for position in positions]

    # Market is not good to trade
    if EMA_10d_market is not None and C_1d_C0_market is not None and H_1d_C0_market is not None and C_1d_C0_market < EMA_10d_market and H_1d_C0_market < 0.0000:
        print(f"SPY is below EMA_10 ({C_1d_C0_market} < {EMA_10d_market}) and H_1d_C0_market ({H_1d_C0_market}) < 0.0000.")
        print("Market is not good to trades.")

        # # Liquidate all existing positions
        # if existing_position_symbols:
        #     print("Liquidating all positions and skipping trades.\n")
        #     for symbol in existing_position_symbols:
        #         position = api.get_position(symbol)
        #         quantity = position.qty
        #         place_sell_order_market(symbol, quantity)
        # else:
        #     print("No existing positions. Waiting for good market conditions to trade.\n")

        # No new open positions but keep checking the existing position
        if existing_position_symbols:
            print("No new open position. Keep checking the existing position.\n")
            for symbol in existing_position_symbols:
                position = api.get_position(symbol)
                market_value = abs(float(position.market_value))
                cost = abs(float(position.cost_basis))
                quantity = position.qty
                # Fetch bars from Alpaca
                minute_5_bars = get_alpaca_bars(symbol, TimeFrame.Minute, start=datetime.now() - timedelta(days=5))
                day_1_bars = get_alpaca_bars(symbol, TimeFrame.Day, start=datetime.now() - timedelta(days=180))
                if day_1_bars.empty or 'Close' not in day_1_bars.columns:
                    print(f"No daily bars for {symbol}, skipping.")
                    continue
                macd_1 = day_1_bars.ta.macd()
                decimal_point = 4
                H_1d_C0 = round(macd_1['MACDh_12_26_9'].iloc[-1], decimal_point)
                market_price = round(minute_5_bars['Close'].iloc[-1], decimal_point) if not minute_5_bars.empty else 0
                
                # Cut-loss 
                if market_value < (0.95 * cost):
                    print(f" - It's cut-loss signal with Strategy 2 (-5.0%).")
                    place_sell_order(symbol, quantity)

                # Exit strategy for big winner
                elif H_1d_C0 < 0.0000:
                    print(f" - Exit for big winner.")             
                    place_sell_order(symbol, quantity)
        else:
            print("Keep checking the existiong position. Waiting for good market condition to trade.\n")                

    # Market is good to trade
    elif EMA_10d_market is not None and C_1d_C0_market is not None and H_1d_C0_market is not None and C_1d_C0_market > EMA_10d_market and H_1d_C0_market > 0.0000:
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
            # Fetch bars from Alpaca
            minute_5_bars = get_alpaca_bars(symbol, TimeFrame.Minute, start=datetime.now() - timedelta(days=5))
            minute_15_bars = get_alpaca_bars(symbol, TimeFrame.Minute, start=datetime.now() - timedelta(days=5))
            minute_60_bars = get_alpaca_bars(symbol, TimeFrame.Hour, start=datetime.now() - timedelta(days=30))
            day_1_bars = get_alpaca_bars(symbol, TimeFrame.Day, start=datetime.now() - timedelta(days=180))
            # Check for empty DataFrames
            if any(df.empty or 'Close' not in df.columns for df in [minute_5_bars, minute_15_bars, minute_60_bars, day_1_bars]):
                print(f"Missing or incomplete data for {symbol}, skipping.")
                continue

            EMA_10d_bars = day_1_bars['Close'].ewm(span=10, adjust=False).mean()
            EMA_10d = EMA_10d_bars.iloc[-1]
            print(f"Last close of day_1_bars of {symbol}: {day_1_bars['Close'].iloc[-1]}")

            # --- Fix for pandas_ta: set columns to lowercase before indicator calculation ---
            minute_5_bars.columns = [col.lower() for col in minute_5_bars.columns]
            minute_15_bars.columns = [col.lower() for col in minute_15_bars.columns]
            minute_60_bars.columns = [col.lower() for col in minute_60_bars.columns]
            day_1_bars.columns = [col.lower() for col in day_1_bars.columns]
            macd_5 = minute_5_bars.ta.macd()
            macd_15 = minute_15_bars.ta.macd()
            macd_60 = minute_60_bars.ta.macd()
            macd_1 = day_1_bars.ta.macd()
            rsi_5 = minute_5_bars.ta.rsi()
            rsi_15 = minute_15_bars.ta.rsi()
            rsi_60 = minute_60_bars.ta.rsi()
            ema_60 = minute_60_bars['close'].ewm(span=10, adjust=False).mean()
            # Restore Title Case for rest of code
            minute_5_bars.columns = [col.title() for col in minute_5_bars.columns]
            minute_15_bars.columns = [col.title() for col in minute_15_bars.columns]
            minute_60_bars.columns = [col.title() for col in minute_60_bars.columns]
            day_1_bars.columns = [col.title() for col in day_1_bars.columns]

            decimal_point = 4
            decimal_point_rsi = 2
            decimal_point_ema = 2

            # Candle Stick
            C_60m_C0 = round(minute_60_bars['Close'].iloc[-1], decimal_point)
            # O_60m_C0 = round(minute_60_bars['Open'][-1], decimal_point)
            C_60m_P1 = round(minute_60_bars['Close'].iloc[-2], decimal_point)
            # O_60m_P1 = round(minute_60_bars['Open'][-2], decimal_point)
            C_60m_P2 = round(minute_60_bars['Close'].iloc[-3], decimal_point)

            C_1d_C0 = round(day_1_bars['Close'].iloc[-1], decimal_point)
            C_1d_P1 = round(day_1_bars['Close'].iloc[-2], decimal_point)
            C_1d_P2 = round(day_1_bars['Close'].iloc[-3], decimal_point)

            M_1d_C0 = round(macd_1['MACD_12_26_9'].iloc[-1], decimal_point)
            M_1d_P1 = round(macd_1['MACD_12_26_9'].iloc[-2], decimal_point)
            H_1d_C0 = round(macd_1['MACDh_12_26_9'].iloc[-1], decimal_point)
            H_1d_P1 = round(macd_1['MACDh_12_26_9'].iloc[-2], decimal_point)

            M_60m_C0 = round(macd_60['MACD_12_26_9'].iloc[-1], decimal_point)
            M_60m_P1 = round(macd_60['MACD_12_26_9'].iloc[-2], decimal_point)
            M_60m_P2 = round(macd_60['MACD_12_26_9'].iloc[-3], decimal_point)
            H_60m_C0 = round(macd_60['MACDh_12_26_9'].iloc[-1], decimal_point)
            H_60m_P1 = round(macd_60['MACDh_12_26_9'].iloc[-2], decimal_point)
            H_60m_P2 = round(macd_60['MACDh_12_26_9'].iloc[-3], decimal_point)
            # S_60m_C0 = round(macd_60['MACDs_12_26_9'][-1], decimal_point)
            # S_60m_P1 = round(macd_60['MACDs_12_26_9'][-2], decimal_point)
            # S_60m_P2 = round(macd_60['MACDs_12_26_9'][-3], decimal_point)
            E_60m_C0 = round(ema_60.iloc[-1], decimal_point_ema)
            E_60m_P1 = round(ema_60.iloc[-2], decimal_point_ema)
            H_60m_Limit = -0.0030

            M_15m_C0 = round(macd_15['MACD_12_26_9'].iloc[-1], decimal_point)
            M_15m_P1 = round(macd_15['MACD_12_26_9'].iloc[-2], decimal_point)
            H_15m_C0 = round(macd_15['MACDh_12_26_9'].iloc[-1], decimal_point)
            H_15m_P1 = round(macd_15['MACDh_12_26_9'].iloc[-2], decimal_point)

            M_5m_C0 = round(macd_5['MACD_12_26_9'].iloc[-1], decimal_point)
            M_5m_P1 = round(macd_5['MACD_12_26_9'].iloc[-2], decimal_point)
            H_5m_C0 = round(macd_5['MACDh_12_26_9'].iloc[-1], decimal_point)
            H_5m_P1 = round(macd_5['MACDh_12_26_9'].iloc[-2], decimal_point)
            Open_5m_C0 = round(minute_5_bars['Open'].iloc[-1], decimal_point)
            Close_5m_C0 = round(minute_5_bars['Close'].iloc[-1], decimal_point)
            High_5m_C0 = round(minute_5_bars['High'].iloc[-1], decimal_point)
            Low_5m_C0 = round(minute_5_bars['Low'].iloc[-1], decimal_point)

            RSI_5m_C0 = round(rsi_5.iloc[-1], decimal_point_rsi)
            RSI_15m_C0 = round(rsi_15.iloc[-1], decimal_point_rsi)
            RSI_60m_C0 = round(rsi_60.iloc[-1], decimal_point_rsi)
            RSI_min = 55.00
            RSI_max = 75.00

            Vol_5m_C0 = minute_5_bars['Volume'].iloc[-1]
            Vol_threshold = 50

            market_price = round(minute_5_bars['Close'].iloc[-1], decimal_point)

            ## -- ENTRY -- ##
            if symbol not in existing_position_symbols:

                if symbol not in existing_order_symbols:

                    # Set Entry Limit not over 10.0% above EMA
                    # LUNR 30 Aug 2024 (Entry price = 5.68, EMA = 4.97 --> 14.3% above EMA --> potential profit -2.3%)
                    # CHWY 28 Aug 2024 (Entry price = 28.89, EMA = 26.45 --> 9.22% above EMA --> potential profit 5.2%)
                    # VRAX 28 Aug 2024 (Entry price = 6.11, EMA = 5.02 --> 21.7% above EMA --> potential profit 18.5%)

                    Entry_Limit_60m = E_60m_C0*1.10
                    Entry_Limit_EMA10_1d = EMA_10d*1.05

                    # Entry Position 0: 60MX0 for Breakout-5
                    if M_60m_C0 > 0.0000 and M_60m_P1 < 0.0000 and H_60m_C0 > 0.0000 and H_1d_C0 > 0.0000:
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
                        # REAL (5 Nov 2024) (M_60m_P1 = 0.0490) Entry 4.17 --> 26 Dec 2024 at 11.05 (+165%)

                        # Also add M_60_P1 limit to set area that 60MXU sometime happened just above 0-line, which seem to be a valid point
                        limit_60MXU = 0.1000
                        if M_60m_P1 < limit_60MXU:
                            print(f" - It's buy signal for Entry Position 0: 60MXU")
                            print(f" H_60m_P2 = {H_60m_P2} < 0.0000")
                            print(f" H_60m_P1 = {H_60m_P1} > 0.0000")
                            print(f" H_60m_C0 = {H_60m_C0} > 0.0000")
                            print(f" M_60m_P1 = {M_60m_P1} < 0.1000")

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

                    # Entry Position 0: 5MX0
                    elif M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_5m_C0 > 0.0000 and H_15m_C0 > 0.0000 and 0.0200 > M_60m_C0 > 0.0000 and Vol_5m_C0 > Vol_threshold:
                        # CMO 19 Mar 2024 Entry 1.11
                        # CMO 1D indicator; EMA10 = 1.09 --> 1.11 (2.0% above EMA10)
                        # CMO 60m indicator; M_60m_C0 = 0.0100
                        # CMO 15m indicator; H_15m_C0 > 0.0000
                        print(f" - It's buy signal for Entry Position 0: 5MX0") 

                        # Check Entry Position Limit
                        if EMA_10d < entry_price < Entry_Limit_EMA10_1d:
                            print(f" - The entry price is in the EMA10-1d Entry Limit")         
                            quantity = calculate_quantity(market_price)
                            place_buy_order(symbol, quantity)
                        else:
                            print(f" - The entry price is over the EMA10-1d Entry Limit")

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

                        # Calculate trailing stop price at -35.0%
                        trailing_stop_price = highest_price * (1 - TRAILING_STOP_PERCENTAGE)

                        # Check if current market price is below trailing stop price
                        # Initially set trailing stop price at -5.0%
                        # NIO 24 Sep 2024 -7.25% from high missed 19.5% in on 27 Sep --> add M_60m_C0 < 0.0000        
                        # However, VERI 11 Oct 2024 -35% but M_60m_C0 > 0.0000 
                        # To optimize the signal (relative) + percentage (absolute), the trailing stop change to -8.0%
                        # and the M_60m_C0 < 0.0000 is removed
                        # Dec 7 2024, Based on proper breakout and 
                        # IONQ (TP(>50%): If TP with 60MX0-, TP = 80% and on Dec 7 2024 TP = 337%) 
                        # BBAI (TSH(8%): TP = 8.60%, If TSH(>8%): TP = 38%  
                        # QBTS (TSH(8%): TP = 1.73%, If TSH(35%): TP = 193% with 60MX0-)
                        # So, TSH 8% --> 35%
                        if market_price <= trailing_stop_price and market_value > cost:
                            print(f" - Trailing stop hit. Placing sell order for {symbol} at {market_price}.\n")
                            place_sell_order(symbol, quantity)   

                    except Exception as e:
                        print(f" - The error as {e}")

                    # Strategy 0 taking profit when 5m indicators are indicating a sell signal            
                    if is_bearish_pin_bar(Open_5m_C0, High_5m_C0, Low_5m_C0, Close_5m_C0):
                        print("Bearish pin bar detected in current 5-min candle.")
                        if market_value > cost:
                            print(f" - It's taking-profit for with 5-min sell signal")
                            place_sell_order(symbol, quantity)
                        else:
                            print(f" - It's taking-profit for with 5-min sell signal but the market value is lower than cost")
                            print(f" - If the stop-loss doesn't hit, keep checking.")

                    # Strategy 1 taking profit for big winner             
                    elif H_1d_C0 < 0.0000 and market_value > cost:
                        # QBTS 13 Nov 2024 Entry with 60MXU at 1.73 Exit with TSH(8%) at 1.76 and missed 503% on 18 Dec 2024
                        # IONQ 02 Oct 2024 Entry with 60MXO at 8.67 Exit with TP(>50%) at 13.46 and missed 405% on 17 Dec 2024
                        print(f" - It's taking-profit for big winner")
                        place_sell_order(symbol, quantity)

                    # # Strategy 1 for taking profit by signal (relative) + percentage (absolute)             
                    # if M_60m_C0 < 0.0000 and H_60m_C0 < 0.0000 and market_value > cost:
                    #     # VRAX 29 Aug 2024 turn 20% profit down to 5% cut loss (not updated) --> Fixed by using Trailing Stop
                    #     # IONQ 18 Oct 2024 sold when the profit over 50% but stock keep going up to 95% 
                    #     # It's need to be the room to fully taking the big win
                    #     # Change from market_value > (1.50 * cost) to M60X0-
                    #     print(f" - It's taking-profit signal with M60X0-.")
                    #     place_sell_order(symbol, quantity)

                    # Strategy 0 for cutting loss for 5MX0 stratergy
                    elif market_price < EMA_10d:
                        print(f" - It's cut-loss signal with Strategy 0, {symbol} price is {market_price} below EMA10-1d of {EMA_10d}.")
                        place_sell_order(symbol, quantity)

                    # Strategy 2 for cutting loss should not greater than 5%
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
                        print(f" - It's cut-loss signal with Strategy 2 (-5.0%).")
                        place_sell_order(symbol, quantity)

                    # Strategy 3 for false 60MX0 and allow 3% for variation (F60MX0)
                    elif M_60m_C0 < 0.0000 and H_60m_C0 > 0.0000 and market_value < (0.97 * cost):
                        print(f" - It's cut-loss signal with Strategy 3 (F60MX0).")
                        print(f" - M_60m_C0 = {M_60m_C0} < 0.0000")
                        print(f" - H_60m_C0 = {H_60m_C0} > 0.0000")                
                        place_sell_order(symbol, quantity)

                    # Strategy 4 for weak up trend: price below ema_10
                    elif C_1d_C0 < EMA_10d and market_value < cost:
                        # NCV 18-23 Oct 2024
                        # Entry with 60MXU
                        print(f" - It's cut-loss signal with Strategy 4 (Price below EMA).")
                        place_sell_order(symbol, quantity)

                    # Strategy 5 for weak up trend: 60MX0-
                    elif M_60m_C0 < 0.0000 and H_60m_C0 < 0.0000 and market_value < cost:
                        # NCV 18-23 Oct 2024
                        # Entry with 60MXU
                        print(f" - It's cut-loss signal with Strategy 5 (60MX0-).")
                        place_sell_order(symbol, quantity)

                    # Strategy 6 for weak up trend: H_1d_C0 < 0.0000 and allow 3% for variation (F1DXD)
                    elif H_1d_C0 < 0.0000 and C_1d_C0 < EMA_10d and market_value < (0.97 * cost):
                        # NCV 18-23 Oct 2024
                        # Entry with 60MXU
                        print(f" - It's cut-loss signal with Strategy 6 (1DXD).")
                        place_sell_order(symbol, quantity)

                    # Strategy END
                    else:
                        print(" - No sell signal yet\n")

                else:
                    print(f" - The order of stock {symbol} is placed\n")

            else: 
                print(" - It's already been traded for today.\n")

    # Market is changing direction
    else:
        print(f"The market is changing direction")
        print(f"Update at {datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')}\n")

else:
    print(f"The market is closed")

