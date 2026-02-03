
import logging
import requests
from typing import List, Dict, Any, Optional
from src.integrations.helpdesk_base import HelpdeskConnector

logger = logging.getLogger(__name__)

class GorgiasConnector(HelpdeskConnector):
    """Connecteur spécifique pour l'API Gorgias."""
    
    def __init__(self, api_key: str, domain: str, email: str):
        """
        Args:
            api_key: Password API Gorgias
            domain: Sous-domaine Gorgias (ex: 'maboutique')
            email: Email utilisateur Gorgias
        """
        super().__init__(api_key, domain)
        self.email = email
        self.base_url = f"https://{domain}.gorgias.com/api"
        self.auth = (email, api_key)

    def get_tickets(self, status: str = "open", limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les tickets Gorgias."""
        try:
            url = f"{self.base_url}/tickets"
            params = {"order_by": "created_datetime:desc", "limit": limit}
            response = requests.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Gorgias get_tickets error: {e}")
            return []

    def get_ticket_messages(self, ticket_id: int) -> List[Dict[str, Any]]:
        """Récupère les messages (notes et emails) d'un ticket."""
        try:
            url = f"{self.base_url}/tickets/{ticket_id}/messages"
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Gorgias get_ticket_messages error: {e}")
            return []

    def get_ticket_attachments(self, ticket_id: int) -> List[Dict[str, Any]]:
        """Extrait toutes les pièces jointes d'un ticket."""
        messages = self.get_ticket_messages(ticket_id)
        attachments = []
        for msg in messages:
            msg_attachments = msg.get('attachments', [])
            for att in msg_attachments:
                # Filtrer images
                if att.get('content_type', '').startswith('image/'):
                    attachments.append({
                        'id': att.get('id'),
                        'name': att.get('name'),
                        'url': att.get('url'),
                        'message_id': msg.get('id')
                    })
        return attachments

    def auto_detect_dispute(self, ticket: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyse un ticket complet et retourne une détection si positive.
        """
        subject = ticket.get('subject', '')
        # Concaténer les messages pour avoir plus de contexte
        # (Dans une vraie implémentation, on prendrait les messages récents)
        preview = ticket.get('excerpt', '')
        
        full_text = f"{subject} {preview}"
        dispute_type = self.analyze_ticket_for_dispute(full_text)
        
        if dispute_type:
            # Essayer d'extraire un numéro de commande ou tracking
            import re
            order_match = re.search(r'#(?:[A-Z0-9-]{4,})|(?:\b\d{4,8}\b)', full_text)
            order_id = order_match.group(0) if order_match else "Inconnu"
            
            return {
                'ticket_id': ticket['id'],
                'dispute_type': dispute_type,
                'order_id': order_id,
                'customer_email': ticket.get('customer', {}).get('email'),
                'confidence': 0.8 # Heuristique simple
            }
        return None
