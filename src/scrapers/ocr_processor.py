
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    Simule l'analyse OCR et NLP des lettres de rejet transporteur.
    Détecte les patterns de refus pour automatiser les conseils clients.
    """
    
    def __init__(self):
        # Dictionnaire des motifs de rejet et conseils associés
        self.rejection_patterns = {
            r"(signature|signature).*(correspond pas|manquante|non reconnue|invalid|missing|not match)": {
                "reason_key": "bad_signature",
                "label_fr": "Signature Non Conforme",
                "label_en": "Invalid Signature",
                "advice_fr": "Le transporteur conteste la signature sur le bordereau. Veuillez fournir une attestation sur l'honneur signée par le client final avec une copie de sa pièce d'identité.",
                "advice_en": "Carrier disputes the signature on the POD. Please provide a signed declaration from the end customer along with a copy of their ID."
            },
            r"(poids|weight|réel).*(conforme|réel|match|verified|correct)": {
                "reason_key": "weight_match",
                "label_fr": "Poids Vérifié",
                "label_en": "Weight Verified",
                "advice_fr": "Le transporteur affirme que le poids au départ correspond au poids à l'arrivée. Veuillez fournir une photo de l'emballage d'origine montrant l'absence de scotch de sécurité transporteur.",
                "advice_en": "Carrier claims departure weight matches arrival weight. Please provide a photo of the original packaging showing the absence of carrier security tape."
            },
            r"(emballage|conditionnement|packaging|packing).*(insuffisant|fragile|insufficient|inadequate)": {
                "reason_key": "bad_packaging",
                "label_fr": "Emballage Insuffisant",
                "label_en": "Inadequate Packaging",
                "advice_fr": "Le refus est basé sur la fragilité de l'emballage. Contre-attaquez en fournissant les spécifications techniques de vos cartons (normes AFCO/FEFCO).",
                "advice_en": "Refusal based on fragile packaging. Counter-attack by providing technical specifications of your boxes (AFCO/FEFCO standards)."
            },
            r"(délai|delai|deadline|late|expired|prescrit)": {
                "reason_key": "deadline_expired",
                "label_fr": "Délai de Prescription Dépassé",
                "label_en": "Claim Deadline Expired",
                "advice_fr": "Le transporteur invoque un dépassement de délai. Vérifiez la date de livraison réelle. Si le retard est de leur fait, la prescription peut être contestée.",
                "advice_en": "Carrier claims the deadline has expired. Check the actual delivery date. If the delay is their fault, the prescription can be contested."
            },
            r"(adresse|address).*(incorrect|wrong|incomplète|incomplete)": {
                "reason_key": "wrong_address",
                "label_fr": "Erreur d'Adresse",
                "label_en": "Address Error",
                "advice_fr": "Le transporteur affirme que l'adresse était erronée. Fournissez une capture d'écran de la commande Shopify/Woo mémorisant l'adresse brute saisie par le client.",
                "advice_en": "Carrier claims the address was incorrect. Provide a screenshot of the Shopify/Woo order showing the exact address entered by the customer."
            }
        }
        # On ajoute aussi l'ordre inverse pour plus de robustesse
        self.rejection_patterns_rev = {
            r"(verified|correct|match).*(weight|poids)": self.rejection_patterns[r"(poids|weight|réel).*(conforme|réel|match|verified|correct)"]
        }

    def preprocess_image(self, image_path: str) -> Dict[str, Any]:
        """
        Simule le prétraitement d'image (Binarisation, Débruitage, Deskewing).
        Prépare l'image pour un OCR haute résolution.
        """
        logger.info(f"Preprocessing image: {image_path}")
        return {
            "status": "success",
            "quality_score": 0.92,
            "dpi": 300,
            "deskewed": True
        }

    def analyze_rejection_text(self, text: str) -> Dict[str, Any]:
        """
        Analyse le texte extrait et retourne le motif détecté avec un score de confiance.
        """
        # Test patterns normaux
        for pattern, info in self.rejection_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                logger.info(f"Rejection pattern detected: {info['reason_key']}")
                info['confidence'] = 0.95
                return info
        
        # Test patterns inversés
        for pattern, info in self.rejection_patterns_rev.items():
            if re.search(pattern, text, re.IGNORECASE):
                logger.info(f"Rejection pattern (rev) detected: {info['reason_key']}")
                info['confidence'] = 0.85
                return info
        
        return {
            "reason_key": "unknown",
            "label_fr": "Motif inconnu",
            "confidence": 0.0,
            "advice_fr": "Nous analysons manuellement la réponse du transporteur.",
            "advice_en": "We are manually analyzing the carrier's response."
        }

    def simulate_ocr_on_file(self, file_path: str) -> str:
        """
        Simule l'extraction de texte. Pour la démo, on retourne un texte type
        en fonction du nom de fichier.
        """
        if "rejet_poids" in file_path.lower():
            return "Après vérification, le poids réel du colis lors du transit correspond au poids déclaré."
        elif "rejet_signature" in file_path.lower():
            return "La signature présente sur le document de livraison est reconnue comme valide par nos services, le colis est livré."
        elif "rejet_delai" in file_path.lower():
            return "Votre demande d'indemnisation est rejetée car le délai de réclamation de 30 jours est dépassé."
        
        return "Nous n'avons pas pu valider votre demande d'indemnisation pour cause d'emballage insuffisant."
