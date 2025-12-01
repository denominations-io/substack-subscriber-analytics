"""
Upload modal component for Substack data import.
"""
import streamlit as st

from upload_handler import (
    process_upload,
    add_subscriber_details,
    get_available_datasets,
)


def render_upload_css():
    """Render custom CSS for the upload modal."""
    st.markdown("""
    <style>
    /* Header */
    .upload-header {
        text-align: center;
        padding: 60px 20px;
        margin: -1rem -1rem 2rem -1rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 0 0 30px 30px;
    }
    .upload-header h1 {
        color: white;
        font-size: 2.2rem;
        font-weight: 600;
        margin: 0 0 8px 0;
        letter-spacing: -0.5px;
    }
    .upload-header p {
        color: rgba(255,255,255,0.7);
        font-size: 1.05rem;
        margin: 0;
    }

    /* Steps */
    .steps-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin: 0 0 2rem 0;
    }
    .step-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 24px 20px;
        text-align: center;
        border: 1px solid #e9ecef;
        transition: all 0.2s ease;
    }
    .step-card:hover {
        border-color: #dee2e6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .step-icon {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
        color: white;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 14px;
    }
    .step-card h4 {
        font-size: 0.95rem;
        font-weight: 600;
        color: #212529;
        margin: 0 0 6px 0;
    }
    .step-card p {
        font-size: 0.82rem;
        color: #6c757d;
        margin: 0;
        line-height: 1.4;
    }

    /* Upload area */
    .upload-section {
        background: white;
        border-radius: 16px;
        padding: 32px;
        border: 1px solid #e9ecef;
    }
    .upload-section h3 {
        font-size: 1.1rem;
        font-weight: 600;
        color: #212529;
        margin: 0 0 20px 0;
    }

    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background: #f8f9fa;
        border-radius: 12px;
        border: 2px dashed #dee2e6;
        padding: 20px;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #adb5bd;
    }
    [data-testid="stFileUploader"] section {
        padding: 0;
    }
    [data-testid="stFileUploader"] section > div {
        padding: 0 !important;
    }

    /* Hide default labels we're replacing */
    .upload-section .stFileUploader label {
        display: none;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 8px 16px;
        border: 1px solid #e9ecef;
    }
    .stTabs [aria-selected="true"] {
        background: #1a1a2e;
        color: white;
        border-color: #1a1a2e;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 0.9rem;
        color: #6c757d;
    }
    </style>
    """, unsafe_allow_html=True)


def render_upload_modal(force_show: bool = False):
    """
    Render the upload modal for importing Substack data.

    Args:
        force_show: If True, show the modal even if data exists (for adding new datasets)

    Returns:
        str or None: Path to newly uploaded dataset, or None if no upload
    """
    render_upload_css()

    # Check if we're in the "add subscriber details" step
    if st.session_state.get('pending_subscriber_details'):
        return _render_subscriber_details_prompt()

    # Check if we have any existing datasets
    datasets = get_available_datasets()
    has_data = len(datasets) > 0

    # Only show full modal if no data exists or force_show
    if not has_data or force_show:
        return _render_full_upload_modal(has_data)

    return None


def _render_full_upload_modal(has_existing_data: bool):
    """Render the full upload modal."""

    # Header
    st.markdown("""
    <div class="upload-header">
        <h1>Substack Subscriber Analytics</h1>
        <p>Upload your Substack export to get started</p>
    </div>
    """, unsafe_allow_html=True)

    # Steps - clean 3-column layout
    st.markdown("""
    <div class="steps-container">
        <div class="step-card">
            <div class="step-icon">1</div>
            <h4>Export from Substack</h4>
            <p>Settings → Exports → Download zip</p>
        </div>
        <div class="step-card">
            <div class="step-icon">2</div>
            <h4>Upload below</h4>
            <p>Drop your .zip file</p>
        </div>
        <div class="step-card">
            <div class="step-icon">3</div>
            <h4>Explore insights</h4>
            <p>Engagement, segments & more</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Upload section
    tab1, tab2 = st.tabs(["Complete Export (.zip)", "Subscriber Details (.csv)"])

    with tab1:
        uploaded_zip = st.file_uploader(
            "Drop your Substack export zip file here",
            type=['zip'],
            key="zip_uploader",
            help="Substack Settings → Exports → Download zip"
        )

        if uploaded_zip is not None:
            with st.spinner("Processing your data..."):
                success, message, dataset_path = process_upload(
                    uploaded_zip,
                    uploaded_zip.name
                )

                if success:
                    st.success(message)
                    st.balloons()

                    # Store the new dataset path and prompt for subscriber details
                    st.session_state.active_dataset = dataset_path
                    st.session_state.pending_subscriber_details = dataset_path
                    st.session_state.show_upload_modal = False

                    # Rerun to show subscriber details prompt
                    st.rerun()
                else:
                    st.error(message)
                    with st.expander("Troubleshooting"):
                        st.markdown("""
                        - Make sure you uploaded the correct zip file from Substack
                        - The zip should contain `posts.csv`, `email_list*.csv`, and a `posts/` folder
                        - Try downloading a fresh export from Substack
                        """)

    with tab2:
        if has_existing_data:
            st.caption("Add geographic & engagement data to your existing dataset")

            # Let user select which dataset to add details to
            datasets = get_available_datasets()
            dataset_options = {
                f"{d['id']} ({d['subscriber_count']} subscribers)": d['path']
                for d in datasets
            }

            selected = st.selectbox(
                "Add to dataset:",
                options=list(dataset_options.keys()),
                label_visibility="collapsed"
            )

            uploaded_csv = st.file_uploader(
                "Drop your subscriber_details.csv here",
                type=['csv'],
                key="csv_uploader",
                help="Substack Subscribers → Export"
            )

            if uploaded_csv is not None and selected:
                dataset_path = dataset_options[selected]
                with st.spinner("Adding subscriber details..."):
                    success, message = add_subscriber_details(
                        dataset_path,
                        uploaded_csv
                    )

                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.info("Upload a complete export first to add subscriber details.")

    return None


def _render_subscriber_details_prompt():
    """Render the optional subscriber details upload prompt after successful zip upload."""

    dataset_path = st.session_state.pending_subscriber_details

    # Header
    st.markdown("""
    <div class="upload-header">
        <h1>Data Imported Successfully!</h1>
        <p>Want to unlock more insights?</p>
    </div>
    """, unsafe_allow_html=True)

    # Explanation
    st.markdown("""
    <div style="background: #f8f9fa; border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 1px solid #e9ecef;">
        <h3 style="margin: 0 0 12px 0; font-size: 1.1rem; color: #212529;">Add Subscriber Details (Optional)</h3>
        <p style="margin: 0 0 16px 0; color: #6c757d; font-size: 0.95rem;">
            Upload <code>subscriber_details.csv</code> to unlock additional analytics:
        </p>
        <ul style="margin: 0; padding-left: 20px; color: #495057; font-size: 0.9rem;">
            <li>Geographic segmentation (by country/region)</li>
            <li>Multi-channel engagement (email, web, comments, shares)</li>
            <li>Advanced inactive subscriber analysis</li>
            <li>Engagement flow Sankey diagrams</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # How to get the file
    with st.expander("How to export subscriber details"):
        st.markdown("""
        1. Go to your Substack dashboard
        2. Navigate to **Subscribers**
        3. Click **Export** to download `subscriber_details.csv`
        """)

    # File uploader
    uploaded_csv = st.file_uploader(
        "Drop your subscriber_details.csv here",
        type=['csv'],
        key="details_csv_uploader",
        help="Substack Subscribers → Export"
    )

    if uploaded_csv is not None:
        with st.spinner("Adding subscriber details..."):
            success, message = add_subscriber_details(
                dataset_path,
                uploaded_csv
            )

            if success:
                st.success(message)
                # Clear the pending state and proceed to dashboard
                st.session_state.pending_subscriber_details = None
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(message)

    # Skip button
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Skip for now →", use_container_width=True):
            st.session_state.pending_subscriber_details = None
            st.rerun()

    st.caption("You can always add subscriber details later from the sidebar.")

    return None


def render_upload_button():
    """Render a compact upload button for use in the sidebar."""
    if st.button("📤 Upload New Data", use_container_width=True):
        st.session_state.show_upload_modal = True
        st.rerun()
