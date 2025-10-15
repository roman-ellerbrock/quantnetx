# Data Files

This directory contains data files used by QuantNetX.

## Files

### `BTCUSD_1W.csv`
Bitcoin weekly OHLC (Open, High, Low, Close) price data.

**Format:**
```csv
time,open,high,low,close
```

**Update frequency:** 4 times per day via GitHub Actions

### `bitcoin_risk_data.json`
Bitcoin risk analysis results including regression parameters and risk bands.

**Structure:**
```json
{
  "parameters": { ... },
  "data": { ... },
  "current": { ... }
}
```

**Update frequency:** 4 times per day via GitHub Actions

### `implied_probabilities.json`
Precomputed implied probability distributions from Deribit options data.

**Structure:**
```json
{
  "timestamp": "2025-10-15T20:13:12.460859+00:00",
  "method": "finite-diff",
  "currencies": {
    "BTC": {
      "16OCT25": {
        "call_probabilities": [
          {
            "strike": 106000.0,
            "probability": 0.0027,
            "iv": 75.87
          },
          ...
        ],
        "put_probabilities": [...],
        "underlying_price": 111448.27,
        "time_to_expiry": 0.0027,
        "expiry_date": "16OCT25",
        "timestamp": "2025-10-15T20:13:12.460859+00:00",
        "method": "finite-diff",
        "call_statistics": {
          "expected_price": 111569.47,
          "std_dev": 1234.56,
          "mode_strike": 112000.0,
          "prob_above_current": 0.52,
          "prob_below_current": 0.48
        },
        "put_statistics": {...}
      },
      ...
    },
    "ETH": {...}
  }
}
```

**Update frequency:** 4 times per day via GitHub Actions (00:00, 06:00, 12:00, 18:00 UTC)

**Coverage:** 3 nearest expiries for BTC and ETH

### `probability_surface.json`
2D probability surface data for contour/heatmap visualizations.

**Structure:**
```json
{
  "timestamp": "2025-10-15T22:06:31.804242+00:00",
  "method": "finite-diff",
  "surfaces": {
    "BTC": {
      "call_surface": {
        "grid": {
          "time_days": [0.41, 1.41, 2.41],
          "time_dates": ["2025-10-16T08:00:00+00:00", ...],
          "prices": [96150.0, 96561.11, ...],
          "probabilities": [[...], [...], ...]
        },
        "metadata": {
          "price_points": 100,
          "time_points": 3,
          "price_min": 98000.0,
          "price_max": 135000.0
        }
      },
      "put_surface": {...},
      "combined_surface": {...},
      "combined_statistics": {
        "statistics": [
          {
            "days_to_expiry": 0.41,
            "expiry_date": "2025-10-16T08:00:00+00:00",
            "expected_price": 111403.87,
            "std_dev": 1879.09,
            "quantiles": {
              "q05": 108483.33,
              "q50": 111000.00,
              "q95": 114238.89
            }
          }
        ]
      }
    }
  }
}
```

**Update frequency:** 4 times per day via GitHub Actions

**Grid format:** 2D array where `probabilities[price_index][time_index]` gives probability at that price/time

## Using Precomputed Probabilities

### Python Example - 1D Probabilities

```python
import json

# Load precomputed probabilities
with open('data/implied_probabilities.json', 'r') as f:
    data = json.load(f)

# Get BTC probabilities for first expiry
btc_expiries = list(data['currencies']['BTC'].keys())
first_expiry = btc_expiries[0]
btc_data = data['currencies']['BTC'][first_expiry]

# Access probability distributions
call_probs = btc_data['call_probabilities']
put_probs = btc_data['put_probabilities']

# Print statistics
print(f"Underlying: ${btc_data['underlying_price']:.2f}")
print(f"Expected (calls): ${btc_data['call_statistics']['expected_price']:.2f}")
print(f"Expected (puts): ${btc_data['put_statistics']['expected_price']:.2f}")

# Plot distribution
import matplotlib.pyplot as plt

strikes = [p['strike'] for p in call_probs]
probs = [p['probability'] for p in call_probs]

plt.plot(strikes, probs)
plt.xlabel('Strike Price')
plt.ylabel('Probability')
plt.title(f'Implied Probability Distribution - {first_expiry}')
plt.show()
```

### JavaScript Example

```javascript
// Fetch precomputed probabilities
fetch('data/implied_probabilities.json')
  .then(response => response.json())
  .then(data => {
    // Get BTC data
    const btcExpiries = Object.keys(data.currencies.BTC);
    const firstExpiry = btcExpiries[0];
    const btcData = data.currencies.BTC[firstExpiry];

    console.log(`Underlying: $${btcData.underlying_price}`);
    console.log(`Expected (calls): $${btcData.call_statistics.expected_price}`);

    // Use probabilities for visualization
    const strikes = btcData.call_probabilities.map(p => p.strike);
    const probs = btcData.call_probabilities.map(p => p.probability);

    // Plot with Plotly, Chart.js, etc.
  });
```

### Python Example - 2D Probability Surface

```python
import json
import numpy as np
import matplotlib.pyplot as plt

# Load probability surface
with open('data/probability_surface.json', 'r') as f:
    surface_data = json.load(f)

# Get BTC combined surface
btc_surface = surface_data['surfaces']['BTC']['combined_surface']

# Extract grid data
time_days = np.array(btc_surface['grid']['time_days'])
time_dates = btc_surface['grid']['time_dates']
prices = np.array(btc_surface['grid']['prices'])
probabilities = np.array(btc_surface['grid']['probabilities'])

# Create contour plot
plt.figure(figsize=(12, 8))
plt.contourf(time_days, prices, probabilities, levels=20, cmap='viridis')
plt.colorbar(label='Probability Density')
plt.xlabel('Days to Expiry')
plt.ylabel('Price (USD)')
plt.title('BTC Implied Probability Surface')

# Add contour lines
plt.contour(time_days, prices, probabilities, levels=10, colors='white', alpha=0.3, linewidths=0.5)

# Mark current price
current_price = btc_surface['current_price']
plt.axhline(current_price, color='red', linestyle='--', label=f'Current: ${current_price:.0f}')

plt.legend()
plt.tight_layout()
plt.show()

# Print statistics for each expiry
stats = surface_data['surfaces']['BTC']['combined_statistics']['statistics']
for stat in stats:
    print(f"\nExpiry: {stat['expiry_date']}")
    print(f"  Days: {stat['days_to_expiry']:.1f}")
    print(f"  Expected: ${stat['expected_price']:.2f}")
    print(f"  Std Dev: ${stat['std_dev']:.2f}")
    print(f"  95% Range: ${stat['quantiles']['q05']:.2f} - ${stat['quantiles']['q95']:.2f}")
```

### JavaScript Example - 2D Surface

```javascript
// Fetch probability surface
fetch('data/probability_surface.json')
  .then(response => response.json())
  .then(data => {
    const btcSurface = data.surfaces.BTC.combined_surface;

    // Extract grid data
    const timeDays = btcSurface.grid.time_days;
    const timeDates = btcSurface.grid.time_dates;
    const prices = btcSurface.grid.prices;
    const probs = btcSurface.grid.probabilities;

    // Create heatmap with Plotly
    const heatmapData = [{
      z: probs,
      x: timeDays,
      y: prices,
      type: 'contour',
      colorscale: 'Viridis',
      colorbar: { title: 'Probability' }
    }];

    const layout = {
      title: 'BTC Implied Probability Surface',
      xaxis: { title: 'Days to Expiry' },
      yaxis: { title: 'Price (USD)' }
    };

    Plotly.newPlot('chart', heatmapData, layout);
  });
```

## Update Schedule

All data files are automatically updated 4 times per day:
- 00:00 UTC
- 06:00 UTC
- 12:00 UTC
- 18:00 UTC

Updates can also be triggered manually via GitHub Actions workflow dispatch.

## Manual Update

To manually update all data files:

```bash
# Update Bitcoin price data
pixi run python scripts/update_bitcoin_data.py

# Regenerate risk analysis
pixi run python scripts/bitcoin_risk_regression.py

# Precompute implied probabilities
pixi run python scripts/precompute_implied_probabilities.py

# Generate probability surface
pixi run python scripts/generate_probability_surface.py
```

Or use the convenience script:

```bash
./scripts/refresh_charts.sh
```
