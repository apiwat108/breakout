"""
Enhanced Breakout Symbols with Market Variation Tracking
=========================================================
This is an enhanced version of breakout_symbols.py that includes:
- Integration with manual breakout metadata (date, stop loss)
- Extended indicator categorization tracking
- Daily percentage calculations for each group
- Storage of market variation statistics

Run this file to update your watchlist with market variation tracking.
"""

import config
import requests
import tulipy
import numpy
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import pandas as pd
import pytz
import pandas_ta as ta
import psycopg2
import psycopg2.extras

# Import our new input handler
from mv_input_handler import BreakoutInputHandler


def get_alpaca_bars(symbol, timeframe, start, end=None):
    """Fetch bars from Alpaca API"""
    try:
        ALPACA_API_KEY = config.API_KEY
        ALPACA_SECRET_KEY = config.SECRET_KEY
        client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start,
            end=end if end else None
        )
        bars = client.get_stock_bars(request_params).df
        if bars.empty:
            return bars
        if isinstance(bars.index, pd.DatetimeIndex):
            if bars.index.tz is None:
                bars.index = bars.index.tz_localize(pytz.UTC)
        bars.columns = [col.title() if col.lower() in ['open', 'close', 'high', 'low', 'volume'] else col for col in bars.columns]
        return bars
    except Exception as e:
        print(f"Error fetching bars for {symbol}: {e}")
        return pd.DataFrame()


def compute_macd(df, fast=12, slow=26, signal=9):
    """Compute MACD indicator"""
    try:
        if df is None or df.empty:
            return pd.DataFrame()
        close_col = None
        for c in df.columns:
            if c.lower() == 'close':
                close_col = c
                break
        if close_col is None:
            print("compute_macd: 'close' column not found")
            return pd.DataFrame()
        if hasattr(df, 'ta'):
            try:
                return df.ta.macd(fast=fast, slow=slow, signal=signal)
            except Exception:
                pass
        try:
            macd_df = ta.macd(df[close_col], fast=fast, slow=slow, signal=signal)
            if isinstance(macd_df, pd.Series):
                return macd_df.to_frame()
            return macd_df
        except Exception as e:
            print(f"compute_macd fallback error: {e}")
            return pd.DataFrame()
    except Exception as e:
        print(f"compute_macd error: {e}")
        return pd.DataFrame()


class MarketVariationTracker:
    """Track symbols with enhanced categorization and market variation statistics"""
    
    def __init__(self):
        self.connection = psycopg2.connect(
            host=config.DB_HOST,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Initialize API
        self.api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
        
        # Get strategy and symbols from database
        self._load_symbols_from_db()
        
        # Initialize tracking lists
        self.reset_tracking_lists()
        
        # Input handler for breakout metadata
        self.input_handler = BreakoutInputHandler()
        
    def _load_symbols_from_db(self):
        """Load symbols from strategy in database"""
        self.cursor.execute("""
            SELECT id FROM strategy WHERE name = 'After Breakout_5MX0'
        """)
        strategy_result = self.cursor.fetchone()
        self.strategy_id = strategy_result['id'] if strategy_result else None
        
        if self.strategy_id:
            self.cursor.execute("""
                SELECT symbol, name
                FROM stock
                JOIN stock_strategy ON stock_strategy.stock_id = stock.id
                WHERE stock_strategy.strategy_id = %s
            """, (self.strategy_id,))
            stocks = self.cursor.fetchall()
            self.new_symbols = [stock['symbol'] for stock in stocks]
        else:
            self.new_symbols = []
        
        # Previous symbols from config
        self.previous_symbols = config.BREAKOUT_SYMBOLS_5MX0_AB
        
        # Get existing positions
        positions = self.api.list_positions()
        self.existing_position_symbols = [position.symbol for position in positions]
        
    def reset_tracking_lists(self):
        """Reset all tracking lists"""
        self.double_check_symbols = []
        self.symbols_end_of_proper_trading_range = []
        self.symbols_low_volume = []
        self.symbols_60m_turning_up = []
        self.symbols_60m_keeping_down = []
        self.symbols_60m_turning_down = []
        self.symbols_60m_keeping_up = []
        
    def process_symbol(self, symbol):
        """
        Process a single symbol with indicator analysis
        Returns dict with symbol analysis results
        """
        try:
            print(f" - Processing symbol {symbol}")
            
            # Get breakout metadata if it exists
            metadata = self.input_handler.get_breakout_metadata(symbol=symbol, active_only=True)
            has_metadata = len(metadata) > 0
            
            if has_metadata:
                metadata_record = metadata[0]
                print(f"   ✓ Has breakout metadata: Date={metadata_record['breakout_date']}, Stop Loss=${metadata_record['stop_loss_price']}")
            
            # Fetch daily bars (6 months)
            day_req = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=pd.Timestamp.now() - pd.Timedelta(days=180)
            )
            client = StockHistoricalDataClient(config.API_KEY, config.SECRET_KEY)
            day_bars = client.get_stock_bars(day_req).df
            
            # Fetch 5-minute bars
            minute_5_bars = get_alpaca_bars(
                symbol, 
                TimeFrame(5, TimeFrameUnit.Minute), 
                start=datetime.now() - timedelta(days=60)
            )
            
            # Check for empty data
            if any(df.empty or 'Close' not in df.columns for df in [minute_5_bars]):
                print(f"   Missing data for {symbol}, skipping.")
                return None
            
            # Process 5-minute bars to create 60-minute bars
            minute_5_bars.columns = [col.lower() for col in minute_5_bars.columns]
            us_eastern = pytz.timezone('America/New_York')
            minute_5_bars_local = minute_5_bars.copy()
            
            if isinstance(minute_5_bars_local.index, pd.MultiIndex):
                minute_5_bars_local.index = minute_5_bars_local.index.get_level_values(-1)
            
            if minute_5_bars_local.index.tz is None:
                minute_5_bars_local.index = minute_5_bars_local.index.tz_localize('UTC').tz_convert(us_eastern)
            else:
                minute_5_bars_local.index = minute_5_bars_local.index.tz_convert(us_eastern)
            
            # Filter for market hours
            def is_market_open_bar(ts):
                return (ts.hour > 9 or (ts.hour == 9 and ts.minute >= 30)) and (ts.hour < 16)
            
            minute_5_bars_open = minute_5_bars_local[minute_5_bars_local.index.map(is_market_open_bar)]
            
            # Reindex to complete set of 5-min intervals
            if not minute_5_bars_open.empty:
                start_date = minute_5_bars_open.index[0].date()
                end_date = minute_5_bars_open.index[-1].date()
                all_expected = []
                for single_date in pd.date_range(start_date, end_date):
                    for hour in range(9, 16):
                        for minute in range(0, 60, 5):
                            if (hour == 9 and minute < 30) or (hour == 16):
                                continue
                            ts = us_eastern.localize(
                                datetime.combine(single_date, datetime.min.time()) + 
                                timedelta(hours=hour, minutes=minute)
                            )
                            all_expected.append(ts)
                expected_index = pd.DatetimeIndex(all_expected)
                minute_5_bars_open = minute_5_bars_open.reindex(expected_index)
                minute_5_bars_open = minute_5_bars_open.sort_index()
            
            # Resample to 60-minute bars
            ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
            try:
                minute_60_bars_open = minute_5_bars_open[ohlcv_cols].resample(
                    '60min', label='left', closed='left', origin='start_day', 
                    offset=pd.Timedelta(minutes=30)
                ).agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna(how='all')
            except Exception:
                minute_60_bars_open = minute_5_bars_open[ohlcv_cols].resample(
                    '60min', label='left', closed='left'
                ).agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna(how='all')
                minute_60_bars_open.index = minute_60_bars_open.index + pd.Timedelta(minutes=30)
            
            minute_60_bars_open = minute_60_bars_open[
                minute_60_bars_open.index.map(lambda ts: ts.hour in range(9, 16) and ts.minute == 30)
            ]
            
            # Clean up data
            minute_60_bars_open = minute_60_bars_open.dropna(how='all')
            if 'volume' in minute_60_bars_open.columns:
                minute_60_bars_open['volume'] = minute_60_bars_open['volume'].fillna(0)
            
            # Filter trading days
            try:
                cal = self.api.get_calendar(
                    start=start_date.strftime('%Y-%m-%d'), 
                    end=end_date.strftime('%Y-%m-%d')
                )
                valid_dates = set([pd.to_datetime(getattr(d, 'date')).date() for d in cal])
                minute_60_bars_open = minute_60_bars_open[
                    minute_60_bars_open.index.map(lambda ts: ts.date() in valid_dates)
                ]
            except Exception:
                minute_60_bars_open = minute_60_bars_open[minute_60_bars_open.index.dayofweek < 5]
            
            # Remove incomplete bars
            def bin_has_data(ts):
                bin_end = ts + pd.Timedelta(minutes=55)
                try:
                    slice_5m = minute_5_bars_open.loc[ts:bin_end]
                    return not slice_5m.dropna(how='all').empty
                except Exception:
                    return False
            
            minute_60_bars_open = minute_60_bars_open[
                minute_60_bars_open.index.map(bin_has_data)
            ]
            if 'volume' in minute_60_bars_open.columns:
                minute_60_bars_open = minute_60_bars_open[minute_60_bars_open['volume'] > 0]
            
            # Normalize day bars
            if not day_bars.empty:
                day_bars.columns = [col.title() for col in day_bars.columns]
            
            if day_bars.empty or 'Close' not in day_bars.columns:
                print(f"   No data for {symbol}, skipping.")
                return None
            
            # Calculate indicators
            decimal_point = 4
            
            # 1D indicators
            closes_1d = numpy.array(day_bars['Close'])
            volume_1d = numpy.array(day_bars['Volume'])
            closes_C0 = closes_1d[-1]
            volume_C0 = volume_1d[-1]
            
            day_bars.columns = [col.lower() for col in day_bars.columns]
            macd_1 = day_bars.ta.macd()
            H_1d_C0 = round(macd_1['MACDh_12_26_9'][-1], decimal_point) if 'MACDh_12_26_9' in macd_1.columns else None
            M_1d_C0 = round(macd_1['MACD_12_26_9'][-1], decimal_point) if 'MACD_12_26_9' in macd_1.columns else None
            day_bars.columns = [col.title() for col in day_bars.columns]
            
            ema_10_C0 = tulipy.ema(numpy.array(closes_1d), period=10)[-1]
            market_value = volume_C0 * closes_C0
            
            # 60M indicators
            macd_60 = compute_macd(minute_60_bars_open, fast=12, slow=26, signal=9)
            M_60m_C0 = round(macd_60['MACD_12_26_9'].iloc[-1], decimal_point) if 'MACD_12_26_9' in macd_60.columns else None
            M_60m_P1 = round(macd_60['MACD_12_26_9'].iloc[-2], decimal_point) if 'MACD_12_26_9' in macd_60.columns else None
            M_60m_P2 = round(macd_60['MACD_12_26_9'].iloc[-3], decimal_point) if 'MACD_12_26_9' in macd_60.columns else None
            H_60m_C0 = round(macd_60['MACDh_12_26_9'].iloc[-1], decimal_point) if 'MACDh_12_26_9' in macd_60.columns else None
            H_60m_P1 = round(macd_60['MACDh_12_26_9'].iloc[-2], decimal_point) if 'MACDh_12_26_9' in macd_60.columns else None
            H_60m_P2 = round(macd_60['MACDh_12_26_9'].iloc[-3], decimal_point) if 'MACDh_12_26_9' in macd_60.columns else None
            
            # Categorize symbol
            category = self._categorize_symbol(
                symbol, closes_C0, ema_10_C0, M_1d_C0, H_1d_C0, volume_C0,
                M_60m_C0, M_60m_P1, H_60m_C0
            )
            
            return {
                'symbol': symbol,
                'category': category,
                'price': closes_C0,
                'volume': volume_C0,
                'market_value': market_value,
                'ema_10': ema_10_C0,
                'M_1d': M_1d_C0,
                'H_1d': H_1d_C0,
                'M_60m_C0': M_60m_C0,
                'M_60m_P1': M_60m_P1,
                'H_60m_C0': H_60m_C0,
                'has_metadata': has_metadata,
                'metadata': metadata_record if has_metadata else None
            }
            
        except Exception as e:
            print(f"   Error processing {symbol}: {e}")
            return None
    
    def _categorize_symbol(self, symbol, closes_C0, ema_10_C0, M_1d_C0, H_1d_C0, 
                          volume_C0, M_60m_C0, M_60m_P1, H_60m_C0):
        """Categorize symbol based on indicators"""
        
        # Add to double check list first
        self.double_check_symbols.append(symbol)
        
        # End of proper trading range - price conditions
        if closes_C0 < (0.95 * ema_10_C0):
            self.symbols_end_of_proper_trading_range.append(symbol)
            self.double_check_symbols.remove(symbol)
            return 'end_of_range'
        
        # End of proper trading range - MACD conditions
        elif M_1d_C0 < 0.0000 or H_1d_C0 < 0.0000:
            self.symbols_end_of_proper_trading_range.append(symbol)
            self.double_check_symbols.remove(symbol)
            return 'end_of_range'
        
        # Low volume
        elif volume_C0 < 700000:
            self.symbols_low_volume.append(symbol)
            self.double_check_symbols.remove(symbol)
            return 'low_volume'
        
        # 60m_turning_up
        elif M_60m_C0 < 0.0000 and M_60m_C0 > M_60m_P1 and H_60m_C0 < 0.0000:
            self.symbols_60m_turning_up.append(symbol)
            return 'turning_up'
        
        # 60m_keeping_down
        elif M_60m_C0 < M_60m_P1 and H_60m_C0 < 0.0000:
            self.symbols_60m_keeping_down.append(symbol)
            return 'keeping_down'
        
        # 60m_turning_down
        elif M_60m_C0 > 0.0000 and M_60m_C0 < M_60m_P1 and H_60m_C0 > 0.0000:
            self.symbols_60m_turning_down.append(symbol)
            return 'turning_down'
        
        # 60m_keeping_up
        elif M_60m_C0 > 0.0000 and M_60m_C0 > M_60m_P1 and H_60m_C0 > 0.0000:
            self.symbols_60m_keeping_up.append(symbol)
            return 'keeping_up'
        
        else:
            return 'other'
    
    def run_analysis(self):
        """Run full analysis on all symbols"""
        print(f"\n{'='*60}")
        print(f"Market Variation - Breakout Symbols Analysis")
        print(f"{'='*60}\n")
        
        all_symbols = list(set(self.previous_symbols))
        total_symbols = len(all_symbols)
        
        print(f"Analyzing {total_symbols} symbols...\n")
        
        for symbol in all_symbols:
            self.process_symbol(symbol)
        
        # Calculate statistics
        self._calculate_and_save_statistics()
    
    def _calculate_and_save_statistics(self):
        """Calculate percentages and save to database"""
        total = len(self.previous_symbols)
        
        if total == 0:
            print("No symbols to analyze")
            return
        
        # Calculate percentages
        pct_turning_up = (len(self.symbols_60m_turning_up) / total) * 100
        pct_keeping_down = (len(self.symbols_60m_keeping_down) / total) * 100
        pct_turning_down = (len(self.symbols_60m_turning_down) / total) * 100
        pct_keeping_up = (len(self.symbols_60m_keeping_up) / total) * 100
        pct_end_of_range = (len(self.symbols_end_of_proper_trading_range) / total) * 100
        pct_low_volume = (len(self.symbols_low_volume) / total) * 100
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}\n")
        
        print(f" - {len(self.new_symbols)} new symbols")
        print(f"   {self.new_symbols}\n")
        
        print(f" - {len(self.previous_symbols)} symbols from previous watch list")
        print(f"   {self.previous_symbols}\n")
        
        print(f" - {len(self.existing_position_symbols)} existing position symbols")
        print(f"   {self.existing_position_symbols}\n")
        
        print(f" - {len(self.symbols_end_of_proper_trading_range)} symbols end of proper trading range ({round(pct_end_of_range, 2)}%)")
        print(f"   {self.symbols_end_of_proper_trading_range}\n")
        
        print(f" - {len(self.symbols_low_volume)} symbols low volume ({round(pct_low_volume, 2)}%)")
        print(f"   {self.symbols_low_volume}\n")
        
        # Updated symbols
        update_symbols = self.new_symbols + self.double_check_symbols + self.existing_position_symbols
        symbols_no_duplicate = list(set(update_symbols))
        print(f" - {len(symbols_no_duplicate)} symbols are updated")
        print(f"   {symbols_no_duplicate}\n")
        
        print(f"\n{'='*60}")
        print(f"MARKET VARIATION INDICATORS")
        print(f"{'='*60}\n")
        
        print(f" - {len(self.symbols_60m_turning_up)} symbols 60m_turning_up ({round(pct_turning_up, 2)}%)")
        print(f"   {self.symbols_60m_turning_up}\n")
        
        print(f" - {len(self.symbols_60m_keeping_down)} symbols 60m_keeping_down ({round(pct_keeping_down, 2)}%)")
        print(f"   {self.symbols_60m_keeping_down}\n")
        
        print(f" - {len(self.symbols_60m_turning_down)} symbols 60m_turning_down ({round(pct_turning_down, 2)}%)")
        print(f"   {self.symbols_60m_turning_down}\n")
        
        print(f" - {len(self.symbols_60m_keeping_up)} symbols 60m_keeping_up ({round(pct_keeping_up, 2)}%)")
        print(f"   {self.symbols_60m_keeping_up}\n")
        
        # Save to database
        run_time = datetime.now()
        trading_date = run_time.date()
        
        self._save_to_database(
            run_time=run_time,
            trading_date=trading_date,
            new_symbols_count=len(self.new_symbols),
            total_symbols=len(symbols_no_duplicate),
            pct_turning_up=pct_turning_up,
            pct_keeping_down=pct_keeping_down,
            pct_turning_down=pct_turning_down,
            pct_keeping_up=pct_keeping_up,
            pct_end_of_range=pct_end_of_range,
            pct_low_volume=pct_low_volume
        )
        
        print(f"\n✓ Statistics saved to database for {trading_date}")
        
    def _save_to_database(self, run_time, trading_date, new_symbols_count, total_symbols,
                         pct_turning_up, pct_keeping_down, pct_turning_down, pct_keeping_up,
                         pct_end_of_range, pct_low_volume):
        """Save market variation statistics to database"""
        try:
            # Create table if doesn't exist
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS mv_daily_statistics (
                    id SERIAL PRIMARY KEY,
                    run_time TIMESTAMP NOT NULL,
                    trading_date DATE NOT NULL,
                    new_symbols_count INTEGER,
                    total_symbols INTEGER,
                    pct_turning_up NUMERIC,
                    pct_keeping_down NUMERIC,
                    pct_turning_down NUMERIC,
                    pct_keeping_up NUMERIC,
                    pct_end_of_range NUMERIC,
                    pct_low_volume NUMERIC,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(trading_date)
                )
            """)
            
            # Insert or update
            self.cursor.execute("""
                INSERT INTO mv_daily_statistics 
                    (run_time, trading_date, new_symbols_count, total_symbols,
                     pct_turning_up, pct_keeping_down, pct_turning_down, pct_keeping_up,
                     pct_end_of_range, pct_low_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (trading_date) 
                DO UPDATE SET
                    run_time = EXCLUDED.run_time,
                    new_symbols_count = EXCLUDED.new_symbols_count,
                    total_symbols = EXCLUDED.total_symbols,
                    pct_turning_up = EXCLUDED.pct_turning_up,
                    pct_keeping_down = EXCLUDED.pct_keeping_down,
                    pct_turning_down = EXCLUDED.pct_turning_down,
                    pct_keeping_up = EXCLUDED.pct_keeping_up,
                    pct_end_of_range = EXCLUDED.pct_end_of_range,
                    pct_low_volume = EXCLUDED.pct_low_volume
            """, (run_time, trading_date, new_symbols_count, total_symbols,
                  pct_turning_up, pct_keeping_down, pct_turning_down, pct_keeping_up,
                  pct_end_of_range, pct_low_volume))
            
            self.connection.commit()
        except Exception as e:
            print(f"Error saving to database: {e}")
            self.connection.rollback()
    
    def close(self):
        """Clean up resources"""
        self.input_handler.close()
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


if __name__ == "__main__":
    tracker = MarketVariationTracker()
    try:
        tracker.run_analysis()
    finally:
        tracker.close()
