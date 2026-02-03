import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from src.reports.pdf_generator import PDFGenerator

class TestPDFGenerator:
    
    @pytest.fixture
    def generator(self):
        return PDFGenerator()
    
    @pytest.fixture
    def sample_kpis(self):
        return {
            'total_recovered': 1250.50,
            'total_claims': 15,
            'success_rate': 73.3,
            'average_processing_time': 5.5,
            'by_carrier': {
                'colissimo': {'count': 5, 'total_value': 450.0, 'success_rate': 80.0},
                'chronopost': {'count': 3, 'total_value': 280.0, 'success_rate': 66.7}
            }
        }

    def test_generate_monthly_report(self, generator, sample_kpis):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_monthly.pdf")
            
            # Use real generation to check for crashes
            # Note: We already have reportlab installed
            path = generator.generate_monthly_report(
                client_name="Client Test",
                client_email="test@client.com",
                month="Janvier 2026",
                kpis=sample_kpis,
                disputes=[],
                output_path=output_path
            )
            
            assert os.path.exists(path)
            assert os.path.getsize(path) > 1000  # Basic sanity check
            
    def test_generate_dispute_detail_report(self, generator):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_dispute.pdf")
            dispute = {
                'claim_reference': 'CLM-123',
                'carrier': 'colissimo',
                'tracking_number': 'FR123',
                'dispute_type': 'late_delivery',
                'submitted_at': '2026-01-20',
                'status': 'submitted',
                'claim_value': 50.0,
                'claim_text': 'Ceci est une réclamation de test.'
            }
            
            path = generator.generate_dispute_detail_report(dispute, output_path)
            
            assert os.path.exists(path)
            assert os.path.getsize(path) > 1000

    def test_init_error_when_reportlab_missing(self):
        with patch('src.reports.pdf_generator.REPORTLAB_AVAILABLE', False):
            with pytest.raises(ImportError) as excinfo:
                PDFGenerator()
            assert "ReportLab is required" in str(excinfo.value)

    def test_generate_monthly_report_empty_carrier(self, generator):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_empty.pdf")
            kpis = {'total_recovered': 0, 'total_claims': 0, 'by_carrier': {}}
            path = generator.generate_monthly_report("N", "E", "M", kpis, [], output_path)
            assert os.path.exists(path)

    def test_pdf_compliance(self, generator, sample_kpis):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_conformite.pdf")
            generator.generate_monthly_report(
                client_name="Client Test",
                client_email="test@client.com",
                month="Janvier 2026",
                kpis=sample_kpis,
                disputes=[],
                output_path=output_path
            )
            # Champs attendus dans le PDF
            required_fields = ["Client Test", "Janvier 2026", "Total récupéré", "Taux de succès"]
            assert generator.verify_pdf_compliance(output_path, required_fields, lang='FR')
