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
current_time = datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M:%S")
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

orders = api.list_orders(status='all', after=current_date)
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']

print(current_time)

for symbol in symbols:
    print(symbol)
    try:
        ticker = yf.Ticker(symbol)
        minute_5_bars = ticker.history(interval='5m',period='5d')#start=current_date, end=current_date)
        minute_15_bars = ticker.history(interval='15m',period='5d')
        minute_60_bars = ticker.history(interval='60m',period='1mo')

        closes_5m = numpy.array(minute_5_bars['Close'])
        closes_15m = numpy.array(minute_15_bars['Close'])
        closes_60m = numpy.array(minute_60_bars['Close'])

        short_period = 12
        long_period = 26
        signal_period = 9
        decimal_point = 4

        try:
            (M_60m_all, S_60m_all, H_60m_all) = tulipy.macd(numpy.array(closes_60m), short_period=short_period , long_period=long_period, signal_period=signal_period)      
            M_60m_C0 = round(M_60m_all[-1], decimal_point)
            M_60m_P1 = round(M_60m_all[-2], decimal_point)
            M_60m_P2 = round(M_60m_all[-3], decimal_point)
            M_60m_P3 = round(M_60m_all[-4], decimal_point)
        except Exception as e:
            print(f"For 60: {e}")

        try:
            (M_15m_all, S_15m_all, H_15m_all) = tulipy.macd(numpy.array(closes_15m), short_period=short_period , long_period=long_period, signal_period=signal_period)
            M_15m_P1 = round(M_15m_all[-2], decimal_point)
            H_15m_C0 = round(H_15m_all[-1], decimal_point)
            H_15m_P1 = round(H_15m_all[-2], decimal_point)
            H_15m_P2 = round(H_15m_all[-3], decimal_point)
            H_15m_P3 = round(H_15m_all[-4], decimal_point)
            limit = -0.0032
        except Exception as e:
            print(f"For 15m: {e}")

        try:
            (M_5m_all, S_5m_all, H_5m_all) = tulipy.macd(numpy.array(closes_5m), short_period=short_period , long_period=long_period, signal_period=signal_period)
            M_5m_C0 = round(M_5m_all[-1], decimal_point)
            H_5m_C0 = round(H_5m_all[-1], decimal_point)
            H_5m_P1 = round(H_5m_all[-2], decimal_point)
        except Exception as e:
            print(f"For 5m: {e}")
    
        if M_60m_P1 > 0 and M_60m_P1 > M_60m_P2 and M_60m_P2 > M_60m_P3:
            if M_15m_P1 > 0 and H_15m_P1 > limit and H_15m_P2 > limit and H_15m_P3 > limit: 
                if M_5m_C0 > 0 and H_5m_C0 > 0.01 and H_5m_P1 < 0:
                    print(f"{symbol} 5m-macd cross up signal line and 0-line. It's buy signal and the order can be placed.")

                    if symbol not in existing_order_symbols:
                        market_price = round(closes_5m[-1], 1)
                        quantity = calculate_quantity(market_price)
                        print(f"placing order for {symbol} at {market_price}")

                        try:
                            position = api.get_position(symbol)
                            portfolio = api.list_positions()
                            quantity = position.qty
                            print(portfolio)
                            print(position)

                        except Exception as e:
                            print(f"No position for buy")

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

    except Exception as e:
        print(e)

    try:
        if symbol in existing_order_symbols:
            print(existing_order_symbols)

            if (H_5m_C0 < 0 and H_5m_P1 > 0) or H_5m_C0 < 0:
                print(f"{symbol} 5m-macd cross down signal line. It's sell signal and placing order.")

                try:
                    position = api.get_position(symbol)
                    portfolio = api.list_positions()
                    quantity = position.qty
                    print(portfolio)
                    print(position)

                except Exception as e:
                    print(f"No position for sell")

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

            try:
                if position.side == 'sell' and orders.status == 'filled':
                    existing_order_symbols.remove(symbol)
            except Exception as e:
                print(f"Keep waiting for sell signal")            

    except Exception as e:
        print(f"check if the sold symbol is still in the existing orders or not {e}")


    