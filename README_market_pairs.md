# Market Pairs Analysis

A new page for analyzing trading pairs and relative asset performance.

## Features

### Asset Selection
- **Dual Dropdown Menus**: Select numerator and denominator assets independently
- **Available Assets**:
  - Bitcoin (BTC)
  - S&P 500
  - NASDAQ
  - Gold
  - Copper
  - Oil (WTI)
  - TLT (20-Year Treasury Bond ETF)
  - USD (Cash - constant value of 1.0)

### Chart Options
- **Scale**: Linear or Logarithmic Y-axis
- **Normalize to 100**: Rebases the first data point to 100 for easier percentage comparison
- **Interactive Plotly Chart**: Hover tooltips, zoom, pan, and export functionality

### Statistics
- Current pair ratio value
- Total percentage change over the entire period
- Average, maximum, and minimum ratios
- Color-coded change indicator (green for gains, red for losses)

## Usage

### Starting the Local Server

The page requires a local web server to access CSV data files. You cannot simply open the HTML file in your browser due to browser security restrictions on local file access.

**Option 1: Using the provided script**
```bash
./start_server.sh
```

**Option 2: Manual Python server**
```bash
python3 -m http.server 8000
```

Then open your browser to:
- http://localhost:8000/static/market_pairs.html

### Example Trading Pairs

**Classic Comparisons:**
- `BTC/USD` - Bitcoin price in dollars
- `Gold/USD` - Gold price in dollars
- `Oil/USD` - Oil price in dollars

**Relative Value Pairs:**
- `BTC/Gold` - Bitcoin vs Gold (digital vs physical store of value)
- `Gold/Copper` - Gold-to-copper ratio (economic indicator)
- `SP500/NASDAQ` - Large-cap vs tech-heavy indices

**Commodities:**
- `Oil/Gold` - Energy vs precious metals
- `Copper/Gold` - Industrial vs safe-haven metals

**Risk Analysis:**
- `SP500/TLT` - Stocks vs long-term treasuries (risk-on vs risk-off)
- `NASDAQ/TLT` - Tech stocks vs treasuries

## Data Source

Market data is loaded from CSV files in `data/market_data/`:
- Daily OHLCV data
- Historical coverage varies by asset:
  - SP500/NASDAQ: Since 1970s
  - Commodities: Since 2000
  - Bitcoin: Since 2014
  - TLT: Since 2002

Data can be refreshed using the `fetch_market_data.py` script.

## Technical Details

### Data Alignment
- The page automatically aligns data by matching dates between two assets
- Only dates present in both datasets are included in the ratio calculation
- This handles different trading calendars (e.g., 24/7 crypto vs weekday-only stocks)

### Ratio Calculation
- **Standard**: `Ratio = Asset1 / Asset2`
- **Normalized**: `Normalized = (Ratio / FirstRatio) × 100`

### File Structure
```
static/market_pairs.html    - Main page
data/market_data/*.csv       - Market data files
start_server.sh              - Convenience script to launch server
```

## Troubleshooting

**Error: "Failed to load data"**
- Ensure you're accessing the page through a web server (http://localhost:8000), not directly as a file (file://)
- Check that CSV files exist in `data/market_data/`
- Run `fetch_market_data.py` if data files are missing

**Error: "No overlapping dates found"**
- This occurs when two assets have completely different date ranges
- Check the date coverage in the CSV files
- Some pairs may have limited overlap (e.g., BTC only goes back to 2014)

**Page shows but chart doesn't load**
- Check browser console for JavaScript errors
- Ensure Plotly CDN is accessible (requires internet connection)
- Try refreshing the page
