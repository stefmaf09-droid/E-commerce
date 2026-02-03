"""
Antigravity Browser Client

Communicates with external Antigravity browser automation service
for real portal navigation and claim submission.
"""

import requests
import logging
import os
from typing import Dict, Optional, List
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class AntigravityBrowserClient:
    """
    Client for communicating with Antigravity browser automation service.
    
    The Antigravity service is a separate microservice that:
    1. Receives skill execution requests via HTTP/WebSocket
    2. Launches browser (Playwright/Selenium)
    3. Navigates carrier portals following SKILL.md instructions
    4. Handles captchas, uploads documents, fills forms
   5. Returns confirmation data and screenshots
    
    Environment variables:
    - ANTIGRAVITY_URL: Base URL of Antigravity service (default: http://localhost:8080)
    - ANTIGRAVITY_API_KEY: Optional API key for authentication
    """
    
    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initialize Antigravity client.
        
        Args:
            base_url: Antigravity service URL
            api_key: Optional API key for authentication
        """
        self.base_url = base_url or os.getenv('ANTIGRAVITY_URL', 'http://localhost:8080')
        self.api_key = api_key or os.getenv('ANTIGRAVITY_API_KEY')
        self.timeout = 300  # 5 minutes max per navigation
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers['X-API-Key'] = self.api_key
        
        logger.info(f"AntigravityBrowserClient initialized: {self.base_url}")
    
    async def execute_skill(
        self,
        skill_name: str,
        skill_path: str,
        dispute: Dict,
        claim_text: str,
        documents: List[str] = None
    ) -> Dict:
        """
        Execute a carrier skill via Antigravity browser.
        
        Args:
            skill_name: Carrier name (colissimo, chronopost, ups, etc.)
            skill_path: Path to SKILL.md file
            dispute: Dispute data dictionary
            claim_text: Generated claim text
            documents: List of document file paths to upload
            
        Returns:
            Execution result dictionary with claim reference, status, screenshot
        """
        # Load skill instructions
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                skill_instructions = f.read()
        except Exception as e:
            logger.error(f"Failed to load skill {skill_path}: {e}")
            return {
                'status': 'error',
                'error': f'Skill file not found: {skill_path}',
                'fallback': 'manual_intervention_required'
            }
        
        # Prepare execution payload
        payload = {
            'skill_name': skill_name,
            'skill_version': '1.0',
            'instructions': skill_instructions,
            'data': {
                'tracking_number': dispute.get('tracking_number'),
                'carrier': dispute.get('carrier'),
                'claim_type': dispute.get('dispute_type'),
                'claim_text': claim_text,
                'client_email': dispute.get('client_email'),
                'client_name': dispute.get('client_name'),
                'order_value': dispute.get('order_value'),
                'shipping_cost': dispute.get('shipping_cost'),
                'documents': documents or []
            },
            'options': {
                'headless': True,
                'timeout': self.timeout,
                'captcha_service': '2captcha',  # or 'anticaptcha'
                'screenshot': True,
                'save_html': True
            }
        }
        
        logger.info(f"📤 Sending {skill_name} skill to Antigravity browser...")
        
        try:
            # POST to Antigravity API
            response = self.session.post(
                f"{self.base_url}/api/v1/execute",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Log success
            claim_ref = result.get('claim_reference', 'N/A')
            status = result.get('status', 'unknown')
            logger.info(f"✓ {skill_name} executed | Status: {status} | Ref: {claim_ref}")
            
            return result
            
        except requests.Timeout:
            logger.error(f"⏱️  Timeout executing {skill_name} (>{self.timeout}s)")
            return {
                'status': 'timeout',
                'error': f'Execution exceeded {self.timeout} seconds',
                'fallback': 'retry_later'
            }
        
        except requests.HTTPError as e:
            logger.error(f"❌ HTTP error executing {skill_name}: {e}")
            return {
                'status': 'http_error',
                'error': str(e),
                'status_code': e.response.status_code if e.response else None,
                'fallback': 'manual_intervention_required'
            }
        
        except Exception as e:
            logger.error(f"❌ Unexpected error executing {skill_name}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'fallback': 'manual_intervention_required'
            }
    
    def get_status(self, execution_id: str) -> Dict:
        """
        Get status of an ongoing execution.
        
        For long-running executions, Antigravity may return an ID immediately
        and complete asynchronously.
        
        Args:
            execution_id: Execution ID from initial request
            
        Returns:
            Current status dictionary
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/executions/{execution_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting execution status: {e}")
            return {'status': 'unknown', 'error': str(e)}
    
    def health_check(self) -> bool:
        """
        Check if Antigravity service is available.
        
        Returns:
            True if service is reachable, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


# Test
if __name__ == "__main__":
    print("="*70)
    print("ANTIGRAVITY BROWSER CLIENT - Test")
    print("="*70)
    
    client = AntigravityBrowserClient()
    
    print(f"\n🔗 Antigravity URL: {client.base_url}")
    
    # Health check
    healthy = client.health_check()
    print(f"🏥 Health check: {'✅ OK' if healthy else '❌ Service unreachable'}")
    
    if not healthy:
        print("\n⚠️  Antigravity service not running")
        print("   To use real browser automation:")
        print("   1. Deploy Antigravity service separately")
        print("   2. Set ANTIGRAVITY_URL environment variable")
        print("   3. Ensure service is accessible")
    
    print("\n" + "="*70)
    print("Note: This is a client library")
    print("Real execution requires Antigravity service running")
    print("="*70)
