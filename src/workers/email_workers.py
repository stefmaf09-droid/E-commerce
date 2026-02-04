
import logging
from datetime import datetime
from typing import Dict, Any

from src.database.database_manager import DatabaseManager
from src.database.escalation_logger import EscalationLogger
from src.email_service.escalation_email_handler import EscalationEmailHandler
from src.reports.legal_document_generator import LegalDocumentGenerator

logger = logging.getLogger(__name__)

def execute_status_request(claim: Dict[str, Any]):
    """
    Worker function to execute a J+7 Status Request.
    """
    logger.info(f"WORKER: Processing Status Request for {claim['claim_reference']}")
    
    db = DatabaseManager()
    email_handler = EscalationEmailHandler()
    escalation_logger = EscalationLogger()
    
    # Logic copied and adapted from FollowUpManager
    country = claim.get('country', 'FR')
    lang = 'FR' if country == 'FR' else 'EN'
    
    success = email_handler.send_status_request_email(claim, lang=lang)
    
    escalation_logger.log_email_sent(
        claim_id=claim['id'],
        escalation_level=1,
        email_sent_to=email_handler.carrier_emails.get(claim['carrier'], 'unknown'),
        email_status='sent' if success else 'failed',
        details={'type': 'status_request', 'lang': lang}
    )
    
    if success:
        db.update_claim(claim['id'], 
                       follow_up_level=1, 
                       last_follow_up_at=datetime.now())
    else:
        raise Exception("Email sending failed")

def execute_warning(claim: Dict[str, Any]):
    """
    Worker function to execute a J+14 Warning.
    """
    logger.info(f"WORKER: Processing Warning for {claim['claim_reference']}")
    
    db = DatabaseManager()
    email_handler = EscalationEmailHandler()
    escalation_logger = EscalationLogger()
    
    country = claim.get('country', 'FR')
    lang = 'FR' if country == 'FR' else 'EN'
    
    success = email_handler.send_warning_email(claim, lang=lang)
    
    escalation_logger.log_email_sent(
        claim_id=claim['id'],
        escalation_level=2,
        email_sent_to=email_handler.carrier_emails.get(claim['carrier'], 'unknown'),
        email_status='sent' if success else 'failed',
        details={'type': 'warning', 'lang': lang}
    )
    
    if success:
        db.update_claim(claim['id'], 
                       follow_up_level=2, 
                       last_follow_up_at=datetime.now())
    else:
        raise Exception("Email sending failed")

def execute_formal_notice(claim: Dict[str, Any]):
    """
    Worker function to execute a J+21 Formal Notice.
    """
    logger.info(f"WORKER: Processing Formal Notice for {claim['claim_reference']}")
    
    db = DatabaseManager()
    email_handler = EscalationEmailHandler()
    escalation_logger = EscalationLogger()
    generator = LegalDocumentGenerator()
    
    country = claim.get('country', 'FR')
    lang = 'FR' if country == 'FR' else 'EN'
    
    # 1. Generate PDF
    pdf_path = generator.generate_formal_notice(claim, lang=lang)
    
    escalation_logger.log_pdf_generation(
        claim_id=claim['id'],
        escalation_level=3,
        pdf_path=pdf_path,
        details={'lang': lang, 'carrier': claim['carrier']}
    )
    
    # 2. Send Email
    email_success = email_handler.send_formal_notice_email(
        claim=claim,
        pdf_path=pdf_path,
        lang=lang
    )
    
    escalation_logger.log_email_sent(
        claim_id=claim['id'],
        escalation_level=3,
        email_sent_to=email_handler.carrier_emails.get(claim['carrier'], 'unknown'),
        email_status='sent' if email_success else 'failed',
        pdf_path=pdf_path,
        details={'type': 'formal_notice', 'lang': lang}
    )
    
    if email_success:
        db.update_claim(claim['id'], 
                       follow_up_level=3, 
                       last_follow_up_at=datetime.now(),
                       automation_status='action_required')
    else:
        raise Exception("Email sending failed")
