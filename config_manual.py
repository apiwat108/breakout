# Configuration for Manual Breakout Entry System

# Use Paper Account 1 for testing, switch to Live for production
# Paper Account 1
API_KEY = 'PKFPXIK488ZVOTTE62E0'
SECRET_KEY = 'eKA6lLM0CGvfsA3LeoS65bgbX8VkiEdvlaOPvCM0'
API_URL = 'https://paper-api.alpaca.markets'

# # Live Account (uncomment when ready for live trading)
# API_KEY = 'AK9WJUKS418ZU6Y8LM66'
# SECRET_KEY = 'JBu0oIEfoUUSuMtu68XglUruZdDBPbzZdAhs8a2m'
# API_URL = 'https://api.alpaca.markets'

HEADERS = {
    'APCA-API-KEY-ID': API_KEY,
    'APCA-API-SECRET-KEY': SECRET_KEY
}

# Database Configuration
DB_HOST = 'localhost'
DB_USER = 'postgres'
DB_PASS = 'Apiwat'
DB_PORT = 5432
DB_NAME = 'app'  # Use main database for manual breakout system
DB_URL = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Manual Breakout System Settings
RISK_PERCENTAGE = 0.02  # 2% risk per trade
MAX_POSITION_VALUE = 10000  # Maximum position value in USD
MIN_POSITION_VALUE = 500  # Minimum position value in USD

# Monitoring Settings
TRACK_VIRTUAL_ENTRIES = True  # Track insufficient funds entries as virtual
CONTINUE_TRACKING_AFTER_PARTIAL_EXIT = True  # Keep tracking after partial sells until fully exited

# Alpaca Data API URL
BARS_URL = 'https://data.alpaca.markets/v2'

# ========== MANUAL BREAKOUT ENTRIES ==========
# This list is updated by breakout_manual_entry.py on MacBook
# Format: {'symbol': 'AAPL', 'breakout_date': '2026-02-26', 'stop_loss': 145.00, 'entry_id': 1}
# Commit this file to GitHub after adding entries, then git pull on Linode
MANUAL_BREAKOUT_ENTRIES = [
    # Example (remove this when you add real entries):
    # {'symbol': 'AAPL', 'breakout_date': '2026-02-26', 'stop_loss': 145.00, 'entry_id': 1},
    {'symbol': 'XTIA', 'breakout_date': '2026-03-03', 'stop_loss': 1.85, 'entry_id': 1},
    {'symbol': 'MOBX', 'breakout_date': '2026-03-03', 'stop_loss': 0.375, 'entry_id': 2},
    {'symbol': 'INGM', 'breakout_date': '2026-03-03', 'stop_loss': 23.2, 'entry_id': 3},
    {'symbol': 'ACEL', 'breakout_date': '2026-03-04', 'stop_loss': 12.1, 'entry_id': 4},
]
