"""
Appeal Generator - Generate counter-claims for carrier refusals.

This module generates professional appeal letters based on the specific refusal reason
provided by the carrier (e.g., bad signature, weight match, packaging).
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AppealGenerator:
    """Generate legally valid appeals for carrier refusals."""
    
    TEMPLATES: Dict[str, str] = {}

    def __init__(self):
        logger.info("AppealGenerator initialized.")
        self.load_templates()

    def load_templates(self):
        """Load templates from JSON file."""
        import json
        import os
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'appeal_templates.json')
        
        try:
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    self.TEMPLATES = json.load(f)
                logger.info(f"Loaded {len(self.TEMPLATES)} appeal templates.")
            else:
                logger.warning("Template file not found, using empty default.")
                self.TEMPLATES = {}
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            self.TEMPLATES = {}

    def generate(self, dispute: Dict, refusal_reason_key: str) -> str:
        """
        Generate an appeal letter based on refusal reason.
        
        Args:
            dispute: Dispute data dictionary
            refusal_reason_key: Key identified by AI (bad_signature, etc.)
            
        Returns:
            Generated appeal text
        """
        # Reload templates to get latest changes
        self.load_templates()
        
        template = self.TEMPLATES.get(refusal_reason_key, self.TEMPLATES.get('default', "Modèle introuvable."))
        
        variables = self._prepare_variables(dispute, refusal_reason_key)
        
        try:
            return template.format(**variables)
        except Exception as e:
            logger.error(f"Error formatting appeal template: {e}")
            return template  # Fallback to returning raw template if format fails

    def _prepare_variables(self, dispute: Dict, reason_key: str) -> Dict:
        """Prepare variables for template filling."""
        return {
            'tracking_number': dispute.get('tracking_number', 'N/A'),
            'claim_reference': dispute.get('claim_reference', 'N/A'),
            'recipient_name': dispute.get('recipient_name', 'le destinataire'),
            'client_name': dispute.get('client_name', 'Client'),
            'client_email': dispute.get('client_email', ''),
            'claim_amount': f"{dispute.get('amount_requested', dispute.get('total_recoverable', 0.0)):.2f}",
            'weight': dispute.get('weight', 'N/A'),
            'ship_date': dispute.get('order_date', 'N/A'),
            'status_desc': dispute.get('status', 'Litige en cours'),
            'refusal_reason': reason_key
        }

    @staticmethod
    def generate_pdf(text: str, filename: str) -> bytes:
        """
        Generate a PDF file from text.
        
        Args:
            text: Content of the letter
            filename: Output filename (used for metadata)
            
        Returns:
            PDF bytes
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from io import BytesIO
            import textwrap

            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # Margins
            margin_left = 2.5 * cm
            margin_top = 2.5 * cm
            y_position = height - margin_top
            
            # Font setup
            p.setFont("Helvetica", 11)
            line_height = 14
            
            # Split text into lines
            paragraphs = text.split('\n')
            
            for paragraph in paragraphs:
                if not paragraph.strip():
                    y_position -= line_height  # Extra space for empty lines
                    continue
                
                # Handling bold (simple heuristic: if line starts with **, make it bold)
                if paragraph.strip().startswith('**') and paragraph.strip().endswith('**'):
                     p.setFont("Helvetica-Bold", 11)
                     clean_text = paragraph.strip().replace('**', '')
                elif paragraph.strip().startswith('Objet :'):
                     p.setFont("Helvetica-Bold", 11)
                     clean_text = paragraph
                else:
                     p.setFont("Helvetica", 11)
                     clean_text = paragraph

                # Wrap text
                wrapped_lines = textwrap.wrap(clean_text, width=85) # Approx char width for A4
                
                for line in wrapped_lines:
                    if y_position < 2 * cm: # New page
                        p.showPage()
                        y_position = height - margin_top
                        p.setFont("Helvetica", 11)
                    
                    p.drawString(margin_left, y_position, line)
                    y_position -= line_height
            
            p.showPage()
            p.save()
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes
            
        except ImportError:
            logger.error("ReportLab not installed. Cannot generate PDF.")
            return b""
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return b""

    def save_appeal(self, text: str, output_path: str):
        """Save the generated appeal to a file (txt or pdf)."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.lower().endswith('.pdf'):
            pdf_bytes = self.generate_pdf(text, Path(output_path).name)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
        
        logger.info(f"Appeal saved to {output_path}")

if __name__ == "__main__":
    # Test
    gen = AppealGenerator()
    test_dispute = {
        'tracking_number': '1Z99999999999',
        'claim_reference': 'CLM-2024-001',
        'recipient_name': 'M. Martin',
        'client_name': 'Shop & Co',
        'amount_requested': 150.50
    }
    print(gen.generate(test_dispute, 'bad_signature'))
