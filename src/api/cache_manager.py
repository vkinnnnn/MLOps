"""
Cache Manager for API Response Caching

Provides in-memory caching with TTL support for API responses.
"""

from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import hashlib
import json
from functools import wraps
import threading


class CacheEntry:
    """Represents a single cache entry with expiration."""
    
    def __init__(self, value: Any, ttl_seconds: int):
        """
        Initialize cache entry.
        
        Args:
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.expires_at


class CacheManager:
    """
    In-memory cache manager with TTL support.
    Thread-safe implementation for concurrent access.
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache manager.
        
        Args:
            default_ttl: Default time to live in seconds (default: 5 minutes)
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Cache key string
        """
        # Create a string representation of arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        
        # Generate hash
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or expired
        """
        with self.lock:
            entry = self.cache.get(key)
            
            if entry is None:
                self.misses += 1
                return None
            
            if entry.is_expired():
                # Remove expired entry
                del self.cache[key]
                self.misses += 1
                return None
            
            self.hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        with self.lock:
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            self.cache[key] = CacheEntry(value, ttl_seconds)
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key was deleted, False if not found
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def cleanup_expired(self):
        """Remove all expired entries from cache."""
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests
            }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds (uses default if None)
        key_prefix: Prefix for cache key
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{cache._generate_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(key_pattern: Optional[str] = None):
    """
    Invalidate cache entries matching pattern.
    
    Args:
        key_pattern: Pattern to match (None = clear all)
    """
    cache = get_cache_manager()
    
    if key_pattern is None:
        cache.clear()
    else:
        # Delete keys matching pattern
        with cache.lock:
            keys_to_delete = [
                key for key in cache.cache.keys()
                if key_pattern in key
            ]
            for key in keys_to_delete:
                cache.delete(key)
