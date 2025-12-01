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
    .upload-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        color: white;
        margin: 20px 0;
    }
    .upload-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .upload-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 30px;
    }
    .upload-step {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        text-align: left;
    }
    .upload-step h4 {
        margin: 0 0 10px 0;
        color: white;
    }
    .upload-step p {
        margin: 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }
    .stFileUploader > div {
        background: rgba(255,255,255,0.95);
        border-radius: 15px;
        padding: 20px;
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
    <div class="upload-container">
        <div class="upload-title">Substack Subscriber Analytics</div>
        <div class="upload-subtitle">Upload your Substack export to get started</div>
    </div>
    """, unsafe_allow_html=True)

    # Instructions
    st.markdown("### How to Get Your Data")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="upload-step">
            <h4>1. Export Your Data</h4>
            <p>Go to your Substack dashboard → Settings → Exports → Download a zip of all your data</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="upload-step">
            <h4>2. Upload the Zip File</h4>
            <p>Drag and drop or click to upload the .zip file you downloaded from Substack</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="upload-step">
            <h4>3. Optional: Subscriber Details</h4>
            <p>For richer analytics, export subscriber details from Subscribers → Export</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="upload-step">
            <h4>4. Explore Your Analytics</h4>
            <p>Once uploaded, explore engagement metrics, subscriber segments, and more!</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Upload section
    st.markdown("### Upload Your Data")

    tab1, tab2 = st.tabs(["Complete Export (.zip)", "Subscriber Details (.csv)"])

    with tab1:
        st.markdown("""
        Upload the complete Substack data export (zip file).
        This includes your email list, posts, and engagement data.
        """)

        uploaded_zip = st.file_uploader(
            "Drop your Substack export zip file here",
            type=['zip'],
            key="zip_uploader",
            help="Export from: Substack Settings → Exports → Download zip"
        )

        if uploaded_zip is not None:
            with st.spinner("Processing your data..."):
                success, message, dataset_path = process_upload(
                    uploaded_zip,
                    uploaded_zip.name
                )

                if success:
                    st.success(f"✅ {message}")
                    st.balloons()

                    # Store the new dataset path in session state
                    st.session_state.active_dataset = dataset_path
                    st.session_state.show_upload_modal = False

                    # Rerun to refresh the app
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
                    st.markdown("""
                    **Troubleshooting:**
                    - Make sure you uploaded the correct zip file from Substack
                    - The zip should contain: posts.csv, email_list*.csv, and a posts/ folder
                    - Try downloading a fresh export from Substack
                    """)

    with tab2:
        if has_existing_data:
            st.markdown("""
            Add subscriber details to enrich your existing dataset.
            This enables geographic analysis, multi-channel engagement tracking, and more.
            """)

            # Let user select which dataset to add details to
            datasets = get_available_datasets()
            dataset_options = {
                f"{d['id']} ({d['subscriber_count']} subscribers)": d['path']
                for d in datasets
            }

            selected = st.selectbox(
                "Add to dataset:",
                options=list(dataset_options.keys())
            )

            uploaded_csv = st.file_uploader(
                "Drop your subscriber_details.csv here",
                type=['csv'],
                key="csv_uploader",
                help="Export from: Substack Subscribers → Export"
            )

            if uploaded_csv is not None and selected:
                dataset_path = dataset_options[selected]
                with st.spinner("Adding subscriber details..."):
                    success, message = add_subscriber_details(
                        dataset_path,
                        uploaded_csv
                    )

                    if success:
                        st.success(f"✅ {message}")
                        # Clear cache to reload data
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        else:
            st.info("Upload a complete export first, then you can add subscriber details.")

    # Show example of expected file structure
    with st.expander("What should the export contain?"):
        st.markdown("""
        A valid Substack export contains:

        ```
        your-export.zip
        ├── email_list.your-newsletter.csv  (subscriber list)
        ├── posts.csv                        (all your posts)
        └── posts/                           (engagement data)
            ├── 12345.opens.csv              (who opened each post)
            └── 12345.delivers.csv           (who received each post)
        ```

        **Optional enhancement:**
        - `subscriber_details.csv` - Export separately from the Subscribers page
          for geographic data, multi-channel engagement metrics, and more
        """)

    return None


def render_upload_button():
    """Render a compact upload button for use in the sidebar."""
    if st.button("📤 Upload New Data", use_container_width=True):
        st.session_state.show_upload_modal = True
        st.rerun()
