import streamlit as st
st.write("query_params at start:", st.query_params)
st.write("session_state at start:", st.session_state)

st.write("Loading auth...")
# Simulating the exact token read
if "token" in st.query_params:
    st.write("Token found:", st.query_params.get("token"))
    st.session_state.authenticated = True
else:
    st.write("No token found")

st.write("claim_id in URL?", st.query_params.get("claim_id"))

if st.button("Rerun Manually"):
    st.rerun()
