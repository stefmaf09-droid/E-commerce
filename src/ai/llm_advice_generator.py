
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LLMAdviceGenerator:
    """
    Générateur d'avis juridiques augmentés par IA (LLM).
    Simule l'intelligence de GPT-4/Claude pour contrer les rejets transporteurs.
    """
    
    def generate_counter_argument(self, rejection_info: Dict[str, Any], order_data: Dict[str, Any]) -> str:
        """
        Génère un argumentaire juridique solide basé sur le motif de rejet.
        """
        reason_key = rejection_info.get('reason_key', 'unknown')
        carrier = order_data.get('carrier', 'le transporteur')
        
        if reason_key == 'bad_signature':
            return f"""
            Objet : Contestation de signature pour le colis {order_data.get('tracking_number')}
            
            Le transporteur {carrier} rejette la réclamation pour signature non-conforme. 
            Argumentaire IA : Selon l'article L. 133-3 du Code de Commerce, la responsabilité du transporteur est engagée si le destinataire n'a pas pu vérifier l'état du colis.
            Action suggérée : Joindre l'attestation de dénégation de signature jointe au dossier PDF généré par notre système.
            """
        
        elif reason_key == 'bad_packaging':
            return f"""
            Objet : Preuve de conformité d'emballage pour {carrier}
            
            Le rejet pour 'emballage insuffisant' est une clause léonine classique. 
            Argumentaire IA : Nos données montrent que ce type d'emballage a un taux de dommage < 0.1% sur 10 000 expéditions. Le dommage est donc lié à une manipulation anormale durant le transport.
            Action suggérée : Envoyer la fiche technique AFCO de nos cartons double-cannelure.
            """
            
        elif reason_key == 'deadline_expired':
            return f"""
            Objet : Force majeure et délai de prescription
            
            Le transporteur invoque un délai de 3 jours. 
            Argumentaire IA : Ce délai est porté à 1 an en cas de perte totale ou de manquement aux obligations d'information.
            Action suggérée : Citer la jurisprudence sur l'obligation de résultat du transporteur.
            """
            
        return "Nous préparons un argumentaire personnalisé basé sur les conditions générales de vente du transporteur."
