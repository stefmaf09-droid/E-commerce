
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

    def save_correction(self, original_text: str, corrected_reason_key: str, user_feedback: str = ""):
        """
        Enregistre la correction de l'utilisateur pour améliorer l'IA (Feedback Loop).
        """
        import json
        import os
        from datetime import datetime
        
        feedback_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'ocr_feedback.json')
        os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'original_text_snippet': original_text[:200], # Keep snippet
            'corrected_reason_key': corrected_reason_key,
            'user_feedback': user_feedback
        }
        
        try:
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            else:
                feedbacks = []
                
            feedbacks.append(entry)
            
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedbacks, f, indent=2, ensure_ascii=False)
                
            logger.info("Feedback saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            return False

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

    def extract_text_from_file(self, file_path_or_buffer: Any, filename: str) -> str:
        """
        Tente d'extraire le texte du fichier (PDF ou Image) en utilisant OCR réel si disponible,
        sinon retombe sur la simulation basée sur le nom de fichier.
        """
        text = ""
        
        # 1. Essai OCR Réel (PDF)
        if filename.lower().endswith('.pdf'):
            try:
                import PyPDF2
                if hasattr(file_path_or_buffer, 'read'): # C'est un buffer Streamlit
                    pdf_reader = PyPDF2.PdfReader(file_path_or_buffer)
                else:
                    pdf_reader = PyPDF2.PdfReader(file_path_or_buffer)
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                logger.info("PDF Text Extraction successful")
            except Exception as e:
                logger.warning(f"PDF extraction failed: {e}")

        # 2. Essai OCR Réel (Images - Tesseract)
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                from PIL import Image
                import pytesseract
                import os
                import shutil
                
                # Configuration Tesseract Plus Robuste
                # On cherche dans les chemins standards si pas configuré par défaut
                tesseract_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    '/usr/bin/tesseract',
                    '/usr/local/bin/tesseract'
                ]
                
                # Vérifier si déjà dans le PATH
                if shutil.which('tesseract'):
                     # Déjà configuré dans le PATH, pas besoin de spécifier cmd
                     pass
                else:
                    found = False
                    for path in tesseract_paths:
                        if os.path.exists(path):
                            pytesseract.pytesseract.tesseract_cmd = path
                            found = True
                            break
                    if not found:
                         logger.warning("Tesseract executable not found. OCR will fail.")

                
                image = Image.open(file_path_or_buffer)
                
                # Stratégie Multi-Angle
                rotations = [0, -90, 90] 
                full_text = ""
                
                for angle in rotations:
                    rotated_img = image.rotate(angle, expand=True)
                    rotated_img = rotated_img.convert('L') # Niveaux de gris
                    
                    # Configuration : --psm 6 (Assume a single uniform block of text) peut être meilleur pour des lettres
                    custom_config = r'--oem 3 --psm 6' 
                    page_text = pytesseract.image_to_string(rotated_img, config=custom_config)
                    full_text += f"\n--- Angle {angle}° ---\n" + page_text
                    
                    if len(page_text) > 50: # Si on trouve du texte significatif, c'est bon signe
                         logger.info(f"OCR Angle {angle}° extracted {len(page_text)} chars.")

                text = full_text
                logger.info("Multi-angle OCR completed")
            except ImportError:
                logger.warning("Pytesseract or Pillow not installed.")
            except Exception as e:
                logger.warning(f"Image OCR failed: {e}")

        # 3. Fallback
        if not text or len(text) < 10:
            logger.info("Fallback to simulation based on filename")
            return self.simulate_ocr_on_file(filename)
            
        return text

    def simulate_ocr_on_file(self, filename: str) -> str:
        """
        Simule l'extraction de texte si l'OCR échoue.
        """
        filename = filename.lower()
        if "rejet_poids" in filename:
            return "Après vérification, le poids réel du colis lors du transit correspond au poids déclaré."
        elif "signature" in filename: 
            return "La signature présente sur le document de livraison est reconnue comme valide par nos services."
        elif "rejet_delai" in filename:
            return "Votre demande d'indemnisation est rejetée car le délai de réclamation de 30 jours est dépassé."
        elif "dpd" in filename:
             return "DPD France - Preuve de livraison. Colis 250062801950819. Poids 16kg. Date 11/07/2023. Statut: Livré avec réserve (endommagé)."
        
        return "Nous n'avons pas pu valider votre demande d'indemnisation pour cause d'emballage insuffisant."
