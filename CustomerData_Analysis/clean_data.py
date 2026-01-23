import pandas as pd
import numpy as np
from datetime import datetime

# Load data
df = pd.read_csv('Customers.csv')
original_count = len(df)

# Start logging
log = []
log.append(f"DATA CLEANING LOG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append("=" * 60)
log.append(f"\nOriginal dataset: {original_count} rows, {len(df.columns)} columns")
log.append(f"Columns: {', '.join(df.columns.tolist())}\n")

# --- 1. Check for duplicates ---
log.append("-" * 60)
log.append("1. DUPLICATE CHECK")
duplicates = df.duplicated().sum()
duplicate_ids = df[df.duplicated(subset=['CustomerID'], keep=False)]
if duplicates > 0:
    log.append(f"   Found {duplicates} duplicate rows - REMOVED")
    log.append(f"   Reason: Duplicate entries can skew analysis and inflate counts")
    df = df.drop_duplicates()
else:
    log.append("   No duplicate rows found")

if len(duplicate_ids) > 0 and duplicates == 0:
    dup_id_count = df['CustomerID'].duplicated().sum()
    if dup_id_count > 0:
        log.append(f"   Found {dup_id_count} duplicate CustomerIDs - REMOVED (kept first)")
        log.append(f"   Reason: Each customer should have a unique ID")
        df = df.drop_duplicates(subset=['CustomerID'], keep='first')

# --- 2. Check for missing values ---
log.append("\n" + "-" * 60)
log.append("2. MISSING VALUES CHECK")
missing = df.isnull().sum()
total_missing = missing.sum()
if total_missing > 0:
    log.append(f"   Found {total_missing} missing values:")
    for col, count in missing.items():
        if count > 0:
            log.append(f"      - {col}: {count} missing")

    # Handle missing values
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if df[col].dtype in ['int64', 'float64']:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                log.append(f"   Filled {col} missing values with median ({median_val})")
                log.append(f"   Reason: Median is robust to outliers for numerical data")
            else:
                mode_val = df[col].mode()[0]
                df[col].fillna(mode_val, inplace=True)
                log.append(f"   Filled {col} missing values with mode ({mode_val})")
                log.append(f"   Reason: Mode preserves most common category")
else:
    log.append("   No missing values found")

# --- 3. Check for invalid/negative values ---
log.append("\n" + "-" * 60)
log.append("3. INVALID VALUES CHECK")
invalid_found = False

# Age should be reasonable (0-120)
invalid_age = df[(df['Age'] < 0) | (df['Age'] > 120)]
if len(invalid_age) > 0:
    log.append(f"   Found {len(invalid_age)} invalid ages - REMOVED")
    log.append(f"   Reason: Age must be between 0-120 years")
    df = df[(df['Age'] >= 0) & (df['Age'] <= 120)]
    invalid_found = True

# Income should be non-negative
invalid_income = df[df['Annual Income ($)'] < 0]
if len(invalid_income) > 0:
    log.append(f"   Found {len(invalid_income)} negative incomes - REMOVED")
    log.append(f"   Reason: Income cannot be negative")
    df = df[df['Annual Income ($)'] >= 0]
    invalid_found = True

# Spending Score should be 1-100
invalid_score = df[(df['Spending Score (1-100)'] < 1) | (df['Spending Score (1-100)'] > 100)]
if len(invalid_score) > 0:
    log.append(f"   Found {len(invalid_score)} invalid spending scores - REMOVED")
    log.append(f"   Reason: Spending score must be between 1-100 as per column definition")
    df = df[(df['Spending Score (1-100)'] >= 1) & (df['Spending Score (1-100)'] <= 100)]
    invalid_found = True

# Work Experience should be non-negative
invalid_exp = df[df['Work Experience'] < 0]
if len(invalid_exp) > 0:
    log.append(f"   Found {len(invalid_exp)} negative work experience - REMOVED")
    log.append(f"   Reason: Work experience cannot be negative")
    df = df[df['Work Experience'] >= 0]
    invalid_found = True

# Family Size should be at least 1
invalid_family = df[df['Family Size'] < 1]
if len(invalid_family) > 0:
    log.append(f"   Found {len(invalid_family)} invalid family sizes - REMOVED")
    log.append(f"   Reason: Family size must be at least 1 (the customer themselves)")
    df = df[df['Family Size'] >= 1]
    invalid_found = True

if not invalid_found:
    log.append("   No invalid values found")

# --- 4. Standardize text fields ---
log.append("\n" + "-" * 60)
log.append("4. TEXT STANDARDIZATION")
# Gender standardization
original_genders = df['Gender'].unique()
df['Gender'] = df['Gender'].str.strip().str.title()
new_genders = df['Gender'].unique()
log.append(f"   Gender values standardized: {original_genders} -> {new_genders}")
log.append(f"   Reason: Consistent capitalization for accurate grouping")

# Profession standardization
original_professions = df['Profession'].unique()
df['Profession'] = df['Profession'].str.strip().str.title()
new_professions = df['Profession'].unique()
if not np.array_equal(original_professions, new_professions):
    log.append(f"   Profession values standardized (trimmed whitespace, title case)")
    log.append(f"   Reason: Consistent formatting prevents duplicate categories")
else:
    log.append("   Profession values already standardized")

# --- 5. Check for outliers using IQR method ---
log.append("\n" + "-" * 60)
log.append("5. OUTLIER DETECTION (IQR Method)")
log.append("   Note: Outliers logged but NOT removed - may be valid data points")

numeric_cols = ['Age', 'Annual Income ($)', 'Spending Score (1-100)', 'Work Experience', 'Family Size']
for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = df[(df[col] < lower) | (df[col] > upper)]
    if len(outliers) > 0:
        log.append(f"   {col}: {len(outliers)} outliers detected (below {lower:.1f} or above {upper:.1f})")
    else:
        log.append(f"   {col}: No outliers detected")

# --- 6. Data type optimization ---
log.append("\n" + "-" * 60)
log.append("6. DATA TYPE OPTIMIZATION")
log.append("   CustomerID: Kept as int (unique identifier)")
log.append("   Gender: Converted to category (memory efficient)")
log.append("   Profession: Converted to category (memory efficient)")
df['Gender'] = df['Gender'].astype('category')
df['Profession'] = df['Profession'].astype('category')

# --- Summary ---
log.append("\n" + "=" * 60)
log.append("SUMMARY")
log.append("=" * 60)
final_count = len(df)
removed = original_count - final_count
log.append(f"Original rows: {original_count}")
log.append(f"Final rows: {final_count}")
log.append(f"Rows removed: {removed} ({(removed/original_count)*100:.2f}%)")
log.append(f"\nCleaned data saved to: Customers_cleaned.csv")

# Save cleaned data
df.to_csv('Customers_cleaned.csv', index=False)

# Save log
with open('cleaning_log.txt', 'w') as f:
    f.write('\n'.join(log))

print('\n'.join(log))
print("\n\nDone! Check 'Customers_cleaned.csv' and 'cleaning_log.txt'")
