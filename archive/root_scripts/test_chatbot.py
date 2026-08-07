"""
Script de test rapide pour le chatbot.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai.chatbot_manager import ChatbotManager

print("🔧 Test du chatbot...")

try:
    # Initialiser le chatbot
    chatbot = ChatbotManager()
    print("✅ Chatbot initialisé")
    
    # Tester une question simple
    print("\n📤 Question: 'Bonjour'")
    response_chunks = list(chatbot.generate_response_stream("Bonjour", []))
    response = "".join(response_chunks)
    print(f"📥 Réponse: {response[:200]}...")
    
    print("\n✅ Test réussi !")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
