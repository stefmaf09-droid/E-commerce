"""
Abstract base class for e-commerce platform connectors.

All platform-specific connectors must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Abstract base connector for e-commerce platforms."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize the connector with platform credentials.
        
        Args:
            credentials: Dictionary containing platform-specific auth credentials
        """
        self.credentials = credentials
        self.platform_name = self.__class__.__name__.replace('Connector', '')
        logger.info(f"Initializing {self.platform_name} connector")
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform.
        
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def fetch_orders(
        self, 
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from the platform.
        
        Args:
            since: Fetch orders created after this date
            until: Fetch orders created before this date
            status: Filter by order status (platform-specific)
            
        Returns:
            List of order dictionaries in standardized format
        """
        pass
    
    @abstractmethod
    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific order.
        
        Args:
            order_id: Platform-specific order identifier
            
        Returns:
            Order details dictionary
        """
        pass
    
    def normalize_order(self, raw_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert platform-specific order format to standardized format.
        
        Args:
            raw_order: Order data in platform-specific format
            
        Returns:
            Standardized order dictionary
        """
        # Standard format expected by dispute detector
        return {
            'order_id': self._extract_order_id(raw_order),
            'order_date': self._extract_order_date(raw_order),
            'customer_email': self._extract_customer_email(raw_order),
            'total_amount': self._extract_total_amount(raw_order),
            'shipping_carrier': self._extract_shipping_carrier(raw_order),
            'tracking_number': self._extract_tracking_number(raw_order),
            'delivery_status': self._extract_delivery_status(raw_order),
            'delivery_date': self._extract_delivery_date(raw_order),
            'shipping_cost': self._extract_shipping_cost(raw_order),
            'shipping_address': self._extract_shipping_address(raw_order),
            'raw_data': raw_order  # Keep original for debugging
        }
    
    @abstractmethod
    def _extract_order_id(self, order: Dict) -> str:
        """Extract order ID from platform-specific format."""
        pass
    
    @abstractmethod
    def _extract_order_date(self, order: Dict) -> datetime:
        """Extract order date from platform-specific format."""
        pass
    
    @abstractmethod
    def _extract_customer_email(self, order: Dict) -> str:
        """Extract customer email from platform-specific format."""
        pass
    
    @abstractmethod
    def _extract_total_amount(self, order: Dict) -> float:
        """Extract total amount from platform-specific format."""
        pass
    
    @abstractmethod
    def _extract_shipping_carrier(self, order: Dict) -> Optional[str]:
        """Extract shipping carrier from platform-specific format."""
        pass
    
    @abstractmethod
    def _extract_tracking_number(self, order: Dict) -> Optional[str]:
        """Extract tracking number from platform-specific format."""
        pass
    
    @abstractmethod
    def _extract_delivery_status(self, order: Dict) -> str:
        """Extract delivery status from platform-specific format."""
        pass
    
    @abstractmethod
    def _extract_delivery_date(self, order: Dict) -> Optional[datetime]:
        """Extract delivery date from platform-specific format."""
        pass
    
    @abstractmethod
    def _extract_shipping_cost(self, order: Dict) -> float:
        """Extract shipping cost from platform-specific format."""
        pass
    
    @abstractmethod
    def _extract_shipping_address(self, order: Dict) -> Dict[str, str]:
        """Extract shipping address from platform-specific format."""
        pass
    
    def test_connection(self) -> bool:
        """
        Test if the connection to the platform is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.authenticate()
            # Try to fetch just 1 order to test
            orders = self.fetch_orders()
            logger.info(f"{self.platform_name} connection test successful")
            return True
        except Exception as e:
            logger.error(f"{self.platform_name} connection test failed: {e}")
            return False
