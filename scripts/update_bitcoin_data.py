#!/usr/bin/env python3
"""
Update Bitcoin price data with latest weekly OHLC data.
Fetches missing data from the end of the CSV to current date.
"""

import pandas as pd
import requests
import time
from datetime import datetime, timezone, timedelta

CSV_FILE = 'data/BTCUSD_1W.csv'
WEEK_SECONDS = 7 * 24 * 3600  # 1 week in seconds
MAX_RETRIES = 3  # Number of retries for API requests
RETRY_DELAY = 2  # Seconds to wait between retries

def fetch_binance_klines(start_time, end_time=None, max_retries=3):
    """
    Fetch weekly Bitcoin price data from Binance API with retry logic.

    Args:
        start_time: Unix timestamp in seconds
        end_time: Unix timestamp in seconds (optional)
        max_retries: Number of retry attempts

    Returns:
        List of OHLC data: [[time, open, high, low, close], ...] or None if geo-blocked
    """
    url = "https://api.binance.com/api/v3/klines"

    # Binance uses milliseconds
    start_ms = int(start_time * 1000)
    end_ms = int(end_time * 1000) if end_time else int(time.time() * 1000)

    params = {
        'symbol': 'BTCUSDT',
        'interval': '1w',
        'startTime': start_ms,
        'endTime': end_ms,
        'limit': 1000  # Max limit per request
    }

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Fetching data from Binance (attempt {attempt}/{max_retries})...")
            print(f"  Start: {datetime.fromtimestamp(start_time, tz=timezone.utc)}")
            print(f"  End:   {datetime.fromtimestamp(end_time if end_time else time.time(), tz=timezone.utc)}")

            response = requests.get(url, params=params, timeout=10)

            # Check for geo-blocking (HTTP 451)
            if response.status_code == 451:
                print(f"  Binance API blocked (HTTP 451 - geo-restricted)")
                print(f"  Response: {response.text[:200]}")
                return None  # Signal to use fallback

            response.raise_for_status()

            klines = response.json()

            # Convert Binance format to our format
            # Binance returns: [open_time, open, high, low, close, volume, ...]
            data = []
            for kline in klines:
                timestamp = int(kline[0]) // 1000  # Convert ms to seconds
                open_price = float(kline[1])
                high_price = float(kline[2])
                low_price = float(kline[3])
                close_price = float(kline[4])

                data.append([timestamp, open_price, high_price, low_price, close_price])

            print(f"  Successfully fetched {len(data)} candles from Binance")
            return data

        except requests.RequestException as e:
            print(f"  Error fetching data from Binance (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"  All {max_retries} attempts failed")
                return []

    return []

def fetch_yahoo_finance(start_time, end_time=None):
    """
    Fetch weekly Bitcoin price data from Yahoo Finance API as fallback.

    Args:
        start_time: Unix timestamp in seconds
        end_time: Unix timestamp in seconds (optional)

    Returns:
        List of OHLC data: [[time, open, high, low, close], ...]
    """
    try:
        print(f"Fetching data from Yahoo Finance (fallback)...")
        print(f"  Start: {datetime.fromtimestamp(start_time, tz=timezone.utc)}")
        print(f"  End:   {datetime.fromtimestamp(end_time if end_time else time.time(), tz=timezone.utc)}")

        url = "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD"
        params = {
            'period1': int(start_time),
            'period2': int(end_time) if end_time else int(time.time()),
            'interval': '1wk',
            'events': 'history'
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()

        data_json = response.json()
        result = data_json['chart']['result'][0]

        timestamps = result['timestamp']
        quotes = result['indicators']['quote'][0]

        # Convert to our format
        data = []
        for i, ts in enumerate(timestamps):
            # Yahoo Finance returns daily data, we need to filter to weekly
            # The timestamps should already be weekly with interval='1wk'
            open_price = quotes['open'][i]
            high_price = quotes['high'][i]
            low_price = quotes['low'][i]
            close_price = quotes['close'][i]

            # Skip if data is None
            if None in [open_price, high_price, low_price, close_price]:
                continue

            data.append([ts, float(open_price), float(high_price), float(low_price), float(close_price)])

        print(f"  Successfully fetched {len(data)} candles from Yahoo Finance")
        return data

    except Exception as e:
        print(f"  Error fetching data from Yahoo Finance: {e}")
        return []

def fetch_coingecko(start_time, end_time=None):
    """
    Fetch Bitcoin price data from CoinGecko API as fallback.
    Note: CoinGecko provides daily data, so we'll aggregate to weekly.

    Args:
        start_time: Unix timestamp in seconds
        end_time: Unix timestamp in seconds (optional)

    Returns:
        List of OHLC data: [[time, open, high, low, close], ...]
    """
    try:
        print(f"Fetching data from CoinGecko (fallback)...")
        print(f"  Start: {datetime.fromtimestamp(start_time, tz=timezone.utc)}")
        print(f"  End:   {datetime.fromtimestamp(end_time if end_time else time.time(), tz=timezone.utc)}")

        # CoinGecko OHLC endpoint gives candles
        # Format: /coins/{id}/ohlc?vs_currency=usd&days={days}
        # We need to calculate days from start_time to end_time
        current_time = end_time if end_time else int(time.time())
        days = (current_time - start_time) // 86400 + 1

        url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"
        params = {
            'vs_currency': 'usd',
            'days': min(days, 365)  # CoinGecko has limits on days
        }

        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()

        ohlc_data = response.json()

        # CoinGecko returns: [[timestamp_ms, open, high, low, close], ...]
        # We need to aggregate daily data into weekly candles
        if not ohlc_data:
            print(f"  No data returned from CoinGecko")
            return []

        # Convert to weekly candles
        weekly_data = []
        current_week = []
        week_start = None

        for candle in ohlc_data:
            timestamp_ms = candle[0]
            timestamp = timestamp_ms // 1000

            # Skip data before start_time
            if timestamp < start_time:
                continue

            # Determine week boundary (Monday 00:00 UTC)
            candle_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            week_start_date = candle_date - timedelta(days=candle_date.weekday())
            week_start_timestamp = int(week_start_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

            if week_start != week_start_timestamp:
                # New week - process previous week if exists
                if current_week:
                    weekly_candle = aggregate_to_weekly(current_week, week_start)
                    if weekly_candle:
                        weekly_data.append(weekly_candle)

                # Start new week
                week_start = week_start_timestamp
                current_week = []

            current_week.append(candle)

        # Process final week
        if current_week:
            weekly_candle = aggregate_to_weekly(current_week, week_start)
            if weekly_candle:
                weekly_data.append(weekly_candle)

        print(f"  Successfully fetched and aggregated {len(weekly_data)} weekly candles from CoinGecko")
        return weekly_data

    except Exception as e:
        print(f"  Error fetching data from CoinGecko: {e}")
        return []

def aggregate_to_weekly(daily_candles, week_start_timestamp):
    """
    Aggregate daily candles into a weekly candle.

    Args:
        daily_candles: List of daily candles [[timestamp_ms, open, high, low, close], ...]
        week_start_timestamp: Unix timestamp for start of week

    Returns:
        Weekly candle [timestamp, open, high, low, close]
    """
    if not daily_candles:
        return None

    # Open: first candle's open
    weekly_open = daily_candles[0][1]

    # High: max of all highs
    weekly_high = max(candle[2] for candle in daily_candles)

    # Low: min of all lows
    weekly_low = min(candle[3] for candle in daily_candles)

    # Close: last candle's close
    weekly_close = daily_candles[-1][4]

    return [week_start_timestamp, weekly_open, weekly_high, weekly_low, weekly_close]

def get_last_timestamp(csv_file):
    """Get the last timestamp from the CSV file."""
    try:
        df = pd.read_csv(csv_file)
        if len(df) == 0:
            return None

        last_time = df['time'].iloc[-1]
        print(f"\nLast timestamp in CSV: {last_time}")
        print(f"  Date: {datetime.fromtimestamp(last_time, tz=timezone.utc)}")
        return int(last_time)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

def update_csv(csv_file):
    """Update CSV with latest Bitcoin data using fallback strategy."""
    # Get last timestamp from CSV
    last_timestamp = get_last_timestamp(csv_file)

    if last_timestamp is None:
        print("Could not read last timestamp from CSV")
        return False

    # Calculate next week's timestamp (we want data after the last entry)
    next_timestamp = last_timestamp + WEEK_SECONDS
    current_timestamp = int(time.time())

    # Check if we need to update
    if next_timestamp > current_timestamp:
        print(f"\nCSV is already up to date!")
        print(f"  Last entry: {datetime.fromtimestamp(last_timestamp, tz=timezone.utc)}")
        print(f"  Next week:  {datetime.fromtimestamp(next_timestamp, tz=timezone.utc)}")
        print(f"  Current:    {datetime.fromtimestamp(current_timestamp, tz=timezone.utc)}")
        return True

    # Fetch new data with fallback strategy
    print(f"\nFetching missing data...")
    print(f"Strategy: Try Binance → Yahoo Finance → CoinGecko")
    print()

    # Try Binance first (primary source)
    new_data = fetch_binance_klines(next_timestamp, current_timestamp)

    # If Binance is geo-blocked (returns None) or failed (returns []), try fallbacks
    if new_data is None or len(new_data) == 0:
        print(f"\nBinance unavailable, trying Yahoo Finance...")
        new_data = fetch_yahoo_finance(next_timestamp, current_timestamp)

    if not new_data or len(new_data) == 0:
        print(f"\nYahoo Finance unavailable, trying CoinGecko...")
        new_data = fetch_coingecko(next_timestamp, current_timestamp)

    if not new_data:
        print("\nAll data sources failed - no new data fetched")
        return False

    # Create DataFrame with new data
    new_df = pd.DataFrame(new_data, columns=['time', 'open', 'high', 'low', 'close'])

    # Remove any duplicates based on timestamp
    existing_df = pd.read_csv(csv_file)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['time'], keep='last')
    combined_df = combined_df.sort_values('time')

    # Save back to CSV
    combined_df.to_csv(csv_file, index=False)

    print(f"\n✓ Successfully updated {csv_file}")
    print(f"  Added {len(new_data)} new entries")
    print(f"  Total entries: {len(combined_df)}")
    print(f"  Latest date: {datetime.fromtimestamp(combined_df['time'].iloc[-1], tz=timezone.utc)}")

    return True

def main():
    print("="*70)
    print("Bitcoin Price Data Update")
    print("="*70)

    success = update_csv(CSV_FILE)

    if success:
        print("\n" + "="*70)
        print("Update complete! Run scripts/bitcoin_risk_regression.py to regenerate charts.")
        print("="*70)
    else:
        print("\nUpdate failed!")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
