"""
Base module for platform integrations.
"""

from .base import BaseConnector
from .shopify_connector import ShopifyConnector
from .woocommerce_connector import WooCommerceConnector
from .prestashop_connector import PrestaShopConnector
from .magento_connector import MagentoConnector
from .bigcommerce_connector import BigCommerceConnector
from .wix_connector import WixConnector

__all__ = [
    'BaseConnector',
    'ShopifyConnector',
    'WooCommerceConnector',
    'PrestaShopConnector',
    'MagentoConnector',
    'BigCommerceConnector',
    'WixConnector'
]

