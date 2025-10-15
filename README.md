# QuantNetX

Financial analytics platform for cryptocurrency risk analysis and options pricing.

🌐 **Live Demo:** [https://roman-ellerbrock.github.io/quantnetx/](https://roman-ellerbrock.github.io/quantnetx/)

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

### View Online

Visit [https://roman-ellerbrock.github.io/quantnetx/](https://roman-ellerbrock.github.io/quantnetx/)

- **Options Analysis:** [/static/index.html](https://roman-ellerbrock.github.io/quantnetx/static/index.html)
- **Bitcoin Risk Metric:** [/static/bitcoin_risk.html](https://roman-ellerbrock.github.io/quantnetx/static/bitcoin_risk.html)

### Local Development

```bash
# Install dependencies
pixi install

# Serve locally
python -m http.server 8000

# Then open:
# http://localhost:8000/static/index.html
# http://localhost:8000/static/bitcoin_risk.html
```

### Update Bitcoin Data

```bash
./scripts/refresh_charts.sh
```

Or run individually:
```bash
pixi run python scripts/update_bitcoin_data.py               # Fetch latest prices
pixi run python scripts/bitcoin_risk_regression.py           # Regenerate analysis
pixi run python scripts/precompute_implied_probabilities.py  # Precompute options probabilities
pixi run python scripts/generate_probability_surface.py      # Generate 2D probability surface
```

## Features

- **Bitcoin Risk Metric** - Logarithmic regression with 6 risk bands, 2-year projections
- **Options Analysis** - Implied probability distributions from Deribit options (BTC/ETH)
- **2D Probability Surface** - Time x Price contour data for probability heatmaps
- **Live Data** - Auto-updates from Binance and Deribit APIs (4x daily)
- **Precomputed Data** - Cached probability data for fast access
- **Interactive Charts** - Plotly.js visualizations with risk color-coding

## Technical Details

**Bitcoin Risk Model:**
- Formula: `log(P(t)) = a·log(t - t₀) + b` where t₀ = 1.2625632×10⁹
- Based on [roman-ellerbrock/bitcoin_risk](https://github.com/roman-ellerbrock/bitcoin_risk)

**Options Analysis:**
- Breeden-Litzenberger formula (second derivative of option prices)
- Methods: Finite differences, cubic spline interpolation
- Precomputed probabilities: `data/implied_probabilities.json`
- 2D probability surface: `data/probability_surface.json` (Time x Price grid)
- Updated 4x daily via GitHub Actions (00:00, 06:00, 12:00, 18:00 UTC)

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
