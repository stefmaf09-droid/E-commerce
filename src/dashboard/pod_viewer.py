"""
POD Viewer Component

Displays POD (Proof of Delivery) documents inline with:
- PDF preview using iframe
- Download button
- Navigation between multiple PODs
- Responsive design
"""

import streamlit as st
import base64
from pathlib import Path
from typing import Optional


def render_pod_viewer(pod_url: str, claim_ref: str, display_mode: str = "inline"):
    """
    Display a POD document with preview and download options.
    
    Args:
        pod_url: URL or local path to the POD PDF
        claim_ref: Claim reference for display
        display_mode: "inline" (embedded in page) or "modal" (popup dialog)
    """
    from src.utils.i18n import get_i18n_text, get_browser_language
    
    lang = get_browser_language()
    
    if not pod_url:
        st.warning(get_i18n_text('pod_not_available', lang))
        return
    
    # Check if it's a local file or URL
    if pod_url.startswith('http://') or pod_url.startswith('https://'):
        # External URL - use iframe directly
        if display_mode == "inline":
            _render_inline_pdf_viewer(pod_url, claim_ref, lang)
        else:
            _render_modal_pdf_viewer(pod_url, claim_ref, lang)
    else:
        # Local file - encode in base64
        try:
            if display_mode == "inline":
                _render_inline_pdf_local(pod_url, claim_ref, lang)
            else:
                _render_modal_pdf_local(pod_url, claim_ref, lang)
        except FileNotFoundError:
            st.error(f"❌ {get_i18n_text('pod_file_not_found', lang)}: {pod_url}")


def _render_inline_pdf_viewer(pdf_url: str, claim_ref: str, lang: str):
    """Render PDF viewer inline in the page."""
    from src.utils.i18n import get_i18n_text
    
    st.markdown(f"#### 📄 POD - {claim_ref}")
    
    # Download button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.link_button(
            f"⬇️ {get_i18n_text('download_csv', lang)}",
            pdf_url,
            use_container_width=True
        )
    with col2:
        if st.button("🔄", key=f"refresh_{claim_ref}", help="Refresh preview"):
            st.rerun()
    with col3:
        if st.button("❌", key=f"close_{claim_ref}", help="Close preview"):
            if f"show_pod_{claim_ref}" in st.session_state:
                del st.session_state[f"show_pod_{claim_ref}"]
            st.rerun()
    
    # PDF viewer with iframe
    st.markdown(
        f"""
        <iframe
            src="{pdf_url}"
            width="100%"
            height="600"
            style="border: 1px solid #ddd; border-radius: 5px;"
        ></iframe>
        """,
        unsafe_allow_html=True
    )


def _render_modal_pdf_viewer(pdf_url: str, claim_ref: str, lang: str):
    """Render PDF viewer in a modal dialog."""
    from src.utils.i18n import get_i18n_text
    
    # Use st.dialog for modal (Streamlit 1.30+)
    @st.dialog(f"📄 POD - {claim_ref}", width="large")
    def show_pdf_dialog():
        st.link_button(
            f"⬇️ {get_i18n_text('download_csv', lang)}",
            pdf_url,
            use_container_width=True
        )
        
        st.markdown(
            f"""
            <iframe
                src="{pdf_url}"
                width="100%"
                height="700"
                style="border: none;"
            ></iframe>
            """,
            unsafe_allow_html=True
        )
    
    show_pdf_dialog()


def _render_inline_pdf_local(pdf_path: str, claim_ref: str, lang: str):
    """Render local PDF file inline using base64 encoding."""
    from src.utils.i18n import get_i18n_text
    
    # Read and encode PDF
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    st.markdown(f"#### 📄 POD - {claim_ref}")
    
    # Download button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        with open(pdf_path, "rb") as f:
            st.download_button(
                label=f"⬇️ {get_i18n_text('download_csv', lang)}",
                data=f.read(),
                file_name=f"POD_{claim_ref}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    with col2:
        if st.button("🔄", key=f"refresh_{claim_ref}", help="Refresh preview"):
            st.rerun()
    with col3:
        if st.button("❌", key=f"close_{claim_ref}", help="Close preview"):
            if f"show_pod_{claim_ref}" in st.session_state:
                del st.session_state[f"show_pod_{claim_ref}"]
            st.rerun()
    
    # Embed PDF using base64
    pdf_display = f'''
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="600"
            style="border: 1px solid #ddd; border-radius: 5px;"
            type="application/pdf"
        ></iframe>
    '''
    st.markdown(pdf_display, unsafe_allow_html=True)


def _render_modal_pdf_local(pdf_path: str, claim_ref: str, lang: str):
    """Render local PDF file in modal using base64 encoding."""
    from src.utils.i18n import get_i18n_text
    
    # Read and encode PDF
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    
    @st.dialog(f"📄 POD - {claim_ref}", width="large")
    def show_pdf_dialog():
        st.download_button(
            label=f"⬇️ {get_i18n_text('download_csv', lang)}",
            data=pdf_data,
            file_name=f"POD_{claim_ref}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        pdf_display = f'''
            <iframe
                src="data:application/pdf;base64,{base64_pdf}"
                width="100%"
                height="700"
                style="border: none;"
                type="application/pdf"
            ></iframe>
        '''
        st.markdown(pdf_display, unsafe_allow_html=True)
    
    show_pdf_dialog()


def render_pod_gallery(claims_with_pods: list, default_index: int = 0):
    """
    Render a gallery/carousel of multiple PODs.
    
    Args:
        claims_with_pods: List of dicts with 'claim_ref' and 'pod_url'
        default_index: Index of POD to display initially
    """
    from src.utils.i18n import get_i18n_text, get_browser_language
    
    lang = get_browser_language()
    
    if not claims_with_pods:
        st.info(get_i18n_text('no_pods_available', lang))
        return
    
    # Navigation
    st.markdown(f"### 📄 {get_i18n_text('pod_gallery', lang)} ({len(claims_with_pods)} PODs)")
    
    # Selection dropdown
    pod_options = [f"{claim['claim_ref']}" for claim in claims_with_pods]
    selected_index = st.selectbox(
        get_i18n_text('select_pod', lang),
        range(len(claims_with_pods)),
        format_func=lambda i: pod_options[i],
        index=default_index
    )
    
    # Display selected POD
    selected_claim = claims_with_pods[selected_index]
    render_pod_viewer(
        selected_claim['pod_url'],
        selected_claim['claim_ref'],
        display_mode="inline"
    )
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ " + get_i18n_text('previous', lang), disabled=selected_index == 0):
            st.session_state.pod_gallery_index = selected_index - 1
            st.rerun()
    with col3:
        if st.button(get_i18n_text('next', lang) + " ➡️", disabled=selected_index == len(claims_with_pods) - 1):
            st.session_state.pod_gallery_index = selected_index + 1
            st.rerun()
