-- Market Variation Trading System - Database Schema
-- ===================================================
-- This SQL file creates all necessary tables for the market variation
-- trading system including breakout metadata and daily statistics tracking.
--
-- Usage: psql -U postgres -d app -f mv_create_tables.sql

-- Table 1: Breakout Metadata
-- Stores manual input for each breakout including date, stop loss, and notes
CREATE TABLE IF NOT EXISTS mv_breakout_metadata (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    breakout_date DATE NOT NULL,
    stop_loss_price NUMERIC NOT NULL,
    entry_price NUMERIC,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(symbol, breakout_date)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_mv_breakout_symbol ON mv_breakout_metadata(symbol);
CREATE INDEX IF NOT EXISTS idx_mv_breakout_date ON mv_breakout_metadata(breakout_date);
CREATE INDEX IF NOT EXISTS idx_mv_breakout_active ON mv_breakout_metadata(is_active);

-- Comments for documentation
COMMENT ON TABLE mv_breakout_metadata IS 'Manual breakout metadata from graph analysis';
COMMENT ON COLUMN mv_breakout_metadata.symbol IS 'Stock ticker symbol';
COMMENT ON COLUMN mv_breakout_metadata.breakout_date IS 'Date when breakout occurred';
COMMENT ON COLUMN mv_breakout_metadata.stop_loss_price IS 'Stop loss price from graph analysis';
COMMENT ON COLUMN mv_breakout_metadata.entry_price IS 'Optional entry price';
COMMENT ON COLUMN mv_breakout_metadata.notes IS 'Additional notes about the setup';
COMMENT ON COLUMN mv_breakout_metadata.is_active IS 'Whether this breakout is still active/relevant';


-- Table 2: Daily Market Variation Statistics
-- Stores daily percentage distributions of indicator groups
CREATE TABLE IF NOT EXISTS mv_daily_statistics (
    id SERIAL PRIMARY KEY,
    run_time TIMESTAMP NOT NULL,
    trading_date DATE NOT NULL UNIQUE,
    new_symbols_count INTEGER,
    total_symbols INTEGER,
    pct_turning_up NUMERIC,
    pct_keeping_down NUMERIC,
    pct_turning_down NUMERIC,
    pct_keeping_up NUMERIC,
    pct_end_of_range NUMERIC,
    pct_low_volume NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster date-based queries
CREATE INDEX IF NOT EXISTS idx_mv_daily_trading_date ON mv_daily_statistics(trading_date);

-- Comments for documentation
COMMENT ON TABLE mv_daily_statistics IS 'Daily percentage distribution of indicator groups for market variation analysis';
COMMENT ON COLUMN mv_daily_statistics.trading_date IS 'The trading date for these statistics';
COMMENT ON COLUMN mv_daily_statistics.pct_turning_up IS 'Percentage of symbols in turning_up category';
COMMENT ON COLUMN mv_daily_statistics.pct_keeping_down IS 'Percentage of symbols in keeping_down category';
COMMENT ON COLUMN mv_daily_statistics.pct_turning_down IS 'Percentage of symbols in turning_down category';
COMMENT ON COLUMN mv_daily_statistics.pct_keeping_up IS 'Percentage of symbols in keeping_up category';
COMMENT ON COLUMN mv_daily_statistics.pct_end_of_range IS 'Percentage of symbols at end of proper trading range';
COMMENT ON COLUMN mv_daily_statistics.pct_low_volume IS 'Percentage of symbols with low volume';


-- Table 3: Symbol Categorization History
-- Tracks how each symbol was categorized on each day
CREATE TABLE IF NOT EXISTS mv_symbol_category_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trading_date DATE NOT NULL,
    category VARCHAR(20) NOT NULL,
    price NUMERIC,
    volume BIGINT,
    market_value NUMERIC,
    m_1d NUMERIC,
    h_1d NUMERIC,
    m_60m NUMERIC,
    h_60m NUMERIC,
    ema_10 NUMERIC,
    has_metadata BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, trading_date)
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_mv_category_symbol ON mv_symbol_category_history(symbol);
CREATE INDEX IF NOT EXISTS idx_mv_category_date ON mv_symbol_category_history(trading_date);
CREATE INDEX IF NOT EXISTS idx_mv_category_category ON mv_symbol_category_history(category);

-- Comments for documentation
COMMENT ON TABLE mv_symbol_category_history IS 'Historical record of how each symbol was categorized each day';
COMMENT ON COLUMN mv_symbol_category_history.category IS 'turning_up, keeping_down, turning_down, keeping_up, end_of_range, low_volume, other';
COMMENT ON COLUMN mv_symbol_category_history.m_1d IS 'Daily MACD value';
COMMENT ON COLUMN mv_symbol_category_history.h_1d IS 'Daily MACD histogram value';
COMMENT ON COLUMN mv_symbol_category_history.m_60m IS '60-minute MACD value';
COMMENT ON COLUMN mv_symbol_category_history.h_60m IS '60-minute MACD histogram value';
COMMENT ON COLUMN mv_symbol_category_history.has_metadata IS 'Whether symbol has breakout metadata';


-- Table 4: Position Sizing History
-- Track position sizing decisions based on market conditions
CREATE TABLE IF NOT EXISTS mv_position_sizing_history (
    id SERIAL PRIMARY KEY,
    trading_date DATE NOT NULL UNIQUE,
    position_multiplier NUMERIC NOT NULL,
    max_positions INTEGER NOT NULL,
    market_trend VARCHAR(20),
    trend_confidence NUMERIC,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for date-based queries
CREATE INDEX IF NOT EXISTS idx_mv_sizing_date ON mv_position_sizing_history(trading_date);

-- Comments
COMMENT ON TABLE mv_position_sizing_history IS 'Historical record of position sizing adjustments based on market conditions';
COMMENT ON COLUMN mv_position_sizing_history.position_multiplier IS 'Multiplier applied to base position size (0.5 to 1.5)';
COMMENT ON COLUMN mv_position_sizing_history.max_positions IS 'Maximum number of concurrent positions allowed';
COMMENT ON COLUMN mv_position_sizing_history.market_trend IS 'bullish, bearish, neutral, or mixed';
COMMENT ON COLUMN mv_position_sizing_history.trend_confidence IS 'Confidence percentage in the trend identification';


-- Table 5: Trading Performance Tracking
-- Enhanced tracking with market condition correlation
CREATE TABLE IF NOT EXISTS mv_trade_performance (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    entry_date DATE NOT NULL,
    entry_price NUMERIC NOT NULL,
    stop_loss_price NUMERIC,
    exit_date DATE,
    exit_price NUMERIC,
    shares INTEGER,
    pnl NUMERIC,
    pnl_percent NUMERIC,
    category_at_entry VARCHAR(20),
    market_trend_at_entry VARCHAR(20),
    pct_keeping_up_at_entry NUMERIC,
    holding_days INTEGER,
    exit_reason VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_mv_trade_symbol ON mv_trade_performance(symbol);
CREATE INDEX IF NOT EXISTS idx_mv_trade_entry_date ON mv_trade_performance(entry_date);
CREATE INDEX IF NOT EXISTS idx_mv_trade_exit_date ON mv_trade_performance(exit_date);

-- Comments
COMMENT ON TABLE mv_trade_performance IS 'Track trade performance with market condition correlation';
COMMENT ON COLUMN mv_trade_performance.category_at_entry IS 'Symbol category when position was entered';
COMMENT ON COLUMN mv_trade_performance.market_trend_at_entry IS 'Overall market trend at entry';
COMMENT ON COLUMN mv_trade_performance.pct_keeping_up_at_entry IS 'Percentage of stocks keeping up at entry';
COMMENT ON COLUMN mv_trade_performance.exit_reason IS 'stop_loss, target, time_based, discretionary, etc.';


-- Create view for easy analysis
CREATE OR REPLACE VIEW mv_current_market_snapshot AS
SELECT 
    s.trading_date,
    s.pct_turning_up,
    s.pct_keeping_down,
    s.pct_turning_down,
    s.pct_keeping_up,
    s.total_symbols,
    CASE 
        WHEN s.pct_keeping_up > 40 AND s.pct_turning_up > 20 THEN 'Strong Bullish'
        WHEN s.pct_keeping_up > 30 THEN 'Bullish'
        WHEN s.pct_keeping_down > 40 AND s.pct_turning_down > 20 THEN 'Strong Bearish'
        WHEN s.pct_keeping_down > 30 THEN 'Bearish'
        ELSE 'Neutral'
    END as market_condition,
    COUNT(DISTINCT m.symbol) as symbols_with_metadata
FROM mv_daily_statistics s
LEFT JOIN mv_breakout_metadata m ON m.is_active = TRUE
WHERE s.trading_date = (SELECT MAX(trading_date) FROM mv_daily_statistics)
GROUP BY s.trading_date, s.pct_turning_up, s.pct_keeping_down, 
         s.pct_turning_down, s.pct_keeping_up, s.total_symbols;

COMMENT ON VIEW mv_current_market_snapshot IS 'Current market condition snapshot with metadata count';


-- Create view for performance analysis by market condition
CREATE OR REPLACE VIEW mv_performance_by_condition AS
SELECT 
    market_trend_at_entry,
    category_at_entry,
    COUNT(*) as trade_count,
    AVG(pnl_percent) as avg_pnl_percent,
    AVG(holding_days) as avg_holding_days,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
    ROUND(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC * 100, 2) as win_rate
FROM mv_trade_performance
WHERE exit_date IS NOT NULL
GROUP BY market_trend_at_entry, category_at_entry
ORDER BY market_trend_at_entry, avg_pnl_percent DESC;

COMMENT ON VIEW mv_performance_by_condition IS 'Analyze trade performance grouped by market conditions';


-- Insert sample/default data if needed (optional)
-- This can help with testing
INSERT INTO mv_daily_statistics (
    run_time, trading_date, new_symbols_count, total_symbols,
    pct_turning_up, pct_keeping_down, pct_turning_down, pct_keeping_up,
    pct_end_of_range, pct_low_volume
) VALUES (
    CURRENT_TIMESTAMP, 
    CURRENT_DATE,
    0, 0, 0, 0, 0, 0, 0, 0
) ON CONFLICT (trading_date) DO NOTHING;


-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;


-- Display table summary
SELECT 
    'mv_breakout_metadata' as table_name,
    COUNT(*) as row_count
FROM mv_breakout_metadata
UNION ALL
SELECT 
    'mv_daily_statistics',
    COUNT(*)
FROM mv_daily_statistics
UNION ALL
SELECT 
    'mv_symbol_category_history',
    COUNT(*)
FROM mv_symbol_category_history
UNION ALL
SELECT 
    'mv_position_sizing_history',
    COUNT(*)
FROM mv_position_sizing_history
UNION ALL
SELECT 
    'mv_trade_performance',
    COUNT(*)
FROM mv_trade_performance;


-- Success message
SELECT '✓ Market Variation tables created successfully!' as status;
