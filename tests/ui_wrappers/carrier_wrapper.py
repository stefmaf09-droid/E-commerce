import streamlit as st
from src.ui.carrier_management import render_carrier_management

# Setup session state for tests
if 'client_email' not in st.session_state:
    st.session_state['client_email'] = 'test@example.com'

render_carrier_management()
