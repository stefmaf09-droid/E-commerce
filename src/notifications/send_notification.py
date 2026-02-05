"""
send_notification_email Function - Integration with NotificationManager.

This module provides the bridge between NotificationManager and EmailSender,
adding template rendering capabilities.
"""

import os
import logging
from typing import Dict, Any

# Import existing EmailSender
from email_service.email_sender import EmailSender

logger = logging.getLogger(__name__)


def send_notification_email(
    to_email: str,
    event_type: str,
    context: Dict[str, Any]
) -> bool:
    """
    Send a notification email using templates.
    
    Args:
        to_email: Recipient email
        event_type: Type of notification (claim_created, etc.)
        context: Template variables
        
    Returns:
        True if sent successfully
    """
    try:
        # Load template
        template_html = _load_template(event_type)
        if not template_html:
            logger.warning(f"Template not found for {event_type}, using fallback")
            template_html = _get_fallback_template(event_type)
        
        # Render template with context
        email_body = _render_template(template_html, context)
        
        # Generate subject
        subject = _get_subject(event_type, context)
        
        # Send email using existing EmailSender
        sender = EmailSender()
        return sender.send_email(to_email, subject, email_body)
        
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
        return False


def _load_template(event_type: str) -> str:
    """Load email template from templates directory."""
    template_dir = os.path.join(
        os.path.dirname(__file__),
        'templates'
    )
    template_path = os.path.join(template_dir, f"{event_type}.html")
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    return ""


def _render_template(template: str, context: Dict[str, Any]) -> str:
    """
    Simple template rendering (replace {{variable}} with values).
    """
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    
    # Add common URLs
    result = result.replace("{{dashboard_url}}", "https://refundly-app.streamlit.app")
    result = result.replace("{{settings_url}}", "https://refundly-app.streamlit.app?page=Settings")
    
    return result


def _get_subject(event_type: str, context: Dict[str, Any]) -> str:
    """Generate email subject."""
    subjects = {
        'claim_created': f"✅ Nouveau litige {context.get('claim_ref', 'créé')}",
        'claim_updated': f"🔄 Mise à jour - {context.get('claim_ref', 'Litige')}",
        'claim_accepted': f"🎉 Litige accepté - {context.get('claim_ref', '')}",
        'payment_received': f"💰 Remboursement reçu - {context.get('client_amount', '')}€",
        'deadline_warning': f"⚠️ Action requise - {context.get('claim_ref', 'Litige')}"
    }
    return subjects.get(event_type, "Notification Refundly")


def _get_fallback_template(event_type: str) -> str:
    """Generate fallback template if file doesn't exist."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; }}
            .footer {{ background: #333; color: #fff; padding: 20px; text-align: center; 
                      border-radius: 0 0 10px 10px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📬 Notification Refundly</h1>
            </div>
            <div class="content">
                <p>Bonjour,</p>
                <p>Vous avez reçu une notification concernant vos litiges.</p>
                <p><strong>Type:</strong> {event_type}</p>
                <p>Connectez-vous à votre <a href="{{{{dashboard_url}}}}">tableau de bord</a> pour plus de détails.</p>
                <p>Cordialement,<br><strong>L'équipe Refundly</strong></p>
            </div>
            <div class="footer">
                <p>© 2026 Refundly.ai - Tous droits réservés</p>
                <p>Vous pouvez gérer vos préférences de notifications <a href="{{{{settings_url}}}}" style="color: #10b981;">ici</a>.</p>
            </div>
        </div>
    </body>
    </html>
    """
