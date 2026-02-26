"""
LegalDocumentGenerator - Générateur de documents juridiques (Mise en demeure, etc.).
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import sys

# Support relative imports when running as a script
if __name__ == "__main__":
    os.path.abspath_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(os.path.abspath_path)

from src.utils.i18n import get_i18n_text, format_currency
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT

logger = logging.getLogger(__name__)

class LegalDocumentGenerator:
    """Génère des documents juridiques PDF conformes au Code des Transports ou lois locales."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Configuration des styles pour documents juridiques."""
        self.styles.add(ParagraphStyle(
            name='LegalBold',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='LegalBody',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='FormalNoticeHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            spaceBefore=20,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='RightAligned',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT,
            spaceAfter=12
        ))

    def generate_formal_notice(self, claim: Dict[str, Any], lang: str = 'FR', output_dir: str = "data/legal_docs") -> str:
        """
        Génère une Mise en Demeure formelle.
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = f"MED_{claim['claim_reference']}_{lang.upper()}_{datetime.now().strftime('%Y%m%d')}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        currency = claim.get('currency', 'EUR')
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2.5*cm,
            leftMargin=2.5*cm,
            topMargin=3*cm,
            bottomMargin=2.5*cm
        )
        
        story = []
        
        # 0. Logo
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(root_dir, 'static', 'refundly_logo.png')
        if os.path.exists(logo_path):
            im = Image(logo_path, width=8*cm, height=2.5*cm)
            im.hAlign = 'LEFT'
            story.append(im)
            story.append(Spacer(1, 0.5*cm))
        
        # 1. En-tête
        story.append(Paragraph(f"<b>{get_i18n_text('legal_header_from', lang)}</b>", self.styles['LegalBold']))
        company = claim.get('company_name', 'Client E-commerce')
        story.append(Paragraph(f"Refundly.ai", self.styles['LegalBody']))
        story.append(Paragraph(f"Agissant pour le compte de : {company}", self.styles['LegalBody']))
        story.append(Spacer(1, 1*cm))
        
        story.append(Paragraph(f"<b>{get_i18n_text('legal_header_to', lang)}</b>", self.styles['LegalBold']))
        story.append(Paragraph(f"Service Litiges {claim['carrier']}", self.styles['LegalBody']))
        story.append(Spacer(1, 1*cm))
        
        # 2. Date et Lieu
        story.append(Paragraph(f"Fait le {datetime.now().strftime('%d/%m/%Y')}", self.styles['RightAligned']))
        story.append(Spacer(1, 1*cm))
        
        # 3. OBJET
        story.append(Paragraph(f"<b>{get_i18n_text('legal_header_subject', lang)}</b>", self.styles['LegalBold']))
        story.append(Paragraph(f"{get_i18n_text('legal_ref_claim', lang)} {claim['claim_reference']}", self.styles['LegalBody']))
        story.append(Paragraph(f"{get_i18n_text('legal_ref_tracking', lang)} {claim.get('tracking_number', 'Inconnu')}", self.styles['LegalBody']))
        story.append(Spacer(1, 1*cm))
        
        # 4. Corps de la lettre
        story.append(Paragraph(f"Madame, Monsieur,", self.styles['LegalBody']))
        
        address = claim.get('delivery_address', '').upper()
        law_key = self._determine_applicable_law(address)
        law_text = get_i18n_text(law_key, lang)
        
        body_text = f"""
        {get_i18n_text('legal_body_intro', lang)}
        (Type : {claim.get('dispute_type', 'Réclamation')}) - {get_i18n_text('legal_ref_claim', lang)} {claim['claim_reference']} 
        pour un montant de {format_currency(claim.get('amount_requested', 0.0), currency)}.
        <br/><br/>
        {law_text}
        <br/><br/>
        <b>{get_i18n_text('legal_body_demand', lang)} ({format_currency(claim.get('amount_requested', 0.0), currency)})</b>
        <br/><br/>
        {get_i18n_text('legal_body_closing', lang)}
        """
        story.append(Paragraph(body_text, self.styles['LegalBody']))
        
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Cordialement / Regards,", self.styles['LegalBody']))
        
        story.append(Spacer(1, 2*cm))
        story.append(Paragraph(f"<b>{get_i18n_text('legal_signature', lang)}</b>", self.styles['LegalBold']))
        
        # Génération
        doc.build(story)
        logger.info(f"Mise en demeure générée : {output_path}")
        return output_path

    def _determine_applicable_law(self, address: str) -> str:
        """Détermine la clé de traduction de la loi applicable selon l'adresse."""
        import re
        
        def has_word(text, word):
            return re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE)
        
        if has_word(address, 'NY') or has_word(address, 'NEW YORK'):
            return 'legal_law_ny'
        elif has_word(address, 'CA') or has_word(address, 'CALIFORNIA'):
            return 'legal_law_ca'
        elif has_word(address, 'TX') or has_word(address, 'TEXAS'):
            return 'legal_law_tx'
        elif has_word(address, 'FL') or has_word(address, 'FLORIDA'):
            return 'legal_law_fl'
        elif has_word(address, 'IL') or has_word(address, 'ILLINOIS'):
            return 'legal_law_il'
        elif any(has_word(address, usa_key) for usa_key in ['US', 'USA', 'UNITED STATES']):
            return 'legal_law_us_federal'

            
        EU_COUNTRIES = [
            'AUSTRIA', 'BELGIUM', 'BULGARIA', 'CROATIA', 'CYPRUS', 'CZECH REPUBLIC', 
            'DENMARK', 'ESTONIA', 'FINLAND', 'FRANCE', 'GERMANY', 'GREECE', 'HUNGARY', 
            'IRELAND', 'ITALY', 'LATVIA', 'LITHUANIA', 'LUXEMBOURG', 'MALTA', 'NETHERLANDS', 
            'POLAND', 'PORTUGAL', 'ROMANIA', 'SLOVAKIA', 'SLOVENIA', 'SPAIN', 'SWEDEN',
            'AUTRICHE', 'BELGIQUE', 'ESPAGNE', 'ITALIE', 'PAYS-BAS'
        ]
        if any(has_word(address, country) for country in EU_COUNTRIES):
             return 'legal_law_eu_cmr'

        return 'legal_body_law'

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_claim = {
        'claim_reference': 'CLM-2026-TEST-US',
        'carrier': 'FedEx',
        'tracking_number': '123456789012',
        'amount_requested': 250.00,
        'currency': 'USD',
        'dispute_type': 'Lost Package',
        'company_name': 'US Store Inc.',
        'delivery_address': '123 Broadway, New York, NY 10001, USA'
    }
    gen = LegalDocumentGenerator()
    path = gen.generate_formal_notice(sample_claim, lang='EN')
    print(f"Generated test PDF: {path}")
