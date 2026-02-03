"""
Shopify OAuth connector.

Implements OAuth 2.0 flow for Shopify integration and order retrieval.
"""

import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlencode
import logging

from .base import BaseConnector

logger = logging.getLogger(__name__)


class ShopifyConnector(BaseConnector):
    """Shopify API connector with OAuth 2.0."""
    
    # Shopify API version
    API_VERSION = "2024-01"
    
    # Required scopes for order access
    SCOPES = "read_orders,read_shipping,read_fulfillments"
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Shopify connector.
        
        Expected credentials keys:
        - shop_domain: Shopify shop domain (e.g., 'myshop.myshopify.com')
        - access_token: OAuth access token (obtained after OAuth flow)
        OR for OAuth flow:
        - api_key: Shopify app API key
        - api_secret: Shopify app API secret
        """
        super().__init__(credentials)
        self.shop_domain = credentials.get('shop_domain')
        self.access_token = credentials.get('access_token')
        self.api_key = credentials.get('api_key')
        self.api_secret = credentials.get('api_secret')
        
        if not self.shop_domain:
            raise ValueError("shop_domain is required")
        
        # Ensure shop_domain has .myshopify.com
        if not self.shop_domain.endswith('.myshopify.com'):
            self.shop_domain = f"{self.shop_domain}.myshopify.com"
        
        self.base_url = f"https://{self.shop_domain}/admin/api/{self.API_VERSION}"
        self.session = requests.Session()
        
        if self.access_token:
            self.session.headers.update({
                'X-Shopify-Access-Token': self.access_token,
                'Content-Type': 'application/json'
            })
    
    @staticmethod
    def get_oauth_authorization_url(shop_domain: str, api_key: str, redirect_uri: str, state: str) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            shop_domain: Shopify shop domain
            api_key: App API key
            redirect_uri: OAuth callback URL
            state: Random state for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        if not shop_domain.endswith('.myshopify.com'):
            shop_domain = f"{shop_domain}.myshopify.com"
        
        params = {
            'client_id': api_key,
            'scope': ShopifyConnector.SCOPES,
            'redirect_uri': redirect_uri,
            'state': state
        }
        
        return f"https://{shop_domain}/admin/oauth/authorize?{urlencode(params)}"
    
    @staticmethod
    def exchange_code_for_token(shop_domain: str, api_key: str, api_secret: str, code: str) -> str:
        """
        Exchange authorization code for access token.
        
        Args:
            shop_domain: Shopify shop domain
            api_key: App API key
            api_secret: App API secret
            code: Authorization code from OAuth callback
            
        Returns:
            Access token
        """
        if not shop_domain.endswith('.myshopify.com'):
            shop_domain = f"{shop_domain}.myshopify.com"
        
        url = f"https://{shop_domain}/admin/oauth/access_token"
        data = {
            'client_id': api_key,
            'client_secret': api_secret,
            'code': code
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result['access_token']
    
    def authenticate(self) -> bool:
        """Test authentication by making a simple API call."""
        try:
            response = self.session.get(f"{self.base_url}/shop.json")
            response.raise_for_status()
            logger.info(f"Shopify authenticationsuccesful for {self.shop_domain}")
            return True
        except Exception as e:
            logger.error(f"Shopify authentication failed: {e}")
            return False
    
    def fetch_orders(
self, 
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from Shopify.
        
        Args:
            since: Fetch orders created after this date
            until: Fetch orders created before this date
            status: Order status (any, open, closed, cancelled)
            
        Returns:
            List of normalized order dictionaries
        """
        all_orders = []
        params = {
            'limit': 250,  # Max allowed by Shopify
            'status': status or 'any'
        }
        
        if since:
            params['created_at_min'] = since.isoformat()
        if until:
            params['created_at_max'] = until.isoformat()
        
        url = f"{self.base_url}/orders.json"
        
        while url:
            try:
                response = self.session.get(url, params=params if url == f"{self.base_url}/orders.json" else None)
                response.raise_for_status()
                
                data = response.json()
                orders = data.get('orders', [])
                
                # Normalize each order
                for order in orders:
                    all_orders.append(self.normalize_order(order))
                
                # Check for pagination (Link header)
                link_header = response.headers.get('Link', '')
                url = self._extract_next_page_url(link_header)
                params = None  # Don't send params for paginated requests
                
                logger.info(f"Fetched {len(orders)} orders from Shopify (total: {len(all_orders)})")
                
            except Exception as e:
                logger.error(f"Error fetching Shopify orders: {e}")
                break
        
        return all_orders
    
    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific order."""
        try:
            response = self.session.get(f"{self.base_url}/orders/{order_id}.json")
            response.raise_for_status()
            
            data = response.json()
            return self.normalize_order(data['order'])
            
        except Exception as e:
            logger.error(f"Error fetching Shopify order {order_id}: {e}")
            return {}
    
    def _extract_next_page_url(self, link_header: str) -> Optional[str]:
        """Extract next page URL from Link header."""
        if not link_header:
            return None
        
        links = link_header.split(',')
        for link in links:
            if 'rel="next"' in link:
                url = link.split(';')[0].strip('<> ')
                return url
        
        return None
    
    # Normalization methods
    def _extract_order_id(self, order: Dict) -> str:
        return str(order.get('id', ''))
    
    def _extract_order_date(self, order: Dict) -> datetime:
        created_at = order.get('created_at', '')
        return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    
    def _extract_customer_email(self, order: Dict) -> str:
        return order.get('email', '') or order.get('contact_email', '')
    
    def _extract_total_amount(self, order: Dict) -> float:
        return float(order.get('total_price', 0))
    
    def _extract_shipping_carrier(self, order: Dict) -> Optional[str]:
        # Check fulfillments for carrier info
        fulfillments = order.get('fulfillments', [])
        if fulfillments and len(fulfillments) > 0:
            tracking_company = fulfillments[0].get('tracking_company')
            if tracking_company:
                return tracking_company
        
        # Fallback to shipping lines
        shipping_lines = order.get('shipping_lines', [])
        if shipping_lines and len(shipping_lines) > 0:
            return shipping_lines[0].get('title', '')
        
        return None
    
    def _extract_tracking_number(self, order: Dict) -> Optional[str]:
        fulfillments = order.get('fulfillments', [])
        if fulfillments and len(fulfillments) > 0:
            tracking_number = fulfillments[0].get('tracking_number')
            return tracking_number
        return None
    
    def _extract_delivery_status(self, order: Dict) -> str:
        fulfillment_status = order.get('fulfillment_status')
        
        if not fulfillment_status:
            return 'pending'
        elif fulfillment_status == 'fulfilled':
            return 'delivered'
        elif fulfillment_status == 'partial':
            return 'in_transit'
        else:
            return fulfillment_status
    
    def _extract_delivery_date(self, order: Dict) -> Optional[datetime]:
        fulfillments = order.get('fulfillments', [])
        if fulfillments and len(fulfillments) > 0:
            updated_at = fulfillments[0].get('updated_at')
            if updated_at:
                return datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        return None
    
    def _extract_shipping_cost(self, order: Dict) -> float:
        shipping_lines = order.get('shipping_lines', [])
        if shipping_lines and len(shipping_lines) > 0:
            return float(shipping_lines[0].get('price', 0))
        return 0.0
    
    def _extract_shipping_address(self, order: Dict) -> Dict[str, str]:
        shipping_address = order.get('shipping_address', {})
        if not shipping_address:
            return {}
        
        return {
            'address1': shipping_address.get('address1', ''),
            'address2': shipping_address.get('address2', ''),
            'city': shipping_address.get('city', ''),
            'province': shipping_address.get('province', ''),
            'country': shipping_address.get('country', ''),
            'zip': shipping_address.get('zip', '')
        }
