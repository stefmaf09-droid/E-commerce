"""
Abstract base class for shipping carrier connectors.
Responsible for tracking packages and retrieving proof of delivery.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CarrierConnector(ABC):
    """Abstract base connector for shipping carriers."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize the connector with carrier credentials.
        
        Args:
            credentials: Dictionary containing carrier-specific auth credentials
        """
        self.credentials = credentials
        self.carrier_name = self.__class__.__name__.replace('Connector', '')
    
    @abstractmethod
    def get_tracking_details(self, tracking_number: str) -> Dict[str, Any]:
        """
        Get detailed tracking information for a package.
        
        Args:
            tracking_number: The tracking number to check
            
        Returns:
            Dictionary containing:
            - status: Standardized status (DELIVERED, IN_TRANSIT, EXCEPTION, etc.)
            - delivery_date: datetime object (if delivered)
            - events: List of tracking events
            - estimated_delivery: datetime object
            - raw_data: The original response from the carrier
        """
        pass
        
    @abstractmethod
    def get_proof_of_delivery(self, tracking_number: str) -> Optional[bytes]:
        """
        Retrieve the Proof of Delivery (POD) document (usually PDF or Image).
        
        Args:
            tracking_number: The tracking number
            
        Returns:
            Binary content of the POD or None if not available
        """
        pass
    
    def normalize_status(self, carrier_status: str) -> str:
        """
        Map carrier-specific status to standardized status.
        
        Standard statuses:
        - DELIVERED
        - IN_TRANSIT
        - EXCEPTION (Lost, Damaged, Held, etc.)
        - PENDING
        - UNKNOWN
        """
        # Default implementation, override in subclasses
        return carrier_status.upper()
