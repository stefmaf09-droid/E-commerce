
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class HelpdeskConnector(ABC):
    """Classe de base pour les intégrations Helpdesk (Gorgias, Zendesk, etc.)."""
    
    def __init__(self, api_key: str, domain: str, **kwargs):
        self.api_key = api_key
        self.domain = domain
        self.kwargs = kwargs

    @abstractmethod
    def get_tickets(self, status: str = "open", limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les tickets récents."""
        pass

    @abstractmethod
    def get_ticket_messages(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Récupère les messages d'un ticket."""
        pass

    @abstractmethod
    def get_ticket_attachments(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Récupère les pièces jointes d'un ticket (photos du client)."""
        pass

    def analyze_ticket_for_dispute(self, ticket_text: str) -> Optional[str]:
        """
        Analyse simple pour détecter si le ticket concerne un litige.
        Retourne le type de litige (damage, lost, late) ou None.
        """
        keywords = {
            'damage': ['cassé', 'endommagé', 'abîmé', 'reçu ouvert', 'broken', 'damaged'],
            'lost': ['pas reçu', 'perdu', 'jamais arrivé', 'not received', 'lost', 'missing'],
            'late': ['retard', 'trop long', 'late', 'delay']
        }
        
        text_lower = ticket_text.lower()
        for dispute_type, words in keywords.items():
            if any(word in text_lower for word in words):
                return dispute_type
        return None
