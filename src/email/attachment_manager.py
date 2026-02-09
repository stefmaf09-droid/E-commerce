"""
Attachment Manager - Orchestrating Email Processing
Coordinates EmailListener, AttachmentExtractor, and DatabaseManager.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os

from src.email.email_listener import EmailListener
from src.email.attachment_extractor import AttachmentExtractor
from src.database.database_manager import get_db_manager
from src.scrapers.ocr_processor import OCRProcessor
from src.config import Config

logger = logging.getLogger(__name__)

class AttachmentManager:
    """Orchestrates fetching emails and extracting attachments."""
    
    def __init__(self):
        self.db = get_db_manager()
        # Storage path from config or default
        self.storage_path = os.getenv('ATTACHMENTS_STORAGE_PATH', os.path.join(os.getcwd(), 'attachments'))
        self.extractor = AttachmentExtractor(self.storage_path)
        self.ocr = OCRProcessor()
        
    def sync_emails(self, client_email: str) -> Dict:
        """
        Synchronize emails for a client and extract attachments.
        
        Args:
            client_email: The client's email to filter/organize.
            
        Returns:
            Summary of the synchronization process.
        """
        # Get IMAP config from secrets/env
        # In a real app, these might be stored per-client or use a central support mailbox
        imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        imap_port = int(os.getenv('IMAP_PORT', 993))
        username = os.getenv('IMAP_USERNAME')
        password = os.getenv('IMAP_PASSWORD')
        
        if not username or not password:
            return {'success': False, 'message': 'Email credentials not configured.'}
            
        listener = EmailListener(imap_server, imap_port, username, password)
        
        if not listener.connect():
            return {'success': False, 'message': 'Failed to connect to email server.'}
            
        try:
            # For now, we search for unread emails where the client email appears in the subject or body
            # OR we just fetch all unread and the UI helps link them.
            # A more advanced version would look for CLM-XXX references.
            unread_emails = listener.fetch_unread_emails()
            
            total_extracted = 0
            new_attachments = []
            
            for mail_data in unread_emails:
                msg = mail_data['message']
                
                # Extract attachments
                files = self.extractor.extract_attachments(msg, client_email)
                
                for file_info in files:
                    # Try to find a claim reference in subject or message
                    claim_ref = self._extract_claim_reference(mail_data['subject']) 
                    
                    # 🔍 Perform AI Analysis (OCR/NLP) on the file
                    ai_analysis_text = ""
                    if file_info['mime_type'] in ['application/pdf', 'image/jpeg', 'image/png']:
                        try:
                            # Extract text and analyze
                            text, nested_attachments = self.ocr.extract_all_from_file(file_info['saved_path'], file_info['original_filename'])
                            analysis = self.ocr.analyze_rejection_text(text)
                            
                            if analysis and analysis.get('reason_key') != 'unknown':
                                ai_analysis_text = f"Analyzed: {analysis.get('label_fr')} (Confidence: {analysis.get('confidence')})"
                                # If it's a rejection, we update the claim status and advice
                                if claim_ref:
                                    self.db.update_claim_ai_analysis(
                                        claim_reference=claim_ref,
                                        reason_key=analysis.get('reason_key'),
                                        advice=analysis.get('advice_fr'),
                                        status='rejected' if analysis.get('reason_key') != 'success' else None
                                    )
                        except Exception as e:
                            logger.warning(f"AI Analysis failed for {file_info['original_filename']}: {e}")

                    # Save to database
                    attachment_id = self.db.create_email_attachment(
                        client_email=client_email,
                        claim_reference=claim_ref,
                        email_subject=mail_data['subject'],
                        email_from=mail_data['from'],
                        email_received_at=mail_data['date'],
                        attachment_filename=file_info['original_filename'],
                        attachment_path=file_info['saved_path'],
                        file_size=file_info['file_size'],
                        mime_type=file_info['mime_type'],
                        ai_analysis=ai_analysis_text
                    )
                    
                    file_info['db_id'] = attachment_id
                    new_attachments.append(file_info)
                    total_extracted += 1
                
                # Mark as read after processing
                listener.mark_as_read(mail_data['id'])
                
            return {
                'success': True,
                'message': f'Sync complete. Extracted {total_extracted} attachments.',
                'attachments': new_attachments
            }
            
        finally:
            listener.disconnect()

    def _extract_claim_reference(self, text: str) -> Optional[str]:
        """Simple regex to find CLM-XXXX patterns."""
        import re
        match = re.search(r'CLM-\d{8}-\w+', text)
        return match.group(0) if match else None

    def get_attachments(self, client_email: str, claim_ref: str = None) -> List[Dict]:
        """Retrieve stored attachments from DB."""
        return self.db.get_client_attachments(client_email, claim_ref)

    def link_to_claim(self, attachment_id: int, claim_ref: str):
        """Link an orphan attachment to a claim."""
        self.db.link_attachment_to_claim(attachment_id, claim_ref)
