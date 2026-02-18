"""
Market Variation-Adjusted Breakout Trading System - Paper Account
==================================================================
This version uses Paper Account 1 and is designed to run on Linode server
with cron scheduling for 60MXU strategy timing.

Usage:
    python breakout_mv_paper.py [--dry-run]
"""

import sys
import os

# Use paper account config
import config_mv_paper as config

import requests
import tulipy
import numpy
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
import datetime as dt
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from helpers import calculate_quantity
import pandas as pd
import pytz
import pandas_ta as ta
import psycopg2
import psycopg2.extras

# Import our market variation modules
from mv_statistics import StatisticsAnalyzer, get_position_sizing
from mv_input_handler import get_breakout_metadata


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


def compute_rsi(df, length=14):
    """Compute RSI indicator"""
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


class MarketVariationBreakoutTrader:
    """Enhanced breakout trader with market variation position sizing - Paper Account"""
    
    def __init__(self, symbols=None, dry_run=False):
        """
        Initialize trader with Paper Account 1
        
        Args:
            symbols (list): List of symbols to trade, or None for database symbols
            dry_run (bool): If True, don't place actual orders
        """
        self.api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
        self.dry_run = dry_run
        
        # Get symbols from database if not provided
        if symbols is None:
            symbols = self._get_symbols_from_db()
        self.symbols = symbols
        
        # Database connection
        self.connection = psycopg2.connect(
            host=config.DB_HOST,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get market condition and position sizing
        self.market_stats = self._get_market_statistics()
        self.position_sizing = self._get_position_sizing_params()
        
        # Get current positions
        self.positions = self.api.list_positions()
        self.position_symbols = [p.symbol for p in self.positions]
        
        # Get account info
        self.account = self.api.get_account()
        self.buying_power = float(self.account.buying_power)
        self.portfolio_value = float(self.account.portfolio_value)
        
        self._print_header()
    
    def _get_symbols_from_db(self):
        """Get symbols from database"""
        try:
            connection = psycopg2.connect(
                host=config.DB_HOST,
                database=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASS
            )
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cursor.execute("""
                SELECT id FROM strategy WHERE name = 'After Breakout_5MX0'
            """)
            strategy_result = cursor.fetchone()
            
            if strategy_result:
                strategy_id = strategy_result['id']
                cursor.execute("""
                    SELECT DISTINCT symbol
                    FROM stock
                    JOIN stock_strategy ON stock_strategy.stock_id = stock.id
                    WHERE stock_strategy.strategy_id = %s
                """, (strategy_id,))
                symbols = [row['symbol'] for row in cursor.fetchall()]
            else:
                # Fallback to active breakout symbols
                cursor.execute("""
                    SELECT DISTINCT symbol
                    FROM mv_breakout_metadata
                    WHERE is_active = TRUE
                """)
                symbols = [row['symbol'] for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            return symbols if symbols else []
        except Exception as e:
            print(f"Error getting symbols from database: {e}")
            return []
    
    def _print_header(self):
        """Print system header"""
        print(f"\n{'='*70}")
        print(f"Market Variation Breakout Trading System - PAPER ACCOUNT")
        print(f"{'='*70}\n")
        print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}")
        print(f"\nAccount Status:")
        print(f"  Account: Paper Account 1")
        print(f"  Portfolio Value: ${self.portfolio_value:,.2f}")
        print(f"  Buying Power:    ${self.buying_power:,.2f}")
        print(f"  Current Positions: {len(self.positions)}")
        print(f"\nMarket Conditions:")
        print(f"  Trend: {self.position_sizing.get('trend', 'N/A').upper()}")
        print(f"  Confidence: {self.position_sizing.get('confidence', 0)}%")
        print(f"  Position Multiplier: {self.position_sizing.get('position_size_multiplier', 1.0)}x")
        print(f"  Max Positions: {self.position_sizing.get('max_positions', 10)}")
        print(f"  Reasoning: {self.position_sizing.get('reasoning', 'N/A')}")
        print(f"\n{'='*70}\n")
        
        if self.dry_run:
            print("⚠️  DRY RUN MODE - No actual orders will be placed\n")
    
    def _get_market_statistics(self):
        """Get latest market statistics"""
        try:
            with StatisticsAnalyzer() as analyzer:
                return analyzer.get_latest_statistics()
        except Exception as e:
            print(f"Warning: Could not fetch market statistics: {e}")
            return None
    
    def _get_position_sizing_params(self):
        """Get position sizing parameters based on market conditions"""
        try:
            return get_position_sizing()
        except Exception as e:
            print(f"Warning: Could not fetch position sizing: {e}")
            return {
                'position_size_multiplier': 1.0,
                'max_positions': 10,
                'trend': 'neutral',
                'confidence': 0,
                'reasoning': 'Using defaults due to error'
            }
    
    def calculate_position_size(self, symbol, price, base_position_value=None):
        """
        Calculate position size with market variation adjustment
        
        Args:
            symbol (str): Stock symbol
            price (float): Current price
            base_position_value (float): Base position value in dollars
            
        Returns:
            int: Number of shares to buy
        """
        if base_position_value is None:
            base_position_value = config.MV_BASE_POSITION_VALUE
        
        # Apply market condition multiplier
        adjusted_value = base_position_value * self.position_sizing['position_size_multiplier']
        
        # Check if symbol has specific metadata
        metadata = get_breakout_metadata(symbol=symbol, active_only=True)
        if metadata:
            # Symbol has breakout metadata - could add custom logic here
            pass
        
        # Calculate shares
        shares = int(adjusted_value / price)
        
        # Ensure we don't exceed buying power
        max_shares_by_bp = int(self.buying_power / price)
        shares = min(shares, max_shares_by_bp)
        
        return shares
    
    def check_max_positions(self):
        """Check if we can open new positions based on market conditions"""
        current_positions = len(self.positions)
        max_allowed = self.position_sizing['max_positions']
        
        can_add = current_positions < max_allowed
        
        if not can_add:
            print(f"⚠️  Max positions reached ({current_positions}/{max_allowed})")
        
        return can_add, current_positions, max_allowed
    
    def should_enter_position(self, symbol, indicators):
        """Determine if we should enter a position"""
        if symbol in self.position_symbols:
            return False, "Already in position"
        
        can_add, current, max_allowed = self.check_max_positions()
        if not can_add:
            return False, f"Max positions reached ({current}/{max_allowed})"
        
        if indicators.get('M_1d') is None or indicators.get('H_1d') is None:
            return False, "Missing daily MACD data"
        
        if indicators.get('M_60m_C0') is None or indicators.get('H_60m_C0') is None:
            return False, "Missing 60m MACD data"
        
        if indicators['M_1d'] < 0 or indicators['H_1d'] < 0:
            return False, "Daily MACD not bullish"
        
        if indicators.get('price') and indicators.get('ema_10'):
            if indicators['price'] < indicators['ema_10'] * 0.95:
                return False, "Price too far below EMA"
        
        if indicators.get('volume') and indicators['volume'] < 700000:
            return False, "Volume too low"
        
        m_60m = indicators['M_60m_C0']
        h_60m = indicators['H_60m_C0']
        m_60m_p1 = indicators.get('M_60m_P1', 0)
        
        if m_60m > 0 and m_60m > m_60m_p1 and h_60m > 0:
            return True, "Strong 60m uptrend (keeping up)"
        
        if m_60m < 0 and m_60m > m_60m_p1 and h_60m < 0:
            if self.position_sizing['trend'] in ['bullish', 'neutral']:
                return True, "60m turning up (early entry)"
            else:
                return False, "60m turning up but market conditions unfavorable"
        
        return False, "Indicators don't meet entry criteria"
    
    def should_exit_position(self, symbol, current_price, indicators):
        """Determine if we should exit a position"""
        metadata = get_breakout_metadata(symbol=symbol, active_only=True)
        if metadata and len(metadata) > 0:
            stop_loss_price = float(metadata[0]['stop_loss_price'])
            if current_price <= stop_loss_price:
                return True, f"Stop loss hit (${stop_loss_price})"
        
        if indicators.get('M_1d') is not None and indicators['M_1d'] < 0:
            return True, "Daily MACD turned negative"
        
        if indicators.get('H_1d') is not None and indicators['H_1d'] < 0:
            return True, "Daily MACD histogram turned negative"
        
        if indicators.get('price') and indicators.get('ema_10'):
            if indicators['price'] < indicators['ema_10'] * 0.93:
                return True, "Price dropped significantly below EMA (>7%)"
        
        if indicators.get('M_60m_C0') and indicators.get('H_60m_C0'):
            m_60m = indicators['M_60m_C0']
            h_60m = indicators['H_60m_C0']
            m_60m_p1 = indicators.get('M_60m_P1', 0)
            
            if m_60m < m_60m_p1 and h_60m < 0:
                return True, "60m trend turning down"
        
        if self.position_sizing['trend'] == 'bearish' and self.position_sizing['confidence'] > 70:
            if indicators.get('M_60m_C0', 0) < 0:
                return True, "Strong bearish market + weak 60m momentum"
        
        return False, "Hold"
    
    def place_order(self, symbol, side, qty):
        """Place market order"""
        if self.dry_run:
            print(f"   [DRY RUN] Would place {side.upper()} order: {qty} shares of {symbol}")
            return None
        
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='day'
            )
            print(f"   ✓ {side.upper()} order placed: {qty} shares of {symbol}")
            return order
        except Exception as e:
            print(f"   ✗ Error placing {side} order for {symbol}: {e}")
            return None
    
    def get_indicators(self, symbol):
        """Get technical indicators for a symbol"""
        try:
            day_req = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=pd.Timestamp.now() - pd.Timedelta(days=180)
            )
            client = StockHistoricalDataClient(config.API_KEY, config.SECRET_KEY)
            day_bars = client.get_stock_bars(day_req).df
            
            if day_bars.empty:
                return None
            
            day_bars.columns = [col.title() if col.lower() in ['open', 'close', 'high', 'low', 'volume'] else col for col in day_bars.columns]
            
            closes_1d = numpy.array(day_bars['Close'])
            volume_1d = numpy.array(day_bars['Volume'])
            closes_C0 = closes_1d[-1]
            volume_C0 = volume_1d[-1]
            
            day_bars.columns = [col.lower() for col in day_bars.columns]
            macd_1 = day_bars.ta.macd()
            H_1d_C0 = round(macd_1['MACDh_12_26_9'][-1], 4) if 'MACDh_12_26_9' in macd_1.columns else None
            M_1d_C0 = round(macd_1['MACD_12_26_9'][-1], 4) if 'MACD_12_26_9' in macd_1.columns else None
            day_bars.columns = [col.title() for col in day_bars.columns]
            
            ema_10_C0 = tulipy.ema(numpy.array(closes_1d), period=10)[-1]
            
            minute_5_req = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame(5, TimeFrameUnit.Minute),
                start=pd.Timestamp.now() - pd.Timedelta(days=10)
            )
            minute_5_bars = client.get_stock_bars(minute_5_req).df
            
            if minute_5_bars.empty:
                return {
                    'price': closes_C0,
                    'volume': volume_C0,
                    'ema_10': ema_10_C0,
                    'M_1d': M_1d_C0,
                    'H_1d': H_1d_C0,
                    'M_60m_C0': None,
                    'H_60m_C0': None,
                    'M_60m_P1': None
                }
            
            minute_5_bars.columns = [col.lower() for col in minute_5_bars.columns]
            
            ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
            minute_60_bars = minute_5_bars[ohlcv_cols].resample('60min').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna(how='all')
            
            if len(minute_60_bars) >= 3:
                macd_60 = compute_macd(minute_60_bars, fast=12, slow=26, signal=9)
                M_60m_C0 = round(macd_60['MACD_12_26_9'].iloc[-1], 4) if 'MACD_12_26_9' in macd_60.columns else None
                M_60m_P1 = round(macd_60['MACD_12_26_9'].iloc[-2], 4) if 'MACD_12_26_9' in macd_60.columns else None
                H_60m_C0 = round(macd_60['MACDh_12_26_9'].iloc[-1], 4) if 'MACDh_12_26_9' in macd_60.columns else None
            else:
                M_60m_C0 = M_60m_P1 = H_60m_C0 = None
            
            return {
                'price': closes_C0,
                'volume': volume_C0,
                'ema_10': ema_10_C0,
                'M_1d': M_1d_C0,
                'H_1d': H_1d_C0,
                'M_60m_C0': M_60m_C0,
                'H_60m_C0': H_60m_C0,
                'M_60m_P1': M_60m_P1
            }
            
        except Exception as e:
            print(f"   Error getting indicators for {symbol}: {e}")
            return None
    
    def run(self):
        """Execute trading strategy"""
        print(f"Processing {len(self.symbols)} symbols...\n")
        
        entries = []
        exits = []
        holds = []
        
        for symbol in self.symbols:
            print(f"\n{symbol}")
            print("-" * 40)
            
            indicators = self.get_indicators(symbol)
            if not indicators:
                print("  ⚠️  Could not fetch indicators")
                continue
            
            print(f"  Price: ${indicators['price']:.2f}  |  EMA10: ${indicators['ema_10']:.2f}")
            print(f"  1D MACD: {indicators['M_1d']}  |  1D Hist: {indicators['H_1d']}")
            if indicators['M_60m_C0'] is not None:
                print(f"  60M MACD: {indicators['M_60m_C0']}  |  60M Hist: {indicators['H_60m_C0']}")
            
            if symbol in self.position_symbols:
                should_exit, reason = self.should_exit_position(symbol, indicators['price'], indicators)
                if should_exit:
                    print(f"  🔴 EXIT SIGNAL: {reason}")
                    position = next((p for p in self.positions if p.symbol == symbol), None)
                    if position:
                        qty = int(float(position.qty))
                        self.place_order(symbol, 'sell', qty)
                        exits.append((symbol, reason))
                else:
                    print(f"  ✓ HOLD: {reason}")
                    holds.append(symbol)
            else:
                should_enter, reason = self.should_enter_position(symbol, indicators)
                if should_enter:
                    print(f"  🟢 ENTRY SIGNAL: {reason}")
                    qty = self.calculate_position_size(symbol, indicators['price'])
                    if qty > 0:
                        print(f"     Position size: {qty} shares (${qty * indicators['price']:.2f})")
                        self.place_order(symbol, 'buy', qty)
                        entries.append((symbol, reason, qty))
                    else:
                        print(f"     ⚠️  Insufficient buying power")
                else:
                    print(f"  ⊗ No entry: {reason}")
        
        # Summary
        print(f"\n{'='*70}")
        print("EXECUTION SUMMARY")
        print(f"{'='*70}\n")
        print(f"Entry Signals:  {len(entries)}")
        for symbol, reason, qty in entries:
            print(f"  • {symbol}: {qty} shares - {reason}")
        
        print(f"\nExit Signals:   {len(exits)}")
        for symbol, reason in exits:
            print(f"  • {symbol}: {reason}")
        
        print(f"\nHolding:        {len(holds)}")
        for symbol in holds:
            print(f"  • {symbol}")
        
        print(f"\n{'='*70}\n")
        
        self._save_position_sizing_decision()
    
    def _save_position_sizing_decision(self):
        """Save today's position sizing decision to database"""
        try:
            trading_date = datetime.now().date()
            self.cursor.execute("""
                INSERT INTO mv_position_sizing_history
                    (trading_date, position_multiplier, max_positions, market_trend, 
                     trend_confidence, reasoning)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (trading_date)
                DO UPDATE SET
                    position_multiplier = EXCLUDED.position_multiplier,
                    max_positions = EXCLUDED.max_positions,
                    market_trend = EXCLUDED.market_trend,
                    trend_confidence = EXCLUDED.trend_confidence,
                    reasoning = EXCLUDED.reasoning
            """, (
                trading_date,
                self.position_sizing['position_size_multiplier'],
                self.position_sizing['max_positions'],
                self.position_sizing['trend'],
                self.position_sizing['confidence'],
                self.position_sizing['reasoning']
            ))
            self.connection.commit()
        except Exception as e:
            print(f"Error saving position sizing: {e}")
            self.connection.rollback()
    
    def close(self):
        """Clean up resources"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


if __name__ == "__main__":
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    trader = MarketVariationBreakoutTrader(dry_run=dry_run)
    try:
        trader.run()
    finally:
        trader.close()
