"""
Customer Data Pattern Analysis
Generates insights for stakeholders from cleaned customer data
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_data():
    """Load the cleaned customer data"""
    df = pd.read_csv('Customers_cleaned.csv')
    return df

def basic_statistics(df):
    """Generate basic statistical summaries"""
    print("=" * 70)
    print("CUSTOMER DATA ANALYSIS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("1. DATASET OVERVIEW")
    print("=" * 70)
    print(f"Total Customers: {len(df):,}")
    print(f"Features Analyzed: {len(df.columns)}")

    print("\n--- Numerical Statistics ---")
    numeric_cols = ['Age', 'Annual Income ($)', 'Spending Score (1-100)', 'Work Experience', 'Family Size']
    stats = df[numeric_cols].describe()
    print(stats.round(2).to_string())

    return stats

def demographic_analysis(df):
    """Analyze customer demographics"""
    print("\n" + "=" * 70)
    print("2. DEMOGRAPHIC ANALYSIS")
    print("=" * 70)

    # Gender distribution
    print("\n--- Gender Distribution ---")
    gender_dist = df['Gender'].value_counts()
    gender_pct = df['Gender'].value_counts(normalize=True) * 100
    for gender in gender_dist.index:
        print(f"  {gender}: {gender_dist[gender]:,} ({gender_pct[gender]:.1f}%)")

    # Age groups
    print("\n--- Age Distribution ---")
    df['Age_Group'] = pd.cut(df['Age'], bins=[0, 25, 35, 45, 55, 100],
                             labels=['18-25', '26-35', '36-45', '46-55', '55+'])
    age_dist = df['Age_Group'].value_counts().sort_index()
    age_pct = df['Age_Group'].value_counts(normalize=True).sort_index() * 100
    for age_grp in age_dist.index:
        print(f"  {age_grp}: {age_dist[age_grp]:,} ({age_pct[age_grp]:.1f}%)")

    # Profession distribution
    print("\n--- Top Professions ---")
    prof_dist = df['Profession'].value_counts().head(10)
    prof_pct = df['Profession'].value_counts(normalize=True).head(10) * 100
    for prof in prof_dist.index:
        print(f"  {prof}: {prof_dist[prof]:,} ({prof_pct[prof]:.1f}%)")

    return df

def income_analysis(df):
    """Analyze income patterns"""
    print("\n" + "=" * 70)
    print("3. INCOME ANALYSIS")
    print("=" * 70)

    # Income brackets
    df['Income_Bracket'] = pd.cut(df['Annual Income ($)'],
                                   bins=[0, 30000, 60000, 90000, float('inf')],
                                   labels=['Low (<$30k)', 'Medium ($30-60k)',
                                          'High ($60-90k)', 'Very High (>$90k)'])

    print("\n--- Income Distribution ---")
    income_dist = df['Income_Bracket'].value_counts().sort_index()
    income_pct = df['Income_Bracket'].value_counts(normalize=True).sort_index() * 100
    for bracket in income_dist.index:
        print(f"  {bracket}: {income_dist[bracket]:,} ({income_pct[bracket]:.1f}%)")

    # Income by profession
    print("\n--- Average Income by Profession ---")
    income_by_prof = df.groupby('Profession')['Annual Income ($)'].agg(['mean', 'median', 'count'])
    income_by_prof = income_by_prof.sort_values('mean', ascending=False)
    print(f"  {'Profession':<15} {'Avg Income':>12} {'Median':>12} {'Count':>8}")
    print("  " + "-" * 50)
    for prof, row in income_by_prof.iterrows():
        print(f"  {prof:<15} ${row['mean']:>10,.0f} ${row['median']:>10,.0f} {row['count']:>8,.0f}")

    # Income by gender
    print("\n--- Income by Gender ---")
    income_by_gender = df.groupby('Gender')['Annual Income ($)'].agg(['mean', 'median'])
    for gender, row in income_by_gender.iterrows():
        print(f"  {gender}: Avg ${row['mean']:,.0f} | Median ${row['median']:,.0f}")

    return df

def spending_analysis(df):
    """Analyze spending patterns"""
    print("\n" + "=" * 70)
    print("4. SPENDING BEHAVIOR ANALYSIS")
    print("=" * 70)

    # Spending score brackets
    df['Spending_Category'] = pd.cut(df['Spending Score (1-100)'],
                                      bins=[0, 33, 66, 100],
                                      labels=['Low Spender', 'Medium Spender', 'High Spender'])

    print("\n--- Spending Score Distribution ---")
    spend_dist = df['Spending_Category'].value_counts().sort_index()
    spend_pct = df['Spending_Category'].value_counts(normalize=True).sort_index() * 100
    for cat in spend_dist.index:
        print(f"  {cat}: {spend_dist[cat]:,} ({spend_pct[cat]:.1f}%)")

    # Spending by age group
    print("\n--- Average Spending Score by Age Group ---")
    spend_by_age = df.groupby('Age_Group')['Spending Score (1-100)'].mean().sort_index()
    for age, score in spend_by_age.items():
        print(f"  {age}: {score:.1f}")

    # Spending by income bracket
    print("\n--- Average Spending Score by Income Bracket ---")
    spend_by_income = df.groupby('Income_Bracket')['Spending Score (1-100)'].mean()
    for bracket, score in spend_by_income.items():
        print(f"  {bracket}: {score:.1f}")

    # Spending by profession
    print("\n--- Average Spending Score by Profession ---")
    spend_by_prof = df.groupby('Profession')['Spending Score (1-100)'].mean().sort_values(ascending=False)
    for prof, score in spend_by_prof.items():
        print(f"  {prof}: {score:.1f}")

    return df

def correlation_analysis(df):
    """Analyze correlations between variables"""
    print("\n" + "=" * 70)
    print("5. CORRELATION ANALYSIS")
    print("=" * 70)

    numeric_cols = ['Age', 'Annual Income ($)', 'Spending Score (1-100)', 'Work Experience', 'Family Size']
    corr_matrix = df[numeric_cols].corr()

    print("\n--- Correlation Matrix ---")
    print(corr_matrix.round(3).to_string())

    # Key correlations
    print("\n--- Key Correlation Insights ---")

    # Income vs Spending
    corr_inc_spend = corr_matrix.loc['Annual Income ($)', 'Spending Score (1-100)']
    print(f"  Income vs Spending Score: {corr_inc_spend:.3f}", end="")
    if abs(corr_inc_spend) < 0.3:
        print(" (Weak correlation)")
    elif abs(corr_inc_spend) < 0.6:
        print(" (Moderate correlation)")
    else:
        print(" (Strong correlation)")

    # Age vs Spending
    corr_age_spend = corr_matrix.loc['Age', 'Spending Score (1-100)']
    print(f"  Age vs Spending Score: {corr_age_spend:.3f}", end="")
    if abs(corr_age_spend) < 0.3:
        print(" (Weak correlation)")
    elif abs(corr_age_spend) < 0.6:
        print(" (Moderate correlation)")
    else:
        print(" (Strong correlation)")

    # Age vs Income
    corr_age_inc = corr_matrix.loc['Age', 'Annual Income ($)']
    print(f"  Age vs Income: {corr_age_inc:.3f}", end="")
    if abs(corr_age_inc) < 0.3:
        print(" (Weak correlation)")
    elif abs(corr_age_inc) < 0.6:
        print(" (Moderate correlation)")
    else:
        print(" (Strong correlation)")

    return corr_matrix

def customer_segmentation(df):
    """Identify key customer segments"""
    print("\n" + "=" * 70)
    print("6. CUSTOMER SEGMENTATION")
    print("=" * 70)

    # Create segments based on income and spending
    conditions = [
        (df['Annual Income ($)'] >= 60000) & (df['Spending Score (1-100)'] >= 60),
        (df['Annual Income ($)'] >= 60000) & (df['Spending Score (1-100)'] < 40),
        (df['Annual Income ($)'] < 40000) & (df['Spending Score (1-100)'] >= 60),
        (df['Annual Income ($)'] < 40000) & (df['Spending Score (1-100)'] < 40),
    ]
    segment_names = ['Premium (High Income, High Spend)',
                     'Careful (High Income, Low Spend)',
                     'Budget Enthusiast (Low Income, High Spend)',
                     'Conservative (Low Income, Low Spend)']

    df['Segment'] = np.select(conditions, segment_names, default='Standard (Middle)')

    print("\n--- Customer Segments ---")
    segment_dist = df['Segment'].value_counts()
    segment_pct = df['Segment'].value_counts(normalize=True) * 100

    for segment in segment_dist.index:
        print(f"\n  {segment}")
        print(f"    Count: {segment_dist[segment]:,} ({segment_pct[segment]:.1f}%)")
        segment_data = df[df['Segment'] == segment]
        print(f"    Avg Age: {segment_data['Age'].mean():.1f}")
        print(f"    Avg Income: ${segment_data['Annual Income ($)'].mean():,.0f}")
        print(f"    Avg Spending Score: {segment_data['Spending Score (1-100)'].mean():.1f}")

    return df

def high_value_customers(df):
    """Identify high-value customer characteristics"""
    print("\n" + "=" * 70)
    print("7. HIGH-VALUE CUSTOMER PROFILE")
    print("=" * 70)

    # Top 20% spenders
    top_spenders = df[df['Spending Score (1-100)'] >= df['Spending Score (1-100)'].quantile(0.8)]

    print(f"\n--- Top 20% Spenders Profile (n={len(top_spenders)}) ---")
    print(f"  Average Age: {top_spenders['Age'].mean():.1f} years")
    print(f"  Average Income: ${top_spenders['Annual Income ($)'].mean():,.0f}")
    print(f"  Average Family Size: {top_spenders['Family Size'].mean():.1f}")

    print("\n  Gender Distribution:")
    for gender, count in top_spenders['Gender'].value_counts().items():
        pct = count / len(top_spenders) * 100
        print(f"    {gender}: {count} ({pct:.1f}%)")

    print("\n  Top Professions:")
    for prof, count in top_spenders['Profession'].value_counts().head(5).items():
        pct = count / len(top_spenders) * 100
        print(f"    {prof}: {count} ({pct:.1f}%)")

    print("\n  Age Group Distribution:")
    for age_grp, count in top_spenders['Age_Group'].value_counts().sort_index().items():
        pct = count / len(top_spenders) * 100
        print(f"    {age_grp}: {count} ({pct:.1f}%)")

    return top_spenders

def stakeholder_insights(df, corr_matrix):
    """Generate actionable insights for stakeholders"""
    print("\n" + "=" * 70)
    print("8. KEY STAKEHOLDER INSIGHTS & RECOMMENDATIONS")
    print("=" * 70)

    insights = []

    # Insight 1: Age targeting
    young_spend = df[df['Age'] <= 35]['Spending Score (1-100)'].mean()
    old_spend = df[df['Age'] > 35]['Spending Score (1-100)'].mean()
    if young_spend > old_spend:
        insights.append({
            'finding': f"Younger customers (<=35) have higher spending scores ({young_spend:.1f}) vs older ({old_spend:.1f})",
            'recommendation': "Focus marketing efforts on 18-35 age demographic for higher conversion"
        })

    # Insight 2: Income-Spending relationship
    corr_val = corr_matrix.loc['Annual Income ($)', 'Spending Score (1-100)']
    if abs(corr_val) < 0.3:
        insights.append({
            'finding': f"Income has weak correlation ({corr_val:.2f}) with spending score",
            'recommendation': "Don't exclusively target high-income customers; spending behavior is driven by other factors"
        })

    # Insight 3: High-value segment
    premium = df[df['Segment'] == 'Premium (High Income, High Spend)']
    if len(premium) > 0:
        pct = len(premium) / len(df) * 100
        insights.append({
            'finding': f"Premium segment (high income + high spend) represents {pct:.1f}% of customers",
            'recommendation': "Develop VIP loyalty program to retain this high-value segment"
        })

    # Insight 4: Budget enthusiasts opportunity
    budget_enth = df[df['Segment'] == 'Budget Enthusiast (Low Income, High Spend)']
    if len(budget_enth) > 0:
        pct = len(budget_enth) / len(df) * 100
        insights.append({
            'finding': f"Budget Enthusiasts ({pct:.1f}%) spend heavily despite lower income",
            'recommendation': "Create affordable product lines and financing options for this engaged segment"
        })

    # Insight 5: Careful spenders
    careful = df[df['Segment'] == 'Careful (High Income, Low Spend)']
    if len(careful) > 0:
        pct = len(careful) / len(df) * 100
        insights.append({
            'finding': f"Careful spenders ({pct:.1f}%) have high income but low spending",
            'recommendation': "Implement targeted campaigns emphasizing value and quality for this untapped segment"
        })

    # Insight 6: Top profession
    top_prof = df.groupby('Profession')['Spending Score (1-100)'].mean().idxmax()
    top_prof_score = df.groupby('Profession')['Spending Score (1-100)'].mean().max()
    insights.append({
        'finding': f"{top_prof} profession has highest avg spending score ({top_prof_score:.1f})",
        'recommendation': f"Consider profession-targeted marketing campaigns for {top_prof}s"
    })

    # Insight 7: Gender
    gender_spend = df.groupby('Gender')['Spending Score (1-100)'].mean()
    top_gender = gender_spend.idxmax()
    insights.append({
        'finding': f"{top_gender} customers have slightly higher avg spending ({gender_spend[top_gender]:.1f})",
        'recommendation': f"Ensure marketing mix appeals to {top_gender} demographic while maintaining balance"
    })

    # Insight 8: Family size
    family_corr = corr_matrix.loc['Family Size', 'Spending Score (1-100)']
    insights.append({
        'finding': f"Family size correlation with spending: {family_corr:.2f}",
        'recommendation': "Consider family-oriented promotions and bulk/family packages"
    })

    print("\n")
    for i, insight in enumerate(insights, 1):
        print(f"  INSIGHT {i}:")
        print(f"    Finding: {insight['finding']}")
        print(f"    Recommendation: {insight['recommendation']}")
        print()

    return insights

def generate_summary(df):
    """Generate executive summary"""
    print("\n" + "=" * 70)
    print("EXECUTIVE SUMMARY")
    print("=" * 70)

    print(f"""
  Dataset: {len(df):,} customers analyzed

  Key Metrics:
  - Average Age: {df['Age'].mean():.1f} years
  - Average Income: ${df['Annual Income ($)'].mean():,.0f}
  - Average Spending Score: {df['Spending Score (1-100)'].mean():.1f}/100

  Customer Composition:
  - Gender: {df['Gender'].value_counts().to_dict()}
  - Top 3 Professions: {', '.join(df['Profession'].value_counts().head(3).index.tolist())}

  Strategic Priorities:
  1. Target younger demographics (18-35) for highest spending potential
  2. Develop retention programs for Premium customers
  3. Create value-focused campaigns for Careful spenders (high income, low spend)
  4. Offer accessible options for Budget Enthusiasts (high engagement, low income)
    """)

def save_report(df, insights):
    """Save analysis results to file"""
    # Save segmented data
    df.to_csv('Customers_segmented.csv', index=False)

    # Save summary stats
    summary_stats = df.describe()
    summary_stats.to_csv('summary_statistics.csv')

    print("\n" + "=" * 70)
    print("OUTPUT FILES GENERATED")
    print("=" * 70)
    print("  - Customers_segmented.csv (with segment labels)")
    print("  - summary_statistics.csv (statistical summary)")
    print("  - Analysis report printed above")

def main():
    # Load data
    df = load_data()

    # Run all analyses
    stats = basic_statistics(df)
    df = demographic_analysis(df)
    df = income_analysis(df)
    df = spending_analysis(df)
    corr_matrix = correlation_analysis(df)
    df = customer_segmentation(df)
    top_spenders = high_value_customers(df)
    insights = stakeholder_insights(df, corr_matrix)
    generate_summary(df)
    save_report(df, insights)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
