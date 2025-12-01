"""
Metrics calculation module for the 7 key newsletter metrics.

The 7 Metrics That Actually Predict Revenue:
1. Open Rate - Are people reading your emails?
2. Click-Through Rate (CTR) - Are readers engaging with your content?
3. Click-to-Open Rate - Of the people who opened, how many clicked?
4. Free-to-Paid Conversion Rate - The ultimate monetization metric
5. List Growth Rate - Are you gaining momentum?
6. Paid Subscriber Churn - Are you retaining revenue?
7. Unsubscribe Rate Per Email - Content-audience fit indicator
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


def rate_open_rate(rate: float) -> str:
    """Benchmark open rate: Excellent 45%+, Good 30-45%, Average 20-30%, Poor <20%"""
    if rate >= 0.45:
        return "Excellent"
    elif rate >= 0.30:
        return "Good"
    elif rate >= 0.20:
        return "Average"
    return "Poor"


def rate_ctr(rate: float) -> str:
    """Benchmark CTR: Excellent 5%+, Good 3-5%, Average 2-3%, Poor <2%"""
    if rate >= 0.05:
        return "Excellent"
    elif rate >= 0.03:
        return "Good"
    elif rate >= 0.02:
        return "Average"
    return "Poor"


def rate_ctor(rate: float) -> str:
    """Benchmark Click-to-Open Rate: Target 10-15% or higher"""
    if rate >= 0.15:
        return "Excellent"
    elif rate >= 0.10:
        return "Good"
    return "Below target"


def rate_conversion(rate: float) -> str:
    """Benchmark Free-to-Paid: Realistic range 2-5%, Political/niche 10-15%, Tech/general 2-3%"""
    if rate >= 0.10:
        return "Excellent (niche-level)"
    elif rate >= 0.05:
        return "Very Good"
    elif rate >= 0.02:
        return "Realistic/Good"
    return "Below average"


def rate_growth(rate: float) -> str:
    """Benchmark List Growth Rate: Target 2-5% monthly"""
    if rate >= 0.05:
        return "Excellent"
    elif rate >= 0.02:
        return "Good"
    elif rate >= 0:
        return "Slow"
    return "Negative growth"


def rate_churn(rate: float) -> str:
    """Benchmark Monthly Churn: Excellent <1%, Good 1-3%, Average 3-5%, Poor >5%"""
    if rate < 0.01:
        return "Excellent"
    elif rate < 0.03:
        return "Good"
    elif rate < 0.05:
        return "Average"
    return "Poor"


def rate_unsubscribe(rate: float) -> str:
    """Benchmark per-email unsubscribe: Excellent <0.1%, Good 0.1-0.17%, Acceptable 0.17-0.25%"""
    if rate < 0.001:
        return "Excellent"
    elif rate < 0.0017:
        return "Good"
    elif rate < 0.0025:
        return "Acceptable"
    return "Audit needed"


def calculate_open_rate(opens: pd.DataFrame, delivers: pd.DataFrame, post_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate open rate overall or for a specific post.
    Open Rate = Unique Opens / Emails Delivered
    """
    if post_id:
        opens = opens[opens['post_id'] == post_id]
        delivers = delivers[delivers['post_id'] == post_id]

    unique_opens = opens['email'].nunique() if not opens.empty else 0
    total_delivered = delivers['email'].nunique() if not delivers.empty else 0

    rate = unique_opens / total_delivered if total_delivered > 0 else 0

    return {
        'metric': 'Open Rate',
        'value': rate,
        'percentage': f"{rate * 100:.1f}%",
        'unique_opens': unique_opens,
        'total_delivered': total_delivered,
        'rating': rate_open_rate(rate),
        'benchmark': 'Excellent: 45%+, Good: 30-45%, Average: 20-30%'
    }


def calculate_free_to_paid_conversion(subscribers: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate free-to-paid conversion rate.
    Conversion Rate = Paid Subscribers / Total Subscribers Who Had Chance to Convert
    """
    total_subscribers = len(subscribers)
    paid_subscribers = subscribers['is_paid'].sum()
    active_paid = subscribers['is_active_paid'].sum()

    rate = paid_subscribers / total_subscribers if total_subscribers > 0 else 0

    return {
        'metric': 'Free-to-Paid Conversion Rate',
        'value': rate,
        'percentage': f"{rate * 100:.2f}%",
        'total_subscribers': total_subscribers,
        'ever_paid': int(paid_subscribers),
        'currently_active_paid': int(active_paid),
        'rating': rate_conversion(rate),
        'benchmark': 'Realistic: 2-5%, Political/niche: 10-15%, Tech/general: 2-3%'
    }


def calculate_list_growth_rate(subscribers: pd.DataFrame, months: int = 1) -> Dict[str, Any]:
    """
    Calculate list growth rate over the specified period.
    Growth Rate = (New Subscribers - Unsubscribes) / Total Subscribers at Start × 100
    """
    now = subscribers['created_at'].max()
    period_start = now - timedelta(days=months * 30)

    # Subscribers at start of period
    subscribers_at_start = len(subscribers[subscribers['created_at'] <= period_start])

    # New subscribers during period
    new_during_period = len(subscribers[
        (subscribers['created_at'] > period_start) &
        (subscribers['created_at'] <= now)
    ])

    # Unsubscribes approximated by email_disabled = True in period
    # Note: Substack export doesn't track exact unsubscribe dates well
    total_disabled = subscribers['email_disabled'].sum()

    # Net growth
    net_growth = new_during_period  # Simplified since we don't have unsubscribe dates

    rate = net_growth / subscribers_at_start if subscribers_at_start > 0 else 0

    return {
        'metric': f'List Growth Rate ({months}mo)',
        'value': rate,
        'percentage': f"{rate * 100:.1f}%",
        'subscribers_at_start': subscribers_at_start,
        'new_subscribers': new_during_period,
        'email_disabled_total': int(total_disabled),
        'net_growth': net_growth,
        'rating': rate_growth(rate),
        'benchmark': 'Target: 2-5% monthly growth'
    }


def calculate_paid_churn(subscribers: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate paid subscriber churn.
    Churned = was paid (first_payment_at not null) but active_subscription = False and expiry < now
    """
    paid_ever = subscribers[subscribers['is_paid'] == True]

    now = pd.Timestamp.now(tz='UTC')
    churned = paid_ever[
        (paid_ever['active_subscription'] == False) &
        (paid_ever['expiry'].notna()) &
        (paid_ever['expiry'] < now)
    ]

    total_paid = len(paid_ever)
    total_churned = len(churned)

    churn_rate = total_churned / total_paid if total_paid > 0 else 0

    return {
        'metric': 'Paid Subscriber Churn',
        'value': churn_rate,
        'percentage': f"{churn_rate * 100:.1f}%",
        'total_ever_paid': total_paid,
        'churned': total_churned,
        'retained': total_paid - total_churned,
        'rating': rate_churn(churn_rate),
        'benchmark': 'Excellent: <1%, Good: 1-3%, Average: 3-5%'
    }


def calculate_post_metrics(posts: pd.DataFrame, opens: pd.DataFrame,
                           delivers: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate per-post engagement metrics.
    Returns a DataFrame with metrics for each post.
    """
    results = []

    for _, post in posts.iterrows():
        post_id = post['post_id']

        # Filter engagement data for this post
        post_opens = opens[opens['post_id'] == post_id] if not opens.empty else pd.DataFrame()
        post_delivers = delivers[delivers['post_id'] == post_id] if not delivers.empty else pd.DataFrame()

        unique_opens = post_opens['email'].nunique() if not post_opens.empty else 0
        total_delivered = post_delivers['email'].nunique() if not post_delivers.empty else 0

        open_rate = unique_opens / total_delivered if total_delivered > 0 else 0

        results.append({
            'post_id': post_id,
            'title': post['title'],
            'post_date': post['post_date'],
            'audience': post['audience'],
            'type': post['type'],
            'delivered': total_delivered,
            'unique_opens': unique_opens,
            'open_rate': open_rate,
            'open_rate_pct': f"{open_rate * 100:.1f}%",
            'rating': rate_open_rate(open_rate)
        })

    return pd.DataFrame(results)


def calculate_all_metrics(data: dict) -> Dict[str, Any]:
    """
    Calculate all 7 key metrics from the audit framework.
    """
    subscribers = data['subscribers']
    posts = data['posts']
    opens = data['opens']
    delivers = data['delivers']

    metrics = {
        'open_rate': calculate_open_rate(opens, delivers),
        'conversion_rate': calculate_free_to_paid_conversion(subscribers),
        'list_growth_1mo': calculate_list_growth_rate(subscribers, months=1),
        'list_growth_3mo': calculate_list_growth_rate(subscribers, months=3),
        'paid_churn': calculate_paid_churn(subscribers),
        'post_metrics': calculate_post_metrics(posts, opens, delivers)
    }

    return metrics


def print_metrics_report(metrics: Dict[str, Any]):
    """Print a formatted metrics report."""
    print("\n" + "=" * 60)
    print("NEWSLETTER METRICS BASELINE REPORT")
    print("=" * 60)

    for key, m in metrics.items():
        if key == 'post_metrics':
            continue

        print(f"\n{m['metric']}")
        print("-" * 40)
        print(f"  Value: {m['percentage']}")
        print(f"  Rating: {m['rating']}")
        print(f"  Benchmark: {m['benchmark']}")

        # Print additional context
        for k, v in m.items():
            if k not in ['metric', 'value', 'percentage', 'rating', 'benchmark']:
                print(f"  {k}: {v}")

    print("\n" + "=" * 60)
