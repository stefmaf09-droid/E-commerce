import streamlit as st
import sys
import os

# Set base path
sys.path.insert(0, os.path.abspath('.'))

from onboarding_functions import render_onboarding
from onboarding.onboarding_manager import OnboardingManager
from unittest.mock import MagicMock

# Mock session state if needed
if 'client_email' not in st.session_state:
    st.session_state.client_email = "test@example.com"

# Mock manager
manager = MagicMock(spec=OnboardingManager)
manager.get_current_step.return_value = st.query_params.get("step", "store_setup")
manager.is_onboarding_complete.return_value = False

render_onboarding(st.session_state.client_email, manager)
