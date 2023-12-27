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

positions = api.list_positions()
existing_position_symbols = [position.symbol for position in positions]
print(current_time)

for symbol in symbols:
    print(symbol)

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

    (M_60m_all, S_60m_all, H_60m_all) = tulipy.macd(numpy.array(closes_60m), short_period=short_period , long_period=long_period, signal_period=signal_period)      
    M_60m_C0 = round(M_60m_all[-1], decimal_point)
    M_60m_P1 = round(M_60m_all[-2], decimal_point)
    M_60m_P2 = round(M_60m_all[-3], decimal_point)
    M_60m_P3 = round(M_60m_all[-4], decimal_point)
    H_60m_C0 = round(H_60m_all[-1], decimal_point)
    H_60m_P1 = round(H_60m_all[-2], decimal_point)
    H_60m_P2 = round(H_60m_all[-3], decimal_point)
    H_60m_P3 = round(H_60m_all[-4], decimal_point)
    limit_60m = -0.0040

    (M_15m_all, S_15m_all, H_15m_all) = tulipy.macd(numpy.array(closes_15m), short_period=short_period , long_period=long_period, signal_period=signal_period)
    M_15m_C0 = round(M_15m_all[-1], decimal_point)
    M_15m_P1 = round(M_15m_all[-2], decimal_point)
    M_15m_P2 = round(M_15m_all[-3], decimal_point)
    M_15m_P3 = round(M_15m_all[-4], decimal_point)
    H_15m_C0 = round(H_15m_all[-1], decimal_point)
    H_15m_P1 = round(H_15m_all[-2], decimal_point)
    H_15m_P2 = round(H_15m_all[-3], decimal_point)
    H_15m_P3 = round(H_15m_all[-4], decimal_point)
    limit_15m = -0.0032

    (M_5m_all, S_5m_all, H_5m_all) = tulipy.macd(numpy.array(closes_5m), short_period=short_period , long_period=long_period, signal_period=signal_period)
    M_5m_C0 = round(M_5m_all[-1], decimal_point)
    M_5m_P1 = round(M_5m_all[-2], decimal_point)
    M_5m_P2 = round(M_5m_all[-3], decimal_point)
    M_5m_P3 = round(M_5m_all[-4], decimal_point)
    H_5m_C0 = round(H_5m_all[-1], decimal_point)
    H_5m_P1 = round(H_5m_all[-2], decimal_point)
    H_5m_P2 = round(H_5m_all[-3], decimal_point)
    H_5m_P3 = round(H_5m_all[-4], decimal_point)
    S_5m_P3 = round(S_5m_all[-4], decimal_point)


    E_5m_C0 = tulipy.ema(numpy.array(closes_5m), period=10)[-1]
    RSI_5m_C0 = tulipy.rsi(numpy.array(closes_5m), period=14)[-1]
    RSI_15m_C0 = tulipy.rsi(numpy.array(closes_15m), period=14)[-1]
    market_price = round(closes_5m[-1], 1)

    if symbol not in existing_position_symbols:

        # Strategy 1 Based on MCA Model Breakout on 18 Dec and Buy Signal on 20 Dec
        if H_60m_C0 > limit_60m:
            if H_15m_C0 > limit_15m and 75.0 > RSI_15m_C0 > 55.0: 
                if ((H_5m_C0 > 0.00 and H_5m_P1 < 0.00) or (M_5m_C0 > 0.00 and M_5m_P1 < 0.00)) and 75.0 > RSI_5m_C0 > 55.0:
                    print(f" - It's buy signal for Strategy 1.")
                    quantity = calculate_quantity(market_price)
                    print(f" - Placing buy order for {symbol} at {market_price}.\n")

                    try:
                        api.submit_order(
                            symbol=symbol,
                            side='buy',
                            type='market',
                            qty=quantity,
                            time_in_force='gtc'
                        )
                    except Exception as e:
                        print(f"Could not submit order {e}")            

                else:
                    print(" - 5m conditions do not pass for Strategy 1\n")
            else:
                print(" - 15m conditions do not pass for Strategy 1\n")
        else:
            print(" - 60m conditions do not pass for Stratergy 1\n")

    elif symbol in existing_position_symbols:
        print(f" - Already in the position")
        position = api.get_position(symbol)
        quantity = position.qty
        entry_price = float(position.avg_entry_price)

        # Strategy 1 for taking profit 1
        if 0 < H_5m_C0 < H_5m_P1 < H_5m_P2 and H_5m_P2 > H_5m_P3 and M_5m_P2 > 0 and S_5m_P3 > 0:
            print(f" - It's taking-profit signal.")
            print(f" - Placing sell order for {symbol} at {market_price}.\n")

            try:
                api.submit_order(
                    symbol=symbol,
                    side='sell',
                    type='market',
                    qty=quantity,
                    time_in_force='gtc'
                )
            except Exception as e:
                print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---\n")

        # Strategy 2 for cutting loss
        elif market_price < E_5m_C0 and market_price < entry_price:
            print(f" - It's cut-loss signal.")
            print(f" - Placing sell order for {symbol} at {market_price}.\n")

            try:
                api.submit_order(
                    symbol=symbol,
                    side='sell',
                    type='market',
                    qty=quantity,
                    time_in_force='gtc'
                )
            except Exception as e:
                print(f" - --- ERROR --- Could not submit order: {e} --- ERROR ---\n")

        else:
            print(" - No sell signal yet\n")
