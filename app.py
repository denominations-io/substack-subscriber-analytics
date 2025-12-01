"""
Streamlit Dashboard for Substack Subscriber Analytics

Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime, timedelta

from data_loader import load_all_data
from metrics import calculate_all_metrics, rate_open_rate
from analytics import run_all_analyses
from upload_handler import get_available_datasets
from components.upload_modal import render_upload_modal
from components.data_manager import render_data_manager, initialize_session_state

# Page config
st.set_page_config(
    page_title="Substack Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Modern dark theme
st.markdown("""
<style>
    /* Global app styling */
    .stApp {
        background-color: #fafafa;
    }

    /* Header styling */
    .app-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 30px 40px;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 2rem -1rem;
        color: white;
    }
    .app-header h1 {
        color: white;
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.5px;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #e9ecef;
        transition: all 0.2s ease;
    }
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .metric-card h4 {
        font-size: 0.85rem;
        font-weight: 500;
        color: #6c757d;
        margin: 0 0 8px 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card h2 {
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0 0 6px 0;
    }
    .metric-card .rating {
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0;
    }
    .metric-card .delta {
        font-size: 0.75rem;
        color: #6c757d;
        margin: 4px 0 0 0;
    }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin: 2rem 0 1rem 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #e9ecef;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #f8f9fa;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.9rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 8px 16px;
        border: 1px solid #e9ecef;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: #1a1a2e;
        color: white;
        border-color: #1a1a2e;
    }

    /* Data table styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    .stButton > button:hover {
        border-color: #1a1a2e;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 0.9rem;
        font-weight: 500;
        color: #495057;
    }

    /* Info/Warning/Success boxes */
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
initialize_session_state()


@st.cache_data
def load_data(data_path: str):
    """Load and cache all data."""
    return load_all_data(data_path)


@st.cache_data
def compute_metrics(_data):
    """Compute and cache metrics."""
    return calculate_all_metrics(_data)


@st.cache_data
def compute_analysis(_data):
    """Compute and cache analysis."""
    return run_all_analyses(_data)


def get_rating_color(rating: str) -> str:
    """Get color based on rating."""
    rating_lower = rating.lower()
    if 'excellent' in rating_lower or 'very good' in rating_lower:
        return "#2ecc71"
    elif 'good' in rating_lower or 'realistic' in rating_lower:
        return "#3498db"
    elif 'average' in rating_lower or 'slow' in rating_lower:
        return "#f39c12"
    else:
        return "#e74c3c"


def render_metric_card(title: str, value: str, rating: str, delta: str = None):
    """Render a metric card with color coding."""
    color = get_rating_color(rating)
    delta_html = f'<p class="delta">{delta}</p>' if delta else ""
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid {color};">
        <h4>{title}</h4>
        <h2 style="color: {color};">{value}</h2>
        <p class="rating" style="color: {color};">{rating}</p>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# Chart theme colors
CHART_COLORS = {
    'primary': '#1a1a2e',
    'secondary': '#0f3460',
    'accent': '#e94560',
    'success': '#2ecc71',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#3498db',
    'light': '#f8f9fa',
    'muted': '#6c757d',
}

# Color palette for charts
CHART_PALETTE = ['#1a1a2e', '#0f3460', '#e94560', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']


def apply_chart_style(fig, title=None, height=450):
    """Apply consistent styling to Plotly charts for social media sharing."""
    fig.update_layout(
        # Font settings - larger for readability in screenshots
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            size=14,
            color='#212529'
        ),
        title=dict(
            text=title,
            font=dict(size=20, color='#1a1a2e', family="Inter, sans-serif"),
            x=0.5,
            xanchor='center',
            y=0.95,
        ) if title else None,
        # Layout
        height=height,
        margin=dict(l=60, r=40, t=80 if title else 40, b=60),
        # Background
        paper_bgcolor='white',
        plot_bgcolor='white',
        # Legend
        legend=dict(
            font=dict(size=13),
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#e9ecef',
            borderwidth=1,
        ),
        # Hover
        hoverlabel=dict(
            bgcolor='white',
            font_size=13,
            font_family="Inter, sans-serif"
        ),
    )
    # Axis styling
    fig.update_xaxes(
        title_font=dict(size=14, color='#495057'),
        tickfont=dict(size=12, color='#495057'),
        gridcolor='#f1f3f4',
        linecolor='#dee2e6',
        showline=True,
    )
    fig.update_yaxes(
        title_font=dict(size=14, color='#495057'),
        tickfont=dict(size=12, color='#495057'),
        gridcolor='#f1f3f4',
        linecolor='#dee2e6',
        showline=True,
    )
    return fig


def main():
    # Check if we're in the subscriber details prompt flow
    if st.session_state.get('pending_subscriber_details'):
        render_upload_modal()
        st.stop()

    # Check if we need to show the upload modal
    datasets = get_available_datasets()
    has_data = len(datasets) > 0

    # Show upload modal if no data OR user requested it
    if not has_data or st.session_state.get('show_upload_modal'):
        render_upload_modal(force_show=st.session_state.get('show_upload_modal', False))

        # If still no data after modal, stop here
        if not has_data:
            st.stop()

        # If user wanted to upload but has data, provide a back button
        if st.session_state.get('show_upload_modal'):
            if st.button("← Back to Dashboard"):
                st.session_state.show_upload_modal = False
                st.rerun()
            st.stop()

    # Main dashboard
    st.markdown("""
    <div class="app-header">
        <h1>Newsletter Analytics Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)

    # Get active dataset from data manager (in sidebar)
    active_dataset = render_data_manager()

    if not active_dataset:
        st.warning("No dataset selected. Please upload your Substack data.")
        if st.button("Upload Data"):
            st.session_state.show_upload_modal = True
            st.rerun()
        st.stop()

    # Load data
    with st.spinner("Loading data..."):
        try:
            data = load_data(active_dataset)
            metrics = compute_metrics(data)
            analysis = compute_analysis(data)
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.info("Try uploading a fresh export from Substack.")
            if st.button("Upload New Data"):
                st.session_state.show_upload_modal = True
                st.rerun()
            st.stop()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["📈 Overview", "📬 Post Analysis", "👥 Subscriber Analysis",
         "📊 Engagement Trends", "🎯 Segments", "🔀 Engagement Flow", "🧹 Inactive Subscribers"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")
    st.sidebar.metric("Total Subscribers", f"{len(data['subscribers']):,}")
    st.sidebar.metric("Total Posts", f"{len(data['posts']):,}")
    st.sidebar.metric("Paid Subscribers", f"{metrics['conversion_rate']['currently_active_paid']}")

    # Main content based on page selection
    if page == "📈 Overview":
        render_overview(metrics, analysis, data)
    elif page == "📬 Post Analysis":
        render_post_analysis(analysis, data)
    elif page == "👥 Subscriber Analysis":
        render_subscriber_analysis(data, analysis)
    elif page == "📊 Engagement Trends":
        render_trends(analysis, data)
    elif page == "🎯 Segments":
        render_segments(analysis, data)
    elif page == "🔀 Engagement Flow":
        render_engagement_flow(data)
    elif page == "🧹 Inactive Subscribers":
        render_inactive_subscribers(data, analysis)


def render_overview(metrics, analysis, data):
    """Render the overview dashboard."""
    st.markdown('<h2 class="section-header">Key Metrics</h2>', unsafe_allow_html=True)
    st.caption("The 7 metrics that predict newsletter revenue")

    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        render_metric_card(
            "Open Rate",
            metrics['open_rate']['percentage'],
            metrics['open_rate']['rating'],
            f"{metrics['open_rate']['unique_opens']:,} / {metrics['open_rate']['total_delivered']:,}"
        )

    with col2:
        render_metric_card(
            "Conversion Rate",
            metrics['conversion_rate']['percentage'],
            metrics['conversion_rate']['rating'],
            f"{metrics['conversion_rate']['ever_paid']} paid"
        )

    with col3:
        render_metric_card(
            "Growth (1mo)",
            metrics['list_growth_1mo']['percentage'],
            metrics['list_growth_1mo']['rating'],
            f"+{metrics['list_growth_1mo']['new_subscribers']} subscribers"
        )

    with col4:
        render_metric_card(
            "Growth (3mo)",
            metrics['list_growth_3mo']['percentage'],
            metrics['list_growth_3mo']['rating'],
            f"+{metrics['list_growth_3mo']['new_subscribers']} subscribers"
        )

    with col5:
        render_metric_card(
            "Paid Churn",
            metrics['paid_churn']['percentage'],
            metrics['paid_churn']['rating'],
            f"{metrics['paid_churn']['retained']} retained"
        )

    st.markdown("---")

    # Two columns for charts
    col1, col2 = st.columns(2)

    with col1:
        funnel_data = {
            'Stage': ['Total Subscribers', 'Active (not disabled)', 'Ever Paid', 'Currently Paid'],
            'Count': [
                len(data['subscribers']),
                len(data['subscribers'][data['subscribers']['email_disabled'] == False]),
                metrics['conversion_rate']['ever_paid'],
                metrics['conversion_rate']['currently_active_paid']
            ]
        }
        fig = go.Figure(go.Funnel(
            y=funnel_data['Stage'],
            x=funnel_data['Count'],
            textinfo="value+percent initial",
            textfont=dict(size=14),
            marker={"color": [CHART_COLORS['info'], CHART_COLORS['success'], CHART_COLORS['warning'], CHART_COLORS['accent']]}
        ))
        apply_chart_style(fig, title="Conversion Funnel", height=420)
        st.plotly_chart(fig, width='stretch')

    with col2:
        subs = data['subscribers'].copy()
        created_at = subs['created_at']
        if created_at.dt.tz is not None:
            created_at = created_at.dt.tz_convert(None)
        subs['month'] = created_at.dt.to_period('M').astype(str)
        monthly = subs.groupby('month').size().reset_index(name='new_subscribers')
        monthly['cumulative'] = monthly['new_subscribers'].cumsum()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly['month'],
            y=monthly['new_subscribers'],
            name='New Subscribers',
            marker_color=CHART_COLORS['info'],
            opacity=0.7
        ))
        fig.add_trace(go.Scatter(
            x=monthly['month'],
            y=monthly['cumulative'],
            name='Cumulative',
            yaxis='y2',
            line=dict(color=CHART_COLORS['primary'], width=3),
            mode='lines+markers',
            marker=dict(size=6)
        ))
        apply_chart_style(fig, title="Subscriber Growth", height=420)
        fig.update_layout(
            yaxis=dict(title='New Subscribers'),
            yaxis2=dict(title='Cumulative', overlaying='y', side='right', gridcolor='rgba(0,0,0,0)'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center')
        )
        st.plotly_chart(fig, width='stretch')

    # Engagement summary
    st.markdown("---")
    st.subheader("Engagement Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Average Open Rate",
            analysis['engagement']['avg_open_rate_pct'],
            help="Average across all posts with 50+ deliveries"
        )

    with col2:
        st.metric(
            "Active Subscribers (30d)",
            analysis['trends']['active_ratio_30d_pct'],
            help="Subscribers who opened at least one email in the last 30 days"
        )

    with col3:
        st.metric(
            "Super Engagers",
            f"{analysis['super_engagers']['super_engager_count']}",
            help="Subscribers with 80%+ open rate"
        )

    # Multi-channel engagement from subscriber_details
    subscriber_details = data.get('subscriber_details', pd.DataFrame())
    if not subscriber_details.empty:
        st.markdown("---")
        st.subheader("Multi-Channel Engagement (30 Days)")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            email_openers = (subscriber_details['emails_opened_30d'] > 0).sum()
            st.metric("Email Openers", f"{email_openers:,}",
                     help="Subscribers who opened at least one email in 30 days")

        with col2:
            post_viewers = (subscriber_details['post_views_30d'] > 0).sum()
            st.metric("Post Viewers", f"{post_viewers:,}",
                     help="Subscribers who viewed posts on web/app in 30 days")

        with col3:
            commenters = (subscriber_details['comments_30d'] > 0).sum()
            st.metric("Commenters", f"{commenters:,}",
                     help="Subscribers who commented in 30 days")

        with col4:
            sharers = (subscriber_details['shares_30d'] > 0).sum()
            st.metric("Sharers", f"{sharers:,}",
                     help="Subscribers who shared content in 30 days")

        with col5:
            total_comments = subscriber_details['comments'].sum()
            st.metric("Total Comments", f"{int(total_comments):,}",
                     help="All-time comments from subscribers")


def render_post_analysis(analysis, data):
    """Render the post analysis page."""
    st.markdown('<h2 class="section-header">Post Analysis</h2>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Engagement by Post", "Conversion Attribution"])

    with tab1:
        st.subheader("Open Rates by Post")

        # Filter controls
        col1, col2 = st.columns([1, 3])
        with col1:
            min_delivered = st.slider("Min. deliveries", 0, 500, 50)

        engagement_df = analysis['engagement']['all_posts']
        filtered = engagement_df[engagement_df['delivered'] >= min_delivered].copy()

        if not filtered.empty:
            filtered = filtered.sort_values('post_date')

            # Open rate over time
            fig = px.scatter(
                filtered,
                x='post_date',
                y=filtered['open_rate'] * 100,
                size='delivered',
                color=filtered['open_rate'] * 100,
                color_continuous_scale='RdYlGn',
                hover_data=['title', 'delivered', 'unique_opens'],
                labels={'y': 'Open Rate (%)', 'post_date': 'Post Date'}
            )
            fig.add_hline(y=45, line_dash="dash", line_color=CHART_COLORS['success'],
                         annotation_text="Excellent (45%)", annotation_font_size=13)
            fig.add_hline(y=30, line_dash="dash", line_color=CHART_COLORS['warning'],
                         annotation_text="Good (30%)", annotation_font_size=13)
            apply_chart_style(fig, title="Open Rates Over Time", height=500)
            fig.update_coloraxes(colorbar_title_font_size=13, colorbar_tickfont_size=12)
            st.plotly_chart(fig, width='stretch')

            # Data table
            st.subheader("Post Details")
            display_df = filtered[['title', 'post_date', 'delivered', 'unique_opens',
                                   'open_rate_pct']].copy()
            display_df['post_date'] = display_df['post_date'].dt.strftime('%Y-%m-%d')
            display_df['rating'] = display_df['open_rate_pct'].str.rstrip('%').astype(float).apply(
                lambda x: 'Excellent' if x >= 45 else 'Good' if x >= 30 else 'Average' if x >= 20 else 'Poor'
            )
            display_df = display_df.sort_values('open_rate_pct', ascending=False)
            st.dataframe(display_df, width='stretch', hide_index=True)

    with tab2:
        st.subheader("Posts Driving Conversions")
        st.markdown("Posts opened by subscribers within 7 days before they converted to paid")

        conv_df = analysis['conversion']['conversion_posts']
        if not conv_df.empty:
            fig = px.bar(
                conv_df.head(10),
                x='conversions',
                y='title',
                orientation='h',
                color='conversion_rate',
                color_continuous_scale='YlOrRd',
                labels={'conversions': 'Conversions', 'title': '',
                       'conversion_rate': 'Conv. Rate (%)'}
            )
            apply_chart_style(fig, title="Top Converting Posts", height=450)
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            fig.update_coloraxes(colorbar_title_font_size=13, colorbar_tickfont_size=12)
            st.plotly_chart(fig, width='stretch')

            st.dataframe(conv_df[['title', 'conversions', 'delivered', 'conversion_rate']],
                        width='stretch', hide_index=True)
        else:
            st.info("No conversion attribution data available")


def render_subscriber_analysis(data, analysis):
    """Render subscriber analysis page."""
    st.markdown('<h2 class="section-header">Subscriber Analysis</h2>', unsafe_allow_html=True)

    subscriber_details = data.get('subscriber_details', pd.DataFrame())

    # Add Acquisition Sources tab if subscriber_details available
    if not subscriber_details.empty:
        tab1, tab2, tab3, tab4 = st.tabs(["Acquisition", "Acquisition Sources", "Plan Distribution", "Conversion Timing"])
    else:
        tab1, tab2, tab3 = st.tabs(["Acquisition", "Plan Distribution", "Conversion Timing"])
        tab4 = None

    with tab1:
        subs = data['subscribers'].copy()
        created_at = subs['created_at']
        if created_at.dt.tz is not None:
            created_at = created_at.dt.tz_convert(None)
        subs['month'] = created_at.dt.to_period('M').astype(str)
        subs['is_paid_label'] = subs['is_paid'].map({True: 'Paid', False: 'Free'})

        monthly = subs.groupby(['month', 'is_paid_label']).size().reset_index(name='count')

        fig = px.bar(
            monthly,
            x='month',
            y='count',
            color='is_paid_label',
            barmode='stack',
            color_discrete_map={'Free': CHART_COLORS['info'], 'Paid': CHART_COLORS['accent']},
            labels={'count': 'New Subscribers', 'month': 'Month', 'is_paid_label': 'Type'}
        )
        apply_chart_style(fig, title="Subscriber Acquisition Over Time", height=420)
        fig.update_layout(legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center'))
        st.plotly_chart(fig, width='stretch')

        # Day of week
        dow = analysis['acquisition']['dow_distribution']
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_df = pd.DataFrame([{'day': d, 'signups': dow.get(d, 0)} for d in day_order])

        fig = px.bar(dow_df, x='day', y='signups', color='signups',
                    color_continuous_scale='Blues')
        apply_chart_style(fig, title="Signup Day Distribution", height=380)
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, width='stretch')

    # Acquisition Sources tab (only if subscriber_details available)
    if not subscriber_details.empty:
        with tab2:
            st.subheader("Acquisition Source Analysis")
            st.markdown("Where your subscribers come from (free subscription sources)")

            # Source distribution
            all_source_counts = subscriber_details['source_free'].value_counts()

            if len(all_source_counts) > 0:
                col1, col2 = st.columns(2)

                # For bar chart, show top 10
                bar_source_counts = all_source_counts.head(10)

                with col1:
                    fig = px.bar(
                        x=bar_source_counts.values,
                        y=bar_source_counts.index,
                        orientation='h',
                        labels={'x': 'Subscribers', 'y': 'Source'},
                        color=bar_source_counts.values,
                        color_continuous_scale='Blues'
                    )
                    apply_chart_style(fig, title='Top Acquisition Sources', height=450)
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                    fig.update_coloraxes(showscale=False)
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    # For pie chart, show top 5 and group rest as "Other"
                    top_sources = all_source_counts.head(5)
                    other_count = all_source_counts.iloc[5:].sum() if len(all_source_counts) > 5 else 0

                    pie_names = list(top_sources.index)
                    pie_values = list(top_sources.values)

                    if other_count > 0:
                        pie_names.append('Other')
                        pie_values.append(other_count)

                    # Shorten long source names for cleaner display
                    display_names = []
                    for name in pie_names:
                        if name == 'Other':
                            display_names.append('Other')
                        elif len(name) > 20:
                            # Shorten common prefixes
                            short = name.replace('substack-', '').replace('-', ' ').title()
                            display_names.append(short[:18] + '...' if len(short) > 20 else short)
                        else:
                            display_names.append(name.replace('-', ' ').title())

                    fig = go.Figure(data=[go.Pie(
                        labels=display_names,
                        values=pie_values,
                        hole=0.4,
                        textinfo='label+percent',
                        textposition='outside',
                        textfont=dict(size=18),
                        outsidetextfont=dict(size=18),
                        marker=dict(colors=CHART_PALETTE[:len(pie_values)]),
                        pull=[0.02] * len(pie_values)  # Slight separation
                    )])
                    apply_chart_style(fig, title='Source Distribution', height=500)
                    fig.update_layout(
                        showlegend=False,
                        margin=dict(l=100, r=100, t=80, b=100)
                    )
                    st.plotly_chart(fig, width='stretch')

                # Source engagement quality
                st.subheader("Engagement by Acquisition Source")
                st.markdown("Which sources bring the most engaged subscribers?")

                source_engagement = subscriber_details.groupby('source_free').agg(
                    total_subscribers=('email', 'count'),
                    avg_open_rate=('open_rate_6mo', 'mean'),
                    active_30d=('is_engaged_30d', 'sum'),
                    total_opens=('total_emails_opened', 'sum'),
                    total_post_views=('post_views', 'sum'),
                    total_comments=('comments', 'sum'),
                    total_shares=('shares', 'sum')
                ).reset_index()

                source_engagement['active_rate'] = (
                    source_engagement['active_30d'] / source_engagement['total_subscribers'] * 100
                ).round(1)
                source_engagement['avg_open_rate'] = (source_engagement['avg_open_rate'] * 100).round(1)

                # Filter to sources with at least 10 subscribers for meaningful analysis
                source_engagement = source_engagement[source_engagement['total_subscribers'] >= 10]
                source_engagement = source_engagement.sort_values('total_subscribers', ascending=False)

                if not source_engagement.empty:
                    # Engagement quality chart
                    fig = px.scatter(
                        source_engagement.head(15),
                        x='total_subscribers',
                        y='active_rate',
                        size='total_opens',
                        color='avg_open_rate',
                        hover_data=['source_free', 'total_comments', 'total_shares'],
                        labels={
                            'total_subscribers': 'Total Subscribers',
                            'active_rate': 'Active Rate (30d) %',
                            'avg_open_rate': 'Avg Open Rate %'
                        },
                        color_continuous_scale='RdYlGn'
                    )
                    apply_chart_style(fig, title='Source Quality: Size vs Engagement', height=420)
                    fig.update_coloraxes(colorbar_title_font_size=13, colorbar_tickfont_size=12)
                    st.plotly_chart(fig, width='stretch')

                    # Table view
                    display_df = source_engagement[['source_free', 'total_subscribers', 'active_rate',
                                                    'avg_open_rate', 'total_post_views', 'total_comments']].head(15)
                    display_df.columns = ['Source', 'Subscribers', 'Active Rate %', 'Open Rate %',
                                         'Post Views', 'Comments']
                    st.dataframe(display_df, width='stretch', hide_index=True)

    # Plan Distribution tab
    plan_tab = tab3 if not subscriber_details.empty else tab2
    with plan_tab:
        plan_dist = analysis['acquisition']['plan_distribution']
        plan_df = pd.DataFrame([{'plan': k, 'count': v} for k, v in plan_dist.items()])
        plan_df['plan'] = plan_df['plan'].replace({'other': 'Free', 'Other': 'Free'}).str.title()
        plan_df = plan_df.sort_values('count', ascending=True)  # Sort for horizontal bar
        total = plan_df['count'].sum()
        plan_df['percentage'] = (plan_df['count'] / total * 100).round(1)
        plan_df['label'] = plan_df.apply(lambda x: f"{x['count']:,} ({x['percentage']}%)", axis=1)

        fig = go.Figure(data=[go.Bar(
            x=plan_df['count'],
            y=plan_df['plan'],
            orientation='h',
            text=plan_df['label'],
            textposition='outside',
            textfont=dict(size=16),
            marker=dict(
                color=plan_df['count'],
                colorscale='Blues',
                showscale=False
            )
        )])
        apply_chart_style(fig, title="Plan Distribution", height=max(300, len(plan_df) * 60 + 150))
        fig.update_layout(
            xaxis_title="Subscribers",
            yaxis_title="",
            margin=dict(l=20, r=120, t=80, b=60)
        )
        fig.update_yaxes(tickfont=dict(size=16))
        st.plotly_chart(fig, width='stretch')

    # Conversion Timing tab
    conversion_tab = tab4 if not subscriber_details.empty else tab3
    with conversion_tab:
        st.subheader("Time to Conversion")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Average Days to Convert",
                     f"{analysis['acquisition']['avg_days_to_convert']} days")
        with col2:
            st.metric("Median Days to Convert",
                     f"{analysis['acquisition']['median_days_to_convert']} days")

        # Conversion timing histogram
        paid_subs = data['subscribers'][data['subscribers']['is_paid']].copy()
        if not paid_subs.empty:
            paid_subs['days_to_convert'] = (
                paid_subs['first_payment_at'] - paid_subs['created_at']
            ).dt.days

            # Compute histogram bins manually for color scaling
            days_data = paid_subs['days_to_convert'].dropna()
            counts, bin_edges = np.histogram(days_data, bins=20)
            bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]
            bin_labels = [f"{int(bin_edges[i])}-{int(bin_edges[i+1])}" for i in range(len(bin_edges)-1)]

            fig = go.Figure(data=[go.Bar(
                x=bin_centers,
                y=counts,
                text=counts,
                textposition='outside',
                textfont=dict(size=14),
                marker=dict(
                    color=counts,
                    colorscale='Blues',
                    showscale=False,
                    line=dict(color='white', width=1)
                ),
                width=(bin_edges[1] - bin_edges[0]) * 0.85,
                customdata=bin_labels,
                hovertemplate='<b>Days:</b> %{customdata}<br><b>Subscribers:</b> %{y}<extra></extra>'
            )])
            apply_chart_style(fig, title="Time to Conversion Distribution", height=420)
            fig.update_layout(
                xaxis_title="Days to Convert",
                yaxis_title="Count",
                bargap=0.1
            )
            st.plotly_chart(fig, width='stretch')


def render_trends(analysis, data):
    """Render engagement trends page."""
    st.markdown('<h2 class="section-header">Engagement Trends</h2>', unsafe_allow_html=True)

    # Monthly open rate trend
    st.subheader("Monthly Open Rate Trend")
    monthly = analysis['trends']['monthly_engagement']

    if not monthly.empty:
        monthly_reset = monthly.reset_index()
        monthly_reset['month'] = monthly_reset['month'].astype(str)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_reset['month'],
            y=monthly_reset['open_rate'] * 100,
            mode='lines+markers',
            name='Open Rate',
            line=dict(color=CHART_COLORS['primary'], width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(26, 26, 46, 0.15)'
        ))
        fig.add_hline(y=45, line_dash="dash", line_color=CHART_COLORS['success'],
                     annotation_text="Excellent (45%)", annotation_font_size=13)
        fig.add_hline(y=30, line_dash="dash", line_color=CHART_COLORS['warning'],
                     annotation_text="Good (30%)", annotation_font_size=13)
        apply_chart_style(fig, title="Monthly Open Rate Trend", height=420)
        fig.update_layout(yaxis_title='Open Rate (%)', xaxis_title='Month')
        st.plotly_chart(fig, width='stretch')

    # Deliveries vs Opens over time
    if not monthly.empty:
        monthly_reset = monthly.reset_index()
        monthly_reset['month'] = monthly_reset['month'].astype(str)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(x=monthly_reset['month'], y=monthly_reset['delivers'],
                  name='Delivered', marker_color=CHART_COLORS['info'], opacity=0.7),
            secondary_y=False
        )
        fig.add_trace(
            go.Bar(x=monthly_reset['month'], y=monthly_reset['opens'],
                  name='Opened', marker_color=CHART_COLORS['accent'], opacity=0.9),
            secondary_y=False
        )
        apply_chart_style(fig, title="Email Activity Over Time", height=420)
        fig.update_layout(
            barmode='group',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center')
        )
        fig.update_yaxes(title_text="Count", secondary_y=False)
        st.plotly_chart(fig, width='stretch')

    # Active subscriber ratio
    st.markdown("---")
    st.subheader("Subscriber Activity")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Active (30 days)",
                 f"{analysis['trends']['recent_openers']:,}",
                 f"{analysis['trends']['active_ratio_30d_pct']} of total")

    with col2:
        st.metric("Total Subscribers",
                 f"{analysis['trends']['total_subscribers']:,}")

    with col3:
        inactive = analysis['trends']['total_subscribers'] - analysis['trends']['recent_openers']
        st.metric("Inactive (30 days)",
                 f"{inactive:,}",
                 f"{inactive/analysis['trends']['total_subscribers']*100:.1f}% of total")


def render_segments(analysis, data):
    """Render subscriber segments page."""
    st.markdown('<h2 class="section-header">Subscriber Segments</h2>', unsafe_allow_html=True)

    subscriber_details = data.get('subscriber_details', pd.DataFrame())
    se = analysis['super_engagers']

    # Segment overview
    col1, col2, col3 = st.columns(3)

    total = se['total_analyzed']
    super_count = se['super_engager_count']
    at_risk = se['at_risk_count']
    average = total - super_count - at_risk

    with col1:
        st.metric("Super Engagers", f"{super_count}",
                 f"{super_count/total*100:.1f}% of analyzed",
                 help="80%+ open rate")

    with col2:
        st.metric("Average Engagers", f"{average}",
                 f"{average/total*100:.1f}% of analyzed")

    with col3:
        st.metric("At-Risk", f"{at_risk}",
                 f"{at_risk/total*100:.1f}% of analyzed",
                 help="<20% open rate")

    # Pie chart
    segment_names = ['Super Engagers (80%+)', 'Average', 'At-Risk (<20%)']
    segment_values = [super_count, average, at_risk]
    segment_colors = [CHART_COLORS['success'], CHART_COLORS['info'], CHART_COLORS['danger']]

    fig = go.Figure(data=[go.Pie(
        labels=segment_names,
        values=segment_values,
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(size=18),
        outsidetextfont=dict(size=18),
        marker=dict(colors=segment_colors),
        pull=[0.02] * len(segment_values)
    )])
    apply_chart_style(fig, title="Subscriber Engagement Segments", height=500)
    fig.update_layout(
        showlegend=False,
        margin=dict(l=100, r=100, t=80, b=100)
    )
    st.plotly_chart(fig, width='stretch')

    # Super engager details
    st.markdown("---")
    st.subheader("Super Engager Insights")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Super Engagers Who Are Paid",
                 f"{se['super_engager_paid_pct']:.1f}%")

    # Show super engager list
    if not se['super_engagers'].empty:
        st.subheader("Super Engager List")
        display_se = se['super_engagers'].copy()
        display_se['open_rate_pct'] = (display_se['open_rate'] * 100).round(1).astype(str) + '%'
        display_se = display_se[['email', 'posts_opened', 'posts_delivered',
                                 'open_rate_pct', 'is_paid']].sort_values(
                                     'posts_opened', ascending=False)
        st.dataframe(display_se.head(50), width='stretch', hide_index=True)

    # Enhanced segments from subscriber_details
    if not subscriber_details.empty:
        st.markdown("---")
        st.subheader("Geographic & Engagement Segments")

        details = subscriber_details.copy()

        # Map ISO 2-letter country codes to continents/regions
        continent_mapping = {
            # North America
            'US': 'North America', 'CA': 'North America', 'MX': 'North America',
            # Europe
            'GB': 'Europe', 'DE': 'Europe', 'FR': 'Europe', 'NL': 'Europe',
            'ES': 'Europe', 'IT': 'Europe', 'PL': 'Europe', 'SE': 'Europe',
            'BE': 'Europe', 'CH': 'Europe', 'AT': 'Europe', 'NO': 'Europe',
            'DK': 'Europe', 'FI': 'Europe', 'IE': 'Europe', 'PT': 'Europe',
            'CZ': 'Europe', 'RO': 'Europe', 'GR': 'Europe', 'HU': 'Europe',
            'SK': 'Europe', 'BG': 'Europe', 'HR': 'Europe', 'SI': 'Europe',
            'LT': 'Europe', 'LV': 'Europe', 'EE': 'Europe', 'RS': 'Europe',
            'UA': 'Europe', 'BY': 'Europe', 'RU': 'Europe',
            # South Asia
            'IN': 'South Asia', 'PK': 'South Asia', 'BD': 'South Asia',
            'LK': 'South Asia', 'NP': 'South Asia',
            # East Asia
            'JP': 'East Asia', 'KR': 'East Asia', 'CN': 'East Asia',
            'TW': 'East Asia', 'HK': 'East Asia', 'MO': 'East Asia',
            # Southeast Asia
            'SG': 'Southeast Asia', 'MY': 'Southeast Asia', 'ID': 'Southeast Asia',
            'TH': 'Southeast Asia', 'VN': 'Southeast Asia', 'PH': 'Southeast Asia',
            'MM': 'Southeast Asia', 'KH': 'Southeast Asia', 'LA': 'Southeast Asia',
            # Oceania
            'AU': 'Oceania', 'NZ': 'Oceania',
            # Middle East
            'IL': 'Middle East', 'AE': 'Middle East', 'SA': 'Middle East',
            'TR': 'Middle East', 'IR': 'Middle East', 'IQ': 'Middle East',
            'JO': 'Middle East', 'LB': 'Middle East', 'QA': 'Middle East',
            'KW': 'Middle East', 'BH': 'Middle East', 'OM': 'Middle East',
            # Latin America
            'BR': 'Latin America', 'AR': 'Latin America', 'CO': 'Latin America',
            'CL': 'Latin America', 'PE': 'Latin America', 'VE': 'Latin America',
            'EC': 'Latin America', 'UY': 'Latin America', 'PY': 'Latin America',
            'BO': 'Latin America', 'CR': 'Latin America', 'PA': 'Latin America',
            'GT': 'Latin America', 'DO': 'Latin America', 'PR': 'Latin America',
            # Africa
            'ZA': 'Africa', 'NG': 'Africa', 'KE': 'Africa', 'EG': 'Africa',
            'MA': 'Africa', 'GH': 'Africa', 'TZ': 'Africa', 'ET': 'Africa',
            'UG': 'Africa', 'DZ': 'Africa', 'TN': 'Africa',
        }

        # Country code to name mapping for display
        country_names = {
            'US': 'United States', 'CA': 'Canada', 'MX': 'Mexico',
            'GB': 'United Kingdom', 'DE': 'Germany', 'FR': 'France', 'NL': 'Netherlands',
            'ES': 'Spain', 'IT': 'Italy', 'PL': 'Poland', 'SE': 'Sweden',
            'BE': 'Belgium', 'CH': 'Switzerland', 'AT': 'Austria', 'NO': 'Norway',
            'DK': 'Denmark', 'FI': 'Finland', 'IE': 'Ireland', 'PT': 'Portugal',
            'IN': 'India', 'PK': 'Pakistan', 'BD': 'Bangladesh',
            'JP': 'Japan', 'KR': 'South Korea', 'CN': 'China', 'TW': 'Taiwan', 'HK': 'Hong Kong',
            'SG': 'Singapore', 'MY': 'Malaysia', 'ID': 'Indonesia',
            'TH': 'Thailand', 'VN': 'Vietnam', 'PH': 'Philippines',
            'AU': 'Australia', 'NZ': 'New Zealand',
            'IL': 'Israel', 'AE': 'UAE', 'SA': 'Saudi Arabia', 'TR': 'Turkey',
            'BR': 'Brazil', 'AR': 'Argentina', 'CO': 'Colombia', 'CL': 'Chile',
            'ZA': 'South Africa', 'NG': 'Nigeria', 'KE': 'Kenya', 'EG': 'Egypt',
            'RU': 'Russia', 'UA': 'Ukraine',
        }

        if 'country' in details.columns:
            details['continent'] = details['country'].map(continent_mapping).fillna('Other')

            # Continent breakdown
            tab1, tab2, tab3 = st.tabs(["By Region", "Engagement by Region", "Activity Breakdown"])

            with tab1:
                col1, col2 = st.columns(2)

                with col1:
                    # Subscriber count by continent
                    continent_counts = details['continent'].value_counts()

                    fig = go.Figure(data=[go.Pie(
                        labels=continent_counts.index,
                        values=continent_counts.values,
                        hole=0.4,
                        textinfo='label+percent',
                        textposition='outside',
                        textfont=dict(size=18),
                        outsidetextfont=dict(size=18),
                        marker=dict(colors=CHART_PALETTE[:len(continent_counts)]),
                        pull=[0.02] * len(continent_counts)
                    )])
                    apply_chart_style(fig, title='Subscribers by Region', height=500)
                    fig.update_layout(
                        showlegend=False,
                        margin=dict(l=100, r=100, t=80, b=100)
                    )
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    # Bar chart
                    fig = px.bar(
                        x=continent_counts.index,
                        y=continent_counts.values,
                        color=continent_counts.values,
                        color_continuous_scale='Blues',
                        labels={'x': 'Region', 'y': 'Subscribers'}
                    )
                    apply_chart_style(fig, title='Subscribers by Region', height=420)
                    fig.update_coloraxes(showscale=False)
                    st.plotly_chart(fig, width='stretch')

                # Top countries
                st.subheader("Top Countries")
                country_counts = details['country'].value_counts().head(15)
                country_df = pd.DataFrame({
                    'Code': country_counts.index,
                    'Country': [country_names.get(c, c) for c in country_counts.index],
                    'Region': [continent_mapping.get(c, 'Other') for c in country_counts.index],
                    'Subscribers': country_counts.values,
                    'Percentage': (country_counts.values / len(details) * 100).round(1)
                })
                st.dataframe(country_df[['Country', 'Region', 'Subscribers', 'Percentage']], width='stretch', hide_index=True)

            with tab2:
                st.subheader("Engagement Metrics by Region")

                # Aggregate metrics by continent
                region_stats = details.groupby('continent').agg(
                    total_subscribers=('email', 'count'),
                    avg_open_rate=('open_rate_6mo', 'mean'),
                    total_comments=('comments', 'sum'),
                    total_shares=('shares', 'sum'),
                    total_post_views=('post_views', 'sum'),
                    total_links_clicked=('links_clicked', 'sum'),
                    active_30d=('is_engaged_30d', 'sum'),
                    paid_count=('is_paid', 'sum')
                ).reset_index()

                region_stats['active_rate'] = (region_stats['active_30d'] / region_stats['total_subscribers'] * 100).round(1)
                region_stats['avg_open_rate'] = (region_stats['avg_open_rate'] * 100).round(1)
                region_stats['paid_rate'] = (region_stats['paid_count'] / region_stats['total_subscribers'] * 100).round(2)

                # Scatter plot: subscribers vs engagement
                fig = px.scatter(
                    region_stats,
                    x='total_subscribers',
                    y='active_rate',
                    size='total_comments',
                    color='avg_open_rate',
                    hover_data=['continent', 'total_shares', 'paid_count'],
                    labels={
                        'total_subscribers': 'Total Subscribers',
                        'active_rate': 'Active Rate (30d) %',
                        'avg_open_rate': 'Avg Open Rate %'
                    },
                    color_continuous_scale='RdYlGn'
                )
                apply_chart_style(fig, title='Region Quality: Size vs Engagement', height=420)
                fig.update_coloraxes(colorbar_title_font_size=13, colorbar_tickfont_size=12)
                st.plotly_chart(fig, width='stretch')

                # Table view
                display_cols = ['continent', 'total_subscribers', 'active_rate', 'avg_open_rate',
                               'total_comments', 'total_shares', 'paid_count']
                display_df = region_stats[display_cols].copy()
                display_df.columns = ['Region', 'Subscribers', 'Active %', 'Open Rate %',
                                     'Comments', 'Shares', 'Paid']
                display_df = display_df.sort_values('Subscribers', ascending=False)
                st.dataframe(display_df, width='stretch', hide_index=True)

            with tab3:
                st.subheader("Activity Breakdown by Region")

                # Stacked bar chart of activity types by region
                activity_by_region = details.groupby('continent').agg(
                    email_openers=('is_engaged_30d', 'sum'),
                    post_viewers=('post_views_30d', lambda x: (x > 0).sum()),
                    commenters=('comments_30d', lambda x: (x > 0).sum()),
                    sharers=('shares_30d', lambda x: (x > 0).sum())
                ).reset_index()

                activity_melted = activity_by_region.melt(
                    id_vars='continent',
                    value_vars=['email_openers', 'post_viewers', 'commenters', 'sharers'],
                    var_name='Activity Type',
                    value_name='Count'
                )

                fig = px.bar(
                    activity_melted,
                    x='continent',
                    y='Count',
                    color='Activity Type',
                    barmode='group',
                    color_discrete_sequence=[CHART_COLORS['info'], CHART_COLORS['success'], CHART_COLORS['warning'], CHART_COLORS['accent']]
                )
                apply_chart_style(fig, title='Activity Types by Region (30d)', height=450)
                fig.update_layout(legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center'))
                st.plotly_chart(fig, width='stretch')

                # Engagement depth by region
                st.subheader("Engagement Depth")
                details['engagement_depth'] = (
                    (details['emails_opened_30d'] > 0).astype(int) +
                    (details['post_views_30d'] > 0).astype(int) +
                    (details['comments_30d'] > 0).astype(int) +
                    (details['shares_30d'] > 0).astype(int)
                )

                depth_by_region = details.groupby(['continent', 'engagement_depth']).size().reset_index(name='count')

                fig = px.bar(
                    depth_by_region,
                    x='continent',
                    y='count',
                    color='engagement_depth',
                    barmode='stack',
                    color_continuous_scale='Blues',
                    labels={'engagement_depth': 'Channels Active', 'count': 'Subscribers'}
                )
                apply_chart_style(fig, title='Engagement Depth by Region', height=420)
                fig.update_coloraxes(colorbar_title_font_size=13, colorbar_tickfont_size=12)
                st.plotly_chart(fig, width='stretch')

        else:
            st.info("No country data available in subscriber_details")


def render_engagement_flow(data):
    """Render Sankey diagrams showing subscriber engagement flows."""
    st.markdown('<h2 class="section-header">Engagement Flow</h2>', unsafe_allow_html=True)
    st.caption("Visualize how subscribers flow between engagement states")

    # Use subscriber_details if available, otherwise fall back to opens/delivers
    subscriber_details = data.get('subscriber_details', pd.DataFrame())

    if not subscriber_details.empty:
        st.success(f"Using enriched subscriber details data ({len(subscriber_details):,} subscribers)")

        # Define engagement based on 60-day inactivity threshold
        # Engaged = opened email OR viewed post OR commented OR shared in last 60 days
        details = subscriber_details.copy()

        # Calculate engagement status (60 days = ~2 months of activity)
        details['is_engaged'] = (
            (details['emails_opened_30d'] > 0) |
            (details['post_views_30d'] > 0) |
            (details['comments_30d'] > 0) |
            (details['shares_30d'] > 0)
        )

        # Define activity types
        details['is_email_opener'] = details['total_emails_opened'] > 0
        details['is_post_viewer'] = details['post_views'] > 0
        details['is_commenter'] = details['comments'] > 0
        details['is_sharer'] = details['shares'] > 0

        # Overview metrics
        st.subheader("Engagement Overview (Last 30 Days)")
        col1, col2, col3, col4 = st.columns(4)

        engaged = details['is_engaged'].sum()
        disengaged = len(details) - engaged

        with col1:
            st.metric("Engaged", f"{engaged:,}",
                     f"{engaged/len(details)*100:.1f}%",
                     help="Active in last 30 days (opened, viewed, commented, or shared)")

        with col2:
            st.metric("Disengaged", f"{disengaged:,}",
                     f"{disengaged/len(details)*100:.1f}%")

        with col3:
            free_engaged = details[(details['is_free']) & (details['is_engaged'])].shape[0]
            free_total = details['is_free'].sum()
            st.metric("Free Engaged Rate",
                     f"{free_engaged/free_total*100:.1f}%" if free_total > 0 else "N/A")

        with col4:
            paid_engaged = details[(details['is_paid']) & (details['is_engaged'])].shape[0]
            paid_total = details['is_paid'].sum()
            st.metric("Paid Engaged Rate",
                     f"{paid_engaged/paid_total*100:.1f}%" if paid_total > 0 else "N/A")

        st.markdown("---")

        # Sankey Diagram 1: Subscriber Type → Engagement Status → Activity Type
        st.subheader("Subscriber Flow: Type → Engagement → Activity")

        # Build Sankey data
        labels = [
            'Free Subscribers',        # 0
            'Paid Subscribers',        # 1
            'Engaged',                 # 2
            'Disengaged',              # 3
            'Email Openers',           # 4
            'Post Viewers',            # 5
            'Commenters',              # 6
            'Sharers',                 # 7
            'No Activity'              # 8
        ]

        # Calculate flows
        free_engaged = details[(details['is_free']) & (details['is_engaged'])].shape[0]
        free_disengaged = details[(details['is_free']) & (~details['is_engaged'])].shape[0]
        paid_engaged = details[(details['is_paid']) & (details['is_engaged'])].shape[0]
        paid_disengaged = details[(details['is_paid']) & (~details['is_engaged'])].shape[0]

        engaged_df = details[details['is_engaged']]
        engaged_openers = engaged_df['is_email_opener'].sum()
        engaged_viewers = engaged_df[~engaged_df['is_email_opener'] & engaged_df['is_post_viewer']].shape[0]
        engaged_commenters = engaged_df['is_commenter'].sum()
        engaged_sharers = engaged_df['is_sharer'].sum()

        disengaged_df = details[~details['is_engaged']]
        disengaged_openers = disengaged_df['is_email_opener'].sum()  # Opened before but not recently
        disengaged_viewers = disengaged_df[disengaged_df['is_post_viewer']].shape[0]
        disengaged_no_activity = disengaged_df[
            ~disengaged_df['is_email_opener'] &
            ~disengaged_df['is_post_viewer'] &
            ~disengaged_df['is_commenter'] &
            ~disengaged_df['is_sharer']
        ].shape[0]

        source = [0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3]
        target = [2, 3, 2, 3, 4, 5, 6, 7, 4, 5, 8]
        value = [
            free_engaged, free_disengaged,
            paid_engaged, paid_disengaged,
            engaged_openers, engaged_viewers, engaged_commenters, engaged_sharers,
            disengaged_openers, disengaged_viewers, disengaged_no_activity
        ]

        # Filter out zero values
        filtered = [(s, t, v) for s, t, v in zip(source, target, value) if v > 0]
        if filtered:
            source, target, value = zip(*filtered)

            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=20,
                    thickness=25,
                    line=dict(color="white", width=1),
                    label=labels,
                    color=[
                        CHART_COLORS['info'],      # Free Subscribers
                        CHART_COLORS['accent'],    # Paid Subscribers
                        CHART_COLORS['success'],   # Engaged
                        '#6c757d',                 # Disengaged
                        '#9b59b6',                 # Email Opens
                        '#1abc9c',                 # Post Views
                        '#f39c12',                 # Comments
                        '#e91e63',                 # Shares
                        '#bdc3c7'                  # No Activity
                    ]
                ),
                link=dict(
                    source=list(source),
                    target=list(target),
                    value=list(value),
                    color=['rgba(52, 152, 219, 0.5)'] * 2 +
                          ['rgba(233, 69, 96, 0.5)'] * 2 +
                          ['rgba(155, 89, 182, 0.5)', 'rgba(26, 188, 156, 0.5)',
                           'rgba(243, 156, 18, 0.5)', 'rgba(233, 30, 99, 0.5)'] +
                          ['rgba(108, 117, 125, 0.4)'] * 3
                ),
                textfont=dict(size=14, color='#212529')
            )])

            apply_chart_style(fig, title="Subscriber Engagement Flow", height=520)
            fig.update_layout(font=dict(size=14))
            st.plotly_chart(fig, width='stretch')

        st.markdown("---")

        # Sankey Diagram 2: Acquisition Source → Engagement
        st.subheader("Acquisition Channel → Engagement")

        # Parse source channels
        source_counts = details.groupby(['source_free', 'is_engaged']).size().reset_index(name='count')

        if not source_counts.empty and 'source_free' in source_counts.columns:
            # Get unique sources
            sources = details['source_free'].dropna().unique()
            sources = [s for s in sources if pd.notna(s) and s != ''][:8]  # Top 8 sources

            if len(sources) > 0:
                source_labels = list(sources) + ['Engaged', 'Disengaged']
                n_sources = len(sources)

                source_idx = []
                target_idx = []
                values = []

                for i, src in enumerate(sources):
                    src_engaged = details[(details['source_free'] == src) & (details['is_engaged'])].shape[0]
                    src_disengaged = details[(details['source_free'] == src) & (~details['is_engaged'])].shape[0]

                    if src_engaged > 0:
                        source_idx.append(i)
                        target_idx.append(n_sources)  # Engaged
                        values.append(src_engaged)

                    if src_disengaged > 0:
                        source_idx.append(i)
                        target_idx.append(n_sources + 1)  # Disengaged
                        values.append(src_disengaged)

                if values:
                    # Distinct colors for each acquisition source
                    source_colors = [
                        '#3498db', '#e94560', '#9b59b6', '#1abc9c',
                        '#f39c12', '#e91e63', '#00bcd4', '#8bc34a'
                    ][:n_sources]

                    # Link colors match source colors with transparency
                    link_colors = []
                    for s, t in zip(source_idx, target_idx):
                        base_color = source_colors[s]
                        # Convert hex to rgba
                        r, g, b = int(base_color[1:3], 16), int(base_color[3:5], 16), int(base_color[5:7], 16)
                        link_colors.append(f'rgba({r}, {g}, {b}, 0.5)')

                    fig2 = go.Figure(data=[go.Sankey(
                        node=dict(
                            pad=20,
                            thickness=25,
                            line=dict(color="white", width=1),
                            label=source_labels,
                            color=source_colors + [CHART_COLORS['success'], CHART_COLORS['danger']]
                        ),
                        link=dict(
                            source=source_idx,
                            target=target_idx,
                            value=values,
                            color=link_colors
                        ),
                        textfont=dict(size=14, color='#212529')
                    )])

                    apply_chart_style(fig2, title="Acquisition Source → Engagement", height=480)
                    fig2.update_layout(font=dict(size=14))
                    st.plotly_chart(fig2, width='stretch')

        st.markdown("---")

        # Engagement Activity Breakdown
        st.subheader("Multi-Channel Engagement Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # Activity breakdown for engaged subscribers
            activity_data = {
                'Activity': ['Email Opens', 'Post Views', 'Comments', 'Shares'],
                'Total': [
                    details['total_emails_opened'].sum(),
                    details['post_views'].sum(),
                    details['comments'].sum(),
                    details['shares'].sum()
                ],
                'Last 30d': [
                    details['emails_opened_30d'].sum(),
                    details['post_views_30d'].sum(),
                    details['comments_30d'].sum(),
                    details['shares_30d'].sum()
                ]
            }
            activity_df = pd.DataFrame(activity_data)

            fig3 = go.Figure()
            fig3.add_trace(go.Bar(name='Total', x=activity_df['Activity'], y=activity_df['Total'],
                                 marker_color=CHART_COLORS['info'], opacity=0.7))
            fig3.add_trace(go.Bar(name='Last 30 Days', x=activity_df['Activity'], y=activity_df['Last 30d'],
                                 marker_color=CHART_COLORS['accent']))
            apply_chart_style(fig3, title='Engagement by Activity Type', height=380)
            fig3.update_layout(
                barmode='group',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center')
            )
            st.plotly_chart(fig3, width='stretch')

        with col2:
            # Subscribers by engagement breadth
            details['engagement_channels'] = (
                details['is_email_opener'].astype(int) +
                details['is_post_viewer'].astype(int) +
                details['is_commenter'].astype(int) +
                details['is_sharer'].astype(int)
            )

            channel_dist = details['engagement_channels'].value_counts().sort_index()

            fig4 = px.bar(
                x=channel_dist.index,
                y=channel_dist.values,
                labels={'x': 'Number of Engagement Channels', 'y': 'Subscribers'},
                color=channel_dist.values,
                color_continuous_scale='Blues'
            )
            apply_chart_style(fig4, title='Engagement Breadth', height=380)
            fig4.update_coloraxes(showscale=False)
            st.plotly_chart(fig4, width='stretch')

        # At-risk segment analysis
        st.markdown("---")
        st.subheader("At-Risk Segment: Previously Engaged, Now Silent")

        at_risk = details[
            (details['total_emails_opened'] > 0) &  # Previously opened
            (details['emails_opened_30d'] == 0) &   # Not opened recently
            (details['post_views_30d'] == 0) &      # Not viewed recently
            (~details['is_paid'])                    # Focus on free (paid need different treatment)
        ]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("At-Risk Free Subscribers", f"{len(at_risk):,}")

        with col2:
            avg_historical = at_risk['total_emails_opened'].mean() if len(at_risk) > 0 else 0
            st.metric("Avg Historical Opens", f"{avg_historical:.1f}")

        with col3:
            if len(at_risk) > 0 and 'last_email_open' in at_risk.columns:
                valid_dates = at_risk['last_email_open'].dropna()
                if len(valid_dates) > 0:
                    try:
                        # Convert to tz-naive for comparison
                        dates_naive = valid_dates.dt.tz_localize(None) if valid_dates.dt.tz is None else valid_dates.dt.tz_convert(None)
                        avg_days = (pd.Timestamp.now() - dates_naive.mean()).days
                        st.metric("Avg Days Since Last Open", f"{avg_days:.0f}")
                    except Exception:
                        st.metric("Avg Days Since Last Open", "N/A")
                else:
                    st.metric("Avg Days Since Last Open", "N/A")
            else:
                st.metric("Avg Days Since Last Open", "N/A")

    else:
        # Fallback to basic opens/delivers data
        st.warning("No subscriber_details.csv found. Using basic engagement data.")
        st.info("Upload subscriber_details.csv for richer engagement flow analysis.")

        opens = data['opens']
        delivers = data['delivers']
        subscribers = data['subscribers']

        if not opens.empty and not delivers.empty:
            # Basic Sankey with opens data
            sub_opens = opens.groupby('email').agg(
                last_open=('timestamp', 'max'),
                total_opens=('post_id', 'count')
            ).reset_index()

            sub_delivers = delivers.groupby('email').agg(
                posts_delivered=('post_id', 'nunique')
            ).reset_index()

            engagement = subscribers.merge(sub_delivers, on='email', how='left')
            engagement = engagement.merge(sub_opens, on='email', how='left')

            now = pd.Timestamp.now(tz='UTC')
            engagement['days_since_last_open'] = (now - engagement['last_open']).dt.days
            engagement['is_engaged'] = engagement['days_since_last_open'] <= 60
            engagement['never_opened'] = engagement['last_open'].isna()

            # Simple Sankey
            engaged = engagement['is_engaged'].sum()
            disengaged = (~engagement['is_engaged'] & ~engagement['never_opened']).sum()
            never = engagement['never_opened'].sum()

            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=20,
                    thickness=25,
                    line=dict(color="white", width=1),
                    label=['All Subscribers', 'Engaged (60d)', 'Disengaged', 'Never Opened'],
                    color=[CHART_COLORS['info'], CHART_COLORS['success'], CHART_COLORS['warning'], CHART_COLORS['danger']]
                ),
                link=dict(
                    source=[0, 0, 0],
                    target=[1, 2, 3],
                    value=[engaged, disengaged, never],
                    color=['rgba(46, 204, 113, 0.5)', 'rgba(243, 156, 18, 0.5)', 'rgba(231, 76, 60, 0.5)']
                ),
                textfont=dict(size=14, color='#212529')
            )])

            apply_chart_style(fig, title="Basic Engagement Flow", height=420)
            fig.update_layout(font=dict(size=14))
            st.plotly_chart(fig, width='stretch')


def render_inactive_subscribers(data, analysis):
    """Render inactive subscribers analysis for list cleaning using subscriber_details."""
    st.markdown('<h2 class="section-header">Inactive Subscribers</h2>', unsafe_allow_html=True)
    st.caption("Identify subscribers who may be candidates for removal to improve list health")

    subscriber_details = data.get('subscriber_details', pd.DataFrame())

    if not subscriber_details.empty:
        # Use subscriber_details for richer analysis
        details = subscriber_details.copy()

        # Filter out subscribers with null/zero emails received (tracking issues)
        excluded_tracking = details[details['emails_received_6mo'].isna() | (details['emails_received_6mo'] == 0)].shape[0]
        details = details[details['emails_received_6mo'] > 0].copy()

        # Calculate days since last open
        now = pd.Timestamp.now()
        if 'last_email_open' in details.columns:
            # Handle timezone-aware dates
            last_open = details['last_email_open'].copy()
            if last_open.dt.tz is not None:
                last_open = last_open.dt.tz_convert(None)
            details['days_since_last_open'] = (now - last_open).dt.days

        # Identify new subscribers (last 30 days) to exclude from inactive analysis
        if 'start_date' in details.columns:
            start_dates = details['start_date'].copy()
            if start_dates.dt.tz is not None:
                start_dates = start_dates.dt.tz_convert(None)
            details['days_since_signup'] = (now - start_dates).dt.days
            details['is_new_subscriber'] = details['days_since_signup'] <= 30
        else:
            details['is_new_subscriber'] = False

        # Minimum emails threshold - require >8 emails received to be considered for inactivity
        MIN_EMAILS = 8
        details['sufficient_emails'] = details['emails_received_6mo'] > MIN_EMAILS

        # Show exclusion info
        excluded_new = details['is_new_subscriber'].sum()
        excluded_few_emails = (~details['sufficient_emails']).sum()

        st.info(f"Exclusions: {excluded_tracking} with no delivery data, {excluded_new} new subscribers (last 30 days), {excluded_few_emails} with <={MIN_EMAILS} emails received")

        # === NEW CATEGORIZATION CRITERIA ===
        # 1. Never Opened: received >8 emails, opened 0 emails
        details['never_opened'] = (
            (details['sufficient_emails']) &
            (details['total_emails_opened'] == 0) &
            (~details['is_new_subscriber'])
        )

        # 2. Inactive: received >8 emails, DID open emails before, but last open >30 days ago,
        #    AND clicked 0, shared 0, commented 0 (no engagement whatsoever)
        details['inactive'] = (
            (details['sufficient_emails']) &
            (details['total_emails_opened'] > 0) &  # They DID open before
            (details['days_since_last_open'] > 30) &  # But stopped >30 days ago
            (details['links_clicked'] == 0) &  # Never clicked
            (details['shares'] == 0) &  # Never shared
            (details['comments'] == 0) &  # Never commented
            (~details['is_new_subscriber']) &
            (~details['is_paid'])  # Exclude paid from removal lists
        )

        # 3. Re-engagement Candidates: received >8 emails, had good engagement at some point,
        #    but stopped in the last 30 days (they were engaged, now gone quiet)
        details['reengagement_candidate'] = (
            (details['sufficient_emails']) &
            (details['total_emails_opened'] > 0) &  # They did engage
            (details['open_rate_6mo'] >= 0.3) &  # Had good engagement (30%+ open rate)
            (details['days_since_last_open'] > 30) &  # But stopped >30 days ago
            (~details['is_new_subscriber']) &
            (~details['is_paid'])
        )

        # Summary metrics
        st.subheader("Inactivity Overview")
        st.markdown(f"*Analyzing subscribers who received more than {MIN_EMAILS} emails*")

        col1, col2, col3, col4 = st.columns(4)

        never_opened_count = details['never_opened'].sum()
        inactive_count = details['inactive'].sum()
        reengagement_count = details['reengagement_candidate'].sum()
        total = len(details)
        eligible = details['sufficient_emails'].sum()

        with col1:
            st.metric("Never Opened", f"{never_opened_count:,}",
                     f"{never_opened_count/eligible*100:.1f}% of eligible",
                     help=f"Received >{MIN_EMAILS} emails but never opened any")

        with col2:
            st.metric("Inactive (Lapsed)", f"{inactive_count:,}",
                     f"{inactive_count/eligible*100:.1f}% of eligible",
                     help="Previously opened emails but stopped >30 days ago with zero clicks/shares/comments")

        with col3:
            st.metric("Re-engagement Candidates", f"{reengagement_count:,}",
                     f"{reengagement_count/eligible*100:.1f}% of eligible",
                     help="Were engaged (30%+ open rate) but stopped in last 30 days")

        with col4:
            # Active subscribers (opened recently)
            active_count = details[
                (details['sufficient_emails']) &
                (details['days_since_last_open'] <= 30) &
                (~details['is_new_subscriber'])
            ].shape[0]
            st.metric("Active (30d)", f"{active_count:,}",
                     f"{active_count/eligible*100:.1f}% of eligible",
                     help="Opened an email in the last 30 days")

        st.markdown("---")

        # Multi-channel engagement breakdown
        st.subheader("Engagement by Channel (30 Days)")

        col1, col2 = st.columns(2)

        with col1:
            # Activity breakdown for eligible subscribers only
            eligible_details = details[details['sufficient_emails']]
            activity_data = {
                'Channel': ['Email Opens', 'Post Views', 'Comments', 'Shares', 'Links Clicked'],
                'Active Subscribers': [
                    (eligible_details['emails_opened_30d'] > 0).sum(),
                    (eligible_details['post_views_30d'] > 0).sum(),
                    (eligible_details['comments_30d'] > 0).sum(),
                    (eligible_details['shares_30d'] > 0).sum(),
                    (eligible_details['links_clicked'] > 0).sum()
                ],
                'Total Activity': [
                    eligible_details['emails_opened_30d'].sum(),
                    eligible_details['post_views_30d'].sum(),
                    eligible_details['comments_30d'].sum(),
                    eligible_details['shares_30d'].sum(),
                    eligible_details['links_clicked'].sum()
                ]
            }
            activity_df = pd.DataFrame(activity_data)

            fig = px.bar(activity_df, x='Channel', y='Active Subscribers',
                        color='Active Subscribers', color_continuous_scale='Blues')
            apply_chart_style(fig, title='Subscribers Active by Channel (30d)', height=380)
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, width='stretch')

        with col2:
            # Pie chart of activity status for eligible subscribers
            eligible_details = details[details['sufficient_emails'] & ~details['is_new_subscriber']]
            active_30d = (eligible_details['days_since_last_open'] <= 30).sum()
            lapsed = eligible_details['inactive'].sum()
            never = eligible_details['never_opened'].sum()
            other = len(eligible_details) - active_30d - lapsed - never

            status_names = ['Active (30d)', 'Inactive (Lapsed)', 'Never Opened', 'Other']
            status_values = [active_30d, lapsed, never, other]
            status_colors = [CHART_COLORS['success'], CHART_COLORS['danger'], CHART_COLORS['muted'], CHART_COLORS['warning']]

            fig = go.Figure(data=[go.Pie(
                labels=status_names,
                values=status_values,
                hole=0.4,
                textinfo='label+percent',
                textposition='outside',
                textfont=dict(size=18),
                outsidetextfont=dict(size=18),
                marker=dict(colors=status_colors),
                pull=[0.02] * len(status_values)
            )])
            apply_chart_style(fig, title="Subscriber Status Breakdown", height=500)
            fig.update_layout(
                showlegend=False,
                margin=dict(l=100, r=100, t=80, b=100)
            )
            st.plotly_chart(fig, width='stretch')

        st.markdown("---")

        # List cleaning recommendations
        st.subheader("List Cleaning Recommendations")
        st.markdown(f"*Only showing subscribers who received >{MIN_EMAILS} emails. Paid subscribers always excluded.*")

        tab1, tab2, tab3 = st.tabs(["Never Opened", "Inactive (Lapsed)", "Re-engagement Candidates"])

        with tab1:
            st.markdown(f"""
            **Never Opened** - Free subscribers who received >{MIN_EMAILS} emails but never opened any.
            These may be spam signups, invalid emails, or users who lost interest immediately.
            """)

            # Filter: never opened, free, not new, received >8 emails
            never_opened_df = details[details['never_opened'] & (~details['is_paid'])].copy()

            # Check for other engagement signals
            never_opened_df['other_engagement'] = (
                (never_opened_df['links_clicked'] > 0) |
                (never_opened_df['comments'] > 0) |
                (never_opened_df['shares'] > 0) |
                (never_opened_df['post_views'] > 0)
            )

            # Show those with other engagement separately
            has_other = never_opened_df['other_engagement'].sum()
            if has_other > 0:
                st.warning(f"{has_other} subscribers never opened email but have other engagement (links/comments/shares/views)")

            never_opened_clean = never_opened_df[~never_opened_df['other_engagement']]

            display_cols = ['email', 'start_date', 'emails_received_6mo', 'links_clicked', 'post_views', 'comments', 'shares']
            available_cols = [c for c in display_cols if c in never_opened_clean.columns]
            never_opened_display = never_opened_clean[available_cols].copy()

            st.markdown(f"**{len(never_opened_clean):,} free subscribers** received >{MIN_EMAILS} emails, never opened, no other engagement")

            st.dataframe(never_opened_display.head(100), width='stretch', hide_index=True)

            if st.button("Download Never Opened List", key="dl_never"):
                csv = never_opened_clean.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "never_opened_subscribers.csv",
                    "text/csv",
                    key="dl_never_csv"
                )

        with tab2:
            st.markdown(f"""
            **Inactive (Lapsed)** - Free subscribers who received >{MIN_EMAILS} emails, previously opened,
            but last email open was >30 days ago AND have zero clicks, shares, or comments.
            These subscribers showed initial interest but completely disengaged.
            """)

            # Use the new 'inactive' flag
            inactive_df = details[details['inactive']].copy()

            display_cols = ['email', 'start_date', 'total_emails_opened', 'open_rate_6mo',
                           'days_since_last_open', 'links_clicked', 'post_views', 'comments', 'shares']
            available_cols = [c for c in display_cols if c in inactive_df.columns]
            inactive_display = inactive_df[available_cols].copy()

            if 'open_rate_6mo' in inactive_display.columns:
                inactive_display['open_rate_6mo'] = (inactive_display['open_rate_6mo'] * 100).round(1).astype(str) + '%'

            inactive_display = inactive_display.sort_values('days_since_last_open', ascending=False)

            st.markdown(f"**{len(inactive_df):,} free subscribers** are inactive (lapsed)")
            st.markdown("*(Opened before, stopped >30 days ago, zero clicks/shares/comments)*")
            st.dataframe(inactive_display.head(100), width='stretch', hide_index=True)

            if st.button("Download Inactive List", key="dl_inactive"):
                csv = inactive_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "inactive_subscribers.csv",
                    "text/csv",
                    key="dl_inactive_csv"
                )

        with tab3:
            st.markdown(f"""
            **Re-engagement Candidates** - Free subscribers who received >{MIN_EMAILS} emails,
            had good engagement (30%+ open rate historically), but stopped opening >30 days ago.
            These are your best targets for a "We miss you" campaign - they were engaged before!
            """)

            # Use the new 'reengagement_candidate' flag
            reengagement_df = details[details['reengagement_candidate']].copy()

            display_cols = ['email', 'total_emails_opened', 'open_rate_6mo', 'days_since_last_open',
                           'links_clicked', 'post_views', 'comments', 'shares']
            available_cols = [c for c in display_cols if c in reengagement_df.columns]
            reengagement_display = reengagement_df[available_cols].copy()

            if 'open_rate_6mo' in reengagement_display.columns:
                reengagement_display['open_rate_6mo'] = (reengagement_display['open_rate_6mo'] * 100).round(1).astype(str) + '%'

            reengagement_display = reengagement_display.sort_values('open_rate_6mo', ascending=False)

            st.markdown(f"**{len(reengagement_df):,} free subscribers** are re-engagement candidates")
            st.markdown("*(Were engaged 30%+ open rate, stopped >30 days ago)*")
            st.dataframe(reengagement_display.head(100), width='stretch', hide_index=True)

            if st.button("Download Re-engagement List", key="dl_reengage"):
                csv = reengagement_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "reengagement_candidates.csv",
                    "text/csv",
                    key="dl_reengage_csv"
                )

        st.markdown("---")

        # Impact analysis
        st.subheader("List Cleaning Impact Analysis")

        st.markdown("See how removing inactive **free** subscribers would affect your metrics:")
        st.markdown(f"*Only subscribers with >{MIN_EMAILS} emails. Paid and new subscribers always protected.*")

        removal_threshold = st.selectbox(
            "If you removed free subscribers:",
            ["Inactive (lapsed)", "Never opened (no other engagement)", "Both groups"]
        )

        # Eligible free subscribers only
        eligible_free = details[details['sufficient_emails'] & (~details['is_paid']) & (~details['is_new_subscriber'])]

        if removal_threshold == "Inactive (lapsed)":
            to_remove = eligible_free[eligible_free['inactive']]
        elif removal_threshold == "Never opened (no other engagement)":
            never_opened_no_engagement = eligible_free[
                (eligible_free['never_opened']) &
                (eligible_free['links_clicked'] == 0) &
                (eligible_free['comments'] == 0) &
                (eligible_free['shares'] == 0) &
                (eligible_free['post_views'] == 0)
            ]
            to_remove = never_opened_no_engagement
        else:
            never_opened_no_engagement = eligible_free[
                (eligible_free['never_opened']) &
                (eligible_free['links_clicked'] == 0) &
                (eligible_free['comments'] == 0) &
                (eligible_free['shares'] == 0) &
                (eligible_free['post_views'] == 0)
            ]
            inactive_lapsed = eligible_free[eligible_free['inactive']]
            to_remove = pd.concat([never_opened_no_engagement, inactive_lapsed]).drop_duplicates()

        remaining = len(details) - len(to_remove)
        # Active = opened in last 30 days
        active_remaining = (details['days_since_last_open'] <= 30).sum()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Subscribers Removed", f"{len(to_remove):,}",
                     f"-{len(to_remove)/len(details)*100:.1f}%")

        with col2:
            st.metric("Remaining List Size", f"{remaining:,}")

        with col3:
            new_active_rate = active_remaining / remaining * 100 if remaining > 0 else 0
            current_active_rate = active_remaining / len(details) * 100
            st.metric("New Active Rate",
                     f"{new_active_rate:.1f}%",
                     f"+{new_active_rate - current_active_rate:.1f}%")

        # Confirm protected subscribers
        paid_count = details['is_paid'].sum()
        new_count = details['is_new_subscriber'].sum()
        few_emails_count = (~details['sufficient_emails']).sum()
        protection_msgs = []
        if paid_count > 0:
            protection_msgs.append(f"{paid_count} paid")
        if new_count > 0:
            protection_msgs.append(f"{new_count} new (last 30 days)")
        if few_emails_count > 0:
            protection_msgs.append(f"{few_emails_count} with <={MIN_EMAILS} emails")
        if protection_msgs:
            st.success(f"Protected from removal: {', '.join(protection_msgs)}")

    else:
        st.warning("No subscriber_details.csv found. Please upload this file for inactive subscriber analysis.")


if __name__ == "__main__":
    main()
