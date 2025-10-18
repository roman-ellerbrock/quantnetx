import csv

btc_dates = set()
sp500_dates = set()

with open('data/market_data/btc_1wk.csv') as f:
    for row in csv.DictReader(f):
        btc_dates.add(row['date'])

with open('data/market_data/sp500_1wk.csv') as f:
    for row in csv.DictReader(f):
        sp500_dates.add(row['date'])

common = btc_dates & sp500_dates
print(f'BTC dates: {len(btc_dates)}')
print(f'SP500 dates: {len(sp500_dates)}')
print(f'Common dates: {len(common)}')
if common:
    print(f'Sample: {sorted(list(common))[:5]}')
