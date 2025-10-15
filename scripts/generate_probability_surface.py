#!/usr/bin/env python3
"""
Generate 2D probability surface data for contour plotting.
Creates a time x price grid showing implied probability distributions
from options data across multiple expiries.

Output format is optimized for contour/heatmap visualization with:
- X-axis: Time (expiry dates)
- Y-axis: Price (strike prices)
- Z-axis: Probability density
"""

import json
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from scipy.interpolate import interp1d, griddata


def load_probability_data(filepath: str = 'data/implied_probabilities.json') -> Dict:
    """Load precomputed probability data."""
    with open(filepath, 'r') as f:
        return json.load(f)


def create_2d_probability_surface(prob_data: Dict,
                                  currency: str = 'BTC',
                                  price_points: int = 100,
                                  use_puts: bool = False) -> Dict:
    """
    Create a 2D probability surface for contour plotting.

    Args:
        prob_data: Precomputed probability data
        currency: 'BTC' or 'ETH'
        price_points: Number of price points in the grid
        use_puts: Use put probabilities instead of call probabilities

    Returns:
        Dict with grid data for contour plotting
    """
    if currency not in prob_data['currencies']:
        raise ValueError(f"Currency {currency} not found in data")

    currency_data = prob_data['currencies'][currency]
    expiries = sorted(currency_data.keys(),
                     key=lambda x: currency_data[x]['expiration_timestamp'])

    # Collect all data points
    time_points = []  # Unix timestamps in seconds
    price_points_list = []
    probability_values = []

    now = datetime.now(timezone.utc).timestamp()  # seconds

    for expiry_key in expiries:
        expiry_data = currency_data[expiry_key]

        # Choose calls or puts
        prob_key = 'put_probabilities' if use_puts else 'call_probabilities'
        probabilities = expiry_data.get(prob_key, [])

        if len(probabilities) == 0:
            continue

        # Get expiry timestamp in seconds
        expiry_timestamp_ms = expiry_data['expiration_timestamp']
        expiry_timestamp = expiry_timestamp_ms / 1000  # Convert to seconds

        # Add each strike price and probability
        for prob_point in probabilities:
            time_points.append(expiry_timestamp)
            price_points_list.append(prob_point['strike'])
            probability_values.append(prob_point['probability'])

    if len(time_points) == 0:
        raise ValueError(f"No probability data available for {currency}")

    # Convert to numpy arrays
    time_array = np.array(time_points)
    price_array = np.array(price_points_list)
    prob_array = np.array(probability_values)

    # Create regular grid
    time_min, time_max = time_array.min(), time_array.max()
    price_min, price_max = price_array.min(), price_array.max()

    # Add some padding to price
    price_range = price_max - price_min
    price_min_padded = price_min - 0.05 * price_range
    price_max_padded = price_max + 0.05 * price_range

    # Create grid - use actual expiry timestamps (in seconds)
    time_grid = np.unique(time_array)  # Unique timestamps
    price_grid = np.linspace(price_min_padded, price_max_padded, price_points)

    # Create meshgrid
    time_mesh, price_mesh = np.meshgrid(time_grid, price_grid)

    # Interpolate probabilities onto grid using griddata
    points = np.column_stack([time_array, price_array])
    grid_prob = griddata(points, prob_array, (time_mesh, price_mesh),
                        method='linear', fill_value=0.0)

    # Ensure non-negative probabilities
    grid_prob = np.maximum(grid_prob, 0.0)

    # Normalize each time slice to sum to 1
    for i, t in enumerate(time_grid):
        col_sum = np.sum(grid_prob[:, i])
        if col_sum > 0:
            grid_prob[:, i] = grid_prob[:, i] / col_sum

    # Convert timestamps to ISO dates and calculate days
    expiry_dates = []
    days_to_expiry = []
    for timestamp in time_grid:
        expiry_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        expiry_dates.append(expiry_date.isoformat())
        days = (timestamp - now) / (60 * 60 * 24)
        days_to_expiry.append(days)

    # Get current price
    first_expiry = currency_data[expiries[0]]
    current_price = first_expiry['underlying_price']

    return {
        'currency': currency,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'current_price': current_price,
        'method': prob_data['method'],
        'option_type': 'puts' if use_puts else 'calls',
        'grid': {
            'time_unix': time_grid.tolist(),  # Unix timestamps in seconds
            'time_dates': expiry_dates,  # ISO format dates
            'time_days': days_to_expiry,  # Days to expiry (for backward compatibility)
            'prices': price_grid.tolist(),
            'probabilities': grid_prob.tolist(),  # 2D array: [price_index, time_index]
        },
        'metadata': {
            'price_points': len(price_grid),
            'time_points': len(time_grid),
            'price_min': float(price_min),
            'price_max': float(price_max),
            'time_min': float(time_min),
            'time_max': float(time_max),
            'time_min_days': float(days_to_expiry[0]) if len(days_to_expiry) > 0 else 0,
            'time_max_days': float(days_to_expiry[-1]) if len(days_to_expiry) > 0 else 0
        }
    }


def create_combined_surface(prob_data: Dict,
                           currency: str = 'BTC',
                           price_points: int = 100) -> Dict:
    """
    Create averaged call and put probability surfaces.

    Args:
        prob_data: Precomputed probability data
        currency: 'BTC' or 'ETH'
        price_points: Number of price points in the grid

    Returns:
        Dict with combined surface data
    """
    # Generate both surfaces
    call_surface = create_2d_probability_surface(prob_data, currency, price_points, use_puts=False)
    put_surface = create_2d_probability_surface(prob_data, currency, price_points, use_puts=True)

    # Average the probabilities
    call_probs = np.array(call_surface['grid']['probabilities'])
    put_probs = np.array(put_surface['grid']['probabilities'])

    # Handle potential shape mismatches by interpolation
    if call_probs.shape == put_probs.shape:
        averaged_probs = (call_probs + put_probs) / 2.0
    else:
        # Use call surface as base
        averaged_probs = call_probs

    # Renormalize
    for i in range(averaged_probs.shape[1]):
        col_sum = np.sum(averaged_probs[:, i])
        if col_sum > 0:
            averaged_probs[:, i] = averaged_probs[:, i] / col_sum

    return {
        'currency': currency,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'current_price': call_surface['current_price'],
        'method': prob_data['method'],
        'option_type': 'combined',
        'grid': {
            'time_unix': call_surface['grid']['time_unix'],
            'time_days': call_surface['grid']['time_days'],
            'time_dates': call_surface['grid']['time_dates'],
            'prices': call_surface['grid']['prices'],
            'probabilities': averaged_probs.tolist(),
        },
        'metadata': call_surface['metadata']
    }


def calculate_statistics_2d(surface_data: Dict) -> Dict:
    """
    Calculate statistics for the 2D probability surface.

    Args:
        surface_data: Output from create_2d_probability_surface

    Returns:
        Dict with statistics for each time point
    """
    prices = np.array(surface_data['grid']['prices'])
    probs = np.array(surface_data['grid']['probabilities'])
    time_unix = surface_data['grid']['time_unix']
    time_dates = surface_data['grid']['time_dates']
    time_days = surface_data['grid']['time_days']

    statistics = []

    for i, (timestamp, date, days) in enumerate(zip(time_unix, time_dates, time_days)):
        prob_slice = probs[:, i]

        # Skip if all zeros
        if np.sum(prob_slice) == 0:
            continue

        # Expected price (mean)
        expected_price = np.sum(prices * prob_slice)

        # Variance and std
        variance = np.sum((prices - expected_price) ** 2 * prob_slice)
        std_dev = np.sqrt(variance)

        # Mode (price with highest probability)
        mode_idx = np.argmax(prob_slice)
        mode_price = prices[mode_idx]

        # Quantiles
        cumsum = np.cumsum(prob_slice)
        cumsum = cumsum / cumsum[-1]  # Normalize

        q05 = prices[np.searchsorted(cumsum, 0.05)]
        q25 = prices[np.searchsorted(cumsum, 0.25)]
        q50 = prices[np.searchsorted(cumsum, 0.50)]
        q75 = prices[np.searchsorted(cumsum, 0.75)]
        q95 = prices[np.searchsorted(cumsum, 0.95)]

        statistics.append({
            'time_unix': float(timestamp),
            'days_to_expiry': float(days),
            'expiry_date': date,
            'expected_price': float(expected_price),
            'std_dev': float(std_dev),
            'mode_price': float(mode_price),
            'quantiles': {
                'q05': float(q05),
                'q25': float(q25),
                'q50': float(q50),
                'q75': float(q75),
                'q95': float(q95)
            }
        })

    return {
        'currency': surface_data['currency'],
        'current_price': surface_data['current_price'],
        'statistics': statistics
    }


def main():
    """Main function to generate probability surface data."""
    print("="*70)
    print("GENERATING 2D PROBABILITY SURFACE DATA")
    print("="*70)
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Load precomputed probability data
    print("Loading precomputed probability data...")
    prob_data = load_probability_data()
    print(f"✓ Loaded data from {prob_data['timestamp']}")
    print()

    results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'method': prob_data['method'],
        'surfaces': {}
    }

    # Generate surfaces for each currency
    for currency in ['BTC', 'ETH']:
        if currency not in prob_data['currencies']:
            print(f"Skipping {currency} - no data available")
            continue

        print(f"Processing {currency}...")
        print("-" * 70)

        try:
            # Generate call surface
            print(f"  Generating call probability surface...")
            call_surface = create_2d_probability_surface(prob_data, currency,
                                                        price_points=100, use_puts=False)

            # Generate put surface
            print(f"  Generating put probability surface...")
            put_surface = create_2d_probability_surface(prob_data, currency,
                                                       price_points=100, use_puts=True)

            # Generate combined surface
            print(f"  Generating combined probability surface...")
            combined_surface = create_combined_surface(prob_data, currency, price_points=100)

            # Calculate statistics
            print(f"  Calculating statistics...")
            call_stats = calculate_statistics_2d(call_surface)
            put_stats = calculate_statistics_2d(put_surface)
            combined_stats = calculate_statistics_2d(combined_surface)

            # Store results
            results['surfaces'][currency] = {
                'call_surface': call_surface,
                'put_surface': put_surface,
                'combined_surface': combined_surface,
                'call_statistics': call_stats,
                'put_statistics': put_stats,
                'combined_statistics': combined_stats
            }

            print(f"✓ {currency} surface generated")
            print(f"  Current price: ${combined_surface['current_price']:.2f}")
            print(f"  Price range: ${combined_surface['metadata']['price_min']:.2f} - "
                  f"${combined_surface['metadata']['price_max']:.2f}")
            print(f"  Time range: {combined_surface['metadata']['time_min_days']:.1f} - "
                  f"{combined_surface['metadata']['time_max_days']:.1f} days")
            print(f"  Grid size: {combined_surface['metadata']['price_points']} prices x "
                  f"{combined_surface['metadata']['time_points']} times")
            print()

        except Exception as e:
            print(f"Error processing {currency}: {e}")
            continue

    # Save results
    output_file = 'data/probability_surface.json'
    print("Saving results...")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print("="*70)
    print(f"✓ Results saved to {output_file}")
    print("="*70)
    print()

    # Print summary
    for currency in results['surfaces'].keys():
        surface = results['surfaces'][currency]['combined_surface']
        stats = results['surfaces'][currency]['combined_statistics']['statistics']

        print(f"\n{currency} Summary:")
        print(f"  Current Price: ${surface['current_price']:.2f}")

        if len(stats) > 0:
            print(f"\n  Nearest Expiry ({stats[0]['days_to_expiry']:.1f} days):")
            print(f"    Expected Price: ${stats[0]['expected_price']:.2f}")
            print(f"    Std Deviation: ${stats[0]['std_dev']:.2f}")
            print(f"    Mode (Most Likely): ${stats[0]['mode_price']:.2f}")
            print(f"    95% Range: ${stats[0]['quantiles']['q05']:.2f} - "
                  f"${stats[0]['quantiles']['q95']:.2f}")

            if len(stats) > 1:
                print(f"\n  Furthest Expiry ({stats[-1]['days_to_expiry']:.1f} days):")
                print(f"    Expected Price: ${stats[-1]['expected_price']:.2f}")
                print(f"    Std Deviation: ${stats[-1]['std_dev']:.2f}")
                print(f"    Mode (Most Likely): ${stats[-1]['mode_price']:.2f}")
                print(f"    95% Range: ${stats[-1]['quantiles']['q05']:.2f} - "
                      f"${stats[-1]['quantiles']['q95']:.2f}")


if __name__ == '__main__':
    main()
