"""
WooCommerce REST API connector.

Uses Consumer Key/Secret authentication for order retrieval.
"""

import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from .base import BaseConnector

logger = logging.getLogger(__name__)


class WooCommerceConnector(BaseConnector):
    """WooCommerce REST API connector."""
    
    API_VERSION = "wc/v3"
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize WooCommerce connector.
        
        Expected credentials keys:
        - store_url: WooCommerce store URL (e.g., 'https://example.com')
        - consumer_key: WooCommerce Consumer Key
        - consumer_secret: WooCommerce Consumer Secret
        """
        super().__init__(credentials)
        self.store_url = credentials.get('store_url', '').rstrip('/')
        self.consumer_key = credentials.get('consumer_key')
        self.consumer_secret = credentials.get('consumer_secret')
        
        if not all([self.store_url, self.consumer_key, self.consumer_secret]):
            raise ValueError("store_url, consumer_key, and consumer_secret are required")
        
        self.base_url = f"{self.store_url}/wp-json/{self.API_VERSION}"
        self.auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)
    
    def authenticate(self) -> bool:
        """Test authentication by fetching system status."""
        try:
            response = requests.get(
                f"{self.base_url}/system_status",
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"WooCommerce authentication successful for {self.store_url}")
            return True
        except Exception as e:
            logger.error(f"WooCommerce authentication failed: {e}")
            return False
    
    def fetch_orders(
        self, 
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from WooCommerce.
        
        Args:
            since: Fetch orders created after this date
            until: Fetch orders created before this date
            status: Order status (pending, processing, completed, etc.)
            
        Returns:
            List of normalized order dictionaries
        """
        all_orders = []
        page = 1
        per_page = 100  # WooCommerce max
        
        params = {
            'per_page': per_page,
            'page': page
        }
        
        if since:
            params['after'] = since.isoformat()
        if until:
            params['before'] = until.isoformat()
        if status:
            params['status'] = status
        
        while True:
            try:
                response = requests.get(
                    f"{self.base_url}/orders",
                    params=params,
                    auth=self.auth,
                    timeout=30
                )
                response.raise_for_status()
                
                orders = response.json()
                
                if not orders:
                    break
                
                # Normalize each order
                for order in orders:
                    all_orders.append(self.normalize_order(order))
                
                logger.info(f"Fetched {len(orders)} orders from WooCommerce page {page} (total: {len(all_orders)})")
                
                # Check if there are more pages
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                
                page += 1
                params['page'] = page
                
            except Exception as e:
                logger.error(f"Error fetching WooCommerce orders: {e}")
                break
        
        return all_orders
    
    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific order."""
        try:
            response = requests.get(
                f"{self.base_url}/orders/{order_id}",
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            
            order = response.json()
            return self.normalize_order(order)
            
        except Exception as e:
            logger.error(f"Error fetching WooCommerce order {order_id}: {e}")
            return {}
    
    # Normalization methods
    def _extract_order_id(self, order: Dict) -> str:
        return str(order.get('id', ''))
    
    def _extract_order_date(self, order: Dict) -> datetime:
        date_created = order.get('date_created', '')
        return datetime.fromisoformat(date_created.replace('Z', '+00:00'))
    
    def _extract_customer_email(self, order: Dict) -> str:
        billing = order.get('billing', {})
        return billing.get('email', '')
    
    def _extract_total_amount(self, order: Dict) -> float:
        return float(order.get('total', 0))
    
    def _extract_shipping_carrier(self, order: Dict) -> Optional[str]:
        # WooCommerce doesn't standardize carrier info
        # Check shipping lines for carrier name
        shipping_lines = order.get('shipping_lines', [])
        if shipping_lines and len(shipping_lines) > 0:
            method_title = shipping_lines[0].get('method_title', '')
            return method_title if method_title else None
        return None
    
    def _extract_tracking_number(self, order: Dict) -> Optional[str]:
        # Tracking usually comes from plugins (WooCommerce Shipment Tracking)
        # Check meta_data for common tracking fields
        meta_data = order.get('meta_data', [])
        for meta in meta_data:
            key = meta.get('key', '').lower()
            if 'tracking' in key or 'track_number' in key:
                return meta.get('value', '')
        return None
    
    def _extract_delivery_status(self, order: Dict) -> str:
        wc_status = order.get('status', 'pending')
        
        # Map WooCommerce status to our standard
        status_map = {
            'pending': 'pending',
            'processing': 'in_transit',
            'on-hold': 'pending',
            'completed': 'delivered',
            'cancelled': 'cancelled',
            'refunded': 'cancelled',
            'failed': 'failed'
        }
        
        return status_map.get(wc_status, wc_status)
    
    def _extract_delivery_date(self, order: Dict) -> Optional[datetime]:
        # WooCommerce doesn't track delivery date by default
        # Check if order is completed
        if order.get('status') == 'completed':
            date_completed = order.get('date_completed')
            if date_completed:
                return datetime.fromisoformat(date_completed.replace('Z', '+00:00'))
        return None
    
    def _extract_shipping_cost(self, order: Dict) -> float:
        return float(order.get('shipping_total', 0))
    
    def _extract_shipping_address(self, order: Dict) -> Dict[str, str]:
        shipping = order.get('shipping', {})
        if not shipping:
            return {}
        
        return {
            'address1': shipping.get('address_1', ''),
            'address2': shipping.get('address_2', ''),
            'city': shipping.get('city', ''),
            'province': shipping.get('state', ''),
            'country': shipping.get('country', ''),
            'zip': shipping.get('postcode', '')
        }
