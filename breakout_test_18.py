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
    opens_5m = numpy.array(minute_5_bars['Open'])
    highs_5m = numpy.array(minute_5_bars['High'])
    lows_5m = numpy.array(minute_5_bars['Low'])
    closes_15m = numpy.array(minute_15_bars['Close'])
    opens_15m = numpy.array(minute_15_bars['Open'])
    highs_15m = numpy.array(minute_15_bars['High'])
    lows_15m = numpy.array(minute_15_bars['Low'])
    closes_60m = numpy.array(minute_60_bars['Close'])
    opens_60m = numpy.array(minute_60_bars['Open'])
    highs_60m = numpy.array(minute_60_bars['High'])
    lows_60m = numpy.array(minute_60_bars['Low'])

    short_period = 12
    long_period = 26
    signal_period = 9
    decimal_point = 4

    # Candle Stick
    C_60m_C0 = round(closes_60m[-1], decimal_point)
    O_60m_C0 = round(opens_60m[-1], decimal_point)
    H_60m_C0 = round(highs_60m[-1], decimal_point)
    L_60m_C0 = round(lows_60m[-1], decimal_point)
    C_60m_P1 = round(closes_60m[-2], decimal_point)
    O_60m_P1 = round(opens_60m[-2], decimal_point)
    H_60m_P1 = round(highs_60m[-2], decimal_point)
    L_60m_P1 = round(lows_60m[-2], decimal_point)

    C_15m_C0 = round(closes_15m[-1], decimal_point)
    O_15m_C0 = round(opens_15m[-1], decimal_point)
    H_15m_C0 = round(highs_15m[-1], decimal_point)
    L_15m_C0 = round(lows_15m[-1], decimal_point)
    C_15m_P1 = round(closes_15m[-2], decimal_point)
    O_15m_P1 = round(opens_15m[-2], decimal_point)
    H_15m_P1 = round(highs_15m[-2], decimal_point)
    L_15m_P1 = round(lows_15m[-2], decimal_point)
    C_15m_P2 = round(closes_15m[-3], decimal_point)
    O_15m_P2 = round(opens_15m[-3], decimal_point)
    H_15m_P2 = round(highs_15m[-3], decimal_point)
    L_15m_P2 = round(lows_15m[-3], decimal_point)

    C_5m_C0 = round(closes_5m[-1], decimal_point)
    O_5m_C0 = round(opens_5m[-1], decimal_point)
    H_5m_C0 = round(highs_5m[-1], decimal_point)
    L_5m_C0 = round(lows_5m[-1], decimal_point)
    C_5m_P1 = round(closes_5m[-2], decimal_point)
    O_5m_P1 = round(opens_5m[-2], decimal_point)
    H_5m_P1 = round(highs_5m[-2], decimal_point)
    L_5m_P1 = round(lows_5m[-2], decimal_point)

    (M_60m_all, S_60m_all, H_60m_all) = tulipy.macd(numpy.array(closes_60m), short_period=short_period , long_period=long_period, signal_period=signal_period)      
    M_60m_C0 = round(M_60m_all[-1], decimal_point)
    M_60m_P1 = round(M_60m_all[-2], decimal_point)
    M_60m_P2 = round(M_60m_all[-3], decimal_point)
    M_60m_P3 = round(M_60m_all[-4], decimal_point)
    H_60m_C0 = round(H_60m_all[-1], decimal_point)
    H_60m_P1 = round(H_60m_all[-2], decimal_point)
    H_60m_P2 = round(H_60m_all[-3], decimal_point)
    H_60m_P3 = round(H_60m_all[-4], decimal_point)
    limit_60m_H = -0.0040

    (M_15m_all, S_15m_all, H_15m_all) = tulipy.macd(numpy.array(closes_15m), short_period=short_period , long_period=long_period, signal_period=signal_period)
    M_15m_C0 = round(M_15m_all[-1], decimal_point)
    M_15m_P1 = round(M_15m_all[-2], decimal_point)
    M_15m_P2 = round(M_15m_all[-3], decimal_point)
    M_15m_P3 = round(M_15m_all[-4], decimal_point)
    H_15m_C0 = round(H_15m_all[-1], decimal_point)
    H_15m_P1 = round(H_15m_all[-2], decimal_point)
    H_15m_P2 = round(H_15m_all[-3], decimal_point)
    H_15m_P3 = round(H_15m_all[-4], decimal_point)
    limit_15m_max_M = 0.1000
    limit_15m_min_M = -0.0010
    limit_15m_H = -0.0400
    limit_15m_max_M_case_4 = 0.0090 # (ZAA case for taking profit and CHASE case for not breakout)

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
    limit_5m_M = 0.0200

    E_60m_C0 = tulipy.ema(numpy.array(closes_60m), period=10)[-1]
    RSI_5m_C0 = tulipy.rsi(numpy.array(closes_5m), period=14)[-1]
    RSI_15m_C0 = tulipy.rsi(numpy.array(closes_15m), period=14)[-1]
    RSI_60m_C0 = tulipy.rsi(numpy.array(closes_60m), period=14)[-1]
    market_price = round(closes_5m[-1], 1)

    if symbol not in existing_position_symbols:

        # Strategy 1 Based on MCA Model Breakout on 18 Dec and Buy Signal on 20 Dec
        # 60m uptrend with limit of retrace and bullsish reversal candlestick pattern (Bullish Engulfing and One White Soldier)
            # Added Continuous green candelstick for more 60-m strategy
        if H_60m_C0 > limit_60m_H and C_60m_C0 > C_60m_P1 and C_60m_C0 > O_60m_C0 and 75.0 > RSI_60m_C0 > 55.0: # Could add Bullish Engulfing or One White Soldier
            
            # 15m Case-1: MACD x up Signal sync with 5m TF
            if H_15m_P1 < 0.00 and H_15m_C0 > 0.00 and 75.0 > RSI_15m_C0 > 55.0 and limit_15m_min_M < M_15m_C0 < limit_15m_max_M: # Bullish Engulfing
                if ((H_5m_P1 < 0.00 and H_5m_C0 > 0.00) or (M_5m_C0 > 0.00 and M_5m_P1 < 0.00)) and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_M: # Bullish Engulfing MCA 20 Dec --> 21 Dec
                    print(f" - It's buy signal for Strategy 15m Case-1: MACD x up Signal sync with 5m TF")
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

            # 15m Case-2: 5m x Up Triggered on 15m Bullish Engulfing or One White Soldier (MCA 20 Dec --> 21 Dec)
            elif O_15m_P1 > C_15m_P1 and C_15m_C0 > O_15m_P1 and 75.0 > RSI_15m_C0 > 55.0 and limit_15m_min_M < M_15m_C0 < limit_15m_max_M:
                if ((H_5m_C0 > 0.00 and H_5m_P1 < 0.00) or (M_5m_C0 > 0.00 and M_5m_P1 < 0.00)) and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_M:
                    print(f" - It's buy signal for Strategy 15m Case-2: 5m x Up Triggered on 15m Bullish Engulfing or One White Soldier")
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

            # 15m Case-3: 5m x Up Triggered just after 15m Bullish Engulfing or One White Soldier (TMC 5 Jan to 8 Jan)
            elif O_15m_P2 > C_15m_P2 and C_15m_P1 > O_15m_P2 and 75.0 > RSI_15m_C0 > 50.0 and -0.0100 < M_15m_C0 < limit_15m_max_M and H_15m_C0 > -0.0050:
                if ((H_5m_C0 > 0.00 and H_5m_P1 < 0.00) or (M_5m_C0 > 0.00 and M_5m_P1 < 0.00)) and 75.0 > RSI_5m_C0 > 55.0 and -0.0100 < M_5m_C0 < limit_5m_M:
                    print(f" - It's buy signal for Strategy 15m Case-3: 5m x Up Triggered just after 15m Bullish Engulfing or One White Soldier")
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

                elif H_5m_P1 > 0.00 and H_5m_P2 < 0.00 and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_M:
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

            # 15m Case-4: 5m x Up Triggered on Continuous Green Bar (ZAA 5 JAN)
            elif C_15m_P1 > O_15m_P1 and C_15m_C0 > C_15m_P1 and C_15m_C0 > O_15m_C0 and 75.0 > RSI_15m_C0 > 55.0 and limit_15m_min_M < M_15m_C0 < limit_15m_max_M_case_4:
                
                # 5m Case-4_1:
                if ((H_5m_C0 > 0.00 and H_5m_P1 < 0.00) or (M_5m_C0 > 0.00 and M_5m_P1 < 0.00)) and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_M:
                    print(f" - It's buy signal for Strategy 15m Case-4: 5m x Up Triggered on Continuous Green Bar (4-1)")
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

                # 5m Case-4_2: Continuous Green Bar after x up CHASE (4 JAN)
                elif C_5m_C0 > O_5m_C0 and C_5m_C0 > C_5m_P1 and C_5m_P1 > O_5m_P1 and 75.0 > RSI_5m_C0 > 55.0 and M_5m_C0 < limit_5m_M:
                    print(f" - It's buy signal for Strategy 15m Case-4: 5m x Up Triggered on Continuous Green Bar (4_2)")
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
        market_value = abs(float(position.market_value))
        cost = abs(float(position.cost_basis))

        # Strategy 1 for taking profit 1
        if market_value > (1.01 * cost):    # 0 < H_5m_C0 < H_5m_P1 < H_5m_P2 and H_5m_P2 > H_5m_P3 and M_5m_P2 > 0 and S_5m_P3 > 0:
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
        elif market_price < E_60m_C0:
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
