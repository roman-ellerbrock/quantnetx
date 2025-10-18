#!/usr/bin/env python3
"""
Merge multiple timeframes (1mo, 1wk, 1d) into single comprehensive files.
Strategy: Use monthly data for old history, weekly for medium, daily for recent.
Remove duplicates and ensure chronological order.
"""

import csv
import os
from datetime import datetime
from collections import defaultdict

DATA_DIR = 'data/market_data'

# Symbols to merge
SYMBOLS = ['btc', 'sp500', 'nasdaq', 'vti', 'eem', 'gold', 'silver', 'palladium', 'nickel',
           'copper', 'oil', 'tlt']

def load_csv(filepath):
    """Load CSV file and return list of rows."""
    if not os.path.exists(filepath):
        return []

    rows = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['close'] and row['close'].strip():
                rows.append(row)
    return rows

def merge_symbol(symbol):
    """Merge all timeframes for a symbol into single file."""
    print(f"\n{symbol.upper()}:")

    # Load all available timeframes
    all_data = {}  # date -> row (keep most granular data per date)

    # Try each interval (monthly first for oldest data, then weekly, then daily)
    intervals = ['1mo', '1wk', '1d']

    for interval in intervals:
        filepath = os.path.join(DATA_DIR, f'{symbol}_{interval}.csv')
        rows = load_csv(filepath)

        if rows:
            print(f"  {interval}: {len(rows)} rows ({rows[0]['date']} to {rows[-1]['date']})")

            for row in rows:
                date = row['date']
                # Keep the most granular data (prefer 1d over 1wk over 1mo)
                # But fill in gaps with whatever we have
                if date not in all_data:
                    all_data[date] = row
                else:
                    # Prefer more granular data (1d > 1wk > 1mo)
                    current_interval = all_data[date].get('_interval', '1mo')
                    interval_rank = {'1d': 3, '1wk': 2, '1mo': 1}
                    if interval_rank.get(interval, 0) > interval_rank.get(current_interval, 0):
                        all_data[date] = row

                # Mark which interval this came from
                all_data[date]['_interval'] = interval

    if not all_data:
        print(f"  ⚠ No data found for {symbol}")
        return

    # Sort by date
    sorted_dates = sorted(all_data.keys())
    sorted_rows = [all_data[date] for date in sorted_dates]

    # Write merged file
    output_file = os.path.join(DATA_DIR, f'{symbol}.csv')
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in sorted_rows:
            # Remove internal tracking field
            if '_interval' in row:
                del row['_interval']
            writer.writerow({k: row[k] for k in fieldnames})

    print(f"  ✓ Merged: {len(sorted_rows)} total rows ({sorted_rows[0]['date']} to {sorted_rows[-1]['date']})")
    print(f"  → Saved to {output_file}")

def main():
    print("=" * 70)
    print("Merging Market Data Timeframes")
    print("=" * 70)

    for symbol in SYMBOLS:
        merge_symbol(symbol)

    print("\n" + "=" * 70)
    print("Done! Merged files saved as data/market_data/{symbol}.csv")
    print("=" * 70)

if __name__ == '__main__':
    main()
