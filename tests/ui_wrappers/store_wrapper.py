import streamlit as st
from src.ui.store_management import render_multi_store_management

if 'client_email' not in st.session_state:
    st.session_state['client_email'] = 'test@example.com'

render_multi_store_management()
