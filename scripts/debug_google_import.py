import google
import os
print(f"Google location: {google.__path__}")
try:
    from google import genai
    print("Successfully imported genai")
except ImportError as e:
    print(f"ImportError: {e}")

# List files in google directory
for path in google.__path__:
    if os.path.exists(path):
        print(f"Contents of {path}:")
        print(os.listdir(path))
    else:
        print(f"Path does not exist: {path}")
