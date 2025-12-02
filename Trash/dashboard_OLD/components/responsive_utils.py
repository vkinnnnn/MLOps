"""
Responsive utilities for adaptive layouts across devices.
Provides helper functions for responsive design patterns.
"""

import streamlit as st
from typing import List, Tuple


def get_device_type() -> str:
    """
    Detect device type based on viewport width.
    Note: This is a heuristic approach since Streamlit doesn't provide direct device detection.
    
    Returns:
        Device type: 'mobile', 'tablet', or 'desktop'
    """
    # Use session state to store device preference
    if 'device_type' not in st.session_state:
        st.session_state.device_type = 'desktop'  # Default to desktop
    
    return st.session_state.device_type


def get_responsive_columns(mobile: int = 1, tablet: int = 2, desktop: int = 3) -> List:
    """
    Get responsive column configuration based on device type.
    
    Args:
        mobile: Number of columns for mobile devices
        tablet: Number of columns for tablet devices
        desktop: Number of columns for desktop devices
        
    Returns:
        Streamlit columns object
    """
    device = get_device_type()
    
    if device == 'mobile':
        return st.columns(mobile)
    elif device == 'tablet':
        return st.columns(tablet)
    else:
        return st.columns(desktop)


def responsive_container(content_func, mobile_width: str = "100%", desktop_width: str = "80%"):
    """
    Create a responsive container with different widths for mobile and desktop.
    
    Args:
        content_func: Function to render content inside container
        mobile_width: Width for mobile devices
        desktop_width: Width for desktop devices
    """
    device = get_device_type()
    width = mobile_width if device == 'mobile' else desktop_width
    
    with st.container():
        st.markdown(f'<div style="width: {width}; margin: 0 auto;">', unsafe_allow_html=True)
        content_func()
        st.markdown('</div>', unsafe_allow_html=True)


def mobile_friendly_table(data, max_columns_mobile: int = 3):
    """
    Display table with responsive behavior - fewer columns on mobile.
    
    Args:
        data: DataFrame or data to display
        max_columns_mobile: Maximum columns to show on mobile
    """
    device = get_device_type()
    
    if device == 'mobile' and hasattr(data, 'columns') and len(data.columns) > max_columns_mobile:
        # Show scrollable table with hint
        st.dataframe(data, use_container_width=True)
        st.caption("👉 Scroll horizontally to see all columns")
    else:
        st.dataframe(data, use_container_width=True)


def responsive_metrics(metrics: List[Tuple[str, str]], cols_mobile: int = 1, cols_desktop: int = 3):
    """
    Display metrics in responsive columns.
    
    Args:
        metrics: List of (label, value) tuples
        cols_mobile: Number of columns on mobile
        cols_desktop: Number of columns on desktop
    """
    device = get_device_type()
    num_cols = cols_mobile if device == 'mobile' else cols_desktop
    
    cols = st.columns(num_cols)
    
    for idx, (label, value) in enumerate(metrics):
        col_idx = idx % num_cols
        with cols[col_idx]:
            st.metric(label, value)


def mobile_optimized_expander(title: str, content_func, expanded: bool = False):
    """
    Create an expander optimized for mobile with better touch targets.
    
    Args:
        title: Expander title
        content_func: Function to render content
        expanded: Whether expander is initially expanded
    """
    with st.expander(title, expanded=expanded):
        content_func()


def responsive_button_group(buttons: List[Tuple[str, callable]], stack_on_mobile: bool = True):
    """
    Create a group of buttons that stack on mobile if needed.
    
    Args:
        buttons: List of (label, callback) tuples
        stack_on_mobile: Whether to stack buttons vertically on mobile
    """
    device = get_device_type()
    
    if device == 'mobile' and stack_on_mobile:
        # Stack buttons vertically on mobile
        for label, callback in buttons:
            if st.button(label, use_container_width=True):
                callback()
    else:
        # Display buttons horizontally
        cols = st.columns(len(buttons))
        for idx, (label, callback) in enumerate(buttons):
            with cols[idx]:
                if st.button(label, use_container_width=True):
                    callback()


def add_mobile_scroll_hint(show_on_mobile: bool = True):
    """
    Add a visual hint for horizontal scrolling on mobile.
    
    Args:
        show_on_mobile: Whether to show hint on mobile devices
    """
    if show_on_mobile:
        st.markdown(
            '<div class="scroll-hint">👈 Swipe to see more 👉</div>',
            unsafe_allow_html=True
        )


def responsive_card(content_func, padding_mobile: str = "0.75rem", padding_desktop: str = "1.5rem"):
    """
    Create a card with responsive padding.
    
    Args:
        content_func: Function to render card content
        padding_mobile: Padding for mobile devices
        padding_desktop: Padding for desktop devices
    """
    device = get_device_type()
    padding = padding_mobile if device == 'mobile' else padding_desktop
    
    st.markdown(
        f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: {padding};
            margin-bottom: 1rem;
            background-color: #f9f9f9;
        ">
        """,
        unsafe_allow_html=True
    )
    content_func()
    st.markdown('</div>', unsafe_allow_html=True)


def set_device_preference():
    """
    Allow users to manually set their device preference.
    Useful for testing or user preference.
    """
    with st.sidebar:
        with st.expander("⚙️ Display Settings", expanded=False):
            device = st.radio(
                "Layout Optimization",
                ["Auto (Desktop)", "Mobile", "Tablet"],
                help="Choose layout optimization for your device"
            )
            
            device_map = {
                "Auto (Desktop)": "desktop",
                "Mobile": "mobile",
                "Tablet": "tablet"
            }
            
            st.session_state.device_type = device_map[device]


def responsive_grid(items: List, items_per_row_mobile: int = 1, items_per_row_desktop: int = 3):
    """
    Create a responsive grid layout for items.
    
    Args:
        items: List of items to display
        items_per_row_mobile: Items per row on mobile
        items_per_row_desktop: Items per row on desktop
    """
    device = get_device_type()
    items_per_row = items_per_row_mobile if device == 'mobile' else items_per_row_desktop
    
    for i in range(0, len(items), items_per_row):
        cols = st.columns(items_per_row)
        for j, item in enumerate(items[i:i + items_per_row]):
            with cols[j]:
                if callable(item):
                    item()
                else:
                    st.write(item)


def mobile_friendly_tabs(tab_labels: List[str], tab_contents: List[callable]):
    """
    Create tabs that work well on mobile with shorter labels if needed.
    
    Args:
        tab_labels: List of tab labels
        tab_contents: List of functions to render tab content
    """
    device = get_device_type()
    
    # Shorten labels on mobile if they're too long
    if device == 'mobile':
        display_labels = [label[:15] + "..." if len(label) > 15 else label for label in tab_labels]
    else:
        display_labels = tab_labels
    
    tabs = st.tabs(display_labels)
    
    for tab, content_func in zip(tabs, tab_contents):
        with tab:
            content_func()


def responsive_spacing(mobile_spacing: str = "1rem", desktop_spacing: str = "2rem"):
    """
    Add responsive spacing between elements.
    
    Args:
        mobile_spacing: Spacing for mobile devices
        desktop_spacing: Spacing for desktop devices
    """
    device = get_device_type()
    spacing = mobile_spacing if device == 'mobile' else desktop_spacing
    
    st.markdown(f'<div style="margin-top: {spacing};"></div>', unsafe_allow_html=True)


def hide_on_mobile(content_func):
    """
    Hide content on mobile devices.
    
    Args:
        content_func: Function to render content (only shown on desktop/tablet)
    """
    device = get_device_type()
    
    if device != 'mobile':
        content_func()


def show_only_on_mobile(content_func):
    """
    Show content only on mobile devices.
    
    Args:
        content_func: Function to render content (only shown on mobile)
    """
    device = get_device_type()
    
    if device == 'mobile':
        content_func()
