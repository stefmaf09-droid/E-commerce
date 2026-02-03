"""
Helper functions for client photo management.
"""

import os
from typing import List
import shutil


def get_client_photos(order_id: str) -> List[str]:
    """
    Get list of client photos for an order.
    
    Args:
        order_id: Order ID
        
    Returns:
        List of photo file paths
    """
    photos_dir = f"data/client_photos/{order_id}"
    
    if not os.path.exists(photos_dir):
        return []
    
    photos = []
    for filename in os.listdir(photos_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            photos.append(os.path.join(photos_dir, filename))
    
    return photos


def has_client_photos(order_id: str) -> bool:
    """Check if client has uploaded photos for an order."""
    return len(get_client_photos(order_id)) > 0


def delete_client_photo(order_id: str, filename: str) -> bool:
    """
    Delete a specific client photo.
    
    Args:
        order_id: Order ID
        filename: Photo filename
        
    Returns:
        True if deleted, False otherwise
    """
    photo_path = f"data/client_photos/{order_id}/{filename}"
    
    if os.path.exists(photo_path):
        os.remove(photo_path)
        return True
    
    return False


def cleanup_order_photos(order_id: str):
    """Delete all photos for an order."""
    photos_dir = f"data/client_photos/{order_id}"
    
    if os.path.exists(photos_dir):
        shutil.rmtree(photos_dir)


# Test
if __name__ == "__main__":
    print("="*70)
    print("CLIENT PHOTOS HELPER - Test")
    print("="*70)
    
    # Create test directory
    test_order = "ORD-TEST-123"
    os.makedirs(f"data/client_photos/{test_order}", exist_ok=True)
    
    # Create dummy file
    with open(f"data/client_photos/{test_order}/test_photo.jpg", 'w') as f:
        f.write("dummy")
    
    # Test functions
    photos = get_client_photos(test_order)
    print(f"\n✅ Photos found: {len(photos)}")
    
    has_photos = has_client_photos(test_order)
    print(f"✅ Has photos: {has_photos}")
    
    # Cleanup
    cleanup_order_photos(test_order)
    print(f"✅ Cleanup done")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
