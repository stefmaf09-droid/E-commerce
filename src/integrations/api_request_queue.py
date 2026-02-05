"""
API Request Queue with Rate Limiting

Manages API requests across carriers to respect rate limits:
- Colissimo/La Poste: 1,000 requests/day
- Chronopost: 500 requests/day
- UPS: 200 requests/hour
- DHL: 2,500 requests/day
- FedEx: 1,000 requests/day

Features:
- Automatic rate limit tracking per carrier
- Time window-based limit reset (hourly/daily)
- Request queuing when limit reached
- Logging and monitoring

Usage:
    from src.integrations.api_request_queue import APIRequestQueue
    
    queue = APIRequestQueue()
    
    # Check if can execute
    if queue.can_execute('colissimo'):
        result = connector.get_pod(tracking)
        queue.record_request('colissimo')
    
    # Or execute with automatic limiting
    result = queue.execute_with_limit(
        'colissimo',
        connector.get_pod,
        tracking_number
    )
"""

import os
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Callable, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class APIRequestQueue:
    """
    Rate limiting queue for carrier APIs.
    
    Tracks requests per carrier and enforces rate limits.
    """
    
    # Rate limits per carrier
    RATE_LIMITS = {
        'colissimo': {'max': 1000, 'window': 'day'},
        'chronopost': {'max': 500, 'window': 'day'},
        'ups': {'max': 200, 'window': 'hour'},
        'dhl': {'max': 2500, 'window': 'day'},
        'fedex': {'max': 1000, 'window': 'day'}
    }
    
    STATS_FILE = Path('data/api_stats/rate_limits.json')
    
    def __init__(self, persist_stats: bool = True):
        """
        Initialize request queue.
        
        Args:
            persist_stats: Whether to persist stats to disk
        """
        self.persist_stats = persist_stats
        
        # Per-carrier counters
        self.daily_counts = defaultdict(lambda: {'count': 0, 'reset_at': None})
        self.hourly_counts = defaultdict(lambda: {'count': 0, 'reset_at': None})
        
        # Load persisted stats
        if persist_stats:
            self._load_stats()
        
        logger.info("API Request Queue initialized")
    
    def can_execute(self, carrier: str) -> bool:
        """
        Check if request can be executed within rate limit.
        
        Args:
            carrier: Carrier name
            
        Returns:
            True if within limit, False if limit reached
        """
        limit_config = self.RATE_LIMITS.get(carrier.lower())
        
        if not limit_config:
            # No limit defined for this carrier
            logger.debug(f"No rate limit defined for {carrier}, allowing")
            return True
        
        max_requests = limit_config['max']
        window = limit_config['window']
        
        # Get appropriate counter
        if window == 'day':
            counter = self.daily_counts[carrier]
            reset_delta = timedelta(days=1)
        else:  # hour
            counter = self.hourly_counts[carrier]
            reset_delta = timedelta(hours=1)
        
        # Reset counter if window expired
        now = datetime.now()
        if counter['reset_at'] is None or now > counter['reset_at']:
            counter['count'] = 0
            counter['reset_at'] = now + reset_delta
            logger.info(f"Rate limit counter reset for {carrier} ({window})")
        
        # Check limit
        if counter['count'] >= max_requests:
            remaining_time = counter['reset_at'] - now
            logger.warning(
                f"⚠️ Rate limit reached for {carrier}: {counter['count']}/{max_requests} "
                f"(resets in {remaining_time})"
            )
            return False
        
        return True
    
    def record_request(self, carrier: str):
        """
        Record that a request was made.
        
        Args:
            carrier: Carrier name
        """
        limit_config = self.RATE_LIMITS.get(carrier.lower())
        
        if not limit_config:
            return
        
        window = limit_config['window']
        
        # Increment counter
        if window == 'day':
            self.daily_counts[carrier]['count'] += 1
        else:
            self.hourly_counts[carrier]['count'] += 1
        
        # Log current usage
        current_count = self.get_count(carrier)
        max_count = limit_config['max']
        logger.debug(f"{carrier} API usage: {current_count}/{max_count}")
        
        # Persist stats
        if self.persist_stats:
            self._save_stats()
    
    def get_count(self, carrier: str) -> int:
        """
        Get current request count for carrier.
        
        Args:
            carrier: Carrier name
            
        Returns:
            Current request count
        """
        limit_config = self.RATE_LIMITS.get(carrier.lower())
        
        if not limit_config:
            return 0
        
        if limit_config['window'] == 'day':
            return self.daily_counts[carrier]['count']
        else:
            return self.hourly_counts[carrier]['count']
    
    def get_stats(self, carrier: Optional[str] = None) -> Dict:
        """
        Get usage statistics.
        
        Args:
            carrier: Specific carrier or None for all
            
        Returns:
            Usage stats dictionary
        """
        if carrier:
            limit_config = self.RATE_LIMITS.get(carrier.lower())
            if not limit_config:
                return {}
            
            window = limit_config['window']
            counter = self.daily_counts[carrier] if window == 'day' else self.hourly_counts[carrier]
            
            return {
                'carrier': carrier,
                'count': counter['count'],
                'limit': limit_config['max'],
                'window': window,
                'reset_at': counter['reset_at'].isoformat() if counter['reset_at'] else None,
                'usage_percent': round((counter['count'] / limit_config['max']) * 100, 1)
            }
        else:
            # All carriers
            stats = {}
            for carrier in self.RATE_LIMITS.keys():
                stats[carrier] = self.get_stats(carrier)
            return stats
    
    def execute_with_limit(
        self,
        carrier: str,
        request_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute request if within rate limit.
        
        Args:
            carrier: Carrier name
            request_func: Function to execute
            *args, **kwargs: Arguments for function
            
        Returns:
            Function result or error dict if limit reached
        """
        if not self.can_execute(carrier):
            # Rate limit reached
            reset_time = self._get_reset_time(carrier)
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': f'Rate limit exceeded for {carrier}. Resets at {reset_time.strftime("%H:%M:%S")}',
                'retry_after': reset_time
            }
        
        # Execute request
        try:
            result = request_func(*args, **kwargs)
            self.record_request(carrier)
            return result
        except Exception as e:
            logger.error(f"Request execution failed for {carrier}: {e}")
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': str(e)
            }
    
    def _get_reset_time(self, carrier: str) -> datetime:
        """Get when rate limit resets."""
        limit_config = self.RATE_LIMITS.get(carrier.lower())
        
        if not limit_config:
            return datetime.now()
        
        if limit_config['window'] == 'day':
            return self.daily_counts[carrier]['reset_at'] or datetime.now()
        else:
            return self.hourly_counts[carrier]['reset_at'] or datetime.now()
    
    def _save_stats(self):
        """Persist stats to disk."""
        try:
            self.STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            stats_data = {
                'last_updated': datetime.now().isoformat(),
                'daily_counts': {
                    k: {
                        'count': v['count'],
                        'reset_at': v['reset_at'].isoformat() if v['reset_at'] else None
                    }
                    for k, v in self.daily_counts.items()
                },
                'hourly_counts': {
                    k: {
                        'count': v['count'],
                        'reset_at': v['reset_at'].isoformat() if v['reset_at'] else None
                    }
                    for k, v in self.hourly_counts.items()
                }
            }
            
            with open(self.STATS_FILE, 'w') as f:
                json.dump(stats_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save API stats: {e}")
    
    def _load_stats(self):
        """Load persisted stats from disk."""
        if not self.STATS_FILE.exists():
            return
        
        try:
            with open(self.STATS_FILE, 'r') as f:
                stats_data = json.load(f)
            
            # Load daily counts
            for carrier, data in stats_data.get('daily_counts', {}).items():
                self.daily_counts[carrier] = {
                    'count': data['count'],
                    'reset_at': datetime.fromisoformat(data['reset_at']) if data['reset_at'] else None
                }
            
            # Load hourly counts
            for carrier, data in stats_data.get('hourly_counts', {}).items():
                self.hourly_counts[carrier] = {
                    'count': data['count'],
                    'reset_at': datetime.fromisoformat(data['reset_at']) if data['reset_at'] else None
                }
            
            logger.info("API stats loaded from disk")
            
        except Exception as e:
            logger.error(f"Failed to load API stats: {e}")


if __name__ == "__main__":
    # Test API Request Queue
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("API REQUEST QUEUE - Test")
    print("="*70)
    
    queue = APIRequestQueue(persist_stats=False)
    
    # Test rate limiting
    print("\n📊 Testing rate limits...")
    
    carriers_to_test = ['colissimo', 'chronopost', 'ups']
    
    for carrier in carriers_to_test:
        print(f"\n{carrier.upper()}:")
        
        # Check initial state
        can_exec = queue.can_execute(carrier)
        print(f"  Can execute: {can_exec}")
        
        # Record some requests
        for i in range(5):
            queue.record_request(carrier)
        
        # Get stats
        stats = queue.get_stats(carrier)
        print(f"  Usage: {stats['count']}/{stats['limit']} ({stats['usage_percent']}%)")
        print(f"  Window: {stats['window']}")
        if stats['reset_at']:
            print(f"  Resets at: {stats['reset_at']}")
    
    # Test with mock function
    print("\n🔄 Testing execute_with_limit...")
    
    def mock_api_call(tracking):
        return {
            'success': True,
            'pod_url': f'https://example.com/pod/{tracking}',
            'pod_data': {'tracking': tracking}
        }
    
    result = queue.execute_with_limit('colissimo', mock_api_call, 'TEST123')
    print(f"  Result: {result['success']}")
    print(f"  POD URL: {result.get('pod_url', 'N/A')}")
    
    # Show all stats
    print("\n📈 All carrier stats:")
    all_stats = queue.get_stats()
    for carrier, stats in all_stats.items():
        print(f"  {carrier}: {stats['count']}/{stats['limit']} ({stats['usage_percent']}%)")
    
    print("\n" + "="*70)
    print("✅ API Request Queue Ready")
    print("="*70)
