"""
Email module for automated communications.
"""

from .email_sender import (
    EmailSender,
    send_disputes_detected_email,
    send_claim_submitted_email,
    send_claim_accepted_email,
    send_claim_rejected_email
)

__all__ = [
    'EmailSender',
    'send_disputes_detected_email',
    'send_claim_submitted_email',
    'send_claim_accepted_email',
    'send_claim_rejected_email'
]
