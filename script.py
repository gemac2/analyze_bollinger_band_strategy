from binance.client import Client
import pandas as pd
from pytz import timezone
from datetime import datetime, timedelta
from ta.volatility import BollingerBands

def get_historical_data(symbol, timeframe, days):

    client = Client('', '', tld='com')

    # Calculate start and end dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Get historical data using the Binance client
    klines = client.futures_historical_klines(symbol, timeframe, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S"))

    return klines

def analyze_bollinger_bands(symbol, timeframe, days):
    # Get historical data
    klines = get_historical_data(symbol, timeframe, days)

    # Convert to pandas DataFrame
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)  # Convert 'high' to float
    df['low'] = df['low'].astype(float)    # Convert 'low' to float

    # Drop rows with missing values
    df.dropna(inplace=True)

    # Calculate Bollinger Bands
    bb = BollingerBands(df['close'], window=20, window_dev=3)
    upper_band = bb.bollinger_hband()
    lower_band = bb.bollinger_lband()

   # Identify when the candle breaks above the upper band (for bullish candles) and below the lower band (for bearish candles)
    df['price_above_upper'] = (df['close'] > df['open']) & (df['high'] > upper_band)   # Bullish candle breaking above upper band
    df['price_below_lower'] = (df['close'] < df['open']) & (df['low'] < lower_band)      # Bearish candle breaking below lower band

    # Initialize variables
    max_distance_above_upper = 0
    max_distance_below_lower = 0
    signals_above_0_5_percent = 0
    signals_under_0_5_percent = 0

    # Print the breakout time and distance to the maximum for each candle
    print("Breakout Time   |   Distance to Band (%)   |   Breaking Candle Max Price   |   Next Candle Min Price   |   Next Candle Max Price   |   Distance to Min (%)   |   Distance to Max (%)")
    for i in range(len(df) - 1):  # Iterate up to the second last row
        if df.iloc[i]['price_above_upper'] or df.iloc[i]['price_below_lower']:
            breakout_time = df.index[i].tz_localize(timezone('UTC')).tz_convert(timezone('America/Bogota'))
            # breakout_close_price = df.iloc[i]['close']
            breaking_candle_max_price = df.iloc[i]['high']
            breaking_candle_min_price = df.iloc[i]['low']
            next_candle_min_price = df.iloc[i + 1]['low']
            next_candle_max_price = df.iloc[i + 1]['high']
            breaking_candle_price = 0.0
            next_candle_first_price = 0.0
            next_candle_second_price = 0.0

            if df.iloc[i]['price_above_upper']:
                distance_to_band = ((breaking_candle_max_price - upper_band.iloc[i]) / upper_band.iloc[i]) * 100
                distance_to_max_percentage = ((breaking_candle_max_price - next_candle_max_price) / next_candle_max_price) * -100
                distance_to_min_percentage = ((breaking_candle_max_price - next_candle_min_price) / next_candle_min_price) * -100
                breaking_candle_price = breaking_candle_max_price
                next_candle_first_price =  next_candle_min_price
                next_candle_second_price = next_candle_max_price

                if abs(distance_to_min_percentage) >= 0.5:
                    signals_above_0_5_percent += 1
                else:
                    signals_under_0_5_percent += 1

            elif df.iloc[i]['price_below_lower']:
                distance_to_band = ((breaking_candle_min_price - lower_band.iloc[i]) / lower_band.iloc[i]) * 100
                distance_to_max_percentage = ((breaking_candle_min_price - next_candle_min_price) / next_candle_min_price) * -100
                distance_to_min_percentage = ((breaking_candle_min_price - next_candle_max_price) / next_candle_max_price) * -100
                breaking_candle_price = breaking_candle_min_price
                next_candle_first_price =  next_candle_max_price
                next_candle_second_price = next_candle_min_price

                if abs(distance_to_min_percentage) >= 0.5:
                    signals_above_0_5_percent += 1
                else:
                    signals_under_0_5_percent += 1
            

            # Update max distances
            if distance_to_band > max_distance_above_upper:
                max_distance_above_upper = distance_to_band
            if distance_to_band < max_distance_below_lower:
                max_distance_below_lower = distance_to_band

            # Format percentage with a "+" sign if positive
            distance_to_band_str = f"+{distance_to_band:.2f}%" if distance_to_band > 0 else f"{distance_to_band:.2f}%"
            distance_to_max_percentage_str = f"+{distance_to_max_percentage:.2f}%" if distance_to_max_percentage > 0 else f"{distance_to_max_percentage:.2f}%"
            distance_to_min_percentage_str = f"+{distance_to_min_percentage:.2f}%" if distance_to_min_percentage > 0 else f"{distance_to_min_percentage:.2f}%"

            print(f"{breakout_time}   |   {distance_to_band_str}   |   {breaking_candle_price:.2f}   |   {next_candle_first_price:.2f}   |   {next_candle_second_price:.2f}   |   {distance_to_min_percentage_str}   |   {distance_to_max_percentage_str}")

    # Print the number of candles that broke the Bollinger Bands
    num_breakouts = sum((df['high'] > upper_band) & (df['close'] > df['open']) | (df['low'] < lower_band) & (df['close'] < df['open']))
    print(f"Number of candles that broke the Bollinger Bands: {num_breakouts}")

    # Print the highest percentage distance from the upper and lower bands
    print(f"Highest percentage distance from upper band: {max_distance_above_upper:.2f}%")
    print(f"Highest percentage distance from lower band: {max_distance_below_lower:.2f}%")
    print("Signals with take profit above 0.5%:", signals_above_0_5_percent)
    print("Signals with take profit under 0.5%:", signals_under_0_5_percent)




# Prompt the user to enter parameters
symbol = input("Enter the cryptocurrency symbol (e.g., 'BTCUSDT'): ")
timeframe = input("Enter the timeframe (e.g., '5m', '1h', '1d'): ")
days = int(input("Enter the number of days back you want to analyze: "))

analyze_bollinger_bands(symbol, timeframe, days)


