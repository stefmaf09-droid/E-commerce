
import pytest
from unittest.mock import MagicMock, patch
from src.analytics.bypass_scorer import BypassScorer
from src.api.webhook_handler import WebhookHandler
from src.ai.predictor import AIPredictor
from src.scrapers.ocr_processor import OCRProcessor
import json
import os

class TestAIEnhancements:
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        conn = MagicMock()
        db.get_connection.return_value = conn
        return db, conn

    def test_bypass_scorer_hybrid_estimation(self, mock_db):
        db, conn = mock_db
        scorer = BypassScorer(db)
        
        # Mock AIPredictor
        with patch.object(AIPredictor, 'predict_success') as mock_predict:
            mock_predict.return_value = {'probability': 0.8, 'reasoning': 'AI Reasoning'}
            
            # Mock Database stats (3 successes out of 4) -> 0.75
            conn.execute.return_value.fetchone.return_value = (3, 4)
            
            # Mock rejection factor (0.0)
            with patch.object(BypassScorer, '_calculate_rejection_factor') as mock_rej:
                mock_rej.return_value = 0.0
                
                # Proba = (0.7 * 0.8) + (0.3 * 0.75) = 0.56 + 0.225 = 0.785
                proba = scorer.estimate_success_probability('UPS', 'lost', 100.0)
                assert abs(proba - 0.785) < 0.01

    def test_bypass_scorer_rejection_factor(self, mock_db):
        db, conn = mock_db
        scorer = BypassScorer(db)
        
        # Mock stats (6 rejections out of 10) -> 0.6 rate (> 0.5)
        conn.execute.return_value.fetchone.return_value = (6, 10)
        
        factor = scorer._calculate_rejection_factor(conn, 'Colissimo')
        assert factor == 0.15

    def test_bypass_scorer_risk_score_density(self, mock_db):
        db, conn = mock_db
        scorer = BypassScorer(db)
        
        # 1. Mock alerts (3 alerts) -> 75 points
        # 2. Mock suspicious claims (0)
        # 3. Mock total claims (20) -> Density = 3/20 = 0.15 (> 0.1) -> +20 points
        # 4. Mock ancientness (New client)
        
        def mock_side_effect(query, params=None):
            m = MagicMock()
            q_lower = query.lower()
            if "system_alerts" in q_lower:
                m.fetchone.return_value = (3,)
            elif "claims" in q_lower:
                # Distinguish between suspicious (where payment_status = 'unpaid') and total
                if "payment_status" in q_lower:
                    m.fetchone.return_value = (0,) # suspicious_claims
                else:
                    m.fetchone.return_value = (20,) # total_claims
            elif "clients" in q_lower:
                m.fetchone.return_value = ("2026-02-01",)
            return m
            
        conn.execute.side_effect = mock_side_effect
        
        score = scorer.calculate_client_risk_score(1)
        # Score = 60 (max alerts) + 0 (suspicious) + 20 (density) = 80
        assert score == 80

    def test_webhook_idempotency(self, mock_db):
        db, conn = mock_db
        handler = WebhookHandler(db)
        
        # Case: Event already exists
        conn.execute.return_value.fetchone.return_value = (1,) # Found in webhook_events
        
        payload = {"msg": {"tracking_number": "TRK123", "tag": "Delivered"}}
        result = handler.handle_tracking_update(payload)
        
        assert result is True
        # Verify db.update_claim was NOT called
        db.update_claim.assert_not_called()

    def test_webhook_extended_events(self, mock_db):
        db, conn = mock_db
        handler = WebhookHandler(db)
        
        # Mock not found in idempotency check
        # Mock claim found
        def mock_side_effect(query, params=None):
            m = MagicMock()
            if "webhook_events" in query:
                m.fetchone.return_value = None
            elif "claims" in query:
                m.fetchone.return_value = (1, 'submitted', 'unpaid', 'late_delivery')
            return m
        conn.execute.side_effect = mock_side_effect
        
        payload = {"msg": {"tracking_number": "TRK123", "tag": "Exception"}}
        result = handler.handle_tracking_update(payload)
        
        assert result is True
        db.update_claim.assert_called_with(1, status='under_review', automation_status='action_required')

    def test_predictor_legal_reasoning(self):
        predictor = AIPredictor()
        reasoning = predictor.get_legal_reasoning('Colissimo', 'lost')
        assert "Code de Commerce" in reasoning
        
        reasoning_late = predictor.get_legal_reasoning('DHL', 'late_delivery')
        assert "frais de port" in reasoning_late

    def test_ocr_feedback_context(self):
        processor = OCRProcessor()
        
        # Test empty context
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            assert processor._get_feedback_context() == ""
            
        # Test with context
        mock_data = [
            {'original_text_snippet': 'Taux de rejet élevé...', 'corrected_reason_key': 'weight_match'}
        ]
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('builtins.open', pytest.raises(Exception)): # Simplify or mock open properly
                # Let's mock the json.load
                with patch('json.load') as mock_load:
                    mock_load.return_value = mock_data
                    with patch('builtins.open'):
                        context = processor._get_feedback_context()
                        assert "weight_match" in context
