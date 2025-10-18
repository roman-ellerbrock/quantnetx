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

SYMBOLS = ['btc', 'sp500', 'nasdaq', 'vti', 'eem', 'gold', 'silver', 'palladium', 'copper', 'oil', 'tlt', 'cpi']
SYMBOL_NAMES = {
    'btc': 'Bitcoin',
    'sp500': 'S&P 500',
    'nasdaq': 'NASDAQ',
    'vti': 'VTI',
    'eem': 'EEM',
    'gold': 'Gold',
    'silver': 'Silver',
    'palladium': 'Palladium',
    'copper': 'Copper',
    'oil': 'Oil',
    'tlt': 'TLT',
    'cpi': 'CPI',
    'usd': 'USD'
}

def load_csv_data(symbol):
    """Load market data from merged CSV file."""
    if symbol == 'usd':
        return None  # USD is constant

    # Special handling for CPI data
    if symbol == 'cpi':
        filepath = os.path.join(DATA_DIR, 'cpi_fred.csv')

        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            return None

        dates = []
        close_prices = []

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # CPI CSV has columns: observation_date, CPILFESL
                    if row['CPILFESL'] and row['CPILFESL'].strip():
                        dates.append(row['observation_date'])
                        close_prices.append(float(row['CPILFESL']))
                except (ValueError, KeyError):
                    continue  # Skip rows with missing/invalid data

        if len(dates) == 0:
            print(f"Warning: No valid data in {filepath}")
            return None

        return {
            'dates': dates,
            'close': np.array(close_prices)
        }

    # Use merged file (combines all timeframes)
    filepath = os.path.join(DATA_DIR, f'{symbol}.csv')

    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found")
        return None

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

    if len(dates) == 0:
        print(f"Warning: No valid data in {filepath}")
        return None

    return {
        'dates': dates,
        'close': np.array(close_prices)
    }

def align_data(data1, data2):
    """Align two datasets by common dates or months."""
    if data1 is None:  # USD case
        return None, data2['close'], data2['dates']
    if data2 is None:  # USD case
        return data1['close'], None, data1['dates']

    # Create date to index mapping
    date_to_idx1 = {date: i for i, date in enumerate(data1['dates'])}
    date_to_idx2 = {date: i for i, date in enumerate(data2['dates'])}

    # Try exact date matching first
    common_dates = sorted(set(data1['dates']) & set(data2['dates']))

    # If we have enough common dates, use exact matching
    if len(common_dates) >= 100:
        aligned1 = np.array([data1['close'][date_to_idx1[d]] for d in common_dates])
        aligned2 = np.array([data2['close'][date_to_idx2[d]] for d in common_dates])
        return aligned1, aligned2, common_dates

    # Otherwise, try month-based alignment (for CPI and other monthly data)
    # Group data by year-month
    def get_year_month(date_str):
        """Extract year-month from date string."""
        return date_str[:7]  # 'YYYY-MM'

    # Create month to index mapping (use last available data point in each month)
    month_to_idx1 = {}
    for i, date in enumerate(data1['dates']):
        ym = get_year_month(date)
        month_to_idx1[ym] = i  # Overwrites with later dates in same month

    month_to_idx2 = {}
    for i, date in enumerate(data2['dates']):
        ym = get_year_month(date)
        month_to_idx2[ym] = i

    # Find common months
    common_months = sorted(set(month_to_idx1.keys()) & set(month_to_idx2.keys()))

    if len(common_months) < 100:
        # Still insufficient data
        aligned1 = np.array([data1['close'][date_to_idx1[d]] for d in common_dates])
        aligned2 = np.array([data2['close'][date_to_idx2[d]] for d in common_dates])
        return aligned1, aligned2, common_dates

    # Align by month
    aligned1 = np.array([data1['close'][month_to_idx1[m]] for m in common_months])
    aligned2 = np.array([data2['close'][month_to_idx2[m]] for m in common_months])
    aligned_dates = [data1['dates'][month_to_idx1[m]] for m in common_months]

    return aligned1, aligned2, aligned_dates

def fit_power_law(ratio_data, dates):
    """
    Fit a power law (exponential) to ratio data with frequency-based weighting.

    Weights are calculated based on the time interval each point represents:
    - Points with daily spacing get lower weight per point
    - Points with weekly/monthly spacing get higher weight per point
    This ensures that all time periods contribute equally to the fit.

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

    # Calculate weights based on time gaps between points
    # Each point's weight is proportional to the time interval it represents
    weights = np.zeros(len(time_years))

    for i in range(len(time_years)):
        if i == 0:
            # First point: use half the gap to next point
            dt = time_years[1] - time_years[0] if len(time_years) > 1 else 1.0
            weights[i] = dt / 2
        elif i == len(time_years) - 1:
            # Last point: use half the gap from previous point
            dt = time_years[i] - time_years[i-1]
            weights[i] = dt / 2
        else:
            # Middle points: use average of gaps on both sides
            dt_before = time_years[i] - time_years[i-1]
            dt_after = time_years[i+1] - time_years[i]
            weights[i] = (dt_before + dt_after) / 2

    # Normalize weights so they sum to the number of points
    # This keeps the effective sample size similar to unweighted regression
    weights = weights * len(weights) / np.sum(weights)

    # Take log of ratio data
    log_ratio = np.log(ratio_data)

    # Perform weighted linear regression: log(R) = a + b*t
    # where b = μ (drift) and a = log(R(0))
    # Using numpy for weighted least squares
    W = np.diag(weights)
    X = np.column_stack([np.ones(len(time_years)), time_years])

    # Weighted least squares: (X^T W X)^-1 X^T W y
    XtWX = X.T @ W @ X
    XtWy = X.T @ W @ log_ratio
    params = np.linalg.solve(XtWX, XtWy)

    intercept = params[0]
    slope = params[1]

    # Calculate fitted values and residuals
    fitted_log_ratio = intercept + slope * time_years
    residuals = log_ratio - fitted_log_ratio

    # Calculate weighted standard deviation of residuals
    weighted_residual_var = np.sum(weights * residuals**2) / np.sum(weights)
    residual_std = np.sqrt(weighted_residual_var)

    # Calculate R-squared for weighted regression
    ss_res = np.sum(weights * residuals**2)
    weighted_mean = np.sum(weights * log_ratio) / np.sum(weights)
    ss_tot = np.sum(weights * (log_ratio - weighted_mean)**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # The residual_std is the volatility (standard deviation around trend)
    sigma = residual_std

    # Growth rate is already annualized from regression
    mu = slope

    return {
        'mu': float(mu),
        'sigma': float(sigma),
        'residual_std': float(residual_std),  # Standard deviation in log space
        'r_squared': float(r_squared),
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
            print(f"  ✓ Loaded {symbol}: {len(data['dates'])} points ({data['dates'][0]} to {data['dates'][-1]})")

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

    interesting_pairs = ['btc/usd', 'gold/usd', 'btc/gold', 'sp500/nasdaq', 'gold/copper', 'sp500/cpi', 'gold/cpi', 'btc/cpi']

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
