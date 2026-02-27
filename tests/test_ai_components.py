import pytest
from unittest.mock import MagicMock, patch
from src.ai.pod_analyzer import PODAnalyzer
from src.ai.claim_generator import ClaimGenerator

class TestAIComponents:
    
    @pytest.fixture
    def mock_openai(self):
        with patch('openai.OpenAI') as mock:
            yield mock
            
    def test_pod_analyzer_initialization(self):
        """PODAnalyzer migré vers Gemini 2.0 Flash — vérifie self.model au lieu de self.client (OpenAI)."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model.return_value = MagicMock()
            analyzer = PODAnalyzer(api_key="test-gemini-key")
            assert analyzer.model is not None
        
    def test_pod_analyzer_fallback_parsing(self):
        analyzer = PODAnalyzer(api_key="test-key")
        raw_text = "La signature est illisible et le colis n'est pas visible sur la photo."
        result = analyzer._parse_vision_response(raw_text)
        assert 'Signature illisible ou suspecte' in result['anomalies']
        assert 'Colis non visible sur la photo' in result['anomalies']
        assert result['confidence_invalid'] >= 0.5

    def test_pod_analyzer_parse_json_response(self):
        analyzer = PODAnalyzer(api_key="test-key")
        raw_json = """
        {
            "signature_present": true,
            "signature_legible": false,
            "package_visible": true,
            "timestamp_present": true,
            "timestamp_coherent": false,
            "photo_quality": "poor",
            "anomalies": ["Signature suspecte", "Timestamp incoherente"],
            "confidence_invalid": 0.8,
            "summary": "POD presentant des anomalies de signature"
        }
        """
        result = analyzer._parse_vision_response(raw_json)
        assert result['signature_present'] is True
        assert abs(result['confidence_invalid'] - 0.8) < 0.001
        assert len(result['anomalies']) == 2

    def test_claim_generator_retard(self):
        generator = ClaimGenerator()
        dispute = {
            'dispute_type': 'retard_livraison',
            'tracking_number': 'TRK123',
            'order_date': '2026-01-01',
            'shipping_cost': 10.0,
            'total_recoverable': 30.0,
            'client_name': 'Jean',
            'client_email': 'jean@test.com'
        }
        claim = generator.generate(dispute)
        assert 'TRK123' in claim
        assert 'retard de livraison' in claim.lower()
        assert '30.00' in claim

    def test_claim_generator_damaged(self):
        generator = ClaimGenerator()
        dispute = {
            'dispute_type': 'colis_endommage',
            'tracking_number': 'TRK_DAMAGED',
            'damage_description': 'Écran brisé',
            'order_value': 200.0,
            'shipping_cost': 15.0,
            'total_recoverable': 215.0
        }
        claim = generator.generate(dispute)
        assert 'TRK_DAMAGED' in claim
        assert 'colis endommagé' in claim.lower()
        assert 'Écran brisé' in claim
        assert '215.00' in claim
        
    def test_claim_generator_with_pod_anomalies(self):
        generator = ClaimGenerator()
        dispute = {
            'dispute_type': 'pod_invalide',
            'tracking_number': 'TRK_POD',
            'order_value': 100.0,
            'carrier': 'Colissimo',
            'delivery_date': '2026-01-15',
            'delivery_time': '14:00',
            'recipient_name': 'Jean Destinataire',
            'shipping_cost': 5.0,
            'damages': 20.0,
            'total_recoverable': 125.0
        }
        pod_analysis = {
            'anomalies': ['Signature suspecte', 'Photo floue']
        }
        claim = generator.generate(dispute, pod_analysis)
        assert 'TRK_POD' in claim
        assert 'Signature suspecte' in claim
        assert 'Photo floue' in claim
        assert '100.00' in claim
        assert '125.00' in claim
