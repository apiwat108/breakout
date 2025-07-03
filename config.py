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


BREAKOUT_SYMBOLS_5MX0_AB = ['QTRX', 'SERA', 'HIVE', 'JHX', 'FHB', 'AMLX', 'CAE', 'ADPT', 'CIFR', 'HUT', 'EVH', 'CORZW', 'CTOR', 'NAK', 'BKSY', 'BGC', 'MUX', 'VERV', 'EXTR', 'INVZ', 'TXG', 'MGNI', 'ANNX', 'GEOS', 'NU', 'PLUG', 'AEHR', 'NKTR', 'BMBL', 'POET', 'EB', 'LAR', 'COMM', 'ADNT', 'ABCL', 'OPRA', 'ENVX', 'JMIA', 'VIAV', 'IE', 'DNA', 'WT', 'SY', 'HBM', 'NEXT', 'MIND', 'GTN', 'RCI', 'SRI', 'CRML', 'PACS', 'MARA', 'TWI', 'RZLV', 'SKYE', 'PRME', 'SLI', 'ERO', 'ARBE', 'UUUU', 'TSSI', 'BLCO', 'WULF', 'ZETA', 'TDOC', 'EXFY', 'CORZ', 'ONL', 'AMTX', 'BUSE', 'PACB', 'VNET', 'BLMN', 'MLCO', 'SNAP', 'KAR', 'QS', 'BBAI']