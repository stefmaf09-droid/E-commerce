"""
Magento (Adobe Commerce) REST API connector.

Uses OAuth 2.0 or Admin Token for authentication.
"""

import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from .base import BaseConnector

logger = logging.getLogger(__name__)


class MagentoConnector(BaseConnector):
    """Magento REST API connector."""
    
    API_VERSION = "V1"
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Magento connector.
        
        Expected credentials keys:
        - store_url: Magento store URL (e.g., 'https://example.com')
        - access_token: Admin token or OAuth access token
        OR
        - username: Admin username
        - password: Admin password (for token generation)
        """
        super().__init__(credentials)
        self.store_url = credentials.get('store_url', '').rstrip('/')
        self.access_token = credentials.get('access_token')
        self.username = credentials.get('username')
        self.password = credentials.get('password')
        
        if not self.store_url:
            raise ValueError("store_url is required")
        
        self.base_url = f"{self.store_url}/rest/{self.API_VERSION}"
        self.session = requests.Session()
        
        # If access_token not provided, generate it
        if not self.access_token and self.username and self.password:
            self.access_token = self._generate_admin_token()
        
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            })
    
    def _generate_admin_token(self) -> str:
        """Generate admin token using username/password."""
        try:
            response = requests.post(
                f"{self.base_url}/integration/admin/token",
                json={
                    'username': self.username,
                    'password': self.password
                },
                timeout=10
            )
            response.raise_for_status()
            token = response.json()
            logger.info("Magento admin token generated successfully")
            return token
        except Exception as e:
            logger.error(f"Failed to generate Magento admin token: {e}")
            raise
    
    def authenticate(self) -> bool:
        """Test authentication by fetching store config."""
        try:
            response = self.session.get(
                f"{self.base_url}/store/storeConfigs",
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Magento authentication successful for {self.store_url}")
            return True
        except Exception as e:
            logger.error(f"Magento authentication failed: {e}")
            return False
    
    def fetch_orders(
        self, 
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from Magento.
        
        Args:
            since: Fetch orders created after this date
            until: Fetch orders created before this date
            status: Order status
            
        Returns:
            List of normalized order dictionaries
        """
        all_orders = []
        page = 1
        page_size = 100
        
        # Build search criteria
        search_criteria = []
        filter_group_index = 0
        
        if since:
            search_criteria.append(
                f"searchCriteria[filter_groups][{filter_group_index}][filters][0][field]=created_at"
            )
            search_criteria.append(
                f"searchCriteria[filter_groups][{filter_group_index}][filters][0][value]={since.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            search_criteria.append(
                f"searchCriteria[filter_groups][{filter_group_index}][filters][0][condition_type]=gteq"
            )
            filter_group_index += 1
        
        if until:
            search_criteria.append(
                f"searchCriteria[filter_groups][{filter_group_index}][filters][0][field]=created_at"
            )
            search_criteria.append(
                f"searchCriteria[filter_groups][{filter_group_index}][filters][0][value]={until.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            search_criteria.append(
                f"searchCriteria[filter_groups][{filter_group_index}][filters][0][condition_type]=lteq"
            )
            filter_group_index += 1
        
        if status:
            search_criteria.append(
                f"searchCriteria[filter_groups][{filter_group_index}][filters][0][field]=status"
            )
            search_criteria.append(
                f"searchCriteria[filter_groups][{filter_group_index}][filters][0][value]={status}"
            )
            search_criteria.append(
                f"searchCriteria[filter_groups][{filter_group_index}][filters][0][condition_type]=eq"
            )
        
        while True:
            try:
                # Add pagination
                params_list = search_criteria + [
                    f"searchCriteria[currentPage]={page}",
                    f"searchCriteria[pageSize]={page_size}"
                ]
                
                params = '&'.join(params_list)
                
                response = self.session.get(
                    f"{self.base_url}/orders?{params}",
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                orders = data.get('items', [])
                
                if not orders:
                    break
                
                # Normalize each order
                for order in orders:
                    all_orders.append(self.normalize_order(order))
                
                logger.info(f"Fetched {len(orders)} orders from Magento page {page} (total: {len(all_orders)})")
                
                # Check if there are more pages
                total_count = data.get('total_count', 0)
                if len(all_orders) >= total_count:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching Magento orders: {e}")
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
            logger.error(f"Error fetching Magento order {order_id}: {e}")
            return {}
    
    # Normalization methods
    def _extract_order_id(self, order: Dict) -> str:
        return str(order.get('entity_id', ''))
    
    def _extract_order_date(self, order: Dict) -> datetime:
        created_at = order.get('created_at', '')
        return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    
    def _extract_customer_email(self, order: Dict) -> str:
        return order.get('customer_email', '')
    
    def _extract_total_amount(self, order: Dict) -> float:
        return float(order.get('grand_total', 0))
    
    def _extract_shipping_carrier(self, order: Dict) -> Optional[str]:
        extension_attributes = order.get('extension_attributes', {})
        shipping_assignments = extension_attributes.get('shipping_assignments', [])
        
        if shipping_assignments:
            shipping = shipping_assignments[0].get('shipping', {})
            method = shipping.get('method', '')
            if method:
                return method
        
        return order.get('shipping_description')
    
    def _extract_tracking_number(self, order: Dict) -> Optional[str]:
        extension_attributes = order.get('extension_attributes', {})
        shipping_assignments = extension_attributes.get('shipping_assignments', [])
        
        if shipping_assignments:
            shipping = shipping_assignments[0].get('shipping', {})
            # Tracking info might be in extension_attributes
            tracks = shipping.get('tracks', [])
            if tracks:
                return tracks[0].get('track_number')
        
        return None
    
    def _extract_delivery_status(self, order: Dict) -> str:
        status = order.get('status', '')
        
        # Magento status mapping
        status_map = {
            'pending': 'pending',
            'processing': 'in_transit',
            'complete': 'delivered',
            'closed': 'delivered',
            'canceled': 'cancelled',
            'holded': 'pending'
        }
        
        return status_map.get(status, status)
    
    def _extract_delivery_date(self, order: Dict) -> Optional[datetime]:
        # Magento doesn't track delivery date by default
        if order.get('status') in ['complete', 'closed']:
            updated_at = order.get('updated_at')
            if updated_at:
                return datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        return None
    
    def _extract_shipping_cost(self, order: Dict) -> float:
        return float(order.get('shipping_amount', 0))
    
    def _extract_shipping_address(self, order: Dict) -> Dict[str, str]:
        extension_attributes = order.get('extension_attributes', {})
        shipping_assignments = extension_attributes.get('shipping_assignments', [])
        
        if shipping_assignments:
            address = shipping_assignments[0].get('shipping', {}).get('address', {})
            if address:
                return {
                    'address1': ' '.join(address.get('street', [])),
                    'address2': '',
                    'city': address.get('city', ''),
                    'province': address.get('region', ''),
                    'country': address.get('country_id', ''),
                    'zip': address.get('postcode', '')
                }
        
        return {}
