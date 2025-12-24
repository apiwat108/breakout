# Live Account
API_KEY = 'AK9WJUKS418ZU6Y8LM66'
SECRET_KEY = 'JBu0oIEfoUUSuMtu68XglUruZdDBPbzZdAhs8a2m'
API_URL = 'https://api.alpaca.markets'

# # Paper Account 1
# API_KEY = 'PKFPXIK488ZVOTTE62E0'
# SECRET_KEY = 'eKA6lLM0CGvfsA3LeoS65bgbX8VkiEdvlaOPvCM0'
# API_URL = 'https://paper-api.alpaca.markets'

# # Paper Account 2
# PAPER_ACCOUNT_2 = {
#     "API_KEY": "PKOJ4CR6F799HJ5LYZ8A",
#     "SECRET_KEY": "MWh3Uhy3UWzEaauZUbcRqH15BhHCkqXhrb3hxdOi",
#     "API_URL": "https://paper-api.alpaca.markets"
# }

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


BREAKOUT_SYMBOLS_5MX0_AB = ['VNDA', 'AROC', 'FNB', 'NEOG', 'LION', 'WIT', 'VLY', 'RIVN', 'AHCO', 'ABUS', 'RF', 'GERN', 'INFY', 'FOLD', 'DDL', 'IVR', 'TWO', 'CLYM', 'DBI', 'DC', 'HOPE', 'WRBY', 'LUNR', 'VUZI', 'EYPT']

# EWTX case on 7 Nov 2025 on SPX changing direction 
# -- First breakout and first pullack -- successed and run up to 41% in 3 weeks,
# in which 1D close above 10EMA all the way
# Weekly breakout as well 

# TXG case on 19 Nov 2025 on SPX is not good to trade condition
# -- First breakout and first pullback -- successed and run up to 25% in 1 week,
# Weekly MXU and PXU and M > 0

# RLAY case on 16 Sep 2025 on SPX is good to trade condition
# -- First breakout and first pullback -- successed and run up to 70% in 8 weeks, until 1D price close below 10EMA and H_1D_C0 < 0

# AXTI case on Aug 2025 till Dec 2025
# Beakout and early weekly uptrend -- successed and run up to 496% in 4 months 
# 1DM > 0 and 1WP > EMA_10