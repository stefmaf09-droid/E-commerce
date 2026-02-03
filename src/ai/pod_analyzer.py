"""
POD (Proof of Delivery) Analyzer using Vision AI.

Analyzes delivery proof images to detect anomalies and validate legitimacy.
Uses OpenAI GPT-4 Vision API for intelligent image analysis.
"""

import base64
import json
import logging
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime

try:
    import openai
except ImportError:
    openai = None

try:
    from PIL import Image
except ImportError:
    Image = None

logger = logging.getLogger(__name__)


class PODAnalyzer:
    """Analyze POD images using Vision AI to detect anomalies."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize POD Analyzer.
        
        Args:
            api_key: OpenAI API key (optional, will use env var if not provided)
        """
        if not openai:
            raise ImportError("openai package required. Install with: pip install openai")
        
        self.client = openai.OpenAI(api_key=api_key) if api_key else openai.OpenAI()
        
        logger.info("PODAnalyzer initialized with Vision AI")
    
    def analyze_pod_image(
        self, 
        image_path: str,
        tracking_number: Optional[str] = None,
        expected_delivery_date: Optional[str] = None
    ) -> Dict:
        """
        Analyze a POD image for anomalies.
        
        Args:
            image_path: Path to POD image file
            tracking_number: Optional tracking number for context
            expected_delivery_date: Expected delivery date for validation
            
        Returns:
            Dictionary with analysis results:
            {
                'signature_present': bool,
                'signature_legible': bool,
                'package_visible': bool,
                'timestamp_coherent': bool,
                'anomalies': List[str],
                'confidence_invalid': float,
                'raw_analysis': str
            }
        """
        logger.info(f"Analyzing POD: {image_path}")
        
        # Validate file exists
        if not Path(image_path).exists():
            logger.error(f"Image file not found: {image_path}")
            return self._create_error_response("Image file not found")
        
        try:
            # Encode image to base64
            image_data = self._encode_image(image_path)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(tracking_number, expected_delivery_date)
            
            # Call GPT-4 Vision
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }],
                max_tokens=1000,
                temperature=0.1  # Low temperature for consistent analysis
            )
            
            # Parse response
            raw_analysis = response.choices[0].message.content
            logger.info(f"Vision API response received ({len(raw_analysis)} chars)")
            
            # Extract structured data
            analysis = self._parse_vision_response(raw_analysis)
            analysis['raw_analysis'] = raw_analysis
            
            logger.info(f"POD analysis complete. Confidence invalid: {analysis['confidence_invalid']:.2f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing POD: {e}")
            return self._create_error_response(str(e))
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _create_analysis_prompt(
        self, 
        tracking_number: Optional[str],
        expected_date: Optional[str]
    ) -> str:
        """Create analysis prompt for Vision AI."""
        
        prompt = """Analyse cette preuve de livraison (POD) pour détecter des anomalies.

CRITÈRES D'ANALYSE :

1. **Signature**
   - Signature présente ?
   - Signature lisible et réaliste ?
   - Signature ressemble à un gribouillis suspect ?

2. **Photo du colis**
   - Colis visible dans la photo ?
   - Photo de bonne qualité ?
   - Contexte de la photo cohérent ?

3. **Timestamp & Métadonnées**
   - Date/heure visible ?
   - Timestamp cohérent (pas trop tard le soir, pas trop tôt) ?
   - Métadonnées GPS si visibles ?

4. **Contexte général**
   - Photo semble authentique ?
   - Lieu de livraison cohérent ?
   - Autres anomalies visuelles ?

"""
        
        if tracking_number:
            prompt += f"\nNuméro de suivi : {tracking_number}"
        
        if expected_date:
            prompt += f"\nDate de livraison attendue : {expected_date}"
        
        prompt += """

RÉPONSE ATTENDUE (format JSON strict) :
```json
{
    "signature_present": true/false,
    "signature_legible": true/false,
    "package_visible": true/false,
    "timestamp_present": true/false,
    "timestamp_coherent": true/false,
    "photo_quality": "good"/"poor"/"very_poor",
    "anomalies": ["Liste des anomalies détectées"],
    "confidence_invalid": 0.0-1.0,
    "summary": "Résumé en 1-2 phrases"
}
```

Sois critique et strict. Si quelque chose semble suspect, marque-le comme anomalie.
"""
        
        return prompt
    
    def _parse_vision_response(self, raw_response: str) -> Dict:
        """Parse Vision AI response into structured format."""
        
        # Try to extract JSON from response
        try:
            # Find JSON block
            start = raw_response.find('{')
            end = raw_response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = raw_response[start:end]
                data = json.loads(json_str)
                
                # Ensure all required fields
                return {
                    'signature_present': data.get('signature_present', False),
                    'signature_legible': data.get('signature_legible', False),
                    'package_visible': data.get('package_visible', False),
                    'timestamp_present': data.get('timestamp_present', False),
                    'timestamp_coherent': data.get('timestamp_coherent', True),
                    'photo_quality': data.get('photo_quality', 'unknown'),
                    'anomalies': data.get('anomalies', []),
                    'confidence_invalid': float(data.get('confidence_invalid', 0.0)),
                    'summary': data.get('summary', '')
                }
        
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse JSON response: {e}")
        
        # Fallback: parse text heuristically
        return self._parse_text_response(raw_response)
    
    def _parse_text_response(self, text: str) -> Dict:
        """Fallback parser for non-JSON responses."""
        
        text_lower = text.lower()
        
        # Simple keyword detection
        anomalies = []
        
        if 'signature' in text_lower:
            if 'illisible' in text_lower or 'gribouillis' in text_lower:
                anomalies.append('Signature illisible ou suspecte')
        
        if 'colis' in text_lower:
            if 'invisible' in text_lower or 'pas visible' in text_lower or 'non visible' in text_lower:
                anomalies.append('Colis non visible sur la photo')
        
        if 'timestamp' in text_lower or 'heure' in text_lower:
            if 'incohérent' in text_lower or 'suspect' in text_lower:
                anomalies.append('Timestamp incohérent')
        
        if 'photo' in text_lower and ('floue' in text_lower or 'mauvaise' in text_lower):
            anomalies.append('Mauvaise qualité photo')
        
        # Estimate confidence based on anomalies
        confidence = min(len(anomalies) * 0.25, 0.95)
        
        return {
            'signature_present': 'signature' in text_lower,
            'signature_legible': 'lisible' in text_lower,
            'package_visible': 'colis' in text_lower and 'visible' in text_lower,
            'timestamp_present': 'timestamp' in text_lower or 'heure' in text_lower,
            'timestamp_coherent': 'incohérent' not in text_lower,
            'photo_quality': 'poor' if 'mauvaise' in text_lower else 'unknown',
            'anomalies': anomalies,
            'confidence_invalid': confidence,
            'summary': text[:200]
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create error response."""
        return {
            'signature_present': False,
            'signature_legible': False,
            'package_visible': False,
            'timestamp_present': False,
            'timestamp_coherent': False,
            'photo_quality': 'error',
            'anomalies': [f'Erreur analyse: {error_message}'],
            'confidence_invalid': 0.0,
            'summary': f'Erreur: {error_message}',
            'error': True
        }
    
    def analyze_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        Analyze multiple POD images in batch.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of analysis results
        """
        results = []
        
        for image_path in image_paths:
            try:
                result = self.analyze_pod_image(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch analysis for {image_path}: {e}")
                results.append(self._create_error_response(str(e)))
        
        return results


# Example usage
if __name__ == "__main__":
    import os
    
    # Demo mode (requires OPENAI_API_KEY env var)
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set. Set it to test POD analysis.")
        print("Example: export OPENAI_API_KEY=sk-...")
    else:
        analyzer = PODAnalyzer(api_key=api_key)
        
        # Test with a sample image (you'd need a real POD image)
        print("\n" + "="*60)
        print("POD ANALYZER - Demo Mode")
        print("="*60)
        print("\nTo test, provide a POD image path:")
        print("  result = analyzer.analyze_pod_image('path/to/pod.jpg')")
        print("\nResult will include:")
        print("  - Signature analysis")
        print("  - Package visibility")
        print("  - Timestamp validation")
        print("  - Anomalies detected")
        print("  - Confidence score (0-1)")
