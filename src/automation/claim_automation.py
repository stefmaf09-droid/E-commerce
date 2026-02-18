"""
Claim Automation Module - Automatic claim submission workflow.

Handles photo analysis, claim generation, and carrier submission.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import random
import string

logger = logging.getLogger(__name__)


# Délais légaux de réponse par transporteur (en jours)
LEGAL_RESPONSE_TIMES = {
    'colissimo': 30,        # Code des Postes - 1 mois maximum
    'chronopost': 21,       # CGV Chronopost - 21 jours
    'ups': 30,              # CGV UPS - 30 jours
    'dpd': 25,              # CGV DPD - 25 jours
    'dhl': 21,              # CGV DHL - 21 jours
    'mondial relay': 35,    # CGV Mondial Relay - 35 jours
    'gls': 28,              # CGV GLS - 28 jours
    'fedex': 30,            # CGV FedEx - 30 jours
    'tnt': 28,              # CGV TNT - 28 jours
    'default': 30           # Délai par défaut si transporteur inconnu
}


class ClaimAutomation:
    """Automate claim submission process."""
    
    def __init__(self):
        """Initialize claim automation."""
        self.claims_dir = Path("data/claims")
        self.claims_dir.mkdir(parents=True, exist_ok=True)
        
        # Load carrier config
        config_path = Path("config/carrier_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.carrier_config = json.load(f)
        else:
            logger.warning("Carrier config not found, using defaults")
            self.carrier_config = {}
        
        # Initialize Email Sender
        # In a real app, we'd inject this dependency or load creds from secure storage
        import os
        from src.email_service.email_sender import EmailSender
        from src.utils.pdf_generator import ClaimPDFGenerator
        
        self.email_sender = EmailSender(
            smtp_user=os.getenv('GMAIL_SENDER'),
            smtp_password=os.getenv('GMAIL_APP_PASSWORD'),
            from_email=os.getenv('GMAIL_SENDER')
        )
        self.pdf_generator = ClaimPDFGenerator()
    
    def analyze_photos(self, photo_paths: List[str]) -> Dict[str, Any]:
        """
        Analyze uploaded photos (metadata, quality checks).
        
        Args:
            photo_paths: List of absolute paths to photos
            
        Returns:
            Dictionary with analysis results
        """
        try:
            analysis = {
                'total_photos': len(photo_paths),
                'photos': [],
                'quality_score': 0.0,
                'has_damage_evidence': False,
                'has_delivery_proof': False
            }
            
            for photo_path in photo_paths:
                if not os.path.exists(photo_path):
                    continue
                
                # Get file metadata
                file_stat = os.stat(photo_path)
                file_size = file_stat.st_size
                
                photo_info = {
                    'path': photo_path,
                    'filename': os.path.basename(photo_path),
                    'size_kb': round(file_size / 1024, 2),
                    'timestamp': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                }
                
                # Simple quality checks
                if file_size > 50 * 1024:  # > 50KB
                    photo_info['quality'] = 'good'
                    analysis['quality_score'] += 1.0
                else:
                    photo_info['quality'] = 'low'
                    analysis['quality_score'] += 0.5
                
                # Simulated AI detection (in production, use actual ML model)
                filename_lower = photo_info['filename'].lower()
                if any(word in filename_lower for word in ['damage', 'casse', 'broken', 'endommage']):
                    photo_info['type'] = 'damage_evidence'
                    analysis['has_damage_evidence'] = True
                elif any(word in filename_lower for word in ['delivery', 'livraison', 'proof', 'preuve']):
                    photo_info['type'] = 'delivery_proof'
                    analysis['has_delivery_proof'] = True
                else:
                    photo_info['type'] = 'general'
                
                analysis['photos'].append(photo_info)
            
            # Normalize quality score
            if analysis['total_photos'] > 0:
                analysis['quality_score'] = round(
                    analysis['quality_score'] / analysis['total_photos'], 2
                )
            
            logger.info(f"Photo analysis complete: {analysis['total_photos']} photos, quality: {analysis['quality_score']}")
            return analysis
            
        except Exception as e:
            logger.error(f"Photo analysis failed: {e}")
            return {
                'total_photos': 0,
                'photos': [],
                'quality_score': 0.0,
                'error': str(e)
            }
    
    def generate_claim_text(
        self, 
        dispute_data: Dict[str, Any], 
        photo_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate optimized claim text based on dispute and photo analysis.
        
        Args:
            dispute_data: Dispute information
            photo_analysis: Result from analyze_photos()
            
        Returns:
            Formatted claim text
        """
        carrier = dispute_data.get('carrier', 'Unknown')
        order_id = dispute_data.get('order_id', 'N/A')
        amount = dispute_data.get('total_recoverable', 0.0)
        dispute_type = dispute_data.get('dispute_type', 'damage')
        
        # Build claim text
        claim_text = f"""RÉCLAMATION - Commande {order_id}

Transporteur : {carrier}
Montant demandé : {amount}€

DESCRIPTION DU PROBLÈME :
"""
        
        if dispute_type == 'damage':
            claim_text += """Le colis a été livré endommagé. Les dommages constatés sont visibles sur les photos jointes.
"""
        elif dispute_type == 'late':
            claim_text += """La livraison a été effectuée avec un retard significatif par rapport à la date promise.
"""
        elif dispute_type == 'lost':
            claim_text += """Le colis n'a jamais été livré et est considéré comme perdu.
"""
        else:
            claim_text += """Problème de livraison constaté. Voir photos jointes pour détails.
"""
        
        # Add photo evidence details
        if photo_analysis['total_photos'] > 0:
            claim_text += f"""
PREUVES JOINTES :
- {photo_analysis['total_photos']} photo(s) à l'appui
- Qualité des preuves : {photo_analysis['quality_score']}/1.0
"""
            
            if photo_analysis.get('has_damage_evidence'):
                claim_text += "- Photos de dommages incluses\n"
            if photo_analysis.get('has_delivery_proof'):
                claim_text += "- Preuve de livraison incluse\n"
        
        claim_text += f"""
Date de réclamation : {datetime.now().strftime('%d/%m/%Y %H:%M')}

Nous demandons le remboursement complet du montant de {amount}€ conformément aux conditions générales de transport.
"""
        
        return claim_text
    
    def _generate_claim_reference(self) -> str:
        """Generate unique claim reference."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"CLM-{timestamp}-{random_suffix}"
    
    def submit_claim_to_carrier(
        self, 
        order_id: str,
        carrier: str,
        claim_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit claim to carrier via Email (with PDF).
        
        Args:
            order_id: Order ID
            carrier: Carrier name
            claim_data: Claim information (text, photos, amount)
            
        Returns:
            Submission result with claim reference
        """
        try:
            claim_reference = self._generate_claim_reference()
            
            # 1. Identify carrier email settings
            carrier_key = carrier.lower()
            carrier_settings = self.carrier_config.get(carrier_key, self.carrier_config.get('default'))
            
            carrier_email = carrier_settings['email']
            subject_template = carrier_settings['claim_subject_template']
            
            tracking_number = f"TRK-{order_id}" # Simplified for now, should come from dispute_data
            
            # Format subject
            subject = subject_template.format(
                tracking_number=tracking_number,
                claim_reference=claim_reference
            )
            
            # 2. Prepare attachments (Images + PDF Claim)
            attachments = list(claim_data.get('photos', []))
            
            # Generate PDF
            try:
                pdf_data = {
                    'claim_reference': claim_reference,
                    'order_id': order_id,
                    'tracking_number': tracking_number,
                    'carrier': carrier,
                    'amount': claim_data.get('amount', 0.0),
                    'dispute_type': 'damage', # Should pass this from claim_data if available
                    'photos': claim_data.get('photos', [])
                }
                pdf_path = self.pdf_generator.generate_claim_pdf(pdf_data)
                attachments.append(pdf_path)
                logger.info(f"Generated PDF claim for {claim_reference}: {pdf_path}")
            except Exception as e:
                logger.error(f"Failed to generate PDF for {claim_reference}: {e}")
                # Continue without PDF if it fails (or fail hard? let's continue for resilience)
            
            # 3. Send Email
            email_success = self.email_sender.send_claim_to_carrier(
                carrier_email=carrier_email,
                claim_reference=claim_reference,
                tracking_number=tracking_number,
                subject=subject,
                body=claim_data.get('text', ''),
                attachments=attachments
            )
            
            # 4. Save record locally regardless of email success (for retry)
            claim_record = {
                'claim_reference': claim_reference,
                'order_id': order_id,
                'carrier': carrier,
                'claim_text': claim_data.get('text', ''),
                'claim_amount': claim_data.get('amount', 0.0),
                'photos': claim_data.get('photos', []),
                'submitted_at': datetime.now().isoformat(),
                'status': 'submitted' if email_success else 'failed_to_send',
                'submission_method': 'email_automation',
                'target_email': carrier_email,
                'pdf_path': pdf_path if 'pdf_path' in locals() else None
            }
            
            claim_file = self.claims_dir / f"{claim_reference}.json"
            with open(claim_file, 'w', encoding='utf-8') as f:
                json.dump(claim_record, f, indent=2, ensure_ascii=False)
            
            if email_success:
                logger.info(f"Claim emailed successfully: {claim_reference} to {carrier_email}")
                
                # Délai légal
                estimated_days = LEGAL_RESPONSE_TIMES.get(carrier_key, LEGAL_RESPONSE_TIMES['default'])
                
                return {
                    'success': True,
                    'claim_reference': claim_reference,
                    'carrier': carrier,
                    'submitted_at': claim_record['submitted_at'],
                    'estimated_response_days': estimated_days,
                    'legal_deadline': True,
                    'message': f"Réclamation envoyée à {carrier} ({carrier_email})"
                }
            else:
                logger.error(f"Failed to email claim {claim_reference} to {carrier_email}")
                return {
                    'success': False, 
                    'error': "Email sending failed",
                    'message': "Erreur lors de l'envoi email, sauvegardé pour réessai."
                }
            
        except Exception as e:
            logger.error(f"Claim submission failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Erreur critique de soumission"
            }
    
    def update_dispute_status(
        self,
        order_id: str,
        status: str,
        claim_reference: Optional[str] = None
    ) -> bool:
        """
        Update dispute status (simulated - in production use database).
        
        Args:
            order_id: Order ID
            status: New status
            claim_reference: Optional claim reference
            
        Returns:
            True if successful
        """
        try:
            # In production, update database
            # For now, just log
            logger.info(f"Dispute status updated: {order_id} -> {status} (ref: {claim_reference})")
            
            # Create status file for tracking
            status_dir = Path("data/dispute_status")
            status_dir.mkdir(parents=True, exist_ok=True)
            
            status_file = status_dir / f"{order_id}.json"
            status_data = {
                'order_id': order_id,
                'status': status,
                'claim_reference': claim_reference,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Status update failed: {e}")
            return False
    
    def process_claim_submission(
        self,
        order_id: str,
        photo_paths: List[str],
        dispute_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete workflow: analyze photos, generate claim, submit.
        
        Args:
            order_id: Order ID
            photo_paths: List of photo file paths
            dispute_data: Dispute information
            
        Returns:
            Complete workflow result
        """
        logger.info(f"Starting claim submission workflow for order {order_id}")
        
        result = {
            'success': False,
            'steps': []
        }
        
        try:
            # Step 1: Analyze photos
            result['steps'].append({'step': 'analyze_photos', 'status': 'running'})
            photo_analysis = self.analyze_photos(photo_paths)
            result['photo_analysis'] = photo_analysis
            result['steps'][-1]['status'] = 'completed'
            
            # Step 2: Generate claim text
            result['steps'].append({'step': 'generate_claim', 'status': 'running'})
            claim_text = self.generate_claim_text(dispute_data, photo_analysis)
            result['claim_text'] = claim_text
            result['steps'][-1]['status'] = 'completed'
            
            # Step 3: Submit to carrier
            result['steps'].append({'step': 'submit_to_carrier', 'status': 'running'})
            submission_result = self.submit_claim_to_carrier(
                order_id=order_id,
                carrier=dispute_data.get('carrier', 'Unknown'),
                claim_data={
                    'text': claim_text,
                    'photos': photo_paths,
                    'amount': dispute_data.get('total_recoverable', 0.0)
                }
            )
            result['submission'] = submission_result
            result['steps'][-1]['status'] = 'completed'
            
            if submission_result['success']:
                # Step 4: Update status
                result['steps'].append({'step': 'update_status', 'status': 'running'})
                self.update_dispute_status(
                    order_id=order_id,
                    status='claim_submitted',
                    claim_reference=submission_result['claim_reference']
                )
                result['steps'][-1]['status'] = 'completed'
                
                result['success'] = True
                result['claim_reference'] = submission_result['claim_reference']
                result['message'] = submission_result['message']
            else:
                result['success'] = False
                result['error'] = submission_result.get('error', 'Unknown error')
            
            logger.info(f"Claim workflow completed for {order_id}: success={result['success']}")
            return result
            
        except Exception as e:
            logger.error(f"Claim workflow failed: {e}")
            result['success'] = False
            result['error'] = str(e)
            return result


# Convenience functions for easy import
def process_claim_submission(
    order_id: str,
    photo_paths: List[str],
    dispute_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Process automatic claim submission."""
    automation = ClaimAutomation()
    return automation.process_claim_submission(order_id, photo_paths, dispute_data)


if __name__ == "__main__":
    # Test the automation
    print("="*70)
    print("CLAIM AUTOMATION - Test")
    print("="*70)
    
    # Test data
    test_dispute = {
        'order_id': 'ORD-TEST-001',
        'carrier': 'Colissimo',
        'total_recoverable': 45.0,
        'dispute_type': 'damage'
    }
    
    test_photos = [
        'data/client_photos/ORD-TEST-001/test_photo_1.jpg',
        'data/client_photos/ORD-TEST-001/test_photo_2.jpg'
    ]
    
    # Create test photos directory
    os.makedirs('data/client_photos/ORD-TEST-001', exist_ok=True)
    
    # Create dummy photo files
    for photo in test_photos:
        with open(photo, 'wb') as f:
            f.write(b'fake image data' * 1000)  # ~15KB
    
    # Run workflow
    result = process_claim_submission(
        order_id=test_dispute['order_id'],
        photo_paths=test_photos,
        dispute_data=test_dispute
    )
    
    print(f"\n✅ Workflow completed: Success = {result['success']}")
    if result['success']:
        print(f"📋 Claim Reference: {result['claim_reference']}")
        print(f"💬 Message: {result['message']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown')}")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
