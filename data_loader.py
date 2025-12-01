"""
Data loader for Substack export data.
Handles loading and initial processing of subscriber, post, and engagement data.
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple


def find_email_list_file(data_path: Path) -> Optional[Path]:
    """Find the email list CSV file in the data directory."""
    # Try common patterns
    patterns = ["email_list*.csv", "email-list*.csv", "subscribers*.csv"]
    for pattern in patterns:
        matches = list(data_path.glob(pattern))
        if matches:
            return matches[0]
    return None


def load_subscribers(data_path: Path) -> pd.DataFrame:
    """Load subscriber email list data."""
    # Find the email list file dynamically
    email_file = find_email_list_file(data_path)
    if email_file is None:
        raise FileNotFoundError(
            f"No email list file found in {data_path}. "
            "Expected a file matching 'email_list*.csv'"
        )

    df = pd.read_csv(email_file)

    # Parse dates
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['first_payment_at'] = pd.to_datetime(df['first_payment_at'])
    df['expiry'] = pd.to_datetime(df['expiry'])

    # Derive useful columns
    df['is_paid'] = df['first_payment_at'].notna()
    df['is_active_paid'] = df['active_subscription'] == True

    return df


def load_posts(data_path: Path) -> pd.DataFrame:
    """Load posts metadata."""
    df = pd.read_csv(data_path / "posts.csv")

    # Parse dates
    df['post_date'] = pd.to_datetime(df['post_date'])
    df['email_sent_at'] = pd.to_datetime(df['email_sent_at'])

    # Extract numeric post_id from the composite ID (e.g., "179800700.title-slug" -> 179800700)
    df['post_id'] = df['post_id'].str.split('.').str[0].astype(int)

    # Filter to only published posts that were emailed
    df = df[df['is_published'] == True].copy()

    return df


def load_engagement_data(data_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load all opens and delivers CSV files from the posts directory."""
    posts_dir = data_path / "posts"

    opens_list = []
    delivers_list = []

    for f in posts_dir.glob("*.opens.csv"):
        try:
            df = pd.read_csv(f)
            if not df.empty:
                opens_list.append(df)
        except pd.errors.EmptyDataError:
            continue

    for f in posts_dir.glob("*.delivers.csv"):
        try:
            df = pd.read_csv(f)
            if not df.empty:
                delivers_list.append(df)
        except pd.errors.EmptyDataError:
            continue

    opens_df = pd.concat(opens_list, ignore_index=True) if opens_list else pd.DataFrame()
    delivers_df = pd.concat(delivers_list, ignore_index=True) if delivers_list else pd.DataFrame()

    # Parse timestamps
    if not opens_df.empty:
        opens_df['timestamp'] = pd.to_datetime(opens_df['timestamp'])
    if not delivers_df.empty:
        delivers_df['timestamp'] = pd.to_datetime(delivers_df['timestamp'])

    return opens_df, delivers_df


def load_subscriber_details(data_path: Path) -> pd.DataFrame:
    """Load detailed subscriber data with engagement metrics."""
    details_path = data_path / "subscriber_details.csv"
    if not details_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(details_path)

    # Rename columns for easier access
    df = df.rename(columns={
        'Email': 'email',
        'Name': 'name',
        'Stripe plan': 'stripe_plan',
        'Cancel date': 'cancel_date',
        'Start date': 'start_date',
        'Paid upgrade date': 'paid_upgrade_date',
        'Bestseller': 'bestseller',
        'Emails received (6mo)': 'emails_received_6mo',
        'Emails dropped (6mo)': 'emails_dropped_6mo',
        'num_emails_opened': 'total_emails_opened',
        'Emails opened (6mo)': 'emails_opened_6mo',
        'Emails opened (7d)': 'emails_opened_7d',
        'Emails opened (30d)': 'emails_opened_30d',
        'Last email open': 'last_email_open',
        'Links clicked': 'links_clicked',
        'Last clicked at': 'last_clicked_at',
        'Unique emails seen (6mo)': 'unique_emails_seen_6mo',
        'Unique emails seen (7d)': 'unique_emails_seen_7d',
        'Unique emails seen (30d)': 'unique_emails_seen_30d',
        'Post views': 'post_views',
        'Post views (7d)': 'post_views_7d',
        'Post views (30d)': 'post_views_30d',
        'Unique posts seen': 'unique_posts_seen',
        'Unique posts seen (7d)': 'unique_posts_seen_7d',
        'Unique posts seen (30d)': 'unique_posts_seen_30d',
        'Comments': 'comments',
        'Comments (7d)': 'comments_7d',
        'Comments (30d)': 'comments_30d',
        'Shares': 'shares',
        'Shares (7d)': 'shares_7d',
        'Shares (30d)': 'shares_30d',
        'Subscriptions gifted': 'subscriptions_gifted',
        'First paid date': 'first_paid_date',
        'Revenue': 'revenue',
        'Subscription source (free)': 'source_free',
        'Subscription source (paid)': 'source_paid',
        'Days active (30d)': 'days_active_30d',
        'Activity': 'activity_score',
        'Country': 'country',
        'State/Province': 'state',
        'Expiration date': 'expiration_date',
        'Type': 'subscriber_type',
        'Sections': 'sections'
    })

    # Parse dates
    date_cols = ['cancel_date', 'start_date', 'paid_upgrade_date', 'last_email_open',
                 'last_clicked_at', 'first_paid_date', 'expiration_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Parse revenue (remove currency symbol)
    if 'revenue' in df.columns:
        df['revenue_amount'] = df['revenue'].str.replace('€', '').str.replace('$', '').str.replace(',', '').astype(float)

    # Derive useful columns
    df['is_paid'] = df['subscriber_type'].str.contains('Subscriber', case=False, na=False)
    df['is_free'] = df['subscriber_type'] == 'Free'
    df['has_opened'] = df['total_emails_opened'] > 0
    df['is_engaged_30d'] = df['emails_opened_30d'] > 0
    df['is_engaged_7d'] = df['emails_opened_7d'] > 0

    # Calculate engagement rate (if received emails)
    df['open_rate_6mo'] = (df['emails_opened_6mo'] / df['emails_received_6mo']).fillna(0)

    # Deliverability rate
    df['deliverability_rate'] = 1 - (df['emails_dropped_6mo'] / (df['emails_received_6mo'] + df['emails_dropped_6mo'])).fillna(0)

    return df


def load_all_data(data_path: str) -> dict:
    """
    Load all Substack export data.

    Args:
        data_path: Path to the Substack export directory

    Returns:
        dict with keys: subscribers, subscriber_details, posts, opens, delivers
    """
    path = Path(data_path)

    if not path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    print("Loading subscriber data...")
    subscribers = load_subscribers(path)
    print(f"  Loaded {len(subscribers)} subscribers")

    print("Loading subscriber details...")
    subscriber_details = load_subscriber_details(path)
    if not subscriber_details.empty:
        print(f"  Loaded {len(subscriber_details)} subscriber details")
    else:
        print("  No subscriber_details.csv found")

    print("Loading posts data...")
    posts = load_posts(path)
    print(f"  Loaded {len(posts)} posts")

    print("Loading engagement data...")
    opens, delivers = load_engagement_data(path)
    print(f"  Loaded {len(opens)} open events, {len(delivers)} delivery events")

    return {
        'subscribers': subscribers,
        'subscriber_details': subscriber_details,
        'posts': posts,
        'opens': opens,
        'delivers': delivers
    }


if __name__ == "__main__":
    # Test loading
    import sys
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = ".data"
        # Find first available dataset
        from pathlib import Path
        data_dir = Path(data_path)
        if data_dir.exists():
            datasets = [d for d in data_dir.iterdir() if d.is_dir()]
            if datasets:
                data_path = str(datasets[0])
            else:
                print("No datasets found in .data/")
                sys.exit(1)
        else:
            print("No .data directory found")
            sys.exit(1)

    data = load_all_data(data_path)
    print("\nData loaded successfully!")
    print(f"\nSubscribers columns: {list(data['subscribers'].columns)}")
    print(f"Posts columns: {list(data['posts'].columns)}")
    print(f"Opens columns: {list(data['opens'].columns)}")
    print(f"Delivers columns: {list(data['delivers'].columns)}")
