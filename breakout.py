import config, requests
import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit  # Add TimeFrameUnit for custom intervals
from helpers import calculate_quantity
import pytz
import pandas_ta as ta
import pandas as pd
import alpaca_trade_api as tradeapi
import datetime as dt

# --- maximize_5MX0: Strategy for maximizing profit on 5MX0 exit ---
def maximize_5MX0(Close_5m_C0, Open_5m_C0, Close_5m_P1, M_5m_C0, M_5m_P1, M_5m_P2, H_5m_C0, H_5m_P1, symbol, quantity):
    """
    Strategy 1.1 for maximizing profit on 5MX0 exit.
    Exits position if certain MACD/price action conditions are met.
    Defensive: All arguments must be defined before calling this function.
    """
    try:
        # Example logic: exit if MACD momentum reverses or price action weakens
        # (You can adjust these rules as needed for your strategy)
        if Close_5m_C0 < Open_5m_C0:
            print(f"Red candle detected. Then check with the previous close")
            if Close_5m_C0 < Close_5m_P1:
                print(f"Red candle detected and close lower than previous close.")
                print(f"Check MACD Momentum Reversal conditions")

                # MACD momentum reversal condition 1 (MMR1)
                # 1. Check MACD
                if M_5m_C0 >= M_5m_P1 and M_5m_C0 > 0.0000:
                    print(f"Check MMR1")
                    print(f"1. Check MACD: M_5m_C0 >= M_5m_P1, then check Histogram.")

                    # 2. Check Histogram
                    if H_5m_C0 < H_5m_P1 and H_5m_C0 > 0.0000:
                        print(f"2. Check Histogram: H_5m_C0 < H_5m_P1, MACD momentum shows the reversal, then check the profit.")
                        print(f"MMR1 met")
                        place_sell_order(symbol, quantity)
                    else:
                        print(f"H_5m_C0 not less than H_5m_P1, MMR1 not met yet.")

                # MACD momentum reversal condition 2 (MMR2)
                # 1. Check MACD
                elif M_5m_P1 > M_5m_C0 and M_5m_P1 > M_5m_P2 and M_5m_P1 > 0.0000:
                    print(f"Check MMR2")
                    print(f"1. Check MACD: M_5m_P1 > M_5m_C0 and M_5m_P1 > M_5m_P2, then check Histogram.")
                
                    # 2. Check Histogram
                    if H_5m_C0 < H_5m_P1 and H_5m_C0 > 0.0000:
                        print(f"2. Check Histogram: H_5m_C0 < H_5m_P1, MACD momentum shows the reversal, then check the profit.")
                        print(f"MMR2 met")
                        place_sell_order(symbol, quantity)
                    else:
                        print(f"H_5m_C0 not less than H_5m_P1, MMR2 not met yet.")

                # MMR not met
                else:
                    print(f"MMR not met yet")
            else:
                print(f"Red candle detected but close higher than previous close.")
        
        else:
            print(f"Red candle not detected, no action taken for {symbol}.")

    except Exception as e:
        print(f"Error in maximize_5MX0 for {symbol}: {e}")

# --- maximize_60MXU: Strategy for maximizing profit on 60MXU exit ---
def maximize_60MXU(Close_60m_C0, Open_60m_C0, Close_60m_P1, M_60m_C0, M_60m_P1, M_60m_P2, H_60m_C0, H_60m_P1, symbol, quantity):
    try:
        # Example logic: exit if MACD momentum reverses or price action weakens
        if Close_60m_C0 < Open_60m_C0:
            print(f"Red candle detected. Then check with the previous close")
            if Close_60m_C0 < Close_60m_P1:
                print(f"Red candle detected and close lower than previous close.")
                print(f"Check MACD Momentum Reversal conditions")

                # MACD momentum reversal condition 1 (MMR1)
                # 1. Check MACD
                if M_60m_C0 >= M_60m_P1 and M_60m_C0 > 0.0000:
                    print(f"Check MMR1")
                    print(f"1. Check MACD: M_60m_C0 >= M_60m_P1, then check Histogram.")

                    # 2. Check Histogram
                    if H_60m_C0 < H_60m_P1 and H_60m_C0 > 0.0000:
                        print(f"2. Check Histogram: H_60m_C0 < H_60m_P1, MACD momentum shows the reversal, then check the profit.")
                        print(f"MMR1 met")
                        place_sell_order(symbol, quantity)
                    else:
                        print(f"H_60m_C0 not less than H_60m_P1, MMR1 not met yet.")

                # MACD momentum reversal condition 2 (MMR2)
                # 1. Check MACD
                elif M_60m_P1 > M_60m_C0 and M_60m_P1 > M_60m_P2 and M_60m_P1 > 0.0000:
                    print(f"Check MMR2")
                    print(f"1. Check MACD: M_60m_P1 > M_60m_C0 and M_60m_P1 > M_60m_P2, then check Histogram.")
                
                    # 2. Check Histogram
                    if H_60m_C0 < H_60m_P1 and H_60m_C0 > 0.0000:
                        print(f"2. Check Histogram: H_60m_C0 < H_60m_P1, MACD momentum shows the reversal, then check the profit.")
                        print(f"MMR2 met")
                        place_sell_order(symbol, quantity)
                    else:
                        print(f"H_60m_C0 not less than H_60m_P1, MMR2 not met yet.")
                
                # MMR not met
                else:
                    print(f"MMR not met yet")

            else:
                print(f"Red candle detected but close higher than previous close.")
        else:
            print(f"Red candle not detected, no action taken for {symbol}.")

    except Exception as e:
        print(f"Error in maximize_60MXU for {symbol}: {e}")

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
def place_buy_order(symbol, quantity, close=None, ema_10=None, macd=None, macd_histogram=None, rsi=None):
    entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Export tracking info before attempting to buy
    if close is not None and ema_10 is not None and macd is not None and macd_histogram is not None and rsi is not None:
        export_60m_entry_tracking(symbol, entry_time, close, ema_10, macd, macd_histogram, rsi)
    try:
        api.submit_order(
            symbol=symbol,
            side='buy',
            type='market',
            qty=quantity,
            time_in_force='gtc'
        )
        print(f" - Placing buy order for {symbol} at {close}.")
    except Exception as e:
        print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---")

# Function to export 60-min entry tracking (called regardless of buy order success)
def export_60m_entry_tracking(symbol, entry_time, close, ema_10, macd, macd_histogram, rsi):
    print(f"TRACK_60M_ENTRY,{entry_time},{symbol},{close},{ema_10},{macd},{macd_histogram},{rsi}")

# Function to export market condition tracking (called every run)
def export_market_condition_tracking(run_time, spy_close, spy_ema10, spy_macdh):
    print(f"TRACK_MARKET_CONDITION,{run_time},{spy_close},{spy_ema10},{spy_macdh}")

# Function to get entry date
def get_entry_date(symbol):
    orders = api.list_orders(status='all', limit=500)
    for order in orders:
        if order.symbol == symbol and order.side == 'buy' and order.filled_at is not None:
            return order.filled_at
    return None

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
                minute_5_bars = get_alpaca_bars(symbol, TimeFrame(5, TimeFrameUnit.Minute), start=datetime.now() - timedelta(days=5))
                day_1_bars = get_alpaca_bars(symbol, TimeFrame.Day, start=datetime.now() - timedelta(days=180))
                if day_1_bars.empty or 'Close' not in day_1_bars.columns:
                    print(f"No daily bars for {symbol}, skipping.")
                    continue
                # --- Fix for pandas_ta: set columns to lowercase before indicator calculation ---
                minute_5_bars.columns = [col.lower() for col in minute_5_bars.columns]
                day_1_bars.columns = [col.lower() for col in day_1_bars.columns]

                # Filter minute_5_bars to only include bars where the time is a market open time (e.g., 09:30, 09:35, ...)
                # For US equities, market open is typically 09:30 to 16:00 Eastern Time
                # We'll keep only bars where the minute is divisible by 5 and the hour/minute is within regular session

                import pytz
                us_eastern = pytz.timezone('America/New_York')
                minute_5_bars_local = minute_5_bars.copy()
                # --- Ensure index is DatetimeIndex for timezone conversion and filtering ---
                minute_5_bars_local = minute_5_bars.copy()
                if isinstance(minute_5_bars_local.index, pd.MultiIndex):
                    # Assume timestamp is the last level
                    minute_5_bars_local.index = minute_5_bars_local.index.get_level_values(-1)

                # Now index is DatetimeIndex, safe to tz_convert
                minute_5_bars_local.index = minute_5_bars_local.index.tz_convert(us_eastern)

                # Filter for regular session (09:30 to 16:00)
                def is_market_open_bar(ts):
                    return (ts.hour > 9 or (ts.hour == 9 and ts.minute >= 30)) and (ts.hour < 16)

                minute_5_bars_open = minute_5_bars_local[minute_5_bars_local.index.map(is_market_open_bar)]

                # Ensure all columns are lowercase for price data
                minute_5_bars_open.columns = [col.lower() for col in minute_5_bars_open.columns]

                # Calculate MACD (pandas_ta always outputs Title Case columns)
                macd_5 = minute_5_bars_open.ta.macd(fast=12, slow=26, signal=9, mamode='ema')
                # print("\n--- pandas_ta MACD (12,26,9, ema) last 10 values (market open only) ---")
                # if not macd_5.empty:
                #     print(macd_5[['MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9']].tail(10))
                # else:
                #     print("MACD DataFrame is empty!")

                macd_1 = day_1_bars.ta.macd()
                decimal_point = 4
                H_1d_C0 = round(macd_1['MACDh_12_26_9'].iloc[-1], decimal_point)
                market_price = round(minute_5_bars['close'].iloc[-1], decimal_point) if not minute_5_bars.empty else 0

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
    elif C_1d_C0_market > EMA_10d_market and ((H_1d_C0_market > 0.0000) or (H_1d_C0_market < 0.0000 and M_1d_C0_market > 0.0000)):
        print("Market is good to trade.")
        print(f"SPY is above EMA_10 ({C_1d_C0_market} > {EMA_10d_market}) and H_1d_C0_market ({H_1d_C0_market}) > 0.0000.\n")
        symbols_5MX0_AB = config.BREAKOUT_SYMBOLS_5MX0_AB

        current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
        current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")

        orders = api.list_orders(status='all', after=current_date)
        existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']
        buy_order_symbols = [order.symbol for order in orders if order.side == 'buy' and order.status != 'canceled']
        positions = api.list_positions()
        existing_position_symbols = [position.symbol for position in positions]
        print(f'{current_time}\n')

        # Breakout Strategy Model-5MX0-AB
        for symbol in symbols_5MX0_AB:
            print(f'\n{symbol}_{current_time}')
            # Fetch bars from Alpaca
            minute_5_bars = get_alpaca_bars(symbol, TimeFrame(5, TimeFrameUnit.Minute), start=datetime.now() - timedelta(days=5))
            minute_60_bars = get_alpaca_bars(symbol, TimeFrame(1, TimeFrameUnit.Hour), start=datetime.now() - timedelta(days=60))
            day_1_bars = get_alpaca_bars(symbol, TimeFrame.Day, start=datetime.now() - timedelta(days=180))
            # Check for empty DataFrames
            if any(df.empty or 'Close' not in df.columns for df in [minute_5_bars, day_1_bars]):
                print(f"Missing or incomplete data for {symbol}, skipping.")
                continue

            EMA_10d_bars = day_1_bars['Close'].ewm(span=10, adjust=False).mean()
            EMA_10d = round(EMA_10d_bars.iloc[-1], 2)

            # --- Fix for pandas_ta: set columns to lowercase before indicator calculation ---
            minute_5_bars.columns = [col.lower() for col in minute_5_bars.columns]
            day_1_bars.columns = [col.lower() for col in day_1_bars.columns]

            # Filter minute_5_bars to only include bars where the time is a market open time (e.g., 09:30, 09:35, ...)
            # For US equities, market open is typically 09:30 to 16:00 Eastern Time
            # We'll keep only bars where the minute is divisible by 5 and the hour/minute is within regular session

            import pytz
            us_eastern = pytz.timezone('America/New_York')
            minute_5_bars_local = minute_5_bars.copy()
            # --- Ensure index is DatetimeIndex for timezone conversion and filtering ---
            minute_5_bars_local = minute_5_bars.copy()
            if isinstance(minute_5_bars_local.index, pd.MultiIndex):
                # Assume timestamp is the last level
                minute_5_bars_local.index = minute_5_bars_local.index.get_level_values(-1)

            # Now index is DatetimeIndex, safe to tz_convert
            minute_5_bars_local.index = minute_5_bars_local.index.tz_convert(us_eastern)

            # Filter for regular session (09:30 to 16:00)
            def is_market_open_bar(ts):
                return (ts.hour > 9 or (ts.hour == 9 and ts.minute >= 30)) and (ts.hour < 16)

            minute_5_bars_open = minute_5_bars_local[minute_5_bars_local.index.map(is_market_open_bar)]

            # Ensure all columns are lowercase for price data
            minute_5_bars_open.columns = [col.lower() for col in minute_5_bars_open.columns]

            # Calculate MACD (pandas_ta always outputs Title Case columns)
            macd_5 = minute_5_bars_open.ta.macd(fast=12, slow=26, signal=9, mamode='ema')           
            macd_1 = day_1_bars.ta.macd()
            rsi_5 = minute_5_bars.ta.rsi()

            decimal_point = 4
            decimal_point_rsi = 2
            decimal_point_ema = 2

            # Candle Stick
            M_5m_C0 = round(macd_5['MACD_12_26_9'].iloc[-1], decimal_point)
            M_5m_P1 = round(macd_5['MACD_12_26_9'].iloc[-2], decimal_point)
            M_5m_P2 = round(macd_5['MACD_12_26_9'].iloc[-3], decimal_point)
            H_5m_C0 = round(macd_5['MACDh_12_26_9'].iloc[-1], decimal_point)
            H_5m_P1 = round(macd_5['MACDh_12_26_9'].iloc[-2], decimal_point)
            H_5m_P2 = round(macd_5['MACDh_12_26_9'].iloc[-3], decimal_point)
            # --- Fix for pandas_ta: set columns to lowercase before indicator calculation ---
            minute_5_bars.columns = [col.lower() for col in minute_5_bars.columns]
            # Defensive: print columns if 'open' is missing
            if 'open' not in minute_5_bars.columns:
                print(f"[DEBUG] minute_5_bars columns before access: {list(minute_5_bars.columns)}")
            # Defensive: check for 'open' before accessing
            Open_5m_C0 = round(minute_5_bars['open'].iloc[-1], decimal_point) if 'open' in minute_5_bars.columns else None
            if Open_5m_C0 is None:
                print("Warning: 'open' column missing in minute_5_bars! Skipping this symbol.")
                continue
            Close_5m_C0 = round(minute_5_bars['close'].iloc[-1], decimal_point)
            Close_5m_P1 = round(minute_5_bars['close'].iloc[-2], decimal_point)
            High_5m_C0 = round(minute_5_bars['high'].iloc[-1], decimal_point)
            Low_5m_C0 = round(minute_5_bars['low'].iloc[-1], decimal_point)

            RSI_5m_C0 = round(rsi_5.iloc[-1], decimal_point_rsi)
            RSI_min = 55.00
            RSI_max = 75.00

            Vol_5m_C0 = minute_5_bars['volume'].iloc[-1]
            Vol_threshold = 50

         # Prepare minute_60_bars_local and filter for market open bars (if needed)
            minute_60_bars_local = minute_60_bars.copy()
            if isinstance(minute_60_bars_local.index, pd.MultiIndex):
                minute_60_bars_local.index = minute_60_bars_local.index.get_level_values(-1)
            
            minute_60_bars_local.index = minute_60_bars_local.index.tz_convert(us_eastern)

            def is_market_open_bar_60(ts):
                return (ts.hour > 9 or (ts.hour == 9 and ts.minute >= 30)) and (ts.hour < 16)

            minute_60_bars_open = minute_60_bars_local[minute_60_bars_local.index.map(is_market_open_bar_60)]

            # Set columns to lowercase for indicator calculation
            minute_60_bars_open.columns = [col.lower() for col in minute_60_bars_open.columns]

            # --- 60-min indicators ---
            EMA_10_60m_bars = minute_60_bars_open['close'].ewm(span=10, adjust=False).mean()
            EMA_10_60m = round(EMA_10_60m_bars.iloc[-1], decimal_point)
            macd_60 = minute_60_bars_open.ta.macd(fast=12, slow=26, signal=9, mamode='ema')
            rsi_60 = minute_60_bars_open.ta.rsi()

            # 60-min MACD and RSI values
            M_60m_C0 = round(macd_60['MACD_12_26_9'].iloc[-1], decimal_point)
            M_60m_P1 = round(macd_60['MACD_12_26_9'].iloc[-2], decimal_point)
            H_60m_C0 = round(macd_60['MACDh_12_26_9'].iloc[-1], decimal_point)
            H_60m_P1 = round(macd_60['MACDh_12_26_9'].iloc[-2], decimal_point)
            H_60m_P2 = round(macd_60['MACDh_12_26_9'].iloc[-3], decimal_point)
            RSI_60m_C0 = round(rsi_60.iloc[-1], decimal_point)

            # 60-min candle stick
            Open_60m_C0 = round(minute_60_bars_open['open'].iloc[-1], decimal_point) 
            Close_60m_C0 = round(minute_60_bars_open['close'].iloc[-1], decimal_point)
            Open_60m_P1 = round(minute_60_bars_open['open'].iloc[-2], decimal_point)
            Close_60m_P1 = round(minute_60_bars_open['close'].iloc[-2], decimal_point)
            Close_60m_P2 = round(minute_60_bars_open['close'].iloc[-3], decimal_point)
            Close_60m_P3 = round(minute_60_bars_open['close'].iloc[-4], decimal_point)
            Close_60m_P4 = round(minute_60_bars_open['close'].iloc[-5], decimal_point)

            # --- 1-day indicators ---
            H_1d_C0 = round(macd_1['MACDh_12_26_9'].iloc[-1], decimal_point) if 'MACDh_12_26_9' in macd_1.columns else None

            market_price = round(minute_5_bars['close'].iloc[-1], decimal_point)
            # maximum_limit_below_ema10 = round(0.95 * EMA_10d, decimal_point) # 5.0% below EMA_10-1d

            ## -- ENTRY -- ##
            if symbol not in existing_position_symbols:

                if symbol not in existing_order_symbols:
                    Upper_Limit_EMA10_1d = round(EMA_10d*1.05, decimal_point) # 5.0% above EMA_10_1d
                    Lower_Limit_EMA10_1d = round(EMA_10d*0.97, decimal_point) # 3.0% below EMA_10_1d
                    percentage_from_ema10_1d = ((Close_5m_C0 - EMA_10d) / EMA_10d) * 100

                    Upper_Limit_EMA10_60m = round(EMA_10_60m*1.05, decimal_point) # 5.0% above EMA_10-60m
                    percentage_from_ema10_60m = ((Close_60m_C0 - EMA_10_60m) / EMA_10_60m) * 100

                    # Entry Position: 60MXU
                    if H_60m_C0 > 0.0000 and H_60m_P1 < 0.0000:
                        print(f" - It's buy signal for 60MXU.")
                        print(f" - The 60-min price: {Close_60m_C0} is above EMA_10-60m: {EMA_10_60m}")
                        print(f" - M_60m_C0: {M_60m_C0}, M_60m_P1: {M_60m_P1}, H_60m_C0: {H_60m_C0}, H_60m_P1: {H_60m_P1}, RSI_60m_C0: {RSI_60m_C0}")
                        
                        # --- Tracking Port Print for 60-min Entry ---
                        print(f"TRACK_60M_ENTRY,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{Close_60m_C0},{EMA_10_60m},{M_60m_C0},{H_60m_C0},{RSI_60m_C0}")

                        # PXU_C0
                        if Close_60m_C0 > EMA_10_60m and Close_60m_P1 < EMA_10_60m:
                            print(f" - 60MXU-PXU_C0 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_5m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_5m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")

                        # PXU_P1
                        elif Close_60m_C0 > EMA_10_60m and Close_60m_P1 > EMA_10_60m and Close_60m_P2 < EMA_10_60m:
                            print(f" - 60MXU-PXU_P1 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_5m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_5m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")

                        # PXU_P2
                        elif Close_60m_C0 > EMA_10_60m and Close_60m_P1 > EMA_10_60m and Close_60m_P2 > EMA_10_60m and Close_60m_P3 < EMA_10_60m:
                            print(f" - 60MXU-PXU_P2 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_5m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_5m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")

                        # PXU_P3
                        elif Close_60m_C0 > EMA_10_60m and Close_60m_P1 > EMA_10_60m and Close_60m_P2 > EMA_10_60m and Close_60m_P3 > EMA_10_60m and Close_60m_P4 < EMA_10_60m:
                            print(f" - 60MXU-PXU_P3 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_5m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_5m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")
                    
                    # Entry Position: 60PXU
                    elif Close_60m_C0 > EMA_10_60m and Close_60m_P1 < EMA_10_60m:
                        print(f" - It's buy signal for 60PXU.")
                        print(f" - The 60-min price: {Close_60m_C0} is above EMA_10-60m: {EMA_10_60m}")
                        print(f" - M_60m_C0: {M_60m_C0}, M_60m_P1: {M_60m_P1}, H_60m_C0: {H_60m_C0}, H_60m_P1: {H_60m_P1}, RSI_60m_C0: {RSI_60m_C0}")
                        
                        # --- Tracking Port Print for 60-min Entry ---
                        print(f"TRACK_60M_ENTRY,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{Close_60m_C0},{EMA_10_60m},{M_60m_C0},{H_60m_C0},{RSI_60m_C0}")
                        
                        # 60MXU_P1
                        if H_60m_C0 > 0.0000 and H_60m_P1 > 0.0000 and H_60m_P2 < 0.0000:
                            print(f" - 60PXU detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_5m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_5m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")
                    else:
                        print(f" - The 60-min indicators are not good to trade for {symbol}")
                        print(f" - The 60-min price: {Close_60m_C0} is below EMA_10-60m: {EMA_10_60m}")

                else:
                    print(f' - The order of stock {symbol} is placed\n')

            ## -- EXIT -- ##
            elif symbol in existing_position_symbols:

                if symbol not in existing_order_symbols or symbol in buy_order_symbols:

                    # Getting Data
                    print(f" - Already in the position")
                    position = api.get_position(symbol)
                    quantity = position.qty
                    entry_price = float(position.avg_entry_price)
                    market_value = abs(float(position.market_value))
                    cost = abs(float(position.cost_basis))
                    entry_date_g = get_entry_date(symbol)
                    entry_d = entry_date_g.astimezone(pytz.timezone('America/New_York')).date()
                    current_date = dt.datetime.now(pytz.timezone('America/New_York')).date()

                    # Current profit/loss
                    print(f" - Current profit/loss: {((market_value - cost) / cost) * 100:.2f}%")
                    
                    # Strategy 1 for 5MX0 taking profit (maximize_5MX0)
                    if market_value > (1.005 * cost):
                        print(f" - It's profit taking signal, profit > 0.5%.")
                        maximize_5MX0(Close_5m_C0, Open_5m_C0, Close_5m_P1, M_5m_C0, M_5m_P1, M_5m_P2, H_5m_C0, H_5m_P1, symbol, quantity)

                    # Strategy 1-TP for 60MXU taking profit (maximize_60MXU)
                    if market_value > (1.005 * cost):
                        print(f" - It's profit taking signal for 60MXU, profit > 0.5%.")
                        maximize_60MXU(Close_60m_C0, Open_60m_C0, Close_60m_P1, M_60m_C0, M_60m_P1, H_60m_C0, H_60m_P1, symbol, quantity)

                    # Strategy 1-CL for 60MXU cutting loss (cut_loss_60MXU)
                    elif H_60m_C0 < 0.0000 and H_60m_P1 > 0.0000:
                        print(f" - It's cut-loss signal for 60MXU, H_60m_C0 < 0.0000 and H_60m_P1 > 0.0000.")
                        place_sell_order(symbol, quantity)
                    
                    # Strategy 2 for cutting loss
                    elif market_value < (0.95 * cost):
                        print(f" - It's cut-loss signal, loss > 5%.")
                        place_sell_order(symbol, quantity)

                    # Strategy 3: Exit by timing (after 2 trading days, excluding weekends/holidays)
                    elif entry_d is not None:
                        # Get all trading dates between entry_d and current_date
                        all_days = pd.date_range(entry_d, current_date)
                        # Fetch market calendar from Alpaca
                        calendar = api.get_calendar(start=entry_d.strftime('%Y-%m-%d'), end=current_date.strftime('%Y-%m-%d'))
                        trading_dates = [day.date.date() if hasattr(day.date, 'date') else day.date for day in calendar]
                        # Find the index of entry_d in trading_dates
                        if entry_d in trading_dates:
                            entry_idx = trading_dates.index(entry_d)
                            # Check if current_date is at least two trading days after entry_d
                            if len(trading_dates) > entry_idx + 3 and current_date >= trading_dates[entry_idx + 2]:
                                print("Strategy 3: Exiting by timing (after 2 trading days)")
                                place_sell_order(symbol, quantity)
                        else:
                            print(f"Entry date {entry_d} not found in trading calendar, skipping timing exit.")

                    # Strategy 4: Exit by 1-day indicator
                    elif H_1d_C0 is not None and H_1d_C0 < 0.0000:
                        print("Strategy 4: Exiting by 1-day indicator (H_1d_C0 < 0.0000)")
                        place_sell_order(symbol, quantity)

                    else:
                        print(f" - No exit conditions met for {symbol} at this time.")

                else:
                    print(f" - The order of stock {symbol} is placed\n")

            else: 
                print(" - It's already been traded for today.\n")

    # Market is changing direction
    else:
        print(f"The market is changing direction")
        print(f"Update at {datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Log market condition every run
    run_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    export_market_condition_tracking(run_time, C_1d_C0_market, EMA_10d_market, H_1d_C0_market)

else:
    print(f"The market is closed")

