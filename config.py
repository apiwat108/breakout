API_KEY = 'PK1578DRKR3CHSG28IEW'
SECRET_KEY = 'arRvpMcSnXTed5bhc4FhMzl8kyX1TBepqJKzOC1N'
API_URL = 'https://paper-api.alpaca.markets'

HEADERS = {
    'APCA-API-KEY-ID': API_KEY,
    'APCA-API-SECRET-KEY': SECRET_KEY
}

DB_FILE = '/Users/apiwat/Documents/FULLSTACK-APP/app.db'
BARS_URL = 'https://data.alpaca.markets/v2'

DB_HOST = 'localhost' #https://dev.to/balt1794/postgresql-port-5432-already-in-use-1pcf
DB_USER = 'postgres'
DB_PASS = 'password'
DB_NAME = 'app'

BREAKOUT_SYMBOLS_DX0 = ['GME', 'ANGI', 'DBI', 'NEO', 'BEPC', 'LADR', 'KC', 'CORZ', 'MRUS', 'AXTI', 'HIW', 'UNIT', 'TNL', 'ARDX', 'MDXG', 'VICI', 'AB', 'CGON', 'HCP', 'MLCO', 'NYT', 'JOBY', 'CWAN', 'NAT', 'MCRB', 'RXT', 'MCW', 'SYF', 'DAR', 'CYH', 'HYLN', 'DX', 'AGEN', 'PTCT', 'VIR', 'JMIA', 'CFLT', 'NLY', 'ETWO', 'ORC', 'IONQ', 'ABR', 'NWL', 'MODV', 'ST', 'TRIP', 'BEP', 'OLPX', 'LFST', 'BFH', 'SHOO', 'SLI', 'TLRY', 'CUE', 'IOVA', 'XHR', 'CDP', 'RIOT', 'WVE', 'ASAN']

BREAKOUT_SYMBOLS_DR1 = ['UGI', 'ALGM', 'QGEN', 'LADR', 'AMBP', 'POR', 'EQT', 'MTTR', 'RILY', 'CYH', 'FITB', 'DAN', 'CSTL', 'NWL', 'HUMA', 'DAWN', 'FTDR', 'LC', 'FWRG', 'ASPN', 'SMPL', 'CGEM', 'BWA', 'ALTM', 'FULT', 'BEPC', 'GRWG', 'SNAP', 'BNL', 'HCP', 'ATNM', 'MCRB', 'ALHC', 'IRDM', 'CUTR', 'AQN', 'MAX', 'ZUO', 'TWST', 'CNDT', 'WEAT', 'PFS', 'BFH', 'LFST', 'WTRG', 'HWC', 'PTCT', 'CMRE', 'GLW', 'GME', 'AGBA', 'TPIC', 'FLO', 'ENVX', 'NYT', 'BE', 'SYF', 'CLAR', 'AY', 'LILM', 'OZK', 'TRN', 'OGE', 'EPR', 'MRVI', 'EBS', 'POET', 'KC', 'AMRX', 'GOGO', 'KRG', 'ZIM', 'MO', 'JOBY', 'ENB', 'DDL', 'WOW', 'AGEN', 'IBRX', 'ILPT', 'BEP', 'COCO']

BREAKOUT_SYMBOLS_DX1 = ['AUR', 'MUX', 'FXN', 'OPK', 'KGC', 'REAL', 'AES', 'OII', 'AG', 'LAUR', 'AUR', 'LU', 'SG', 'CGC', 'GSM', 'SAND', 'AA', 'SMTC', 'TH', 'CRON', 'FSM', 'AMRK', 'ACVA', 'DOC', 'SNDL', 'VET', 'TTI', 'IE', 'EH', 'MGY', 'TALO', 'PWFL', 'OUST', 'HLX', 'STOK']