"""
Multi-store support utilities.

Helps manage clients with multiple e-commerce stores.
"""

import json
import os
from typing import List, Dict, Optional


def get_client_stores(client_email: str, credentials_manager) -> List[Dict]:
    """
    Get all stores for a client.
    
    Args:
        client_email: Client email
        credentials_manager: CredentialsManager instance
        
    Returns:
        List of store dictionaries with platform, name, etc.
    """
    all_creds = credentials_manager._load_credentials()
    
    stores = []
    
    if client_email in all_creds:
        for platform, creds in all_creds[client_email].items():
            store_name = creds.get('shop_url', creds.get('store_name', f'{platform.capitalize()} Store'))
            
            stores.append({
                'platform': platform,
                'name': store_name,
                'credentials': creds,
                'display_name': f"{store_name} ({platform.capitalize()})"
            })
    
    return stores


def get_platform_icon(platform: str) -> str:
    """Get emoji icon for platform."""
    icons = {
        'shopify': '🛍️',
        'woocommerce': '🛒',
        'prestashop': '💼',
        'magento': '🏬',
        'bigcommerce': '🏪',
        'wix': '✨'
    }
    return icons.get(platform.lower(), '🏪')


def get_platform_color(platform: str) -> str:
    """Get color hex for platform."""
    colors = {
        'shopify': '#96bf48',
        'woocommerce': '#96588a',
        'prestashop': '#df0067',
        'magento': '#f26322',
        'bigcommerce': '#1a1a1a',
        'wix': '#0c6ebd'
    }
    return colors.get(platform.lower(), '#6366f1')


# Test
if __name__ == "__main__":
    print("="*70)
    print("MULTI-STORE UTILITIES - Test")
    print("="*70)
    
    # Test icons
    for platform in ['shopify', 'woocommerce', 'prestashop']:
        icon = get_platform_icon(platform)
        color = get_platform_color(platform)
        print(f"{icon} {platform.capitalize()}: {color}")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
