#!/usr/bin/env python3
"""
Fit Power Law (Exponential) to trading pairs.

For a trading pair ratio R(t), we model it as a power law:
R(t) = R(0) * exp(μ*t)

In log space:
log(R(t)) = log(R(0)) + μ*t

Where:
- μ = exponential growth rate (annualized)
- R(0) = initial ratio value
- t = time in years

This is a simple exponential/power law fit with linear regression in log space.
"""

import os
import csv
import json
import numpy as np
from datetime import datetime
from scipy import stats

# Market data directory
DATA_DIR = 'data/market_data'
OUTPUT_FILE = 'data/power_law_fits.json'

SYMBOLS = ['btc', 'sp500', 'nasdaq', 'gold', 'copper', 'oil', 'tlt']
SYMBOL_NAMES = {
    'btc': 'Bitcoin',
    'sp500': 'S&P 500',
    'nasdaq': 'NASDAQ',
    'gold': 'Gold',
    'copper': 'Copper',
    'oil': 'Oil',
    'tlt': 'TLT',
    'usd': 'USD'
}

def load_csv_data(symbol):
    """Load market data from CSV file. Try monthly first (longer history), then weekly."""
    if symbol == 'usd':
        return None  # USD is constant

    # Try monthly data first (longer history), then fall back to weekly
    intervals = ['1mo', '1wk', '1d']

    for interval in intervals:
        filepath = os.path.join(DATA_DIR, f'{symbol}_{interval}.csv')

        if not os.path.exists(filepath):
            continue

        dates = []
        close_prices = []

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    if row['close'] and row['close'].strip():
                        dates.append(row['date'])
                        close_prices.append(float(row['close']))
                except (ValueError, KeyError):
                    continue  # Skip rows with missing/invalid data

        if len(dates) > 0:
            return {
                'dates': dates,
                'close': np.array(close_prices),
                'interval': interval
            }

    print(f"Warning: No data found for {symbol}")
    return None

def align_data(data1, data2):
    """Align two datasets by common dates."""
    if data1 is None:  # USD case
        return None, data2['close'], data2['dates']
    if data2 is None:  # USD case
        return data1['close'], None, data1['dates']

    # Create date to index mapping
    date_to_idx1 = {date: i for i, date in enumerate(data1['dates'])}
    date_to_idx2 = {date: i for i, date in enumerate(data2['dates'])}

    # Find common dates
    common_dates = sorted(set(data1['dates']) & set(data2['dates']))

    aligned1 = np.array([data1['close'][date_to_idx1[d]] for d in common_dates])
    aligned2 = np.array([data2['close'][date_to_idx2[d]] for d in common_dates])

    return aligned1, aligned2, common_dates

def fit_power_law(ratio_data, dates):
    """
    Fit a power law (exponential) to ratio data.

    Returns:
        dict with:
        - mu: exponential growth rate (annualized)
        - sigma: annualized volatility estimate
        - residual_std: standard deviation of residuals in log space
        - r_squared: goodness of fit
        - initial_value: R(0)
    """
    # Filter out non-positive ratios (can't take log of negative or zero)
    valid_mask = ratio_data > 0
    if np.sum(valid_mask) < 100:  # Need minimum valid points
        raise ValueError("Insufficient positive data points for log transformation")

    ratio_data = ratio_data[valid_mask]
    dates = [d for d, valid in zip(dates, valid_mask) if valid]

    # Convert dates to time in years from start
    start_date = datetime.strptime(dates[0], '%Y-%m-%d')
    time_years = np.array([
        (datetime.strptime(d, '%Y-%m-%d') - start_date).days / 365.25
        for d in dates
    ])

    # Take log of ratio data
    log_ratio = np.log(ratio_data)

    # Fit linear regression: log(R) = a + b*t
    # where b = μ (drift) and a = log(R(0))
    slope, intercept, r_value, p_value, std_err = stats.linregress(time_years, log_ratio)

    # Calculate residuals for volatility estimation
    fitted_log_ratio = intercept + slope * time_years
    residuals = log_ratio - fitted_log_ratio

    # Calculate standard deviation of residuals (in log space)
    # This is the typical deviation from the fitted power law
    residual_std = np.std(residuals)

    # The residual_std is already the volatility we want
    # It's the standard deviation of log returns around the trend
    # No need to annualize since we're fitting against time in years
    sigma = residual_std

    # Growth rate is already annualized from regression
    mu = slope

    return {
        'mu': float(mu),
        'sigma': float(sigma),
        'residual_std': float(residual_std),  # Standard deviation in log space
        'r_squared': float(r_value ** 2),
        'initial_value': float(np.exp(intercept))
    }

def calculate_pair_ratio(data1, data2):
    """Calculate ratio of two aligned datasets."""
    if data1 is None:  # Numerator is USD
        return 1.0 / data2
    if data2 is None:  # Denominator is USD
        return data1
    return data1 / data2

def main():
    """Fit power law to all trading pairs."""
    print("=" * 70)
    print("Power Law Fitting for Trading Pairs")
    print("=" * 70)
    print()

    # Load all market data
    print("Loading market data...")
    market_data = {}
    for symbol in SYMBOLS:
        data = load_csv_data(symbol)
        if data is not None:
            market_data[symbol] = data
            interval = data.get('interval', '1d')
            print(f"  ✓ Loaded {symbol}: {len(data['dates'])} points ({interval})")

    print()

    # Fit all pairs
    all_fits = {}
    pair_count = 0

    print("Fitting power laws...")
    print()

    # All symbols including USD
    all_symbols = SYMBOLS + ['usd']

    for num_symbol in all_symbols:
        for denom_symbol in all_symbols:
            if num_symbol == denom_symbol:
                continue

            pair_name = f"{num_symbol}/{denom_symbol}"

            # Load data
            data1 = market_data.get(num_symbol)
            data2 = market_data.get(denom_symbol)

            # Align data
            aligned1, aligned2, common_dates = align_data(data1, data2)

            if aligned1 is None and aligned2 is None:
                continue

            if len(common_dates) < 100:  # Need minimum data points
                print(f"  ⚠ Skipping {pair_name}: insufficient data ({len(common_dates)} days)")
                continue

            # Calculate ratio
            ratio = calculate_pair_ratio(aligned1, aligned2)

            # Fit power law
            try:
                fit_result = fit_power_law(ratio, common_dates)

                # Store results
                all_fits[pair_name] = {
                    'numerator': num_symbol,
                    'denominator': denom_symbol,
                    'numerator_name': SYMBOL_NAMES[num_symbol],
                    'denominator_name': SYMBOL_NAMES[denom_symbol],
                    'data_points': len(common_dates),
                    'start_date': common_dates[0],
                    'end_date': common_dates[-1],
                    'drift_annual': fit_result['mu'],
                    'volatility_annual': fit_result['sigma'],
                    'residual_std': fit_result['residual_std'],
                    'r_squared': fit_result['r_squared'],
                    'initial_value': fit_result['initial_value']
                }

                pair_count += 1

                # Print summary
                print(f"  {pair_name:20s} | μ={fit_result['mu']:+.4f} | R²={fit_result['r_squared']:.3f} | n={len(common_dates)}")

            except Exception as e:
                print(f"  ✗ Error fitting {pair_name}: {e}")

    print()
    print("=" * 70)
    print(f"Successfully fit {pair_count} trading pairs")
    print("=" * 70)
    print()

    # Save results
    print(f"Saving results to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    output_data = {
        'metadata': {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_pairs': pair_count,
            'description': 'Power law (exponential) fits for trading pairs',
            'model': 'R(t) = R(0) * exp(μ*t), or log(R(t)) = log(R(0)) + μ*t',
            'units': {
                'growth_rate': 'annualized (per year)',
                'volatility': 'annualized (per year)',
                'time': 'years from start date'
            }
        },
        'fits': all_fits
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"✓ Saved {pair_count} fits to {OUTPUT_FILE}")
    print()

    # Print some interesting statistics
    print("Interesting Pairs:")
    print("-" * 70)

    interesting_pairs = ['btc/usd', 'gold/usd', 'btc/gold', 'sp500/nasdaq', 'gold/copper']

    for pair in interesting_pairs:
        if pair in all_fits:
            fit = all_fits[pair]
            print(f"\n{fit['numerator_name']}/{fit['denominator_name']}:")
            print(f"  Growth Rate (μ): {fit['drift_annual']:+.2%} per year")
            print(f"  Volatility (σ):  {fit['volatility_annual']:.2%} per year")
            print(f"  R²:              {fit['r_squared']:.3f}")
            print(f"  Data points:     {fit['data_points']} days")
            print(f"  Period:          {fit['start_date']} to {fit['end_date']}")

if __name__ == '__main__':
    main()
