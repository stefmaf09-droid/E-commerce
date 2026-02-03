
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analyseur de sentiment pour les interactions SAV.
    Identifie les clients frustrés ou mécontents pour priorisation.
    """
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyse le sentiment du texte.
        Retourne un score de sentiment (-1.0 à 1.0) et des labels.
        """
        text_lower = text.lower()
        
        # Mots-clés de frustration (Simulation Lexicale)
        negative_words = ['énervé', 'mécontent', 'inacceptable', 'scandaleux', 'remboursement immédiat', 'avocat', 'plainte', 'nul']
        positive_words = ['merci', 'super', 'génial', 'rapide', 'efficace', 'parfait']
        
        neg_count = sum(1 for word in negative_words if word in text_lower)
        pos_count = sum(1 for word in positive_words if word in text_lower)
        
        score = 0
        if neg_count > 0:
            score = -0.5 * min(neg_count, 2)
        if pos_count > 0:
            score += 0.3 * min(pos_count, 2)
            
        # Déterminer le label
        if score <= -0.5:
            sentiment = "CRITICAL_FRUSTRATION"
            priority = "HIGH"
        elif score < 0:
            sentiment = "DISSATISFIED"
            priority = "MEDIUM"
        elif score > 0.5:
            sentiment = "VERY_SATISFIED"
            priority = "LOW"
        else:
            sentiment = "NEUTRAL"
            priority = "NORMAL"
            
        return {
            "score": score,
            "sentiment": sentiment,
            "priority": priority,
            "detected_frustration": neg_count > 0
        }

    def batch_analyze_tickets(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyse une liste de tickets et ajoute les métadonnées de sentiment."""
        for ticket in tickets:
            content = ticket.get('preview', '') + " " + ticket.get('subject', '')
            ticket['sentiment_analysis'] = self.analyze_sentiment(content)
        return tickets
