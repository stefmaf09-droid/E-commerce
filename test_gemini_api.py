import logging
import sys
import os

# Set up path so we can import from src
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, root_dir)

from src.config import Config
from google import genai

logging.basicConfig(level=logging.DEBUG)

def test_gemini():
    api_key = Config.get_gemini_api_key()
    if not api_key:
        print("NO API KEY FOUND")
        return
        
    print(f"API Key starts with: {api_key[:10]}...")
    
    try:
        client = genai.Client(api_key=api_key)
        print("Client initialized. Making test request...")
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents='Dis bonjour très brièvement.',
        )
        print("SUCCESS! Response:")
        print(response.text)
    except Exception as e:
        print(f"ERROR: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    test_gemini()
