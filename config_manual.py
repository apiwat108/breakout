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
CONTINUE_TRACKING_AFTER_PARTIAL_EXIT = True  # Keep tracking after partial sells until fully exitedENTRY_WINDOW_HOUR = 9  # Allow entries only during this market open hour (ET)
# Alpaca Data API URL
BARS_URL = 'https://data.alpaca.markets/v2'

# ========== MANUAL BREAKOUT ENTRIES ==========
# This list is updated by breakout_manual_entry.py on MacBook
# Format: {'symbol': 'AAPL', 'breakout_date': '2026-02-26', 'stop_loss': 145.00, 'entry_id': 1}
# Commit this file to GitHub after adding entries, then git pull on Linode
MANUAL_BREAKOUT_ENTRIES = [
    # Example (remove this when you add real entries):
    # {'symbol': 'AAPL', 'breakout_date': '2026-02-26', 'stop_loss': 145.00, 'entry_id': 1},  # Not in positions
    # {'symbol': 'XTIA', 'breakout_date': '2026-03-03', 'stop_loss': 1.85, 'entry_id': 1},  # Not in positions
    # {'symbol': 'MOBX', 'breakout_date': '2026-03-03', 'stop_loss': 0.375, 'entry_id': 2},  # Not in positions
    # {'symbol': 'INGM', 'breakout_date': '2026-03-03', 'stop_loss': 23.2, 'entry_id': 3},  # Not in positions
    # {'symbol': 'ACEL', 'breakout_date': '2026-03-04', 'stop_loss': 12.1, 'entry_id': 4},  # Not in positions
    # {'symbol': 'PDYN', 'breakout_date': '2026-03-05', 'stop_loss': 8.05, 'entry_id': 5},  # Not in positions
    # {'symbol': 'ALTO', 'breakout_date': '2026-03-05', 'stop_loss': 3.05, 'entry_id': 6},  # Not in positions
    # {'symbol': 'AMPX', 'breakout_date': '2026-03-05', 'stop_loss': 12.75, 'entry_id': 7},  # Not in positions
    # {'symbol': 'TNGX', 'breakout_date': '2026-03-05', 'stop_loss': 13.0, 'entry_id': 8},  # Not in positions
    # {'symbol': 'BAK', 'breakout_date': '2026-03-05', 'stop_loss': 4.15, 'entry_id': 9},  # Not in positions
    # {'symbol': 'PRSO', 'breakout_date': '2026-03-06', 'stop_loss': 1.4, 'entry_id': 10},  # Not in positions
    # {'symbol': 'LION', 'breakout_date': '2026-03-06', 'stop_loss': 9.7, 'entry_id': 11},  # Not in positions  # Not in positions
    # {'symbol': 'GEVO', 'breakout_date': '2026-03-06', 'stop_loss': 1.85, 'entry_id': 12},  # Not in positions
    # {'symbol': 'SWBI', 'breakout_date': '2026-03-06', 'stop_loss': 12.65, 'entry_id': 13},  # Not in positions
    # {'symbol': 'OVID', 'breakout_date': '2026-03-09', 'stop_loss': 1.8, 'entry_id': 14},  # Not in positions
    # {'symbol': 'SLDB', 'breakout_date': '2026-03-09', 'stop_loss': 6.75, 'entry_id': 15},  # Not in positions
    # {'symbol': 'RLMD', 'breakout_date': '2026-03-09', 'stop_loss': 5.75, 'entry_id': 16},  # Not in positions
    # {'symbol': 'MGNX', 'breakout_date': '2026-03-11', 'stop_loss': 2.25, 'entry_id': 17},  # Not in positions
    # {'symbol': 'OCGN', 'breakout_date': '2026-03-11', 'stop_loss': 1.8, 'entry_id': 18},  # Not in positions
    # {'symbol': 'ACTG', 'breakout_date': '2026-03-11', 'stop_loss': 4.4, 'entry_id': 19},  # Not in positions
    # {'symbol': 'LWLG', 'breakout_date': '2026-03-12', 'stop_loss': 5.8, 'entry_id': 20},  # Not in positions
    # {'symbol': 'LOCO', 'breakout_date': '2026-03-13', 'stop_loss': 12.0, 'entry_id': 21},  # Not in positions
    # {'symbol': 'EQ', 'breakout_date': '2026-03-13', 'stop_loss': 2.2, 'entry_id': 22},  # Not in positions
    # {'symbol': 'BIAF', 'breakout_date': '2026-03-13', 'stop_loss': 1.75, 'entry_id': 23},  # Not in positions
    # {'symbol': 'CCLD', 'breakout_date': '2026-03-13', 'stop_loss': 2.75, 'entry_id': 24},  # Not in positions
    # {'symbol': 'BCRX', 'breakout_date': '2026-03-17', 'stop_loss': 8.1, 'entry_id': 25},  # Not in positions
    # {'symbol': 'FINV', 'breakout_date': '2026-03-17', 'stop_loss': 5.5, 'entry_id': 26},  # Not in positions
    # {'symbol': 'CMBM', 'breakout_date': '2026-03-20', 'stop_loss': 1.3, 'entry_id': 27},  # Not in positions
    # {'symbol': 'CURV', 'breakout_date': '2026-03-20', 'stop_loss': 1.4, 'entry_id': 28},  # Not in positions
    # {'symbol': 'CV', 'breakout_date': '2026-03-20', 'stop_loss': 5.5, 'entry_id': 29},  # Not in positions
    # {'symbol': 'WATT', 'breakout_date': '2026-03-20', 'stop_loss': 13.55, 'entry_id': 30},  # Not in positions
    # {'symbol': 'ANNA', 'breakout_date': '2026-03-20', 'stop_loss': 3.85, 'entry_id': 31},  # Not in positions
    # {'symbol': 'DEC', 'breakout_date': '2026-03-20', 'stop_loss': 15.45, 'entry_id': 32},  # Not in positions
    # {'symbol': 'NIXX', 'breakout_date': '2026-03-24', 'stop_loss': 0.8, 'entry_id': 33},  # Not in positions
    # {'symbol': 'SMMT', 'breakout_date': '2026-03-25', 'stop_loss': 15.8, 'entry_id': 34},  # Not in positions
    # {'symbol': 'VIVO', 'breakout_date': '2026-03-25', 'stop_loss': 2.35, 'entry_id': 35},  # Not in positions  # Not in positions
    # {'symbol': 'HPE', 'breakout_date': '2026-03-25', 'stop_loss': 24.0, 'entry_id': 36},  # Not in positions
    # {'symbol': 'JD', 'breakout_date': '2026-03-25', 'stop_loss': 28.5, 'entry_id': 37},  # Not in positions
    # {'symbol': 'NRXP', 'breakout_date': '2026-03-25', 'stop_loss': 2.1, 'entry_id': 38},  # Not in positions
    # {'symbol': 'PAYS', 'breakout_date': '2026-03-25', 'stop_loss': 4.2, 'entry_id': 39},  # Not in positions
    # {'symbol': 'SRPT', 'breakout_date': '2026-03-25', 'stop_loss': 19.6, 'entry_id': 40},  # Not in positions
    # {'symbol': 'KSCP', 'breakout_date': '2026-03-25', 'stop_loss': 4.25, 'entry_id': 41},  # Not in positions
    # {'symbol': 'UNIT', 'breakout_date': '2026-03-31', 'stop_loss': 8.2, 'entry_id': 42},  # Not in positions
    # {'symbol': 'FC', 'breakout_date': '2026-04-02', 'stop_loss': 17.5, 'entry_id': 43},  # Not in positions
    # {'symbol': 'KODK', 'breakout_date': '2026-04-02', 'stop_loss': 9.0, 'entry_id': 44},  # Not in positions
    # {'symbol': 'LUNR', 'breakout_date': '2026-04-02', 'stop_loss': 19.0, 'entry_id': 45},  # Not in positions
    # {'symbol': 'RLAY', 'breakout_date': '2026-04-02', 'stop_loss': 10.4, 'entry_id': 46},  # Not in positions
    # {'symbol': 'BMEA', 'breakout_date': '2026-04-07', 'stop_loss': 1.5, 'entry_id': 47},  # Not in positions
    # {'symbol': 'SPIR', 'breakout_date': '2026-04-08', 'stop_loss': 16.0, 'entry_id': 48},  # Not in positions
    # {'symbol': 'EXTR', 'breakout_date': '2026-04-08', 'stop_loss': 16.0, 'entry_id': 49},  # Not in positions
    # {'symbol': 'ZNTL', 'breakout_date': '2026-04-09', 'stop_loss': 3.0, 'entry_id': 50},  # Not in positions
    # {'symbol': 'WOLF', 'breakout_date': '2026-04-09', 'stop_loss': 20.0, 'entry_id': 51},  # Not in positions
    # {'symbol': 'HURA', 'breakout_date': '2026-04-14', 'stop_loss': 2.2, 'entry_id': 52},  # Not in positions
    # {'symbol': 'TBRG', 'breakout_date': '2026-04-16', 'stop_loss': 19.0, 'entry_id': 53},  # Not in positions
    # {'symbol': 'TSSI', 'breakout_date': '2026-04-14', 'stop_loss': 12.0, 'entry_id': 54},  # Not in positions
    # {'symbol': 'KEEL', 'breakout_date': '2026-04-14', 'stop_loss': 2.4, 'entry_id': 55},  # Not in positions
    # {'symbol': 'BOLD', 'breakout_date': '2026-04-14', 'stop_loss': 1.4, 'entry_id': 56},  # Not in positions
    # {'symbol': 'SNAL', 'breakout_date': '2026-04-14', 'stop_loss': 0.75, 'entry_id': 57},  # Not in positions
    # {'symbol': 'RUM', 'breakout_date': '2026-04-16', 'stop_loss': 5.65, 'entry_id': 58},  # Not in positions
    # {'symbol': 'DARE', 'breakout_date': '2026-04-16', 'stop_loss': 1.9, 'entry_id': 59},  # Not in positions
    # {'symbol': 'GRPN', 'breakout_date': '2026-04-16', 'stop_loss': 13.0, 'entry_id': 60},  # Not in positions
    # {'symbol': 'NN', 'breakout_date': '2026-04-16', 'stop_loss': 18.45, 'entry_id': 61},  # Not in positions
    # {'symbol': 'NVTS', 'breakout_date': '2026-04-16', 'stop_loss': 10.0, 'entry_id': 62},  # Not in positions
    # {'symbol': 'BZUN', 'breakout_date': '2026-04-16', 'stop_loss': 2.65, 'entry_id': 63},  # Not in positions
    # {'symbol': 'EFOI', 'breakout_date': '2026-04-17', 'stop_loss': 5.0, 'entry_id': 64},  # Not in positions
    # {'symbol': 'LION', 'breakout_date': '2026-04-17', 'stop_loss': 11.1, 'entry_id': 65},  # Not in positions  # Not in positions
    # {'symbol': 'IMVT', 'breakout_date': '2026-04-17', 'stop_loss': 27.5, 'entry_id': 66},  # Not in positions
    # {'symbol': 'RPAY', 'breakout_date': '2026-04-17', 'stop_loss': 3.75, 'entry_id': 67},  # Not in positions
    # {'symbol': 'BZAI', 'breakout_date': '2026-04-17', 'stop_loss': 2.0, 'entry_id': 68},  # Not in positions
    # {'symbol': 'NKTX', 'breakout_date': '2026-04-17', 'stop_loss': 2.8, 'entry_id': 69},  # Not in positions
    # {'symbol': 'CRML', 'breakout_date': '2026-04-17', 'stop_loss': 11.15, 'entry_id': 70},  # Not in positions
    # {'symbol': 'INV', 'breakout_date': '2026-04-20', 'stop_loss': 4.5, 'entry_id': 71},  # Not in positions
    # {'symbol': 'ARCO', 'breakout_date': '2026-04-20', 'stop_loss': 9.12, 'entry_id': 72},  # Not in positions
    # {'symbol': 'CADL', 'breakout_date': '2026-04-20', 'stop_loss': 6.4, 'entry_id': 73},  # Not in positions
    # {'symbol': 'CMPS', 'breakout_date': '2026-04-20', 'stop_loss': 8.6, 'entry_id': 74},  # Not in positions
    # {'symbol': 'DGXX', 'breakout_date': '2026-04-20', 'stop_loss': 3.05, 'entry_id': 75},  # Not in positions
    # {'symbol': 'LFMD', 'breakout_date': '2026-04-20', 'stop_loss': 4.0, 'entry_id': 76},  # Not in positions
    # {'symbol': 'POET', 'breakout_date': '2026-04-21', 'stop_loss': 8.8, 'entry_id': 77},  # Not in positions
    # {'symbol': 'VELO', 'breakout_date': '2026-04-21', 'stop_loss': 12.0, 'entry_id': 78},  # Not in positions
    # {'symbol': 'MX', 'breakout_date': '2026-04-21', 'stop_loss': 3.35, 'entry_id': 79},  # Not in positions
    # {'symbol': 'FCEL', 'breakout_date': '2026-04-21', 'stop_loss': 8.45, 'entry_id': 80},  # Not in positions
    # {'symbol': 'ILPT', 'breakout_date': '2026-04-22', 'stop_loss': 6.25, 'entry_id': 81},  # Not in positions
    # {'symbol': 'TLRY', 'breakout_date': '2026-04-22', 'stop_loss': 7.85, 'entry_id': 82},  # Not in positions
    # {'symbol': 'NMAX', 'breakout_date': '2026-04-22', 'stop_loss': 7.25, 'entry_id': 83},  # Not in positions
    # {'symbol': 'SNDL', 'breakout_date': '2026-04-22', 'stop_loss': 1.5, 'entry_id': 84},  # Not in positions
    # {'symbol': 'BEEM', 'breakout_date': '2026-04-22', 'stop_loss': 1.5, 'entry_id': 85},  # Not in positions
    # {'symbol': 'VIVO', 'breakout_date': '2026-04-23', 'stop_loss': 2.9, 'entry_id': 86},  # Not in positions
    # {'symbol': 'TRT', 'breakout_date': '2026-04-23', 'stop_loss': 10.7, 'entry_id': 87},  # Not in positions
    # {'symbol': 'PENN', 'breakout_date': '2026-04-23', 'stop_loss': 14.6, 'entry_id': 88},  # Not in positions
    # {'symbol': 'ATOM', 'breakout_date': '2026-04-24', 'stop_loss': 6.5, 'entry_id': 89},  # Not in positions
    # {'symbol': 'RMAX', 'breakout_date': '2026-04-24', 'stop_loss': 6.5, 'entry_id': 90},  # Not in positions
    # {'symbol': 'OSTX', 'breakout_date': '2026-04-24', 'stop_loss': 1.4, 'entry_id': 91},  # Not in positions
    # {'symbol': 'SGMT', 'breakout_date': '2026-04-27', 'stop_loss': 7.1, 'entry_id': 92},  # Not in positions
    # {'symbol': 'YAAS', 'breakout_date': '2026-04-27', 'stop_loss': 1.25, 'entry_id': 93},  # Not in positions
    # {'symbol': 'NWBI', 'breakout_date': '2026-04-28', 'stop_loss': 13.6, 'entry_id': 94},  # Not in positions
    # {'symbol': 'DDI', 'breakout_date': '2026-04-28', 'stop_loss': 10.65, 'entry_id': 95},  # Not in positions
    # {'symbol': 'FIVN', 'breakout_date': '2026-05-01', 'stop_loss': 19.6, 'entry_id': 96},  # Not in positions
    # {'symbol': 'SOUN', 'breakout_date': '2026-05-01', 'stop_loss': 8.0, 'entry_id': 97},  # Not in positions
    # {'symbol': 'FATE', 'breakout_date': '2026-05-04', 'stop_loss': 1.5, 'entry_id': 98},  # Not in positions
    # {'symbol': 'CABA', 'breakout_date': '2026-05-04', 'stop_loss': 3.15, 'entry_id': 99},  # Not in positions
    {'symbol': 'AURA', 'breakout_date': '2026-05-04', 'stop_loss': 7.0, 'entry_id': 100},
    # {'symbol': 'CLNN', 'breakout_date': '2026-05-04', 'stop_loss': 7.0, 'entry_id': 101},  # Not in positions
    # {'symbol': 'HR', 'breakout_date': '2026-05-05', 'stop_loss': 19.0, 'entry_id': 102},  # Not in positions
    # {'symbol': 'BLDP', 'breakout_date': '2026-05-05', 'stop_loss': 3.5, 'entry_id': 103},  # Not in positions
    # {'symbol': 'CIFR', 'breakout_date': '2026-05-05', 'stop_loss': 18.5, 'entry_id': 104},  # Not in positions
    # {'symbol': 'OSS', 'breakout_date': '2026-05-06', 'stop_loss': 12.0, 'entry_id': 105},  # Not in positions
    # {'symbol': 'DOC', 'breakout_date': '2026-05-06', 'stop_loss': 17.0, 'entry_id': 106},  # Not in positions
    # {'symbol': 'GEO', 'breakout_date': '2026-05-06', 'stop_loss': 20.0, 'entry_id': 107},  # Not in positions
    # {'symbol': 'FLYW', 'breakout_date': '2026-05-06', 'stop_loss': 16.0, 'entry_id': 108},  # Not in positions
    # {'symbol': 'QMCO', 'breakout_date': '2026-05-06', 'stop_loss': 9.0, 'entry_id': 109},  # Not in positions
    # {'symbol': 'SLS', 'breakout_date': '2026-05-13', 'stop_loss': 5.65, 'entry_id': 110},  # Not in positions
    # {'symbol': 'MEI', 'breakout_date': '2026-05-13', 'stop_loss': 9.5, 'entry_id': 111},  # Not in positions
    # {'symbol': 'PCT', 'breakout_date': '2026-05-14', 'stop_loss': 11.4, 'entry_id': 112},  # Not in positions
    {'symbol': 'PLSE', 'breakout_date': '2026-05-14', 'stop_loss': 22.8, 'entry_id': 113},
    # {'symbol': 'KLAR', 'breakout_date': '2026-05-14', 'stop_loss': 14.9, 'entry_id': 114},  # Not in positions
    # {'symbol': 'FENC', 'breakout_date': '2026-05-14', 'stop_loss': 7.2, 'entry_id': 115},  # Not in positions
    # {'symbol': 'INMB', 'breakout_date': '2026-05-14', 'stop_loss': 1.5, 'entry_id': 116},  # Not in positions
    # {'symbol': 'IPWR', 'breakout_date': '2026-05-14', 'stop_loss': 5.25, 'entry_id': 117},  # Not in positions
    {'symbol': 'SACH', 'breakout_date': '2026-05-18', 'stop_loss': 1.08, 'entry_id': 118},
    # {'symbol': 'GCTS', 'breakout_date': '2026-05-18', 'stop_loss': 2.0, 'entry_id': 119},  # Not in positions
    # {'symbol': 'AMPG', 'breakout_date': '2026-05-18', 'stop_loss': 2.8, 'entry_id': 120},  # Not in positions
    # {'symbol': 'SG', 'breakout_date': '2026-05-18', 'stop_loss': 6.75, 'entry_id': 121},  # Not in positions
    # {'symbol': 'CMBT', 'breakout_date': '2026-05-19', 'stop_loss': 15.75, 'entry_id': 122},  # Not in positions
    # {'symbol': 'TENB', 'breakout_date': '2026-05-19', 'stop_loss': 21.2, 'entry_id': 123},  # Not in positions
    # {'symbol': 'RGTI', 'breakout_date': '2026-05-21', 'stop_loss': 18.35, 'entry_id': 124},  # Not in positions
    # {'symbol': 'RGTIW', 'breakout_date': '2026-05-21', 'stop_loss': 8.5, 'entry_id': 125},  # Not in positions
    # {'symbol': 'BB', 'breakout_date': '2026-05-22', 'stop_loss': 6.65, 'entry_id': 126},  # Not in positions
    # {'symbol': 'LION', 'breakout_date': '2026-05-22', 'stop_loss': 13.5, 'entry_id': 127},  # Not in positions
    # {'symbol': 'HPQ', 'breakout_date': '2026-05-22', 'stop_loss': 22.5, 'entry_id': 128},  # Not in positions
    {'symbol': 'HOVR', 'breakout_date': '2026-05-22', 'stop_loss': 2.5, 'entry_id': 129},
    {'symbol': 'HLIT', 'breakout_date': '2026-05-22', 'stop_loss': 13.7, 'entry_id': 130},
    # {'symbol': 'QBTS', 'breakout_date': '2026-05-22', 'stop_loss': 21.6, 'entry_id': 131},  # Not in positions
    # {'symbol': 'NRXP', 'breakout_date': '2026-05-26', 'stop_loss': 3.25, 'entry_id': 132},  # Not in positions
    # {'symbol': 'ASPI', 'breakout_date': '2026-05-26', 'stop_loss': 6.35, 'entry_id': 133},  # Not in positions
    # {'symbol': 'RR', 'breakout_date': '2026-05-26', 'stop_loss': 2.7, 'entry_id': 134},  # Not in positions
    # {'symbol': 'AEMD', 'breakout_date': '2026-05-27', 'stop_loss': 2.6, 'entry_id': 135},  # Not in positions  # Not in positions
    # {'symbol': 'TEO', 'breakout_date': '2026-05-27', 'stop_loss': 12.7, 'entry_id': 136},  # Not in positions  # Not in positions
    # {'symbol': 'IMRN', 'breakout_date': '2026-05-27', 'stop_loss': 0.99, 'entry_id': 137},  # Not in positions  # Not in positions
    # {'symbol': 'QTTB', 'breakout_date': '2026-05-27', 'stop_loss': 9.1, 'entry_id': 138},  # Not in positions  # Not in positions
    # {'symbol': 'APPS', 'breakout_date': '2026-05-27', 'stop_loss': 6.15, 'entry_id': 139},  # Not in positions  # Not in positions
    # {'symbol': 'MANU', 'breakout_date': '2026-05-27', 'stop_loss': 20.45, 'entry_id': 140},  # Not in positions  # Not in positions
    # {'symbol': 'UIS', 'breakout_date': '2026-05-27', 'stop_loss': 3.2, 'entry_id': 141},  # Not in positions  # Not in positions
    {'symbol': 'PD', 'breakout_date': '2026-05-29', 'stop_loss': 8.6, 'entry_id': 142},
    {'symbol': 'CHA', 'breakout_date': '2026-05-29', 'stop_loss': 11.3, 'entry_id': 143},
    {'symbol': 'ASAN', 'breakout_date': '2026-05-29', 'stop_loss': 7.0, 'entry_id': 144},
    {'symbol': 'RPD', 'breakout_date': '2026-05-29', 'stop_loss': 7.5, 'entry_id': 145},
]
