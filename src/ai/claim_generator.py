"""
Claim Generator - Generate legally valid claims automatically.

Uses templates and LLM to create professional, legally sound claims
for different dispute types.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ClaimGenerator:
    """Generate legally valid claims for delivery disputes."""
    
    # Legal templates for different dispute types
    TEMPLATES = {
        'retard_livraison': """Objet : Réclamation pour retard de livraison - Colis {tracking_number}

Madame, Monsieur,

Je me permets de vous contacter concernant le colis référencé {tracking_number}, expédié le {ship_date}.

Selon vos conditions générales de vente et l'engagement contractuel de livraison, le colis devait être livré sous {guaranteed_days} jours ouvrés, soit au plus tard le {expected_date}.

Or, à ce jour ({current_date}), soit {delay_days} jours après la date garantie, le colis n'a toujours pas été livré à destination.

Ce retard de livraison me cause un préjudice commercial direct estimé à {claim_amount}€, correspondant à :
- Frais de port : {shipping_cost}€
- Indemnisation forfaitaire pour préjudice : {compensation}€

Conformément à :
- L'article L216-1 du Code de la consommation relatif aux obligations contractuelles
- Vos conditions générales article {cgv_article}
- La jurisprudence en matière de transport (Cass. Com., 22 oct. 1996)

Je sollicite le remboursement intégral de la somme de {total_claim}€.

Pièces jointes :
- Preuve d'expédition et contrat de transport
- Historique de suivi démontrant le retard
- Facture justificatif du montant réclamé

Dans l'attente de votre retour sous un délai de 8 jours ouvrés, conformément à l'article L.216-2 du Code de la consommation.

Cordialement,
{client_name}
{client_email}
        """,
        
        'colis_perdu': """Objet : Réclamation pour perte de colis - {tracking_number}

Madame, Monsieur,

Je vous contacte au sujet du colis {tracking_number} expédié le {ship_date}.

D'après le suivi en ligne, le colis est indiqué comme "en transit" depuis le {last_scan_date}, soit {missing_days} jours sans aucune mise à jour.

Malgré mes relances auprès de votre service client (références : {support_tickets}), aucune information sur la localisation du colis ne m'a été communiquée.

Je considère donc ce colis comme définitivement perdu.

Le préjudice subi s'élève à {total_claim}€, détaillé comme suit :
- Valeur du colis (marchandise + frais d'envoi) : {order_value}€
- Frais de port : {shipping_cost}€
- Frais de réexpédition urgente au client final : {reshipment_cost}€

Conformément à :
- L'article L133-3 du Code de commerce (responsabilité du transporteur)
- Vos conditions générales de vente article {cgv_article}
- Convention de Montréal (si applicable)

Je vous demande le remboursement intégral de {total_claim}€ dans un délai de 15 jours.

Passé ce délai, je me verrai contraint de :
1. Saisir le médiateur de la consommation
2. Engager une procédure judiciaire
3. Signaler cette perte auprès de l'Autorité de régulation des transports

Pièces jointes :
- Récépissé d'expédition
- Historique complet du suivi
- Échanges avec votre service client
- Facture et preuve de valeur

Cordialement,
{client_name}
{client_email}
        """,
        
        'pod_invalide': """Objet : Contestation de la preuve de livraison (POD) - {tracking_number}

Madame, Monsieur,

Le colis {tracking_number} est indiqué comme "livré" le {delivery_date} à {delivery_time}.

Cependant, ni moi ni le destinataire ({recipient_name}) n'avons réceptionné ce colis.

Après analyse approfondie de la preuve de livraison (POD) que vous avez fournie, plusieurs anomalies majeures sont constatées :

{anomalies_list}

Ces éléments remettent gravement en cause la validité de cette prétendue livraison et constituent une violation de vos obligations contractuelles (CGV article {cgv_article}) et des dispositions de l'article L133-1 du Code de commerce.

Une signature illisible ou l'absence de photo probante du colis ne saurait constituer une preuve valable de livraison conforme.

En conséquence, je demande :

1. Une enquête approfondie sur cette prétendue livraison
2. La localisation réelle du colis
3. À défaut, le remboursement intégral comprenant :
   - Valeur du colis : {order_value}€
   - Frais de port : {shipping_cost}€
   - Dommages et intérêts pour préjudice commercial : {damages}€
   
**Montant total réclamé : {total_claim}€**

Pièces jointes :
{pieces_jointes_list}

Je vous laisse un délai de 10 jours pour :
- Produire une POD valable ET
- Localiser le colis

À défaut, je considérerai le colis comme perdu et exigerai le remboursement immédiat.

Cordialement,
{client_name}
{client_email}
        """,
        
        'colis_endommage': """Objet : Réclamation pour colis endommagé - {tracking_number}

Madame, Monsieur,

J'accuse réception du colis {tracking_number} livré le {delivery_date}.

Malheureusement, le colis est arrivé dans un état de détérioration avancé, rendant la marchandise inutilisable.

**Dommages constatés :**
{damage_description}

Des photos ont été prises immédiatement à la réception et sont jointes à ce courrier.

Conformément à l'article L133-3 du Code de commerce, le transporteur est présumé responsable des dommages survenus pendant le transport, sauf preuve contraire de sa part.

Le préjudice subi s'élève à {total_claim}€ :
- Valeur de la marchandise endommagée : {order_value}€
- Frais de port : {shipping_cost}€
- Frais de remplacement urgent : {replacement_cost}€

Je sollicite donc le remboursement intégral de cette somme sous 15 jours.

Pièces jointes :
- Photos du colis à réception (emballage + contenu)
- Facture d'achat de la marchandise
- Rapport de constat (si huissier)
- Historique de suivi

En l'absence de réponse satisfaisante, je me réserve le droit de saisir votre compagnie d'assurance et d'engager une procédure contentieuse.

Cordialement,
{client_name}
{client_email}
        """
    }
    
    def __init__(self):
        """Initialize Claim Generator."""
        logger.info("ClaimGenerator initialized with legal templates")
    
    def generate(
        self, 
        dispute: Dict,
        pod_analysis: Optional[Dict] = None
    ) -> str:
        """
        Generate a legally valid claim.
        
        Args:
            dispute: Dispute data dictionary
            pod_analysis: Optional POD analysis results
            
        Returns:
            Generated claim text
        """
        dispute_type = dispute.get('dispute_type', 'retard_livraison')
        
        logger.info(f"Generating claim for dispute type: {dispute_type}")
        
        # Select appropriate template
        template = self.TEMPLATES.get(dispute_type, self.TEMPLATES['retard_livraison'])
        
        # Prepare variables
        variables = self._prepare_variables(dispute, pod_analysis)
        
        # Fill template
        try:
            claim_text = template.format(**variables)
            logger.info(f"Claim generated ({len(claim_text)} chars)")
            return claim_text
        except KeyError as e:
            logger.error(f"Missing variable in template: {e}")
            # Return template with placeholder for missing vars
            return template
    
    def _prepare_variables(
        self, 
        dispute: Dict,
        pod_analysis: Optional[Dict]
    ) -> Dict:
        """Prepare variables for template filling."""
        
        # Base variables
        tracking_number = dispute.get('tracking_number', 'N/A')
        order_date = dispute.get('order_date', datetime.now())
        
        if isinstance(order_date, str):
            try:
                order_date = datetime.fromisoformat(order_date)
            except:
                order_date = datetime.now()
        
        # Calculate dates
        ship_date = order_date.strftime('%d/%m/%Y')
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        guaranteed_days = dispute.get('guaranteed_delivery_days', 3)
        expected_date = (order_date + timedelta(days=guaranteed_days)).strftime('%d/%m/%Y')
        
        delay_days = max((datetime.now() - order_date).days - guaranteed_days, 0)
        
        # Amounts
        order_value = float(dispute.get('order_value', 0))
        shipping_cost = float(dispute.get('shipping_cost', 0))
        total_recoverable = float(dispute.get('total_recoverable', shipping_cost + 20))
        
        compensation = max(total_recoverable - shipping_cost, 0)
        
        # POD analysis variables
        anomalies_list = ''
        if pod_analysis and pod_analysis.get('anomalies'):
            anomalies= pod_analysis['anomalies']
            anomalies_list = '\n'.join(f"- {a}" for a in anomalies)
        else:
            anomalies_list = "- Aucune preuve de livraison valide fournie"
        
        # Build variables dict
        variables = {
            'tracking_number': tracking_number,
            'ship_date': ship_date,
            'current_date': current_date,
            'expected_date': expected_date,
            'guaranteed_days': guaranteed_days,
            'delay_days': delay_days,
            
            'order_value': f"{order_value:.2f}",
            'shipping_cost': f"{shipping_cost:.2f}",
            'claim_amount': f"{total_recoverable:.2f}",
            'compensation': f"{compensation:.2f}",
            'total_claim': f"{total_recoverable:.2f}",
            
            'client_name': dispute.get('client_name', 'Client'),
            'client_email': dispute.get('client_email', ''),
            
            'recipient_name': dispute.get('recipient_name', 'Destinataire'),
            'delivery_date': dispute.get('delivery_date', 'N/A'),
            'delivery_time': dispute.get('delivery_time', 'N/A'),
            
            'anomalies_list': anomalies_list,
            
            'cgv_article': dispute.get('cgv_article', '5.2'),
            
            'last_scan_date': dispute.get('last_scan_date', ship_date),
            'missing_days': delay_days,
            'support_tickets': dispute.get('support_tickets', 'N/A'),
            'reshipment_cost': f"{dispute.get('reshipment_cost', 0):.2f}",
            
            'damage_description': dispute.get('damage_description', 'Emballage déchiré, contenu endommagé'),
            'replacement_cost': f"{dispute.get('replacement_cost', 0):.2f}",
            'damages': f"{dispute.get('damages', 20):.2f}",
            'pieces_jointes_list': "- Preuve d'expédition\n- Photos du colis\n- Facture d'achat"
        }
        
        return variables
    
    def save_claim(self, claim_text: str, output_path: str):
        """
        Save generated claim to file.
        
        Args:
            claim_text: Generated claim text
            output_path: Path to save file
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(claim_text)
        
        logger.info(f"Claim saved to {output_path}")


# Example usage
if __name__ == "__main__":
    generator = ClaimGenerator()
    
    # Example dispute
    dispute = {
        'dispute_type': 'pod_invalide',
        'tracking_number': 'FR123456789',
        'order_date': '2024-01-10',
        'delivery_date': '2024-01-15',
        'order_value': 150.00,
        'shipping_cost': 12.50,
        'total_recoverable': 182.50,
        'client_name': 'Jean Dupont',
        'client_email': 'jean.dupont@example.com',
        'recipient_name': 'Marie Martin'
    }
    
    # Example POD analysis
    pod_analysis = {
        'anomalies': [
            'Signature totalement illisible (simple gribouillis)',
            'Aucune photo du colis fournie',
            'Timestamp incohérent : livraison indiquée à 23h45 (suspect)',
            'Localisation GPS absente du document'
        ]
    }
    
    print("="*70)
    print("CLAIM GENERATOR - Demo")
    print("="*70)
    
    claim = generator.generate(dispute, pod_analysis)
    
    print("\n" + claim)
    print("\n" + "="*70)
    print(f"✅ Claim generated ({len(claim)} characters)")
