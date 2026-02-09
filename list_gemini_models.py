"""
Script pour lister les modèles Gemini disponibles avec la clé API actuelle.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
import google.generativeai as genai

print("🔍 Listing available Gemini models...")

api_key = Config.get_gemini_api_key()
if not api_key:
    print("❌ No API key found!")
    sys.exit(1)

genai.configure(api_key=api_key)

print(f"\n✅ API Key configured (ends with: ...{api_key[-8:]})")

try:
    print("\n📋 Available models:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  ✓ {model.name}")
            print(f"    Description: {model.display_name}")
            print(f"    Methods: {model.supported_generation_methods}")
            print()
except Exception as e:
    print(f"❌ Error listing models: {e}")
    import traceback
    traceback.print_exc()
