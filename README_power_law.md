# Power Law Fitting for Trading Pairs

Exponential/power law model for trading pair analysis.

## Mathematical Model

For a trading pair ratio R(t) = Asset1(t) / Asset2(t):

**Model:** `R(t) = R(0) · exp(μ·t)`

In log space: `log(R(t)) = log(R(0)) + μ·t`

This is a simple exponential fit (straight line in log space), not a stochastic process.

## Usage

Generate fits for all pairs:
```bash
pixi run python fit_power_law.py
```

View on Market Pairs page - orange dashed line shows exponential trend with parallel ±1σ bands.

## Interpretation

- **μ > 0**: Exponential growth
- **μ < 0**: Exponential decline  
- **High R²**: Good exponential fit
- **Narrow bands**: Low volatility

## Examples

- BTC/USD: μ = +55.58%/yr, R² = 0.880
- Gold/USD: μ = +8.31%/yr, R² = 0.840
- SP500/NASDAQ: μ = -1.95%/yr, R² = 0.822

See full documentation in comments of fit_power_law.py
