import streamlit as st
import google
import os
import sys

st.title("Streamlit Diagnostic")
st.write(f"Python version: {sys.version}")
st.write(f"Python executable: {sys.executable}")
st.write(f"sys.path: {sys.path}")

st.header("Google Package")
st.write(f"Google path: {getattr(google, '__path__', 'No Path')}")
st.write(f"Google file: {getattr(google, '__file__', 'No File')}")

try:
    from google import genai
    st.success("Successfully imported genai via: from google import genai")
except ImportError as e:
    st.error(f"ImportError (from google import genai): {e}")

try:
    import google.genai
    st.success("Successfully imported google.genai")
except ImportError as e:
    st.error(f"ImportError (import google.genai): {e}")

# Check content of google directory
for path in getattr(google, '__path__', []):
    if os.path.exists(path):
        st.write(f"Contents of {path}:")
        st.write(os.listdir(path))
