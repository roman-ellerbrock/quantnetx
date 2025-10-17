#!/usr/bin/env python3
"""
Fetch historical market data for equities and commodities.
Simple, extensible script using Yahoo Finance via yfinance or direct API calls.
"""

import requests
import csv
import os
import time
from datetime import datetime, timedelta

# Symbol mapping: name -> Yahoo Finance ticker
SYMBOLS = {
    'SP500': '^GSPC',      # S&P 500
    'NASDAQ': '^IXIC',     # NASDAQ Composite
    'COPPER': 'HG=F',      # Copper Futures
    'GOLD': 'GC=F',        # Gold Futures
    'OIL': 'CL=F',         # Crude Oil WTI Futures
    'TLT': 'TLT',          # iShares 20+ Year Treasury Bond ETF
    'BTC': 'BTC-USD',      # Bitcoin (for comparison)
}

def fetch_yahoo_finance(symbol, start_date=None, end_date=None, interval='1d'):
    """
    Fetch historical data from Yahoo Finance using direct API.

    Args:
        symbol: Yahoo Finance ticker symbol
        start_date: Start date (YYYY-MM-DD) or None for max history
        end_date: End date (YYYY-MM-DD) or None for today
        interval: Data interval (1d, 1wk, 1mo)

    Returns:
        List of dicts with OHLCV data
    """
    # Convert dates to Unix timestamps
    if start_date:
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
    else:
        start_ts = 0  # Earliest available

    if end_date:
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
    else:
        end_ts = int(datetime.now().timestamp())

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        'period1': start_ts,
        'period2': end_ts,
        'interval': interval,
        'events': 'history'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quotes = result['indicators']['quote'][0]

        # Convert to list of dicts
        records = []
        for i, ts in enumerate(timestamps):
            date_obj = datetime.fromtimestamp(ts)
            records.append({
                'date': date_obj.strftime('%Y-%m-%d'),
                'timestamp': ts,
                'open': quotes['open'][i],
                'high': quotes['high'][i],
                'low': quotes['low'][i],
                'close': quotes['close'][i],
                'volume': quotes['volume'][i] if quotes['volume'][i] else 0
            })

        return records

    except Exception as e:
        print(f"  ✗ Error fetching {symbol}: {e}")
        return []

def save_to_csv(data, filename, symbol_name):
    """Save data to CSV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w', newline='') as f:
        if not data:
            print(f"  ✗ No data for {symbol_name}")
            return

        fieldnames = ['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"  ✓ Saved {len(data)} days to {filename}")

def fetch_all_symbols(symbols=SYMBOLS, interval='1d', start_date=None, end_date=None):
    """
    Fetch data for all symbols and save to CSV files.

    Args:
        symbols: Dict of {name: ticker}
        interval: Data interval (1d, 1wk, 1mo)
        start_date: Start date or None
        end_date: End date or None
    """
    print("=" * 60)
    print(f"Fetching Market Data (interval={interval})")
    print("=" * 60)

    results = {}

    for name, ticker in symbols.items():
        print(f"\n{name} ({ticker}):")
        data = fetch_yahoo_finance(ticker, start_date, end_date, interval)

        # Rate limiting - wait between requests
        time.sleep(1.5)

        if data:
            filename = f'data/market_data/{name.lower()}_{interval}.csv'
            save_to_csv(data, filename, name)
            results[name] = data

            # Show summary
            if len(data) > 0:
                first = data[0]
                last = data[-1]
                pct_change = ((last['close'] - first['close']) / first['close']) * 100
                print(f"  Range: {first['date']} to {last['date']}")
                print(f"  Return: {pct_change:+.2f}%")

    print("\n" + "=" * 60)
    print(f"Summary: Fetched {len(results)}/{len(symbols)} symbols")
    print("=" * 60)

    return results

def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch market data from Yahoo Finance')
    parser.add_argument('--symbols', nargs='+', help='Symbols to fetch (default: all)')
    parser.add_argument('--interval', default='1d', choices=['1d', '1wk', '1mo'],
                        help='Data interval (default: 1d)')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--add-symbol', nargs=2, metavar=('NAME', 'TICKER'),
                        help='Add custom symbol (e.g., --add-symbol AAPL AAPL)')

    args = parser.parse_args()

    # Build symbol dict
    symbols = SYMBOLS.copy()

    if args.add_symbol:
        symbols[args.add_symbol[0]] = args.add_symbol[1]

    if args.symbols:
        # Filter to requested symbols
        symbols = {k: v for k, v in symbols.items() if k in args.symbols}

    # Fetch data
    fetch_all_symbols(symbols, args.interval, args.start, args.end)

if __name__ == '__main__':
    main()
