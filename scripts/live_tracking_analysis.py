#!/usr/bin/env python3
"""
Script to demonstrate live API tracking updates replacing static CSV analysis.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.carrier_factory import CarrierFactory
from src.integrations.carrier_base import CarrierConnector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_tracking_live(orders_data: list):
    """
    Analyze orders using live tracking data from carrier APIs.
    """
    results = []
    
    logger.info(f"Starting live analysis for {len(orders_data)} orders...")
    
    for order in orders_data:
        tracking_number = order['tracking_number']
        carrier_name = order['carrier']
        
        try:
            # 1. Get Connector
            connector = CarrierFactory.get_connector(carrier_name)
            
            # 2. Fetch Live Details
            details = connector.get_tracking_details(tracking_number)
            
            # 3. Analyze (Simplified Logic for Demo)
            status = details.get('status')
            delivery_date = details.get('delivery_date')
            
            analysis = {
                'order_id': order['order_id'],
                'carrier': carrier_name,
                'tracking_number': tracking_number,
                'live_status': status,
                'delivery_date': delivery_date,
                'is_late': False,
                'is_lost': False,
                'action_needed': 'None'
            }
            
            if status == 'EXCEPTION' or (status == 'IN_TRANSIT' and "LOST" in tracking_number):
                analysis['is_lost'] = True
                analysis['action_needed'] = 'File Lost Claim'
            elif status == 'DELIVERED':
                 # Check for lateness (mock logic: if delivered > 3 days after shipping)
                 # In real app, compare delivery_date with shipping_date + SLA
                 pass
            
            # Mock Logic for 'LATE' in tracking number (from ColissimoConnector)
            if "LATE" in tracking_number:
                analysis['is_late'] = True
                analysis['action_needed'] = 'File Late Delivery Claim'

            results.append(analysis)
            logger.info(f"Analyzed {tracking_number}: {status} -> {analysis['action_needed']}")
            
        except Exception as e:
            logger.error(f"Error processing {tracking_number}: {e}")
            
    return pd.DataFrame(results)

def main():
    # Sample Data (Replacing the CSV input)
    orders_sample = [
        {'order_id': 'ORD-001', 'carrier': 'DHL', 'tracking_number': 'DHL123456789'},
        {'order_id': 'ORD-002', 'carrier': 'Colissimo', 'tracking_number': '88888888888888'}, # Standard
        {'order_id': 'ORD-003', 'carrier': 'Colissimo', 'tracking_number': '8LATE123456'},    # Simulate Late
        {'order_id': 'ORD-004', 'carrier': 'Colissimo', 'tracking_number': '8LOST987654'},    # Simulate Lost
    ]
    
    print("="*60)
    print("🚀 LIVE TRACKING ANALYSIS DEMO")
    print("="*60)
    
    df = analyze_tracking_live(orders_sample)
    
    print("\n📊 ANALYSIS RESULTS:")
    print(df.to_string(index=False))
    
    print("\n✅ Live tracking integration demonstrated.")
    print("   The system now uses CarrierConnectors to fetch real-time status")
    print("   instead of relying on static CSV columns.")

if __name__ == "__main__":
    main()
