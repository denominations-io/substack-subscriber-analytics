"""
Analytics module for Substack subscriber data.

Analyses:
1. Post Conversion Analysis - Which posts drive free-to-paid conversions
2. Engagement Analysis - Which posts drive engaged subscribers (open rates)
3. Channel Performance Analysis - Best performing acquisition channels
4. Trend Analysis - Subscriber engagement trends over time
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple


def analyze_post_conversions(subscribers: pd.DataFrame, posts: pd.DataFrame,
                             opens: pd.DataFrame, delivers: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze which posts are associated with free-to-paid conversions.

    Strategy: Look at which posts were opened by subscribers shortly before
    they converted to paid (within 7 days before first_payment_at).
    """
    # Get paid subscribers with their conversion dates
    paid_subs = subscribers[subscribers['is_paid'] == True].copy()

    if paid_subs.empty or opens.empty:
        return {
            'conversion_posts': pd.DataFrame(),
            'summary': "No paid subscribers or engagement data available"
        }

    conversion_window_days = 7

    # For each paid subscriber, find posts they opened in the week before converting
    conversion_attribution = []

    for _, sub in paid_subs.iterrows():
        email = sub['email']
        conversion_date = sub['first_payment_at']

        if pd.isna(conversion_date):
            continue

        # Posts opened by this subscriber in the conversion window
        window_start = conversion_date - timedelta(days=conversion_window_days)

        subscriber_opens = opens[
            (opens['email'] == email) &
            (opens['timestamp'] >= window_start) &
            (opens['timestamp'] <= conversion_date)
        ]

        for post_id in subscriber_opens['post_id'].unique():
            conversion_attribution.append({
                'email': email,
                'post_id': post_id,
                'conversion_date': conversion_date
            })

    if not conversion_attribution:
        return {
            'conversion_posts': pd.DataFrame(),
            'summary': "No posts found in conversion windows"
        }

    attr_df = pd.DataFrame(conversion_attribution)

    # Count conversions attributed to each post
    post_conversions = attr_df.groupby('post_id').agg(
        conversions=('email', 'nunique')
    ).reset_index()

    # Merge with post metadata
    post_conversions = post_conversions.merge(
        posts[['post_id', 'title', 'post_date', 'audience']],
        on='post_id',
        how='left'
    )

    # Calculate conversion rate for each post
    post_delivers = delivers.groupby('post_id')['email'].nunique().reset_index()
    post_delivers.columns = ['post_id', 'delivered']

    post_conversions = post_conversions.merge(post_delivers, on='post_id', how='left')
    post_conversions['conversion_rate'] = (
        post_conversions['conversions'] / post_conversions['delivered'] * 100
    ).round(2)

    post_conversions = post_conversions.sort_values('conversions', ascending=False)

    return {
        'conversion_posts': post_conversions,
        'total_conversions_tracked': len(paid_subs),
        'posts_with_attribution': len(post_conversions),
        'top_converter': post_conversions.iloc[0]['title'] if len(post_conversions) > 0 else None,
        'summary': f"Analyzed {len(paid_subs)} paid subscribers, attributed conversions to {len(post_conversions)} posts"
    }


def analyze_engagement_by_post(posts: pd.DataFrame, opens: pd.DataFrame,
                                delivers: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze which posts drive the most engaged subscribers.
    Looks at open rates and identifies top-performing posts.
    """
    results = []

    for _, post in posts.iterrows():
        post_id = post['post_id']

        post_opens = opens[opens['post_id'] == post_id] if not opens.empty else pd.DataFrame()
        post_delivers = delivers[delivers['post_id'] == post_id] if not delivers.empty else pd.DataFrame()

        unique_opens = post_opens['email'].nunique() if not post_opens.empty else 0
        total_delivered = post_delivers['email'].nunique() if not post_delivers.empty else 0

        open_rate = unique_opens / total_delivered if total_delivered > 0 else 0

        # Engagement score: combines open rate and absolute reach
        # Higher is better
        engagement_score = open_rate * np.log1p(total_delivered)

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
            'engagement_score': round(engagement_score, 2)
        })

    engagement_df = pd.DataFrame(results)
    engagement_df = engagement_df.sort_values('open_rate', ascending=False)

    # Filter to posts with meaningful delivery counts
    significant_posts = engagement_df[engagement_df['delivered'] >= 50].copy()

    # Identify high and low performers
    if len(significant_posts) > 0:
        avg_open_rate = significant_posts['open_rate'].mean()
        top_performers = significant_posts[significant_posts['open_rate'] > avg_open_rate]
        low_performers = significant_posts[significant_posts['open_rate'] < avg_open_rate * 0.7]
    else:
        avg_open_rate = 0
        top_performers = pd.DataFrame()
        low_performers = pd.DataFrame()

    return {
        'all_posts': engagement_df,
        'significant_posts': significant_posts,
        'avg_open_rate': avg_open_rate,
        'avg_open_rate_pct': f"{avg_open_rate * 100:.1f}%",
        'top_performers': top_performers,
        'low_performers': low_performers,
        'summary': f"Average open rate: {avg_open_rate*100:.1f}%, {len(top_performers)} top performers, {len(low_performers)} underperformers"
    }


def analyze_subscriber_acquisition(subscribers: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze subscriber acquisition patterns and channels.

    Note: Substack export doesn't include explicit channel data, so we analyze:
    - Subscription plan distribution (yearly vs monthly vs other)
    - Acquisition timing patterns
    - Conversion timing patterns
    """
    # Plan distribution
    plan_dist = subscribers['plan'].value_counts()

    # Acquisition by month
    subscribers['signup_month'] = subscribers['created_at'].dt.to_period('M')
    monthly_signups = subscribers.groupby('signup_month').size()

    # Paid vs free over time
    monthly_paid = subscribers[subscribers['is_paid']].groupby('signup_month').size()

    # Day of week analysis
    subscribers['signup_dow'] = subscribers['created_at'].dt.day_name()
    dow_dist = subscribers['signup_dow'].value_counts()

    # Time to conversion (for those who converted)
    converted = subscribers[subscribers['is_paid']].copy()
    if not converted.empty:
        converted['days_to_convert'] = (
            converted['first_payment_at'] - converted['created_at']
        ).dt.days
        avg_days_to_convert = converted['days_to_convert'].mean()
        median_days_to_convert = converted['days_to_convert'].median()
    else:
        avg_days_to_convert = 0
        median_days_to_convert = 0

    return {
        'plan_distribution': plan_dist.to_dict(),
        'monthly_signups': monthly_signups,
        'monthly_paid_signups': monthly_paid,
        'dow_distribution': dow_dist.to_dict(),
        'avg_days_to_convert': round(avg_days_to_convert, 1),
        'median_days_to_convert': round(median_days_to_convert, 1),
        'summary': f"Avg time to convert: {avg_days_to_convert:.1f} days, Median: {median_days_to_convert:.1f} days"
    }


def analyze_engagement_trends(subscribers: pd.DataFrame, opens: pd.DataFrame,
                               delivers: pd.DataFrame, posts: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze engagement trends over time.
    """
    if opens.empty or delivers.empty:
        return {
            'monthly_engagement': pd.DataFrame(),
            'summary': "No engagement data available"
        }

    # Calculate monthly open rates
    opens['month'] = opens['timestamp'].dt.to_period('M')
    delivers['month'] = delivers['timestamp'].dt.to_period('M')

    monthly_opens = opens.groupby('month')['email'].nunique()
    monthly_delivers = delivers.groupby('month')['email'].nunique()

    monthly_engagement = pd.DataFrame({
        'opens': monthly_opens,
        'delivers': monthly_delivers
    }).fillna(0)

    monthly_engagement['open_rate'] = (
        monthly_engagement['opens'] / monthly_engagement['delivers']
    ).fillna(0)

    # Subscriber growth trend
    subscribers['signup_month'] = subscribers['created_at'].dt.to_period('M')
    cumulative_subs = subscribers.groupby('signup_month').size().cumsum()

    # Active subscriber ratio over time (those who opened recent emails)
    last_30_days = pd.Timestamp.now(tz='UTC') - timedelta(days=30)
    recent_openers = opens[opens['timestamp'] >= last_30_days]['email'].nunique()
    total_subs = len(subscribers)
    active_ratio = recent_openers / total_subs if total_subs > 0 else 0

    return {
        'monthly_engagement': monthly_engagement,
        'cumulative_subscribers': cumulative_subs,
        'active_ratio_30d': active_ratio,
        'active_ratio_30d_pct': f"{active_ratio * 100:.1f}%",
        'recent_openers': recent_openers,
        'total_subscribers': total_subs,
        'summary': f"{active_ratio*100:.1f}% of subscribers opened an email in the last 30 days"
    }


def identify_super_engagers(opens: pd.DataFrame, delivers: pd.DataFrame,
                            subscribers: pd.DataFrame) -> Dict[str, Any]:
    """
    Identify subscribers with consistently high engagement.
    Super engagers: opened >80% of emails delivered to them.
    """
    if opens.empty or delivers.empty:
        return {
            'super_engagers': pd.DataFrame(),
            'summary': "No engagement data available"
        }

    # Per-subscriber metrics
    sub_opens = opens.groupby('email')['post_id'].nunique().reset_index()
    sub_opens.columns = ['email', 'posts_opened']

    sub_delivers = delivers.groupby('email')['post_id'].nunique().reset_index()
    sub_delivers.columns = ['email', 'posts_delivered']

    sub_engagement = sub_opens.merge(sub_delivers, on='email', how='outer').fillna(0)
    sub_engagement['open_rate'] = (
        sub_engagement['posts_opened'] / sub_engagement['posts_delivered']
    ).fillna(0)

    # Filter to subscribers with meaningful sample size
    engaged = sub_engagement[sub_engagement['posts_delivered'] >= 5].copy()

    # Super engagers: 80%+ open rate
    super_engagers = engaged[engaged['open_rate'] >= 0.8]

    # At-risk: <20% open rate
    at_risk = engaged[engaged['open_rate'] < 0.2]

    # Merge with subscriber data for more context
    super_engagers = super_engagers.merge(
        subscribers[['email', 'is_paid', 'created_at']],
        on='email',
        how='left'
    )

    return {
        'super_engagers': super_engagers,
        'super_engager_count': len(super_engagers),
        'super_engager_paid_pct': super_engagers['is_paid'].mean() * 100 if len(super_engagers) > 0 else 0,
        'at_risk_count': len(at_risk),
        'total_analyzed': len(engaged),
        'summary': f"{len(super_engagers)} super engagers (80%+ open rate), {len(at_risk)} at-risk subscribers"
    }


def run_all_analyses(data: dict) -> Dict[str, Any]:
    """
    Run all analytics on the Substack data.
    """
    subscribers = data['subscribers']
    posts = data['posts']
    opens = data['opens']
    delivers = data['delivers']

    print("\nRunning post conversion analysis...")
    conversion = analyze_post_conversions(subscribers, posts, opens, delivers)

    print("Running engagement analysis...")
    engagement = analyze_engagement_by_post(posts, opens, delivers)

    print("Running subscriber acquisition analysis...")
    acquisition = analyze_subscriber_acquisition(subscribers)

    print("Running engagement trend analysis...")
    trends = analyze_engagement_trends(subscribers, opens, delivers, posts)

    print("Identifying super engagers...")
    super_engagers = identify_super_engagers(opens, delivers, subscribers)

    return {
        'conversion': conversion,
        'engagement': engagement,
        'acquisition': acquisition,
        'trends': trends,
        'super_engagers': super_engagers
    }


def print_analysis_report(analysis: Dict[str, Any]):
    """Print a formatted analysis report."""
    print("\n" + "=" * 60)
    print("NEWSLETTER ANALYSIS REPORT")
    print("=" * 60)

    # Conversion Analysis
    print("\n### POST CONVERSION ANALYSIS ###")
    print(analysis['conversion']['summary'])
    if not analysis['conversion']['conversion_posts'].empty:
        print("\nTop 5 posts driving conversions:")
        top_conv = analysis['conversion']['conversion_posts'].head()
        for _, row in top_conv.iterrows():
            print(f"  - {row['title'][:50]}... ({row['conversions']} conversions)")

    # Engagement Analysis
    print("\n### ENGAGEMENT ANALYSIS ###")
    print(analysis['engagement']['summary'])
    if not analysis['engagement']['top_performers'].empty:
        print("\nTop 5 posts by open rate:")
        top_eng = analysis['engagement']['top_performers'].head()
        for _, row in top_eng.iterrows():
            print(f"  - {row['title'][:50]}... ({row['open_rate_pct']})")

    # Acquisition Analysis
    print("\n### ACQUISITION ANALYSIS ###")
    print(analysis['acquisition']['summary'])
    print(f"Plan distribution: {analysis['acquisition']['plan_distribution']}")

    # Trends
    print("\n### ENGAGEMENT TRENDS ###")
    print(analysis['trends']['summary'])

    # Super Engagers
    print("\n### SUBSCRIBER SEGMENTS ###")
    print(analysis['super_engagers']['summary'])
    if analysis['super_engagers']['super_engager_count'] > 0:
        print(f"  {analysis['super_engagers']['super_engager_paid_pct']:.1f}% of super engagers are paid subscribers")

    print("\n" + "=" * 60)
