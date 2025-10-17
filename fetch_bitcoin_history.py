#!/usr/bin/env python3
"""
Fetch historical Bitcoin daily price data and save to file.
Uses only standard library + requests (Binance API - free, no auth needed).
"""

import json
import requests
from datetime import datetime
import os
import time

def fetch_bitcoin_from_binance():
    """
    Fetch historical Bitcoin data from Binance API.
    Binance has free API access and data back to 2017-08-17.

    Returns:
        List of price data dictionaries
    """
    print("Fetching Bitcoin historical data from Binance...")
    print("(Data available from 2017-08-17 onwards)")

    all_data = []

    # Binance API endpoint
    url = "https://api.binance.com/api/v3/klines"

    # Start from earliest available date on Binance
    start_time = int(datetime(2017, 8, 17).timestamp() * 1000)
    end_time = int(datetime.now().timestamp() * 1000)

    current_time = start_time
    batch_count = 0

    while current_time < end_time:
        params = {
            'symbol': 'BTCUSDT',
            'interval': '1d',
            'startTime': current_time,
            'limit': 1000  # Max per request
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            # Process each candle
            for candle in data:
                timestamp_ms = candle[0]
                date_obj = datetime.fromtimestamp(timestamp_ms / 1000)

                price_data = {
                    'timestamp': timestamp_ms,
                    'date': date_obj.strftime('%Y-%m-%d'),
                    'datetime': date_obj.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                }

                all_data.append(price_data)

            # Move to next batch
            current_time = data[-1][0] + 86400000  # Add 1 day in milliseconds

            batch_count += 1
            if batch_count % 5 == 0:
                print(f"  Fetched {len(all_data)} days so far...")

            # Rate limiting - be nice to Binance API
            time.sleep(0.2)

            if len(data) < 1000:
                break

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching data: {e}")
            if all_data:
                print(f"  Returning partial data ({len(all_data)} days)")
                break
            return None

    print(f"✓ Successfully fetched {len(all_data)} days of Bitcoin data")
    return all_data

def save_to_json(data, filename='data/bitcoin_historical_prices.json'):
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    print(f"\nSaving data to {filename}...")

    output = {
        'metadata': {
            'source': 'Binance API',
            'symbol': 'BTCUSDT',
            'currency': 'USD',
            'interval': 'daily',
            'total_days': len(data),
            'first_date': data[0]['date'] if data else None,
            'last_date': data[-1]['date'] if data else None,
            'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        'data': data
    }

    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✓ Saved {len(data)} days to {filename}")

def save_to_csv(data, filename='data/bitcoin_historical_prices.csv'):
    """Save data to CSV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    print(f"Saving data to {filename}...")

    import csv

    with open(filename, 'w', newline='') as f:
        if not data:
            print("✗ No data to save")
            return

        fieldnames = ['date', 'datetime', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(data)

    print(f"✓ Saved {len(data)} days to {filename}")

def calculate_statistics(data):
    """Calculate basic statistics from the data."""
    if not data or len(data) < 2:
        return

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    first = data[0]
    last = data[-1]

    print(f"Total days:        {len(data)}")
    print(f"Date range:        {first['date']} to {last['date']}")
    print()
    print(f"First close:       ${first['close']:,.2f}")
    print(f"Last close:        ${last['close']:,.2f}")
    print()

    # Calculate total return
    total_return = ((last['close'] - first['close']) / first['close']) * 100
    print(f"Total return:      {total_return:,.2f}%")

    # Calculate high and low
    all_highs = [d['high'] for d in data]
    all_lows = [d['low'] for d in data]
    all_time_high = max(all_highs)
    all_time_low = min(all_lows)

    ath_date = next(d['date'] for d in data if d['high'] == all_time_high)
    atl_date = next(d['date'] for d in data if d['low'] == all_time_low)

    print(f"All-time high:     ${all_time_high:,.2f} ({ath_date})")
    print(f"All-time low:      ${all_time_low:,.2f} ({atl_date})")

    # Average daily volume
    avg_volume = sum(d['volume'] for d in data) / len(data)
    print(f"Avg daily volume:  {avg_volume:,.0f} BTC")

    print("=" * 60)

def main():
    """Main execution function."""
    print("=" * 60)
    print("Bitcoin Historical Price Data Fetcher")
    print("=" * 60)
    print()

    # Fetch data
    data = fetch_bitcoin_from_binance()

    if not data:
        print("\n✗ Failed to fetch data. Exiting.")
        return

    # Save data
    save_to_json(data)
    save_to_csv(data)

    # Show statistics
    calculate_statistics(data)

if __name__ == '__main__':
    main()
