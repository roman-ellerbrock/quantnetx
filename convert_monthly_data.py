#!/usr/bin/env python3
"""
Convert TradingView monthly data format to standard format.
Input: time,open,high,low,close (Unix timestamp)
Output: date,timestamp,open,high,low,close,volume (standard format)
"""

import csv
from datetime import datetime

def convert_file(input_file, output_file):
    """Convert TradingView format to standard format."""
    rows_in = []
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_in.append(row)

    rows_out = []
    for row in rows_in:
        timestamp = int(row['time'])
        date_obj = datetime.fromtimestamp(timestamp)

        rows_out.append({
            'date': date_obj.strftime('%Y-%m-%d'),
            'timestamp': timestamp,
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': 0  # Monthly data doesn't have volume
        })

    with open(output_file, 'w', newline='') as f:
        fieldnames = ['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Converted {input_file} -> {output_file} ({len(rows_out)} rows)")
    if rows_out:
        print(f"  Range: {rows_out[0]['date']} to {rows_out[-1]['date']}")

if __name__ == '__main__':
    convert_file('data/SP_SPX, 1M.csv', 'data/market_data/sp500_1mo.csv')
    convert_file('data/TVC_GOLD, 1M.csv', 'data/market_data/gold_1mo.csv')
    convert_file('data/TVC_UKOIL, 1M.csv', 'data/market_data/oil_1mo.csv')
