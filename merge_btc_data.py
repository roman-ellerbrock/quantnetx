#!/usr/bin/env python3
"""Merge Bitcoin data from BTCUSD_1W.csv and btc.csv"""

import csv
from datetime import datetime

# Read BTCUSD_1W.csv (extended historical data)
btc_weekly = {}
with open('data/BTCUSD_1W.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        unix_time = int(row['time'])
        date_str = datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d')
        btc_weekly[date_str] = float(row['close'])

print(f'Loaded {len(btc_weekly)} points from BTCUSD_1W.csv')
print(f'Date range: {min(btc_weekly.keys())} to {max(btc_weekly.keys())}')

# Read existing btc.csv
btc_daily = {}
try:
    with open('data/market_data/btc.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['close'] and row['close'].strip():
                btc_daily[row['date']] = float(row['close'])
    print(f'Loaded {len(btc_daily)} points from btc.csv')
    print(f'Date range: {min(btc_daily.keys())} to {max(btc_daily.keys())}')
except Exception as e:
    print(f'Error reading btc.csv: {e}')
    btc_daily = {}

# Merge: use weekly data as base, then fill in with daily data for dates not in weekly
merged = btc_weekly.copy()
for date, price in btc_daily.items():
    if date not in merged:
        merged[date] = price

print(f'\nMerged total: {len(merged)} points')
print(f'Date range: {min(merged.keys())} to {max(merged.keys())}')

# Write merged data back to btc.csv with proper format (date, timestamp, open, high, low, close, volume)
sorted_dates = sorted(merged.keys())
with open('data/market_data/btc.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])
    for date in sorted_dates:
        price = merged[date]
        # Calculate Unix timestamp from date
        from datetime import datetime
        dt = datetime.strptime(date, '%Y-%m-%d')
        timestamp = int(dt.timestamp())
        # Use same price for open, high, low, close (we only have close data)
        writer.writerow([date, timestamp, price, price, price, price, 0])

print(f'\nWritten {len(sorted_dates)} points to data/market_data/btc.csv')
print('Merge complete!')
