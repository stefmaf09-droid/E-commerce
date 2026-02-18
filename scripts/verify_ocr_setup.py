import sys
import os

# Add project root to path (so 'src.config' works)
sys.path.append(os.getcwd())

from src.scrapers.ocr_processor import OCRProcessor
from src.config import Config

def test_ocr_init():
    print("Testing OCRProcessor Initialization...")
    
    # Force load secrets if needed (Config handles it)
    api_key = Config.get_gemini_api_key()
    print(f"API Key detected: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key prefix: {api_key[:5]}...")
    
    try:
        processor = OCRProcessor()
        if processor.model:
            print("✅ Gemini Model initialized successfully")
            return True
        else:
            print("❌ Gemini Model failed to initialize (processor.model is None)")
            print("Note: Check if google-generativeai is installed and API key is valid.")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing OCRProcessor: {e}")
        return False

if __name__ == "__main__":
    success = test_ocr_init()
    sys.exit(0 if success else 1)
