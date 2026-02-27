"""
Email Templates - HTML professional templates for all notification emails.

Templates disponibles:
- disputes_detected: Nouveaux litiges détectés (digest quotidien)
- claim_submitted: Réclamation soumise
- claim_accepted: Réclamation acceptée
- claim_rejected: Réclamation refusée
"""

import os
from typing import Dict, List

# URL du dashboard dans les emails — surchargeable via variable d'environnement
DASHBOARD_URL = os.getenv('DASHBOARD_URL', 'http://localhost:8503')


def get_base_template() -> str:
    """Template HTML de base pour tous les emails."""
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px;
        }}
        .highlight-box {{
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .stats {{
            display: table;
            width: 100%;
            margin: 20px 0;
        }}
        .stat-item {{
            display: table-row;
        }}
        .stat-label {{
            display: table-cell;
            padding: 8px;
            font-weight: 600;
            color: #666;
        }}
        .stat-value {{
            display: table-cell;
            padding: 8px;
            text-align: right;
            color: #333;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            text-align: center;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        .amount {{
            font-size: 28px;
            font-weight: 700;
            color: #10b981;
        }}
        .alert {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .success {{
            background-color: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        {content}
    </div>
</body>
</html>
"""


def template_disputes_detected(client_name: str, disputes_count: int, 
                               total_amount: float, disputes_summary: List[Dict]) -> str:
    """
    Template: Nouveaux litiges détectés.
    
    Args:
        client_name: Nom du client
        disputes_count: Nombre de litiges
        total_amount: Montant total récupérable
        disputes_summary: Liste des litiges (max 5 pour email)
    """
    
    # Limiter à 5 litiges dans l'email
    top_disputes = disputes_summary[:5]
    
    disputes_html = ""
    for dispute in top_disputes:
        disputes_html += f"""
        <div class="highlight-box">
            <strong>📦 Commande #{dispute.get('order_id')}</strong><br>
            Transporteur: {dispute.get('carrier', 'N/A')}<br>
            Type: {dispute.get('dispute_type', 'N/A')}<br>
            Montant: <strong>{dispute.get('total_recoverable', 0):.2f}€</strong>
        </div>
        """
    
    more_text = ""
    if disputes_count > 5:
        more_text = f"<p><em>+ {disputes_count - 5} autres litiges dans votre dashboard</em></p>"
    
    content = f"""
    <div class="header">
        <h1>🚨 Nouveaux Litiges Détectés</h1>
    </div>
    <div class="content">
        <p>Bonjour {client_name},</p>
        
        <p>Notre système a détecté <strong>{disputes_count} nouveau{'x' if disputes_count > 1 else ''} litige{'s' if disputes_count > 1 else ''}</strong> dans vos commandes récentes.</p>
        
        <div class="success">
            <p style="margin: 0; font-size: 16px;">
                💰 <strong>Montant Total Récupérable: {total_amount:.2f}€</strong>
            </p>
        </div>
        
        <h3>🔍 Aperçu des litiges:</h3>
        
        {disputes_html}
        
        {more_text}
        
        <p style="text-align: center;">
            <a href="{DASHBOARD_URL}" class="button">
                📊 Voir Mon Dashboard
            </a>
        </p>
        
        <div class="alert">
            <strong>⚡ Action recommandée:</strong><br>
            Connectez-vous à votre dashboard pour soumettre automatiquement vos réclamations.
        </div>
    </div>
    <div class="footer">
        <p>Refundly.ai - Recouvrement Automatique E-commerce</p>
        <p>Vous recevez cet email car de nouveaux litiges ont été détectés sur votre compte.</p>
    </div>
    """
    
    return get_base_template().format(content=content)


def template_claim_submitted(client_name: str, claim_reference: str,
                             carrier: str, amount_requested: float,
                             order_id: str, submission_method: str,
                             dispute_type: str = "N/A") -> str:
    """
    Template: Réclamation soumise.
    
    Args:
        client_name: Nom du client
        claim_reference: Référence de la réclamation
        carrier: Transporteur
        amount_requested: Montant demandé
        order_id: ID de la commande
        submission_method: Méthode de soumission (api/portal)
    """
    
    method_text = "automatiquement via API" if submission_method == "api" else "via le portail transporteur"
    
    content = f"""
    <div class="header">
        <h1>✅ Réclamation Soumise</h1>
    </div>
    <div class="content">
        <p>Bonjour {client_name},</p>
        
        <p>Excellente nouvelle ! Votre réclamation a été soumise avec succès {method_text}.</p>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-label">📋 Référence:</div>
                <div class="stat-value"><strong>{claim_reference}</strong></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">📦 Commande:</div>
                <div class="stat-value">{order_id}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">🚚 Transporteur:</div>
                <div class="stat-value">{carrier.upper()}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">💰 Montant demandé:</div>
                <div class="stat-value"><strong>{amount_requested:.2f}€</strong></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">📝 Type de litige:</div>
                <div class="stat-value">{dispute_type}</div>
            </div>
        </div>
        
        <div class="highlight-box">
            <strong>⏳ Délai de réponse:</strong><br>
            Le transporteur dispose généralement de 30 jours pour répondre à votre réclamation.
        </div>
        
        <h3>📅 Prochaines étapes:</h3>
        <ul>
            <li>Nous suivons votre réclamation automatiquement</li>
            <li>Vous serez notifié dès réception de la réponse</li>
            <li>En cas d'acceptation, votre paiement sera traité sous 3-5 jours</li>
        </ul>
        
        <p style="text-align: center;">
            <a href="{DASHBOARD_URL}" class="button">
                📊 Suivre Ma Réclamation
            </a>
        </p>
    </div>
    <div class="footer">
        <p>Refundly.ai - Recouvrement Automatique E-commerce</p>
        <p>Vous recevez cet email suite à la soumission d'une réclamation pour le compte #{order_id}.</p>
    </div>
    """
    
    return get_base_template().format(content=content)


def template_claim_accepted(client_name: str, claim_reference: str,
                            carrier: str, accepted_amount: float,
                            client_share: float, platform_fee: float) -> str:
    """
    Template: Réclamation acceptée.
    
    Args:
        client_name: Nom du client
        claim_reference: Référence de la réclamation
        carrier: Transporteur
        accepted_amount: Montant accepté
        client_share: Part client (80%)
        platform_fee: Frais plateforme (20%)
    """
    
    content = f"""
    <div class="header">
        <h1>🎉 Réclamation Acceptée !</h1>
    </div>
    <div class="content">
        <p>Bonjour {client_name},</p>
        
        <p><strong>Excellente nouvelle !</strong> Votre réclamation a été acceptée par {carrier.upper()}.</p>
        
        <div class="success">
            <p style="text-align: center; margin: 10px 0;">
                <span class="amount">{client_share:.2f}€</span><br>
                <span style="font-size: 14px; color: #666;">Votre part (80%)</span>
            </p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-label">📋 Référence:</div>
                <div class="stat-value">{claim_reference}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">💰 Montant total accepté:</div>
                <div class="stat-value">{accepted_amount:.2f}€</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">✅ Votre part (80%):</div>
                <div class="stat-value"><strong style="color: #10b981;">{client_share:.2f}€</strong></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">🔧 Frais de service (20%):</div>
                <div class="stat-value">{platform_fee:.2f}€</div>
            </div>
        </div>
        
        <h3>💸 Paiement:</h3>
        <div class="highlight-box">
            Votre paiement sera traité sous <strong>3-5 jours ouvrés</strong>.<br>
            Le virement sera effectué sur votre compte bancaire enregistré.
        </div>
        
        <p style="text-align: center;">
            <a href="{DASHBOARD_URL}" class="button">
                📊 Voir Détails du Paiement
            </a>
        </p>
        
        <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
            <strong>💡 Astuce:</strong> Continuez à utiliser notre plateforme pour récupérer automatiquement 
            vos fonds perdus à chaque nouveau litige !
        </p>
    </div>
    <div class="footer">
        <p>Refundly.ai - Recouvrement Automatique E-commerce</p>
        <p>Félicitations pour cette réclamation réussie ! 🎊</p>
    </div>
    """
    
    return get_base_template().format(content=content)


def template_claim_rejected(client_name: str, claim_reference: str,
                           carrier: str, rejection_reason: str) -> str:
    """
    Template: Réclamation refusée.
    
    Args:
        client_name: Nom du client
        claim_reference: Référence de la réclamation
        carrier: Transporteur
        rejection_reason: Raison du refus
    """
    
    content = f"""
    <div class="header">
        <h1>⚠️ Réclamation Refusée</h1>
    </div>
    <div class="content">
        <p>Bonjour {client_name},</p>
        
        <p>Malheureusement, votre réclamation <strong>{claim_reference}</strong> a été refusée par {carrier.upper()}.</p>
        
        <div class="alert">
            <strong>Raison du refus:</strong><br>
            {rejection_reason or 'Aucune raison spécifique fournie'}
        </div>
        
        <h3>🔄 Options disponibles:</h3>
        <ul>
            <li><strong>Faire appel:</strong> Vous pouvez contester cette décision auprès du transporteur</li>
            <li><strong>Fournir plus de preuves:</strong> Si possible, ajoutez des documents supplémentaires</li>
            <li><strong>Support:</strong> Notre équipe peut vous aider à analyser le refus</li>
        </ul>
        
        <div class="highlight-box">
            <strong>💡 Conseil:</strong><br>
            Dans certains cas, un appel avec des preuves supplémentaires peut renverser la décision.
            Contactez-nous si vous souhaitez de l'aide.
        </div>
        
        <p style="text-align: center;">
            <a href="{DASHBOARD_URL}" class="button">
                📊 Voir Détails
            </a>
        </p>
    </div>
    <div class="footer">
        <p>Refundly.ai - Recouvrement Automatique E-commerce</p>
        <p>Ne vous découragez pas, nous sommes là pour vous aider !</p>
    </div>
    """
    
    return get_base_template().format(content=content)
