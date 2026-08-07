"""Test si les tools sont correctement formatés pour Gemini 2.5"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai.chatbot_tools import ChatbotTools
import json

tools = ChatbotTools()
available_tools = tools.get_available_tools()

print("🔧 Tools disponibles:")
print(json.dumps(available_tools, indent=2, ensure_ascii=False))

print(f"\n\n✅ {len(available_tools)} outils trouvés")

# Test si le format est compatible avec Gemini API
try:
    import google.generativeai as genai
    from src.config import Config
    
    api_key = Config.get_gemini_api_key()
    genai.configure(api_key=api_key)
    
    # Essayer de créer un modèle avec les tools
    model = genai.GenerativeModel('gemini-2.5-flash', tools=available_tools)
    print("\n✅ Modèle créé avec succès avec les tools!")
    
except Exception as e:
    print(f"\n❌ Erreur lors de la création du modèle: {e}")
    import traceback
    traceback.print_exc()
