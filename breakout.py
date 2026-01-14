import config, requests
import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
import datetime as dt
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit  # Add TimeFrameUnit for custom intervals
from helpers import calculate_quantity
import pandas as pd
import pytz
import pandas_ta as ta

# Robust indicator helpers: compute_macd and compute_rsi
def compute_macd(df, fast=12, slow=26, signal=9):
    try:
        if df is None or df.empty:
            return pd.DataFrame()
        # find close column name
        close_col = None
        for c in df.columns:
            if c.lower() == 'close':
                close_col = c
                break
        if close_col is None:
            print("compute_macd: 'close' column not found")
            return pd.DataFrame()
        # try DataFrame accessor
        if hasattr(df, 'ta'):
            try:
                return df.ta.macd(fast=fast, slow=slow, signal=signal)
            except Exception:
                pass
        # fallback functional API (returns DataFrame)
        try:
            macd_df = ta.macd(df[close_col], fast=fast, slow=slow, signal=signal)
            # pandas_ta functional may return Series or DataFrame; ensure DataFrame
            if isinstance(macd_df, pd.Series):
                return macd_df.to_frame()
            return macd_df
        except Exception as e:
            print(f"compute_macd fallback error: {e}")
            return pd.DataFrame()
    except Exception as e:
        print(f"compute_macd error: {e}")
        return pd.DataFrame()

def compute_rsi(df, length=14):
    try:
        if df is None or df.empty:
            return pd.Series()
        close_col = None
        for c in df.columns:
            if c.lower() == 'close':
                close_col = c
                break
        if close_col is None:
            print("compute_rsi: 'close' column not found")
            return pd.Series()
        if hasattr(df, 'ta'):
            try:
                return df.ta.rsi(length=length)
            except Exception:
                pass
        try:
            return ta.rsi(df[close_col], length=length)
        except Exception as e:
            print(f"compute_rsi fallback error: {e}")
            return pd.Series()
    except Exception as e:
        print(f"compute_rsi error: {e}")
        return pd.Series()

# --- Pattern detection helpers ---
def _get_col(df, name):
    """Return actual column in DataFrame matching lower-case 'name' or None."""
    if df is None or df.empty:
        return None
    for c in df.columns:
        if c.lower() == name.lower():
            return c
    return None

def is_bearish_pin_bar(df, idx=None, index=None, body_max_ratio=0.3, upper_wick_min_ratio=2.0):
    """
    Detect a bearish pin bar on a given row (default last row).
    Conditions (configurable):
      - Candle is bearish (close < open)
      - Body is small relative to total range: body / (high-low) <= body_max_ratio
      - Upper wick is long relative to body: upper_wick >= body * upper_wick_min_ratio
      - Upper wick noticeably larger than lower wick
    Returns True/False.
    """
    try:
        if df is None or df.empty:
            return False
        # normalize index parameter (support both 'idx' and legacy 'index')
        if idx is None and index is None:
            idx_to_use = -1
        elif idx is not None:
            idx_to_use = idx
        else:
            idx_to_use = index
        # get column names
        o_col = _get_col(df, 'open')
        h_col = _get_col(df, 'high')
        l_col = _get_col(df, 'low')
        c_col = _get_col(df, 'close')
        if None in (o_col, h_col, l_col, c_col):
            return False
        row = df.iloc[idx_to_use]
        o = float(row[o_col])
        h = float(row[h_col])
        l = float(row[l_col])
        c = float(row[c_col])
        # basic checks
        if h <= l:
            return False
        body = abs(c - o)
        total_range = h - l
        if total_range == 0:
            return False
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        # bearish candle
        if not (c < o):
            return False
        # body small relative to range
        if (body / total_range) > body_max_ratio:
            return False
        # upper wick long relative to body
        if body == 0:
            # extremely small body -> treat as pin if upper wick exists
            if upper_wick <= 0:
                return False
        else:
            if upper_wick < (body * upper_wick_min_ratio):
                return False
        # upper wick should be noticeably larger than lower wick
        if upper_wick <= (lower_wick * 1.0):
            return False
        return True
    except Exception:
        return False

def is_bearish_engulfing(df, idx=-1):
    """
    Detect bearish engulfing on the last two candles by default.
    Conditions:
      - Requires at least two rows
      - Previous candle bullish (prev_close > prev_open)
      - Current candle bearish (close < open)
      - Current real body engulfs previous real body:
            current_open >= prev_close and current_close <= prev_open
    Returns True/False.
    """
    try:
        if df is None or len(df) < 2:
            return False
        # map columns
        o_col = _get_col(df, 'open')
        c_col = _get_col(df, 'close')
        if None in (o_col, c_col):
            return False
        # get last two rows
        cur = df.iloc[idx]
        prev = df.iloc[idx-1]
        cur_o = float(cur[o_col]); cur_c = float(cur[c_col])
        prev_o = float(prev[o_col]); prev_c = float(prev[c_col])
        # previous bullish, current bearish
        if not (prev_c > prev_o and cur_c < cur_o):
            return False
        # engulfing body condition
        # allow equality to be considered engulfing
        if (cur_o >= prev_c) and (cur_c <= prev_o):
            return True
        return False
    except Exception:
        return False

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
        # Ensure DatetimeIndex is timezone-aware (Alpaca returns UTC but may be naive)
        if isinstance(bars.index, pd.DatetimeIndex):
            if bars.index.tz is None:
                bars.index = bars.index.tz_localize(pytz.UTC)
        # Normalize columns to Title Case for compatibility with rest of code
        bars.columns = [col.title() if col.lower() in ['open', 'close', 'high', 'low', 'volume'] else col for col in bars.columns]
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

# Function to get entry quantity
def get_entry_quantity(symbol):
    """Return the most-recent filled buy quantity for symbol as int, or None if not found."""
    try:
        orders = api.list_orders(status='all', limit=1000)
        buys = [o for o in orders if getattr(o, 'symbol', None) == symbol and getattr(o, 'side', None) == 'buy' and getattr(o, 'filled_at', None) is not None]
        if not buys:
            return None
        # sort by filled_at (oldest -> newest)
        try:
            buys_sorted = sorted(buys, key=lambda o: o.filled_at)
        except Exception:
            buys_sorted = buys
        last = buys_sorted[-1]
        fq = getattr(last, 'filled_qty', None) or getattr(last, 'filled_qty', None) or getattr(last, 'qty', None)
        if fq is None:
            return None
        # filled_qty may be a string; convert safely
        try:
            return int(float(fq))
        except Exception:
            return None
    except Exception:
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
        EMA_10d_market_P1 = round(EMA_10d_bars_market.iloc[-2], decimal_point)
        day_1_bars_market.columns = [col.lower() for col in day_1_bars_market.columns]
        # Ensure 'close' column exists and enough rows for MACD
        if 'close' in day_1_bars_market.columns and len(day_1_bars_market) >= 35:
            macd_1_market = compute_macd(day_1_bars_market)
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
        C_1d_C0_market_P1 = round(day_1_bars_market['Close'].iloc[-2], decimal_point)
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
    if EMA_10d_market is not None and C_1d_C0_market is not None and H_1d_C0_market is not None and (M_1d_C0_market < 0.0000 and H_1d_C0_market < 0.0000):
        print(" - Market is not good to trades.")
        current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
        current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")

        # No new open positions but keep checking the existing position
        if existing_position_symbols:
            print(" - No new open position. Keep checking the existing position.\n")
            for symbol in existing_position_symbols:
                print(f'{symbol}_{current_time}')

                # Fetch bars from Alpaca
                minute_5_bars = get_alpaca_bars(symbol, TimeFrame(5, TimeFrameUnit.Minute), start=datetime.now() - timedelta(days=60))
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
                if minute_5_bars_local.index.tz is None:
                    minute_5_bars_local.index = minute_5_bars_local.index.tz_localize('UTC').tz_convert(us_eastern)
                else:
                    minute_5_bars_local.index = minute_5_bars_local.index.tz_convert(us_eastern)

                # Filter for regular session (09:30 to 16:00)
                def is_market_open_bar(ts):
                    return (ts.hour > 9 or (ts.hour == 9 and ts.minute >= 30)) and (ts.hour < 16)

                minute_5_bars_open = minute_5_bars_local[minute_5_bars_local.index.map(is_market_open_bar)]

                # --- Fix: Reindex to complete set of market open 5-min intervals ---
                # Build expected 5-min timestamps for each day in the data
                if not minute_5_bars_open.empty:
                    start_date = minute_5_bars_open.index[0].date()
                    end_date = minute_5_bars_open.index[-1].date()
                    us_eastern = pytz.timezone('America/New_York')
                    all_expected = []
                    for single_date in pd.date_range(start_date, end_date):
                        for hour in range(9, 16):
                            for minute in range(0, 60, 5):
                                if (hour == 9 and minute < 30) or (hour == 16):
                                    continue
                                ts = us_eastern.localize(datetime.combine(single_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute))
                                all_expected.append(ts)
                    expected_index = pd.DatetimeIndex(all_expected)
                    # Reindex and sort
                    minute_5_bars_open = minute_5_bars_open.reindex(expected_index)
                    minute_5_bars_open = minute_5_bars_open.sort_index()

                # Ensure index is timezone-aware and in US/Eastern for resampling anchored at :30
                us_eastern = pytz.timezone('America/New_York')
                if isinstance(minute_5_bars_open.index, pd.DatetimeIndex):
                    if minute_5_bars_open.index.tz is None:
                        minute_5_bars_open.index = minute_5_bars_open.index.tz_localize(pytz.UTC).tz_convert(us_eastern)
                    else:
                        minute_5_bars_open.index = minute_5_bars_open.index.tz_convert(us_eastern)

                # Resample to custom 60-min bars aligned to TradingView times (09:30, 10:30, ..., 15:30 US/Eastern)
                # Only resample OHLCV columns to avoid NaN propagation from extra columns
                ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
                try:
                    minute_60_bars_open = minute_5_bars_open[ohlcv_cols].resample(
                        '60min', label='left', closed='left', origin='start_day', offset=pd.Timedelta(minutes=30)
                    ).agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna(how='all')
                except Exception as e:
                    # Fallback if pandas version does not support origin/offset
                    minute_60_bars_open = minute_5_bars_open[ohlcv_cols].resample('60min', label='left', closed='left').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna(how='all')
                    # Shift index by 30 minutes and keep only :30 times
                    minute_60_bars_open.index = minute_60_bars_open.index + pd.Timedelta(minutes=30)

                # Filter to only bars starting at TradingView times (09:30, 10:30, ..., 15:30)
                minute_60_bars_open = minute_60_bars_open[minute_60_bars_open.index.map(lambda ts: ts.hour in range(9, 16) and ts.minute == 30)]

                # --- NEW: Exclude weekends/holidays and incomplete/future bars ---
                # 1) Drop rows that are all-NaN or have zero/NaN volume
                try:
                    minute_60_bars_open = minute_60_bars_open.dropna(how='all')
                    if 'volume' in minute_60_bars_open.columns:
                        minute_60_bars_open = minute_60_bars_open[minute_60_bars_open['volume'].fillna(0) > 0]
                except Exception:
                    pass

                # 2) Exclude non-trading days using Alpaca calendar; fallback to weekday filtering
                try:
                    # start_date / end_date were created earlier when building expected 5-min index
                    cal = api.get_calendar(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
                    valid_dates = set([pd.to_datetime(getattr(d, 'date')).date() for d in cal])
                    minute_60_bars_open = minute_60_bars_open[minute_60_bars_open.index.map(lambda ts: ts.date() in valid_dates)]
                except Exception:
                    # Fallback: drop weekends
                    minute_60_bars_open = minute_60_bars_open[minute_60_bars_open.index.dayofweek < 5]

                # 3) Remove incomplete/future bars: require the underlying 5-min source to cover the full 60-min bin
                try:
                    max_5m_ts = minute_5_bars_open.index.max()
                    minute_60_bars_open = minute_60_bars_open[minute_60_bars_open.index.map(lambda ts: max_5m_ts >= ts + pd.Timedelta(minutes=55))]
                except Exception:
                    pass

                # Ensure all columns are lowercase for price data
                minute_5_bars_open.columns = [col.lower() for col in minute_5_bars_open.columns]

                # Calculate MACD (pandas_ta always outputs Title Case columns)
                macd_5 = compute_macd(minute_5_bars_open, fast=12, slow=26, signal=9)
                macd_60 = compute_macd(minute_60_bars_open, fast=12, slow=26, signal=9)
                rsi_60 = minute_60_bars_open.ta.rsi()
                # print(f"MACD_60 for {symbol}:")
                # print(macd_60.iloc[-10:])  # Print last 10 rows of MACD_60 for debugging
                EMA_10_60m_bars = minute_60_bars_open['close'].ewm(span=10, adjust=False).mean()
                EMA_10_60m_C0 = round(EMA_10_60m_bars.iloc[-1], decimal_point)
                EMA_10_60m_P1 = round(EMA_10_60m_bars.iloc[-2], decimal_point)
                macd_1 = compute_macd(day_1_bars)
                rsi_5 = compute_rsi(minute_5_bars)

                # Restore Title Case for rest of code
                minute_5_bars.columns = [col.title() for col in minute_5_bars.columns]
                day_1_bars.columns = [col.title() for col in day_1_bars.columns]

                decimal_point = 4
                decimal_point_rsi = 2
                decimal_point_ema = 2

                # Candle Stick
                M_1d_C0 = round(macd_1['MACD_12_26_9'].iloc[-1], decimal_point) if 'MACD_12_26_9' in macd_1.columns else None
                M_1d_P1 = round(macd_1['MACD_12_26_9'].iloc[-2], decimal_point) if 'MACD_12_26_9' in macd_1.columns else None
                H_1d_C0 = round(macd_1['MACDh_12_26_9'].iloc[-1], decimal_point) if 'MACDh_12_26_9' in macd_1.columns else None
                H_1d_P1 = round(macd_1['MACDh_12_26_9'].iloc[-2], decimal_point) if 'MACDh_12_26_9' in macd_1.columns else None
                Close_1d_C0 = round(day_1_bars['Close'].iloc[-1], decimal_point) if 'Close' in day_1_bars.columns else None

                # 60-Minute in dicators
                M_60m_C0 = round(macd_60['MACD_12_26_9'].iloc[-1], decimal_point)
                M_60m_P1 = round(macd_60['MACD_12_26_9'].iloc[-2], decimal_point)
                H_60m_C0 = round(macd_60['MACDh_12_26_9'].iloc[-1], decimal_point)
                H_60m_P1 = round(macd_60['MACDh_12_26_9'].iloc[-2], decimal_point)
                H_60m_P2 = round(macd_60['MACDh_12_26_9'].iloc[-3], decimal_point) 
                Close_60m_C0 = round(minute_60_bars_open['close'].iloc[-1], decimal_point)
                Close_60m_P1 = round(minute_60_bars_open['close'].iloc[-2], decimal_point)

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

                market_price = round(minute_5_bars['close'].iloc[-1], decimal_point)
                # maximum_limit_below_ema10 = round(0.95 * EMA_10d, decimal_point) # 5.0% below EMA_10-1d

                # Getting Data
                position = api.get_position(symbol)
                # normalize current position quantity to int
                try:
                    position_qty = int(float(position.qty))
                except Exception:
                    # fallback if qty not available or convertible
                    position_qty = position.qty
                quantity = position_qty
                # determine entry_quantity (original filled buy quantity)
                entry_quantity = get_entry_quantity(symbol)
                if entry_quantity is None:
                    # fallback to current position quantity if we can't find a filled buy order record
                    try:
                        entry_quantity = int(position_qty)
                    except Exception:
                        entry_quantity = position_qty
                entry_price = float(position.avg_entry_price)
                market_value = abs(float(position.market_value))
                cost = abs(float(position.cost_basis))
                entry_date_g = get_entry_date(symbol)
                entry_d = entry_date_g.astimezone(pytz.timezone('America/New_York')).date()
                current_date = dt.datetime.now(pytz.timezone('America/New_York')).date()

                # Check 1-day candlestick pattern exits
                # Prepare a safe daily DataFrame for pattern detection (lowercase columns)
                try:
                    day_df_for_patterns = day_1_bars.copy() if 'day_1_bars' in locals() else None
                    if isinstance(day_df_for_patterns, pd.DataFrame) and not day_df_for_patterns.empty:
                        day_df_for_patterns.columns = [c.lower() for c in day_df_for_patterns.columns]
                    else:
                        day_df_for_patterns = None
                except Exception:
                    day_df_for_patterns = None

                # Strategy 1: False Entry Position
                if M_60m_C0 < 0.0000 and H_60m_C0 < 0.0000 and H_60m_P1 > 0.0000:
                    print(f" - EXIT: It's a fasle 60MXU, H_60m_C0 < 0.0000 and H_60m_P1 > 0.0000.")
                    place_sell_order(symbol, quantity)  

                # Strategy 2: False Running Uptrend
                elif M_60m_C0 < 0.0000 and M_60m_P1 > 0.0000 and Close_1d_C0 < EMA_10d:
                    print(f" - EXIT: It's a false running uptrend, M_60m_C0 < 0.0000 and M_60m_P1 > 0.0000.")
                    place_sell_order(symbol, quantity)

                # Strategy 3: 1DXD
                elif H_1d_C0 < 0.0000 and H_60m_C0 < 0.0000:
                    print(f" - EXIT: It's a 1DXD, H_1d_C0 < 0.0000 and H_60m_C0 < 0.0000.")
                    place_sell_order(symbol, quantity)

                # Strategy 4: Cutting Loss at 5%
                elif market_value < (0.95 * cost):
                    print(f" - EXIT: It's a cut-loss > 5%.")
                    place_sell_order(symbol, quantity)

                # Strategy 5: Exit by timing (after 3 trading days, excluding weekends/holidays)
                elif M_60m_C0 < 0.0000 and entry_d is not None:
                    # Get all trading dates between entry_d and current_date
                    all_days = pd.date_range(entry_d, current_date)
                    # Fetch market calendar from Alpaca
                    calendar = api.get_calendar(start=entry_d.strftime('%Y-%m-%d'), end=current_date.strftime('%Y-%m-%d'))
                    trading_dates = [day.date.date() if hasattr(day.date, 'date') else day.date for day in calendar]
                    # Find the index of entry_d in trading_dates
                    if entry_d in trading_dates:
                        entry_idx = trading_dates.index(entry_d)
                        # Check if current_date is at least three trading days after entry_d
                        if len(trading_dates) > entry_idx + 3 and current_date >= trading_dates[entry_idx + 3]:
                            print("Strategy 3: Exiting by timing (after 3 trading days)")
                            place_sell_order(symbol, quantity)
                    else:
                        print(f"Entry date {entry_d} not found in trading calendar, skipping timing exit.")

                # Strategy 6: Taking profit when 60MXD
                elif M_60m_C0 > 0.0000 and H_60m_C0 < 0.0000 and H_60m_P1 > 0.0000:
                    if quantity == entry_quantity:
                        print(f" - EXIT: Taking profit by 60MXD on {symbol}.")
                        quantity = int(int(quantity) / 2)
                        place_sell_order(symbol, quantity)
                    else:
                        print(f" - Let profit run for {symbol}.")

                # Strategy 7: Taking profit when 60MXD-0
                elif M_60m_C0 < 0.0000 and M_60m_P1 > 0.0000 and Close_60m_C0 < EMA_10_60m_C0:
                    print(f" - EXIT: Taking profit by 60MXD-0 on {symbol}.")
                    place_sell_order(symbol, quantity)

                # Strategy 8: Taking profit by detecting bearish patterns on the previous FULLY-CLOSED daily bar
                # Use the previous trading day's single 1-day candle (e.g., if running at 09:30 on Oct 8, check Oct 7)
                elif M_1d_C0 > M_1d_P1 and M_60m_C0 > 0.0000:
                    try:
                        if day_df_for_patterns is None or day_df_for_patterns.empty:
                            print(f" - No daily data available for pattern checks for {symbol}.")
                        else:
                            # Determine if the last bar in day_df_for_patterns is today's partial bar (not fully closed)
                            # Safely derive the last index value and avoid pandas ambiguous parsing warning
                            try:
                                last_index_val = day_df_for_patterns.index[-1]
                                # If it's already a Timestamp/Datetime-like object, use it directly
                                if isinstance(last_index_val, pd.Timestamp):
                                    last_bar_ts = last_index_val
                                else:
                                    # Parse conservatively and coerce invalid formats to NaT
                                    last_bar_ts = pd.to_datetime(last_index_val, errors='coerce')

                                ny_today = datetime.now(pytz.timezone('America/New_York')).date()
                                # If parsing failed (NaT), fall back to using penultimate bar when available
                                if pd.isna(last_bar_ts):
                                    prev_idx = -2 if len(day_df_for_patterns) >= 2 else -1
                                else:
                                    try:
                                        last_date = last_bar_ts.date()
                                        # If the last day in the DataFrame is today (or in the future), treat it as partial and use -2
                                        prev_idx = -2 if last_date >= ny_today else -1
                                    except Exception:
                                        prev_idx = -2 if len(day_df_for_patterns) >= 2 else -1
                            except Exception:
                                # Fallback: if anything goes wrong, prefer the penultimate bar when available
                                prev_idx = -2 if len(day_df_for_patterns) >= 2 else -1

                            # Extract the single previous fully-closed daily bar as a one-row DataFrame
                            try:
                                prev_day_df = day_df_for_patterns.iloc[[prev_idx]].copy()
                            except Exception:
                                prev_day_df = None

                            # Check bearish pin bar on previous day only
                            proceed_with_check = True
                            # If we have an entry date, ensure the previous day is the trading day immediately after entry_d
                            if entry_d is not None and prev_day_df is not None and not prev_day_df.empty:
                                try:
                                    # get the date for prev_day_df
                                    prev_idx_val = prev_day_df.index[0]
                                    prev_day_ts = pd.to_datetime(prev_idx_val)
                                    prev_day_date = prev_day_ts.date()
                                    # request calendar from entry_d to prev_day_date
                                    calendar = api.get_calendar(start=entry_d.strftime('%Y-%m-%d'), end=prev_day_date.strftime('%Y-%m-%d'))
                                    trading_dates = []
                                    for d in calendar:
                                        dt = d.date
                                        if hasattr(dt, 'date'):
                                            trading_dates.append(dt.date())
                                        else:
                                            try:
                                                trading_dates.append(pd.to_datetime(dt).date())
                                            except Exception:
                                                pass
                                    # verify that prev_day_date is the immediate next trading day after entry_d
                                    if entry_d in trading_dates:
                                        entry_idx = trading_dates.index(entry_d)
                                        if not (entry_idx + 1 < len(trading_dates) and trading_dates[entry_idx + 1] == prev_day_date):
                                            proceed_with_check = False
                                    else:
                                        # if entry_d not found in calendar, do not proceed
                                        proceed_with_check = False
                                except Exception:
                                    proceed_with_check = False

                            if proceed_with_check and prev_day_df is not None and not prev_day_df.empty and is_bearish_pin_bar(prev_day_df, idx=-1):
                                print(f" - Bearish Pin Bar detected on previous daily bar for {symbol}.")
                                TRACK_1D_EXIT = f"TRACK_1D_EXIT,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{market_price},{entry_price},{market_value},{cost},{((market_value - cost) / cost) * 100:.2f}%"
                                print(TRACK_1D_EXIT)
                                place_sell_order(symbol, quantity)
                            else:
                                if not proceed_with_check:
                                    print(f" - Previous daily bar for {symbol} is not the trading day immediately after entry date {entry_d}; skipping bearish-pin check.")
                                else:
                                    print(f" - No bearish pin-bar on previous daily bar for {symbol}.")
                    except Exception as e:
                        print(f" - Error checking previous daily bearish pattern for {symbol}: {e}")

                # No exit conditions met
                else:
                    print(f" - No exit conditions met for {symbol} at this time.\n")

        else:
            print("Keep checking the existiong position. Waiting for good market condition to trade.\n")                

    # Market is good to trade
    elif M_1d_C0_market > 0.0000 or (M_1d_C0_market < 0.0000 and H_1d_C0_market > 0.0000):
        print(f"\nMarket is good to trade.")
        symbols_5MX0_AB = config.BREAKOUT_SYMBOLS_5MX0_AB
        current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
        current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")

        orders = api.list_orders(status='all', after=current_date)
        existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']
        buy_order_symbols = [order.symbol for order in orders if order.side == 'buy' and order.status != 'canceled']
        positions = api.list_positions()
        existing_position_symbols = [position.symbol for position in positions]
        # print(f'{current_time}\n')

        # Breakout Strategy Model-5MX0-AB
        for symbol in symbols_5MX0_AB:
            print(f'\n{symbol}_{current_time}')
            # Fetch bars from Alpaca
            minute_5_bars = get_alpaca_bars(symbol, TimeFrame(5, TimeFrameUnit.Minute), start=datetime.now() - timedelta(days=60))
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
            if minute_5_bars_local.index.tz is None:
                minute_5_bars_local.index = minute_5_bars_local.index.tz_localize('UTC').tz_convert(us_eastern)
            else:
                minute_5_bars_local.index = minute_5_bars_local.index.tz_convert(us_eastern)

            # Filter for regular session (09:30 to 16:00)
            def is_market_open_bar(ts):
                return (ts.hour > 9 or (ts.hour == 9 and ts.minute >= 30)) and (ts.hour < 16)

            minute_5_bars_open = minute_5_bars_local[minute_5_bars_local.index.map(is_market_open_bar)]
            # print(f"minute_5_bars_open for {symbol}:")
            # print(minute_5_bars_open)

            # --- Fix: Reindex to complete set of market open 5-min intervals ---
            # Build expected 5-min timestamps for each day in the data
            if not minute_5_bars_open.empty:
                start_date = minute_5_bars_open.index[0].date()
                end_date = minute_5_bars_open.index[-1].date()
                us_eastern = pytz.timezone('America/New_York')
                all_expected = []
                for single_date in pd.date_range(start_date, end_date):
                    for hour in range(9, 16):
                        for minute in range(0, 60, 5):
                            if (hour == 9 and minute < 30) or (hour == 16):
                                continue
                            ts = us_eastern.localize(datetime.combine(single_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute))
                            all_expected.append(ts)
                expected_index = pd.DatetimeIndex(all_expected)
                # Reindex and sort
                minute_5_bars_open = minute_5_bars_open.reindex(expected_index)
                minute_5_bars_open = minute_5_bars_open.sort_index()

            # Ensure index is timezone-aware and in US/Eastern for resampling anchored at :30
            us_eastern = pytz.timezone('America/New_York')
            if isinstance(minute_5_bars_open.index, pd.DatetimeIndex):
                if minute_5_bars_open.index.tz is None:
                    minute_5_bars_open.index = minute_5_bars_open.index.tz_localize(pytz.UTC).tz_convert(us_eastern)
                else:
                    minute_5_bars_open.index = minute_5_bars_open.index.tz_convert(us_eastern)

            # Resample to custom 60-min bars aligned to TradingView times (09:30, 10:30, ..., 15:30 US/Eastern)
            # Only resample OHLCV columns to avoid NaN propagation from extra columns
            ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
            try:
                minute_60_bars_open = minute_5_bars_open[ohlcv_cols].resample(
                    '60min', label='left', closed='left', origin='start_day', offset=pd.Timedelta(minutes=30)
                ).agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna(how='all')
            except Exception as e:
                # Fallback if pandas version does not support origin/offset
                minute_60_bars_open = minute_5_bars_open[ohlcv_cols].resample('60min', label='left', closed='left').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna(how='all')
                # Shift index by 30 minutes and keep only :30 times
                minute_60_bars_open.index = minute_60_bars_open.index + pd.Timedelta(minutes=30)

            # Filter to only bars starting at TradingView times (09:30, 10:30, ..., 15:30)
            minute_60_bars_open = minute_60_bars_open[minute_60_bars_open.index.map(lambda ts: ts.hour in range(9, 16) and ts.minute == 30)]

            # --- NEW: Exclude weekends/holidays and incomplete/future bars ---
            # 1) Drop rows that are all-NaN or have zero/NaN volume
            try:
                minute_60_bars_open = minute_60_bars_open.dropna(how='all')
                if 'volume' in minute_60_bars_open.columns:
                    minute_60_bars_open = minute_60_bars_open[minute_60_bars_open['volume'].fillna(0) > 0]
            except Exception:
                pass

            # 2) Exclude non-trading days using Alpaca calendar; fallback to weekday filtering
            try:
                # start_date / end_date were created earlier when building expected 5-min index
                cal = api.get_calendar(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
                valid_dates = set([pd.to_datetime(getattr(d, 'date')).date() for d in cal])
                minute_60_bars_open = minute_60_bars_open[minute_60_bars_open.index.map(lambda ts: ts.date() in valid_dates)]
            except Exception:
                # Fallback: drop weekends
                minute_60_bars_open = minute_60_bars_open[minute_60_bars_open.index.dayofweek < 5]

            # 3) Remove incomplete/future bars: require the underlying 5-min source to cover the full 60-min bin
            try:
                max_5m_ts = minute_5_bars_open.index.max()
                minute_60_bars_open = minute_60_bars_open[minute_60_bars_open.index.map(lambda ts: max_5m_ts >= ts + pd.Timedelta(minutes=55))]
            except Exception:
                pass

            # Ensure all columns are lowercase for price data
            minute_5_bars_open.columns = [col.lower() for col in minute_5_bars_open.columns]

            # Calculate MACD (pandas_ta always outputs Title Case columns)
            macd_5 = compute_macd(minute_5_bars_open, fast=12, slow=26, signal=9)
            macd_60 = compute_macd(minute_60_bars_open, fast=12, slow=26, signal=9)
            rsi_60 = minute_60_bars_open.ta.rsi()
            # print(f"MACD_60 for {symbol}:")
            # print(macd_60.iloc[-10:])  # Print last 10 rows of MACD_60 for debugging
            EMA_10_60m_bars = minute_60_bars_open['close'].ewm(span=10, adjust=False).mean()
            EMA_10_60m_C0 = round(EMA_10_60m_bars.iloc[-1], decimal_point)
            EMA_10_60m_P1 = round(EMA_10_60m_bars.iloc[-2], decimal_point)
            EMA_10_60m_P2 = round(EMA_10_60m_bars.iloc[-3], decimal_point)
            EMA_10_60m_P3 = round(EMA_10_60m_bars.iloc[-4], decimal_point)
            EMA_10_60m_P4 = round(EMA_10_60m_bars.iloc[-5], decimal_point)
            EMA_10_60m_P5 = round(EMA_10_60m_bars.iloc[-6], decimal_point)
            EMA_10_60m_P6 = round(EMA_10_60m_bars.iloc[-7], decimal_point)
            EMA_10_60m_P7 = round(EMA_10_60m_bars.iloc[-8], decimal_point)
            macd_1 = compute_macd(day_1_bars)
            rsi_5 = compute_rsi(minute_5_bars)

            # Restore Title Case for rest of code
            minute_5_bars.columns = [col.title() for col in minute_5_bars.columns]
            day_1_bars.columns = [col.title() for col in day_1_bars.columns]

            decimal_point = 4
            decimal_point_rsi = 2
            decimal_point_ema = 2

            # Candle Stick
            M_1d_C0 = round(macd_1['MACD_12_26_9'].iloc[-1], decimal_point) if 'MACD_12_26_9' in macd_1.columns else None
            M_1d_P1 = round(macd_1['MACD_12_26_9'].iloc[-2], decimal_point) if 'MACD_12_26_9' in macd_1.columns else None
            M_1d_P2 = round(macd_1['MACD_12_26_9'].iloc[-3], decimal_point) if 'MACD_12_26_9' in macd_1.columns else None
            M_1d_P3 = round(macd_1['MACD_12_26_9'].iloc[-4], decimal_point) if 'MACD_12_26_9' in macd_1.columns else None
            H_1d_C0 = round(macd_1['MACDh_12_26_9'].iloc[-1], decimal_point) if 'MACDh_12_26_9' in macd_1.columns else None
            H_1d_P1 = round(macd_1['MACDh_12_26_9'].iloc[-2], decimal_point) if 'MACDh_12_26_9' in macd_1.columns else None
            H_1d_P2 = round(macd_1['MACDh_12_26_9'].iloc[-3], decimal_point) if 'MACDh_12_26_9' in macd_1.columns else None
            Close_1d_C0 = round(day_1_bars['Close'].iloc[-1], decimal_point) if 'Close' in day_1_bars.columns else None

            # 60-Minute in dicators
            M_60m_C0 = round(macd_60['MACD_12_26_9'].iloc[-1], decimal_point)
            M_60m_P1 = round(macd_60['MACD_12_26_9'].iloc[-2], decimal_point)
            M_60m_P2 = round(macd_60['MACD_12_26_9'].iloc[-3], decimal_point)
            M_60m_P3 = round(macd_60['MACD_12_26_9'].iloc[-4], decimal_point)
            H_60m_C0 = round(macd_60['MACDh_12_26_9'].iloc[-1], decimal_point)
            H_60m_P1 = round(macd_60['MACDh_12_26_9'].iloc[-2], decimal_point)
            H_60m_P2 = round(macd_60['MACDh_12_26_9'].iloc[-3], decimal_point)
            H_60m_P3 = round(macd_60['MACDh_12_26_9'].iloc[-4], decimal_point)
            RSI_60m_C0 = round(rsi_60.iloc[-1], decimal_point)
            Open_60m_C0 = round(minute_60_bars_open['open'].iloc[-1], decimal_point) 
            Close_60m_C0 = round(minute_60_bars_open['close'].iloc[-1], decimal_point)
            Open_60m_P1 = round(minute_60_bars_open['open'].iloc[-2], decimal_point)
            Close_60m_P1 = round(minute_60_bars_open['close'].iloc[-2], decimal_point)
            Close_60m_P2 = round(minute_60_bars_open['close'].iloc[-3], decimal_point)
            Close_60m_P3 = round(minute_60_bars_open['close'].iloc[-4], decimal_point)
            Close_60m_P4 = round(minute_60_bars_open['close'].iloc[-5], decimal_point)
            Close_60m_P5 = round(minute_60_bars_open['close'].iloc[-6], decimal_point)
            Close_60m_P6 = round(minute_60_bars_open['close'].iloc[-7], decimal_point)
            Close_60m_P7 = round(minute_60_bars_open['close'].iloc[-8], decimal_point)

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

            market_price = round(minute_5_bars['close'].iloc[-1], decimal_point)
            # maximum_limit_below_ema10 = round(0.95 * EMA_10d, decimal_point) # 5.0% below EMA_10-1d

            ## -- ENTRY -- ##
            if symbol not in existing_position_symbols:

                if symbol not in existing_order_symbols:
                    Upper_Limit_EMA10_1d = round(EMA_10d*1.075, decimal_point) # 7.5% above EMA_10_1d
                    Lower_Limit_EMA10_1d = round(EMA_10d*0.97, decimal_point) # 3.0% below EMA_10_1d
                    percentage_from_ema10_1d = ((Close_5m_C0 - EMA_10d) / EMA_10d) * 100

                    Upper_Limit_EMA10_60m = round(EMA_10_60m_C0*1.05, decimal_point) # 5.0% above EMA_10-60m
                    percentage_from_ema10_60m = ((Close_60m_C0 - EMA_10_60m_C0) / EMA_10_60m_C0) * 100

                    # Entry Position: 60MXU
                    if H_60m_P1 > 0.0000 and H_60m_P2 < 0.0000 and M_60m_P2 < 0.0000:
                        print(f" - 60MXU Detected.")
                        print(f" - The 60-min price: {Close_60m_C0} is above EMA_10-60m: {EMA_10_60m_C0} at {percentage_from_ema10_60m:.2f}%")

                        # PXU_P1
                        if Close_60m_P1 > EMA_10_60m_P1 and Close_60m_P2 < EMA_10_60m_P2:
                            print(f" - 60MXU-PXU_P1 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_60m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                # --- Tracking Port Print for 60-min Entry ---
                                print(f"TRACK_60M_ENTRY,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{Close_60m_C0},{EMA_10_60m_C0},{M_60m_C0},{H_60m_C0},{RSI_60m_C0}")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")
    
                        # PXU_P2
                        elif Close_60m_P1 > EMA_10_60m_P1 and Close_60m_P2 > EMA_10_60m_P2 and Close_60m_P3 < EMA_10_60m_P3:
                            print(f" - 60MXU-PXU_P2 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_60m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                # --- Tracking Port Print for 60-min Entry ---
                                print(f"TRACK_60M_ENTRY,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{Close_60m_C0},{EMA_10_60m_C0},{M_60m_C0},{H_60m_C0},{RSI_60m_C0}")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")

                        # PXU_P3
                        elif Close_60m_P1 > EMA_10_60m_P1 and Close_60m_P2 > EMA_10_60m_P2 and Close_60m_P3 > EMA_10_60m_P3 and Close_60m_P4 < EMA_10_60m_P4:
                            print(f" - 60MXU-PXU_P3 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_60m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                # --- Tracking Port Print for 60-min Entry ---
                                print(f"TRACK_60M_ENTRY,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{Close_60m_C0},{EMA_10_60m_C0},{M_60m_C0},{H_60m_C0},{RSI_60m_C0}")                                
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")

                        # PXU_P4
                        elif Close_60m_P1 > EMA_10_60m_P1 and Close_60m_P2 > EMA_10_60m_P2 and Close_60m_P3 > EMA_10_60m_P3 and Close_60m_P4 > EMA_10_60m_P4 and Close_60m_P5 < EMA_10_60m_P5:
                            print(f" - 60MXU-PXU_P4 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_60m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                # --- Tracking Port Print for 60-min Entry ---
                                print(f"TRACK_60M_ENTRY,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{Close_60m_C0},{EMA_10_60m_C0},{M_60m_C0},{H_60m_C0},{RSI_60m_C0}")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")

                        # PXU_P5
                        elif Close_60m_P1 > EMA_10_60m_P1 and Close_60m_P2 > EMA_10_60m_P2 and Close_60m_P3 > EMA_10_60m_P3 and Close_60m_P4 > EMA_10_60m_P4 and Close_60m_P5 < EMA_10_60m_P5 and Close_60m_P6 < EMA_10_60m_P6:
                            print(f" - 60MXU-PXU_P5 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_60m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                # --- Tracking Port Print for 60-min Entry ---
                                print(f"TRACK_60M_ENTRY,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{Close_60m_C0},{EMA_10_60m_C0},{M_60m_C0},{H_60m_C0},{RSI_60m_C0}")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")

                        # PXU_P6
                        elif Close_60m_P1 > EMA_10_60m_P1 and Close_60m_P2 > EMA_10_60m_P2 and Close_60m_P3 > EMA_10_60m_P3 and Close_60m_P4 > EMA_10_60m_P4 and Close_60m_P5 > EMA_10_60m_P5 and Close_60m_P6 < EMA_10_60m_P6 and Close_60m_P7 < EMA_10_60m_P7:
                            print(f" - 60MXU-PXU_P6 detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_60m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                # --- Tracking Port Print for 60-min Entry ---
                                print(f"TRACK_60M_ENTRY,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{Close_60m_C0},{EMA_10_60m_C0},{M_60m_C0},{H_60m_C0},{RSI_60m_C0}")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")

                        # No PXU pattern detected
                        else:
                            print(f" - No PXU pattern detected for {symbol} on 60MXU.")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                    
                    # Entry Position: 60PXU
                    elif Close_60m_P1 > EMA_10_60m_P1 and Close_60m_P2 < EMA_10_60m_P2:
                        print(f" - 60PXU Detected.")
                        print(f" - The 60-min price: {Close_60m_C0} is above EMA_10-60m: {EMA_10_60m_C0}")

                        # 60MXU_P1
                        if H_60m_P2 > 0.0000 and H_60m_P3 < 0.0000 and M_60m_P2 < 0.0000:
                            print(f" - 60PXU detected for {symbol}")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")
                            
                            # Check Entry Position in The Entry Range
                            if Lower_Limit_EMA10_1d < Close_5m_C0 < Upper_Limit_EMA10_1d and H_1d_C0 > 0.0000:
                                print(f" - The {symbol} price: {Close_5m_C0} is at {percentage_from_ema10_1d:.2f}% from EMA10-1d")
                                # --- Tracking Port Print for 60-min Entry ---
                                print(f"TRACK_60M_ENTRY,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{Close_60m_C0},{EMA_10_60m_C0},{M_60m_C0},{H_60m_C0},{RSI_60m_C0}")
                                quantity = calculate_quantity(market_price)
                                place_buy_order(symbol, quantity)
                            else:
                                print(f" - The {symbol} price is over the EMA10-1d Entry Range at {percentage_from_ema10_1d:.2f}% from EMA10-1d: {EMA_10d}\n")
                    
                        else:
                            print(f" - No 60PXU pattern detected for {symbol}.")
                            print(f" - The {symbol} price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m")

                    # No Entry Position detected
                    else:
                        print(f" - No Entry Position detected for {symbol}")
                        print(f" - The 60-min price: {Close_60m_C0} is at {percentage_from_ema10_60m:.2f}% from EMA10-60m: {EMA_10_60m_C0}\n")

                else:
                    print(f' - The order of stock {symbol} is placed\n')

            ## -- EXIT -- ##
            elif symbol in existing_position_symbols:

                if symbol not in existing_order_symbols or symbol in buy_order_symbols:

                    # Getting Data
                    print(f" - Already in the position")
                    position = api.get_position(symbol)
                    # normalize current position quantity to int
                    try:
                        position_qty = int(float(position.qty))
                    except Exception:
                        # fallback if qty not available or convertible
                        position_qty = position.qty
                    quantity = position_qty
                    # determine entry_quantity (original filled buy quantity)
                    entry_quantity = get_entry_quantity(symbol)
                    if entry_quantity is None:
                        # fallback to current position quantity if we can't find a filled buy order record
                        try:
                            entry_quantity = int(position_qty)
                        except Exception:
                            entry_quantity = position_qty
                    entry_price = float(position.avg_entry_price)
                    market_value = abs(float(position.market_value))
                    cost = abs(float(position.cost_basis))
                    entry_date_g = get_entry_date(symbol)
                    entry_d = entry_date_g.astimezone(pytz.timezone('America/New_York')).date()
                    current_date = dt.datetime.now(pytz.timezone('America/New_York')).date()
                    trading_day = datetime.now(pytz.timezone('America/New_York')).date()

                    # Current profit/loss
                    print(f" - Current profit/loss: {((market_value - cost) / cost) * 100:.2f}%")

                    # Check 1-day candlestick pattern exits
                    # Prepare a safe daily DataFrame for pattern detection (lowercase columns)
                    try:
                        day_df_for_patterns = day_1_bars.copy() if 'day_1_bars' in locals() else None
                        if isinstance(day_df_for_patterns, pd.DataFrame) and not day_df_for_patterns.empty:
                            day_df_for_patterns.columns = [c.lower() for c in day_df_for_patterns.columns]
                        else:
                            day_df_for_patterns = None
                    except Exception:
                        day_df_for_patterns = None

                    # Strategy 1: False Entry Position
                    if M_60m_P1 < 0.0000 and H_60m_P1 < 0.0000 and H_60m_P2 > 0.0000:
                        print(f" - EXIT: It's a fasle 60MXU, H_60m_C0 < 0.0000 and H_60m_P1 > 0.0000.")
                        place_sell_order(symbol, quantity)  

                    # Strategy 2: False Running Uptrend
                    elif M_60m_P1 < 0.0000 and M_60m_P2 > 0.0000 and Close_1d_C0 < EMA_10d:
                        print(f" - EXIT: It's a false running uptrend, M_60m_C0 < 0.0000 and M_60m_P1 > 0.0000.")
                        place_sell_order(symbol, quantity)

                    # Strategy 3: Cutting Loss at 5%
                    elif market_value < (0.95 * cost):
                        print(f" - EXIT: It's a cut-loss > 5%.")
                        place_sell_order(symbol, quantity)

                    # Strategy 4: Combined: Staged partial exits based on position percentage
                    # Stage 1 (100% position): 1DT (60MT, 60MXD) -> sell 20%
                    # Stage 2 (60% position): 1DXD (1DT) -> sell 30% (of original)
                    # Stage 3 (30% position): 1DX0 -> sell remaining 50%
                    elif market_value >= (1.0000 * cost) and trading_day != entry_d:
                        # Calculate position percentage relative to entry
                        position_pct = (quantity / entry_quantity) if entry_quantity > 0 else 0
                        
                        # Stage 1: At 100% entry_quantity (no sells yet)
                        if position_pct >= 0.95:  # Allow small tolerance for rounding
                            # # Check if 60M is bending (M_60m Topped at P2, now declining at P1)
                            # if M_60m_P1 < M_60m_P2 and M_60m_P2 > M_60m_P3 and M_60m_P1 > 0.0000:
                            #     quantity = int(int(entry_quantity) * 0.20)
                            #     print(f" - EXIT Stage 1: Taking profit 20% by 60MT  on {symbol}.")
                            #     place_sell_order(symbol, quantity)

                            # # Check if 60MXD (MACD histogram cross down on 60m)
                            # elif H_60m_P1 < 0.0000 and H_60m_P2 > 0.0000:
                            #     quantity = int(int(entry_quantity) * 0.20)
                            #     print(f" - EXIT Stage 1: Taking profit 20% by 60MXD on {symbol}.")
                            #     place_sell_order(symbol, quantity)

                            # Check if 1DM is bending (M_1d Topped at P2, now declining at P1)
                            if M_1d_P1 < M_1d_P2 and M_1d_P2 > M_1d_P3 and M_1d_P1 > 0.0000:
                                quantity = int(int(entry_quantity) * 0.20)
                                print(f" - EXIT Stage 1: Taking profit 20% by 1DT on {symbol}.")
                                place_sell_order(symbol, quantity)

                            else:
                                print(f" - Let the stock running for the 1st volume-position exit on {symbol}.")
                        
                        # Stage 2: At ~80% entry_quantity (after 1st sell of 20%)
                        elif 0.70 <= position_pct < 0.90:
                            # Check if 1DXD (daily cross down + 60m cross down)
                            if H_1d_P1 < 0.0000 and H_1d_P2 > 0.0000 and H_60m_P1 < 0.0000:
                                quantity = int(int(entry_quantity) * 0.3)
                                print(f" - EXIT Stage 2: Taking profit 30% by 1DXD on {symbol}.")
                                place_sell_order(symbol, quantity)
                            
                            # # Check if 1DM is bending (M_1d Topped at P2, now declining at P1)
                            # elif M_1d_P1 < M_1d_P2 and M_1d_P2 > M_1d_P3 and M_1d_P1 > 0.0000:
                            #     quantity = int(int(entry_quantity) * 0.3)
                            #     print(f" - EXIT Stage 2: Taking profit 30% by 1DT on {symbol}.")
                            #     place_sell_order(symbol, quantity)

                            else:
                                print(f" - Let the stock running for the 2nd volume-position exit on {symbol}.")
                        
                        # Stage 3: At ~50% entry_quantity (after 1st and 2nd sells)
                        elif 0.40 <= position_pct < 0.60:
                            # Check if 1DX0-line (daily cross down at zero line)
                            if M_1d_P1 < 0.0000 and M_1d_P2 > 0.0000 and M_1d_C0 < M_1d_P1:
                                quantity = int(int(entry_quantity) * 0.50)
                                print(f" - EXIT Stage 3: Taking profit final 50% by 1DX0 on {symbol}.")
                                place_sell_order(symbol, quantity)
                            else:
                                print(f" - Let the stock running for the 3rd volume-position exit on {symbol}.")
                        
                        else:
                            print(f" - Position at {position_pct*100:.1f}% of entry, outside staged exit ranges for {symbol}.")
                    
                    # No exit conditions met
                    else:
                        print(f" - No exit conditions met for {symbol} at this time.")

                else:
                    print(f" - The order of stock {symbol} is placed\n")

            else: 
                print(" - It's already been traded for today.\n")

    # Market condition is not defined
    else:
        print(f"The market is not defined")
        print(f"Update at {datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')}\n")

else:
    print(f"The market is closed")

