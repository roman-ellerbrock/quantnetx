#!/usr/bin/env python3
"""
Precompute implied probability distributions from Deribit options data.
This script fetches options data from Deribit API and calculates implied
probabilities using the Breeden-Litzenberger formula (second derivative of option prices).

The computed probabilities are stored in JSON format for later use.
"""

import json
import requests
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
import time


# Deribit API configuration
DERIBIT_API_BASE = 'https://www.deribit.com/api/v2/public'

# Default currencies and methods
DEFAULT_CURRENCIES = ['BTC', 'ETH']
DEFAULT_METHOD = 'finite-diff'  # or 'cubic-spline'


def parse_expiry_to_timestamp(expiry_str: str) -> Optional[int]:
    """
    Parse expiry date string to timestamp.
    Format: DDMMMYY (e.g., "14OCT25")

    Returns:
        Unix timestamp in milliseconds, or None if parsing fails
    """
    try:
        day = int(expiry_str[0:2])
        month_str = expiry_str[2:5].upper()
        year = 2000 + int(expiry_str[5:7])

        months = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }

        month = months.get(month_str)
        if month is None:
            return None

        # Deribit options expire at 8:00 UTC
        dt = datetime(year, month, day, 8, 0, 0, tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)  # milliseconds
    except Exception as e:
        print(f"Error parsing expiry '{expiry_str}': {e}")
        return None


def fetch_available_expiries(currency: str = 'BTC') -> List[Dict]:
    """
    Fetch available expiry dates from Deribit.

    Args:
        currency: 'BTC' or 'ETH'

    Returns:
        List of dicts with 'expiry' (str) and 'timestamp' (int) keys
    """
    try:
        url = f"{DERIBIT_API_BASE}/get_book_summary_by_currency"
        params = {'currency': currency, 'kind': 'option'}

        print(f"Fetching available expiries for {currency}...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        instruments = data.get('result', [])

        # Extract unique expiry dates
        expiry_map = {}
        for instrument in instruments:
            # Parse instrument name: BTC-14OCT25-80000-C
            parts = instrument['instrument_name'].split('-')
            if len(parts) >= 4:
                expiry_str = parts[1]
                if expiry_str not in expiry_map:
                    timestamp = parse_expiry_to_timestamp(expiry_str)
                    if timestamp:
                        expiry_map[expiry_str] = timestamp

        # Sort by timestamp
        expiries = [
            {'expiry': expiry, 'timestamp': ts}
            for expiry, ts in expiry_map.items()
        ]
        expiries.sort(key=lambda x: x['timestamp'])

        print(f"Found {len(expiries)} expiries for {currency}")
        return expiries

    except Exception as e:
        print(f"Error fetching expiries for {currency}: {e}")
        return []


def fetch_option_chain_data(currency: str, expiry: str) -> List[Dict]:
    """
    Fetch option chain data from Deribit for a specific expiry.

    Args:
        currency: 'BTC' or 'ETH'
        expiry: Expiry date string (e.g., '14OCT25')

    Returns:
        List of option data dictionaries
    """
    try:
        url = f"{DERIBIT_API_BASE}/get_book_summary_by_currency"
        params = {'currency': currency, 'kind': 'option'}

        print(f"Fetching option chain for {currency}-{expiry}...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        instruments = data.get('result', [])

        # Filter by expiry
        filtered = [
            inst for inst in instruments
            if expiry in inst['instrument_name']
        ]

        # Transform to our format
        timestamp = datetime.now(timezone.utc).isoformat()
        options_data = []

        for inst in filtered:
            # Parse instrument name: BTC-14OCT25-80000-C
            parts = inst['instrument_name'].split('-')
            if len(parts) < 4:
                continue

            underlying = parts[0]
            expiry_date = parts[1]
            strike = float(parts[2])
            option_type = parts[3]

            options_data.append({
                'timestamp': timestamp,
                'instrument_name': inst['instrument_name'],
                'underlying': underlying,
                'expiry': expiry_date,
                'strike': strike,
                'option_type': option_type,
                'underlying_price': inst.get('underlying_price'),
                'underlying_index': inst.get('underlying_index'),
                'mark_price': inst.get('mark_price'),
                'mark_iv': inst.get('mark_iv'),
                'bid_price': inst.get('bid_price'),
                'ask_price': inst.get('ask_price'),
                'mid_price': inst.get('mid_price'),
                'last_price': inst.get('last'),
                'open_interest': inst.get('open_interest'),
                'volume': inst.get('volume'),
                'expiration_timestamp': parse_expiry_to_timestamp(expiry_date)
            })

        print(f"Fetched {len(options_data)} options for {currency}-{expiry}")
        return options_data

    except Exception as e:
        print(f"Error fetching option chain for {currency}-{expiry}: {e}")
        return []


def calculate_second_derivative_finite_diff(options: List[Dict]) -> List[Dict]:
    """
    Calculate second derivative using finite differences for non-uniformly spaced points.

    Args:
        options: List of option data (sorted by strike)

    Returns:
        List of dicts with 'strike', 'probability', 'iv' keys
    """
    probabilities = []

    for i in range(1, len(options) - 1):
        xa = options[i - 1]['strike']
        xb = options[i]['strike']
        xc = options[i + 1]['strike']

        fa = options[i - 1]['mark_price']
        fb = options[i]['mark_price']
        fc = options[i + 1]['mark_price']

        # Check for valid prices
        if fa is None or fb is None or fc is None:
            continue
        if fa <= 0 or fb <= 0 or fc <= 0:
            continue

        d1 = xb - xa
        d2 = xc - xb

        if d1 <= 0 or d2 <= 0:
            continue

        # Second derivative for non-uniformly spaced points
        second_deriv = 2 * (fa * d2 + fc * d1 - fb * (d1 + d2)) / (d1 * d2 * (d1 + d2))

        if second_deriv > 0:
            probabilities.append({
                'strike': xb,
                'probability': second_deriv,
                'iv': options[i]['mark_iv']
            })

    return probabilities


def cubic_spline(x: np.ndarray, y: np.ndarray) -> Dict:
    """
    Natural cubic spline implementation.

    Args:
        x: Strike prices (sorted)
        y: Option prices

    Returns:
        Dict with spline coefficients
    """
    n = len(x) - 1
    a = y.copy()
    b = np.zeros(n)
    c = np.zeros(n + 1)
    d = np.zeros(n)
    h = np.zeros(n)
    alpha = np.zeros(n)
    l = np.ones(n + 1)
    mu = np.zeros(n + 1)
    z = np.zeros(n + 1)

    # Calculate h values
    for i in range(n):
        h[i] = x[i + 1] - x[i]

    # Calculate alpha values
    for i in range(1, n):
        alpha[i] = (3 / h[i]) * (a[i + 1] - a[i]) - (3 / h[i - 1]) * (a[i] - a[i - 1])

    # Solve tridiagonal system
    for i in range(1, n):
        l[i] = 2 * (x[i + 1] - x[i - 1]) - h[i - 1] * mu[i - 1]
        mu[i] = h[i] / l[i]
        z[i] = (alpha[i] - h[i - 1] * z[i - 1]) / l[i]

    # Back substitution
    for j in range(n - 1, -1, -1):
        c[j] = z[j] - mu[j] * c[j + 1]
        b[j] = (a[j + 1] - a[j]) / h[j] - h[j] * (c[j + 1] + 2 * c[j]) / 3
        d[j] = (c[j + 1] - c[j]) / (3 * h[j])

    return {'a': a, 'b': b, 'c': c, 'd': d, 'x': x}


def eval_spline_second_derivative(spline: Dict, x_val: float) -> float:
    """
    Evaluate second derivative of cubic spline at a point.

    Args:
        spline: Spline coefficients from cubic_spline()
        x_val: Point to evaluate at

    Returns:
        Second derivative value
    """
    c = spline['c']
    d = spline['d']
    x = spline['x']

    # Find interval
    i = 0
    for i in range(len(x) - 1):
        if x_val <= x[i + 1]:
            break

    i = min(i, len(c) - 1)

    dx = x_val - x[i]
    return 2 * c[i] + 6 * d[i] * dx


def calculate_second_derivative_spline(options: List[Dict]) -> List[Dict]:
    """
    Calculate second derivative using cubic spline interpolation.

    Args:
        options: List of option data (sorted by strike)

    Returns:
        List of dicts with 'strike', 'probability', 'iv' keys
    """
    strikes = np.array([opt['strike'] for opt in options])
    prices = np.array([opt['mark_price'] for opt in options])

    # Create cubic spline
    spline = cubic_spline(strikes, prices)

    # Generate dense grid
    min_strike = strikes[0]
    max_strike = strikes[-1]
    num_points = max(100, len(strikes) * 10)
    strike_step = (max_strike - min_strike) / num_points

    probabilities = []
    k = min_strike
    while k <= max_strike - strike_step:
        second_deriv = eval_spline_second_derivative(spline, k)

        if second_deriv > 0:
            # Find closest option for IV
            closest_idx = np.argmin(np.abs(strikes - k))

            probabilities.append({
                'strike': float(k),
                'probability': float(second_deriv),
                'iv': options[closest_idx]['mark_iv']
            })

        k += strike_step

    return probabilities


def calculate_probabilities_from_options(options: List[Dict], method: str = 'finite-diff') -> List[Dict]:
    """
    Calculate implied probabilities from options using the specified method.

    Args:
        options: List of option data (sorted by strike)
        method: 'finite-diff' or 'cubic-spline'

    Returns:
        List of dicts with 'strike', 'probability', 'iv' keys (normalized)
    """
    if len(options) < 3:
        return []

    # Filter valid prices
    valid_options = [
        opt for opt in options
        if opt['mark_price'] is not None and opt['mark_price'] > 0
    ]

    if len(valid_options) < 3:
        return []

    # Sort by strike
    valid_options.sort(key=lambda x: x['strike'])

    # Calculate probabilities based on method
    if method == 'cubic-spline':
        probabilities = calculate_second_derivative_spline(valid_options)
    else:  # finite-diff
        probabilities = calculate_second_derivative_finite_diff(valid_options)

    if len(probabilities) == 0:
        return []

    # Normalize so total probability = 1
    total_prob = sum(p['probability'] for p in probabilities)
    if total_prob > 0:
        for p in probabilities:
            p['probability'] = p['probability'] / total_prob

    return probabilities


def calculate_implied_probability(options_data: List[Dict], method: str = 'finite-diff') -> Dict:
    """
    Calculate implied probability distribution from both calls and puts.

    Args:
        options_data: List of option data
        method: 'finite-diff' or 'cubic-spline'

    Returns:
        Dict with probability distributions and metadata
    """
    # Separate calls and puts
    calls = [opt for opt in options_data if opt['option_type'] == 'C']
    puts = [opt for opt in options_data if opt['option_type'] == 'P']

    if len(calls) < 3 and len(puts) < 3:
        raise ValueError('Insufficient data for probability calculation (need at least 3 call or put options)')

    # Get underlying price
    underlying_price = None
    for opt in options_data:
        if opt['underlying_price'] is not None:
            underlying_price = opt['underlying_price']
            break

    if underlying_price is None:
        raise ValueError('No underlying price available')

    # Get expiry information
    expiry_date = options_data[0]['expiry']
    expiration_timestamp = options_data[0]['expiration_timestamp']

    # Calculate time to expiry in years
    now = time.time() * 1000  # milliseconds
    time_to_expiry = (expiration_timestamp - now) / (1000 * 60 * 60 * 24 * 365)

    if time_to_expiry <= 0:
        raise ValueError('Options have expired')

    # Calculate probabilities
    call_probabilities = calculate_probabilities_from_options(calls, method) if len(calls) >= 3 else []
    put_probabilities = calculate_probabilities_from_options(puts, method) if len(puts) >= 3 else []

    if len(call_probabilities) == 0 and len(put_probabilities) == 0:
        raise ValueError('No valid probabilities calculated from calls or puts')

    return {
        'call_probabilities': call_probabilities,
        'put_probabilities': put_probabilities,
        'underlying_price': underlying_price,
        'time_to_expiry': time_to_expiry,
        'expiry_date': expiry_date,
        'expiration_timestamp': expiration_timestamp,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'method': method
    }


def calculate_statistics(probabilities: List[Dict], underlying_price: float) -> Dict:
    """
    Calculate statistics from probability distribution.

    Args:
        probabilities: List of probability data
        underlying_price: Current underlying price

    Returns:
        Dict with statistics
    """
    if len(probabilities) == 0:
        return None

    strikes = [p['strike'] for p in probabilities]
    probs = [p['probability'] for p in probabilities]

    # Expected price (mean)
    expected_price = sum(s * p for s, p in zip(strikes, probs))

    # Variance and standard deviation
    variance = sum((s - expected_price) ** 2 * p for s, p in zip(strikes, probs))
    std_dev = np.sqrt(variance)

    # Mode (strike with highest probability)
    mode_idx = np.argmax(probs)
    mode_strike = strikes[mode_idx]

    # Probability above/below current price
    prob_above = sum(p for s, p in zip(strikes, probs) if s > underlying_price)
    prob_below = sum(p for s, p in zip(strikes, probs) if s <= underlying_price)

    return {
        'expected_price': expected_price,
        'std_dev': std_dev,
        'mode_strike': mode_strike,
        'prob_above_current': prob_above,
        'prob_below_current': prob_below
    }


def create_visualization_density(probabilities: List[Dict],
                                expiry_timestamp: int,
                                num_points: int = 200) -> Dict:
    """
    Create a simplified probability density for visualization.

    Args:
        probabilities: List of probability data with 'strike' and 'probability'
        expiry_timestamp: Expiry timestamp in milliseconds
        num_points: Number of points for interpolation

    Returns:
        Dict with 'strikes' and 'densities' for visualization
    """
    if len(probabilities) == 0:
        return {'strikes': [], 'densities': []}

    strikes = np.array([p['strike'] for p in probabilities])
    probs = np.array([p['probability'] for p in probabilities])

    # Create interpolated density on uniform grid
    min_strike = strikes.min()
    max_strike = strikes.max()
    strike_range = np.linspace(min_strike, max_strike, num_points)

    # Interpolate probabilities
    density = np.interp(strike_range, strikes, probs, left=0, right=0)

    # Calculate days to expiry for labeling
    now = time.time() * 1000
    days_to_expiry = (expiry_timestamp - now) / (1000 * 60 * 60 * 24)

    return {
        'strikes': strike_range.tolist(),
        'densities': density.tolist(),
        'days_to_expiry': days_to_expiry,
        'expiry_timestamp': expiry_timestamp
    }


def precompute_all_probabilities(currencies: List[str] = None,
                                 method: str = 'finite-diff',
                                 max_days: int = 90) -> Dict:
    """
    Precompute implied probabilities for multiple currencies and expiries.

    Args:
        currencies: List of currencies to process (default: ['BTC', 'ETH'])
        method: Calculation method ('finite-diff' or 'cubic-spline')
        max_days: Maximum days to expiry to include (default: 90)

    Returns:
        Dict with all computed probabilities
    """
    if currencies is None:
        currencies = DEFAULT_CURRENCIES

    results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'method': method,
        'currencies': {}
    }

    for currency in currencies:
        print(f"\n{'='*70}")
        print(f"Processing {currency}")
        print(f"{'='*70}")

        # Get available expiries
        expiries = fetch_available_expiries(currency)

        if len(expiries) == 0:
            print(f"No expiries found for {currency}")
            continue

        # Filter expiries within max_days
        now = time.time() * 1000  # milliseconds
        filtered_expiries = []
        for expiry_info in expiries:
            days_to_expiry = (expiry_info['timestamp'] - now) / (1000 * 60 * 60 * 24)
            if days_to_expiry <= max_days:
                filtered_expiries.append(expiry_info)

        print(f"Found {len(filtered_expiries)} expiries within {max_days} days")

        # Process filtered expiries
        currency_results = {}
        for expiry_info in filtered_expiries:
            expiry = expiry_info['expiry']

            try:
                # Fetch option chain
                options_data = fetch_option_chain_data(currency, expiry)

                if len(options_data) == 0:
                    print(f"No options data for {currency}-{expiry}")
                    continue

                # Calculate probabilities
                prob_result = calculate_implied_probability(options_data, method)

                # Calculate statistics
                call_stats = calculate_statistics(
                    prob_result['call_probabilities'],
                    prob_result['underlying_price']
                )
                put_stats = calculate_statistics(
                    prob_result['put_probabilities'],
                    prob_result['underlying_price']
                )

                prob_result['call_statistics'] = call_stats
                prob_result['put_statistics'] = put_stats

                # Create visualization-friendly density data
                call_density = create_visualization_density(
                    prob_result['call_probabilities'],
                    prob_result['expiration_timestamp']
                )
                put_density = create_visualization_density(
                    prob_result['put_probabilities'],
                    prob_result['expiration_timestamp']
                )

                prob_result['call_density'] = call_density
                prob_result['put_density'] = put_density

                currency_results[expiry] = prob_result

                print(f"✓ Computed probabilities for {currency}-{expiry}")
                print(f"  Underlying: ${prob_result['underlying_price']:.2f}")
                print(f"  Time to expiry: {prob_result['time_to_expiry']*365:.0f} days")
                if call_stats:
                    print(f"  Call expected: ${call_stats['expected_price']:.2f}")
                if put_stats:
                    print(f"  Put expected: ${put_stats['expected_price']:.2f}")

            except Exception as e:
                print(f"Error processing {currency}-{expiry}: {e}")
                continue

        results['currencies'][currency] = currency_results

    return results


def main():
    """Main function to precompute and save implied probabilities."""
    print("="*70)
    print("PRECOMPUTING IMPLIED PROBABILITIES")
    print("="*70)
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")

    # Compute probabilities
    results = precompute_all_probabilities(
        currencies=['BTC', 'ETH'],
        method='finite-diff',
        max_days=90  # Compute for expiries up to 90 days out
    )

    # Save to JSON
    output_file = 'data/implied_probabilities.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*70)
    print(f"Results saved to {output_file}")
    print("="*70)

    # Print summary
    for currency, expiries in results['currencies'].items():
        print(f"\n{currency}: {len(expiries)} expiries processed")
        for expiry in expiries:
            print(f"  - {expiry}")


if __name__ == '__main__':
    main()
