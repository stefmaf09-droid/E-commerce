import sys
import os
# Add root to sys.path like the app does
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

print(f"sys.path: {sys.path[:3]}")
try:
    import google
    print(f"Google location: {getattr(google, '__path__', 'No Path')}")
    from google import genai
    print("Successfully imported genai via: from google import genai")
except ImportError as e:
    print(f"ImportError (from google import genai): {e}")

try:
    import google.genai
    print("Successfully imported google.genai")
except ImportError as e:
    print(f"ImportError (import google.genai): {e}")
