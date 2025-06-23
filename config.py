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


BREAKOUT_SYMBOLS_5MX0_AB = ['TE', 'TGB', 'ADNT', 'CRML', 'PHAT', 'GALT', 'ALT', 'CCLD', 'GTN', 'BRY', 'QUBT', 'UROY', 'CTOR', 'TSSI', 'PBF', 'VERV', 'WT', 'EDIT', 'CRK', 'BKSY', 'MANU', 'PLAY', 'DOMH', 'DNA', 'RELI', 'QXO', 'DGXX', 'MOMO', 'INVZ', 'DK', 'OSCR', 'ABCL', 'PACS', 'PACB', 'APPS', 'GRRR', 'BTE', 'QTRX', 'BLMN', 'DNN', 'OUST', 'SA', 'AMTX']