# Market Variation System - Paper Account 1 Configuration
# =========================================================
# This config is specifically for the MV trading system running on Linode
# Uses Paper Account 1 for testing the market variation strategy

# Paper Account 1 - For MV Trading System
API_KEY = 'PKFPXIK488ZVOTTE62E0'
SECRET_KEY = 'eKA6lLM0CGvfsA3LeoS65bgbX8VkiEdvlaOPvCM0'
API_URL = 'https://paper-api.alpaca.markets'

HEADERS = {
    'APCA-API-KEY-ID': API_KEY,
    'APCA-API-SECRET-KEY': SECRET_KEY
}

# Database Configuration - Linode Server
DB_FILE = '/root/breakout/app.db'
BARS_URL = 'https://data.alpaca.markets/v2'

# PostgreSQL Configuration - Update for your Linode setup
DB_HOST = 'localhost'
DB_USER = 'postgres'
DB_PASS = 'Apiwat'  # Update this for your Linode PostgreSQL password
DB_PORT = 5432
DB_NAME = 'app_mv'  # Separate database for MV system
DB_URL = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# MV Strategy Symbols (will be updated dynamically from database)
BREAKOUT_SYMBOLS_5MX0_AB = []

# MV System Settings
MV_BASE_POSITION_VALUE = 1000  # $1,000 base position
MV_MAX_POSITIONS_DEFAULT = 10
MV_POSITION_MULTIPLIER_MIN = 0.5
MV_POSITION_MULTIPLIER_MAX = 1.5

# Trading Hours Settings (for cron scheduling)
# These match your existing cron schedule
CRON_SCHEDULES = {
    'evening_check': '30 21 * * 1-5',     # 9:30 PM EST
    'late_evening': '45 22-23 * * 1-5',   # 10:45-11:45 PM EST
    'early_morning': '45 0-3 * * 2-6'     # 12:45-3:45 AM EST
}

# Logging Configuration
LOG_DIR = '/root/logs'
LOG_FILE_PREFIX = 'MV-Breakout'
