"""
PrestaShop Webservice APIconnector.

Uses API Key authentication for order retrieval.
"""

import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import xml.etree.ElementTree as ET

from .base import BaseConnector

logger = logging.getLogger(__name__)


class PrestaShopConnector(BaseConnector):
    """PrestaShop Webservice API connector."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize PrestaShop connector.
        
        Expected credentials keys:
        - store_url: PrestaShop store URL (e.g., 'https://example.com')
        - api_key: PrestaShop Webservice API key
        """
        super().__init__(credentials)
        self.store_url = credentials.get('store_url', '').rstrip('/')
        self.api_key = credentials.get('api_key')
        
        if not all([self.store_url, self.api_key]):
            raise ValueError("store_url and api_key are required")
        
        self.base_url = f"{self.store_url}/api"
        self.session = requests.Session()
        self.session.auth = (self.api_key, '')  # API key as username, empty password
    
    def authenticate(self) -> bool:
        """Test authentication by fetching shop info."""
        try:
            response = self.session.get(
                f"{self.base_url}/shops",
                params={'output_format': 'JSON'},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"PrestaShop authentication successful for {self.store_url}")
            return True
        except Exception as e:
            logger.error(f"PrestaShop authentication failed: {e}")
            return False
    
    def fetch_orders(
        self, 
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from PrestaShop.
        
        Args:
            since: Fetch orders created after this date
            until: Fetch orders created before this date
            status: Order status (not commonly used in PrestaShop filtering)
            
        Returns:
            List of normalized order dictionaries
        """
        all_orders = []
        
        params = {
            'output_format': 'JSON',
            'display': 'full'
        }
        
        # PrestaShop uses filter syntax
        filters = []
        if since:
            filters.append(f"date_add>[{since.strftime('%Y-%m-%d %H:%M:%S')}]")
        if until:
            filters.append(f"date_add<[{until.strftime('%Y-%m-%d %H:%M:%S')}]")
        
        if filters:
            params['filter[date_add]'] = ','.join(filters)
        
        try:
            response = self.session.get(
                f"{self.base_url}/orders",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            orders = data.get('orders', [])
            
            # PrestaShop returns minimal data, need to fetch each order
            for order_summary in orders:
                order_id = order_summary.get('id')
                if order_id:
                    order_detail = self.get_order_details(str(order_id))
                    if order_detail:
                        all_orders.append(order_detail)
            
            logger.info(f"Fetched {len(all_orders)} orders from PrestaShop")
            
        except Exception as e:
            logger.error(f"Error fetching PrestaShop orders: {e}")
        
        return all_orders
    
    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific order."""
        try:
            response = self.session.get(
                f"{self.base_url}/orders/{order_id}",
                params={'output_format': 'JSON', 'display': 'full'},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            order = data.get('order', {})
            return self.normalize_order(order)
            
        except Exception as e:
            logger.error(f"Error fetching PrestaShop order {order_id}: {e}")
            return {}
    
    # Normalization methods
    def _extract_order_id(self, order: Dict) -> str:
        return str(order.get('id', ''))
    
    def _extract_order_date(self, order: Dict) -> datetime:
        date_add = order.get('date_add', '')
        try:
            return datetime.strptime(date_add, '%Y-%m-%d %H:%M:%S')
        except:
            return datetime.now()
    
    def _extract_customer_email(self, order: Dict) -> str:
        # PrestaShop doesn't include email in order by default
        # Would need to fetch customer separately
        return ''
    
    def _extract_total_amount(self, order: Dict) -> float:
        return float(order.get('total_paid', 0))
    
    def _extract_shipping_carrier(self, order: Dict) -> Optional[str]:
        # Carrier name from id_carrier (would need separate API call)
        carrier_id = order.get('id_carrier')
        if carrier_id:
            return f"Carrier_{carrier_id}"  # Placeholder
        return None
    
    def _extract_tracking_number(self, order: Dict) -> Optional[str]:
        # 1. Check direct 'shipping_number' field (standard in 1.7+)
        shipping_number = order.get('shipping_number')
        if shipping_number and shipping_number != '':
            return shipping_number
            
        # 2. Check associations (if expanded) - logic could be added here
        return None
    
    def _extract_delivery_status(self, order: Dict) -> str:
        # PrestaShop uses order states
        current_state = order.get('current_state')
        
        # Common PrestaShop state IDs (may vary by shop)
        state_map = {
            '1': 'pending',       # Awaiting check payment
            '2': 'in_transit',    # Payment accepted
            '3': 'in_transit',    # Processing in progress
            '4': 'in_transit',    # Shipped
            '5': 'delivered',     # Delivered
            '6': 'cancelled',     # Canceled
            '7': 'refunded'       # Refunded
        }
        
        return state_map.get(str(current_state), 'unknown')
    
    def _extract_delivery_date(self, order: Dict) -> Optional[datetime]:
        delivery_date = order.get('delivery_date')
        if delivery_date and delivery_date != '0000-00-00 00:00:00':
            try:
                return datetime.strptime(delivery_date, '%Y-%m-%d %H:%M:%S')
            except:
                pass
        return None
    
    def _extract_shipping_cost(self, order: Dict) -> float:
        return float(order.get('total_shipping', 0))
    
    def _extract_shipping_address(self, order: Dict) -> Dict[str, str]:
        # PrestaShop requires separate call to get address
        # This is a simplified version
        return {
            'address1': '',
            'address2': '',
            'city': '',
            'province': '',
            'country': '',
            'zip': ''
        }
