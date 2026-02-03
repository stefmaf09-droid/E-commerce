"""
LegalDocumentGenerator - Générateur de documents juridiques (Mise en demeure, etc.).
"""

import os
from datetime import datetime
from typing import Dict, Any
import logging
import logging
import sys

# Support relative imports when running as a script
if __name__ == "__main__":
    os.environ['PYTHONPATH'] = os.getcwd()
    sys.path.append(os.getcwd())

from src.utils.i18n import get_i18n_text, format_currency
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT

logger = logging.getLogger(__name__)

class LegalDocumentGenerator:
    """Génère des documents juridiques PDF conformes au Code des Transports."""
    
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
        
        Args:
            claim: Données de la réclamation
            lang: Langue du document ('FR' ou 'EN')
            output_dir: Dossier de sortie
            
        Returns:
            Chemin vers le PDF généré
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
        
        # 1. En-tête (Expéditeur & Destinataire)
        story.append(Paragraph(f"<b>{get_i18n_text('legal_header_from', lang)}</b>", self.styles['LegalBold']))
        story.append(Paragraph(f"{claim.get('customer_name', 'Client E-commerce')}", self.styles['LegalBody']))
        story.append(Paragraph(f"Agissant par mandat de : Recours E-commerce", self.styles['LegalBody']))
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
        
        # Listes de pays pour détection
        EU_COUNTRIES = [
            'AUSTRIA', 'BELGIUM', 'BULGARIA', 'CROATIA', 'CYPRUS', 'CZECH REPUBLIC', 
            'DENMARK', 'ESTONIA', 'FINLAND', 'FRANCE', 'GERMANY', 'GREECE', 'HUNGARY', 
            'IRELAND', 'ITALY', 'LATVIA', 'LITHUANIA', 'LUXEMBOURG', 'MALTA', 'NETHERLANDS', 
            'POLAND', 'PORTUGAL', 'ROMANIA', 'SLOVAKIA', 'SLOVENIA', 'SPAIN', 'SWEDEN',
            'AUTRICHE', 'BELGIQUE', 'BULGARIE', 'CHYPRE', 'DANEMARK', 'ESPAGNE', 'ESTONIE', 
            'FINLANDE', 'GRÈCE', 'HONGRIE', 'IRLANDE', 'ITALIE', 'LETTONIE', 'LITUANIE', 
            'PAYS-BAS', 'POLOGNE', 'ROUMANIE', 'SLOVAQUIE', 'SLOVÉNIE', 'SUÈDE'
        ]

        # Sélection de la loi spécifique
        law_text = get_i18n_text('legal_body_law', lang)
        address = claim.get('delivery_address', '').upper()
        
        if lang == 'DE':
             law_text = get_i18n_text('legal_body_law', 'DE')
        elif lang == 'IT':
             law_text = get_i18n_text('legal_body_law', 'IT')
        elif lang == 'ES':
             law_text = get_i18n_text('legal_body_law', 'ES')
        elif any(country in address for country in EU_COUNTRIES):
             # Fallback CMR pour toute l'Union Européenne
             law_text = get_i18n_text('legal_law_eu_cmr', 'EN' if lang == 'EN' else 'FR')
        elif lang == 'EN':
            if any(uk_key in address for uk_key in ['UK', 'UNITED KINGDOM', 'LONDON', 'MANCHESTER', 'BIRMINGHAM']):
                law_text = get_i18n_text('legal_law_uk', lang)
            elif any(hk_key in address for hk_key in ['HK', 'HONG KONG', 'KOWLOON', 'LANTAU']):
                law_text = get_i18n_text('legal_law_hk', lang)
            elif any(sg_key in address for sg_key in ['SG', 'SINGAPORE', 'SENTOSA']):
                law_text = get_i18n_text('legal_law_sg', lang)
            elif 'NY' in address or 'NEW YORK' in address:
                law_text = get_i18n_text('legal_law_ny', lang)
            elif 'CA' in address or 'CALIFORNIA' in address:
                law_text = get_i18n_text('legal_law_ca', lang)
            elif 'TX' in address or 'TEXAS' in address:
                law_text = get_i18n_text('legal_law_tx', lang)
            elif any(usa_key in address for usa_key in ['USA', 'UNITED STATES', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']):
                law_text = get_i18n_text('legal_law_us_federal', lang)
        body_text = f"""
        {get_i18n_text('legal_body_intro', lang)}
        (Type : {claim['dispute_type']}) - {get_i18n_text('legal_ref_claim', lang)} {claim['claim_reference']} 
        pour un montant de {format_currency(claim['amount_requested'], currency)}.
        <br/><br/>
        {law_text}
        <br/><br/>
        <b>{get_i18n_text('legal_body_demand', lang)} ({format_currency(claim['amount_requested'], currency)})</b>
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

if __name__ == "__main__":
    # Test
    sample_claim = {
        'claim_reference': 'CLM-2026-TEST',
        'carrier': 'Colissimo',
        'tracking_number': '6A1234567890',
        'amount_requested': 124.50,
        'dispute_type': 'Colis Perdu',
        'customer_name': 'Boutique Alpha'
    }
    gen = LegalDocumentGenerator()
    gen.generate_formal_notice(sample_claim)
