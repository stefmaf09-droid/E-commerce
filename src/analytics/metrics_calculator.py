"""
Analytics - Metrics Calculator

Calculates advanced KPIs and statistics for the recovery system.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import random

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculate advanced metrics and KPIs for recovery analytics."""
    
    def __init__(self):
        """Initialize metrics calculator."""
        self.metrics_cache = {}
        logger.info("MetricsCalculator initialized")
    
    def calculate_kpis(self, disputes: List[Dict]) -> Dict:
        """
        Calculate key performance indicators.
        
        Args:
            disputes: List of dispute dictionaries
            
        Returns:
            Dictionary with KPIs
        """
        if not disputes:
            return self._empty_kpis()
        
        df = pd.DataFrame(disputes)
        
        # Convert dates if string
        if 'submitted_at' in df.columns:
            df['submitted_at'] = pd.to_datetime(df['submitted_at'], errors='coerce')
        
        kpis = {
            'total_claims': len(df),
            'success_rate': self._calculate_success_rate(df),
            'average_processing_time': self._calculate_avg_processing_time(df),
            'total_recovered': self._calculate_total_recovered(df),
            'average_claim_value': self._calculate_avg_claim_value(df),
            'roi_client': self._calculate_roi(df),
            'by_carrier': self._calculate_by_carrier(df),
            'by_status': self._calculate_by_status(df)
        }
        
        return kpis
    
    def _calculate_success_rate(self, df: pd.DataFrame) -> float:
        """Calculate success rate (accepted claims / total)."""
        if 'status' not in df.columns or len(df) == 0:
            return 0.0
        
        success_statuses = ['accepted', 'recovered', 'paid', 'success']
        successful = df[df['status'].str.lower().isin(success_statuses)]
        
        return (len(successful) / len(df)) * 100
    
    def _calculate_avg_processing_time(self, df: pd.DataFrame) -> float:
        """Calculate average processing time in days."""
        if 'submitted_at' not in df.columns or 'resolved_at' not in df.columns:
            return 5.0  # Default estimate
        
        df_resolved = df.dropna(subset=['resolved_at'])
        
        if len(df_resolved) == 0:
            return 5.0
        
        df_resolved['resolved_at'] = pd.to_datetime(df_resolved['resolved_at'], errors='coerce')
        df_resolved['processing_days'] = (df_resolved['resolved_at'] - df_resolved['submitted_at']).dt.days
        
        return df_resolved['processing_days'].mean()
    
    def _calculate_total_recovered(self, df: pd.DataFrame) -> float:
        """Calculate total amount recovered."""
        if 'amount_recovered' in df.columns:
            return df['amount_recovered'].sum()
        
        # Fallback: estimate from claim values
        if 'claim_value' in df.columns and 'status' in df.columns:
            success_statuses = ['accepted', 'recovered', 'paid']
            successful = df[df['status'].str.lower().isin(success_statuses)]
            return successful['claim_value'].sum()
        
        return 0.0
    
    def _calculate_avg_claim_value(self, df: pd.DataFrame) -> float:
        """Calculate average claim value."""
        if 'claim_value' in df.columns:
            return df['claim_value'].mean()
        return 0.0
    
    def _calculate_roi(self, df: pd.DataFrame) -> float:
        """Calculate ROI for client (money recovered / time invested)."""
        total_recovered = self._calculate_total_recovered(df)
        
        # Assume each claim takes 10 min of client time at setup
        # Then fully automated (0 time)
        setup_time_hours = (len(df) * 10) / 60  # minutes to hours
        
        # Value of time: €30/hour assumption
        time_value = setup_time_hours * 30
        
        if time_value == 0:
            return 0.0
        
        roi = ((total_recovered - time_value) / time_value) * 100
        return max(roi, 0)  # Can't be negative in our model
    
    def _calculate_by_carrier(self, df: pd.DataFrame) -> Dict:
        """Calculate metrics by carrier."""
        if 'carrier' not in df.columns:
            return {}
        
        carriers = df.groupby('carrier').agg({
            'claim_value': ['count', 'mean', 'sum'],
            'status': lambda x: (x.str.lower().isin(['accepted', 'recovered'])).sum()
        }).to_dict()
        
        # Reformat
        result = {}
        for carrier in df['carrier'].unique():
            carrier_df = df[df['carrier'] == carrier]
            result[carrier] = {
                'count': len(carrier_df),
                'avg_value': carrier_df['claim_value'].mean() if 'claim_value' in carrier_df.columns else 0,
                'total_value': carrier_df['claim_value'].sum() if 'claim_value' in carrier_df.columns else 0,
                'success_rate': self._calculate_success_rate(carrier_df)
            }
        
        return result
    
    def _calculate_by_status(self, df: pd.DataFrame) -> Dict:
        """Calculate distribution by status."""
        if 'status' not in df.columns:
            return {}
        
        status_counts = df['status'].value_counts().to_dict()
        return status_counts
    
    def _empty_kpis(self) -> Dict:
        """Return empty KPIs structure."""
        return {
            'total_claims': 0,
            'success_rate': 0.0,
            'average_processing_time': 0.0,
            'total_recovered': 0.0,
            'average_claim_value': 0.0,
            'roi_client': 0.0,
            'by_carrier': {},
            'by_status': {}
        }
    
    def get_temporal_evolution(
        self,
        disputes: List[Dict],
        period_days: int = 30
    ) -> Dict:
        """
        Get temporal evolution of claims and recoveries.
        
        Args:
            disputes: List of disputes
            period_days: Time period (30, 90, 365)
            
        Returns:
            Dictionary with daily data for charts
        """
        if not disputes:
            return {'dates': [], 'claims': [], 'amounts': [], 'cumulative': []}
        
        df = pd.DataFrame(disputes)
        
        if 'submitted_at' not in df.columns:
            return {'dates': [], 'claims': [], 'amounts': [], 'cumulative': []}
        
        df['submitted_at'] = pd.to_datetime(df['submitted_at'], errors='coerce')
        df = df.dropna(subset=['submitted_at'])
        
        # Filter to period
        cutoff_date = datetime.now() - timedelta(days=period_days)
        df = df[df['submitted_at'] >= cutoff_date]
        
        # Group by date
        df['date'] = df['submitted_at'].dt.date
        daily = df.groupby('date').agg({
            'claim_value': ['count', 'sum']
        }).reset_index()
        
        daily.columns = ['date', 'count', 'amount']
        daily = daily.sort_values('date')
        
        # Calculate cumulative
        daily['cumulative'] = daily['amount'].cumsum()
        
        return {
            'dates': daily['date'].tolist(),
            'claims': daily['count'].tolist(),
            'amounts': daily['amount'].tolist(),
            'cumulative': daily['cumulative'].tolist()
        }

    def get_store_benchmarks(self, client_id: int) -> Dict[str, Any]:
        """Compare la performance de différents magasins d'un même client."""
        # simulation
        return {
            "Shopify Main": {"recovery_rate": 85.0, "total": 12400.0},
            "Amazon FBM": {"recovery_rate": 62.0, "total": 4500.0},
            "WooCommerce EU": {"recovery_rate": 78.0, "total": 8200.0}
        }
    
    def get_disputes_data(self) -> pd.DataFrame:
        """Fetch real dispute data for the current authenticated user."""
        import streamlit as st
        try:
            from database.database_manager import get_db_manager
            db = get_db_manager()
            client_email = st.session_state.get('client_email')
            if not client_email:
                return pd.DataFrame()
                
            client = db.get_client(email=client_email)
            if not client:
                return pd.DataFrame()
                
            claims = db.get_client_claims(client['id'])
            if not claims:
                return pd.DataFrame()
                
            return pd.DataFrame(claims)
        except Exception as e:
            logger.error(f"Error fetching real disputes: {e}")
            return pd.DataFrame()

    def simulate_disputes_data(self, num_records: int = 10) -> pd.DataFrame:
        """Generate high-fidelity simulated dispute data for demo purposes."""
        carriers = ['UPS', 'DHL', 'FedEx', 'Chronopost', 'Colissimo', 'USPS', 'DPD']
        statuses = ['pending', 'accepted', 'rejected', 'recovered', 'under_review']
        dispute_types = ['damaged_item', 'lost_package', 'late_delivery', 'wrong_address']
        
        data = []
        for i in range(num_records):
            submitted_date = datetime.now() - timedelta(days=random.randint(1, 30))
            resolved_date = submitted_date + timedelta(days=random.randint(3, 15)) if random.random() > 0.5 else None
            
            data.append({
                'order_id': f'#{8800 + i}',
                'claim_reference': f'CL-{1000 + i}',
                'carrier': random.choice(carriers),
                'total_recoverable': round(random.uniform(50, 450), 2),
                'claim_value': round(random.uniform(50, 450), 2),
                'amount_requested': round(random.uniform(50, 450), 2),
                'amount_recovered': round(random.uniform(50, 450), 2) if resolved_date else 0,
                'status': random.choice(statuses),
                'dispute_type': random.choice(dispute_types),
                'submitted_at': submitted_date,
                'resolved_at': resolved_date,
                'created_at': submitted_date,
                'payment_status': 'paid' if resolved_date and random.random() > 0.2 else 'pending'
            })
        
        return pd.DataFrame(data)
    

# Test
if __name__ == "__main__":
    calculator = MetricsCalculator()
    
    # Sample data
    sample_disputes = [
        {
            'claim_value': 150.0,
            'status': 'accepted',
            'carrier': 'colissimo',
            'submitted_at': '2024-01-15',
            'resolved_at': '2024-01-20',
            'amount_recovered': 150.0
        },
        {
            'claim_value': 80.0,
            'status': 'pending',
            'carrier': 'chronopost',
            'submitted_at': '2024-01-18'
        },
        {
            'claim_value': 200.0,
            'status': 'recovered',
            'carrier': 'ups',
            'submitted_at': '2024-01-10',
            'resolved_at': '2024-01-17',
            'amount_recovered': 200.0
        }
    ]
    
    print("="*70)
    print("METRICS CALCULATOR - Test")
    print("="*70)
    
    kpis = calculator.calculate_kpis(sample_disputes)
    
    print("\n📊 KPIs:")
    print(f"  Total Claims: {kpis['total_claims']}")
    print(f"  Success Rate: {kpis['success_rate']:.1f}%")
    print(f"  Avg Processing: {kpis['average_processing_time']:.1f} days")
    print(f"  Total Recovered: €{kpis['total_recovered']:.2f}")
    print(f"  Avg Claim Value: €{kpis['average_claim_value']:.2f}")
    print(f"  ROI Client: {kpis['roi_client']:.1f}%")
    
    print("\n🚚 By Carrier:")
    for carrier, metrics in kpis['by_carrier'].items():
        print(f"  {carrier.capitalize()}:")
        print(f"    - Count: {metrics['count']}")
        print(f"    - Success: {metrics['success_rate']:.1f}%")
    
    print("\n✅ Test Complete")
    print("="*70)
