"""
Custom carrier management for disputes.

Allows clients to add manual/custom carriers not in the standard list.
"""

import json
import os
from pathlib import Path
from typing import List, Dict


class CustomCarrierManager:
    """Manage custom carriers per client."""
    
    def __init__(self, data_file: str = "data/custom_carriers.json"):
        """Initialize carrier manager."""
        self.data_file = data_file
        Path(data_file).parent.mkdir(parents=True, exist_ok=True)
        
        if not os.path.exists(data_file):
            with open(data_file, 'w') as f:
                json.dump({}, f)
    
    def get_carriers(self, client_email: str) -> List[Dict]:
        """Get all custom carriers for a client."""
        with open(self.data_file, 'r') as f:
            data = json.load(f)
        
        return data.get(client_email, [])
    
    def add_carrier(self, client_email: str, carrier_name: str, carrier_info: Dict = None) -> bool:
        """Add a custom carrier for a client."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            if client_email not in data:
                data[client_email] = []
            
            # Check if carrier already exists
            if any(c['name'].lower() == carrier_name.lower() for c in data[client_email]):
                return False
            
            carrier = {
                'name': carrier_name,
                'type': 'custom',
                'info': carrier_info or {}
            }
            
            data[client_email].append(carrier)
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error adding carrier: {e}")
            return False
    
    def delete_carrier(self, client_email: str, carrier_name: str) -> bool:
        """Delete a custom carrier."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            if client_email in data:
                data[client_email] = [c for c in data[client_email] if c['name'] != carrier_name]
                
                with open(self.data_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                return True
            return False
        except Exception as e:
            print(f"Error deleting carrier: {e}")
            return False
    
    def get_all_carriers(self, client_email: str) -> List[str]:
        """Get all carriers (standard + custom) for a client."""
        # Standard carriers
        standard = [
            'Colissimo',
            'Chronopost', 
            'Mondial Relay',
            'DPD',
            'UPS',
            'DHL',
            'GLS',
            'Colis Privé',
            'Relais Colis'
        ]
        
        # Custom carriers
        custom = [c['name'] for c in self.get_carriers(client_email)]
        
        return standard + custom


# Test
if __name__ == "__main__":  # pragma: no cover
    print("="*70)
    print("CUSTOM CARRIER MANAGER - Test")
    print("="*70)
    
    manager = CustomCarrierManager()
    
    # Test add
    email = "test@example.com"
    manager.add_carrier(email, "Transport Local Parisien", {'phone': '01 23 45 67 89'})
    manager.add_carrier(email, "Coursier Express Lyon")
    
    # Get all carriers
    all_carriers = manager.get_all_carriers(email)
    
    print(f"\n✅ Carriers for {email}: {len(all_carriers)}")
    print("\nStandard carriers:")
    for i, carrier in enumerate(all_carriers[:9], 1):
        print(f"  {i}. {carrier}")
    
    print("\nCustom carriers:")
    custom = manager.get_carriers(email)
    for i, carrier in enumerate(custom, 1):
        print(f"  {i}. {carrier['name']}")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
