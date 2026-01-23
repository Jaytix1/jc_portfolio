"""
Customer Data Visualizations - Fun Professional Style
Modern, vibrant charts for stakeholder presentations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as path_effects

# Modern fun color palette - vibrant but professional
COLORS = {
    'coral': '#FF6B6B',
    'teal': '#4ECDC4',
    'purple': '#9B59B6',
    'gold': '#F39C12',
    'blue': '#3498DB',
    'pink': '#E91E63',
    'green': '#2ECC71',
    'orange': '#FF9F43',
    'navy': '#2C3E50',
    'light_gray': '#ECF0F1',
    'dark_gray': '#34495E'
}

SEGMENT_COLORS = ['#4ECDC4', '#FF6B6B', '#F39C12', '#9B59B6', '#3498DB']
GRADIENT_COLORS = ['#667eea', '#764ba2']  # Purple gradient

# Set modern style
plt.rcParams.update({
    'figure.facecolor': '#FAFBFC',
    'axes.facecolor': '#FAFBFC',
    'axes.edgecolor': '#E1E4E8',
    'axes.labelcolor': '#24292E',
    'axes.titlecolor': '#24292E',
    'xtick.color': '#586069',
    'ytick.color': '#586069',
    'grid.color': '#E1E4E8',
    'grid.alpha': 0.6,
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 11,
    'axes.titleweight': 'bold',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

def load_data():
    df = pd.read_csv('Customers_segmented.csv')
    return df

def add_value_labels(ax, bars, fmt='{:.0f}', offset=3, fontsize=10, color='#24292E'):
    """Add value labels on top of bars"""
    for bar in bars:
        height = bar.get_height()
        ax.annotate(fmt.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, offset),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=fontsize, fontweight='bold', color=color)

def create_demographic_charts(df):
    """Create demographic distribution charts with fun style"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.patch.set_facecolor('#FAFBFC')

    # Main title with style
    fig.suptitle('Customer Demographics', fontsize=22, fontweight='bold',
                 color=COLORS['navy'], y=0.98)
    fig.text(0.5, 0.93, 'Who are our customers?', ha='center', fontsize=13,
             color=COLORS['dark_gray'], style='italic')

    # 1. Gender Distribution - Donut Chart
    ax1 = axes[0, 0]
    gender_counts = df['Gender'].value_counts()
    colors = [COLORS['pink'], COLORS['blue']]
    explode = (0.02, 0.02)
    wedges, texts, autotexts = ax1.pie(gender_counts, labels=None,
                                        autopct='%1.1f%%', colors=colors,
                                        explode=explode, startangle=90,
                                        pctdistance=0.75,
                                        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=3))
    for autotext in autotexts:
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    # Custom legend
    ax1.legend(wedges, [f'{g} ({c:,})' for g, c in zip(gender_counts.index, gender_counts.values)],
               loc='center', fontsize=11, frameon=False)
    ax1.set_title('Gender Split', fontweight='bold', pad=20, fontsize=14)

    # 2. Age Distribution - Gradient Histogram
    ax2 = axes[0, 1]
    n, bins, patches = ax2.hist(df['Age'], bins=20, edgecolor='white', linewidth=1.5)

    # Apply gradient colors
    cm = plt.cm.get_cmap('plasma')
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    col = bin_centers - min(bin_centers)
    col /= max(col)
    for c, p in zip(col, patches):
        plt.setp(p, 'facecolor', cm(c))

    ax2.axvline(df['Age'].mean(), color=COLORS['coral'], linestyle='--', linewidth=2.5,
                label=f'Average: {df["Age"].mean():.0f} yrs')
    ax2.set_xlabel('Age', fontweight='bold')
    ax2.set_ylabel('Customers', fontweight='bold')
    ax2.set_title('Age Distribution', fontweight='bold', pad=15)
    ax2.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)

    # 3. Age Groups - Rounded Bar Chart
    ax3 = axes[1, 0]
    age_bins = [0, 25, 35, 45, 55, 100]
    age_labels = ['18-25', '26-35', '36-45', '46-55', '55+']
    df['Age_Group'] = pd.cut(df['Age'], bins=age_bins, labels=age_labels)
    age_dist = df['Age_Group'].value_counts().sort_index()

    bars = ax3.bar(age_dist.index, age_dist.values, color=SEGMENT_COLORS,
                   edgecolor='white', linewidth=2, width=0.7)

    # Add emoji-style labels
    age_emojis = ['Young Adults', 'Early Career', 'Mid Career', 'Senior', 'Experienced']
    for bar, val, emoji in zip(bars, age_dist.values, age_emojis):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f'{val:,}', ha='center', va='bottom', fontweight='bold', fontsize=11)
        ax3.text(bar.get_x() + bar.get_width()/2, -50,
                emoji, ha='center', va='top', fontsize=8, color=COLORS['dark_gray'], rotation=0)

    ax3.set_xlabel('Age Group', fontweight='bold')
    ax3.set_ylabel('Number of Customers', fontweight='bold')
    ax3.set_title('Customers by Age Group', fontweight='bold', pad=15)
    ax3.set_ylim(0, max(age_dist.values) * 1.15)

    # 4. Top Professions - Horizontal Lollipop Chart
    ax4 = axes[1, 1]
    prof_dist = df['Profession'].value_counts().head(8)
    y_pos = np.arange(len(prof_dist))

    # Draw lines
    for i, (prof, val) in enumerate(zip(prof_dist.index[::-1], prof_dist.values[::-1])):
        ax4.hlines(y=i, xmin=0, xmax=val, color=COLORS['light_gray'], linewidth=4)
        ax4.hlines(y=i, xmin=0, xmax=val, color=SEGMENT_COLORS[i % len(SEGMENT_COLORS)],
                   linewidth=4, alpha=0.7)

    # Draw circles at end
    ax4.scatter(prof_dist.values[::-1], y_pos, s=200,
                c=[SEGMENT_COLORS[i % len(SEGMENT_COLORS)] for i in range(len(prof_dist))],
                zorder=3, edgecolor='white', linewidth=2)

    # Add value labels
    for i, val in enumerate(prof_dist.values[::-1]):
        ax4.text(val + 15, i, f'{val:,}', va='center', fontweight='bold', fontsize=10)

    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(prof_dist.index[::-1])
    ax4.set_xlabel('Number of Customers', fontweight='bold')
    ax4.set_title('Top Professions', fontweight='bold', pad=15)
    ax4.set_xlim(0, max(prof_dist.values) * 1.15)

    plt.tight_layout(rect=[0, 0, 1, 0.91])
    plt.savefig('viz_01_demographics.png', dpi=200, bbox_inches='tight', facecolor='#FAFBFC')
    plt.close()
    print("Created: viz_01_demographics.png")

def create_income_charts(df):
    """Create income analysis charts with fun style"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.patch.set_facecolor('#FAFBFC')

    fig.suptitle('Income Analysis', fontsize=22, fontweight='bold',
                 color=COLORS['navy'], y=0.98)
    fig.text(0.5, 0.93, 'Understanding customer earning power', ha='center', fontsize=13,
             color=COLORS['dark_gray'], style='italic')

    # 1. Income Distribution - KDE style
    ax1 = axes[0, 0]
    income_k = df['Annual Income ($)'] / 1000
    n, bins, patches = ax1.hist(income_k, bins=30, density=True, alpha=0.7,
                                 color=COLORS['teal'], edgecolor='white', linewidth=1)

    # Add KDE line
    from scipy.stats import gaussian_kde
    try:
        kde = gaussian_kde(income_k)
        x_range = np.linspace(income_k.min(), income_k.max(), 100)
        ax1.plot(x_range, kde(x_range), color=COLORS['coral'], linewidth=3, label='Density')
    except:
        pass

    ax1.axvline(income_k.mean(), color=COLORS['purple'], linestyle='--', linewidth=2.5,
                label=f'Avg: ${income_k.mean():.0f}K')
    ax1.set_xlabel('Annual Income ($K)', fontweight='bold')
    ax1.set_ylabel('Density', fontweight='bold')
    ax1.set_title('Income Distribution', fontweight='bold', pad=15)
    ax1.legend(frameon=True, fancybox=True)

    # 2. Income Brackets - Fun Pie
    ax2 = axes[0, 1]
    income_brackets = pd.cut(df['Annual Income ($)'],
                             bins=[0, 30000, 60000, 90000, float('inf')],
                             labels=['< $30K', '$30-60K', '$60-90K', '> $90K'])
    bracket_counts = income_brackets.value_counts().sort_index()

    colors_pie = [COLORS['coral'], COLORS['gold'], COLORS['teal'], COLORS['purple']]
    wedges, texts, autotexts = ax2.pie(bracket_counts, labels=None, autopct='%1.1f%%',
                                        colors=colors_pie, startangle=45,
                                        wedgeprops=dict(edgecolor='white', linewidth=2),
                                        pctdistance=0.6)
    for autotext in autotexts:
        autotext.set_fontsize(11)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    ax2.legend(wedges, bracket_counts.index, loc='center left', bbox_to_anchor=(0.85, 0.5),
               fontsize=10, frameon=False)
    ax2.set_title('Income Brackets', fontweight='bold', pad=15)

    # 3. Income by Profession - Gradient bars
    ax3 = axes[1, 0]
    income_by_prof = df.groupby('Profession')['Annual Income ($)'].mean().sort_values() / 1000

    colors_grad = plt.cm.viridis(np.linspace(0.2, 0.9, len(income_by_prof)))
    bars = ax3.barh(income_by_prof.index, income_by_prof.values, color=colors_grad,
                    edgecolor='white', linewidth=1.5, height=0.7)

    ax3.axvline(df['Annual Income ($)'].mean()/1000, color=COLORS['coral'],
                linestyle='--', linewidth=2, alpha=0.7, label='Overall Avg')

    for bar, val in zip(bars, income_by_prof.values):
        ax3.text(val + 1, bar.get_y() + bar.get_height()/2,
                f'${val:.0f}K', va='center', fontweight='bold', fontsize=9)

    ax3.set_xlabel('Average Annual Income ($K)', fontweight='bold')
    ax3.set_title('Income by Profession', fontweight='bold', pad=15)
    ax3.legend(loc='lower right', frameon=True, fancybox=True)

    # 4. Income by Gender - Comparison
    ax4 = axes[1, 1]
    income_gender = df.groupby('Gender')['Annual Income ($)'].agg(['mean', 'median']) / 1000
    x = np.arange(len(income_gender))
    width = 0.35

    bars1 = ax4.bar(x - width/2, income_gender['mean'], width, label='Mean',
                    color=COLORS['blue'], edgecolor='white', linewidth=2)
    bars2 = ax4.bar(x + width/2, income_gender['median'], width, label='Median',
                    color=COLORS['pink'], edgecolor='white', linewidth=2)

    add_value_labels(ax4, bars1, fmt='${:.0f}K', offset=5, fontsize=10)
    add_value_labels(ax4, bars2, fmt='${:.0f}K', offset=5, fontsize=10)

    ax4.set_ylabel('Income ($K)', fontweight='bold')
    ax4.set_title('Income by Gender', fontweight='bold', pad=15)
    ax4.set_xticks(x)
    ax4.set_xticklabels(income_gender.index, fontweight='bold')
    ax4.legend(frameon=True, fancybox=True)
    ax4.set_ylim(0, 140)

    plt.tight_layout(rect=[0, 0, 1, 0.91])
    plt.savefig('viz_02_income.png', dpi=200, bbox_inches='tight', facecolor='#FAFBFC')
    plt.close()
    print("Created: viz_02_income.png")

def create_spending_charts(df):
    """Create spending behavior charts with fun style"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.patch.set_facecolor('#FAFBFC')

    fig.suptitle('Spending Behavior', fontsize=22, fontweight='bold',
                 color=COLORS['navy'], y=0.98)
    fig.text(0.5, 0.93, 'How do customers spend?', ha='center', fontsize=13,
             color=COLORS['dark_gray'], style='italic')

    # 1. Spending Score Distribution
    ax1 = axes[0, 0]
    n, bins, patches = ax1.hist(df['Spending Score (1-100)'], bins=20,
                                 edgecolor='white', linewidth=1.5)

    # Gradient coloring
    cm = plt.cm.get_cmap('RdYlGn')
    for i, (patch, b) in enumerate(zip(patches, bins[:-1])):
        patch.set_facecolor(cm(b / 100))

    ax1.axvline(df['Spending Score (1-100)'].mean(), color=COLORS['navy'],
                linestyle='--', linewidth=2.5, label=f'Avg: {df["Spending Score (1-100)"].mean():.1f}')
    ax1.set_xlabel('Spending Score', fontweight='bold')
    ax1.set_ylabel('Number of Customers', fontweight='bold')
    ax1.set_title('Spending Score Distribution', fontweight='bold', pad=15)
    ax1.legend(frameon=True, fancybox=True)

    # 2. Spending Categories - Semi-circle
    ax2 = axes[0, 1]
    spend_cat = pd.cut(df['Spending Score (1-100)'], bins=[0, 33, 66, 100],
                       labels=['Low Spenders', 'Medium Spenders', 'High Spenders'])
    cat_counts = spend_cat.value_counts().sort_index()

    colors_cat = [COLORS['coral'], COLORS['gold'], COLORS['green']]
    wedges, texts, autotexts = ax2.pie(cat_counts, labels=None, autopct='%1.1f%%',
                                        colors=colors_cat, startangle=90,
                                        wedgeprops=dict(width=0.6, edgecolor='white', linewidth=3),
                                        pctdistance=0.75)
    for autotext in autotexts:
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')

    ax2.legend(wedges, [f'{cat} ({cnt:,})' for cat, cnt in zip(cat_counts.index, cat_counts.values)],
               loc='center', fontsize=10, frameon=False)
    ax2.set_title('Spending Categories', fontweight='bold', pad=15)

    # 3. Spending by Age Group - Highlight best
    ax3 = axes[1, 0]
    age_bins = [0, 25, 35, 45, 55, 100]
    age_labels = ['18-25', '26-35', '36-45', '46-55', '55+']
    df['Age_Group'] = pd.cut(df['Age'], bins=age_bins, labels=age_labels)
    spend_by_age = df.groupby('Age_Group')['Spending Score (1-100)'].mean()

    max_idx = spend_by_age.values.argmax()
    colors_age = [COLORS['teal'] if i == max_idx else COLORS['light_gray']
                  for i in range(len(spend_by_age))]

    bars = ax3.bar(spend_by_age.index, spend_by_age.values, color=colors_age,
                   edgecolor='white', linewidth=2, width=0.6)

    for i, (bar, val) in enumerate(zip(bars, spend_by_age.values)):
        color = 'white' if i == max_idx else COLORS['dark_gray']
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 5,
                f'{val:.1f}', ha='center', va='top', fontweight='bold',
                fontsize=12, color=color)

    # Highlight annotation
    ax3.annotate('Highest!', xy=(0, spend_by_age.values[0]),
                xytext=(0.5, spend_by_age.values[0] + 8),
                fontsize=11, fontweight='bold', color=COLORS['coral'],
                arrowprops=dict(arrowstyle='->', color=COLORS['coral'], lw=2))

    ax3.set_xlabel('Age Group', fontweight='bold')
    ax3.set_ylabel('Average Spending Score', fontweight='bold')
    ax3.set_title('Spending by Age Group', fontweight='bold', pad=15)
    ax3.set_ylim(0, 70)

    # 4. Spending by Profession - Lollipop
    ax4 = axes[1, 1]
    spend_by_prof = df.groupby('Profession')['Spending Score (1-100)'].mean().sort_values()
    y_pos = np.arange(len(spend_by_prof))

    colors_prof = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(spend_by_prof)))

    ax4.hlines(y=y_pos, xmin=0, xmax=spend_by_prof.values, color=colors_prof, linewidth=3)
    ax4.scatter(spend_by_prof.values, y_pos, c=colors_prof, s=150, zorder=3,
                edgecolor='white', linewidth=2)

    ax4.axvline(df['Spending Score (1-100)'].mean(), color=COLORS['navy'],
                linestyle='--', linewidth=2, alpha=0.5, label='Average')

    for i, val in enumerate(spend_by_prof.values):
        ax4.text(val + 0.8, i, f'{val:.1f}', va='center', fontsize=9, fontweight='bold')

    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(spend_by_prof.index)
    ax4.set_xlabel('Average Spending Score', fontweight='bold')
    ax4.set_title('Spending by Profession', fontweight='bold', pad=15)
    ax4.legend(loc='lower right', frameon=True, fancybox=True)

    plt.tight_layout(rect=[0, 0, 1, 0.91])
    plt.savefig('viz_03_spending.png', dpi=200, bbox_inches='tight', facecolor='#FAFBFC')
    plt.close()
    print("Created: viz_03_spending.png")

def create_segmentation_chart(df):
    """Create customer segmentation scatter plot with fun style"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    fig.patch.set_facecolor('#FAFBFC')

    fig.suptitle('Customer Segmentation', fontsize=22, fontweight='bold',
                 color=COLORS['navy'], y=0.98)
    fig.text(0.5, 0.92, '5 distinct customer personas identified', ha='center', fontsize=13,
             color=COLORS['dark_gray'], style='italic')

    segment_colors = {
        'Premium (High Income, High Spend)': COLORS['teal'],
        'Careful (High Income, Low Spend)': COLORS['pink'],
        'Standard (Middle)': COLORS['gold'],
        'Budget Enthusiast (Low Income, High Spend)': COLORS['coral'],
        'Conservative (Low Income, Low Spend)': COLORS['purple']
    }

    segment_labels = {
        'Premium (High Income, High Spend)': 'Premium',
        'Careful (High Income, Low Spend)': 'Careful',
        'Standard (Middle)': 'Standard',
        'Budget Enthusiast (Low Income, High Spend)': 'Budget Enthusiast',
        'Conservative (Low Income, Low Spend)': 'Conservative'
    }

    # 1. Scatter plot
    ax1 = axes[0]
    for segment in df['Segment'].unique():
        segment_data = df[df['Segment'] == segment]
        ax1.scatter(segment_data['Annual Income ($)'] / 1000,
                   segment_data['Spending Score (1-100)'],
                   c=segment_colors.get(segment, 'gray'),
                   label=segment_labels.get(segment, segment),
                   alpha=0.6, s=50, edgecolor='white', linewidth=0.5)

    ax1.set_xlabel('Annual Income ($K)', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Spending Score', fontweight='bold', fontsize=12)
    ax1.set_title('Income vs Spending by Segment', fontweight='bold', pad=15)

    # Add quadrant labels
    ax1.axhline(y=50, color=COLORS['dark_gray'], linestyle='--', alpha=0.3, linewidth=1.5)
    ax1.axvline(x=df['Annual Income ($)'].median()/1000, color=COLORS['dark_gray'],
                linestyle='--', alpha=0.3, linewidth=1.5)

    # Quadrant annotations
    ax1.text(160, 90, 'High Value', fontsize=10, fontweight='bold',
             color=COLORS['teal'], alpha=0.8)
    ax1.text(160, 15, 'Untapped\nPotential', fontsize=10, fontweight='bold',
             color=COLORS['pink'], alpha=0.8, ha='center')
    ax1.text(20, 90, 'Engaged\nBudget', fontsize=10, fontweight='bold',
             color=COLORS['coral'], alpha=0.8, ha='center')
    ax1.text(20, 15, 'Low\nPriority', fontsize=10, fontweight='bold',
             color=COLORS['purple'], alpha=0.8, ha='center')

    ax1.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=10,
               frameon=True, fancybox=True, shadow=True)

    # 2. Segment sizes - Horizontal bars with icons
    ax2 = axes[1]
    segment_counts = df['Segment'].value_counts()
    segment_short = [segment_labels.get(s, s) for s in segment_counts.index]
    colors_bar = [segment_colors.get(s, 'gray') for s in segment_counts.index]

    bars = ax2.barh(segment_short[::-1], segment_counts.values[::-1],
                    color=colors_bar[::-1], edgecolor='white', linewidth=2, height=0.6)

    for bar, val in zip(bars, segment_counts.values[::-1]):
        pct = val / len(df) * 100
        ax2.text(val + 15, bar.get_y() + bar.get_height()/2,
                f'{val:,} ({pct:.1f}%)', va='center', fontweight='bold', fontsize=11)

    ax2.set_xlabel('Number of Customers', fontweight='bold', fontsize=12)
    ax2.set_title('Segment Distribution', fontweight='bold', pad=15)
    ax2.set_xlim(0, max(segment_counts.values) * 1.25)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    plt.savefig('viz_04_segmentation.png', dpi=200, bbox_inches='tight', facecolor='#FAFBFC')
    plt.close()
    print("Created: viz_04_segmentation.png")

def create_correlation_heatmap(df):
    """Create correlation heatmap with fun style"""
    fig, ax = plt.subplots(figsize=(10, 9))
    fig.patch.set_facecolor('#FAFBFC')

    numeric_cols = ['Age', 'Annual Income ($)', 'Spending Score (1-100)',
                    'Work Experience', 'Family Size']
    corr_matrix = df[numeric_cols].corr()

    # Custom colormap
    im = ax.imshow(corr_matrix, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('Correlation', rotation=270, labelpad=20, fontweight='bold')

    # Labels
    short_labels = ['Age', 'Income', 'Spending', 'Experience', 'Family']
    ax.set_xticks(np.arange(len(numeric_cols)))
    ax.set_yticks(np.arange(len(numeric_cols)))
    ax.set_xticklabels(short_labels, rotation=45, ha='right', fontweight='bold')
    ax.set_yticklabels(short_labels, fontweight='bold')

    # Add values with styling
    for i in range(len(numeric_cols)):
        for j in range(len(numeric_cols)):
            val = corr_matrix.iloc[i, j]
            color = 'white' if abs(val) > 0.5 else COLORS['dark_gray']
            text = ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                          color=color, fontweight='bold', fontsize=13)

    ax.set_title('Correlation Matrix', fontweight='bold', fontsize=18, pad=20,
                 color=COLORS['navy'])

    # Add insight box
    insight_text = "Key Finding: Income has almost NO correlation\nwith Spending Score (0.02)"
    props = dict(boxstyle='round,pad=0.5', facecolor=COLORS['gold'], alpha=0.3)
    ax.text(0.5, -0.15, insight_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', ha='center', bbox=props, fontweight='bold')

    plt.tight_layout()
    plt.savefig('viz_05_correlations.png', dpi=200, bbox_inches='tight', facecolor='#FAFBFC')
    plt.close()
    print("Created: viz_05_correlations.png")

def create_high_value_profile(df):
    """Create high-value customer profile with fun style"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.patch.set_facecolor('#FAFBFC')

    fig.suptitle('High-Value Customer Profile', fontsize=22, fontweight='bold',
                 color=COLORS['navy'], y=0.98)
    fig.text(0.5, 0.93, 'Who are our top 20% spenders?', ha='center', fontsize=13,
             color=COLORS['dark_gray'], style='italic')

    threshold = df['Spending Score (1-100)'].quantile(0.8)
    top_spenders = df[df['Spending Score (1-100)'] >= threshold]
    others = df[df['Spending Score (1-100)'] < threshold]

    # 1. Key metrics comparison
    ax1 = axes[0, 0]
    metrics = ['Age', 'Income ($K)', 'Spending', 'Family']
    top_vals = [top_spenders['Age'].mean(), top_spenders['Annual Income ($)'].mean()/1000,
                top_spenders['Spending Score (1-100)'].mean(), top_spenders['Family Size'].mean()]
    other_vals = [others['Age'].mean(), others['Annual Income ($)'].mean()/1000,
                  others['Spending Score (1-100)'].mean(), others['Family Size'].mean()]

    x = np.arange(len(metrics))
    width = 0.35

    bars1 = ax1.bar(x - width/2, top_vals, width, label='Top 20%',
                    color=COLORS['teal'], edgecolor='white', linewidth=2)
    bars2 = ax1.bar(x + width/2, other_vals, width, label='Others',
                    color=COLORS['light_gray'], edgecolor=COLORS['dark_gray'], linewidth=1)

    ax1.set_ylabel('Value', fontweight='bold')
    ax1.set_title('Top Spenders vs Others', fontweight='bold', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics, fontweight='bold')
    ax1.legend(frameon=True, fancybox=True, loc='upper right')

    # 2. Gender comparison
    ax2 = axes[0, 1]
    gender_data = pd.DataFrame({
        'Top 20%': [top_spenders['Gender'].value_counts().get('Female', 0)/len(top_spenders)*100,
                    top_spenders['Gender'].value_counts().get('Male', 0)/len(top_spenders)*100],
        'Others': [others['Gender'].value_counts().get('Female', 0)/len(others)*100,
                   others['Gender'].value_counts().get('Male', 0)/len(others)*100]
    }, index=['Female', 'Male'])

    x = np.arange(2)
    bars1 = ax2.bar(x - width/2, gender_data['Top 20%'], width, label='Top 20%',
                    color=COLORS['pink'], edgecolor='white', linewidth=2)
    bars2 = ax2.bar(x + width/2, gender_data['Others'], width, label='Others',
                    color=COLORS['light_gray'], edgecolor=COLORS['dark_gray'], linewidth=1)

    add_value_labels(ax2, bars1, fmt='{:.1f}%', offset=3)
    add_value_labels(ax2, bars2, fmt='{:.1f}%', offset=3)

    ax2.set_ylabel('Percentage', fontweight='bold')
    ax2.set_title('Gender Distribution', fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(['Female', 'Male'], fontweight='bold')
    ax2.legend(frameon=True, fancybox=True)
    ax2.set_ylim(0, 75)

    # 3. Top professions
    ax3 = axes[1, 0]
    top_prof = top_spenders['Profession'].value_counts().head(6)
    colors_prof = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_prof)))[::-1]

    bars = ax3.barh(top_prof.index[::-1], top_prof.values[::-1],
                    color=colors_prof, edgecolor='white', linewidth=2, height=0.6)

    for bar, val in zip(bars, top_prof.values[::-1]):
        pct = val / len(top_spenders) * 100
        ax3.text(val + 3, bar.get_y() + bar.get_height()/2,
                f'{val} ({pct:.1f}%)', va='center', fontweight='bold', fontsize=10)

    ax3.set_xlabel('Number of Customers', fontweight='bold')
    ax3.set_title('Top Professions in High-Value Segment', fontweight='bold', pad=15)
    ax3.set_xlim(0, max(top_prof.values) * 1.3)

    # 4. Age distribution
    ax4 = axes[1, 1]
    age_bins = [0, 25, 35, 45, 55, 100]
    age_labels = ['18-25', '26-35', '36-45', '46-55', '55+']

    top_copy = top_spenders.copy()
    other_copy = others.copy()
    top_copy['Age_Group'] = pd.cut(top_copy['Age'], bins=age_bins, labels=age_labels)
    other_copy['Age_Group'] = pd.cut(other_copy['Age'], bins=age_bins, labels=age_labels)

    top_age = top_copy['Age_Group'].value_counts().sort_index()
    other_age = other_copy['Age_Group'].value_counts().sort_index()

    x = np.arange(len(age_labels))
    ax4.bar(x - width/2, [top_age.get(l, 0)/len(top_spenders)*100 for l in age_labels],
            width, label='Top 20%', color=COLORS['teal'], edgecolor='white', linewidth=2)
    ax4.bar(x + width/2, [other_age.get(l, 0)/len(others)*100 for l in age_labels],
            width, label='Others', color=COLORS['light_gray'], edgecolor=COLORS['dark_gray'], linewidth=1)

    ax4.set_ylabel('Percentage', fontweight='bold')
    ax4.set_xlabel('Age Group', fontweight='bold')
    ax4.set_title('Age Distribution Comparison', fontweight='bold', pad=15)
    ax4.set_xticks(x)
    ax4.set_xticklabels(age_labels, fontweight='bold')
    ax4.legend(frameon=True, fancybox=True)

    plt.tight_layout(rect=[0, 0, 1, 0.91])
    plt.savefig('viz_06_high_value.png', dpi=200, bbox_inches='tight', facecolor='#FAFBFC')
    plt.close()
    print("Created: viz_06_high_value.png")

def create_executive_dashboard(df):
    """Create executive dashboard with fun professional style"""
    fig = plt.figure(figsize=(18, 13))
    fig.patch.set_facecolor('#FAFBFC')

    # Title
    fig.text(0.5, 0.96, 'CUSTOMER ANALYTICS DASHBOARD', ha='center', fontsize=26,
             fontweight='bold', color=COLORS['navy'])
    fig.text(0.5, 0.925, 'Key insights from 1,998 customers', ha='center', fontsize=14,
             color=COLORS['dark_gray'], style='italic')

    # Main grid with proper margins for centering
    gs = fig.add_gridspec(3, 4, hspace=0.35, wspace=0.25,
                          top=0.88, bottom=0.06, left=0.06, right=0.94)

    # KPI Cards
    kpis = [
        ('Total Customers', f'{len(df):,}', COLORS['teal'], 'Users analyzed'),
        ('Avg Income', f'${df["Annual Income ($)"].mean()/1000:.0f}K', COLORS['purple'], 'Per year'),
        ('Spending Score', f'{df["Spending Score (1-100)"].mean():.0f}/100', COLORS['gold'], 'Average'),
        ('Premium Segment', f'{len(df[df["Segment"].str.contains("Premium")])/len(df)*100:.0f}%', COLORS['coral'], 'High value')
    ]

    for i, (label, value, color, subtitle) in enumerate(kpis):
        ax = fig.add_subplot(gs[0, i])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        # Card background
        card = FancyBboxPatch((0.08, 0.08), 0.84, 0.84, boxstyle="round,pad=0.02,rounding_size=0.05",
                               facecolor='white', edgecolor=color, linewidth=3)
        ax.add_patch(card)

        # Colored accent bar
        accent = plt.Rectangle((0.08, 0.78), 0.84, 0.14, facecolor=color, alpha=0.8)
        ax.add_patch(accent)

        ax.text(0.5, 0.52, value, ha='center', va='center', fontsize=26,
                fontweight='bold', color=color)
        ax.text(0.5, 0.28, label, ha='center', va='center', fontsize=11,
                fontweight='bold', color=COLORS['dark_gray'])
        ax.text(0.5, 0.15, subtitle, ha='center', va='center', fontsize=9,
                color=COLORS['dark_gray'], alpha=0.7)
        ax.axis('off')

    # Segment Distribution
    ax_seg = fig.add_subplot(gs[1, :2])
    segment_counts = df['Segment'].value_counts()
    segment_short = [s.split('(')[0].strip() for s in segment_counts.index]
    colors_seg = [COLORS['teal'], COLORS['pink'], COLORS['gold'], COLORS['coral'], COLORS['purple']]

    bars = ax_seg.barh(segment_short[::-1], segment_counts.values[::-1],
                       color=colors_seg[::-1], edgecolor='white', linewidth=2, height=0.6)
    for bar, val in zip(bars, segment_counts.values[::-1]):
        ax_seg.text(val + 15, bar.get_y() + bar.get_height()/2,
                   f'{val:,} ({val/len(df)*100:.1f}%)', va='center',
                   fontweight='bold', fontsize=10)
    ax_seg.set_title('Customer Segments', fontweight='bold', fontsize=14, pad=10)
    ax_seg.set_xlim(0, max(segment_counts.values) * 1.25)

    # Scatter plot
    ax_scatter = fig.add_subplot(gs[1, 2:])
    segment_colors_map = {
        'Premium (High Income, High Spend)': COLORS['teal'],
        'Careful (High Income, Low Spend)': COLORS['pink'],
        'Standard (Middle)': COLORS['gold'],
        'Budget Enthusiast (Low Income, High Spend)': COLORS['coral'],
        'Conservative (Low Income, Low Spend)': COLORS['purple']
    }
    for segment in df['Segment'].unique():
        segment_data = df[df['Segment'] == segment]
        ax_scatter.scatter(segment_data['Annual Income ($)'] / 1000,
                          segment_data['Spending Score (1-100)'],
                          c=segment_colors_map.get(segment, 'gray'),
                          alpha=0.5, s=25, edgecolor='white', linewidth=0.3)
    ax_scatter.set_xlabel('Income ($K)', fontweight='bold')
    ax_scatter.set_ylabel('Spending Score', fontweight='bold')
    ax_scatter.set_title('Income vs Spending', fontweight='bold', fontsize=14, pad=10)
    ax_scatter.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
    ax_scatter.axvline(x=df['Annual Income ($)'].median()/1000, color='gray', linestyle='--', alpha=0.3)

    # Spending by Profession
    ax_prof = fig.add_subplot(gs[2, :2])
    spend_prof = df.groupby('Profession')['Spending Score (1-100)'].mean().sort_values()
    colors_bar = [COLORS['teal'] if v == spend_prof.max() else COLORS['light_gray']
                  for v in spend_prof.values]
    ax_prof.barh(spend_prof.index, spend_prof.values, color=colors_bar,
                 edgecolor='white', linewidth=1, height=0.6)
    ax_prof.axvline(x=df['Spending Score (1-100)'].mean(), color=COLORS['coral'],
                    linestyle='--', linewidth=2, alpha=0.7)
    ax_prof.set_xlabel('Avg Spending Score', fontweight='bold')
    ax_prof.set_title('Spending by Profession', fontweight='bold', fontsize=14, pad=10)

    # Spending by Age
    ax_age = fig.add_subplot(gs[2, 2:])
    age_bins = [0, 25, 35, 45, 55, 100]
    age_labels = ['18-25', '26-35', '36-45', '46-55', '55+']
    df_temp = df.copy()
    df_temp['Age_Group'] = pd.cut(df_temp['Age'], bins=age_bins, labels=age_labels)
    spend_age = df_temp.groupby('Age_Group')['Spending Score (1-100)'].mean()

    max_idx = spend_age.values.argmax()
    colors_age = [COLORS['teal'] if i == max_idx else COLORS['light_gray']
                  for i in range(len(spend_age))]
    bars = ax_age.bar(spend_age.index, spend_age.values, color=colors_age,
                      edgecolor='white', linewidth=2, width=0.6)
    for bar, val in zip(bars, spend_age.values):
        ax_age.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{val:.1f}', ha='center', fontsize=10, fontweight='bold')
    ax_age.set_ylabel('Avg Spending Score', fontweight='bold')
    ax_age.set_title('Spending by Age Group', fontweight='bold', fontsize=14, pad=10)
    ax_age.set_ylim(0, 65)

    plt.savefig('viz_00_dashboard.png', dpi=200, facecolor='#FAFBFC',
                pad_inches=0.2, bbox_inches='tight')
    plt.close()
    print("Created: viz_00_dashboard.png")

def main():
    print("=" * 60)
    print("  GENERATING FUN PROFESSIONAL VISUALIZATIONS")
    print("=" * 60)

    df = load_data()
    print(f"\n  Loaded {len(df):,} customer records")
    print("\n  Creating visualizations...\n")

    create_executive_dashboard(df)
    create_demographic_charts(df)
    create_income_charts(df)
    create_spending_charts(df)
    create_segmentation_chart(df)
    create_correlation_heatmap(df)
    create_high_value_profile(df)

    print("\n" + "=" * 60)
    print("  VISUALIZATION COMPLETE!")
    print("=" * 60)
    print("""
  Generated files:
    viz_00_dashboard.png    - Executive Dashboard
    viz_01_demographics.png - Demographics Overview
    viz_02_income.png       - Income Analysis
    viz_03_spending.png     - Spending Behavior
    viz_04_segmentation.png - Customer Segments
    viz_05_correlations.png - Correlation Heatmap
    viz_06_high_value.png   - High-Value Profile
    """)

if __name__ == "__main__":
    main()
