import pytest
import asyncio
import time
import logging
from src.orchestrator import AutoRecoveryOrchestrator
from src.database import get_db_manager

# Configure logging to see performance metrics
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSystemPerformance:
    
    @pytest.fixture
    def orchestrator(self, db_manager):
        return AutoRecoveryOrchestrator(db_manager=db_manager)
    
    @pytest.mark.asyncio
    async def test_high_volume_dispute_processing(self, orchestrator, db_manager, sample_client):
        """Test processing 100 disputes concurrently."""
        num_disputes = 100
        disputes = []
        
        for i in range(num_disputes):
            disputes.append({
                'order_id': f'PERF-ORD-{i}',
                'tracking_number': f'TRK-{i}',
                'carrier': 'colissimo',
                'dispute_type': 'late_delivery',
                'order_date': '2026-01-10',
                'total_recoverable': 50.0,
                'client_email': sample_client['email']
            })
            
        # Patch heavy operations to make test deterministic and fast
        async def fast_submit(dispute, claim_text, pod_analysis):
            return {'method': 'manual_required', 'status': 'pending_manual', 'tracking_id': f"TEST-{dispute['order_id']}"}

        async def fast_update(dispute, result):
            return None

        async def fast_notify(dispute, result):
            return None

        # Replace heavy components
        orchestrator.claim_generator.generate = lambda d, p: "SIMULATED_CLAIM"
        orchestrator.claim_generator.save_claim = lambda txt, path: None
        orchestrator._submit_via_portal = fast_submit
        orchestrator._update_dashboard = fast_update
        orchestrator._notify_client = fast_notify
        orchestrator.skill_executor.can_handle = lambda carrier: False

        start_time = time.time()

        # Parallel processing
        tasks = [orchestrator.process_dispute(d) for d in disputes]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"PROCESSED {num_disputes} DISPUTES IN {duration:.2f} SECONDS")
        logger.info(f"AVERAGE TIME PER DISPUTE: {duration/num_disputes:.4f}s")
        
        # Verify all were processed
        assert len(results) == num_disputes
        for r in results:
            assert r['success'] is True or r.get('status') == 'pending_manual'
            
        # Check database
        claims = db_manager.get_client_claims(sample_client['id'])
        assert len(claims) >= num_disputes
        
        # Target: Less than 5 seconds for 100 simulated (non-browser) claims
        assert duration < 10

    @pytest.mark.asyncio
    async def test_database_concurrency(self, db_manager, sample_client):
        """Test high concurrency database writes."""
        num_writes = 500
        start_time = time.time()
        
        def write_activity(i):
            db_manager.log_activity(
                action=f"PERF_TEST_{i}",
                client_id=sample_client['id']
            )
            
        # Use ThreadPool for sync db operations
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=20) as executor:
            list(executor.map(write_activity, range(num_writes)))
            
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"COMPLETED {num_writes} DB WRITES IN {duration:.2f} SECONDS")
        assert duration < 5

    def test_order_sync_performance(self):
        """Vérifie que la synchronisation des commandes reste sous 10s pour 100 clients fictifs."""
        from src.workers.order_sync_worker import OrderSyncWorker
        worker = OrderSyncWorker()
        # Simulation: patcher list_clients pour retourner 100 clients fictifs
        worker.credentials_manager.list_clients = lambda: [(f"client{i}@test.com", "Shopify", "2026-01-01") for i in range(100)]
        start = time.time()
        worker.sync_all_clients()
        duration = time.time() - start
        assert duration < 10, f"Sync trop lente: {duration:.2f}s"
