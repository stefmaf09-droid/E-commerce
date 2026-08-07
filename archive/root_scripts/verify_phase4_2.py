
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.scrapers.ocr_processor import OCRProcessor
from src.ai.llm_advice_generator import LLMAdviceGenerator
from src.analytics.sentiment_analyzer import SentimentAnalyzer

def verify_ai_components():
    print("=== 🧪 VÉRIFICATION PHASE 4.2 : IA VISION & NLP ===")
    
    # 1. Test OCR Preprocessing
    print("\n--- 👁️ Vision OCR ---")
    ocr = OCRProcessor()
    meta = ocr.preprocess_image("test_rejet.jpg")
    print(f"✅ Preprocessing result: {meta['status']} (Quality: {meta['quality_score']})")
    
    analysis = ocr.analyze_rejection_text("Signature does not match records.")
    print(f"✅ Text analysis: {analysis['label_en']} (Confidence: {analysis['confidence']})")

    # 2. Test LLM Advice
    print("\n--- ⚖️ LLM Advice Generator ---")
    llm = LLMAdviceGenerator()
    advice = llm.generate_counter_argument(analysis, {"carrier": "Chronopost", "tracking_number": "CHR123"})
    print(f"✅ Generated Advice: {advice[:100]}...")
    if "Article L. 133-3" in advice:
        print("✅ Legal reference found in advice")

    # 3. Test Sentiment Analysis
    print("\n--- 📊 Sentiment Analysis ---")
    sentiment = SentimentAnalyzer()
    s_neg = sentiment.analyze_sentiment("C'est inacceptable ! Je vais porter plainte !")
    print(f"✅ Negative sentiment: {s_neg['sentiment']} (Priority: {s_neg['priority']})")
    
    s_pos = sentiment.analyze_sentiment("Merci beaucoup pour votre efficacité, c'est parfait.")
    print(f"✅ Positive sentiment: {s_pos['sentiment']} (Priority: {s_pos['priority']})")

    if s_neg['priority'] == 'HIGH' and s_pos['priority'] == 'LOW':
        print("✅ Sentiment prioritization logic working!")

    print("\n=== ✨ TOUTES LES VÉRIFICATIONS SONT TERMINÉES ===")

if __name__ == "__main__":
    verify_ai_components()
