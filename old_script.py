from binance.client import Client
import pandas as pd
from pytz import timezone
from datetime import datetime, timedelta
from ta.volatility import BollingerBands

def get_historical_data(symbol, timeframe, days):
    """
    Gets historical data from Binance for a given cryptocurrency pair and timeframe.
    """
    client = Client('', '', tld='com')

    # Calculate start and end dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Get historical data using the Binance client
    klines = client.futures_historical_klines(symbol, timeframe, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S"))

    return klines

def analyze_bollinger_bands(symbol, timeframe, days):
    """
    Performs the analysis of Bollinger Bands for a given cryptocurrency pair.
    """
    # Get historical data
    klines = get_historical_data(symbol, timeframe, days)

    # Convert to pandas DataFrame
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)  # Convert 'high' to float
    df['low'] = df['low'].astype(float)    # Convert 'low' to float

    # Drop rows with missing values
    df.dropna(inplace=True)

    # Calculate Bollinger Bands
    bb = BollingerBands(df['close'], window=20, window_dev=3)
    upper_band = bb.bollinger_hband()
    lower_band = bb.bollinger_lband()

    # Identify the times when the price breaks above and below the bands
    df['price_above_upper'] = df['close'] > upper_band
    df['price_below_lower'] = df['close'] < lower_band

    # Initialize variables to store the highest percentage distance from the upper and lower bands
    max_distance_above_upper = 0
    max_distance_below_lower = 0

    # Print the breakout time and distance to the maximum for each candle
    print("Breakout Time   |   Distance to Max (%)")
    for index, row in df.iterrows():
        if row['price_above_upper']:
            distance_to_max_price_percentage = ((row['high'] - row['close']) / row['close']) * 100
            print(f"{index.tz_localize(timezone('UTC')).tz_convert(timezone('America/Bogota'))}   |   {distance_to_max_price_percentage:.2f}%")
            if distance_to_max_price_percentage > max_distance_above_upper:
                max_distance_above_upper = distance_to_max_price_percentage
        elif row['price_below_lower']:
            distance_to_min_price_percentage = ((row['low'] - row['close']) / row['close']) * 100
            print(f"{index.tz_localize(timezone('UTC')).tz_convert(timezone('America/Bogota'))}   |   {distance_to_min_price_percentage:.2f}%")
            if distance_to_min_price_percentage < max_distance_below_lower:
                max_distance_below_lower = distance_to_min_price_percentage
    
    # Print the number of candles that broke the Bollinger Bands
    num_breakouts = sum((df['price_above_upper'] | df['price_below_lower']).astype(int))
    print(f"Number of candles that broke the Bollinger Bands: {num_breakouts}")

    # Print the highest percentage distance from the upper and lower bands
    print(f"Highest percentage distance from upper band: {max_distance_above_upper:.2f}%")
    print(f"Highest percentage distance from lower band: {max_distance_below_lower:.2f}%")

# Prompt the user to enter parameters
symbol = input("Enter the cryptocurrency symbol (e.g., 'BTCUSDT'): ")
timeframe = '5m'
days = int(input("Enter the number of days back you want to analyze: "))

analyze_bollinger_bands(symbol, timeframe, days)
