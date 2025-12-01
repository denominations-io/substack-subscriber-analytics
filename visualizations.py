"""
Visualization module for Substack analytics.
Uses seaborn and matplotlib to create charts and graphs.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def setup_style():
    """Set up consistent visualization style."""
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12


def plot_subscriber_growth(subscribers: pd.DataFrame, output_dir: Path) -> str:
    """Plot cumulative subscriber growth over time."""
    setup_style()

    subscribers['signup_month'] = subscribers['created_at'].dt.to_period('M')
    monthly = subscribers.groupby('signup_month').size()
    cumulative = monthly.cumsum()

    fig, ax = plt.subplots(figsize=(14, 6))

    # Convert Period index to datetime for plotting
    x_dates = cumulative.index.to_timestamp()

    ax.fill_between(x_dates, cumulative.values, alpha=0.3, color='steelblue')
    ax.plot(x_dates, cumulative.values, color='steelblue', linewidth=2, marker='o', markersize=4)

    ax.set_title('Cumulative Subscriber Growth', fontsize=16, fontweight='bold')
    ax.set_xlabel('Month')
    ax.set_ylabel('Total Subscribers')

    # Add annotations for key milestones
    max_subs = cumulative.max()
    ax.axhline(y=max_subs, color='green', linestyle='--', alpha=0.5, label=f'Current: {max_subs}')

    plt.xticks(rotation=45)
    plt.tight_layout()

    filepath = output_dir / 'subscriber_growth.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def plot_monthly_signups(subscribers: pd.DataFrame, output_dir: Path) -> str:
    """Plot monthly new subscriber signups with paid vs free breakdown."""
    setup_style()

    subscribers['signup_month'] = subscribers['created_at'].dt.to_period('M')

    # Group by month and paid status
    monthly_breakdown = subscribers.groupby(['signup_month', 'is_paid']).size().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(14, 6))

    x = np.arange(len(monthly_breakdown))
    width = 0.6

    if True in monthly_breakdown.columns and False in monthly_breakdown.columns:
        ax.bar(x, monthly_breakdown[False], width, label='Free', color='lightsteelblue')
        ax.bar(x, monthly_breakdown[True], width, bottom=monthly_breakdown[False],
               label='Paid', color='coral')
    elif False in monthly_breakdown.columns:
        ax.bar(x, monthly_breakdown[False], width, label='Free', color='lightsteelblue')

    ax.set_title('Monthly New Subscribers (Free vs Paid)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Month')
    ax.set_ylabel('New Subscribers')
    ax.set_xticks(x[::2])  # Show every other month
    ax.set_xticklabels([str(m) for m in monthly_breakdown.index[::2]], rotation=45)
    ax.legend()

    plt.tight_layout()

    filepath = output_dir / 'monthly_signups.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def plot_open_rates_by_post(engagement: pd.DataFrame, output_dir: Path) -> str:
    """Plot open rates for each post with benchmarks."""
    setup_style()

    # Filter to posts with meaningful data and sort by date
    df = engagement[engagement['delivered'] >= 50].copy()
    df = df.sort_values('post_date')

    if df.empty:
        return ""

    fig, ax = plt.subplots(figsize=(16, 8))

    colors = ['green' if r >= 0.45 else 'steelblue' if r >= 0.30 else 'orange' if r >= 0.20 else 'red'
              for r in df['open_rate']]

    bars = ax.barh(range(len(df)), df['open_rate'] * 100, color=colors, alpha=0.8)

    # Add benchmark lines
    ax.axvline(x=45, color='green', linestyle='--', alpha=0.7, label='Excellent (45%)')
    ax.axvline(x=30, color='steelblue', linestyle='--', alpha=0.7, label='Good (30%)')
    ax.axvline(x=20, color='orange', linestyle='--', alpha=0.7, label='Average (20%)')

    # Truncate titles for readability
    titles = [t[:40] + '...' if len(t) > 40 else t for t in df['title']]
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(titles, fontsize=8)

    ax.set_xlabel('Open Rate (%)')
    ax.set_title('Open Rates by Post (with Benchmarks)', fontsize=16, fontweight='bold')
    ax.legend(loc='lower right')

    plt.tight_layout()

    filepath = output_dir / 'open_rates_by_post.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def plot_engagement_distribution(engagement: pd.DataFrame, output_dir: Path) -> str:
    """Plot distribution of open rates across all posts."""
    setup_style()

    df = engagement[engagement['delivered'] >= 50].copy()

    if df.empty:
        return ""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram
    ax1 = axes[0]
    sns.histplot(df['open_rate'] * 100, bins=15, kde=True, ax=ax1, color='steelblue')
    ax1.axvline(x=45, color='green', linestyle='--', label='Excellent (45%)')
    ax1.axvline(x=30, color='orange', linestyle='--', label='Good (30%)')
    ax1.set_xlabel('Open Rate (%)')
    ax1.set_ylabel('Number of Posts')
    ax1.set_title('Distribution of Open Rates')
    ax1.legend()

    # Box plot by audience type
    ax2 = axes[1]
    if 'audience' in df.columns and df['audience'].nunique() > 1:
        sns.boxplot(x='audience', y=df['open_rate'] * 100, data=df, ax=ax2, palette='Set2')
        ax2.set_xlabel('Audience')
        ax2.set_ylabel('Open Rate (%)')
        ax2.set_title('Open Rates by Audience Type')
    else:
        sns.boxplot(y=df['open_rate'] * 100, ax=ax2, color='steelblue')
        ax2.set_ylabel('Open Rate (%)')
        ax2.set_title('Open Rate Distribution')

    plt.tight_layout()

    filepath = output_dir / 'engagement_distribution.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def plot_conversion_funnel(subscribers: pd.DataFrame, output_dir: Path) -> str:
    """Plot conversion funnel from subscriber to paid."""
    setup_style()

    total = len(subscribers)
    active = len(subscribers[subscribers['email_disabled'] == False])
    paid_ever = len(subscribers[subscribers['is_paid'] == True])
    active_paid = len(subscribers[subscribers['is_active_paid'] == True])

    stages = ['Total Subscribers', 'Active (not disabled)', 'Ever Paid', 'Currently Paid']
    values = [total, active, paid_ever, active_paid]
    percentages = [100, active/total*100, paid_ever/total*100, active_paid/total*100]

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = sns.color_palette('Blues_r', n_colors=4)
    bars = ax.barh(stages[::-1], values[::-1], color=colors)

    # Add value labels
    for bar, val, pct in zip(bars, values[::-1], percentages[::-1]):
        ax.text(bar.get_width() + max(values)*0.02, bar.get_y() + bar.get_height()/2,
                f'{val:,} ({pct:.1f}%)', va='center', fontsize=11)

    ax.set_xlabel('Number of Subscribers')
    ax.set_title('Subscriber Conversion Funnel', fontsize=16, fontweight='bold')
    ax.set_xlim(0, max(values) * 1.3)

    plt.tight_layout()

    filepath = output_dir / 'conversion_funnel.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def plot_monthly_engagement_trend(trends: Dict[str, Any], output_dir: Path) -> str:
    """Plot monthly engagement trend (open rates over time)."""
    setup_style()

    monthly = trends['monthly_engagement']
    if monthly.empty:
        return ""

    fig, ax = plt.subplots(figsize=(14, 6))

    x_dates = monthly.index.to_timestamp()

    ax.plot(x_dates, monthly['open_rate'] * 100, color='steelblue',
            linewidth=2, marker='o', markersize=6, label='Open Rate')

    # Add benchmark lines
    ax.axhline(y=45, color='green', linestyle='--', alpha=0.5, label='Excellent (45%)')
    ax.axhline(y=30, color='orange', linestyle='--', alpha=0.5, label='Good (30%)')

    ax.fill_between(x_dates, monthly['open_rate'] * 100, alpha=0.2, color='steelblue')

    ax.set_xlabel('Month')
    ax.set_ylabel('Open Rate (%)')
    ax.set_title('Monthly Open Rate Trend', fontsize=16, fontweight='bold')
    ax.legend(loc='upper right')

    plt.xticks(rotation=45)
    plt.tight_layout()

    filepath = output_dir / 'monthly_engagement_trend.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def plot_top_converting_posts(conversion: Dict[str, Any], output_dir: Path) -> str:
    """Plot top posts by conversion attribution."""
    setup_style()

    df = conversion['conversion_posts']
    if df.empty:
        return ""

    # Top 10 posts by conversions
    top = df.head(10).copy()

    fig, ax = plt.subplots(figsize=(12, 8))

    colors = sns.color_palette('YlOrRd', n_colors=len(top))[::-1]
    bars = ax.barh(range(len(top)), top['conversions'], color=colors)

    # Truncate titles
    titles = [t[:45] + '...' if len(t) > 45 else t for t in top['title']]
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(titles, fontsize=9)

    # Add value labels
    for bar, val in zip(bars, top['conversions']):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                f'{val}', va='center', fontsize=10)

    ax.set_xlabel('Conversions Attributed')
    ax.set_title('Top Posts Driving Free-to-Paid Conversions', fontsize=16, fontweight='bold')

    plt.tight_layout()

    filepath = output_dir / 'top_converting_posts.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def plot_signup_day_distribution(acquisition: Dict[str, Any], output_dir: Path) -> str:
    """Plot signup distribution by day of week."""
    setup_style()

    dow = acquisition['dow_distribution']

    # Order days correctly
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    ordered = {d: dow.get(d, 0) for d in day_order}

    fig, ax = plt.subplots(figsize=(10, 5))

    colors = sns.color_palette('viridis', n_colors=7)
    bars = ax.bar(ordered.keys(), ordered.values(), color=colors)

    ax.set_xlabel('Day of Week')
    ax.set_ylabel('Number of Signups')
    ax.set_title('Subscriber Signups by Day of Week', fontsize=16, fontweight='bold')

    # Highlight peak day
    peak_day = max(ordered, key=ordered.get)
    ax.annotate(f'Peak: {peak_day}', xy=(list(ordered.keys()).index(peak_day), ordered[peak_day]),
                xytext=(0, 10), textcoords='offset points', ha='center', fontsize=10,
                color='darkgreen', fontweight='bold')

    plt.tight_layout()

    filepath = output_dir / 'signup_day_distribution.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def plot_engagement_segments(super_engagers: Dict[str, Any], output_dir: Path) -> str:
    """Plot subscriber engagement segments."""
    setup_style()

    total = super_engagers['total_analyzed']
    super_count = super_engagers['super_engager_count']
    at_risk = super_engagers['at_risk_count']
    average = total - super_count - at_risk

    if total == 0:
        return ""

    fig, ax = plt.subplots(figsize=(10, 8))

    sizes = [super_count, average, at_risk]
    labels = [
        f'Super Engagers\n(80%+ open rate)\n{super_count} ({super_count/total*100:.1f}%)',
        f'Average\n{average} ({average/total*100:.1f}%)',
        f'At Risk\n(<20% open rate)\n{at_risk} ({at_risk/total*100:.1f}%)'
    ]
    colors = ['#2ecc71', '#3498db', '#e74c3c']
    explode = (0.05, 0, 0.05)

    ax.pie(sizes, labels=labels, colors=colors, explode=explode,
           autopct='', startangle=90, textprops={'fontsize': 11})

    ax.set_title('Subscriber Engagement Segments', fontsize=16, fontweight='bold')

    plt.tight_layout()

    filepath = output_dir / 'engagement_segments.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def plot_metrics_dashboard(metrics: Dict[str, Any], output_dir: Path) -> str:
    """Create a dashboard-style visualization of key metrics."""
    setup_style()

    fig = plt.figure(figsize=(16, 10))

    # Create grid
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

    # Metric cards
    metric_data = [
        ('Open Rate', metrics['open_rate']['percentage'], metrics['open_rate']['rating']),
        ('Free-to-Paid', metrics['conversion_rate']['percentage'], metrics['conversion_rate']['rating']),
        ('List Growth (1mo)', metrics['list_growth_1mo']['percentage'], metrics['list_growth_1mo']['rating']),
        ('List Growth (3mo)', metrics['list_growth_3mo']['percentage'], metrics['list_growth_3mo']['rating']),
        ('Paid Churn', metrics['paid_churn']['percentage'], metrics['paid_churn']['rating']),
    ]

    colors = {
        'Excellent': '#2ecc71',
        'Very Good': '#27ae60',
        'Good': '#3498db',
        'Realistic/Good': '#3498db',
        'Average': '#f39c12',
        'Slow': '#e67e22',
        'Below average': '#e74c3c',
        'Poor': '#c0392b',
        'Excellent (niche-level)': '#1abc9c',
        'Negative growth': '#c0392b'
    }

    positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]

    for (name, value, rating), pos in zip(metric_data, positions):
        ax = fig.add_subplot(gs[pos])
        color = colors.get(rating, '#95a5a6')

        ax.text(0.5, 0.6, value, fontsize=36, fontweight='bold',
                ha='center', va='center', color=color, transform=ax.transAxes)
        ax.text(0.5, 0.25, name, fontsize=14, ha='center', va='center',
                transform=ax.transAxes)
        ax.text(0.5, 0.1, rating, fontsize=11, ha='center', va='center',
                color=color, transform=ax.transAxes, style='italic')

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Add border
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(color)
            spine.set_linewidth(3)

    # Add summary text
    ax_summary = fig.add_subplot(gs[1, 2])
    summary_text = f"""Key Insights:

Total Subscribers: {metrics['conversion_rate']['total_subscribers']:,}
Ever Paid: {metrics['conversion_rate']['ever_paid']}
Currently Active Paid: {metrics['conversion_rate']['currently_active_paid']}

Unique Opens: {metrics['open_rate']['unique_opens']:,}
Total Delivered: {metrics['open_rate']['total_delivered']:,}
"""
    ax_summary.text(0.1, 0.9, summary_text, fontsize=11, va='top',
                    transform=ax_summary.transAxes, family='monospace')
    ax_summary.set_xlim(0, 1)
    ax_summary.set_ylim(0, 1)
    ax_summary.axis('off')
    ax_summary.set_title('Summary', fontsize=14, fontweight='bold')

    fig.suptitle('Newsletter Metrics Dashboard', fontsize=20, fontweight='bold', y=0.98)

    filepath = output_dir / 'metrics_dashboard.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def generate_all_visualizations(data: dict, metrics: Dict[str, Any],
                                analysis: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    """Generate all visualizations and return paths."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("\nGenerating visualizations...")
    paths = {}

    paths['subscriber_growth'] = plot_subscriber_growth(data['subscribers'], out_path)
    print("  - Subscriber growth chart")

    paths['monthly_signups'] = plot_monthly_signups(data['subscribers'], out_path)
    print("  - Monthly signups chart")

    if not analysis['engagement']['significant_posts'].empty:
        paths['open_rates'] = plot_open_rates_by_post(
            analysis['engagement']['significant_posts'], out_path)
        print("  - Open rates by post")

        paths['engagement_dist'] = plot_engagement_distribution(
            analysis['engagement']['significant_posts'], out_path)
        print("  - Engagement distribution")

    paths['conversion_funnel'] = plot_conversion_funnel(data['subscribers'], out_path)
    print("  - Conversion funnel")

    if not analysis['trends']['monthly_engagement'].empty:
        paths['monthly_trend'] = plot_monthly_engagement_trend(analysis['trends'], out_path)
        print("  - Monthly engagement trend")

    if not analysis['conversion']['conversion_posts'].empty:
        paths['top_converting'] = plot_top_converting_posts(analysis['conversion'], out_path)
        print("  - Top converting posts")

    paths['signup_days'] = plot_signup_day_distribution(analysis['acquisition'], out_path)
    print("  - Signup day distribution")

    if analysis['super_engagers']['total_analyzed'] > 0:
        paths['segments'] = plot_engagement_segments(analysis['super_engagers'], out_path)
        print("  - Engagement segments")

    paths['dashboard'] = plot_metrics_dashboard(metrics, out_path)
    print("  - Metrics dashboard")

    print(f"\nAll visualizations saved to: {output_dir}")

    return paths
