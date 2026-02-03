"""
OAuth handler for managing OAuth flows for different platforms.

Handles OAuth redirects, callbacks, and token exchange.
"""

import logging
from typing import Dict, Optional
from src.integrations import (
    ShopifyConnector,
    BigCommerceConnector
)
from src.auth.magic_links import MagicLinksManager
from src.auth.credentials_manager import CredentialsManager

logger = logging.getLogger(__name__)


class OAuthHandler:
    """Handle OAuth flows for different e-commerce platforms."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize OAuth handler.
        
        Args:
            base_url: Base URL of the application (for OAuth callbacks)
        """
        self.base_url = base_url.rstrip('/')
        self.magic_links = MagicLinksManager(base_url=base_url)
        self.credentials = CredentialsManager()
    
    def get_callback_url(self, platform: str) -> str:
        """
        Get OAuth callback URL for a platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Callback URL
        """
        return f"{self.base_url}/oauth/callback/{platform}"
    
    def initiate_oauth_flow(
        self, 
        link_id: str, 
        token: str,
        platform_credentials: Dict[str, str]
    ) -> Optional[str]:
        """
        Initiate OAuth flow after magic link validation.
        
        Args:
            link_id: Magic link ID
            token: Magic link token
            platform_credentials: Platform-specific credentials (API key, etc.)
            
        Returns:
            Authorization URL to redirect user to, or None if invalid
        """
        # Validate magic link
        link_info = self.magic_links.validate_magic_link(link_id, token)
        
        if not link_info:
            logger.error(f"Invalid magic link: {link_id}")
            return None
        
        platform = link_info['platform']
        client_email = link_info['client_email']
        
        # Generate OAuth Authauthorization URL based on platform
        if platform == 'shopify':
            shop_domain = platform_credentials.get('shop_domain')
            api_key = platform_credentials.get('api_key')
            
            if not shop_domain or not api_key:
                logger.error("Missing shopify credentials")
                return None
            
            # Generate state (link_id for tracking)
            state = link_id
            
            auth_url = ShopifyConnector.get_oauth_authorization_url(
                shop_domain=shop_domain,
                api_key=api_key,
                redirect_uri=self.get_callback_url('shopify'),
                state=state
            )
            
            return auth_url
        
        elif platform == 'bigcommerce':
            client_id = platform_credentials.get('client_id')
            
            if not client_id:
                logger.error("Missing BigCommerce client_id")
                return None
            
            state = link_id
            
            auth_url = BigCommerceConnector.get_oauth_authorization_url(
                client_id=client_id,
                redirect_uri=self.get_callback_url('bigcommerce'),
                state=state
            )
            
            return auth_url
        
        else:
            logger.error(f"OAuth not supported for platform: {platform}")
            return None
    
    def handle_oauth_callback(
        self, 
        platform: str, 
        code: str, 
        state: str,
        platform_credentials: Dict[str, str]
    ) -> bool:
        """
        Handle OAuth callback and exchange code for token.
        
        Args:
            platform: Platform name
            code: Authorization code
            state: State parameter (should be link_id)
            platform_credentials: Platform-specific credentials
            
        Returns:
            True if successful, False otherwise
        """
        link_id = state
        
        # Get link info to retrieve client email
        # Note: we need to reconstruct validation here
        # In production, you'd store state securely
        
        try:
            if platform == 'shopify':
                shop_domain = platform_credentials.get('shop_domain')
                api_key = platform_credentials.get('api_key')
                api_secret = platform_credentials.get('api_secret')
                
                # Exchange code for access token
                access_token = ShopifyConnector.exchange_code_for_token(
                    shop_domain=shop_domain,
                    api_key=api_key,
                    api_secret=api_secret,
                    code=code
                )
                
                # Store credentials
                credentials = {
                    'shop_domain': shop_domain,
                    'access_token': access_token
                }
                
                # Lookup client_email from link_id
                link_info = self.magic_links.get_link_info(link_id)
                if not link_info:
                    logger.error(f"Cannot find link info for {link_id}")
                    return False
                    
                client_email = link_info.get('client_email')
                if not client_email:
                    logger.error(f"No client email in link {link_id}")
                    return False
                
                self.credentials.store_credentials(
                    client_id=client_email,
                    platform=platform,
                    credentials=credentials
                )
                
                # Mark magic link as used
                self.magic_links.mark_as_used(link_id)
                
                logger.info(f"OAuth successful for {client_email} ({platform})")
                return True
            
            elif platform == 'bigcommerce':
                client_id = platform_credentials.get('client_id')
                client_secret = platform_credentials.get('client_secret')
                
                result = BigCommerceConnector.exchange_code_for_token(
                    client_id=client_id,
                    client_secret=client_secret,
                    code=code,
                    redirect_uri=self.get_callback_url('bigcommerce')
                )
                
                credentials = {
                    'store_hash': result['store_hash'],
                    'access_token': result['access_token']
                }
                
                # Lookup client_email from link_id
                link_info = self.magic_links.get_link_info(link_id)
                if not link_info:
                    logger.error(f"Cannot find link info for {link_id}")
                    return False
                    
                client_email = link_info.get('client_email')
                if not client_email:
                    logger.error(f"No client email in link {link_id}")
                    return False
                
                self.credentials.store_credentials(
                    client_id=client_email,
                    platform=platform,
                    credentials=credentials
                )
                
                self.magic_links.mark_as_used(link_id)
                
                logger.info(f"OAuth successful for {client_email} ({platform})")
                return True
            
            else:
                logger.error(f"Unsupported platform: {platform}")
                return False
                
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return False
