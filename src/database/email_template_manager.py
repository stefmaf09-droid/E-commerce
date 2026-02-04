"""
Email Templates Manager - Gestion des templates d'emails personnalisables.

Permet aux clients de personnaliser le contenu des emails d'escalade
tout en gardant les variables dynamiques et l'automation.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class EmailTemplateManager:
    """Gestionnaire des templates d'emails personnalisés."""
    
    # Templates par défaut
    DEFAULT_TEMPLATES = {
        'status_request': {
            'FR': {
                'subject': 'Demande de mise à jour - {claim_reference}',
                'body': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="text-align: right; margin-bottom: 20px;">
        <p>{location}, le {date}</p>
    </div>
    <div style="margin-bottom: 30px;">
        <img src="cid:refundly_logo" alt="Refundly.ai" style="max-height: 80px;">
    </div>
    <h2>Demande de statut de réclamation</h2>
    <p>Madame, Monsieur,</p>
    <p>Nous sommes la société <strong>Refundly.ai</strong> et agissons pour le compte de notre client <strong>{company_name}</strong>.</p>
    <p>Nous vous contactons concernant la réclamation <strong>{claim_reference}</strong> 
    pour le colis <strong>{tracking_number}</strong> expédié via vos services.</p>
    <p><strong>Détails:</strong></p>
    <ul>
        <li>Référence: {claim_reference}</li>
        <li>Numéro de suivi: {tracking_number}</li>
        <li>Montant réclamé: {amount} {currency}</li>
        <li>Type: {dispute_type}</li>
    </ul>
    <p>Nous n'avons pas reçu de réponse concernant cette réclamation. 
    Merci de nous fournir une mise à jour dans les plus brefs délais.</p>
    <p>Cordialement,<br>L'équipe Refundly.ai pour {company_name}</p>
    
    <div style="margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 11px; color: #777;">
        <p><strong>Refundly.ai</strong> - SAS au capital de 10 000 € - SIRET 123 456 789 00012<br>
        25 Rue de Ponthieu, 75008 Paris - <a href="#" style="color: #777;">Conditions Générales</a></p>
        <p><em>Eco-responsabilité : N'imprimez cet email que si nécessaire.</em></p>
    </div>
</body>
</html>'''
            },
            'EN': {
                'subject': 'Status Update Request - {claim_reference}',
                'body': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="text-align: right; margin-bottom: 20px;">
        <p>{location}, {date}</p>
    </div>
    <h2>Claim Status Request</h2>
    <p>Dear Sir/Madam,</p>
    <p>We are contacting you regarding our claim <strong>{claim_reference}</strong> 
    for package <strong>{tracking_number}</strong> shipped via your services.</p>
    <p><strong>Details:</strong></p>
    <ul>
        <li>Reference: {claim_reference}</li>
        <li>Tracking number: {tracking_number}</li>
        <li>Amount claimed: {amount} {currency}</li>
        <li>Type: {dispute_type}</li>
    </ul>
    <p>We have not received a response regarding this claim. 
    Please provide an update at your earliest convenience.</p>
    <p>Best regards,<br>{company_name}</p>
</body>
</html>'''
            }
        },
        'warning': {
            'FR': {
                'subject': 'Avertissement - Réclamation {claim_reference}',
                'body': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="text-align: right; margin-bottom: 20px;">
        <p>{location}, le {date}</p>
    </div>
    <div style="margin-bottom: 30px;">
        <img src="cid:refundly_logo" alt="Refundly.ai" style="width: 250px; height: auto;">
    </div>
    <h2 style="color: #d9534f;">⚠️ Avertissement - Réclamation non traitée</h2>
    <p>Madame, Monsieur,</p>
    <p>Nous sommes la société <strong>Refundly.ai</strong> et agissons pour le compte de notre client <strong>{company_name}</strong>.</p>
    <p>Malgré notre précédente demande, nous n'avons toujours pas reçu de réponse 
    concernant la réclamation <strong>{claim_reference}</strong>.</p>
    <p><strong>Détails de la réclamation:</strong></p>
    <ul>
        <li>Référence: {claim_reference}</li>
        <li>Numéro de suivi: {tracking_number}</li>
        <li>Montant: {amount} {currency}</li>
        <li>Client final: {customer_name}</li>
        <li>Adresse de livraison: {delivery_address}</li>
    </ul>
    <p><strong style="color: #d9534f;">Sans réponse de votre part sous 7 jours, 
    nous serons contraints de procéder à une mise en demeure formelle.</strong></p>
    <p>Nous vous invitons à traiter cette réclamation dans les meilleurs délais.</p>
    <p>Cordialement,<br>L'équipe Refundly.ai pour {company_name}</p>

    <div style="margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 11px; color: #777;">
        <p><strong>Refundly.ai</strong> - SAS au capital de 10 000 € - SIRET 123 456 789 00012<br>
        25 Rue de Ponthieu, 75008 Paris - <a href="#" style="color: #777;">Conditions Générales</a></p>
        <p><em>Eco-responsabilité : N'imprimez cet email que si nécessaire.</em></p>
    </div>
</body>
</html>'''
            },
            'EN': {
                'subject': 'Warning - Claim {claim_reference}',
                'body': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="text-align: right; margin-bottom: 20px;">
        <p>{location}, {date}</p>
    </div>
    <h2 style="color: #d9534f;">⚠️ Warning - Unprocessed Claim</h2>
    <p>Dear Sir/Madam,</p>
    <p>Despite our previous request, we have still not received a response 
    regarding our claim <strong>{claim_reference}</strong>.</p>
    <p><strong>Claim details:</strong></p>
    <ul>
        <li>Reference: {claim_reference}</li>
        <li>Tracking number: {tracking_number}</li>
        <li>Amount: {amount} {currency}</li>
        <li>End customer: {customer_name}</li>
        <li>Delivery address: {delivery_address}</li>
    </ul>
    <p><strong style="color: #d9534f;">Without a response from you within 7 days, 
    we will be forced to proceed with a formal demand letter.</strong></p>
    <p>We kindly ask you to process this claim promptly.</p>
    <p>Best regards,<br>{company_name}</p>
</body>
</html>'''
            }
        },
        'formal_notice': {
            'FR': {
                'subject': '⚖️ MISE EN DEMEURE - {claim_reference}',
                'body': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="text-align: right; margin-bottom: 20px;">
        <p style="font-weight: bold;">{location}, le {date}</p>
    </div>
    <div style="margin-bottom: 30px;">
        <img src="cid:refundly_logo" alt="Refundly.ai" style="width: 250px; height: auto;">
    </div>
    <h2 style="color: #c9302c;">⚖️ MISE EN DEMEURE OFFICIELLE</h2>
    <p>Madame, Monsieur,</p>
    <p>Nous sommes la société <strong>Refundly.ai</strong> et agissons pour le compte de notre client <strong>{company_name}</strong>.</p>
    <p><strong>Référence:</strong> {claim_reference}<br>
    <strong>Numéro de suivi:</strong> {tracking_number}</p>
    
    <p>Par la présente, nous vous mettons formellement en demeure de traiter 
    la réclamation concernant le colis ci-dessus référencé.</p>
    
    <p><strong>Montant réclamé: {amount} {currency}</strong></p>
    
    <p>Conformément à l'<strong>article L. 133-3 du Code de commerce</strong>, 
    le transporteur est garant de la perte et des avaries des objets transportés. 
    Notre demande d'indemnisation étant restée sans réponse satisfaisante, 
    nous exigeons le règlement immédiat de ce litige.</p>
    
    <p>Vous trouverez ci-joint notre mise en demeure officielle avec tous les 
    détails et pièces justificatives.</p>
    
    <p><strong style="color: #c9302c;">Délai de réponse: 15 jours à compter de la réception de ce courrier.</strong></p>
    
    <p>À défaut de règlement dans ce délai, nous nous réserverons le droit 
    d'engager toute action judiciaire appropriée devant le Tribunal de Commerce compétent.</p>
    
    <p>Veuillez agréer, Madame, Monsieur, nos salutations distinguées.</p>
    <p>L'équipe Refundly.ai pour {company_name}</p>
    <p><small><em>Ce courrier a valeur de notification officielle.</em></small></p>

    <div style="margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 11px; color: #777;">
        <p><strong>Refundly.ai</strong> - SAS au capital de 10 000 € - SIRET 123 456 789 00012<br>
        25 Rue de Ponthieu, 75008 Paris - <a href="#" style="color: #777;">Conditions Générales</a></p>
        <p><em>Eco-responsabilité : N'imprimez cet email que si nécessaire.</em></p>
    </div>
</body>
</html>'''
            },
            'EN': {
                'subject': '⚖️ FORMAL DEMAND - {claim_reference}',
                'body': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="text-align: right; margin-bottom: 20px;">
        <p style="font-weight: bold;">{location}, {date}</p>
    </div>
    <h2 style="color: #c9302c;">⚖️ OFFICIAL FORMAL DEMAND</h2>
    <p>Dear Sir/Madam,</p>
    <p><strong>Reference:</strong> {claim_reference}<br>
    <strong>Tracking number:</strong> {tracking_number}</p>
    <p>We hereby formally demand that you process our claim regarding 
    the above-referenced package.</p>
    <p><strong>Amount claimed: {amount} {currency}</strong></p>
    <p>Please find attached our official demand letter with all 
    details and supporting documents.</p>
    <p><strong style="color: #c9302c;">Response deadline: 15 days from receipt of this letter.</strong></p>
    <p>Failing settlement within this period, we reserve the right 
    to take any appropriate legal action.</p>
    <p>Yours faithfully,<br>{company_name}</p>
</body>
</html>'''
            }
        }
    }
    
    # Variables disponibles pour les templates
    AVAILABLE_VARIABLES = [
        'claim_reference', 'carrier', 'tracking_number', 'amount', 'currency',
        'customer_name', 'delivery_address', 'dispute_type', 'company_name',
        'order_id', 'submission_date', 'date', 'location'
    ]
    
    def __init__(self, db_path: str = "database/recours_ecommerce.db"):
        """Initialise le gestionnaire de templates."""
        self.db_path = db_path
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Crée la table email_templates si elle n'existe pas."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    template_type TEXT NOT NULL,
                    language TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body_html TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(client_id, template_type, language)
                )
            """)
            conn.commit()
            logger.info("Table email_templates created or already exists")
        except Exception as e:
            logger.error(f"Error creating email_templates table: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_template(self, template_type: str, language: str = 'FR', 
                    client_id: Optional[int] = None) -> Dict[str, str]:
        """
        Récupère un template (personnalisé ou par défaut).
        
        Args:
            template_type: Type de template ('status_request', 'warning', 'formal_notice')
            language: Langue du template ('FR', 'EN', etc.)
            client_id: ID du client (optionnel)
        
        Returns:
            Dict avec 'subject' et 'body_html'
        """
        # Essayer de récupérer le template personnalisé
        if client_id:
            custom_template = self._get_custom_template(client_id, template_type, language)
            if custom_template:
                return custom_template
        
        # Fallback sur le template par défaut
        return self._get_default_template(template_type, language)
    
    def _get_custom_template(self, client_id: int, template_type: str, 
                            language: str) -> Optional[Dict[str, str]]:
        """Récupère un template personnalisé depuis la DB."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT subject, body_html
                FROM email_templates
                WHERE client_id = ? AND template_type = ? AND language = ?
            """, (client_id, template_type, language))
            
            row = cursor.fetchone()
            if row:
                return {'subject': row['subject'], 'body': row['body_html']}
            return None
        except Exception as e:
            logger.error(f"Error fetching custom template: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def _get_default_template(self, template_type: str, language: str) -> Dict[str, str]:
        """Récupère un template par défaut."""
        if template_type in self.DEFAULT_TEMPLATES:
            if language in self.DEFAULT_TEMPLATES[template_type]:
                return self.DEFAULT_TEMPLATES[template_type][language]
            # Fallback sur FR si langue non trouvée
            return self.DEFAULT_TEMPLATES[template_type].get('FR', {'subject': '', 'body': ''})
        return {'subject': '', 'body': ''}
    
    def save_template(self, client_id: int, template_type: str, language: str,
                     subject: str, body_html: str) -> bool:
        """
        Sauvegarde un template personnalisé.
        
        Args:
            client_id: ID du client
            template_type: Type de template
            language: Langue
            subject: Sujet de l'email
            body_html: Corps HTML de l'email
        
        Returns:
            True si succès
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO email_templates 
                (client_id, template_type, language, subject, body_html, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (client_id, template_type, language, subject, body_html, datetime.now()))
            conn.commit()
            logger.info(f"Template saved: client_id={client_id}, type={template_type}, lang={language}")
            return True
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def delete_template(self, client_id: int, template_type: str, language: str) -> bool:
        """Supprime un template personnalisé (reset to default)."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                DELETE FROM email_templates
                WHERE client_id = ? AND template_type = ? AND language = ?
            """, (client_id, template_type, language))
            conn.commit()
            logger.info(f"Template deleted: client_id={client_id}, type={template_type}, lang={language}")
            return True
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def render_template(self, template: Dict[str, str], claim_data: Dict[str, Any],
                       company_name: str = "Recours Ecommerce") -> Dict[str, str]:
        """
        Rend un template avec les données réelles.
        
        Args:
            template: Template avec subject et body
            claim_data: Données de la réclamation
            company_name: Nom de l'entreprise
        
        Returns:
            Template rendu avec subject et body
        """
        # Préparer les variables
        from datetime import datetime
        
        variables = {
            'claim_reference': claim_data.get('claim_reference', 'N/A'),
            'carrier': claim_data.get('carrier', 'N/A'),
            'tracking_number': claim_data.get('tracking_number', 'N/A'),
            'amount': f"{claim_data.get('amount_requested', 0):.2f}",
            'currency': claim_data.get('currency', 'EUR'),
            'customer_name': claim_data.get('customer_name', 'N/A'),
            'delivery_address': claim_data.get('delivery_address', 'N/A'),
            'dispute_type': claim_data.get('dispute_type', 'N/A'),
            'company_name': company_name,
            'order_id': claim_data.get('order_id', 'N/A'),
            'submission_date': claim_data.get('submitted_at', 'N/A'),
            'date': datetime.now().strftime('%d/%m/%Y'),
            'location': claim_data.get('location', 'Paris')
        }
        
        # Rendre le subject et le body
        subject = template['subject'].format(**variables)
        body = template['body'].format(**variables)
        
        return {'subject': subject, 'body': body}
    
    def get_all_templates(self, client_id: int) -> List[Dict[str, Any]]:
        """Récupère tous les templates d'un client."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT template_type, language, subject, body_html, created_at, updated_at
                FROM email_templates
                WHERE client_id = ?
                ORDER BY template_type, language
            """, (client_id,))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching all templates: {e}")
            return []
        finally:
            if conn:
                conn.close()
