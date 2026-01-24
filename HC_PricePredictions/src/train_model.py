"""
Cruise Price Prediction Model Training
Trains and evaluates multiple ML models for cruise price prediction
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

# Plotting style
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = ['#4ECDC4', '#FF6B6B', '#F39C12', '#9B59B6', '#3498DB']


def load_data(filepath):
    """Load and display basic info about the dataset"""
    df = pd.read_csv(filepath)
    print("=" * 60)
    print("CRUISE PRICE PREDICTION - MODEL TRAINING")
    print("=" * 60)
    print(f"\nDataset Shape: {df.shape}")
    print(f"\nFeatures: {list(df.columns)}")
    print(f"\nTarget Variable: price")
    print(f"  Range: ${df['price'].min():,.0f} - ${df['price'].max():,.0f}")
    print(f"  Mean: ${df['price'].mean():,.0f}")
    return df


def create_preprocessing_pipeline():
    """Create preprocessing pipeline for features"""

    # Define feature types
    categorical_features = ['cruise_line', 'destination', 'departure_port', 'cabin_type']
    numerical_features = ['duration_nights', 'departure_month', 'days_until_departure',
                          'ship_age_years', 'passengers']

    # Create transformers
    categorical_transformer = OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore')
    numerical_transformer = StandardScaler()

    # Combine into column transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    return preprocessor, categorical_features, numerical_features


def train_and_evaluate_models(X_train, X_test, y_train, y_test, preprocessor):
    """Train multiple models and compare performance"""

    models = {
        'Linear Regression': LinearRegression(),
        'Ridge Regression': Ridge(alpha=1.0),
        'Lasso Regression': Lasso(alpha=1.0),
        'Random Forest': RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    }

    results = []

    print("\n" + "=" * 60)
    print("MODEL TRAINING & EVALUATION")
    print("=" * 60)

    best_model = None
    best_r2 = -float('inf')
    best_pipeline = None

    for name, model in models.items():
        print(f"\nTraining {name}...")

        # Create pipeline
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', model)
        ])

        # Train
        pipeline.fit(X_train, y_train)

        # Predict
        y_pred = pipeline.predict(X_test)

        # Metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        # Cross-validation
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='r2')

        results.append({
            'Model': name,
            'MAE': mae,
            'RMSE': rmse,
            'R2': r2,
            'CV_R2_Mean': cv_scores.mean(),
            'CV_R2_Std': cv_scores.std()
        })

        print(f"  MAE: ${mae:,.0f}")
        print(f"  RMSE: ${rmse:,.0f}")
        print(f"  R2 Score: {r2:.4f}")
        print(f"  CV R2: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

        # Track best model
        if r2 > best_r2:
            best_r2 = r2
            best_model = name
            best_pipeline = pipeline

    return pd.DataFrame(results), best_model, best_pipeline


def analyze_feature_importance(pipeline, feature_names):
    """Analyze and visualize feature importance for tree-based models"""

    model = pipeline.named_steps['regressor']

    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_

        # Get feature names after preprocessing
        preprocessor = pipeline.named_steps['preprocessor']
        cat_features = preprocessor.named_transformers_['cat'].get_feature_names_out()
        num_features = ['duration_nights', 'departure_month', 'days_until_departure',
                        'ship_age_years', 'passengers']
        all_features = list(num_features) + list(cat_features)

        # Create importance dataframe
        importance_df = pd.DataFrame({
            'Feature': all_features[:len(importances)],
            'Importance': importances
        }).sort_values('Importance', ascending=True)

        # Plot top 15 features
        fig, ax = plt.subplots(figsize=(10, 8))
        top_features = importance_df.tail(15)
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_features)))

        ax.barh(top_features['Feature'], top_features['Importance'], color=colors)
        ax.set_xlabel('Importance', fontweight='bold')
        ax.set_title('Top 15 Feature Importances', fontweight='bold', fontsize=14)
        plt.tight_layout()
        plt.savefig('../visualizations/feature_importance.png', dpi=150, facecolor='white')
        plt.close()
        print("\nSaved: visualizations/feature_importance.png")

        return importance_df


def create_visualizations(df, results_df, pipeline, X_test, y_test):
    """Create visualizations for the analysis"""

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle('Cruise Price Prediction Analysis', fontsize=18, fontweight='bold', y=1.02)

    # 1. Price Distribution
    ax1 = axes[0, 0]
    ax1.hist(df['price'], bins=40, color=COLORS[0], edgecolor='white', alpha=0.8)
    ax1.axvline(df['price'].mean(), color=COLORS[1], linestyle='--', linewidth=2,
                label=f'Mean: ${df["price"].mean():,.0f}')
    ax1.set_xlabel('Price ($)', fontweight='bold')
    ax1.set_ylabel('Frequency', fontweight='bold')
    ax1.set_title('Price Distribution', fontweight='bold')
    ax1.legend()

    # 2. Model Comparison
    ax2 = axes[0, 1]
    models = results_df['Model'].values
    r2_scores = results_df['R2'].values
    colors = [COLORS[0] if r2 == max(r2_scores) else COLORS[4] for r2 in r2_scores]
    bars = ax2.barh(models, r2_scores, color=colors, edgecolor='white')
    ax2.set_xlabel('R2 Score', fontweight='bold')
    ax2.set_title('Model Performance Comparison', fontweight='bold')
    for bar, val in zip(bars, r2_scores):
        ax2.text(val + 0.01, bar.get_y() + bar.get_height()/2,
                f'{val:.3f}', va='center', fontweight='bold')
    ax2.set_xlim(0, 1.1)

    # 3. Actual vs Predicted
    ax3 = axes[1, 0]
    y_pred = pipeline.predict(X_test)
    ax3.scatter(y_test, y_pred, alpha=0.5, c=COLORS[0], s=20)
    max_val = max(y_test.max(), y_pred.max())
    ax3.plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    ax3.set_xlabel('Actual Price ($)', fontweight='bold')
    ax3.set_ylabel('Predicted Price ($)', fontweight='bold')
    ax3.set_title('Actual vs Predicted Prices', fontweight='bold')
    ax3.legend()

    # 4. Price by Destination
    ax4 = axes[1, 1]
    dest_prices = df.groupby('destination')['price'].mean().sort_values()
    colors_dest = plt.cm.viridis(np.linspace(0.2, 0.9, len(dest_prices)))
    ax4.barh(dest_prices.index, dest_prices.values, color=colors_dest)
    ax4.set_xlabel('Average Price ($)', fontweight='bold')
    ax4.set_title('Average Price by Destination', fontweight='bold')

    plt.tight_layout()
    plt.savefig('../visualizations/model_analysis.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("Saved: visualizations/model_analysis.png")


def create_price_factors_viz(df):
    """Create visualization showing price factors"""

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle('Factors Affecting Cruise Prices', fontsize=18, fontweight='bold', y=1.02)

    # 1. Price by Cabin Type
    ax1 = axes[0, 0]
    cabin_order = ['Interior', 'Ocean View', 'Balcony', 'Suite']
    cabin_prices = df.groupby('cabin_type')['price'].mean().reindex(cabin_order)
    bars = ax1.bar(cabin_prices.index, cabin_prices.values, color=COLORS[:4], edgecolor='white')
    ax1.set_ylabel('Average Price ($)', fontweight='bold')
    ax1.set_title('Price by Cabin Type', fontweight='bold')
    for bar, val in zip(bars, cabin_prices.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'${val:,.0f}', ha='center', fontweight='bold')

    # 2. Price by Cruise Line
    ax2 = axes[0, 1]
    line_prices = df.groupby('cruise_line')['price'].mean().sort_values()
    colors_line = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(line_prices)))
    ax2.barh(line_prices.index, line_prices.values, color=colors_line)
    ax2.set_xlabel('Average Price ($)', fontweight='bold')
    ax2.set_title('Price by Cruise Line', fontweight='bold')

    # 3. Price by Duration
    ax3 = axes[1, 0]
    duration_prices = df.groupby('duration_nights')['price'].mean()
    ax3.plot(duration_prices.index, duration_prices.values, marker='o',
             color=COLORS[0], linewidth=2, markersize=8)
    ax3.fill_between(duration_prices.index, duration_prices.values, alpha=0.3, color=COLORS[0])
    ax3.set_xlabel('Duration (Nights)', fontweight='bold')
    ax3.set_ylabel('Average Price ($)', fontweight='bold')
    ax3.set_title('Price by Cruise Duration', fontweight='bold')

    # 4. Price by Booking Window
    ax4 = axes[1, 1]
    df['booking_window'] = pd.cut(df['days_until_departure'],
                                   bins=[0, 14, 30, 90, 180, 365],
                                   labels=['<2 weeks', '2-4 weeks', '1-3 months', '3-6 months', '6-12 months'])
    window_prices = df.groupby('booking_window')['price'].mean()
    bars = ax4.bar(range(len(window_prices)), window_prices.values, color=COLORS, edgecolor='white')
    ax4.set_xticks(range(len(window_prices)))
    ax4.set_xticklabels(window_prices.index, rotation=15)
    ax4.set_ylabel('Average Price ($)', fontweight='bold')
    ax4.set_title('Price by Booking Window', fontweight='bold')

    plt.tight_layout()
    plt.savefig('../visualizations/price_factors.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("Saved: visualizations/price_factors.png")


def save_model(pipeline, filepath):
    """Save the trained model"""
    joblib.dump(pipeline, filepath)
    print(f"\nModel saved to: {filepath}")


def main():
    # Load data
    df = load_data('../data/cruise_prices.csv')

    # Prepare features and target
    X = df.drop('price', axis=1)
    y = df['price']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\nTraining set: {len(X_train):,} samples")
    print(f"Test set: {len(X_test):,} samples")

    # Create preprocessing pipeline
    preprocessor, cat_features, num_features = create_preprocessing_pipeline()

    # Train and evaluate models
    results_df, best_model, best_pipeline = train_and_evaluate_models(
        X_train, X_test, y_train, y_test, preprocessor
    )

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"\nBest Model: {best_model}")
    print(f"\nAll Results:")
    print(results_df.to_string(index=False))

    # Save results
    results_df.to_csv('../data/model_results.csv', index=False)

    # Feature importance
    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("=" * 60)
    importance_df = analyze_feature_importance(best_pipeline, X.columns)
    if importance_df is not None:
        print("\nTop 10 Features:")
        print(importance_df.tail(10).to_string(index=False))

    # Create visualizations
    print("\n" + "=" * 60)
    print("CREATING VISUALIZATIONS")
    print("=" * 60)
    create_visualizations(df, results_df, best_pipeline, X_test, y_test)
    create_price_factors_viz(df)

    # Save best model
    save_model(best_pipeline, '../models/cruise_price_model.joblib')

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)

    return best_pipeline, results_df


if __name__ == "__main__":
    main()
