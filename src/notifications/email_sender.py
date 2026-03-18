"""
Email Sender — Module notifications (façade).

Redirige vers src.email_service.email_sender qui est le module canonique.
Conservé pour compatibilité avec les imports existants.
Ajoute send_admin_notification() manquante (utilisée par proactive_agent.py).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

from src.config import Config

# ── Réexports du module canonique ─────────────────────────────────────────────
from src.email_service.email_sender import (
    EmailSender,
    send_claim_submitted_email,
    send_claim_accepted_email,
    send_claim_rejected_email,
    send_disputes_detected_email,
)

__all__ = [
    "EmailSender",
    "send_claim_submitted_email",
    "send_claim_accepted_email",
    "send_claim_rejected_email",
    "send_disputes_detected_email",
    "send_welcome_email",
    "send_admin_notification",
]


def send_welcome_email(to_email: str, client_name: str) -> bool:
    """Send welcome email after registration (délègue au module canonique)."""
    from src.email_service.email_sender import _get_smtp_settings
    cfg = _get_smtp_settings()
    sender = EmailSender(
        **cfg,
    )
    return sender.send_welcome_email(
        to_email=to_email,
        client_name=client_name,
        dashboard_url=Config.get('DASHBOARD_URL', default='http://localhost:8503'),
    )


def send_admin_notification(subject: str, body: str) -> bool:
    """
    Envoie une notification interne à l'équipe admin Refundly.

    Args:
        subject: Sujet de l'email admin
        body:    Corps de l'email en texte brut

    Returns:
        True si envoyé avec succès
    """
    admin_email = Config.get('ADMIN_EMAIL') or Config.get('SMTP_USER') or ''
    if not admin_email:
        logger.warning("ADMIN_EMAIL non configuré — notification admin non envoyée.")
        logger.info(f"[ADMIN NOTIF] {subject}: {body}")
        return False

    from src.email_service.email_sender import _get_smtp_settings
    cfg = _get_smtp_settings()
    sender = EmailSender(
        **cfg,
        from_name='Refundly.ai Bot',
    )

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; padding: 20px;">
        <h2>🔔 Notification Admin — Refundly.ai</h2>
        <p>{body}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">Message automatique envoyé par Refundly.ai</p>
    </body>
    </html>
    """

    success = sender.send_email(
        to_email=admin_email,
        subject=subject,
        html_body=html_body,
        text_body=body,
    )

    if success:
        logger.info(f"Admin notification sent: {subject}")
    else:
        logger.error(f"Failed to send admin notification: {subject}")

    return success
