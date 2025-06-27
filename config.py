# # Live Account
# API_KEY = 'AK9WJUKS418ZU6Y8LM66'
# SECRET_KEY = 'JBu0oIEfoUUSuMtu68XglUruZdDBPbzZdAhs8a2m'
# API_URL = 'https://api.alpaca.markets'

# Paper Account 1
API_KEY = 'PKFPXIK488ZVOTTE62E0'
SECRET_KEY = 'eKA6lLM0CGvfsA3LeoS65bgbX8VkiEdvlaOPvCM0'
API_URL = 'https://paper-api.alpaca.markets'

# Paper Account 2
PAPER_ACCOUNT_2 = {
    "API_KEY": "PKOJ4CR6F799HJ5LYZ8A",
    "SECRET_KEY": "MWh3Uhy3UWzEaauZUbcRqH15BhHCkqXhrb3hxdOi",
    "API_URL": "https://paper-api.alpaca.markets"
}

HEADERS = {
    'APCA-API-KEY-ID': API_KEY,
    'APCA-API-SECRET-KEY': SECRET_KEY
}

DB_FILE = '/Users/apiwat/Documents/FULLSTACK-APP/app.db'
BARS_URL = 'https://data.alpaca.markets/v2'

DB_HOST = 'localhost' #https://dev.to/balt1794/postgresql-port-5432-already-in-use-1pcf
DB_USER = 'postgres'
DB_PASS = 'Apiwat'
DB_PORT = 5432
DB_NAME = 'app'
DB_URL = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


BREAKOUT_SYMBOLS_5MX0_AB = ['ENVX', 'PACS', 'ONL', 'BLMN', 'PLAY', 'MOMO', 'VERV', 'DOMH', 'IE', 'PACB', 'RZLV', 'AEHR', 'MANU', 'SKYE', 'COMM', 'MIND', 'TXG', 'CCLD', 'NKTR', 'CTOR', 'CATX', 'SY', 'RELI', 'EVH', 'WT', 'NEXT', 'ABCL', 'TDOC', 'BBAI', 'INVZ', 'DNN', 'BMBL', 'AMTX', 'CRML', 'CRK', 'AMLX', 'HBM', 'QS', 'EYPT', 'GALT', 'BKSY', 'GRRR', 'QTRX', 'DGXX', 'EXTR', 'RCI', 'ARBE', 'PBF', 'NAK', 'ADPT', 'ZETA', 'OUST', 'CORZW', 'MLCO', 'GEOS', 'NU', 'TSSI', 'QXO', 'GTN', 'AUPH', 'TWI', 'POET', 'ERO', 'ADNT', 'DNA', 'CORZ', 'OSCR']