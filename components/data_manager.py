"""
Data manager component for the sidebar.
Allows users to switch datasets, view info, and manage uploads.
"""
import streamlit as st
from datetime import datetime

from upload_handler import (
    get_available_datasets,
    delete_dataset,
    add_subscriber_details,
    load_manifest,
)


def render_data_manager():
    """
    Render the data manager in the sidebar.
    Handles dataset selection and management.

    Returns:
        str or None: Currently selected dataset path
    """
    datasets = get_available_datasets()

    if not datasets:
        return None

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data Management")

    # Dataset selector
    if len(datasets) > 1:
        dataset_labels = []
        for d in datasets:
            upload_date = d.get('upload_date', '')
            if upload_date:
                try:
                    dt = datetime.fromisoformat(upload_date)
                    date_str = dt.strftime("%b %d, %Y")
                except Exception:
                    date_str = d['id']
            else:
                date_str = d['id']

            label = f"{date_str} ({d['subscriber_count']:,} subs)"
            dataset_labels.append(label)

        # Get current selection from session state
        current_idx = 0
        if 'active_dataset' in st.session_state:
            for i, d in enumerate(datasets):
                if d['path'] == st.session_state.active_dataset:
                    current_idx = i
                    break

        selected_idx = st.sidebar.selectbox(
            "Active Dataset",
            range(len(datasets)),
            index=current_idx,
            format_func=lambda i: dataset_labels[i],
            key="dataset_selector"
        )

        selected_dataset = datasets[selected_idx]
    else:
        selected_dataset = datasets[0]

    # Store selected dataset in session state
    st.session_state.active_dataset = selected_dataset['path']

    # Dataset info
    with st.sidebar.expander("Dataset Info", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Subscribers", f"{selected_dataset['subscriber_count']:,}")
        with col2:
            st.metric("Posts", f"{selected_dataset['post_count']:,}")

        # Show if subscriber details are available
        if selected_dataset.get('has_subscriber_details'):
            st.success("✓ Subscriber details loaded")
        else:
            st.warning("No subscriber details")

            # Option to add subscriber details
            uploaded_csv = st.file_uploader(
                "Add subscriber_details.csv",
                type=['csv'],
                key="sidebar_csv_uploader",
                help="Export from Substack Subscribers page"
            )

            if uploaded_csv is not None:
                with st.spinner("Adding..."):
                    success, message = add_subscriber_details(
                        selected_dataset['path'],
                        uploaded_csv
                    )
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)

        # Upload date
        upload_date = selected_dataset.get('upload_date')
        if upload_date:
            try:
                dt = datetime.fromisoformat(upload_date)
                st.caption(f"Uploaded: {dt.strftime('%Y-%m-%d %H:%M')}")
            except Exception:
                pass

    # Action buttons
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("📤 New", use_container_width=True, help="Upload new dataset"):
            st.session_state.show_upload_modal = True
            st.rerun()

    with col2:
        if len(datasets) > 1:
            if st.button("🗑️ Delete", use_container_width=True, help="Delete current dataset"):
                st.session_state.confirm_delete = True
                st.rerun()

    # Deletion confirmation
    if st.session_state.get('confirm_delete'):
        st.sidebar.warning(f"Delete dataset with {selected_dataset['subscriber_count']:,} subscribers?")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Yes, delete", type="primary", use_container_width=True):
                success, msg = delete_dataset(selected_dataset['path'])
                if success:
                    st.session_state.confirm_delete = False
                    st.session_state.active_dataset = None
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_delete = False
                st.rerun()

    return selected_dataset['path']


def initialize_session_state():
    """Initialize session state variables for data management."""
    if 'active_dataset' not in st.session_state:
        # Try to load most recent dataset
        datasets = get_available_datasets()
        if datasets:
            st.session_state.active_dataset = datasets[0]['path']
        else:
            st.session_state.active_dataset = None

    if 'show_upload_modal' not in st.session_state:
        st.session_state.show_upload_modal = False

    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = False
