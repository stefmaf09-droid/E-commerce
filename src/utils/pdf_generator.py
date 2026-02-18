import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT, TA_CENTER

class ClaimPDFGenerator:
    """Generates formal PDF claim letters."""

    def __init__(self, output_dir: str = "data/claims/pdfs"):
        """
        Initialize the PDF generator.
        
        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Define custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='Header',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='NormalJustified',
            parent=self.styles['Normal'],
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='RightAlign',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT
        ))

    def generate_claim_pdf(self, claim_data: dict, output_filename: str = None) -> str:
        """
        Generate a PDF for the given claim.

        Args:
            claim_data: Dictionary containing claim details (order_id, carrier, amount, etc.)
            output_filename: Optional filename. If None, uses claim reference.

        Returns:
            Absolute path to the generated PDF file.
        """
        claim_ref = claim_data.get('claim_reference', 'UNKNOWN')
        if not output_filename:
            output_filename = f"{claim_ref}.pdf"
        
        output_path = self.output_dir / output_filename
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        story = []

        # -- Header Section --
        # Client Company Info (Placeholder for now, could be dynamic)
        client_info = """
        <b>E-Commerce Store Name</b><br/>
        123 Business Street<br/>
        75001 Paris, France<br/>
        contact@store.com
        """
        story.append(Paragraph(client_info, self.styles['Normal']))
        story.append(Spacer(1, 1*cm))

        # Carrier Info (Right Aligned)
        carrier_name = claim_data.get('carrier', 'Carrier Service')
        carrier_info = f"""
        <b>A l'attention du Service Réclamation {carrier_name}</b><br/>
        (Adresse du Siège Social)<br/>
        """
        story.append(Paragraph(carrier_info, self.styles['RightAlign']))
        story.append(Spacer(1, 2*cm))

        # Date and Subject
        date_str = datetime.now().strftime("%d/%m/%Y")
        story.append(Paragraph(f"Paris, le {date_str}", self.styles['RightAlign']))
        story.append(Spacer(1, 1*cm))

        subject = f"<b>Objet : Réclamation / Mise en demeure de remboursement - Colis {claim_data.get('tracking_number', 'N/A')}</b>"
        story.append(Paragraph(subject, self.styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        ref_line = f"<b>Référence Dossier :</b> {claim_ref}<br/><b>Commande :</b> {claim_data.get('order_id', 'N/A')}"
        story.append(Paragraph(ref_line, self.styles['Normal']))
        story.append(Spacer(1, 1*cm))

        # -- Body Content --
        intro_text = f"""
        Madame, Monsieur,<br/><br/>
        Par la présente, je vous notifie officiellement une réclamation concernant l'envoi référencé ci-dessus, confié à vos services.
        """
        story.append(Paragraph(intro_text, self.styles['NormalJustified']))

        # Problem Description
        dispute_type = claim_data.get('dispute_type', 'damage')
        if dispute_type == 'damage':
            reason_text = "Le colis a été livré dans un état endommagé, compromettant l'intégrité de la marchandise."
        elif dispute_type == 'lost':
            reason_text = "Le colis n'a jamais été livré à son destinataire et est considéré comme perdu."
        elif dispute_type == 'late':
            reason_text = "La livraison a été effectuée avec un retard inacceptable au regard de vos engagements."
        else:
            reason_text = "Un incident de livraison a été constaté."
            
        story.append(Paragraph(f"<b>Motif de la réclamation :</b> {reason_text}", self.styles['NormalJustified']))
        
        # Details & Demand
        amount = claim_data.get('amount', 0.0)
        details_text = f"""
        Conformément aux dispositions légales et à vos Conditions Générales de Vente, votre responsabilité est engagée.
        Le préjudice subi s'élève à <b>{amount:.2f} €</b>.<br/><br/>
        Je vous mets donc en demeure de procéder au remboursement de cette somme dans les plus brefs délais.
        """
        story.append(Paragraph(details_text, self.styles['NormalJustified']))
        story.append(Spacer(1, 1*cm))

        # Evidence List
        story.append(Paragraph("<b>Pièces justificatives jointes :</b>", self.styles['Normal']))
        evidence_list = [
            "- Facture commerciale",
            "- Preuve de dépôt (si disponible)",
            "- Photos des dommages " + ("(jointes au dossier)" if claim_data.get('photos') else "(non applicables)")
        ]
        for item in evidence_list:
            story.append(Paragraph(item, self.styles['Normal'], bulletText="•"))
        
        story.append(Spacer(1, 2*cm))

        # -- Signature --
        story.append(Paragraph("Cordialement,", self.styles['RightAlign']))
        story.append(Spacer(1, 1.5*cm))
        story.append(Paragraph("<b>Direction Service Client</b><br/>E-Commerce Store", self.styles['RightAlign']))

        # Build PDF
        doc.build(story)
        return str(output_path)

if __name__ == "__main__":
    # Test generation
    gen = ClaimPDFGenerator()
    test_data = {
        'claim_reference': 'TEST-PDF-001',
        'order_id': 'ORD-12345',
        'tracking_number': '1Z999999999',
        'carrier': 'Colissimo',
        'amount': 129.50,
        'dispute_type': 'damage',
        'photos': ['p1.jpg']
    }
    path = gen.generate_claim_pdf(test_data)
    print(f"PDF generated at: {path}")
