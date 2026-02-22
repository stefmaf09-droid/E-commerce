
import logging
from src.ai.chatbot_manager import ChatbotManager

logging.basicConfig(level=logging.INFO)

def debug_bot():
    bot = ChatbotManager()
    
    # Test 1: Simple greeting
    print("\n--- Test 1: Greeting ---")
    response_chunks = list(bot.generate_response_stream("Bonjour", []))
    response = "".join(response_chunks)
    print(f"Assistant: {response}")
    
    # Test 2: Tracking (Manual Trigger)
    print("\n--- Test 2: Tracking (XS419416933FR) ---")
    response_chunks = list(bot.generate_response_stream("Où est mon colis XS419416933FR ?", []))
    response = "".join(response_chunks)
    print(f"Assistant: {response}")

if __name__ == "__main__":
    debug_bot()
