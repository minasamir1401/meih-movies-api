"""
ScrapingAnt API Key Manager
============================
Manages multiple ScrapingAnt API keys with:
- Automatic rotation
- Credit/quota tracking
- Blacklisting exhausted keys
- Error detection and recovery
"""

import logging
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger("api_key_manager")


@dataclass
class APIKeyStats:
    """Statistics for a single API key"""
    key: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    quota_errors: int = 0
    last_used: Optional[float] = None
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None
    is_blacklisted: bool = False
    blacklist_reason: Optional[str] = None
    blacklist_time: Optional[float] = None
    estimated_credits_used: int = 0
    
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'key': self.key[:8] + '...' + self.key[-4:],  # Masked for security
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'quota_errors': self.quota_errors,
            'last_used': self.last_used,
            'last_error': self.last_error,
            'is_blacklisted': self.is_blacklisted,
            'blacklist_reason': self.blacklist_reason,
            'success_rate': round(self.success_rate(), 2),
            'estimated_credits_used': self.estimated_credits_used
        }


class APIKeyManager:
    """
    Manages multiple ScrapingAnt API keys with intelligent rotation and tracking.
    
    Features:
    - Automatic key rotation
    - Quota tracking and management
    - Blacklisting of exhausted/blocked keys
    - Persistent statistics
    - Error recovery
    """
    
    # Error codes that indicate quota/limit issues
    QUOTA_ERROR_CODES = [429, 402, 403]
    QUOTA_ERROR_MESSAGES = [
        'quota exceeded',
        'limit reached',
        'insufficient credits',
        'payment required',
        'rate limit',
        'too many requests'
    ]
    
    # Blacklist duration (24 hours by default)
    BLACKLIST_DURATION = 24 * 60 * 60
    
    def __init__(self, api_keys: List[str], stats_file: str = "api_key_stats.json"):
        """
        Initialize the API Key Manager
        
        Args:
            api_keys: List of ScrapingAnt API keys
            stats_file: Path to file for persisting statistics
        """
        if not api_keys:
            raise ValueError("At least one API key must be provided")
        
        self.api_keys = api_keys
        self.stats_file = stats_file
        self.current_index = 0
        
        # Initialize stats for each key
        self.key_stats: Dict[str, APIKeyStats] = {}
        for key in api_keys:
            self.key_stats[key] = APIKeyStats(key=key)
        
        # Load previous statistics if available
        self._load_stats()
        
        logger.info(f"Initialized API Key Manager with {len(api_keys)} keys")
    
    def get_current_key(self) -> Optional[str]:
        """
        Get the current active API key.
        Automatically rotates to next available key if current is blacklisted.
        
        Returns:
            Current API key or None if all keys are blacklisted
        """
        attempts = 0
        max_attempts = len(self.api_keys)
        
        while attempts < max_attempts:
            current_key = self.api_keys[self.current_index]
            stats = self.key_stats[current_key]
            
            # Check if key is blacklisted
            if stats.is_blacklisted:
                # Check if blacklist has expired
                if stats.blacklist_time and (time.time() - stats.blacklist_time) > self.BLACKLIST_DURATION:
                    logger.info(f"Removing key {self._mask_key(current_key)} from blacklist (duration expired)")
                    stats.is_blacklisted = False
                    stats.blacklist_reason = None
                    stats.blacklist_time = None
                    return current_key
                else:
                    logger.debug(f"Key {self._mask_key(current_key)} is blacklisted, rotating...")
                    self._rotate_key()
                    attempts += 1
                    continue
            
            return current_key
        
        logger.error("All API keys are blacklisted!")
        return None
    
    def _rotate_key(self):
        """Rotate to the next API key"""
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        logger.info(f"Rotated to key index {self.current_index}")
    
    def record_success(self, key: str, credits_used: int = 1):
        """
        Record a successful request
        
        Args:
            key: The API key that was used
            credits_used: Estimated credits consumed (default: 1)
        """
        if key not in self.key_stats:
            return
        
        stats = self.key_stats[key]
        stats.total_requests += 1
        stats.successful_requests += 1
        stats.last_used = time.time()
        stats.estimated_credits_used += credits_used
        
        logger.debug(f"Success recorded for key {self._mask_key(key)} (Total: {stats.successful_requests})")
        self._save_stats()
    
    def record_failure(self, key: str, error_code: Optional[int] = None, error_message: Optional[str] = None):
        """
        Record a failed request and handle quota errors
        
        Args:
            key: The API key that was used
            error_code: HTTP error code
            error_message: Error message
        """
        if key not in self.key_stats:
            return
        
        stats = self.key_stats[key]
        stats.total_requests += 1
        stats.failed_requests += 1
        stats.last_used = time.time()
        stats.last_error = error_message
        stats.last_error_time = time.time()
        
        # Check if this is a quota/limit error
        is_quota_error = False
        
        if error_code in self.QUOTA_ERROR_CODES:
            is_quota_error = True
        
        if error_message:
            error_lower = error_message.lower()
            if any(msg in error_lower for msg in self.QUOTA_ERROR_MESSAGES):
                is_quota_error = True
        
        if is_quota_error:
            stats.quota_errors += 1
            logger.warning(f"Quota error detected for key {self._mask_key(key)} (Code: {error_code})")
            
            # Blacklist after 3 quota errors
            if stats.quota_errors >= 3:
                self._blacklist_key(key, f"Quota exceeded (errors: {stats.quota_errors})")
        
        logger.debug(f"Failure recorded for key {self._mask_key(key)} (Total: {stats.failed_requests})")
        self._save_stats()
    
    def _blacklist_key(self, key: str, reason: str):
        """
        Blacklist an API key
        
        Args:
            key: The API key to blacklist
            reason: Reason for blacklisting
        """
        if key not in self.key_stats:
            return
        
        stats = self.key_stats[key]
        stats.is_blacklisted = True
        stats.blacklist_reason = reason
        stats.blacklist_time = time.time()
        
        logger.warning(f"Blacklisted key {self._mask_key(key)}: {reason}")
        
        # Automatically rotate to next key
        self._rotate_key()
        self._save_stats()
    
    def manually_blacklist_key(self, key: str, reason: str = "Manual blacklist"):
        """
        Manually blacklist a specific key
        
        Args:
            key: The API key to blacklist
            reason: Reason for blacklisting
        """
        self._blacklist_key(key, reason)
    
    def unblacklist_key(self, key: str):
        """
        Remove a key from blacklist
        
        Args:
            key: The API key to unblacklist
        """
        if key not in self.key_stats:
            return
        
        stats = self.key_stats[key]
        stats.is_blacklisted = False
        stats.blacklist_reason = None
        stats.blacklist_time = None
        stats.quota_errors = 0  # Reset quota errors
        
        logger.info(f"Removed key {self._mask_key(key)} from blacklist")
        self._save_stats()
    
    def get_stats(self) -> Dict:
        """
        Get statistics for all keys
        
        Returns:
            Dictionary containing stats for all keys
        """
        return {
            'total_keys': len(self.api_keys),
            'active_keys': sum(1 for s in self.key_stats.values() if not s.is_blacklisted),
            'blacklisted_keys': sum(1 for s in self.key_stats.values() if s.is_blacklisted),
            'current_key_index': self.current_index,
            'keys': [stats.to_dict() for stats in self.key_stats.values()]
        }
    
    def _mask_key(self, key: str) -> str:
        """Mask API key for logging (show first 8 and last 4 chars)"""
        if len(key) <= 12:
            return '*' * len(key)
        return f"{key[:8]}...{key[-4:]}"
    
    def _save_stats(self):
        """Save statistics to file"""
        try:
            stats_data = {
                'last_updated': time.time(),
                'keys': {key: stats.to_dict() for key, stats in self.key_stats.items()}
            }
            
            with open(self.stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2)
            
            logger.debug(f"Statistics saved to {self.stats_file}")
        except Exception as e:
            logger.error(f"Failed to save statistics: {e}")
    
    def _load_stats(self):
        """Load statistics from file"""
        if not os.path.exists(self.stats_file):
            logger.info("No previous statistics file found")
            return
        
        try:
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
            
            # Restore stats for keys that still exist
            for key, stats_dict in data.get('keys', {}).items():
                if key in self.key_stats:
                    # Restore stats (excluding masked key)
                    stats = self.key_stats[key]
                    stats.total_requests = stats_dict.get('total_requests', 0)
                    stats.successful_requests = stats_dict.get('successful_requests', 0)
                    stats.failed_requests = stats_dict.get('failed_requests', 0)
                    stats.quota_errors = stats_dict.get('quota_errors', 0)
                    stats.last_used = stats_dict.get('last_used')
                    stats.last_error = stats_dict.get('last_error')
                    stats.is_blacklisted = stats_dict.get('is_blacklisted', False)
                    stats.blacklist_reason = stats_dict.get('blacklist_reason')
                    stats.estimated_credits_used = stats_dict.get('estimated_credits_used', 0)
            
            logger.info(f"Statistics loaded from {self.stats_file}")
        except Exception as e:
            logger.error(f"Failed to load statistics: {e}")
    
    def reset_stats(self):
        """Reset all statistics"""
        for stats in self.key_stats.values():
            stats.total_requests = 0
            stats.successful_requests = 0
            stats.failed_requests = 0
            stats.quota_errors = 0
            stats.last_error = None
            stats.last_error_time = None
            stats.estimated_credits_used = 0
        
        logger.info("All statistics reset")
        self._save_stats()
