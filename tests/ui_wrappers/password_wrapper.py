import streamlit as st
from src.ui.password_reset import render_password_reset, render_reset_password_form

# Test if we should show the reset form or the request form
if st.query_params.get('reset_token'):
    render_reset_password_form(st.query_params['reset_token'])
else:
    render_password_reset()
