import streamlit as st
from src.ui.store_management import render_multi_store_management

if 'client_email' not in st.session_state:
    st.session_state['client_email'] = 'test@example.com'

render_multi_store_management()
<!-- slide -->
import streamlit as st
from src.ui.password_reset import render_password_reset, render_reset_password_form

if 'reset_token' in st.query_params:
    render_reset_password_form(st.query_params['reset_token'])
else:
    render_password_reset()
