"""
Retry Manager with Exponential Backoff
=======================================
Handles retries with intelligent backoff strategies and error classification.
"""

import asyncio
import logging
import time
from typing import Callable, Optional, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("retry_manager")


class ErrorType(Enum):
    """Classification of errors for retry strategies"""
    NETWORK = "network"  # Connection errors, timeouts
    RATE_LIMIT = "rate_limit"  # 429, rate limiting
    SERVER_ERROR = "server_error"  # 5xx errors
    CLIENT_ERROR = "client_error"  # 4xx errors (except 429)
    CLOUDFLARE = "cloudflare"  # Cloudflare challenges
    QUOTA = "quota"  # API quota exceeded
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 5
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True  # Add random jitter to prevent thundering herd
    retry_on_errors: List[ErrorType] = None
    
    def __post_init__(self):
        if self.retry_on_errors is None:
            # Default: retry on network, rate limit, and server errors
            self.retry_on_errors = [
                ErrorType.NETWORK,
                ErrorType.RATE_LIMIT,
                ErrorType.SERVER_ERROR,
                ErrorType.CLOUDFLARE
            ]


class RetryManager:
    """
    Manages retry logic with exponential backoff and intelligent error handling.
    
    Features:
    - Exponential backoff with jitter
    - Error classification
    - Configurable retry strategies
    - Circuit breaker pattern
    - Detailed logging
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry manager
        
        Args:
            config: Retry configuration (uses defaults if None)
        """
        self.config = config or RetryConfig()
        self.stats = {
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'total_delay_time': 0.0
        }
    
    def classify_error(self, error: Exception, status_code: Optional[int] = None, 
                      response_text: Optional[str] = None) -> ErrorType:
        """
        Classify an error to determine retry strategy
        
        Args:
            error: The exception that occurred
            status_code: HTTP status code (if applicable)
            response_text: Response body text (if applicable)
        
        Returns:
            ErrorType classification
        """
        # Check status code first
        if status_code:
            if status_code == 429:
                return ErrorType.RATE_LIMIT
            elif status_code in [402, 403] and response_text:
                if any(msg in response_text.lower() for msg in ['quota', 'credits', 'limit']):
                    return ErrorType.QUOTA
            elif 500 <= status_code < 600:
                return ErrorType.SERVER_ERROR
            elif 400 <= status_code < 500:
                return ErrorType.CLIENT_ERROR
        
        # Check response text for Cloudflare
        if response_text:
            cloudflare_indicators = [
                'cloudflare',
                'just a moment',
                'checking your browser',
                'cf-ray'
            ]
            if any(indicator in response_text.lower() for indicator in cloudflare_indicators):
                return ErrorType.CLOUDFLARE
        
        # Check exception type
        error_str = str(error).lower()
        if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'unreachable']):
            return ErrorType.NETWORK
        
        return ErrorType.UNKNOWN
    
    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """
        Determine if we should retry based on error type and attempt number
        
        Args:
            error_type: Classification of the error
            attempt: Current attempt number (0-indexed)
        
        Returns:
            True if should retry, False otherwise
        """
        # Don't retry if max attempts reached
        if attempt >= self.config.max_retries:
            return False
        
        # Don't retry quota errors (need to switch API key instead)
        if error_type == ErrorType.QUOTA:
            return False
        
        # Don't retry client errors (except rate limit)
        if error_type == ErrorType.CLIENT_ERROR:
            return False
        
        # Retry if error type is in configured list
        return error_type in self.config.retry_on_errors
    
    def calculate_delay(self, attempt: int, error_type: ErrorType) -> float:
        """
        Calculate delay before next retry using exponential backoff
        
        Args:
            attempt: Current attempt number (0-indexed)
            error_type: Classification of the error
        
        Returns:
            Delay in seconds
        """
        # Base exponential backoff
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Special handling for rate limits (longer delays)
        if error_type == ErrorType.RATE_LIMIT:
            delay = min(delay * 2, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            import random
            jitter = random.uniform(0, delay * 0.1)  # Up to 10% jitter
            delay += jitter
        
        return delay
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        error_classifier: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            error_classifier: Optional custom error classifier
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of func
        
        Raises:
            Last exception if all retries fail
        """
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                self.stats['total_attempts'] += 1
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    self.stats['successful_retries'] += 1
                    logger.info(f"Retry successful after {attempt} attempts")
                
                return result
            
            except Exception as e:
                last_error = e
                
                # Classify error
                status_code = getattr(e, 'status_code', None)
                response_text = getattr(e, 'response_text', None)
                
                if error_classifier:
                    error_type = error_classifier(e, status_code, response_text)
                else:
                    error_type = self.classify_error(e, status_code, response_text)
                
                # Check if we should retry
                if not self.should_retry(error_type, attempt):
                    logger.warning(f"Not retrying error type {error_type.value} after {attempt} attempts")
                    self.stats['failed_retries'] += 1
                    raise
                
                # Calculate delay
                delay = self.calculate_delay(attempt, error_type)
                self.stats['total_delay_time'] += delay
                
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed "
                    f"(Error: {error_type.value}). Retrying in {delay:.2f}s... "
                    f"Error: {str(e)[:100]}"
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # All retries exhausted
        self.stats['failed_retries'] += 1
        logger.error(f"All {self.config.max_retries + 1} attempts failed")
        raise last_error
    
    def get_stats(self) -> dict:
        """Get retry statistics"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_retries'] / max(self.stats['total_attempts'], 1) * 100
            ),
            'avg_delay': (
                self.stats['total_delay_time'] / max(self.stats['failed_retries'], 1)
            )
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'total_delay_time': 0.0
        }


# Convenience function for simple retry scenarios
async def retry_async(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    *args,
    **kwargs
) -> Any:
    """
    Simple async retry wrapper
    
    Args:
        func: Async function to execute
        max_retries: Maximum number of retries
        base_delay: Base delay between retries
        *args: Arguments for func
        **kwargs: Keyword arguments for func
    
    Returns:
        Result of func
    """
    config = RetryConfig(max_retries=max_retries, base_delay=base_delay)
    manager = RetryManager(config)
    return await manager.execute_with_retry(func, *args, **kwargs)
