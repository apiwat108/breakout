# Configuration for Manual Breakout Entry System

# LIVE ACCOUNT - ACTIVE FOR PRODUCTION TRADING
API_KEY = 'AK9WJUKS418ZU6Y8LM66'
SECRET_KEY = 'JBu0oIEfoUUSuMtu68XglUruZdDBPbzZdAhs8a2m'
API_URL = 'https://api.alpaca.markets'

# # Paper Account 1 (for testing only)
# API_KEY = 'PKFPXIK488ZVOTTE62E0'
# SECRET_KEY = 'eKA6lLM0CGvfsA3LeoS65bgbX8VkiEdvlaOPvCM0'
# API_URL = 'https://paper-api.alpaca.markets'

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
RISK_PERCENTAGE = 0.02  # 2% risk per trade (~$223 per trade with current portfolio)
MAX_POSITION_VALUE = 5000  # Maximum position value in USD (adjusted for live account)
MIN_POSITION_VALUE = 300  # Minimum position value in USD (adjusted for live account)

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
    {'symbol': 'PDYN', 'breakout_date': '2026-03-05', 'stop_loss': 8.05, 'entry_id': 5},
    {'symbol': 'ALTO', 'breakout_date': '2026-03-05', 'stop_loss': 3.05, 'entry_id': 6},
    {'symbol': 'AMPX', 'breakout_date': '2026-03-05', 'stop_loss': 12.75, 'entry_id': 7},
    {'symbol': 'TNGX', 'breakout_date': '2026-03-05', 'stop_loss': 13.0, 'entry_id': 8},
    {'symbol': 'BAK', 'breakout_date': '2026-03-05', 'stop_loss': 4.15, 'entry_id': 9},
    {'symbol': 'PRSO', 'breakout_date': '2026-03-06', 'stop_loss': 1.4, 'entry_id': 10},
    {'symbol': 'LION', 'breakout_date': '2026-03-06', 'stop_loss': 9.7, 'entry_id': 11},
    {'symbol': 'GEVO', 'breakout_date': '2026-03-06', 'stop_loss': 1.85, 'entry_id': 12},
    {'symbol': 'SWBI', 'breakout_date': '2026-03-06', 'stop_loss': 12.65, 'entry_id': 13},
    {'symbol': 'OVID', 'breakout_date': '2026-03-09', 'stop_loss': 1.8, 'entry_id': 14},
    {'symbol': 'SLDB', 'breakout_date': '2026-03-09', 'stop_loss': 6.75, 'entry_id': 15},
    {'symbol': 'RLMD', 'breakout_date': '2026-03-09', 'stop_loss': 5.75, 'entry_id': 16},
    {'symbol': 'MGNX', 'breakout_date': '2026-03-11', 'stop_loss': 2.25, 'entry_id': 17},
    {'symbol': 'OCGN', 'breakout_date': '2026-03-11', 'stop_loss': 1.8, 'entry_id': 18},
    {'symbol': 'ACTG', 'breakout_date': '2026-03-11', 'stop_loss': 4.4, 'entry_id': 19},
    {'symbol': 'LWLG', 'breakout_date': '2026-03-12', 'stop_loss': 5.8, 'entry_id': 20},
    {'symbol': 'LOCO', 'breakout_date': '2026-03-13', 'stop_loss': 12.0, 'entry_id': 21},
    {'symbol': 'EQ', 'breakout_date': '2026-03-13', 'stop_loss': 2.2, 'entry_id': 22},
    {'symbol': 'BIAF', 'breakout_date': '2026-03-13', 'stop_loss': 1.75, 'entry_id': 23},
    {'symbol': 'CCLD', 'breakout_date': '2026-03-13', 'stop_loss': 2.75, 'entry_id': 24},
    {'symbol': 'BCRX', 'breakout_date': '2026-03-17', 'stop_loss': 8.1, 'entry_id': 25},
    {'symbol': 'FINV', 'breakout_date': '2026-03-17', 'stop_loss': 5.5, 'entry_id': 26},
    {'symbol': 'CMBM', 'breakout_date': '2026-03-20', 'stop_loss': 1.3, 'entry_id': 27},
    {'symbol': 'CURV', 'breakout_date': '2026-03-20', 'stop_loss': 1.4, 'entry_id': 28},
    {'symbol': 'CV', 'breakout_date': '2026-03-20', 'stop_loss': 5.5, 'entry_id': 29},
    {'symbol': 'WATT', 'breakout_date': '2026-03-20', 'stop_loss': 13.55, 'entry_id': 30},
    {'symbol': 'ANNA', 'breakout_date': '2026-03-20', 'stop_loss': 3.85, 'entry_id': 31},
    {'symbol': 'DEC', 'breakout_date': '2026-03-20', 'stop_loss': 15.45, 'entry_id': 32},
    {'symbol': 'NIXX', 'breakout_date': '2026-03-24', 'stop_loss': 0.8, 'entry_id': 33},
    {'symbol': 'SMMT', 'breakout_date': '2026-03-25', 'stop_loss': 15.8, 'entry_id': 34},
    {'symbol': 'VIVO', 'breakout_date': '2026-03-25', 'stop_loss': 2.35, 'entry_id': 35},
    {'symbol': 'HPE', 'breakout_date': '2026-03-25', 'stop_loss': 24.0, 'entry_id': 36},
    {'symbol': 'JD', 'breakout_date': '2026-03-25', 'stop_loss': 28.5, 'entry_id': 37},
    {'symbol': 'NRXP', 'breakout_date': '2026-03-25', 'stop_loss': 2.1, 'entry_id': 38},
    {'symbol': 'PAYS', 'breakout_date': '2026-03-25', 'stop_loss': 4.2, 'entry_id': 39},
    {'symbol': 'SRPT', 'breakout_date': '2026-03-25', 'stop_loss': 19.6, 'entry_id': 40},
    {'symbol': 'KSCP', 'breakout_date': '2026-03-25', 'stop_loss': 4.25, 'entry_id': 41},
    {'symbol': 'UNIT', 'breakout_date': '2026-03-31', 'stop_loss': 8.2, 'entry_id': 42},
    {'symbol': 'FC', 'breakout_date': '2026-04-02', 'stop_loss': 17.5, 'entry_id': 43},
    {'symbol': 'KODK', 'breakout_date': '2026-04-02', 'stop_loss': 9.0, 'entry_id': 44},
    {'symbol': 'LUNR', 'breakout_date': '2026-04-02', 'stop_loss': 19.0, 'entry_id': 45},
    {'symbol': 'RLAY', 'breakout_date': '2026-04-02', 'stop_loss': 10.4, 'entry_id': 46},
    {'symbol': 'BMEA', 'breakout_date': '2026-04-07', 'stop_loss': 1.5, 'entry_id': 47},
    {'symbol': 'SPIR', 'breakout_date': '2026-04-08', 'stop_loss': 16.0, 'entry_id': 48},
    {'symbol': 'EXTR', 'breakout_date': '2026-04-08', 'stop_loss': 16.0, 'entry_id': 49},
    {'symbol': 'ZNTL', 'breakout_date': '2026-04-09', 'stop_loss': 3.0, 'entry_id': 50},
    {'symbol': 'WOLF', 'breakout_date': '2026-04-09', 'stop_loss': 20.0, 'entry_id': 51},
]
