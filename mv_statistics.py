"""
Market Variation Statistics Tracker
====================================
This module provides tools to analyze and track market variation statistics over time.
It helps identify market trends and conditions by analyzing percentage changes
in indicator groups day-over-day.

Key Features:
- Retrieve historical statistics
- Calculate moving averages of percentages
- Identify market condition trends
- Export data for analysis

Usage:
    from mv_statistics import StatisticsAnalyzer
    
    analyzer = StatisticsAnalyzer()
    recent_stats = analyzer.get_recent_statistics(days=30)
    trend = analyzer.identify_market_trend()
"""

import psycopg2
import psycopg2.extras
import config
import pandas as pd
from datetime import datetime, timedelta


class StatisticsAnalyzer:
    """Analyze market variation statistics over time"""
    
    def __init__(self):
        self.connection = psycopg2.connect(
            host=config.DB_HOST,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
    def get_recent_statistics(self, days=30):
        """
        Get statistics for the last N days
        
        Args:
            days (int): Number of days to retrieve
            
        Returns:
            pandas.DataFrame: Statistics with dates as index
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        self.cursor.execute("""
            SELECT 
                trading_date,
                run_time,
                new_symbols_count,
                total_symbols,
                pct_turning_up,
                pct_keeping_down,
                pct_turning_down,
                pct_keeping_up,
                pct_end_of_range,
                pct_low_volume
            FROM mv_daily_statistics
            WHERE trading_date >= %s
            ORDER BY trading_date DESC
        """, (cutoff_date,))
        
        rows = self.cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(row) for row in rows])
        df['trading_date'] = pd.to_datetime(df['trading_date'])
        df = df.sort_values('trading_date')
        df.set_index('trading_date', inplace=True)
        
        return df
    
    def get_latest_statistics(self):
        """Get the most recent statistics record"""
        self.cursor.execute("""
            SELECT *
            FROM mv_daily_statistics
            ORDER BY trading_date DESC
            LIMIT 1
        """)
        
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def calculate_moving_averages(self, days=30, window=5):
        """
        Calculate moving averages of percentage indicators
        
        Args:
            days (int): Number of days to retrieve
            window (int): Moving average window size
            
        Returns:
            pandas.DataFrame: DataFrame with moving averages
        """
        df = self.get_recent_statistics(days)
        
        if df.empty:
            return df
        
        # Calculate moving averages for key indicators
        pct_cols = ['pct_turning_up', 'pct_keeping_down', 'pct_turning_down', 'pct_keeping_up']
        
        for col in pct_cols:
            df[f'{col}_ma{window}'] = df[col].rolling(window=window).mean()
        
        return df
    
    def identify_market_trend(self, days=10):
        """
        Identify current market trend based on recent data
        
        Returns a dict with:
        - trend: 'bullish', 'bearish', 'neutral', or 'mixed'
        - confidence: percentage confidence in the trend
        - indicators: dict of supporting indicators
        """
        df = self.get_recent_statistics(days)
        
        if df.empty or len(df) < 3:
            return {
                'trend': 'unknown',
                'confidence': 0,
                'reason': 'Insufficient data',
                'indicators': {}
            }
        
        # Get latest values
        latest = df.iloc[-1]
        
        # Handle None/NaN values by filling with 0
        df = df.fillna(0)
        latest = df.iloc[-1]
        
        # Calculate trends (positive slope = increasing)
        turning_up_trend = (df['pct_turning_up'].iloc[-1] - df['pct_turning_up'].iloc[0]) / len(df)
        keeping_up_trend = (df['pct_keeping_up'].iloc[-1] - df['pct_keeping_up'].iloc[0]) / len(df)
        turning_down_trend = (df['pct_turning_down'].iloc[-1] - df['pct_turning_down'].iloc[0]) / len(df)
        keeping_down_trend = (df['pct_keeping_down'].iloc[-1] - df['pct_keeping_down'].iloc[0]) / len(df)
        
        # Bullish indicators
        bullish_score = 0
        if latest['pct_keeping_up'] > 40:
            bullish_score += 2
        if latest['pct_turning_up'] > 20:
            bullish_score += 1.5
        if keeping_up_trend > 0:
            bullish_score += 1
        if turning_up_trend > 0:
            bullish_score += 0.5
        
        # Bearish indicators
        bearish_score = 0
        if latest['pct_keeping_down'] > 40:
            bearish_score += 2
        if latest['pct_turning_down'] > 20:
            bearish_score += 1.5
        if keeping_down_trend > 0:
            bearish_score += 1
        if turning_down_trend > 0:
            bearish_score += 0.5
        
        # Determine trend
        total_score = bullish_score + bearish_score
        if total_score == 0:
            trend = 'neutral'
            confidence = 0
        elif bullish_score > bearish_score * 1.5:
            trend = 'bullish'
            confidence = min(100, (bullish_score / total_score) * 100)
        elif bearish_score > bullish_score * 1.5:
            trend = 'bearish'
            confidence = min(100, (bearish_score / total_score) * 100)
        else:
            trend = 'mixed'
            confidence = 50
        
        return {
            'trend': trend,
            'confidence': round(confidence, 1),
            'bullish_score': round(bullish_score, 2),
            'bearish_score': round(bearish_score, 2),
            'indicators': {
                'pct_turning_up': float(latest['pct_turning_up']) if latest['pct_turning_up'] is not None else 0.0,
                'pct_keeping_up': float(latest['pct_keeping_up']) if latest['pct_keeping_up'] is not None else 0.0,
                'pct_turning_down': float(latest['pct_turning_down']) if latest['pct_turning_down'] is not None else 0.0,
                'pct_keeping_down': float(latest['pct_keeping_down']) if latest['pct_keeping_down'] is not None else 0.0,
                'turning_up_trend': round(turning_up_trend, 2),
                'keeping_up_trend': round(keeping_up_trend, 2),
                'turning_down_trend': round(turning_down_trend, 2),
                'keeping_down_trend': round(keeping_down_trend, 2)
            }
        }
    
    def get_position_sizing_recommendation(self):
        """
        Get recommended position sizing adjustments based on market conditions
        
        Returns:
            dict with sizing recommendations
        """
        trend_info = self.identify_market_trend(days=10)
        latest = self.get_latest_statistics()
        
        if not latest:
            return {
                'position_size_multiplier': 1.0,
                'max_positions': 10,
                'reasoning': 'No data available - using default settings'
            }
        
        # Base multiplier
        multiplier = 1.0
        max_positions = 10
        reasoning = []
        
        # Adjust based on trend
        if trend_info['trend'] == 'bullish' and trend_info['confidence'] > 60:
            multiplier = 1.2
            max_positions = 12
            reasoning.append(f"Strong bullish trend ({trend_info['confidence']}% confidence)")
        elif trend_info['trend'] == 'bearish' and trend_info['confidence'] > 60:
            multiplier = 0.7
            max_positions = 8
            reasoning.append(f"Strong bearish trend ({trend_info['confidence']}% confidence)")
        elif trend_info['trend'] == 'mixed':
            multiplier = 0.9
            max_positions = 9
            reasoning.append("Mixed market conditions - reducing exposure")
        
        # Adjust based on keeping_up percentage
        keeping_up_pct = latest['pct_keeping_up'] if latest['pct_keeping_up'] is not None else 0
        if keeping_up_pct > 50:
            multiplier *= 1.1
            reasoning.append(f"High percentage keeping up ({keeping_up_pct:.1f}%)")
        elif keeping_up_pct < 20:
            multiplier *= 0.9
            reasoning.append(f"Low percentage keeping up ({keeping_up_pct:.1f}%)")
        
        # Adjust based on turning_down percentage (risk factor)
        turning_down_pct = latest['pct_turning_down'] if latest['pct_turning_down'] is not None else 0
        if turning_down_pct > 30:
            multiplier *= 0.85
            reasoning.append(f"High percentage turning down ({turning_down_pct:.1f}%) - increase caution")
        
        # Cap multiplier
        multiplier = max(0.5, min(1.5, multiplier))
        
        return {
            'position_size_multiplier': round(multiplier, 2),
            'max_positions': max_positions,
            'trend': trend_info['trend'],
            'confidence': trend_info['confidence'],
            'reasoning': ' | '.join(reasoning),
            'latest_stats': {
                'keeping_up': f"{keeping_up_pct:.1f}%",
                'turning_up': f"{latest['pct_turning_up'] if latest['pct_turning_up'] is not None else 0:.1f}%",
                'turning_down': f"{turning_down_pct:.1f}%",
                'keeping_down': f"{latest['pct_keeping_down'] if latest['pct_keeping_down'] is not None else 0:.1f}%"
            }
        }
    
    def compare_periods(self, period1_days=7, period2_days=7):
        """
        Compare two time periods to see how market conditions have changed
        
        Args:
            period1_days (int): Most recent period length
            period2_days (int): Previous period length
            
        Returns:
            dict: Comparison results
        """
        # Get data for both periods
        total_days = period1_days + period2_days
        df = self.get_recent_statistics(days=total_days)
        
        if len(df) < total_days / 2:  # Need at least half the data
            return {'error': 'Insufficient data for comparison'}
        
        # Split into two periods
        period1 = df.iloc[-period1_days:] if len(df) >= period1_days else df
        period2 = df.iloc[-(period1_days + period2_days):-period1_days] if len(df) >= period1_days + period2_days else pd.DataFrame()
        
        if period2.empty:
            return {'error': 'Insufficient data for second period'}
        
        # Calculate averages
        p1_avg_keeping_up = period1['pct_keeping_up'].mean()
        p2_avg_keeping_up = period2['pct_keeping_up'].mean()
        
        p1_avg_turning_down = period1['pct_turning_down'].mean()
        p2_avg_turning_down = period2['pct_turning_down'].mean()
        
        p1_avg_turning_up = period1['pct_turning_up'].mean()
        p2_avg_turning_up = period2['pct_turning_up'].mean()
        
        # Calculate changes
        change_keeping_up = p1_avg_keeping_up - p2_avg_keeping_up
        change_turning_down = p1_avg_turning_down - p2_avg_turning_down
        change_turning_up = p1_avg_turning_up - p2_avg_turning_up
        
        # Determine overall change
        if change_keeping_up > 10 and change_turning_down < -5:
            condition_change = 'improving'
        elif change_keeping_up < -10 and change_turning_down > 5:
            condition_change = 'deteriorating'
        else:
            condition_change = 'stable'
        
        return {
            'period1_days': period1_days,
            'period2_days': period2_days,
            'condition_change': condition_change,
            'changes': {
                'keeping_up': round(change_keeping_up, 2),
                'turning_down': round(change_turning_down, 2),
                'turning_up': round(change_turning_up, 2)
            },
            'period1_averages': {
                'keeping_up': round(p1_avg_keeping_up, 2),
                'turning_down': round(p1_avg_turning_down, 2),
                'turning_up': round(p1_avg_turning_up, 2)
            },
            'period2_averages': {
                'keeping_up': round(p2_avg_keeping_up, 2),
                'turning_down': round(p2_avg_turning_down, 2),
                'turning_up': round(p2_avg_turning_up, 2)
            }
        }
    
    def export_to_csv(self, filename, days=90):
        """Export statistics to CSV file"""
        df = self.get_recent_statistics(days)
        df.to_csv(filename)
        print(f"✓ Exported {len(df)} days of statistics to {filename}")
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience functions
def get_current_market_condition():
    """Quick function to get current market condition"""
    with StatisticsAnalyzer() as analyzer:
        return analyzer.identify_market_trend()


def get_position_sizing():
    """Quick function to get position sizing recommendation"""
    with StatisticsAnalyzer() as analyzer:
        return analyzer.get_position_sizing_recommendation()


if __name__ == "__main__":
    with StatisticsAnalyzer() as analyzer:
        print("\n" + "="*60)
        print("Market Variation Statistics Analysis")
        print("="*60 + "\n")
        
        # Get latest stats
        latest = analyzer.get_latest_statistics()
        if latest:
            print(f"Latest Statistics (Date: {latest['trading_date']})")
            print(f"  Keeping Up:    {latest['pct_keeping_up'] if latest['pct_keeping_up'] is not None else 0:.1f}%")
            print(f"  Turning Up:    {latest['pct_turning_up'] if latest['pct_turning_up'] is not None else 0:.1f}%")
            print(f"  Turning Down:  {latest['pct_turning_down'] if latest['pct_turning_down'] is not None else 0:.1f}%")
            print(f"  Keeping Down:  {latest['pct_keeping_down'] if latest['pct_keeping_down'] is not None else 0:.1f}%")
            print(f"  Total Symbols: {latest['total_symbols']}")
        
        # Get market trend
        print("\n" + "-"*60)
        trend = analyzer.identify_market_trend(days=10)
        print(f"\nMarket Trend Analysis (10 days)")
        print(f"  Trend:      {trend['trend'].upper()}")
        print(f"  Confidence: {trend['confidence']}%")
        print(f"  Bullish Score: {trend['bullish_score']}")
        print(f"  Bearish Score: {trend['bearish_score']}")
        
        # Get position sizing
        print("\n" + "-"*60)
        sizing = analyzer.get_position_sizing_recommendation()
        print(f"\nPosition Sizing Recommendation")
        print(f"  Position Multiplier: {sizing['position_size_multiplier']}x")
        print(f"  Max Positions:       {sizing['max_positions']}")
        print(f"  Reasoning:           {sizing['reasoning']}")
        
        # Compare periods
        print("\n" + "-"*60)
        comparison = analyzer.compare_periods(period1_days=7, period2_days=7)
        if 'error' not in comparison:
            print(f"\nPeriod Comparison (Last 7 days vs Previous 7 days)")
            print(f"  Condition Change: {comparison['condition_change'].upper()}")
            print(f"  Keeping Up Change:    {comparison['changes']['keeping_up']:+.2f}%")
            print(f"  Turning Down Change:  {comparison['changes']['turning_down']:+.2f}%")
        
        print("\n" + "="*60)
