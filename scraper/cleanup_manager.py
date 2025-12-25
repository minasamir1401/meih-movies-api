"""
Resource Cleanup Manager
========================
Handles automatic cleanup of temporary files, cache, and logs.
"""

import os
import logging
import asyncio
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger("cleanup_manager")


class CleanupManager:
    """
    Manages automatic cleanup of temporary resources.
    
    Features:
    - Cleanup of temporary HTML files
    - Cache file management
    - Log rotation
    - Scheduled cleanup tasks
    - Safe deletion with error handling
    """
    
    def __init__(
        self,
        temp_dirs: List[str] = None,
        cache_dirs: List[str] = None,
        log_dirs: List[str] = None,
        max_temp_age_hours: int = 24,
        max_cache_age_days: int = 7,
        max_log_age_days: int = 30,
        max_cache_size_mb: int = 500
    ):
        """
        Initialize cleanup manager
        
        Args:
            temp_dirs: Directories containing temporary files
            cache_dirs: Directories containing cache files
            log_dirs: Directories containing log files
            max_temp_age_hours: Maximum age for temp files (hours)
            max_cache_age_days: Maximum age for cache files (days)
            max_log_age_days: Maximum age for log files (days)
            max_cache_size_mb: Maximum total cache size (MB)
        """
        self.temp_dirs = [Path(d) for d in (temp_dirs or [])]
        self.cache_dirs = [Path(d) for d in (cache_dirs or ['.cache'])]
        self.log_dirs = [Path(d) for d in (log_dirs or [])]
        
        self.max_temp_age = max_temp_age_hours * 3600
        self.max_cache_age = max_cache_age_days * 86400
        self.max_log_age = max_log_age_days * 86400
        self.max_cache_size = max_cache_size_mb * 1024 * 1024
        
        self.stats = {
            'temp_files_deleted': 0,
            'cache_files_deleted': 0,
            'log_files_deleted': 0,
            'total_space_freed_mb': 0.0,
            'last_cleanup': None,
            'errors': 0
        }
    
    async def cleanup_temp_files(self) -> Dict:
        """
        Clean up temporary HTML and debug files
        
        Returns:
            Statistics about cleanup operation
        """
        deleted = 0
        space_freed = 0
        errors = 0
        
        # Patterns for temporary files
        temp_patterns = [
            '*.html',
            'debug_*.html',
            'test_*.html',
            'temp_*.html',
            '*_dump.html',
            '*_debug.html'
        ]
        
        current_time = time.time()
        
        for temp_dir in self.temp_dirs:
            if not temp_dir.exists():
                continue
            
            for pattern in temp_patterns:
                for file_path in temp_dir.glob(pattern):
                    try:
                        # Check file age
                        file_age = current_time - file_path.stat().st_mtime
                        
                        if file_age > self.max_temp_age:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            deleted += 1
                            space_freed += file_size
                            logger.debug(f"Deleted temp file: {file_path.name}")
                    
                    except Exception as e:
                        logger.error(f"Error deleting temp file {file_path}: {e}")
                        errors += 1
        
        self.stats['temp_files_deleted'] += deleted
        self.stats['total_space_freed_mb'] += space_freed / (1024 * 1024)
        self.stats['errors'] += errors
        
        logger.info(f"Temp cleanup: {deleted} files deleted, {space_freed / (1024 * 1024):.2f} MB freed")
        
        return {
            'files_deleted': deleted,
            'space_freed_mb': space_freed / (1024 * 1024),
            'errors': errors
        }
    
    async def cleanup_cache_files(self, force_size_limit: bool = True) -> Dict:
        """
        Clean up old cache files and enforce size limits
        
        Args:
            force_size_limit: If True, delete oldest files if size limit exceeded
        
        Returns:
            Statistics about cleanup operation
        """
        deleted = 0
        space_freed = 0
        errors = 0
        
        current_time = time.time()
        
        for cache_dir in self.cache_dirs:
            if not cache_dir.exists():
                continue
            
            # Get all cache files with their stats
            cache_files = []
            total_size = 0
            
            for file_path in cache_dir.glob("*.cache"):
                try:
                    stat = file_path.stat()
                    cache_files.append({
                        'path': file_path,
                        'size': stat.st_size,
                        'mtime': stat.st_mtime
                    })
                    total_size += stat.st_size
                except Exception as e:
                    logger.error(f"Error reading cache file {file_path}: {e}")
                    errors += 1
            
            # Delete old files
            for file_info in cache_files:
                try:
                    file_age = current_time - file_info['mtime']
                    
                    if file_age > self.max_cache_age:
                        file_info['path'].unlink()
                        deleted += 1
                        space_freed += file_info['size']
                        total_size -= file_info['size']
                        logger.debug(f"Deleted old cache file: {file_info['path'].name}")
                
                except Exception as e:
                    logger.error(f"Error deleting cache file {file_info['path']}: {e}")
                    errors += 1
            
            # Enforce size limit if needed
            if force_size_limit and total_size > self.max_cache_size:
                # Sort by modification time (oldest first)
                remaining_files = [f for f in cache_files if f['path'].exists()]
                remaining_files.sort(key=lambda x: x['mtime'])
                
                # Delete oldest files until under limit
                for file_info in remaining_files:
                    if total_size <= self.max_cache_size:
                        break
                    
                    try:
                        file_info['path'].unlink()
                        deleted += 1
                        space_freed += file_info['size']
                        total_size -= file_info['size']
                        logger.debug(f"Deleted cache file (size limit): {file_info['path'].name}")
                    
                    except Exception as e:
                        logger.error(f"Error deleting cache file {file_info['path']}: {e}")
                        errors += 1
        
        self.stats['cache_files_deleted'] += deleted
        self.stats['total_space_freed_mb'] += space_freed / (1024 * 1024)
        self.stats['errors'] += errors
        
        logger.info(f"Cache cleanup: {deleted} files deleted, {space_freed / (1024 * 1024):.2f} MB freed")
        
        return {
            'files_deleted': deleted,
            'space_freed_mb': space_freed / (1024 * 1024),
            'errors': errors
        }
    
    async def cleanup_log_files(self) -> Dict:
        """
        Clean up old log files
        
        Returns:
            Statistics about cleanup operation
        """
        deleted = 0
        space_freed = 0
        errors = 0
        
        current_time = time.time()
        
        log_patterns = ['*.log', '*.log.*']
        
        for log_dir in self.log_dirs:
            if not log_dir.exists():
                continue
            
            for pattern in log_patterns:
                for file_path in log_dir.glob(pattern):
                    try:
                        file_age = current_time - file_path.stat().st_mtime
                        
                        if file_age > self.max_log_age:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            deleted += 1
                            space_freed += file_size
                            logger.debug(f"Deleted old log file: {file_path.name}")
                    
                    except Exception as e:
                        logger.error(f"Error deleting log file {file_path}: {e}")
                        errors += 1
        
        self.stats['log_files_deleted'] += deleted
        self.stats['total_space_freed_mb'] += space_freed / (1024 * 1024)
        self.stats['errors'] += errors
        
        logger.info(f"Log cleanup: {deleted} files deleted, {space_freed / (1024 * 1024):.2f} MB freed")
        
        return {
            'files_deleted': deleted,
            'space_freed_mb': space_freed / (1024 * 1024),
            'errors': errors
        }
    
    async def cleanup_all(self) -> Dict:
        """
        Run all cleanup tasks
        
        Returns:
            Combined statistics
        """
        logger.info("Starting full cleanup...")
        
        temp_stats = await self.cleanup_temp_files()
        cache_stats = await self.cleanup_cache_files()
        log_stats = await self.cleanup_log_files()
        
        self.stats['last_cleanup'] = time.time()
        
        total_deleted = (
            temp_stats['files_deleted'] +
            cache_stats['files_deleted'] +
            log_stats['files_deleted']
        )
        
        total_freed = (
            temp_stats['space_freed_mb'] +
            cache_stats['space_freed_mb'] +
            log_stats['space_freed_mb']
        )
        
        logger.info(f"Cleanup complete: {total_deleted} files deleted, {total_freed:.2f} MB freed")
        
        return {
            'temp': temp_stats,
            'cache': cache_stats,
            'logs': log_stats,
            'total_files_deleted': total_deleted,
            'total_space_freed_mb': round(total_freed, 2)
        }
    
    async def start_scheduled_cleanup(self, interval_hours: int = 24):
        """
        Start background task for scheduled cleanup
        
        Args:
            interval_hours: Hours between cleanup runs
        """
        logger.info(f"Starting scheduled cleanup (every {interval_hours} hours)")
        
        while True:
            try:
                await asyncio.sleep(interval_hours * 3600)
                await self.cleanup_all()
            except Exception as e:
                logger.error(f"Error in scheduled cleanup: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour on error
    
    def get_stats(self) -> Dict:
        """Get cleanup statistics"""
        return {
            **self.stats,
            'last_cleanup_time': (
                datetime.fromtimestamp(self.stats['last_cleanup']).isoformat()
                if self.stats['last_cleanup'] else None
            )
        }
    
    async def safe_delete_file(self, file_path: Path) -> bool:
        """
        Safely delete a file with error handling
        
        Args:
            file_path: Path to file to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            self.stats['errors'] += 1
            return False
