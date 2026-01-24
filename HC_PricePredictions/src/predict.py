"""
Cruise Price Prediction Interface
Make predictions using the trained model
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime


def load_model(model_path='../models/cruise_price_model.joblib'):
    """Load the trained model"""
    return joblib.load(model_path)


def predict_price(model, cruise_line, destination, departure_port, cabin_type,
                  duration_nights, departure_month, days_until_departure,
                  ship_age_years, passengers):
    """Make a single prediction"""

    # Create input dataframe
    input_data = pd.DataFrame([{
        'cruise_line': cruise_line,
        'destination': destination,
        'departure_port': departure_port,
        'cabin_type': cabin_type,
        'duration_nights': duration_nights,
        'departure_month': departure_month,
        'days_until_departure': days_until_departure,
        'ship_age_years': ship_age_years,
        'passengers': passengers
    }])

    # Make prediction
    predicted_price = model.predict(input_data)[0]

    return round(predicted_price, -1)  # Round to nearest $10


def get_price_range(model, base_params, vary_param, vary_values):
    """Get price predictions across a range of values for a parameter"""

    prices = []
    for value in vary_values:
        params = base_params.copy()
        params[vary_param] = value
        price = predict_price(model, **params)
        prices.append({'value': value, 'price': price})

    return pd.DataFrame(prices)


def interactive_prediction():
    """Interactive command-line prediction interface"""

    print("=" * 60)
    print("CRUISE PRICE PREDICTOR")
    print("=" * 60)

    # Load model
    try:
        model = load_model()
        print("\nModel loaded successfully!")
    except FileNotFoundError:
        print("\nError: Model not found. Please run train_model.py first.")
        return

    # Valid options
    cruise_lines = ['Royal Caribbean', 'Carnival', 'Norwegian', 'MSC',
                    'Princess', 'Celebrity', 'Holland America', 'Disney']
    destinations = ['Caribbean', 'Bahamas', 'Alaska', 'Mediterranean',
                    'Mexico', 'Hawaii', 'Northern Europe', 'South Pacific']
    cabin_types = ['Interior', 'Ocean View', 'Balcony', 'Suite']
    ports = ['Miami', 'Fort Lauderdale', 'Port Canaveral', 'Tampa',
             'New Orleans', 'Galveston', 'Seattle', 'Los Angeles', 'New York', 'San Juan']

    print("\n--- Enter Cruise Details ---")

    # Get inputs
    print(f"\nCruise Lines: {', '.join(cruise_lines)}")
    cruise_line = input("Cruise Line: ").strip() or 'Royal Caribbean'

    print(f"\nDestinations: {', '.join(destinations)}")
    destination = input("Destination: ").strip() or 'Caribbean'

    print(f"\nDeparture Ports: {', '.join(ports)}")
    departure_port = input("Departure Port: ").strip() or 'Miami'

    print(f"\nCabin Types: {', '.join(cabin_types)}")
    cabin_type = input("Cabin Type: ").strip() or 'Balcony'

    duration = int(input("\nDuration (nights, 3-14): ").strip() or '7')
    departure_month = int(input("Departure Month (1-12): ").strip() or '6')
    days_until = int(input("Days Until Departure (7-365): ").strip() or '90')
    ship_age = int(input("Ship Age (years, 0-25): ").strip() or '5')
    passengers = int(input("Number of Passengers (1-4): ").strip() or '2')

    # Make prediction
    price = predict_price(
        model,
        cruise_line=cruise_line,
        destination=destination,
        departure_port=departure_port,
        cabin_type=cabin_type,
        duration_nights=duration,
        departure_month=departure_month,
        days_until_departure=days_until,
        ship_age_years=ship_age,
        passengers=passengers
    )

    print("\n" + "=" * 60)
    print("PREDICTION RESULT")
    print("=" * 60)
    print(f"\nCruise Details:")
    print(f"  {cruise_line} - {destination}")
    print(f"  Departing from {departure_port}")
    print(f"  {duration} nights, {cabin_type} cabin")
    print(f"  {passengers} passenger(s)")
    print(f"  Departing in {days_until} days (Month {departure_month})")

    print(f"\n  PREDICTED PRICE: ${price:,.0f}")
    print(f"  (${price/passengers:,.0f} per person)")

    # Show price comparison
    print("\n--- Price Comparison by Cabin Type ---")
    for ct in cabin_types:
        ct_price = predict_price(model, cruise_line, destination, departure_port,
                                  ct, duration, departure_month, days_until, ship_age, passengers)
        marker = " <-- Your selection" if ct == cabin_type else ""
        print(f"  {ct:12s}: ${ct_price:>8,.0f}{marker}")


def example_predictions():
    """Show example predictions"""

    print("=" * 60)
    print("EXAMPLE CRUISE PRICE PREDICTIONS")
    print("=" * 60)

    model = load_model()

    examples = [
        {
            'name': 'Budget Caribbean Getaway',
            'cruise_line': 'Carnival', 'destination': 'Caribbean',
            'departure_port': 'Miami', 'cabin_type': 'Interior',
            'duration_nights': 5, 'departure_month': 9,
            'days_until_departure': 60, 'ship_age_years': 12, 'passengers': 2
        },
        {
            'name': 'Luxury Alaska Adventure',
            'cruise_line': 'Celebrity', 'destination': 'Alaska',
            'departure_port': 'Seattle', 'cabin_type': 'Suite',
            'duration_nights': 10, 'departure_month': 7,
            'days_until_departure': 120, 'ship_age_years': 3, 'passengers': 2
        },
        {
            'name': 'Disney Family Magic',
            'cruise_line': 'Disney', 'destination': 'Bahamas',
            'departure_port': 'Port Canaveral', 'cabin_type': 'Balcony',
            'duration_nights': 4, 'departure_month': 12,
            'days_until_departure': 180, 'ship_age_years': 5, 'passengers': 4
        },
        {
            'name': 'Mediterranean Romance',
            'cruise_line': 'Princess', 'destination': 'Mediterranean',
            'departure_port': 'New York', 'cabin_type': 'Balcony',
            'duration_nights': 12, 'departure_month': 6,
            'days_until_departure': 90, 'ship_age_years': 8, 'passengers': 2
        },
    ]

    for ex in examples:
        name = ex.pop('name')
        price = predict_price(model, **ex)
        print(f"\n{name}")
        print(f"  {ex['cruise_line']} - {ex['destination']} ({ex['duration_nights']} nights)")
        print(f"  {ex['cabin_type']} cabin, {ex['passengers']} passengers")
        print(f"  PREDICTED: ${price:,.0f} (${price/ex['passengers']:,.0f}/person)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--examples':
        example_predictions()
    else:
        interactive_prediction()
