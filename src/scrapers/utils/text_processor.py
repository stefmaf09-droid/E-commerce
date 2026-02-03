"""
Text processor for extracting dispute patterns from reviews and forum posts.

Uses regex and keyword matching to identify common dispute patterns.
"""

import re
from typing import Dict, List, Set
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class DisputePatternExtractor:
    """Extract dispute-related patterns from text."""
    
    # Keywords for different dispute types
    DELAY_KEYWORDS = {
        'retard', 'tard', 'délai', 'attente', 'jamais arrivé',
        'toujours pas reçu', 'en cours', 'bloqué'
    }
    
    LOSS_KEYWORDS = {
        'perdu', 'disparu', 'introuvable', 'jamais reçu',
        'pas reçu', 'manquant', 'égaré', 'volatilisé'
    }
    
    DAMAGE_KEYWORDS = {
        'cassé', 'endommagé', 'abîmé', 'détérioré',
        'écrasé', 'défoncé', 'ouvert', 'déchiré'
    }
    
    PROOF_KEYWORDS = {
        'signature', 'preuve', 'pod', 'photo', 'justificatif',
        'attestation', 'reçu', 'accusé'
    }
    
    CARRIERS = {
        'colissimo': ['colissimo', 'la poste', 'laposte'],
        'chronopost': ['chronopost', 'chrono'],
        'ups': ['ups'],
        'fedex': ['fedex', 'fed ex'],
        'dhl': ['dhl'],
        'dpd': ['dpd', 'geopost'],
        'mondial relay': ['mondial relay', 'mondial-relay', 'mondialrelay'],
        'relais colis': ['relais colis', 'relaiscolis']
    }
    
    def __init__(self):
        """Initialize the pattern extractor."""
        self.delay_pattern = re.compile(
            r'(?:retard\s*de\s*)?(\d+)\s*(jours?|semaines?|heures?|mois)(?:\s*de\s*retard)?',
            re.IGNORECASE
        )
        self.amount_pattern = re.compile(
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:€|euros?|EUR)',
            re.IGNORECASE
        )
    
    def extract_patterns(self, text: str) -> Dict:
        """
        Extract all dispute patterns from text.
        
        Args:
            text: Review or post text
            
        Returns:
            Dictionary with extracted patterns
        """
        text_lower = text.lower()
        
        patterns = {
            'has_delay': self._detect_keywords(text_lower, self.DELAY_KEYWORDS),
            'has_loss': self._detect_keywords(text_lower, self.LOSS_KEYWORDS),
            'has_damage': self._detect_keywords(text_lower, self.DAMAGE_KEYWORDS),
            'has_proof_issue': self._detect_keywords(text_lower, self.PROOF_KEYWORDS),
            'delay_mentions': self._extract_delays(text),
            'amount_mentions': self._extract_amounts(text),
            'carriers': self._extract_carriers(text_lower),
            'severity_score': 0
        }
        
        # Calculate severity score (1-5)
        score = 0
        if patterns['has_delay']: score += 1
        if patterns['has_loss']: score += 2
        if patterns['has_damage']: score += 1.5
        if patterns['delay_mentions']: score += len(patterns['delay_mentions']) * 0.5
        
        patterns['severity_score'] = min(5, score)
        
        return patterns
    
    def _detect_keywords(self, text: str, keywords: Set[str]) -> bool:
        """Check if any keyword is present in text."""
        return any(keyword in text for keyword in keywords)
    
    def _extract_delays(self, text: str) -> List[Dict[str, str]]:
        """
        Extract delay mentions (e.g., "3 jours de retard").
        
        Returns:
            List of dictionaries with 'value' and 'unit'
        """
        matches = self.delay_pattern.findall(text)
        delays = []
        
        for value, unit in matches:
            delays.append({
                'value': int(value),
                'unit': unit.lower()
            })
        
        return delays
    
    def _extract_amounts(self, text: str) -> List[float]:
        """
        Extract monetary amounts mentioned.
        
        Returns:
            List of amounts in euros
        """
        matches = self.amount_pattern.findall(text)
        amounts = []
        
        for match in matches:
            # Remove thousands separator and convert
            amount_str = match.replace(',', '')
            try:
                amounts.append(float(amount_str))
            except ValueError:
                continue
        
        return amounts
    
    def _extract_carriers(self, text: str) -> List[str]:
        """
        Extract mentioned carriers.
        
        Returns:
            List of standardized carrier names
        """
        found_carriers = []
        
        for carrier_name, keywords in self.CARRIERS.items():
            if any(keyword in text for keyword in keywords):
                found_carriers.append(carrier_name)
        
        return found_carriers
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Simple sentiment analysis based on keywords.
        
        Returns:
            'negative', 'neutral', or 'positive'
        """
        negative_words = {
            'horrible', 'catastrophe', 'nul', 'mauvais', 'incompétent',
            'arnaque', 'scandaleux', 'inadmissible', 'désastreux'
        }
        
        positive_words = {
            'excellent', 'parfait', 'super', 'rapide', 'efficace',
            'professionnel', 'satisfait', 'content'
        }
        
        text_lower = text.lower()
        
        neg_count = sum(1 for word in negative_words if word in text_lower)
        pos_count = sum(1 for word in positive_words if word in text_lower)
        
        # Threshold lowered for short texts
        if neg_count > pos_count:
            return 'negative'
        elif pos_count > neg_count:
            return 'positive'
        else:
            return 'neutral'
    
    def extract_summary_stats(self, texts: List[str]) -> Dict:
        """
        Extract summary statistics from multiple texts.
        
        Args:
            texts: List of review/post texts
            
        Returns:
            Dictionary with aggregate statistics
        """
        all_patterns = [self.extract_patterns(text) for text in texts]
        
        # Aggregate carriers
        all_carriers = []
        for p in all_patterns:
            all_carriers.extend(p['carriers'])
        
        carrier_counts = Counter(all_carriers)
        
        # Aggregate delays
        all_delays = []
        for p in all_patterns:
            for delay in p['delay_mentions']:
                # Convert to days
                value = delay['value']
                unit = delay['unit']
                
                if 'heure' in unit:
                    days = value / 24
                elif 'semaine' in unit:
                    days = value * 7
                elif 'mois' in unit:
                    days = value * 30
                else:  # jours
                    days = value
                
                all_delays.append(days)
        
        return {
            'total_reviews': len(texts),
            'with_delay': sum(1 for p in all_patterns if p['has_delay']),
            'with_loss': sum(1 for p in all_patterns if p['has_loss']),
            'with_damage': sum(1 for p in all_patterns if p['has_damage']),
            'avg_severity': sum(p['severity_score'] for p in all_patterns) / len(all_patterns) if all_patterns else 0,
            'carrier_mentions': dict(carrier_counts.most_common()),
            'avg_delay_days': sum(all_delays) / len(all_delays) if all_delays else 0,
            'max_delay_days': max(all_delays) if all_delays else 0
        }
