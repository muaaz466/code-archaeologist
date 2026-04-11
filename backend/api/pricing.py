"""
Usage-Based API Pricing Module - Week 4

Implements tiered pricing:
- First 1000 calls: Free
- $0.01 per analysis
- $0.001 per query

Tracks usage per API key with rate limiting.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
import hashlib
import time


class PricingTier(Enum):
    """Pricing tiers"""
    FREE = "free"           # First 1000 calls
    STANDARD = "standard"   # Pay per use
    ENTERPRISE = "enterprise"  # Custom pricing


@dataclass
class UsageRecord:
    """Record of API usage"""
    api_key: str
    endpoint: str           # e.g., '/upload', '/query'
    cost: float             # Cost in USD
    timestamp: datetime
    session_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class ApiKeyInfo:
    """Information about an API key"""
    api_key: str
    tier: PricingTier
    created_at: datetime
    total_calls: int = 0
    total_cost: float = 0.0
    free_calls_remaining: int = 1000
    rate_limit_per_minute: int = 60
    last_reset: datetime = field(default_factory=datetime.now)


class PricingManager:
    """
    Manages API pricing and usage tracking.
    
    Pricing:
    - Analysis (upload): $0.01
    - Query: $0.001
    - Free tier: 1000 calls
    """
    
    # Pricing in USD
    PRICES = {
        '/upload': 0.01,
        '/analyze': 0.01,
        '/query': 0.001,
        '/explain': 0.005,
        '/export/pdf': 0.02,
        '/batch': 0.05,
        '/whatif': 0.005,
        '/compare': 0.01
    }
    
    FREE_TIER_CALLS = 1000
    
    def __init__(self, storage_path: str = "api_usage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self._keys: Dict[str, ApiKeyInfo] = {}
        self._usage_cache: Dict[str, list] = {}
        self._load_keys()
    
    def generate_api_key(self, tier: PricingTier = PricingTier.FREE) -> str:
        """Generate a new API key"""
        # Generate random key
        key_data = f"{time.time()}{tier.value}{hashlib.sha256().hexdigest()[:16]}"
        api_key = f"ca_{hashlib.sha256(key_data.encode()).hexdigest()[:32]}"
        
        # Create key info
        key_info = ApiKeyInfo(
            api_key=api_key,
            tier=tier,
            created_at=datetime.now(),
            free_calls_remaining=self.FREE_TIER_CALLS if tier == PricingTier.FREE else 0,
            rate_limit_per_minute=60 if tier == PricingTier.FREE else 1000
        )
        
        self._keys[api_key] = key_info
        self._save_key(key_info)
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate API key and check rate limits.
        
        Returns:
            (is_valid, error_message)
        """
        if not api_key or api_key not in self._keys:
            return False, "Invalid API key"
        
        key_info = self._keys[api_key]
        
        # Check rate limit
        recent_calls = self._get_recent_calls(api_key, minutes=1)
        if len(recent_calls) >= key_info.rate_limit_per_minute:
            return False, f"Rate limit exceeded: {key_info.rate_limit_per_minute} calls/minute"
        
        return True, None
    
    def record_usage(
        self, 
        api_key: str, 
        endpoint: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record API usage and calculate cost.
        
        Returns:
            Usage summary including cost
        """
        if api_key not in self._keys:
            return {'error': 'Invalid API key', 'cost': 0}
        
        key_info = self._keys[api_key]
        
        # Calculate cost
        base_cost = self.PRICES.get(endpoint, 0.001)
        
        # Apply free tier
        if key_info.tier == PricingTier.FREE and key_info.free_calls_remaining > 0:
            actual_cost = 0.0
            key_info.free_calls_remaining -= 1
        else:
            actual_cost = base_cost
            key_info.total_cost += base_cost
        
        key_info.total_calls += 1
        
        # Record usage
        record = UsageRecord(
            api_key=api_key,
            endpoint=endpoint,
            cost=actual_cost,
            timestamp=datetime.now(),
            session_id=session_id,
            metadata=metadata or {}
        )
        
        self._save_usage(record)
        
        # Update key info
        self._save_key(key_info)
        
        return {
            'cost': actual_cost,
            'endpoint': endpoint,
            'free_calls_remaining': key_info.free_calls_remaining,
            'tier': key_info.tier.value,
            'total_calls': key_info.total_calls,
            'total_cost': round(key_info.total_cost, 4)
        }
    
    def get_usage_summary(self, api_key: str) -> Dict:
        """Get usage summary for API key"""
        if api_key not in self._keys:
            return {'error': 'Invalid API key'}
        
        key_info = self._keys[api_key]
        
        # Get usage breakdown
        usage = self._load_usage(api_key)
        
        endpoint_breakdown = {}
        for record in usage:
            ep = record['endpoint']
            endpoint_breakdown[ep] = endpoint_breakdown.get(ep, 0) + 1
        
        # Calculate costs by endpoint
        cost_breakdown = {}
        for ep, count in endpoint_breakdown.items():
            price = self.PRICES.get(ep, 0.001)
            cost_breakdown[ep] = {
                'calls': count,
                'estimated_cost': count * price
            }
        
        return {
            'api_key': api_key[:10] + '...',  # Masked
            'tier': key_info.tier.value,
            'total_calls': key_info.total_calls,
            'free_calls_remaining': key_info.free_calls_remaining,
            'total_cost': round(key_info.total_cost, 4),
            'endpoint_breakdown': cost_breakdown,
            'created_at': key_info.created_at.isoformat()
        }
    
    def check_budget(self, api_key: str, max_budget: float) -> Tuple[bool, float]:
        """
        Check if user has exceeded budget.
        
        Returns:
            (under_budget, current_cost)
        """
        if api_key not in self._keys:
            return False, 0.0
        
        key_info = self._keys[api_key]
        return key_info.total_cost < max_budget, key_info.total_cost
    
    def _get_recent_calls(self, api_key: str, minutes: int = 1) -> list:
        """Get recent calls for rate limiting"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        usage = self._load_usage(api_key)
        
        return [
            u for u in usage 
            if datetime.fromisoformat(u['timestamp']) > cutoff
        ]
    
    def _load_keys(self):
        """Load API keys from storage"""
        keys_file = self.storage_path / "api_keys.json"
        if not keys_file.exists():
            return
        
        with open(keys_file) as f:
            data = json.load(f)
        
        for key_data in data:
            key_info = ApiKeyInfo(
                api_key=key_data['api_key'],
                tier=PricingTier(key_data['tier']),
                created_at=datetime.fromisoformat(key_data['created_at']),
                total_calls=key_data.get('total_calls', 0),
                total_cost=key_data.get('total_cost', 0.0),
                free_calls_remaining=key_data.get('free_calls_remaining', 0),
                rate_limit_per_minute=key_data.get('rate_limit_per_minute', 60),
                last_reset=datetime.fromisoformat(key_data.get('last_reset', key_data['created_at']))
            )
            self._keys[key_info.api_key] = key_info
    
    def _save_key(self, key_info: ApiKeyInfo):
        """Save API key to storage"""
        keys_file = self.storage_path / "api_keys.json"
        
        data = []
        if keys_file.exists():
            with open(keys_file) as f:
                data = json.load(f)
        
        # Update or append
        updated = False
        for i, k in enumerate(data):
            if k['api_key'] == key_info.api_key:
                data[i] = {
                    'api_key': key_info.api_key,
                    'tier': key_info.tier.value,
                    'created_at': key_info.created_at.isoformat(),
                    'total_calls': key_info.total_calls,
                    'total_cost': key_info.total_cost,
                    'free_calls_remaining': key_info.free_calls_remaining,
                    'rate_limit_per_minute': key_info.rate_limit_per_minute,
                    'last_reset': key_info.last_reset.isoformat()
                }
                updated = True
                break
        
        if not updated:
            data.append({
                'api_key': key_info.api_key,
                'tier': key_info.tier.value,
                'created_at': key_info.created_at.isoformat(),
                'total_calls': key_info.total_calls,
                'total_cost': key_info.total_cost,
                'free_calls_remaining': key_info.free_calls_remaining,
                'rate_limit_per_minute': key_info.rate_limit_per_minute,
                'last_reset': key_info.last_reset.isoformat()
            })
        
        with open(keys_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_usage(self, record: UsageRecord):
        """Save usage record"""
        usage_file = self.storage_path / f"{record.api_key}_usage.jsonl"
        
        entry = {
            'api_key': record.api_key,
            'endpoint': record.endpoint,
            'cost': record.cost,
            'timestamp': record.timestamp.isoformat(),
            'session_id': record.session_id,
            'metadata': record.metadata
        }
        
        with open(usage_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def _load_usage(self, api_key: str) -> list:
        """Load usage history"""
        usage_file = self.storage_path / f"{api_key}_usage.jsonl"
        
        if not usage_file.exists():
            return []
        
        records = []
        with open(usage_file) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        return records


# Singleton instance
_pricing_manager = None

def get_pricing_manager() -> PricingManager:
    """Get singleton pricing manager"""
    global _pricing_manager
    if _pricing_manager is None:
        _pricing_manager = PricingManager()
    return _pricing_manager


# Decorator for automatic pricing
def track_usage(endpoint: str):
    """Decorator to track API usage automatically"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get API key from request (assuming it's in kwargs or first arg)
            api_key = kwargs.get('api_key') or kwargs.get('x_api_key')
            
            # Call original function
            result = await func(*args, **kwargs)
            
            # Track usage if we have an API key
            if api_key:
                pricing = get_pricing_manager()
                session_id = None
                if isinstance(result, dict):
                    session_id = result.get('session_id')
                
                usage = pricing.record_usage(api_key, endpoint, session_id)
                
                # Add usage info to result if it's a dict
                if isinstance(result, dict):
                    result['_usage'] = usage
            
            return result
        return wrapper
    return decorator
