import pytest
import asyncio
from src.ai.skill_executor import AntigravitySkillExecutor

class TestAntigravitySkillExecutor:
    
    @pytest.fixture
    def executor(self):
        return AntigravitySkillExecutor()
    
    def test_can_handle_existing_carrier(self, executor):
        # Vérifie que les transporteurs standard sont gérés
        assert executor.can_handle('colissimo') is True
        assert executor.can_handle('CHRONOPOST') is True # Test case-insensitive
        assert executor.can_handle('mondial_relay') is True # Test normalization
        
    def test_cannot_handle_unknown_carrier(self, executor):
        assert executor.can_handle('unknown_carrier') is False
        
    @pytest.mark.asyncio
    async def test_execute_claim_submission_success(self, executor):
        dispute = {
            'tracking_number': 'FR123456789',
            'carrier': 'colissimo',
            'order_id': 'ORD-123'
        }
        claim_text = "Ma réclamation"
        
        result = await executor.execute_claim_submission('colissimo', dispute, claim_text)
        
        assert result['status'] == 'success_simulated'
        assert result['carrier'] == 'colissimo'
        assert 'claim_reference' in result
        assert result['method'] == 'antigravity_skill'
        
    @pytest.mark.asyncio
    async def test_execute_claim_submission_unsupported(self, executor):
        result = await executor.execute_claim_submission('unknown', {}, "")
        assert result['status'] == 'unsupported'
        
    def test_get_skill_info(self, executor):
        info = executor.get_skill_info('colissimo')
        assert info['available'] is True
        assert 'skill_path' in info
        
        info = executor.get_skill_info('nonexistent')
        assert info['available'] is False
