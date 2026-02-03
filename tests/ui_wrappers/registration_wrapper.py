import streamlit as st
import sys
import os

# Set base path
sys.path.insert(0, os.path.abspath('.'))

from client_dashboard import authenticate
from unittest.mock import MagicMock

# Force unauthenticated state to show login/register tabs
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

authenticate()
