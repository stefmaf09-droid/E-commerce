"""
Chatbot Tools - Fonctions exécutables par le chatbot via Function Calling.

Permet au chatbot de :
- Créer des réclamations
- Envoyer des relances
- Exporter des données
- Marquer des réclamations comme payées
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.database.database_manager import get_db_manager
from src.notifications.notification_manager import NotificationManager

logger = logging.getLogger(__name__)


class ChatbotTools:
    """
    Collection d'outils que le chatbot peut appeler pour effectuer des actions.
    """
    
    def __init__(self):
        self.db = get_db_manager()
        self.notif_manager = NotificationManager()
    
    def get_available_tools(self) -> list:
        """
        Retourne la liste des outils disponibles au format Gemini Function Calling.
        """
        return [
            {
                "name": "get_claim_details",
                "description": "Récupère les détails complets d'une réclamation spécifique",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "claim_reference": {
                            "type": "string",
                            "description": "Référence de la réclamation (ex: CLM-20260206-001)"
                        }
                    },
                    "required": ["claim_reference"]
                }
            },
            {
                "name": "list_pending_claims",
                "description": "Liste toutes les réclamations en attente d'un client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_email": {
                            "type": "string",
                            "description": "Email du client"
                        }
                    },
                    "required": ["client_email"]
                }
            },
            {
                "name": "create_claim",
                "description": "Crée une nouvelle réclamation pour un client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_email": {
                            "type": "string",
                            "description": "Email du client"
                        },
                        "order_id": {
                            "type": "string",
                            "description": "ID de la commande concernée"
                        },
                        "carrier": {
                            "type": "string",
                            "description": "Nom du transporteur (Colissimo, Chronopost, UPS, etc.)"
                        },
                        "dispute_type": {
                            "type": "string",
                            "description": "Type de litige: lost, damaged, late_delivery, invalid_pod"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Montant de la réclamation en euros"
                        },
                        "tracking_number": {
                            "type": "string",
                            "description": "Numéro de suivi du colis"
                        }
                    },
                    "required": ["client_email", "order_id", "carrier", "dispute_type", "amount"]
                }
            },
            {
                "name": "send_carrier_reminder",
                "description": "Envoie une relance au transporteur pour une réclamation sans réponse",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "claim_reference": {
                            "type": "string",
                            "description": "Référence de la réclamation"
                        }
                    },
                    "required": ["claim_reference"]
                }
            },
            {
                "name": "mark_claim_paid",
                "description": "Marque une réclamation comme payée après réception du paiement",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "claim_reference": {
                            "type": "string",
                            "description": "Référence de la réclamation"
                        },
                        "amount_received": {
                            "type": "number",
                            "description": "Montant reçu en euros"
                        }
                    },
                    "required": ["claim_reference", "amount_received"]
                }
            },
            {
                "name": "export_claims_csv",
                "description": "Exporte les réclamations d'un client au format CSV",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_email": {
                            "type": "string",
                            "description": "Email du client"
                        },
                        "status_filter": {
                            "type": "string",
                            "description": "Filtre optionnel sur le statut (pending, accepted, rejected, etc.)"
                        }
                    },
                    "required": ["client_email"]
                }
            },
            {
                "name": "get_tracking_status",
                "description": "Récupère les informations de suivi en temps réel d'un colis (Colissimo, UPS, DHL, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tracking_number": {
                            "type": "string",
                            "description": "Numéro de suivi du colis (ex: XS419416933FR)"
                        },
                        "carrier": {
                            "type": "string",
                            "description": "Nom optionnel du transporteur"
                        },
                        "client_email": {
                            "type": "string",
                            "description": "Email du client pour utiliser ses propres clés API"
                        }
                    },
                    "required": ["tracking_number"]

                }
            }
        ]
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute un outil et retourne le résultat.
        
        Args:
            tool_name: Nom de l'outil à exécuter
            parameters: Paramètres de l'outil
            
        Returns:
            Dict contenant 'success', 'message' et optionnellement 'data'
        """
        try:
            if tool_name == "get_claim_details":
                return self._get_claim_details(parameters["claim_reference"])
            
            elif tool_name == "list_pending_claims":
                return self._list_pending_claims(parameters["client_email"])
            
            elif tool_name == "create_claim":
                return self._create_claim(parameters)
            
            elif tool_name == "send_carrier_reminder":
                return self._send_carrier_reminder(parameters["claim_reference"])
            
            elif tool_name == "mark_claim_paid":
                return self._mark_claim_paid(
                    parameters["claim_reference"],
                    parameters["amount_received"]
                )
            
            elif tool_name == "export_claims_csv":
                return self._export_claims_csv(
                    parameters["client_email"],
                    parameters.get("status_filter")
                )
            
                return self._get_tracking_status(
                    parameters["tracking_number"],
                    parameters.get("carrier"),
                    parameters.get("client_email")
                )

            
            else:
                return {
                    "success": False,
                    "message": f"Outil '{tool_name}' non reconnu"
                }
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "message": f"Erreur lors de l'exécution: {str(e)}"
            }
    
    # ==================== Implémentations des outils ====================
    
    def _get_claim_details(self, claim_reference: str) -> Dict[str, Any]:
        """Récupère les détails d'une réclamation."""
        claim = self.db.get_claim(claim_reference=claim_reference)
        
        if not claim:
            return {
                "success": False,
                "message": f"Réclamation {claim_reference} introuvable"
            }
        
        return {
            "success": True,
            "message": "Réclamation trouvée",
            "data": claim
        }
    
    def _list_pending_claims(self, client_email: str) -> Dict[str, Any]:
        """Liste les réclamations en attente d'un client."""
        client = self.db.get_client(email=client_email)
        if not client:
            return {
                "success": False,
                "message": "Client introuvable"
            }
        
        claims = self.db.get_client_claims(client['id'], status='pending')
        
        return {
            "success": True,
            "message": f"{len(claims)} réclamation(s) en attente trouvée(s)",
            "data": claims
        }
    
    def _create_claim(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle réclamation."""
        # Récupérer le client
        client = self.db.get_client(email=params["client_email"])
        if not client:
            return {
                "success": False,
                "message": "Client introuvable"
            }
        
        # Générer la référence
        today = datetime.now()
        date_str = today.strftime("%Y%m%d")
        
        # Compter les claims du jour pour l'incrément
        existing_claims = self.db.get_client_claims(client['id'])
        today_claims = [c for c in existing_claims if c.get('created_at', '').startswith(today.strftime("%Y-%m-%d"))]
        increment = len(today_claims) + 1
        
        claim_reference = f"CLM-{date_str}-{increment:03d}"
        
        # Créer la réclamation
        claim = self.db.create_claim(
            claim_reference=claim_reference,
            client_id=client['id'],
            order_id=params["order_id"],
            carrier=params["carrier"],
            dispute_type=params["dispute_type"],
            amount_requested=params["amount"],
            tracking_number=params.get("tracking_number"),
            status='pending'
        )
        
        logger.info(f"Claim {claim_reference} created by chatbot for {params['client_email']}")
        
        return {
            "success": True,
            "message": f"Réclamation {claim_reference} créée avec succès",
            "data": {"claim_reference": claim_reference}
        }
    
    def _send_carrier_reminder(self, claim_reference: str) -> Dict[str, Any]:
        """Envoie une relance au transporteur."""
        claim = self.db.get_claim(claim_reference=claim_reference)
        
        if not claim:
            return {
                "success": False,
                "message": f"Réclamation {claim_reference} introuvable"
            }
        
        if claim['status'] not in ['submitted', 'under_review']:
            return {
                "success": False,
                "message": f"Impossible de relancer: statut actuel = {claim['status']}"
            }
        
        # Mettre à jour le follow-up level
        current_level = claim.get('follow_up_level', 0)
        self.db.update_claim(
            claim['id'],
            follow_up_level=current_level + 1,
            last_follow_up_at=datetime.now().isoformat()
        )
        
        logger.info(f"Reminder sent for claim {claim_reference} (level {current_level + 1})")
        
        return {
            "success": True,
            "message": f"Relance envoyée au transporteur {claim['carrier']} (niveau {current_level + 1})"
        }
    
    def _mark_claim_paid(self, claim_reference: str, amount_received: float) -> Dict[str, Any]:
        """Marque une réclamation comme payée."""
        claim = self.db.get_claim(claim_reference=claim_reference)
        
        if not claim:
            return {
                "success": False,
                "message": f"Réclamation {claim_reference} introuvable"
            }
        
        # Mettre à jour le statut
        self.db.update_claim(
            claim['id'],
            payment_status='paid',
            payment_date=datetime.now().isoformat()
        )
        
        logger.info(f"Claim {claim_reference} marked as paid: {amount_received} EUR")
        
        return {
            "success": True,
            "message": f"Réclamation {claim_reference} marquée comme payée ({amount_received} EUR)"
        }
    
    def _export_claims_csv(self, client_email: str, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Exporte les réclamations au format CSV."""
        client = self.db.get_client(email=client_email)
        if not client:
            return {
                "success": False,
                "message": "Client introuvable"
            }
        
        claims = self.db.get_client_claims(client['id'], status=status_filter)
        
        if not claims:
            return {
                "success": False,
                "message": "Aucune réclamation à exporter"
            }
        
        # Créer le CSV (simplifié pour l'exemple)
        import csv
        import io
        
        output = io.StringIO()
        fieldnames = ['claim_reference', 'carrier', 'dispute_type', 'amount_requested', 'status', 'created_at']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for claim in claims:
            writer.writerow({k: claim.get(k, '') for k in fieldnames})
        
        csv_content = output.getvalue()
        
        return {
            "success": True,
            "message": f"{len(claims)} réclamation(s) exportée(s)",
            "data": {"csv_content": csv_content, "count": len(claims)}
        }
    
    def _get_tracking_status(self, tracking_number: str, carrier_name: Optional[str] = None, client_email: Optional[str] = None) -> Dict[str, Any]:
        """Récupère l'état d'un colis via les connecteurs transporteurs."""
        from src.integrations.carrier_factory import CarrierFactory
        from src.config import Config
        from src.auth.credentials_manager import CredentialsManager

        
        tracking_number = tracking_number.strip().upper()
        
        # 1. Détecter le transporteur si non fourni
        if not carrier_name:
            # Logique de détection basée sur le format
            if tracking_number.startswith("XS") or tracking_number.startswith("8") or len(tracking_number) == 13:
                carrier_name = "Colissimo"
            elif tracking_number.startswith("1Z"):
                carrier_name = "UPS"
            elif len(tracking_number) == 12 or len(tracking_number) == 15:
                carrier_name = "FedEx"
            elif len(tracking_number) == 11 and tracking_number.isdigit():
                carrier_name = "GLS"
            elif (len(tracking_number) == 8 or len(tracking_number) == 10 or len(tracking_number) == 12) and tracking_number.isdigit():
                carrier_name = "Mondial Relay"
            else:
                carrier_name = "Colissimo" # Fallback par défaut
        
        try:
            # 2. Obtenir le connecteur avec toutes les clés dispo
            # Clés globales
            config = {
                'COLISSIMO_API_KEY': Config.get('COLISSIMO_API_KEY'),
                'UPS_CLIENT_ID': Config.get('UPS_CLIENT_ID'),
                'UPS_CLIENT_SECRET': Config.get('UPS_CLIENT_SECRET'),
                'FEDEX_CLIENT_ID': Config.get('FEDEX_CLIENT_ID'),
                'FEDEX_CLIENT_SECRET': Config.get('FEDEX_CLIENT_SECRET'),
                'FEDEX_USE_SANDBOX': Config.get('FEDEX_USE_SANDBOX', 'false'),
                'GLS_API_KEY': Config.get('GLS_API_KEY'),
                'DHL_API_KEY': Config.get('DHL_API_KEY'),
                'DHL_MERCHANT_ID': Config.get('DHL_MERCHANT_ID'),
                'MONDIAL_RELAY_ENSEIGNE': Config.get('MONDIAL_RELAY_ENSEIGNE'),
                'MONDIAL_RELAY_PASSWORD': Config.get('MONDIAL_RELAY_PASSWORD'),
                'DPD_DELIS_ID': Config.get('DPD_DELIS_ID'),
                'DPD_PASSWORD': Config.get('DPD_PASSWORD')
            }
            
            # Surcharge avec les clés du client si présentes
            if client_email:
                mgr = CredentialsManager()
                stores = mgr.get_all_stores(client_email)
                for store in stores:
                    carrier_apis = store.get('credentials', {}).get('carrier_apis', {})
                    if carrier_apis:
                        fedex = carrier_apis.get('fedex')
                        if fedex and fedex.get('client_id'):
                            config['FEDEX_CLIENT_ID'] = fedex['client_id']
                            config['FEDEX_CLIENT_SECRET'] = fedex['client_secret']
                        
                        dpd = carrier_apis.get('dpd')
                        if dpd and dpd.get('delis_id'):
                            config['DPD_DELIS_ID'] = dpd['delis_id']
                            config['DPD_PASSWORD'] = dpd['password']
                        break # On prend le premier store qui a des clés
            
            connector = CarrierFactory.get_connector(carrier_name, config)

            
            # 3. Récupérer les détails
            details = connector.get_tracking_details(tracking_number)
            
            return {
                "success": True,
                "message": f"Informations de suivi récupérées pour {tracking_number}",
                "data": details
            }
            
        except Exception as e:
            logger.error(f"Error fetching tracking for {tracking_number}: {e}")
            return {
                "success": False,
                "message": f"Impossible de récupérer le suivi pour {tracking_number}: {str(e)}"
            }
