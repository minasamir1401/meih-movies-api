"""
Multi-Level Cache System
=========================
Implements memory and file-based caching with TTL and LRU eviction.
"""

import os
import json
import time
import hashlib
import logging
import asyncio
from typing import Optional, Any, Dict
from collections import OrderedDict
from pathlib import Path
import pickle

logger = logging.getLogger("cache_manager")


class MemoryCache:
    """
    In-memory LRU cache with TTL support.
    Fast but limited by available RAM.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize memory cache
        
        Args:
            max_size: Maximum number of items to store
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            value, expiry = self.cache[key]
            
            # Check if expired
            if time.time() > expiry:
                del self.cache[key]
                self.stats['expirations'] += 1
                self.stats['misses'] += 1
                return None
            
            # Move to end (LRU)
            self.cache.move_to_end(key)
            self.stats['hits'] += 1
            return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        async with self._lock:
            ttl = ttl or self.default_ttl
            expiry = time.time() + ttl
            
            # Update existing or add new
            if key in self.cache:
                self.cache.move_to_end(key)
            
            self.cache[key] = (value, expiry)
            
            # Evict oldest if over capacity
            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats['evictions'] += 1
    
    async def delete(self, key: str):
        """Delete a key from cache"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
    
    async def clear(self):
        """Clear all cache entries"""
        async with self._lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': round(hit_rate, 2)
        }


class FileCache:
    """
    File-based cache for persistent storage.
    Slower than memory but survives restarts.
    """
    
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 86400):
        """
        Initialize file cache
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'errors': 0
        }
        self._lock = asyncio.Lock()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for a cache key"""
        # Hash the key to create a valid filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from file cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self.stats['misses'] += 1
            return None
        
        try:
            async with self._lock:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                
                value, expiry = data['value'], data['expiry']
                
                # Check if expired
                if time.time() > expiry:
                    cache_path.unlink()
                    self.stats['misses'] += 1
                    return None
                
                self.stats['hits'] += 1
                return value
        
        except Exception as e:
            logger.error(f"Error reading cache file {cache_path}: {e}")
            self.stats['errors'] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in file cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        cache_path = self._get_cache_path(key)
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        
        try:
            async with self._lock:
                with open(cache_path, 'wb') as f:
                    pickle.dump({
                        'value': value,
                        'expiry': expiry,
                        'created': time.time()
                    }, f)
                
                self.stats['writes'] += 1
        
        except Exception as e:
            logger.error(f"Error writing cache file {cache_path}: {e}")
            self.stats['errors'] += 1
    
    async def delete(self, key: str):
        """Delete a key from cache"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
    
    async def clear(self):
        """Clear all cache files"""
        async with self._lock:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_file}: {e}")
    
    async def cleanup_expired(self):
        """Remove expired cache files"""
        removed = 0
        async with self._lock:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    if time.time() > data['expiry']:
                        cache_file.unlink()
                        removed += 1
                
                except Exception as e:
                    logger.error(f"Error checking cache file {cache_file}: {e}")
        
        logger.info(f"Cleaned up {removed} expired cache files")
        return removed
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Count cache files
        cache_files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            **self.stats,
            'files': len(cache_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'hit_rate': round(hit_rate, 2)
        }


class MultiLevelCache:
    """
    Multi-level cache combining memory and file caching.
    Checks memory first (fast), falls back to file cache (persistent).
    """
    
    def __init__(
        self,
        memory_size: int = 1000,
        memory_ttl: int = 3600,
        file_cache_dir: str = ".cache",
        file_ttl: int = 86400
    ):
        """
        Initialize multi-level cache
        
        Args:
            memory_size: Maximum items in memory cache
            memory_ttl: TTL for memory cache (seconds)
            file_cache_dir: Directory for file cache
            file_ttl: TTL for file cache (seconds)
        """
        self.memory = MemoryCache(max_size=memory_size, default_ttl=memory_ttl)
        self.file = FileCache(cache_dir=file_cache_dir, default_ttl=file_ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (checks memory first, then file)
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        # Try memory cache first
        value = await self.memory.get(key)
        if value is not None:
            return value
        
        # Fall back to file cache
        value = await self.file.get(key)
        if value is not None:
            # Promote to memory cache
            await self.memory.set(key, value)
            return value
        
        return None
    
    async def set(self, key: str, value: Any, memory_ttl: Optional[int] = None, file_ttl: Optional[int] = None):
        """
        Set value in both caches
        
        Args:
            key: Cache key
            value: Value to cache
            memory_ttl: TTL for memory cache
            file_ttl: TTL for file cache
        """
        # Set in both caches
        await self.memory.set(key, value, memory_ttl)
        await self.file.set(key, value, file_ttl)
    
    async def delete(self, key: str):
        """Delete from both caches"""
        await self.memory.delete(key)
        await self.file.delete(key)
    
    async def clear(self):
        """Clear both caches"""
        await self.memory.clear()
        await self.file.clear()
    
    async def cleanup(self):
        """Cleanup expired entries from file cache"""
        return await self.file.cleanup_expired()
    
    def get_stats(self) -> Dict:
        """Get combined statistics"""
        return {
            'memory': self.memory.get_stats(),
            'file': self.file.get_stats()
        }
