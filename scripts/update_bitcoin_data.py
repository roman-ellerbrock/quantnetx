#!/usr/bin/env python3
"""
Update Bitcoin price data with latest weekly OHLC data.
Fetches missing data from the end of the CSV to current date.
"""

import pandas as pd
import requests
import time
from datetime import datetime, timezone

CSV_FILE = 'data/BTCUSD_1W.csv'
WEEK_SECONDS = 7 * 24 * 3600  # 1 week in seconds
MAX_RETRIES = 3  # Number of retries for API requests
RETRY_DELAY = 2  # Seconds to wait between retries

def fetch_binance_klines(start_time, end_time=None):
    """
    Fetch weekly Bitcoin price data from Binance API with retry logic.

    Args:
        start_time: Unix timestamp in seconds
        end_time: Unix timestamp in seconds (optional)

    Returns:
        List of OHLC data: [[time, open, high, low, close], ...]
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

    print(f"Fetching data from Binance...")
    print(f"  Start: {datetime.fromtimestamp(start_time, tz=timezone.utc)}")
    print(f"  End:   {datetime.fromtimestamp(end_time if end_time else time.time(), tz=timezone.utc)}")

    # Retry loop
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                print(f"  Retry attempt {attempt + 1}/{MAX_RETRIES}...")
                time.sleep(RETRY_DELAY)

            response = requests.get(url, params=params, timeout=10)
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

            print(f"Fetched {len(data)} candles from Binance")
            return data

        except requests.RequestException as e:
            print(f"Error fetching data from Binance (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Status code: {e.response.status_code}")
                print(f"  Response body: {e.response.text}")

            # If this was the last attempt, return empty list
            if attempt == MAX_RETRIES - 1:
                print("All retry attempts exhausted")
                return []

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
    """Update CSV with latest Bitcoin data."""
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

    # Fetch new data
    print(f"\nFetching missing data...")
    new_data = fetch_binance_klines(next_timestamp, current_timestamp)

    if not new_data:
        print("No new data fetched")
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
