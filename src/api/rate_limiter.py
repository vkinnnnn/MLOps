"""
Rate Limiting System
Controls request limits per user to prevent abuse and manage costs
"""
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
import json
import os

# Rate limit storage file
RATE_LIMIT_FILE = "/app/rate_limits.json"


class RateLimiter:
    """
    Rate limiter to control API usage
    
    Features:
    - Per-user request tracking
    - Daily/hourly limits
    - Automatic reset
    - Usage statistics
    """
    
    def __init__(self):
        """Initialize rate limiter"""
        # Store: {api_key: [timestamp1, timestamp2, ...]}
        self.requests = defaultdict(list)
        self._load_state()
    
    def _load_state(self):
        """Load rate limit state from file"""
        if os.path.exists(RATE_LIMIT_FILE):
            try:
                with open(RATE_LIMIT_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert ISO strings back to datetime
                    for key, timestamps in data.items():
                        self.requests[key] = [
                            datetime.fromisoformat(ts) for ts in timestamps
                        ]
            except:
                pass
    
    def _save_state(self):
        """Save rate limit state to file"""
        try:
            os.makedirs(os.path.dirname(RATE_LIMIT_FILE), exist_ok=True)
            # Convert datetime to ISO strings for JSON
            data = {
                key: [ts.isoformat() for ts in timestamps]
                for key, timestamps in self.requests.items()
            }
            with open(RATE_LIMIT_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save rate limits: {e}")
    
    def check_rate_limit(
        self,
        api_key: str,
        limit: int,
        window_seconds: int = 86400  # 24 hours default
    ) -> Dict[str, int]:
        """
        Check if user has exceeded rate limit
        
        Args:
            api_key: User's API key
            limit: Maximum requests allowed
            window_seconds: Time window in seconds (default: 86400 = 24 hours)
            
        Returns:
            Dictionary with usage statistics:
            {
                "requests_used": 45,
                "requests_remaining": 55,
                "limit": 100,
                "reset_time": "2025-10-29T00:00:00"
            }
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Remove old requests outside the time window
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if req_time > cutoff
        ]
        
        # Count current requests
        requests_used = len(self.requests[api_key])
        requests_remaining = max(0, limit - requests_used)
        
        # Calculate reset time (start of next day)
        reset_time = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # Check if limit exceeded
        if requests_used >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"You have used all {limit} requests for today",
                    "requests_used": requests_used,
                    "requests_remaining": 0,
                    "limit": limit,
                    "reset_time": reset_time.isoformat(),
                    "retry_after_seconds": int((reset_time - now).total_seconds())
                }
            )
        
        # Add current request
        self.requests[api_key].append(now)
        self._save_state()
        
        return {
            "requests_used": requests_used + 1,  # Include current request
            "requests_remaining": requests_remaining - 1,
            "limit": limit,
            "reset_time": reset_time.isoformat()
        }
    
    def get_usage_stats(self, api_key: str, window_seconds: int = 86400) -> Dict:
        """
        Get usage statistics for a user
        
        Args:
            api_key: User's API key
            window_seconds: Time window in seconds
            
        Returns:
            Usage statistics dictionary
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if req_time > cutoff
        ]
        
        requests_used = len(self.requests[api_key])
        
        # Calculate hourly breakdown
        hourly_usage = defaultdict(int)
        for req_time in self.requests[api_key]:
            hour = req_time.replace(minute=0, second=0, microsecond=0)
            hourly_usage[hour.isoformat()] += 1
        
        return {
            "requests_used_24h": requests_used,
            "hourly_breakdown": dict(hourly_usage),
            "last_request": self.requests[api_key][-1].isoformat() if self.requests[api_key] else None
        }
    
    def reset_user_limit(self, api_key: str):
        """Reset rate limit for a specific user (admin function)"""
        self.requests[api_key] = []
        self._save_state()
    
    def get_all_usage(self) -> Dict:
        """Get usage statistics for all users (admin function)"""
        stats = {}
        for api_key in self.requests.keys():
            stats[api_key] = self.get_usage_stats(api_key)
        return stats


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(user: Dict) -> Dict[str, int]:
    """
    FastAPI dependency to check rate limit
    
    Usage:
        @router.post("/endpoint")
        async def endpoint(
            user: dict = Depends(verify_api_key),
            rate_info: dict = Depends(check_rate_limit)
        ):
            # rate_info contains usage stats
    """
    # Get user's email as unique identifier
    user_id = user.get("email", "unknown")
    limit = user.get("requests_per_day", 100)
    
    return rate_limiter.check_rate_limit(user_id, limit)
