"""
I18n Utility - Fonctions pour l'internationalisation (multi-devises et traductions).
"""

import streamlit as st
from streamlit.components.v1 import html

# Dictionnaire de symboles monétaires
CURRENCY_SYMBOLS = {
    'EUR': '€',
    'USD': '$',
    'GBP': '£',
    'CAD': 'C$',
    'AUD': 'A$',
    'JPY': '¥'
}

def get_browser_language():
    """
    Détecte la langue du navigateur de l'utilisateur.
    
    Returns:
        str: Code langue en majuscules ('FR', 'EN', 'DE', 'IT', 'ES')
    """
    # Try to get from session state first
    if 'browser_language' in st.session_state:
        return st.session_state.browser_language
    
    # Use JavaScript to get browser language
    language_js = """
    <script>
        const lang = navigator.language || navigator.userLanguage;
        const langCode = lang.substring(0, 2).toUpperCase();
        window.parent.postMessage({type: 'streamlit:setComponentValue', value: langCode}, '*');
    </script>
    """
    
    try:
        # Default to French if unable to detect
        detected_lang = 'FR'
        
        # Try to get from browser headers through Streamlit
        # Streamlit doesn't expose headers directly, so we'll use a simpler approach
        # Check query params if language is manually set
        query_params = st.query_params
        if 'lang' in query_params:
            detected_lang = query_params['lang'].upper()
        
        # Store in session state
        st.session_state.browser_language = detected_lang
        return detected_lang
    except:
        return 'FR'


def format_currency(amount: float, currency_code: str = 'EUR') -> str:
    """
    Formate un montant avec le symbole monétaire approprié.
    
    Args:
        amount: Montant à formater
        currency_code: Code ISO de la devise (EUR, USD, etc.)
        
    Returns:
        Chaîne formatée (ex: '124,50 €' ou '$124.50')
    """
    symbol = CURRENCY_SYMBOLS.get(currency_code.upper(), '€')
    
    if currency_code.upper() in ['USD', 'GBP', 'CAD', 'AUD']:
        return f"{symbol}{amount:,.2f}"
    else:
        # Format européen: 1.234,56 €
        # On utilise une astuce pour ne pas toucher à l'espace final
        num_part = f"{amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{num_part} {symbol}"

def get_i18n_text(key: str, lang: str = None) -> str:
    """
    Récupère une traduction pour une clé donnée.
    
    Args:
        key: Clé de traduction
        lang: Langue ('FR', 'EN', etc.). Si None, détecte automatiquement
        
    Returns:
        Texte traduit
    """
    # Auto-detect language if not provided
    if lang is None:
        lang = get_browser_language()
    
    translations = {
        'FR': {
            # Dashboard
            'dashboard_title': 'Refundly.ai - Tableau de bord',
            'recoverable': '💰 RÉCUPÉRABLE',
            'your_share': '🎯 VOTRE PART',
            'recovered': '✅ RÉCUPÉRÉ',
            'disputes_count': '📦 LITIGES ÉLIGIBLES',
            
            # Buttons & Actions
            'btn_back': 'Retour',
            'btn_view': 'Voir',
            'btn_escalate': 'Escalader',
            'btn_archive': 'Archiver',
            'btn_download_pdf': 'Télécharger PDF',
            'btn_add_note': 'Ajouter une note',
            'btn_view_details': 'Voir les détails',
            'btn_save_note': 'Enregistrer la note',
            
            # Page Titles & Headers
            'dispute_details': 'LITIGE',
            'carrier_overview': 'Vue d\'ensemble',
            'order_information': 'Informations de commande',
            'timeline': 'Chronologie',
            'evidence_photos': 'Photos de preuve',
            'statistics': 'Statistiques',
            'all_disputes': 'Tous les litiges',
            
            # Labels
            'status': 'Statut',
            'financial': 'Finances',
            'actions': 'Actions',
            'customer': 'Client',
            'email': 'Email',
            'address': 'Adresse',
            'order_date': 'Date de commande',
            'issue_type': 'Type de problème',
            'tracking': 'Suivi',
            'order': 'Commande',
            
            # Financial
            'total_recoverable': 'Total récupérable',
            'you_receive': 'Vous recevez',
            'our_fee': 'Nos frais',
            'ai_confidence': 'Confiance IA',
            
            # Statistics
            'active_disputes': 'Litiges actifs',
            'win_rate': 'Taux de succès',
            'total_recoverable': 'Total récupérable',
            
            # Dispute Types
            'delayed_delivery': 'Livraison retardée',
            'lost_package': 'Colis perdu',
            'damaged_package': 'Colis endommagé',
            'invalid_pod': 'POD invalide',
            'unknown': 'Problème inconnu',
            
            # Messages
            'no_evidence_yet': 'Aucune photo de preuve téléchargée',
            'no_disputes_found': 'Aucun litige trouvé avec',
            'all_disputes_with': 'Tous les litiges',
            'your_note': 'Votre note',
            
            # Status labels
            'status_pending': '⏳ En attente',
            'status_processing': '🔄 En traitement',
            'status_under_review': '📋 En révision',
            'status_resolved': '✅ Résolu',
            'status_rejected': '❌ Rejeté',
            
            # Legal (existing)
            'legal_header_from': 'EXPÉDITEUR :',
            'legal_header_to': 'DESTINATAIRE :',
            'legal_header_subject': 'OBJET : MISE EN DEMEURE POUR DÉFAUT D\'INDEMNISATION',
            'legal_ref_claim': 'Réf. Réclamation :',
            'legal_ref_tracking': 'Réf. Colis (Tracking) :',
            'legal_body_intro': 'Nous faisons suite à notre réclamation concernant le litige cité en référence.',
            'legal_body_law': 'En vertu de l\'article L133-1 du Code des Transports, vous êtes garant de la perte ou de l\'avarie des objets à transporter.',
            'legal_body_demand': 'Par la présente, nous vous METTONS EN DEMEURE d\'effectuer le règlement sous 8 jours.',
            'legal_body_closing': 'À défaut, nous saisirons le Médiateur compétent.',
            'legal_signature': 'POUR ORDRE : L\'AGENT MANDATAIRE AUTOMATISÉ'
        },
        'EN': {
            # Dashboard
            'dashboard_title': 'Client Dashboard',
            'recoverable': '💰 RECOVERABLE',
            'your_share': '🎯 YOUR SHARE',
            'recovered': '✅ RECOVERED',
            'disputes_count': '📦 ELIGIBLE DISPUTES',
            
            # Buttons & Actions
            'btn_back': 'Back',
            'btn_view': 'View',
            'btn_escalate': 'Escalate',
            'btn_archive': 'Archive',
            'btn_download_pdf': 'Download PDF',
            'btn_add_note': 'Add Note',
            'btn_view_details': 'View Details',
            'btn_save_note': 'Save Note',
            
            # Page Titles & Headers
            'dispute_details': 'DISPUTE',
            'carrier_overview': 'Overview',
            'order_information': 'Order Information',
            'timeline': 'Timeline',
            'evidence_photos': 'Evidence Photos',
            'statistics': 'Statistics',
            'all_disputes': 'All Disputes',
            
            # Labels
            'status': 'Status',
            'financial': 'Financial',
            'actions': 'Actions',
            'customer': 'Customer',
            'email': 'Email',
            'address': 'Address',
            'order_date': 'Order Date',
            'issue_type': 'Issue Type',
            'tracking': 'Tracking',
            'order': 'Order',
            
            # Financial
            'total_recoverable': 'Total Recoverable',
            'you_receive': 'You Receive',
            'our_fee': 'Our Fee',
            'ai_confidence': 'AI Confidence',
            
            # Statistics
            'active_disputes': 'Active Disputes',
            'win_rate': 'Win Rate',
            
            # Dispute Types
            'delayed_delivery': 'Delayed delivery',
            'lost_package': 'Lost package',
            'damaged_package': 'Damaged package',
            'invalid_pod': 'Invalid POD',
            'unknown': 'Unknown issue',
            
            # Messages
            'no_evidence_yet': 'No evidence photos uploaded yet',
            'no_disputes_found': 'No disputes found with',
            'all_disputes_with': 'All disputes with',
            'your_note': 'Your note',
            
            # Status labels
            'status_pending': '⏳ Pending',
            'status_processing': '🔄 Processing',
            'status_under_review': '📋 Under Review',
            'status_resolved': '✅ Resolved',
            'status_rejected': '❌ Rejected',
            
            # Legal (existing)
            'legal_header_from': 'SENDER:',
            'legal_header_to': 'RECIPIENT:',
            'legal_header_subject': 'SUBJECT: FORMAL NOTICE FOR NON-PAYMENT OF COMPENSATION',
            'legal_ref_claim': 'Claim Ref:',
            'legal_ref_tracking': 'Tracking Ref:',
            'legal_body_intro': 'We are writing following our claim regarding the referenced dispute.',
            'legal_body_law': 'Under the applicable transport laws (including the Consumer Rights Act where applicable), you are liable for the loss or damage of goods in transit.',
            'legal_body_demand': 'We hereby give you FORMAL NOTICE to settle this claim within 8 days.',
            'legal_body_closing': 'Failing that, we will escalate this matter to the relevant Ombudsman.',
            'legal_signature': 'FOR AND ON BEHALF OF: THE AUTOMATED CLAIMS AGENT',
            'legal_law_ny': 'Under New York State General Business Law § 396-u and the Federal Carmack Amendment (49 U.S.C. § 14706), carrier is liable for loss or damage as an insurer.',
            'legal_law_ca': 'Under California Commercial Code § 7309, a carrier who issues a bill of lading is required to exercise the degree of care that a reasonably careful person would exercise.',
            'legal_law_tx': 'Under Texas Deceptive Trade Practices-Consumer Protection Act (DTPA) and Common Law carrier liability, you are responsible for the safe delivery of goods.',
            'legal_law_us_federal': 'Under the Federal Carmack Amendment (49 U.S.C. § 14706), a common carrier is liable for "actual loss or injury to the property" occurring during the transportation of goods in interstate commerce.',
            'legal_law_uk': 'Under the Consumer Rights Act 2015 and the Carriage of Goods by Road Act 1965, the carrier is strictly liable for the loss or damage of goods from the time they take possession until delivery.',
            'legal_body_law_uk': 'In accordance with the UK Consumer Rights Act 2015, the delivery of goods is a part of the contract, and you are responsible for ensuring they reach the consumer in satisfactory condition.',
            'legal_law_hk': 'Under the Control of Exemption Clauses Ordinance (Cap. 71) and common law principles governing contracts of carriage, the carrier is liable for loss or damage unless they can prove reasonable care was taken.',
            'legal_law_sg': 'Under the Carriage of Goods by Sea Act or the common law of bailment as applicable in Singapore, the carrier owes a duty of care to ensure the safe arrival of goods.',
            'legal_law_eu_cmr': 'Pursuant to the CMR Convention (Article 17) and relevant EU transport regulations, the carrier is liable for the total or partial loss of the goods and for damage thereto occurring between the time when they take over the goods and the time of delivery.',
            'legal_body_law_eu': 'According to the CMR Convention, which governs international and domestic transport in the EU, you are strictly liable for the safety and integrity of the shipment.'
        },
        'DE': {
            # Dashboard
            'dashboard_title': 'Händler-Dashboard',
            'recoverable': '💰 RÜCKFORDERBAR',
            'your_share': '🎯 IHR ANTEIL',
            'recovered': '✅ ERSTATTET',
            'disputes_count': '📦 BERECHTIGTE FÄLLE',
            
            # Buttons & Actions
            'btn_back': 'Zurück',
            'btn_view': 'Ansehen',
            'btn_escalate': 'Eskalieren',
            'btn_archive': 'Archivieren',
            'btn_download_pdf': 'PDF herunterladen',
            'btn_add_note': 'Notiz hinzufügen',
            'btn_view_details': 'Details ansehen',
            'btn_save_note': 'Notiz speichern',
            
            # Page Titles
            'dispute_details': 'STREITFALL',
            'carrier_overview': 'Übersicht',
            'order_information': 'Bestellinformationen',
            'timeline': 'Zeitleiste',
            'evidence_photos': 'Beweisfotos',
            'statistics': 'Statistiken',
            'all_disputes': 'Alle Streitfälle',
            
            # Labels
            'status': 'Status',
            'financial': 'Finanzen',
            'actions': 'Aktionen',
            'customer': 'Kunde',
            'email': 'E-Mail',
            'address': 'Adresse',
            'order_date': 'Bestelldatum',
            'issue_type': 'Problemtyp',
            'tracking': 'Sendungsnummer',
            'order': 'Bestellung',
            
            # Financial
            'total_recoverable': 'Gesamt rückforderbar',
            'you_receive': 'Sie erhalten',
            'our_fee': 'Unsere Gebühr',
            'ai_confidence': 'KI-Vertrauen',
            
            # Statistics
            'active_disputes': 'Aktive Streitfälle',
            'win_rate': 'Erfolgsquote',
            
            # Dispute Types
            'delayed_delivery': 'Verspätete Lieferung',
            'lost_package': 'Verlorenes Paket',
            'damaged_package': 'Beschädigtes Paket',
            'invalid_pod': 'Ungültige Zustellbestätigung',
            'unknown': 'Unbekanntes Problem',
            
            # Messages
            'no_evidence_yet': 'Noch keine Beweisfotos hochgeladen',
            'no_disputes_found': 'Keine Streitfälle gefunden mit',
            'all_disputes_with': 'Alle Streitfälle mit',
            'your_note': 'Ihre Notiz',
            
            # Legal
            'legal_header_from': 'ABSENDER:',
            'legal_header_to': 'EMPFÄNGER:',
            'legal_header_subject': 'BETREFF: MAHNUNG WEGEN FEHLENDER ENTSCHÄDIGUNG',
            'legal_ref_claim': 'Reklamations-Nr:',
            'legal_ref_tracking': 'Sendungsnummer:',
            'legal_body_intro': 'Wir beziehen uns auf unsere Reklamation bezüglich des oben genannten Falls.',
            'legal_body_law': 'Gemäß § 425 HGB haftet der Frachtführer für den Schaden, der durch Verlust oder Beschädigung des Gut in der Zeit von der Übernahme zur Beförderung bis zur Ablieferung entsteht.',
            'legal_body_demand': 'Hiermit FORDERN WIR SIE AUF, den ausstehenden Betrag innerhalb von 8 Tagen auszugleichen.',
            'legal_body_closing': 'Sollte diese Frist fruchtlos verstreichen, werden wir rechtliche Schritte einleiten.',
            'legal_signature': 'IM AUFTRAG: DER AUTOMATISIERTE REKLAMATIONS-AGENT'
        },
        'IT': {
            # Dashboard
            'dashboard_title': 'Dashboard Commerciante',
            'recoverable': '💰 RECUPERABILE',
            'your_share': '🎯 TUA QUOTA',
            'recovered': '✅ RECUPERATO',
            'disputes_count': '📦 DISPUTE IDONEE',
            
            # Buttons & Actions
            'btn_back': 'Indietro',
            'btn_view': 'Visualizza',
            'btn_escalate': 'Escalare',
            'btn_archive': 'Archivia',
            'btn_download_pdf': 'Scarica PDF',
            'btn_add_note': 'Aggiungi nota',
            'btn_view_details': 'Vedi dettagli',
            'btn_save_note': 'Salva nota',
            
            # Page Titles
            'dispute_details': 'CONTROVERSIA',
            'carrier_overview': 'Panoramica',
            'order_information': 'Informazioni ordine',
            'timeline': 'Cronologia',
            'evidence_photos': 'Foto di prova',
            'statistics': 'Statistiche',
            'all_disputes': 'Tutte le controversie',
            
            # Labels
            'status': 'Stato',
            'financial': 'Finanziario',
            'actions': 'Azioni',
            'customer': 'Cliente',
            'email': 'Email',
            'address': 'Indirizzo',
            'order_date': 'Data ordine',
            'issue_type': 'Tipo di problema',
            'tracking': 'Tracciamento',
            'order': 'Ordine',
            
            # Legal
            'legal_header_from': 'MITTENTE:',
            'legal_header_to': 'DESTINATARIO:',
            'legal_header_subject': 'OGGETTO: MESSA IN MORA PER MANCATO INDENNIZZO',
            'legal_ref_claim': 'Rif. Reclamo:',
            'legal_ref_tracking': 'Rif. Spedizione:',
            'legal_body_intro': 'Facciamo seguito al nostro reclamo relativo alla controversia citata in riferimento.',
            'legal_body_law': 'Ai sensi dell\'articolo 1693 del Codice Civile, il vettore è responsabile della perdita e dell\'avaria delle cose consegnategli per il trasporto.',
            'legal_body_demand': 'Con la presente, vi METTIAMO IN MORA affinché provvediate al pagamento entro 8 giorni.',
            'legal_body_closing': 'In mancanza di ciò, agiremo nelle sedi competenti.',
            'legal_signature': 'PER ORDINE: L\'AGENTE DI RECLAMO AUTOMATIZZATO'
        },
        'ES': {
            # Dashboard
            'dashboard_title': 'Panel de Control',
            'recoverable': '💰 RECUPERABLE',
            'your_share': '🎯 TU PARTE',
            'recovered': '✅ RECUPERADO',
            'disputes_count': '📦 DISPUTAS ELEGIBLES',
            
            # Buttons & Actions
            'btn_back': 'Atrás',
            'btn_view': 'Ver',
            'btn_escalate': 'Escalar',
            'btn_archive': 'Archivar',
            'btn_download_pdf': 'Descargar PDF',
            'btn_add_note': 'Añadir nota',
            'btn_view_details': 'Ver detalles',
            'btn_save_note': 'Guardar nota',
            
            # Page Titles
            'dispute_details': 'DISPUTA',
            'carrier_overview': 'Resumen',
            'order_information': 'Información del pedido',
            'timeline': 'Línea de tiempo',
            'evidence_photos': 'Fotos de prueba',
            'statistics': 'Estadísticas',
            'all_disputes': 'Todas las disputas',
            
            # Labels
            'status': 'Estado',
            'financial': 'Financiero',
            'actions': 'Acciones',
            'customer': 'Cliente',
            'email': 'Correo',
            'address': 'Dirección',
            'order_date': 'Fecha del pedido',
            'issue_type': 'Tipo de problema',
            'tracking': 'Seguimiento',
            'order': 'Pedido',
            
            # Legal
            'legal_header_from': 'REMITENTE:',
            'legal_header_to': 'DESTINATARIO:',
            'legal_header_subject': 'ASUNTO: REQUERIMIENTO FORMAL POR FALTA DE INDEMNIZACIÓN',
            'legal_ref_claim': 'Ref. Reclamación:',
            'legal_ref_tracking': 'Ref. Seguimiento:',
            'legal_body_intro': 'Hacemos seguimiento a nuestra reclamación relativa a la disputa mencionada.',
            'legal_body_law': 'De acuerdo con la Ley 15/2009 del Contrato de Transporte Terrestre, el porteador responderá de la pérdida total o parcial de las mercancías.',
            'legal_body_demand': 'Por la presente, le REQUERIMOS FORMALMENTE para que proceda al pago en un plazo de 8 días.',
            'legal_body_closing': 'De lo contrario, tomaremos las medidas legales oportunas.',
            'legal_signature': 'POR ORDEN: EL AGENTE DE RECLAMACIONES AUTOMATIZADO'
        }
    }
    
    return translations.get(lang.upper(), translations['FR']).get(key, key)

