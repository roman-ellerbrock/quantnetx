import numpy as np
import pandas as pd
import json

# Fixed t0 value from the bitcoin_risk package
FIRST_BTC = 1.2625632e+09  # BTC start time in unix time
DELTA = 1e7  # Time delta added to make values more numerically stable

def _unix_to_btc_time(date):
    """
    Transform unix time to Bitcoin time using the same method as bitcoin_risk package.
    bitcoin_time = (unix_time - FIRST_BTC) + DELTA
    """
    return date - FIRST_BTC + DELTA

def log_regression_model(btc_time, a, b):
    """
    Logarithmic regression model: log(P(t)) = a*log(btc_time) + b
    Which means: P(t) = exp(a*log(btc_time) + b) = exp(b) * btc_time^a

    Note: btc_time is already transformed via _unix_to_btc_time
    """
    return np.exp(b) * np.power(btc_time, a)

def load_bitcoin_data(csv_path):
    """Load Bitcoin data from CSV file and transform to bitcoin time"""
    df = pd.read_csv(csv_path)
    # Convert unix time to bitcoin time
    times_unix = df['time'].values
    times_btc = _unix_to_btc_time(times_unix)
    # Use open prices
    prices = df['open'].values
    return times_btc, prices, times_unix

def perform_log_regression(btc_times, prices, label=""):
    """
    Perform logarithmic regression on Bitcoin price data
    Returns fitted parameters and model predictions

    Note: btc_times should already be transformed via _unix_to_btc_time
    """
    # Transform to log space for linear regression
    log_btc_time = np.log(btc_times)
    log_prices = np.log(prices)

    # Perform linear regression in log space
    # log(P) = a*log(btc_time) + b
    coeffs = np.polyfit(log_btc_time, log_prices, 1)
    a = coeffs[0]
    b = coeffs[1]

    if label:
        print(f"\n{label} Fitted parameters:")
    else:
        print(f"\nFitted parameters:")
    print(f"  a = {a:.6f}")
    print(f"  b = {b:.6f}")
    print(f"  Number of points: {len(btc_times)}")

    return a, b

# def calculate_risk_bands(times, a, b, std_devs=[1, 2, 3]):
#     """
#     Calculate risk bands based on the regression model
#     """
#     # Calculate fitted values
#     fitted_prices = log_regression_model(times, a, b)

#     # For risk bands, we'll use multiplicative factors
#     # In log space, we add/subtract standard deviations
#     # This is a simplified approach - the actual implementation may vary
#     bands = {}
#     bands['fitted'] = fitted_prices.tolist()

#     # Calculate residuals in log space for std calculation
#     # This is a placeholder - proper implementation would calculate
#     # std from actual residuals
#     log_std = 0.5  # This should be calculated from residuals

#     for n in std_devs:
#         upper = fitted_prices * np.exp(n * log_std)
#         lower = fitted_prices * np.exp(-n * log_std)
#         bands[f'upper_{n}sigma'] = upper.tolist()
#         bands[f'lower_{n}sigma'] = lower.tolist()

#     return bands

def main():
    # Load data
    csv_path = 'BTCUSD_1W.csv'
    times_btc, prices, times_unix = load_bitcoin_data(csv_path)

    print(f"Loaded {len(times_btc)} data points")
    print(f"Unix time range: {times_unix[0]} to {times_unix[-1]}")
    print(f"BTC time range: {times_btc[0]:.0f} to {times_btc[-1]:.0f}")
    print(f"Price range: ${prices.min():.2f} to ${prices.max():.2f}")

    # Filter data (only positive prices and positive btc_time)
    valid_mask = (times_btc > 3*DELTA) & (prices > 0)
    times_btc_filtered = times_btc[valid_mask]
    times_unix_filtered = times_unix[valid_mask]
    prices_filtered = prices[valid_mask]

    print(f"\nFiltered to {len(times_btc_filtered)} valid points")

    # ========================================================================
    # First regression: Mean price (using all data)
    # ========================================================================
    print("\n" + "="*70)
    print("FIRST FIT: Mean Price (all data)")
    print("="*70)
    a_mean, b_mean = perform_log_regression(times_btc_filtered, prices_filtered, "Mean Price")

    # Calculate fitted values for mean price
    fitted_mean = log_regression_model(times_btc_filtered, a_mean, b_mean)

    # ========================================================================
    # Second regression: Overvalued price (points above mean)
    # ========================================================================
    print("\n" + "="*70)
    print("SECOND FIT: Average Overvalued Price (points above mean)")
    print("="*70)

    # Select points above the mean fitted line
    overvalued_mask = prices_filtered > fitted_mean
    times_btc_overvalued = times_btc_filtered[overvalued_mask]
    prices_overvalued = prices_filtered[overvalued_mask]

    print(f"Selected {len(times_btc_overvalued)} overvalued points")

    if len(times_btc_overvalued) > 10:  # Need sufficient points for regression
        a_over, b_over = perform_log_regression(times_btc_overvalued, prices_overvalued, "Overvalued")
        fitted_overvalued = log_regression_model(times_btc_filtered, a_over, b_over)
    else:
        print("Warning: Not enough overvalued points for regression")
        a_over, b_over = a_mean, b_mean
        fitted_overvalued = fitted_mean

    # ========================================================================
    # Third regression: Undervalued price (points below mean)
    # ========================================================================
    print("\n" + "="*70)
    print("THIRD FIT: Average Undervalued Price (points below mean)")
    print("="*70)

    # Select points below the mean fitted line
    undervalued_mask = prices_filtered <= fitted_mean
    times_btc_undervalued = times_btc_filtered[undervalued_mask]
    prices_undervalued = prices_filtered[undervalued_mask]

    print(f"Selected {len(times_btc_undervalued)} undervalued points")

    if len(times_btc_undervalued) > 10:  # Need sufficient points for regression
        a_under, b_under = perform_log_regression(times_btc_undervalued, prices_undervalued, "Undervalued")
        fitted_undervalued = log_regression_model(times_btc_filtered, a_under, b_under)
    else:
        print("Warning: Not enough undervalued points for regression")
        a_under, b_under = a_mean, b_mean
        fitted_undervalued = fitted_mean

    # ========================================================================
    # Fourth regression: Extreme overvalued (points above overvalued)
    # ========================================================================
    print("\n" + "="*70)
    print("FOURTH FIT: Extreme Overvalued Price (points above overvalued)")
    print("="*70)

    # Select points above the overvalued fitted line
    extreme_over_mask = prices_filtered > fitted_overvalued
    times_btc_extreme_over = times_btc_filtered[extreme_over_mask]
    prices_extreme_over = prices_filtered[extreme_over_mask]

    print(f"Selected {len(times_btc_extreme_over)} extreme overvalued points")

    if len(times_btc_extreme_over) > 10:  # Need sufficient points for regression
        a_extreme_over, b_extreme_over = perform_log_regression(times_btc_extreme_over, prices_extreme_over, "Extreme Overvalued")
        fitted_extreme_over = log_regression_model(times_btc_filtered, a_extreme_over, b_extreme_over)
    else:
        print("Warning: Not enough extreme overvalued points for regression")
        a_extreme_over, b_extreme_over = a_over, b_over
        fitted_extreme_over = fitted_overvalued

    # ========================================================================
    # Fifth regression: Extreme undervalued (points below undervalued)
    # ========================================================================
    print("\n" + "="*70)
    print("FIFTH FIT: Extreme Undervalued Price (points below undervalued)")
    print("="*70)

    # Select points below the undervalued fitted line
    extreme_under_mask = prices_filtered <= fitted_undervalued
    times_btc_extreme_under = times_btc_filtered[extreme_under_mask]
    prices_extreme_under = prices_filtered[extreme_under_mask]

    print(f"Selected {len(times_btc_extreme_under)} extreme undervalued points")

    if len(times_btc_extreme_under) > 10:  # Need sufficient points for regression
        a_extreme_under, b_extreme_under = perform_log_regression(times_btc_extreme_under, prices_extreme_under, "Extreme Undervalued")
        fitted_extreme_under = log_regression_model(times_btc_filtered, a_extreme_under, b_extreme_under)
    else:
        print("Warning: Not enough extreme undervalued points for regression")
        a_extreme_under, b_extreme_under = a_under, b_under
        fitted_extreme_under = fitted_undervalued

    # ========================================================================
    # Sixth regression: Top (points above extreme overvalued / bubble)
    # ========================================================================
    print("\n" + "="*70)
    print("SIXTH FIT: Top Price (points above extreme overvalued)")
    print("="*70)

    # Select points above the extreme overvalued fitted line
    top_mask = prices_filtered > fitted_extreme_over
    times_btc_top = times_btc_filtered[top_mask]
    prices_top = prices_filtered[top_mask]

    print(f"Selected {len(times_btc_top)} top points")

    if len(times_btc_top) > 10:  # Need sufficient points for regression
        a_top, b_top = perform_log_regression(times_btc_top, prices_top, "Top")
        fitted_top = log_regression_model(times_btc_filtered, a_top, b_top)
    else:
        print("Warning: Not enough top points for regression")
        a_top, b_top = a_extreme_over, b_extreme_over
        fitted_top = fitted_extreme_over

    # ========================================================================
    # Calculate statistics and risk metrics
    # ========================================================================
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    # Calculate residuals in log space for mean fit
    log_residuals = np.log(prices_filtered) - np.log(fitted_mean)
    log_std = np.std(log_residuals)

    print(f"\nLog-space standard deviation (from mean): {log_std:.6f}")

    # Calculate risk metric (distance from mean regression in standard deviations)
    current_price = prices_filtered[-1]
    current_fitted_mean = fitted_mean[-1]
    current_fitted_over = fitted_overvalued[-1]
    current_fitted_under = fitted_undervalued[-1]
    current_fitted_extreme_over = fitted_extreme_over[-1]
    current_fitted_extreme_under = fitted_extreme_under[-1]
    current_fitted_top = fitted_top[-1]
    risk_metric_sigma = (np.log(current_price) - np.log(current_fitted_mean)) / log_std

    # Compute normalized risk metric using UNDERVALUED and TOP (matching bitcoin_risk package)
    # risk = (log(price) - log(undervalued)) / (log(top) - log(undervalued))
    v0 = np.log(fitted_undervalued)
    v1 = np.log(fitted_top)
    risk_normalized = (np.log(prices_filtered) - v0) / (v1 - v0)

    # Current normalized risk
    current_risk_normalized = risk_normalized[-1]

    print(f"\nCurrent Analysis:")
    print(f"  Current Price:                   ${current_price:.2f}")
    print(f"  Mean Fitted Price:               ${current_fitted_mean:.2f}")
    print(f"  Overvalued Fitted Price:         ${current_fitted_over:.2f}")
    print(f"  Undervalued Fitted Price:        ${current_fitted_under:.2f}")
    print(f"  Extreme Overvalued Price:        ${current_fitted_extreme_over:.2f}")
    print(f"  Extreme Undervalued Price:       ${current_fitted_extreme_under:.2f}")
    print(f"  Top Price:                       ${current_fitted_top:.2f}")
    print(f"  Risk Metric (sigma):             {risk_metric_sigma:.2f} σ")
    print(f"  Risk Metric (normalized):        {current_risk_normalized:.2f}")
    print(f"    (0=undervalued, 1=top - matching bitcoin_risk package)")

    # ========================================================================
    # Generate extended time range for plotting (2 years into future)
    # ========================================================================
    print("\n" + "="*70)
    print("GENERATING EXTENDED PLOT DATA")
    print("="*70)

    # Calculate future time range (2 years = 104 weeks for weekly data)
    last_unix_time = times_unix[-1]
    two_years_seconds = 2 * 365.25 * 24 * 3600
    future_unix_time = last_unix_time + two_years_seconds

    # Start from 2010-01-01 (unix timestamp: 1262304000)
    start_unix_time = 1262304000  # 2010-01-01 00:00:00 UTC

    # Create extended time array from 2010 to 2 years ahead
    # Using weekly intervals (604800 seconds = 1 week)
    week_seconds = 7 * 24 * 3600
    num_future_weeks = int((future_unix_time - start_unix_time) / week_seconds) + 1
    extended_unix_times = np.linspace(start_unix_time, future_unix_time, num_future_weeks)
    extended_btc_times = _unix_to_btc_time(extended_unix_times)

    print(f"Extended time range:")
    print(f"  Start: {start_unix_time} (unix, 2010-01-01)")
    print(f"  End:   {future_unix_time:.0f} (unix, +2 years)")
    print(f"  Total points for plotting: {len(extended_unix_times)}")

    # Generate fitted curves for extended time range
    extended_fitted_mean = log_regression_model(extended_btc_times, a_mean, b_mean)
    extended_fitted_over = log_regression_model(extended_btc_times, a_over, b_over)
    extended_fitted_under = log_regression_model(extended_btc_times, a_under, b_under)
    extended_fitted_extreme_over = log_regression_model(extended_btc_times, a_extreme_over, b_extreme_over)
    extended_fitted_extreme_under = log_regression_model(extended_btc_times, a_extreme_under, b_extreme_under)
    extended_fitted_top = log_regression_model(extended_btc_times, a_top, b_top)

    # For actual prices, we need to pad with NaN for future values
    extended_prices = np.full(len(extended_unix_times), np.nan)
    # Find where actual data points match in the extended array
    for i, t in enumerate(times_unix):
        idx = np.argmin(np.abs(extended_unix_times - t))
        extended_prices[idx] = prices[i]

    # Calculate risk metric for the available data range
    v0_extended = np.log(extended_fitted_under)
    v1_extended = np.log(extended_fitted_top)

    # Risk only where we have actual prices
    extended_risk_normalized = np.full(len(extended_unix_times), np.nan)
    mask_with_prices = ~np.isnan(extended_prices)
    extended_risk_normalized[mask_with_prices] = (
        (np.log(extended_prices[mask_with_prices]) - v0_extended[mask_with_prices]) /
        (v1_extended[mask_with_prices] - v0_extended[mask_with_prices])
    )

    # ========================================================================
    # Save results to JSON for HTML visualization
    # ========================================================================
    results = {
        'parameters': {
            'mean': {
                'a': float(a_mean),
                'b': float(b_mean),
                'first_btc': float(FIRST_BTC),
                'delta': float(DELTA)
            },
            'overvalued': {
                'a': float(a_over),
                'b': float(b_over)
            },
            'undervalued': {
                'a': float(a_under),
                'b': float(b_under)
            },
            'extreme_overvalued': {
                'a': float(a_extreme_over),
                'b': float(b_extreme_over)
            },
            'extreme_undervalued': {
                'a': float(a_extreme_under),
                'b': float(b_extreme_under)
            },
            'top': {
                'a': float(a_top),
                'b': float(b_top)
            },
            'log_std': float(log_std)
        },
        'data': {
            # Extended data for plotting (includes 2 years future projection)
            'times': extended_unix_times.tolist(),
            'prices': extended_prices.tolist(),
            'fitted_mean': extended_fitted_mean.tolist(),
            'fitted_overvalued': extended_fitted_over.tolist(),
            'fitted_undervalued': extended_fitted_under.tolist(),
            'fitted_extreme_overvalued': extended_fitted_extreme_over.tolist(),
            'fitted_extreme_undervalued': extended_fitted_extreme_under.tolist(),
            'fitted_top': extended_fitted_top.tolist(),
            'risk_normalized': extended_risk_normalized.tolist(),
            # Keep sigma bands based on mean fit
            'upper_1sigma': (extended_fitted_mean * np.exp(log_std)).tolist(),
            'lower_1sigma': (extended_fitted_mean * np.exp(-log_std)).tolist(),
            'upper_2sigma': (extended_fitted_mean * np.exp(2 * log_std)).tolist(),
            'lower_2sigma': (extended_fitted_mean * np.exp(-2 * log_std)).tolist(),
            'upper_3sigma': (extended_fitted_mean * np.exp(3 * log_std)).tolist(),
            'lower_3sigma': (extended_fitted_mean * np.exp(-3 * log_std)).tolist(),
        },
        'current': {
            'price': float(current_price),
            'fitted_mean': float(current_fitted_mean),
            'fitted_overvalued': float(current_fitted_over),
            'fitted_undervalued': float(current_fitted_under),
            'fitted_extreme_overvalued': float(current_fitted_extreme_over),
            'fitted_extreme_undervalued': float(current_fitted_extreme_under),
            'fitted_top': float(current_fitted_top),
            'risk_metric_sigma': float(risk_metric_sigma),
            'risk_metric_normalized': float(current_risk_normalized),
            'time': int(times_unix_filtered[-1])
        }
    }

    # Convert NaN to None (null in JSON) before saving
    def convert_nan_to_none(obj):
        if isinstance(obj, dict):
            return {k: convert_nan_to_none(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_nan_to_none(item) for item in obj]
        elif isinstance(obj, float) and np.isnan(obj):
            return None
        else:
            return obj

    results_clean = convert_nan_to_none(results)

    with open('bitcoin_risk_data.json', 'w') as f:
        json.dump(results_clean, f, indent=2)

    print("\nResults saved to bitcoin_risk_data.json")

if __name__ == '__main__':
    main()
