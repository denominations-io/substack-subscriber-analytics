#!/usr/bin/env python3
"""
Substack Subscriber Analytics Runner

Analyzes subscriber growth and engagement using the Substack export data.
Generates metrics, analysis, and visualizations based on the newsletter audit framework.

Usage:
    python run_analytics.py [--data-path PATH] [--output-dir DIR]

Default paths assume running from the subscriber-analytics directory.
"""
import argparse
from pathlib import Path
from datetime import datetime

from data_loader import load_all_data
from metrics import calculate_all_metrics, print_metrics_report
from analytics import run_all_analyses, print_analysis_report
from visualizations import generate_all_visualizations


def generate_markdown_report(metrics: dict, analysis: dict, viz_paths: dict,
                             output_dir: str) -> str:
    """Generate a comprehensive markdown report."""

    report = f"""# Newsletter Analytics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Executive Summary

This report analyzes subscriber growth and engagement for The Circuit newsletter
based on the Substack export data.

---

## 1. Key Metrics Baseline

The 7 metrics that actually predict revenue:

### Open Rate
- **Value**: {metrics['open_rate']['percentage']}
- **Rating**: {metrics['open_rate']['rating']}
- **Benchmark**: {metrics['open_rate']['benchmark']}
- Unique opens: {metrics['open_rate']['unique_opens']:,} / {metrics['open_rate']['total_delivered']:,} delivered

### Free-to-Paid Conversion Rate
- **Value**: {metrics['conversion_rate']['percentage']}
- **Rating**: {metrics['conversion_rate']['rating']}
- **Benchmark**: {metrics['conversion_rate']['benchmark']}
- Total subscribers: {metrics['conversion_rate']['total_subscribers']:,}
- Ever paid: {metrics['conversion_rate']['ever_paid']}
- Currently active paid: {metrics['conversion_rate']['currently_active_paid']}

### List Growth Rate (1 month)
- **Value**: {metrics['list_growth_1mo']['percentage']}
- **Rating**: {metrics['list_growth_1mo']['rating']}
- **Benchmark**: {metrics['list_growth_1mo']['benchmark']}
- New subscribers: {metrics['list_growth_1mo']['new_subscribers']}

### List Growth Rate (3 months)
- **Value**: {metrics['list_growth_3mo']['percentage']}
- **Rating**: {metrics['list_growth_3mo']['rating']}
- New subscribers: {metrics['list_growth_3mo']['new_subscribers']}

### Paid Subscriber Churn
- **Value**: {metrics['paid_churn']['percentage']}
- **Rating**: {metrics['paid_churn']['rating']}
- **Benchmark**: {metrics['paid_churn']['benchmark']}
- Total ever paid: {metrics['paid_churn']['total_ever_paid']}
- Churned: {metrics['paid_churn']['churned']}
- Retained: {metrics['paid_churn']['retained']}

![Metrics Dashboard](output/metrics_dashboard.png)

---

## 2. Post Conversion Analysis

**Question**: Which posts convert free subscribers to paid?

{analysis['conversion']['summary']}

### Top Converting Posts
"""

    # Add top converting posts
    if not analysis['conversion']['conversion_posts'].empty:
        conv_df = analysis['conversion']['conversion_posts'].head(10)
        report += "\n| Post Title | Conversions | Delivered | Conv Rate |\n"
        report += "|------------|-------------|-----------|----------|\n"
        for _, row in conv_df.iterrows():
            title = row['title'][:50] + '...' if len(str(row['title'])) > 50 else row['title']
            report += f"| {title} | {row['conversions']} | {row['delivered']:.0f} | {row['conversion_rate']:.2f}% |\n"

        report += "\n![Top Converting Posts](output/top_converting_posts.png)\n"
    else:
        report += "\nNo conversion data available.\n"

    report += f"""
---

## 3. Engagement Analysis

**Question**: Which posts drive the most engaged subscribers?

{analysis['engagement']['summary']}

### Top Performing Posts by Open Rate
"""

    # Add top performing posts
    if not analysis['engagement']['top_performers'].empty:
        top_df = analysis['engagement']['top_performers'].head(10)
        report += "\n| Post Title | Open Rate | Delivered | Opens |\n"
        report += "|------------|-----------|-----------|-------|\n"
        for _, row in top_df.iterrows():
            title = row['title'][:50] + '...' if len(str(row['title'])) > 50 else row['title']
            report += f"| {title} | {row['open_rate_pct']} | {row['delivered']} | {row['unique_opens']} |\n"

        report += "\n![Open Rates by Post](output/open_rates_by_post.png)\n"
        report += "\n![Engagement Distribution](output/engagement_distribution.png)\n"

    # Low performers
    if not analysis['engagement']['low_performers'].empty:
        report += "\n### Underperforming Posts (< 70% of average)\n"
        low_df = analysis['engagement']['low_performers'].head(5)
        report += "\n| Post Title | Open Rate | Delivered |\n"
        report += "|------------|-----------|----------|\n"
        for _, row in low_df.iterrows():
            title = row['title'][:50] + '...' if len(str(row['title'])) > 50 else row['title']
            report += f"| {title} | {row['open_rate_pct']} | {row['delivered']} |\n"

    report += f"""
---

## 4. Channel & Acquisition Analysis

**Question**: What are the best performing channels and where can we improve?

{analysis['acquisition']['summary']}

### Plan Distribution
"""
    for plan, count in analysis['acquisition']['plan_distribution'].items():
        report += f"- **{plan}**: {count}\n"

    report += f"""
### Conversion Timing
- Average days to convert: {analysis['acquisition']['avg_days_to_convert']} days
- Median days to convert: {analysis['acquisition']['median_days_to_convert']} days

![Conversion Funnel](output/conversion_funnel.png)

### Signup Patterns
![Signup Day Distribution](output/signup_day_distribution.png)

---

## 5. Subscriber Engagement Trends

**Question**: What are the general trends in subscriber engagement?

{analysis['trends']['summary']}

### Active Subscriber Ratio (30 days)
- **Value**: {analysis['trends']['active_ratio_30d_pct']}
- Recent openers: {analysis['trends']['recent_openers']:,}
- Total subscribers: {analysis['trends']['total_subscribers']:,}

![Subscriber Growth](output/subscriber_growth.png)

![Monthly Signups](output/monthly_signups.png)

![Monthly Engagement Trend](output/monthly_engagement_trend.png)

---

## 6. Subscriber Segments

{analysis['super_engagers']['summary']}

- Super engagers who are paid: {analysis['super_engagers']['super_engager_paid_pct']:.1f}%
- Total analyzed: {analysis['super_engagers']['total_analyzed']}

![Engagement Segments](output/engagement_segments.png)

---

## Recommendations

Based on the analysis:

1. **Open Rate**: Your open rate is {metrics['open_rate']['rating'].lower()}. """

    if metrics['open_rate']['value'] < 0.30:
        report += "Consider A/B testing subject lines and send times to improve engagement.\n"
    else:
        report += "Keep doing what you're doing with subject lines and content quality.\n"

    report += f"""
2. **Conversion**: With a {metrics['conversion_rate']['percentage']} conversion rate, """

    if metrics['conversion_rate']['value'] < 0.02:
        report += "there's room to improve. Consider:\n   - Adding more CTAs to your content\n   - Creating a compelling paid offer\n   - Nurturing free subscribers with targeted content\n"
    else:
        report += "you're performing well for the newsletter space.\n"

    report += f"""
3. **Growth**: Your {metrics['list_growth_1mo']['rating'].lower()} growth rate suggests """

    if metrics['list_growth_1mo']['value'] < 0.02:
        report += "you should focus on:\n   - Cross-promotion with other newsletters\n   - SEO-optimized content\n   - Social media presence\n"
    else:
        report += "your acquisition efforts are working. Focus on retention.\n"

    report += f"""
4. **Top Performing Content**: Your highest-engaging posts tend to focus on:
"""
    if not analysis['engagement']['top_performers'].empty:
        for _, row in analysis['engagement']['top_performers'].head(3).iterrows():
            report += f"   - {row['title'][:60]}...\n"

    report += """
Consider creating more content in these themes.

---

*Report generated by subscriber-analytics*
"""

    # Save report
    report_path = Path(output_dir) / 'analytics_report.md'
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\nMarkdown report saved to: {report_path}")

    return str(report_path)


def main():
    parser = argparse.ArgumentParser(description='Analyze Substack subscriber data')
    parser.add_argument('--data-path', type=str,
                        default='../data/substack-export-28-11-2025',
                        help='Path to Substack export directory')
    parser.add_argument('--output-dir', type=str,
                        default='output',
                        help='Output directory for visualizations and reports')

    args = parser.parse_args()

    print("=" * 60)
    print("SUBSTACK SUBSCRIBER ANALYTICS")
    print("=" * 60)

    # Load data
    print("\n[1/4] Loading data...")
    data = load_all_data(args.data_path)

    # Calculate metrics
    print("\n[2/4] Calculating metrics...")
    metrics = calculate_all_metrics(data)
    print_metrics_report(metrics)

    # Run analyses
    print("\n[3/4] Running analyses...")
    analysis = run_all_analyses(data)
    print_analysis_report(analysis)

    # Generate visualizations
    print("\n[4/4] Generating visualizations...")
    viz_paths = generate_all_visualizations(data, metrics, analysis, args.output_dir)

    # Generate markdown report
    report_path = generate_markdown_report(metrics, analysis, viz_paths, args.output_dir)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nOutputs:")
    print(f"  - Visualizations: {args.output_dir}/")
    print(f"  - Report: {report_path}")


if __name__ == "__main__":
    main()
