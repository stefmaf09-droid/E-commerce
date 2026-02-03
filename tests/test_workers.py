import pytest
import time
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
from src.workers.order_sync_worker import OrderSyncWorker, main

class TestOrderSyncWorker:
    
    @pytest.fixture
    def worker(self):
        with patch('src.workers.order_sync_worker.CredentialsManager'), \
             patch('src.workers.order_sync_worker.DisputeDetectionEngine'):
            return OrderSyncWorker()

    def test_sync_all_clients_success(self, worker):
        worker.credentials_manager.list_clients.return_value = [('client1', 'shopify', 'date1'), ('client2', 'woocommerce', 'date2')]
        with patch.object(worker, 'sync_client') as mock_sync:
            worker.sync_all_clients()
            assert mock_sync.call_count == 2

    def test_sync_all_clients_with_error(self, worker):
        worker.credentials_manager.list_clients.return_value = [('c1', 'p1', 'd1')]
        with patch.object(worker, 'sync_client') as mock_sync:
            mock_sync.side_effect = Exception("Test Error")
            worker.sync_all_clients()  # Should handle exception and continue

    def test_sync_client_no_credentials(self, worker):
        worker.credentials_manager.get_credentials.return_value = None
        worker.sync_client('bad_client')
        # Should log error and return

    def test_sync_client_unsupported_platform(self, worker):
        worker.credentials_manager.get_credentials.return_value = {'platform': 'unknown'}
        worker.sync_client('client1')
        # Should log error and return

    @patch('src.database.get_db_manager')
    @patch('src.email_service.send_disputes_detected_email')
    def test_sync_client_success(self, mock_email, mock_db_manager, worker):
        # Setup mocks
        client_id = 'test@example.com'
        worker.credentials_manager.get_credentials.return_value = {'platform': 'shopify', 'shop_domain': 'test.myshopify.com'}
        
        mock_conn = MagicMock()
        mock_conn.authenticate.return_value = True
        mock_conn.fetch_orders.return_value = [{'order_id': 'ORD1', 'total_amount': 100}]
        
        # Inject mock connector directly into the instance or class map
        with patch.dict(worker.CONNECTOR_MAP, {'shopify': MagicMock(return_value=mock_conn)}):
            worker.dispute_detector.analyze_orders.return_value = [
                {'order_id': 'ORD1', 'has_dispute': True, 'total_recoverable': 110.0, 'carrier': 'colissimo', 'order_date': '2026-01-01', 'tracking_number': 'TRK1', 'recipient': {'name': 'Jean'}}
            ]
            
            mock_db = MagicMock()
            mock_db_manager.return_value = mock_db
            mock_db.get_client.return_value = {'id': 1}
            mock_db.get_client_disputes.return_value = [] # No existing disputes
            
            result = worker.sync_client(client_id)
            
            assert result['disputes_found'] == 1
            assert result['new_disputes_saved'] == 1
            assert result['orders_fetched'] == 1
            assert result['total_recoverable'] == 110.0
        mock_db.create_dispute.assert_called_once()
        mock_email.assert_called_once()
        mock_db.log_notification.assert_called_once()

    @patch.object(OrderSyncWorker, 'sync_all_clients')
    @patch('time.sleep')
    def test_run_forever_loop(self, mock_sleep, mock_sync, worker):
        # Stop loop after one vibration by raising exception after first call
        mock_sync.side_effect = [None, KeyboardInterrupt]
        worker.run_forever()
        assert mock_sync.call_count == 2

    @patch.object(OrderSyncWorker, 'sync_all_clients')
    @patch('time.sleep')
    def test_run_forever_error_retry(self, mock_sleep, mock_sync, worker):
        mock_sync.side_effect = [Exception("Loop error"), KeyboardInterrupt]
        worker.run_forever()
        assert mock_sleep.called

    def test_sync_client_once(self, worker):
        with patch.object(worker, 'sync_client', return_value={'ok': True}) as mock_sync:
            result = worker.sync_client_once('test@test.com')
            assert result['ok'] is True
            mock_sync.assert_called_with('test@test.com')

    @patch('argparse.ArgumentParser.parse_args')
    @patch('src.workers.order_sync_worker.OrderSyncWorker')
    def test_main_once_all(self, mock_worker_class, mock_args):
        mock_args.return_value = MagicMock(mode='once', client=None, interval=24)
        mock_worker = mock_worker_class.return_value
        main()
        mock_worker.sync_all_clients.assert_called_once()

    @patch('argparse.ArgumentParser.parse_args')
    @patch('src.workers.order_sync_worker.OrderSyncWorker')
    def test_main_once_client(self, mock_worker_class, mock_args):
        mock_args.return_value = MagicMock(mode='once', client='c1@t.com', interval=24)
        mock_worker = mock_worker_class.return_value
        mock_worker.sync_client_once.return_value = {'client_id': 'c1@t.com', 'platform': 's', 'orders_fetched': 1, 'disputes_found': 0, 'total_recoverable': 0}
        main()
        mock_worker.sync_client_once.assert_called_with('c1@t.com')

    @patch('argparse.ArgumentParser.parse_args')
    @patch('src.workers.order_sync_worker.OrderSyncWorker')
    def test_main_continuous(self, mock_worker_class, mock_args):
        mock_args.return_value = MagicMock(mode='continuous', client=None, interval=12)
        mock_worker = mock_worker_class.return_value
        main()
        mock_worker.run_forever.assert_called_once()
