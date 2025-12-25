"""
ScrapingAnt API Client
======================
Enhanced client for ScrapingAnt API with key rotation and error handling.
"""

import aiohttp
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from .api_key_manager import APIKeyManager
from .retry_manager import RetryManager, RetryConfig, ErrorType

logger = logging.getLogger("scrapingant_client")


class ScrapingAntError(Exception):
    """Base exception for ScrapingAnt errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class ScrapingAntClient:
    """
    Enhanced ScrapingAnt API client with intelligent key rotation.
    
    Features:
    - Automatic API key rotation
    - Quota tracking
    - Retry logic with exponential backoff
    - JavaScript rendering support
    - Proxy support
    - Custom headers
    """
    
    BASE_URL = "https://api.scrapingant.com/v2/general"
    
    def __init__(
        self,
        api_keys: list[str],
        key_manager: Optional[APIKeyManager] = None,
        retry_manager: Optional[RetryManager] = None,
        timeout: int = 60
    ):
        """
        Initialize ScrapingAnt client
        
        Args:
            api_keys: List of ScrapingAnt API keys
            key_manager: API key manager (creates new if None)
            retry_manager: Retry manager (creates new if None)
            timeout: Request timeout in seconds
        """
        self.api_keys = api_keys
        self.key_manager = key_manager or APIKeyManager(api_keys)
        
        # Configure retry manager for ScrapingAnt
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=2.0,
            max_delay=30.0,
            retry_on_errors=[
                ErrorType.NETWORK,
                ErrorType.RATE_LIMIT,
                ErrorType.SERVER_ERROR,
                ErrorType.CLOUDFLARE
            ]
        )
        self.retry_manager = retry_manager or RetryManager(retry_config)
        
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'key_rotations': 0,
            'total_credits_used': 0
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def scrape(
        self,
        url: str,
        js_rendering: bool = False,
        proxy_type: Optional[str] = None,
        proxy_country: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        wait_for_selector: Optional[str] = None,
        browser: bool = True
    ) -> str:
        """
        Scrape a URL using ScrapingAnt API
        
        Args:
            url: URL to scrape
            js_rendering: Enable JavaScript rendering
            proxy_type: Proxy type (datacenter, residential)
            proxy_country: Proxy country code
            custom_headers: Custom HTTP headers
            cookies: Cookies to send
            wait_for_selector: CSS selector to wait for (requires js_rendering)
            browser: Use browser mode (recommended)
        
        Returns:
            HTML content
        
        Raises:
            ScrapingAntError: If scraping fails after all retries
        """
        self.stats['total_requests'] += 1
        
        # Get current API key
        api_key = self.key_manager.get_current_key()
        if not api_key:
            raise ScrapingAntError("All API keys are blacklisted or exhausted")
        
        # Estimate credits (1 for basic, 10 for JS rendering)
        estimated_credits = 10 if js_rendering else 1
        
        # Build request parameters
        params = {
            'url': url,
            'x-api-key': api_key,
            'browser': 'true' if browser else 'false'
        }
        
        if js_rendering:
            params['js_rendering'] = 'true'
        
        if proxy_type:
            params['proxy_type'] = proxy_type
        
        if proxy_country:
            params['proxy_country'] = proxy_country
        
        if wait_for_selector and js_rendering:
            params['wait_for_selector'] = wait_for_selector
        
        # Add custom headers
        if custom_headers:
            for key, value in custom_headers.items():
                params[f'x-custom-header-{key}'] = value
        
        # Add cookies
        if cookies:
            import json
            params['x-cookies'] = json.dumps(cookies)
        
        try:
            # Execute with retry logic
            content = await self.retry_manager.execute_with_retry(
                self._make_request,
                params,
                api_key,
                estimated_credits
            )
            
            self.stats['successful_requests'] += 1
            self.stats['total_credits_used'] += estimated_credits
            
            return content
        
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"ScrapingAnt request failed for {url}: {e}")
            raise ScrapingAntError(f"Failed to scrape {url}", response_text=str(e))
    
    async def _make_request(
        self,
        params: Dict[str, Any],
        api_key: str,
        estimated_credits: int
    ) -> str:
        """
        Make the actual API request
        
        Args:
            params: Request parameters
            api_key: API key to use
            estimated_credits: Estimated credits for this request
        
        Returns:
            Response content
        
        Raises:
            ScrapingAntError: If request fails
        """
        session = await self._get_session()
        
        try:
            async with session.get(self.BASE_URL, params=params, ssl=False) as response:
                content = await response.text()
                
                # Check for errors
                if response.status == 200:
                    # Success
                    self.key_manager.record_success(api_key, estimated_credits)
                    return content
                
                elif response.status == 429:
                    # Rate limit
                    logger.warning(f"Rate limit hit for key {self.key_manager._mask_key(api_key)}")
                    self.key_manager.record_failure(api_key, 429, "Rate limit exceeded")
                    self.stats['key_rotations'] += 1
                    
                    # Try with next key
                    next_key = self.key_manager.get_current_key()
                    if next_key and next_key != api_key:
                        params['x-api-key'] = next_key
                        return await self._make_request(params, next_key, estimated_credits)
                    
                    raise ScrapingAntError("Rate limit exceeded", status_code=429, response_text=content)
                
                elif response.status in [402, 403]:
                    # Quota or auth error
                    error_msg = "Quota exceeded" if response.status == 402 else "Forbidden"
                    logger.warning(f"{error_msg} for key {self.key_manager._mask_key(api_key)}")
                    self.key_manager.record_failure(api_key, response.status, error_msg)
                    self.stats['key_rotations'] += 1
                    
                    # Try with next key
                    next_key = self.key_manager.get_current_key()
                    if next_key and next_key != api_key:
                        params['x-api-key'] = next_key
                        return await self._make_request(params, next_key, estimated_credits)
                    
                    raise ScrapingAntError(error_msg, status_code=response.status, response_text=content)
                
                else:
                    # Other error
                    self.key_manager.record_failure(api_key, response.status, f"HTTP {response.status}")
                    raise ScrapingAntError(
                        f"Request failed with status {response.status}",
                        status_code=response.status,
                        response_text=content
                    )
        
        except aiohttp.ClientError as e:
            # Network error
            self.key_manager.record_failure(api_key, None, str(e))
            raise ScrapingAntError(f"Network error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            'client': self.stats,
            'key_manager': self.key_manager.get_stats(),
            'retry_manager': self.retry_manager.get_stats()
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
