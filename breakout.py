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
            M_1d_C0_market = round(macd_1_market['MACD_12_26_9'].iloc[-1], decimal_point)
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
    elif EMA_10d_market is not None and C_1d_C0_market is not None and H_1d_C0_market is not None and C_1d_C0_market > EMA_10d_market and (H_1d_C0_market > 0.0000 or M_1d_C0_market > 0.0000):
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
            minute_5_bars = get_alpaca_bars(symbol, TimeFrame.Minute, start=datetime.now() - timedelta(days=30))
            day_1_bars = get_alpaca_bars(symbol, TimeFrame.Day, start=datetime.now() - timedelta(days=180))
            # Check for empty DataFrames
            if any(df.empty or 'Close' not in df.columns for df in [minute_5_bars, day_1_bars]):
                print(f"Missing or incomplete data for {symbol}, skipping.")
                continue

            EMA_10d_bars = day_1_bars['Close'].ewm(span=10, adjust=False).mean()
            EMA_10d = EMA_10d_bars.iloc[-1]
            print(f"Last close of day_1_bars of {symbol}: {day_1_bars['Close'].iloc[-1]}")

            # --- Fix for pandas_ta: set columns to lowercase before indicator calculation ---
            minute_5_bars.columns = [col.lower() for col in minute_5_bars.columns]
            day_1_bars.columns = [col.lower() for col in day_1_bars.columns]
            macd_5 = minute_5_bars.ta.macd()
            macd_1 = day_1_bars.ta.macd()
            rsi_5 = minute_5_bars.ta.rsi()
            # Restore Title Case for rest of code
            minute_5_bars.columns = [col.title() for col in minute_5_bars.columns]
            day_1_bars.columns = [col.title() for col in day_1_bars.columns]

            decimal_point = 4
            decimal_point_rsi = 2
            decimal_point_ema = 2

            # Candle Stick
            H_1d_C0 = round(macd_1['MACDh_12_26_9'].iloc[-1], decimal_point) if 'MACDh_12_26_9' in macd_1.columns else None

            M_5m_C0 = round(macd_5['MACD_12_26_9'].iloc[-1], decimal_point)
            M_5m_P1 = round(macd_5['MACD_12_26_9'].iloc[-2], decimal_point)
            H_5m_C0 = round(macd_5['MACDh_12_26_9'].iloc[-1], decimal_point)
            H_5m_P1 = round(macd_5['MACDh_12_26_9'].iloc[-2], decimal_point)
            H_5m_P2 = round(macd_5['MACDh_12_26_9'].iloc[-3], decimal_point)
            Open_5m_C0 = round(minute_5_bars['Open'].iloc[-1], decimal_point)
            Close_5m_C0 = round(minute_5_bars['Close'].iloc[-1], decimal_point)
            High_5m_C0 = round(minute_5_bars['High'].iloc[-1], decimal_point)
            Low_5m_C0 = round(minute_5_bars['Low'].iloc[-1], decimal_point)

            RSI_5m_C0 = round(rsi_5.iloc[-1], decimal_point_rsi)
            RSI_min = 55.00
            RSI_max = 75.00

            Vol_5m_C0 = minute_5_bars['Volume'].iloc[-1]
            Vol_threshold = 50

            market_price = round(minute_5_bars['Close'].iloc[-1], decimal_point)
            maximum_limit_below_ema10 = 0.97 * EMA_10d # 3.0% below EMA_10-1d

            ## -- ENTRY -- ##
            if symbol not in existing_position_symbols:

                if symbol not in existing_order_symbols:
                    Upper_Limit_EMA10_1d = EMA_10d*1.05 # 5.0% above EMA_10_1d
                    Lower_Limit_EMA10_1d = EMA_10d*0.98 # 2.0% below EMA_10_1d

                    # Entry Position 0: 5MX0
                    if M_5m_C0 > 0.0000 and M_5m_P1 < 0.0000 and H_5m_C0 > 0.0000 and Vol_5m_C0 > Vol_threshold and RSI_min < RSI_5m_C0 < RSI_max:
                        print(f" - It's buy signal for Entry Position 0: 5MX0") 
                        # Collect other indicators for trading model development
                        print(f"Collecting other indicators")
                        # 5m indicators
                        print(f" RSI_5m_C0 = {RSI_5m_C0}")
                        print(f" M_5m_C0 = {M_5m_C0}, M_5m_P1 = {M_5m_P1}")
                        print(f" H_5m_C0 = {H_5m_C0}")
                        # 1d indicator
                        print(f" EMA_10d = {EMA_10d}")
                        print(f" H_1d_C0 = {H_1d_C0}")

                        # Check Entry Position in The Entry Range
                        if Lower_Limit_EMA10_1d < Close_5m_C0 < Upper_Limit_EMA10_1d:
                            percentage_from_ema10_1d = ((Close_5m_C0 - EMA_10d) / EMA_10d) * 100
                            print(f" - The {symbol} price: {Close_5m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                            quantity = calculate_quantity(market_price)
                            place_buy_order(symbol, quantity)
                        else:
                            print(f" - The {symbol} price is over the EMA10-1d Entry Range")

                    # End of Entry Options
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

                        # Trailing Stop
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
                        if market_price <= trailing_stop_price and market_value > cost:
                            print(f" - Trailing stop hit. Placing sell order for {symbol} at {market_price}.\n")
                            place_sell_order(symbol, quantity)   

                    except Exception as e:
                        print(f" - The error as {e}")

                    # Strategy 1 for taking profit
                    if market_value > cost:
                        if entry_d != current_date:
                            print(f" - Taking-profit for with 5-min")
                            place_sell_order(symbol, quantity)
                            # if is_bearish_pin_bar(Open_5m_C0, High_5m_C0, Low_5m_C0, Close_5m_C0):
                        else:
                            print(f" - The position of {symbol} is opened today, avoid day-trade-count limit.\n")
                    
                    # Strategy 2 for cutting loss
                    elif market_price < maximum_limit_below_ema10:
                        print(f" - It's cut-loss signal, {symbol} price is {market_price} over the maximum limit below EMA10-1d of {maximum_limit_below_ema10}.")
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

