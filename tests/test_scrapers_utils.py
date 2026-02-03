import pytest
import time
from unittest.mock import MagicMock, patch
from src.scrapers.utils.rate_limiter import RateLimiter
from src.scrapers.utils.text_processor import DisputePatternExtractor

class TestRateLimiter:
    def test_init(self):
        limiter = RateLimiter(requests_per_second=2.0, burst=5)
        assert limiter.min_interval == 0.5
        assert limiter.burst == 5
        assert limiter.tokens == 5

    def test_wait_no_delay_needed(self):
        limiter = RateLimiter(requests_per_second=10.0, burst=1)
        start = time.time()
        limiter.wait()
        end = time.time()
        assert end - start < 0.1
        assert limiter.tokens == 0

    @patch('time.sleep')
    def test_wait_with_delay(self, mock_sleep):
        limiter = RateLimiter(requests_per_second=10.0, burst=1)
        limiter.tokens = 0
        limiter.last_token_update = time.time()
        
        limiter.wait()
        mock_sleep.assert_called_once()
    
    def test_context_manager(self):
        limiter = RateLimiter(requests_per_second=100.0)
        with limiter as l:
            assert l == limiter
            assert limiter.tokens < limiter.burst

class TestDisputePatternExtractor:
    @pytest.fixture
    def extractor(self):
        return DisputePatternExtractor()

    def test_detect_keywords(self, extractor):
        text = "Mon colis est en retard et abîmé"
        assert extractor._detect_keywords(text.lower(), extractor.DELAY_KEYWORDS) is True
        assert extractor._detect_keywords(text.lower(), extractor.DAMAGE_KEYWORDS) is True
        assert extractor._detect_keywords(text.lower(), extractor.LOSS_KEYWORDS) is False

    def test_extract_delays(self, extractor):
        text = "J'ai 3 jours de retard sur ma livraison"
        delays = extractor._extract_delays(text)
        assert len(delays) == 1
        assert delays[0]['value'] == 3
        assert delays[0]['unit'] == 'jours'

    def test_extract_amounts(self, extractor):
        text = "Le colis valait 150.50€ et j'ai payé 10 euros de frais"
        amounts = extractor._extract_amounts(text)
        assert 150.5 in amounts
        assert 10.0 in amounts

    def test_extract_carriers(self, extractor):
        text = "Livraison par Colissimo et Chronopost"
        carriers = extractor._extract_carriers(text.lower())
        assert 'colissimo' in carriers
        assert 'chronopost' in carriers

    def test_analyze_sentiment(self, extractor):
        assert extractor.analyze_sentiment("C'est une arnaque horrible") == 'negative'
        assert extractor.analyze_sentiment("Service parfait et rapide") == 'positive'
        assert extractor.analyze_sentiment("Le colis est arrivé") == 'neutral'

    def test_extract_patterns(self, extractor):
        text = "Colis Colissimo perdu de 50€"
        patterns = extractor.extract_patterns(text)
        assert patterns['has_loss'] is True
        assert 'colissimo' in patterns['carriers']
        assert 50.0 in patterns['amount_mentions']
        assert patterns['severity_score'] >= 2

    def test_extract_summary_stats(self, extractor):
        texts = [
            "Colis en retard de 2 jours",
            "Produit cassé",
            "Jamais reçu mon colis"
        ]
        stats = extractor.extract_summary_stats(texts)
        assert stats['total_reviews'] == 3
        assert stats['with_delay'] == 1
        assert stats['with_loss'] == 1
        assert stats['with_damage'] == 1
        assert stats['avg_delay_days'] == 2.0
