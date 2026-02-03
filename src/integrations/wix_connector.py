"""
Wix eCommerce REST API connector.

Uses OAuth 2.0 or API key for authentication.
"""

import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from .base import BaseConnector

logger = logging.getLogger(__name__)


class WixConnector(BaseConnector):
    """Wix eCommerce API connector."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Wix connector.
        
        Expected credentials keys:
        - site_id: Wix site ID
        - access_token: OAuth access token or API key
        """
        super().__init__(credentials)
        self.site_id = credentials.get('site_id')
        self.access_token = credentials.get('access_token')
        
        if not all([self.site_id, self.access_token]):
            raise ValueError("site_id and access_token are required")
        
        self.base_url = "https://www.wixapis.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': self.access_token,
            'Content-Type': 'application/json'
        })
    
    def authenticate(self) -> bool:
        """Test authentication by fetching site info."""
        try:
            # Try to fetch orders with limit 1 as a test
            response = self.session.post(
                f"{self.base_url}/stores/v2/orders/query",
                json={'query': {'paging': {'limit': 1}}},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Wix authentication successful for site {self.site_id}")
            return True
        except Exception as e:
            logger.error(f"Wix authentication failed: {e}")
            return False
    
    def fetch_orders(
        self, 
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from Wix.
        
        Args:
            since: Fetch orders created after this date
            until: Fetch orders created before this date
            status: Order status (not commonly filtered)
            
        Returns:
            List of normalized order dictionaries
        """
        all_orders = []
        
        # Build query
        query_filters = []
        
        if since:
            query_filters.append({
                'dateCreated': {
                    '$gte': since.isoformat()
                }
            })
        
        if until:
            query_filters.append({
                'dateCreated': {
                    '$lte': until.isoformat()
                }
            })
        
        query = {
            'paging': {
                'limit': 100
            }
        }
        
        if query_filters:
            query['filter'] = {'$and': query_filters}
        
        cursor = None
        
        while True:
            try:
                if cursor:
                    query['paging']['cursor'] = cursor
                
                response = self.session.post(
                    f"{self.base_url}/stores/v2/orders/query",
                    json={'query': query},
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                orders = data.get('orders', [])
                
                if not orders:
                    break
                
                # Normalize each order
                for order in orders:
                    all_orders.append(self.normalize_order(order))
                
                logger.info(f"Fetched {len(orders)} orders from Wix (total: {len(all_orders)})")
                
                # Check for next page
                paging_metadata = data.get('pagingMetadata', {})
                cursor = paging_metadata.get('cursors', {}).get('next')
                
                if not cursor:
                    break
                
            except Exception as e:
                logger.error(f"Error fetching Wix orders: {e}")
                break
        
        return all_orders
    
    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific order."""
        try:
            response = self.session.get(
                f"{self.base_url}/stores/v2/orders/{order_id}",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            order = data.get('order', {})
            return self.normalize_order(order)
            
        except Exception as e:
            logger.error(f"Error fetching Wix order {order_id}: {e}")
            return {}
    
    # Normalization methods
    def _extract_order_id(self, order: Dict) -> str:
        return str(order.get('id', ''))
    
    def _extract_order_date(self, order: Dict) -> datetime:
        date_created = order.get('dateCreated', '')
        return datetime.fromisoformat(date_created.replace('Z', '+00:00'))
    
    def _extract_customer_email(self, order: Dict) -> str:
        buyer_info = order.get('buyerInfo', {})
        return buyer_info.get('email', '')
    
    def _extract_total_amount(self, order: Dict) -> float:
        pricing_summary = order.get('pricingSummary', {})
        total = pricing_summary.get('total', {})
        return float(total.get('amount', 0))
    
    def _extract_shipping_carrier(self, order: Dict) -> Optional[str]:
        fulfillment = order.get('fulfillment', {})
        tracking_info = fulfillment.get('trackingInfo', {})
        return tracking_info.get('shippingProvider')
    
    def _extract_tracking_number(self, order: Dict) -> Optional[str]:
        fulfillment = order.get('fulfillment', {})
        tracking_info = fulfillment.get('trackingInfo', {})
        return tracking_info.get('trackingNumber')
    
    def _extract_delivery_status(self, order: Dict) -> str:
        fulfillment = order.get('fulfillment', {})
        status = fulfillment.get('status', 'NOT_FULFILLED')
        
        # Wix fulfillment status mapping
        status_map = {
            'NOT_FULFILLED': 'pending',
            'PARTIALLY_FULFILLED': 'in_transit',
            'FULFILLED': 'delivered',
            'CANCELED': 'cancelled'
        }
        
        return status_map.get(status, 'pending')
    
    def _extract_delivery_date(self, order: Dict) -> Optional[datetime]:
        # Wix doesn't always track delivery date
        fulfillment = order.get('fulfillment', {})
        if fulfillment.get('status') == 'FULFILLED':
            updated_date = order.get('updatedDate')
            if updated_date:
                return datetime.fromisoformat(updated_date.replace('Z', '+00:00'))
        return None
    
    def _extract_shipping_cost(self, order: Dict) -> float:
        pricing_summary = order.get('pricingSummary', {})
        shipping = pricing_summary.get('shipping', {})
        return float(shipping.get('amount', 0))
    
    def _extract_shipping_address(self, order: Dict) -> Dict[str, str]:
        shipping_info = order.get('shippingInfo', {})
        logistics = shipping_info.get('logistics', {})
        if logistics:
            address = logistics.get('shippingDestination', {}).get('address', {})
            if address:
                return {
                    'address1': address.get('addressLine1', ''),
                    'address2': address.get('addressLine2', ''),
                    'city': address.get('city', ''),
                    'province': address.get('subdivision', ''),
                    'country': address.get('country', ''),
                    'zip': address.get('postalCode', '')
                }
        
        return {}
