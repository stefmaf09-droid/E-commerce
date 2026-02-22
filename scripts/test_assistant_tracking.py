
import logging
from src.ai.chatbot_manager import ChatbotManager

logging.basicConfig(level=logging.INFO)

def test_tracking_live():
    bot = ChatbotManager()
    
    # Numéro réel qui était en "Point Relais" hier
    tracking_number = "XS419416933FR"
    
    print(f"\n--- Testing Tracking Query (LIVE) ---")
    print(f"User: Quelles sont les informations pour le colis {tracking_number} ?")
    
    # Simuler le flux de l'assistant
    response_chunks = list(bot.generate_response_stream(f"Quelles sont les informations pour le colis {tracking_number} ?", []))
    response = "".join(response_chunks)
    
    print(f"Assistant: {response}")
    
    if "point de retrait" in response.lower() or "livré" in response.lower():
        print(f"\n✅ SUCCESS: Live status correctly identified!")
    else:
        print(f"\n❌ FAILURE: Status still seems incorrect or simulated.")

if __name__ == "__main__":
    test_tracking_live()
