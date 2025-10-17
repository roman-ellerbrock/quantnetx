# Market Data Fetcher

Simple script to fetch historical market data from Yahoo Finance.

## Usage

### Fetch all default symbols (daily data):
```bash
python3 fetch_market_data.py
```

### Fetch specific symbols only:
```bash
python3 fetch_market_data.py --symbols SP500 NASDAQ BTC
```

### Fetch weekly data:
```bash
python3 fetch_market_data.py --interval 1wk
```

### Fetch data for specific date range:
```bash
python3 fetch_market_data.py --start 2020-01-01 --end 2023-12-31
```

### Add custom symbol:
```bash
python3 fetch_market_data.py --add-symbol AAPL AAPL
python3 fetch_market_data.py --add-symbol TSLA TSLA
```

## Default Symbols

| Name | Yahoo Ticker | Description |
|------|--------------|-------------|
| SP500 | ^GSPC | S&P 500 Index |
| NASDAQ | ^IXIC | NASDAQ Composite |
| COPPER | HG=F | Copper Futures |
| GOLD | GC=F | Gold Futures |
| OIL | CL=F | Crude Oil WTI Futures |
| TLT | TLT | 20+ Year Treasury Bond ETF |
| BTC | BTC-USD | Bitcoin |

## Output

Data is saved to `data/market_data/{symbol}_{interval}.csv`

CSV format:
- date: YYYY-MM-DD
- timestamp: Unix timestamp
- open: Opening price
- high: High price
- low: Low price
- close: Closing price
- volume: Trading volume

## Data Coverage

- **SP500/NASDAQ**: Back to 1970s
- **Commodities**: Back to ~2000
- **TLT**: Back to 2002
- **BTC**: Back to 2014

## Adding More Symbols

Edit `SYMBOLS` dict in the script or use `--add-symbol` flag.

Examples of Yahoo Finance tickers:
- Stocks: AAPL, MSFT, TSLA, etc.
- Indices: ^GSPC, ^DJI, ^IXIC
- Futures: GC=F (gold), SI=F (silver), NG=F (natural gas)
- ETFs: SPY, QQQ, GLD, SLV
- Crypto: BTC-USD, ETH-USD
