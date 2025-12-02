"""
API Key Authentication System
"""
import secrets
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import json
import os

# API Keys storage file
API_KEYS_FILE = "api_keys.json"

# In-memory storage (for demo)
API_KEYS_DB = {}


def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"excloan_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def create_api_key(
    user_name: str,
    tier: str = "standard",
    rate_limit: int = 100
) -> Dict[str, Any]:
    """
    Create a new API key
    
    Args:
        user_name: Name of the user
        tier: API tier (free, standard, premium)
        rate_limit: Daily request limit
        
    Returns:
        API key details
    """
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    
    key_data = {
        "api_key": api_key,
        "key_hash": key_hash,
        "user_name": user_name,
        "tier": tier,
        "rate_limit": rate_limit,
        "created_at": datetime.now().isoformat(),
        "is_active": True,
        "usage_count": 0
    }
    
    # Store in memory
    API_KEYS_DB[key_hash] = key_data
    
    # Save to file
    save_api_keys()
    
    return key_data


def save_api_keys():
    """Save API keys to file"""
    try:
        with open(API_KEYS_FILE, 'w') as f:
            json.dump(API_KEYS_DB, f, indent=2)
    except Exception as e:
        print(f"Error saving API keys: {e}")


def load_api_keys():
    """Load API keys from file"""
    global API_KEYS_DB
    try:
        if os.path.exists(API_KEYS_FILE):
            with open(API_KEYS_FILE, 'r') as f:
                API_KEYS_DB = json.load(f)
    except Exception as e:
        print(f"Error loading API keys: {e}")


def verify_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Verify an API key
    
    Args:
        api_key: API key to verify
        
    Returns:
        Key data if valid, None otherwise
    """
    key_hash = hash_api_key(api_key)
    
    if key_hash in API_KEYS_DB:
        key_data = API_KEYS_DB[key_hash]
        if key_data.get("is_active", False):
            # Increment usage count
            key_data["usage_count"] = key_data.get("usage_count", 0) + 1
            save_api_keys()
            return key_data
    
    return None


def list_api_keys() -> list:
    """List all API keys (without showing actual keys)"""
    return [
        {
            "user_name": data["user_name"],
            "tier": data["tier"],
            "rate_limit": data["rate_limit"],
            "created_at": data["created_at"],
            "is_active": data["is_active"],
            "usage_count": data.get("usage_count", 0)
        }
        for data in API_KEYS_DB.values()
    ]


def revoke_api_key(api_key: str) -> bool:
    """Revoke an API key"""
    key_hash = hash_api_key(api_key)
    
    if key_hash in API_KEYS_DB:
        API_KEYS_DB[key_hash]["is_active"] = False
        save_api_keys()
        return True
    
    return False


# Load existing keys on import
load_api_keys()
