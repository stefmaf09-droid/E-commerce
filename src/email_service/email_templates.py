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
DASHBOARD_URL = os.getenv('DASHBOARD_URL', 'https://e-commerce-c9ph46yfkru4n6hjart2rb.streamlit.app')


def get_base_template() -> str:
    """Template HTML de base pour tous les emails."""
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notification Refundly.AI</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            {header_style}
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
            background: #f9fafb;
            padding: 30px;
        }}
        .info-box {{
            background: #ffffff;
            border-left: 4px solid {accent_color};
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .success-box {{
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            text-align: center;
        }}
        .warning-box {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .update-box {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
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
            padding: 8px 0;
            font-weight: 600;
            color: #666;
        }}
        .stat-value {{
            display: table-cell;
            padding: 8px 0;
            text-align: right;
            color: #333;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background: {accent_color};
            color: white !important;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
        }}
        .footer {{
            background: #333;
            color: #fff;
            padding: 20px;
            text-align: center;
            font-size: 12px;
        }}
        .footer a {{
            color: {accent_color};
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""


def template_disputes_detected(client_email: str, client_name: str, disputes_count: int, 
                               total_amount: float, disputes_summary: List[Dict]) -> str:
    """
    Template: Nouveaux litiges détectés.
    """
    
    top_disputes = disputes_summary[:5]
    
    disputes_html = ""
    for dispute in top_disputes:
        disputes_html += f"""
        <div class="info-box">
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
            
            <div class="success-box">
                <h2 style="margin: 0; font-size: 28px; color: #10b981;">{total_amount:.2f}€</h2>
                <p style="margin: 10px 0 0 0;">Montant Total Récupérable</p>
            </div>
            
            <h3>🔍 Aperçu des litiges:</h3>
            
            {disputes_html}
            
            {more_text}
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{DASHBOARD_URL}?token={client_email}&page=Dashboard" class="button">
                    📊 Voir Mon Dashboard
                </a>
            </p>
            
            <p><strong>⚡ Action recommandée:</strong></p>
            <p>Connectez-vous à votre dashboard pour soumettre automatiquement vos réclamations.</p>
            <p>Cordialement,<br>
                <strong>L'équipe Refundly.AI</strong>
            </p>
        </div>
        <div class="footer">
            <p>© 2026 Refundly.ai - Tous droits réservés</p>
            <p>Vous recevez cet email car de nouveaux litiges ont été détectés sur votre compte.</p>
        </div>
    """
    
    base = get_base_template()
    return base.format(
        content=content, 
        header_style="background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);",
        accent_color="#ef4444"
    )


def template_claim_submitted(client_email: str, client_name: str, claim_reference: str,
                             carrier: str, amount_requested: float,
                             order_id: str, submission_method: str,
                             dispute_type: str = "N/A") -> str:
    """
    Template: Réclamation soumise.
    """
    
    content = f"""
        <div class="header">
            <h1>✅ Nouveau litige créé avec succès !</h1>
        </div>
        <div class="content">
            <p>Bonjour {client_name},</p>
            
            <p>Votre litige pour la commande <strong>{order_id}</strong> a été <strong>créé et soumis automatiquement</strong> au transporteur.</p>
            
            <div class="info-box">
                <h3 style="margin-top: 0;">📋 Détails de votre litige</h3>
                <p><strong>Référence :</strong> {claim_reference}</p>
                <p><strong>Transporteur :</strong> {carrier.upper()}</p>
                <p><strong>Montant réclamé :</strong> {amount_requested:.2f}€</p>
                <p><strong>Type :</strong> {dispute_type}</p>
            </div>
            
            <p>Le transporteur dispose d'un délai légal pour répondre à votre réclamation.</p>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{DASHBOARD_URL}?token={client_email}&page=Mes%20Litiges" class="button">Voir le détail du litige</a>
            </p>
            
            <p><strong>💡 Prochaines étapes :</strong></p>
            <ol>
                <li>Le transporteur examine votre dossier</li>
                <li>Vous recevrez une notification en cas de mise à jour</li>
                <li>Si accepté, vous recevrez 80% du montant récupéré</li>
            </ol>
            
            <p>Cordialement,<br>
                <strong>L'équipe Refundly.AI</strong>
            </p>
        </div>
        <div class="footer">
            <p>© 2026 Refundly.ai - Tous droits réservés</p>
            <p>Vous recevez cet email suite à la soumission d'une réclamation pour le compte #{order_id}.</p>
        </div>
    """
    
    base = get_base_template()
    return base.format(
        content=content, 
        header_style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);",
        accent_color="#10b981"
    )


def template_claim_accepted(client_email: str, client_name: str, claim_reference: str,
                            carrier: str, accepted_amount: float,
                            client_share: float, platform_fee: float) -> str:
    """
    Template: Réclamation acceptée.
    """
    
    content = f"""
        <div class="header">
            <h1>🎉 Excellente nouvelle !</h1>
        </div>
        <div class="content">
            <p>Bonjour {client_name},</p>
            
            <p>Nous avons le plaisir de vous informer que <strong>{carrier.upper()}</strong> a <strong>accepté votre réclamation</strong> !</p>
            
            <div class="success-box">
                <h2 style="margin: 0; font-size: 28px; color: #10b981;">{accepted_amount:.2f}€</h2>
                <p style="margin: 10px 0 0 0;">Montant Total Accordé</p>
            </div>
            
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-label">📋 Référence:</div>
                    <div class="stat-value"><strong>{claim_reference}</strong></div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">🎁 Votre part (80%):</div>
                    <div class="stat-value"><strong style="color: #10b981;">{client_share:.2f}€</strong></div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">🔧 Frais Refundly (20%):</div>
                    <div class="stat-value">{platform_fee:.2f}€</div>
                </div>
            </div>
            
            <p>Le paiement est en cours de traitement. Vous recevrez une notification dès que le virement sera effectué sur votre compte bancaire enregistré.</p>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{DASHBOARD_URL}?token={client_email}&page=Gestion" class="button">Voir les détails du paiement</a>
            </p>
            
            <p>Félicitations ! 🎊</p>
            
            <p>Cordialement,<br>
                <strong>L'équipe Refundly.AI</strong>
            </p>
        </div>
        <div class="footer">
            <p>© 2026 Refundly.ai - Tous droits réservés</p>
            <p>Félicitations pour cette réclamation réussie !</p>
        </div>
    """
    
    base = get_base_template()
    return base.format(
        content=content,
        header_style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);",
        accent_color="#10b981"
    )


def template_claim_rejected(client_email: str, client_name: str, claim_reference: str,
                           carrier: str, rejection_reason: str) -> str:
    """
    Template: Réclamation refusée.
    """
    
    content = f"""
        <div class="header">
            <h1>🔄 Mise à jour sur votre litige</h1>
        </div>
        <div class="content">
            <p>Bonjour {client_name},</p>
            
            <p>Le transporteur <strong>{carrier.upper()}</strong> a répondu à votre litige et a <strong>refusé</strong> la réclamation.</p>
            
            <div class="update-box">
                <h3 style="margin-top: 0; color: #1e3a8a;">📬 Nouvelle réponse</h3>
                <p><strong>Référence :</strong> {claim_reference}</p>
                <p><strong>Nouveau statut :</strong> Refusé</p>
                <p><strong>Raison indiquée :</strong><br>{rejection_reason or 'Aucune raison spécifique n a été fournie.'}</p>
            </div>
            
            <p><strong>Que faire maintenant ?</strong></p>
            <ul>
                <li><strong>Faire appel:</strong> Vous pouvez contester cette décision auprès du transporteur.</li>
                <li><strong>Fournir plus de preuves:</strong> Ajoutez des documents supplémentaires si possible.</li>
                <li><strong>Support:</strong> Notre équipe peut vous aider à analyser le refus.</li>
            </ul>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{DASHBOARD_URL}?token={client_email}&page=Mes%20Litiges" class="button">Consulter la réponse complète</a>
            </p>
            
            <p>Connectez-vous à votre tableau de bord pour plus de détails et voir les options d'appel.</p>
            
            <p>Cordialement,<br>
                <strong>L'équipe Refundly.AI</strong>
            </p>
        </div>
        <div class="footer">
            <p>© 2026 Refundly.ai - Tous droits réservés</p>
            <p>Ne vous découragez pas, la procédure d'appel peut inverser la décision !</p>
        </div>
    """
    
    base = get_base_template()
    return base.format(
        content=content,
        header_style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);",
        accent_color="#3b82f6"
    )
