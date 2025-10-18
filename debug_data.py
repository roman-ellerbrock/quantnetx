import csv
import os

filepath = 'data/market_data/sp500_1mo.csv'
dates = []

with open(filepath, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['close'] and row['close'].strip():
            dates.append(row['date'])

print(f'SP500 monthly data:')
print(f'  Total rows: {len(dates)}')
print(f'  First date: {dates[0]}')
print(f'  Last date: {dates[-1]}')
