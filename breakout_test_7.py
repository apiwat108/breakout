import config, requests
import tulipy, numpy
import alpaca_trade_api as tradeapi
from datetime import datetime
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from helpers import calculate_quantity
import pytz
import yfinance as yf

symbols = config.BREAKOUT_SYMBOLS

current_date = datetime.now(pytz.timezone('America/New_York')).date().isoformat()
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

orders = api.list_orders(status='all', after=current_date)
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']

for symbol in symbols:
    try:
        ticker = yf.Ticker(symbol)
        minute_5_bars = ticker.history(interval='5m',period='2d')#start=current_date, end=current_date)
        minute_15_bars = ticker.history(interval='15m',period='2d')
        minute_60_bars = ticker.history(interval='60m',period='5d')
    except Exception as e:
        print(e)

    closes_5m = numpy.array(minute_5_bars['Close'])
    closes_15m = numpy.array(minute_15_bars['Close'])
    closes_60m = numpy.array(minute_60_bars['Close'])

    short_period = 12
    long_period = 26
    signal_period = 9
    decimal_point = 4

    (M_60m_all, S_60m_all, H_60m_all) = tulipy.macd(numpy.array(closes_60m), short_period=short_period , long_period=long_period, signal_period=signal_period)
    M_60m_C0 = round(M_60m_all[-1], decimal_point)
    M_60m_P1 = round(M_60m_all[-2], decimal_point)
    M_60m_P2 = round(M_60m_all[-3], decimal_point)
    M_60m_P3 = round(M_60m_all[-4], decimal_point)
 
    (M_15m_all, S_15m_all, H_15m_all) = tulipy.macd(numpy.array(closes_15m), short_period=short_period , long_period=long_period, signal_period=signal_period)
    M_15m_P1 = round(M_15m_all[-2], decimal_point)
    H_15m_C0 = round(H_15m_all[-1], decimal_point)
    H_15m_P1 = round(H_15m_all[-2], decimal_point)
    H_15m_P2 = round(H_15m_all[-3], decimal_point)
    H_15m_P3 = round(H_15m_all[-4], decimal_point)
    limit = -0.0032

    (M_5m_all, S_5m_all, H_5m_all) = tulipy.macd(numpy.array(closes_5m), short_period=short_period , long_period=long_period, signal_period=signal_period)
    M_5m_C0 = round(M_5m_all[-1], decimal_point)
    H_5m_C0 = round(H_5m_all[-1], decimal_point)
    H_5m_P1 = round(H_5m_all[-2], decimal_point)
    
    if M_60m_P1 > 0 and M_60m_P1 > M_60m_P2 and M_60m_P2 > M_60m_P3:
        if M_15m_P1 > 0 and H_15m_P1 > limit and H_15m_P2 > limit and H_15m_P3 > limit: 
            if M_5m_C0 > 0 and H_5m_C0 > 0 and H_5m_P1 < 0:
                print(f"{symbol} 5m-macd cross up signal line and 0-line. It's buy signal and the order can be placed.")

                if symbol not in existing_order_symbols:
                    market_price = round(closes_5m[-1], 1)
                    quantity = calculate_quantity(market_price)
                    print(f"placing order for {symbol} at {market_price}")

                    try:
                        api.submit_order(
                            symbol=symbol,
                            side='buy',
                            type='market',
                            qty=quantity,
                            time_in_force='gtc'
                        )
                    except Exception as e:
                        print(f"could not submit order {e}")            
                else:
                    print(f"Already an order for {symbol}, skipping")

    if symbol in existing_order_symbols:
        if (H_5m_C0 < 0 and H_5m_P1 > 0) or H_5m_C0 < 0:
            print(f"{symbol} 5m-macd cross down signal line. It's sell signal and the order can be placed.")
            print(f"sell for {symbol} at the best bid")
            position = api.get_position(symbol)
            quantity = position.qty
            try:
                api.submit_order(
                    symbol=symbol,
                    side='sell',
                    type='market',
                    qty=quantity,
                    time_in_force='gtc'
                )
            except Exception as e:
                print(f"could not submit order {e}")