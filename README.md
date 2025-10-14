# QuantNetX

Financial analytics platform for cryptocurrency risk analysis and options pricing.

## Project Structure

```
quantnetx/
├── data/                # Bitcoin price data and analysis results
├── scripts/             # Python analysis scripts
├── static/              # Web interface (HTML, CSS, images)
├── pixi.toml           # Python dependencies
└── README.md
```

## Quick Start

### Installation

```bash
# Install dependencies
pixi install
```

### Usage

**View the web interface:**
```bash
# Serve locally (recommended)
python -m http.server 8000

# Then open:
# http://localhost:8000/static/index.html        # Options analysis
# http://localhost:8000/static/bitcoin_risk.html # Bitcoin risk metrics
```

**Update Bitcoin data:**
```bash
./scripts/refresh_charts.sh
```

Or run individually:
```bash
pixi run python scripts/update_bitcoin_data.py      # Fetch latest prices
pixi run python scripts/bitcoin_risk_regression.py  # Regenerate analysis
```

## Features

- **Bitcoin Risk Metric** - Logarithmic regression with 6 risk bands, 2-year projections
- **Options Analysis** - Implied probability distributions from Deribit options (BTC/ETH)
- **Live Data** - Auto-updates from Binance and Deribit APIs
- **Interactive Charts** - Plotly.js visualizations with risk color-coding

## Technical Details

**Bitcoin Risk Model:**
- Formula: `log(P(t)) = a·log(t - t₀) + b` where t₀ = 1.2625632×10⁹
- Based on [roman-ellerbrock/bitcoin_risk](https://github.com/roman-ellerbrock/bitcoin_risk)

**Options Analysis:**
- Breeden-Litzenberger formula (second derivative of option prices)
- Methods: Finite differences, cubic spline interpolation

## Data Sources

- Bitcoin Prices: [Binance API](https://api.binance.com)
- Options Data: [Deribit API](https://www.deribit.com/api/v2/)

## Dependencies

- Python ≥3.9
- numpy, pandas, scipy, requests
- Managed via [Pixi](https://prefix.dev/docs/pixi/overview)

## License

MIT License - see [LICENSE](LICENSE)

---

**Built for quantitative crypto analysis**
