"""
Cruise Price Dataset Generator
Creates a realistic synthetic dataset for cruise price prediction
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_SAMPLES = 5000

# Cruise Lines with base price multipliers
CRUISE_LINES = {
    'Royal Caribbean': 1.0,
    'Carnival': 0.85,
    'Norwegian': 0.95,
    'MSC': 0.80,
    'Princess': 1.05,
    'Celebrity': 1.15,
    'Holland America': 1.10,
    'Disney': 1.45,
}

# Destinations with base prices and seasonal patterns
DESTINATIONS = {
    'Caribbean': {'base': 800, 'peak_months': [12, 1, 2, 3], 'peak_mult': 1.4},
    'Bahamas': {'base': 600, 'peak_months': [12, 1, 2, 3], 'peak_mult': 1.35},
    'Alaska': {'base': 1200, 'peak_months': [6, 7, 8], 'peak_mult': 1.5},
    'Mediterranean': {'base': 1400, 'peak_months': [6, 7, 8], 'peak_mult': 1.45},
    'Mexico': {'base': 700, 'peak_months': [12, 1, 2, 3], 'peak_mult': 1.3},
    'Hawaii': {'base': 1500, 'peak_months': [12, 1, 6, 7], 'peak_mult': 1.35},
    'Northern Europe': {'base': 1600, 'peak_months': [6, 7, 8], 'peak_mult': 1.4},
    'South Pacific': {'base': 1800, 'peak_months': [11, 12, 1, 2], 'peak_mult': 1.3},
}

# Cabin types with multipliers
CABIN_TYPES = {
    'Interior': 1.0,
    'Ocean View': 1.25,
    'Balcony': 1.55,
    'Suite': 2.5,
}

# Departure ports
DEPARTURE_PORTS = {
    'Miami': 1.0,
    'Fort Lauderdale': 0.98,
    'Port Canaveral': 0.95,
    'Tampa': 0.92,
    'New Orleans': 0.90,
    'Galveston': 0.88,
    'Seattle': 1.05,
    'Los Angeles': 1.02,
    'New York': 1.08,
    'San Juan': 0.95,
}

def generate_cruise_data(num_samples):
    """Generate synthetic cruise pricing data"""

    data = []

    for _ in range(num_samples):
        # Random selections
        cruise_line = random.choice(list(CRUISE_LINES.keys()))
        destination = random.choice(list(DESTINATIONS.keys()))
        cabin_type = random.choice(list(CABIN_TYPES.keys()))
        departure_port = random.choice(list(DEPARTURE_PORTS.keys()))

        # Duration (nights) - weighted towards common lengths
        duration_weights = [0.05, 0.15, 0.25, 0.25, 0.15, 0.08, 0.04, 0.02, 0.01]
        duration = random.choices(range(3, 12), weights=duration_weights)[0]

        # Longer cruises for certain destinations
        if destination in ['Alaska', 'Mediterranean', 'Northern Europe', 'South Pacific']:
            duration = max(duration, random.randint(7, 14))

        # Departure date (within next 365 days)
        days_until_departure = random.randint(7, 365)
        departure_date = datetime.now() + timedelta(days=days_until_departure)
        departure_month = departure_date.month

        # Ship age (0-25 years)
        ship_age = random.randint(0, 25)

        # Passengers (1-4)
        passengers = random.choices([1, 2, 3, 4], weights=[0.1, 0.6, 0.2, 0.1])[0]

        # Calculate base price
        dest_info = DESTINATIONS[destination]
        base_price = dest_info['base']

        # Apply multipliers
        price = base_price
        price *= CRUISE_LINES[cruise_line]
        price *= CABIN_TYPES[cabin_type]
        price *= DEPARTURE_PORTS[departure_port]

        # Duration multiplier (per night, with diminishing returns)
        price *= (duration * 0.85 + 0.15 * duration ** 0.5)

        # Seasonal adjustment
        if departure_month in dest_info['peak_months']:
            price *= dest_info['peak_mult']
        elif departure_month in [(m % 12) + 1 for m in dest_info['peak_months']]:
            price *= (dest_info['peak_mult'] + 1) / 2  # Shoulder season

        # Days until departure (last minute = cheaper, but very last minute = expensive)
        if days_until_departure < 14:
            price *= 0.85  # Last minute deals
        elif days_until_departure < 30:
            price *= 0.92
        elif days_until_departure > 300:
            price *= 1.05  # Early booking premium
        elif days_until_departure > 180:
            price *= 0.95  # Sweet spot for booking

        # Ship age discount
        if ship_age > 15:
            price *= 0.88
        elif ship_age > 10:
            price *= 0.94
        elif ship_age < 3:
            price *= 1.08  # New ship premium

        # Per passenger (not linear - economies of scale)
        price *= (1 + (passengers - 1) * 0.7)

        # Add some randomness (market variation)
        price *= np.random.uniform(0.9, 1.1)

        # Round to nearest $10
        price = round(price / 10) * 10

        # Ensure minimum price
        price = max(price, 299)

        data.append({
            'cruise_line': cruise_line,
            'destination': destination,
            'departure_port': departure_port,
            'cabin_type': cabin_type,
            'duration_nights': duration,
            'departure_month': departure_month,
            'days_until_departure': days_until_departure,
            'ship_age_years': ship_age,
            'passengers': passengers,
            'price': price
        })

    return pd.DataFrame(data)


def main():
    print("=" * 60)
    print("GENERATING CRUISE PRICING DATASET")
    print("=" * 60)

    # Generate data
    df = generate_cruise_data(NUM_SAMPLES)

    # Display stats
    print(f"\nGenerated {len(df):,} cruise records")
    print(f"\nPrice Statistics:")
    print(f"  Min: ${df['price'].min():,.0f}")
    print(f"  Max: ${df['price'].max():,.0f}")
    print(f"  Mean: ${df['price'].mean():,.0f}")
    print(f"  Median: ${df['price'].median():,.0f}")

    print(f"\nFeature Summary:")
    print(f"  Cruise Lines: {df['cruise_line'].nunique()}")
    print(f"  Destinations: {df['destination'].nunique()}")
    print(f"  Cabin Types: {df['cabin_type'].nunique()}")
    print(f"  Departure Ports: {df['departure_port'].nunique()}")

    print(f"\nSample Records:")
    print(df.head(10).to_string())

    # Save to CSV
    output_path = '../data/cruise_prices.csv'
    df.to_csv(output_path, index=False)
    print(f"\nDataset saved to: {output_path}")

    return df


if __name__ == "__main__":
    main()
