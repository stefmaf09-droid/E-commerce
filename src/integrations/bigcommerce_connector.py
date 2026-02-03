"""
BigCommerce OAuth connector.

Implements OAuth 2.0 flow for BigCommerce integration.
"""

import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlencode
import logging

from .base import BaseConnector

logger = logging.getLogger(__name__)


class BigCommerceConnector(BaseConnector):
    """BigCommerce API connector with OAuth 2.0."""
    
    API_VERSION = "v2"
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize BigCommerce connector.
        
        Expected credentials keys:
        - store_hash: BigCommerce store hash
        - access_token: OAuth access token
        OR for API account:
        - client_id: API client ID
        - client_secret: API client secret
        """
        super().__init__(credentials)
        self.store_hash = credentials.get('store_hash')
        self.access_token = credentials.get('access_token')
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        
        if not self.store_hash:
            raise ValueError("store_hash is required")
        
        self.base_url = f"https://api.bigcommerce.com/stores/{self.store_hash}/{self.API_VERSION}"
        self.session = requests.Session()
        
        if self.access_token:
            self.session.headers.update({
                'X-Auth-Token': self.access_token,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        elif self.client_id and self.client_secret:
            self.session.headers.update({
                'X-Auth-Client': self.client_id,
                'X-Auth-Token': self.client_secret,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
    
    @staticmethod
    def get_oauth_authorization_url(client_id: str, redirect_uri: str, state: str) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            client_id: BigCommerce app client ID
            redirect_uri: OAuth callback URL
            state: Random state for CSRF protection
            
        Returns:
            Authorization URL
        """
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state
        }
        
        return f"https://login.bigcommerce.com/oauth2/authorize?{urlencode(params)}"
    
    @staticmethod
    def exchange_code_for_token(client_id: str, client_secret: str, code: str, redirect_uri: str) -> Dict[str, str]:
        """
        Exchange authorization code for access token.
        
        Args:
            client_id: App client ID
            client_secret: App client secret
            code: Authorization code
            redirect_uri: OAuth callback URL
            
        Returns:
            Dictionary with access_token and store_hash
        """
        url = "https://login.bigcommerce.com/oauth2/token"
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        return {
            'access_token': result['access_token'],
            'store_hash': result['context'].split('/')[1]  # Extract from "stores/{hash}"
        }
    
    def authenticate(self) -> bool:
        """Test authentication by fetching store info."""
        try:
            response = self.session.get(f"{self.base_url}/store", timeout=10)
            response.raise_for_status()
            logger.info(f"BigCommerce authentication successful for store {self.store_hash}")
            return True
        except Exception as e:
            logger.error(f"BigCommerce authentication failed: {e}")
            return False
    
    def fetch_orders(
        self, 
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from BigCommerce.
        
        Args:
            since: Fetch orders created after this date
            until: Fetch orders created before this date
            status: Order status ID
            
        Returns:
            List of normalized order dictionaries
        """
        all_orders = []
        page = 1
        limit = 250  # BigCommerce max
        
        params = {
            'limit': limit,
            'page': page
        }
        
        if since:
            params['min_date_created'] = since.strftime('%a, %d %b %Y %H:%M:%S %z')
        if until:
            params['max_date_created'] = until.strftime('%a, %d %b %Y %H:%M:%S %z')
        if status:
            params['status_id'] = status
        
        while True:
            try:
                response = self.session.get(
                    f"{self.base_url}/orders",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                orders = response.json()
                
                if not orders or not isinstance(orders, list):
                    break
                
                # Normalize each order
                for order in orders:
                    all_orders.append(self.normalize_order(order))
                
                logger.info(f"Fetched {len(orders)} orders from BigCommerce page {page} (total: {len(all_orders)})")
                
                # Check if there are more pages (if we got less than limit, we're done)
                if len(orders) < limit:
                    break
                
                page += 1
                params['page'] = page
                
            except Exception as e:
                logger.error(f"Error fetching BigCommerce orders: {e}")
                break
        
        return all_orders
    
    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific order."""
        try:
            response = self.session.get(
                f"{self.base_url}/orders/{order_id}",
                timeout=10
            )
            response.raise_for_status()
            
            order = response.json()
            return self.normalize_order(order)
            
        except Exception as e:
            logger.error(f"Error fetching BigCommerce order {order_id}: {e}")
            return {}
    
    # Normalization methods
    def _extract_order_id(self, order: Dict) -> str:
        return str(order.get('id', ''))
    
    def _extract_order_date(self, order: Dict) -> datetime:
        date_created = order.get('date_created', '')
        return datetime.strptime(date_created, '%a, %d %b %Y %H:%M:%S %z')
    
    def _extract_customer_email(self, order: Dict) -> str:
        billing_address = order.get('billing_address', {})
        return billing_address.get('email', '')
    
    def _extract_total_amount(self, order: Dict) -> float:
        return float(order.get('total_inc_tax', 0))
    
    def _extract_shipping_carrier(self, order: Dict) -> Optional[str]:
        # BigCommerce has shipping_cost_ex_tax but not always carrier
        # Sometimes in shipping_addresses
        return None  # Would need to fetch shipping quotes separately
    
    def _extract_tracking_number(self, order: Dict) -> Optional[str]:
        # Tracking numbers are in shipments
        # Would need separate API call to /orders/{id}/shipments
        return None
    
    def _extract_delivery_status(self, order: Dict) -> str:
        status_id = order.get('status_id', 0)
        
        # BigCommerce status IDs
        status_map = {
            0: 'pending',
            1: 'pending',       # Pending
            2: 'in_transit',    # Shipped
            3: 'in_transit',    # Partially Shipped
            4: 'refunded',      # Refunded
            5: 'cancelled',     # Cancelled
            6: 'cancelled',     # Declined
            7: 'pending',       # Awaiting Payment
            8: 'pending',       # Awaiting Pickup
            9: 'pending',       # Awaiting Shipment
            10: 'delivered',    # Completed
            11: 'pending',      # Awaiting Fulfillment
            12: 'pending',      # Manual Verification Required
            13: 'cancelled'     # Disputed
        }
        
        return status_map.get(status_id, 'unknown')
    
    def _extract_delivery_date(self, order: Dict) -> Optional[datetime]:
        # BigCommerce doesn't track delivery date by default
        if order.get('status_id') == 10:  # Completed
            date_modified = order.get('date_modified')
            if date_modified:
                return datetime.strptime(date_modified, '%a, %d %b %Y %H:%M:%S %z')
        return None
    
    def _extract_shipping_cost(self, order: Dict) -> float:
        return float(order.get('shipping_cost_inc_tax', 0))
    
    def _extract_shipping_address(self, order: Dict) -> Dict[str, str]:
        shipping_addresses = order.get('shipping_addresses', [])
        if shipping_addresses:
            addr = shipping_addresses[0]
            return {
                'address1': addr.get('street_1', ''),
                'address2': addr.get('street_2', ''),
                'city': addr.get('city', ''),
                'province': addr.get('state', ''),
                'country': addr.get('country', ''),
                'zip': addr.get('zip', '')
            }
        
        return {}
