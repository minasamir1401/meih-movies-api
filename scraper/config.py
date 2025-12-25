"""
Configuration Management
========================
Centralized configuration for the scraping system.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ScrapingAntConfig:
    """ScrapingAnt API configuration"""
    api_keys: List[str] = field(default_factory=lambda: [
        "081cb06a3398496b846339716110d5e0",
        "9887fa3dd82d439c8e6f753439cfa1e6",
        "1e1b5f0ca90d4b0c88c04bda127eff0e",
        "06322a53d873408993dcb023ad513c5f",
        "07194a68784d4b13a148a85c6a2e152d",
        "54a445f5ab2a44cda0266e3d0a871468",
        "c5f11017dff84918807b9d453f35e857",
        "e0c1d18e05f9493bb8ec632f43c92da2"
    ])
    enabled: bool = True
    js_rendering_default: bool = False
    timeout: int = 60
    proxy_type: Optional[str] = None  # datacenter, residential
    proxy_country: Optional[str] = None


@dataclass
class CacheConfig:
    """Cache configuration"""
    enabled: bool = True
    memory_size: int = 1000
    memory_ttl: int = 3600  # 1 hour
    file_cache_dir: str = ".cache"
    file_ttl: int = 86400  # 24 hours
    max_cache_size_mb: int = 500


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CleanupConfig:
    """Cleanup configuration"""
    enabled: bool = True
    temp_dirs: List[str] = field(default_factory=lambda: ["."])
    cache_dirs: List[str] = field(default_factory=lambda: [".cache"])
    log_dirs: List[str] = field(default_factory=lambda: ["logs"])
    max_temp_age_hours: int = 24
    max_cache_age_days: int = 7
    max_log_age_days: int = 30
    max_cache_size_mb: int = 500
    cleanup_interval_hours: int = 24


@dataclass
class LoggingConfig:
    """Logging configuration"""
    app_name: str = "scraper"
    log_dir: str = "logs"
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    json_logs: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class ScraperConfig:
    """Main scraper configuration"""
    # Network nodes (domains)
    network_nodes: List[str] = field(default_factory=lambda: [
        "https://larooza.site",
        "https://larooza.video",
        "https://larooza.net",
        "https://larooza.tv",
        "https://larooza.icu",
        "https://q.larozavideo.net"
    ])
    
    # Concurrency
    max_concurrent_requests: int = 30
    
    # Timeouts
    request_timeout: int = 15
    page_timeout: int = 25
    
    # User agents
    user_agents: List[str] = field(default_factory=lambda: [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    ])
    
    # Tier priorities (1 = highest priority)
    tier_priorities: List[str] = field(default_factory=lambda: [
        "node_proxy",      # Tier 1: Fast local proxy
        "direct",          # Tier 2: Direct HTTP
        "curl_cffi",       # Tier 3: TLS fingerprint bypass
        "scrapingant",     # Tier 4: ScrapingAnt (costs money)
        "playwright"       # Tier 5: Full browser (heavy)
    ])
    
    # Enable/disable specific tiers
    enable_node_proxy: bool = True
    enable_direct: bool = True
    enable_curl_cffi: bool = True
    enable_scrapingant: bool = True
    enable_playwright: bool = True
    
    # Node proxy URL
    node_proxy_url: str = "http://localhost:3001"


@dataclass
class Config:
    """Main configuration object"""
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    scrapingant: ScrapingAntConfig = field(default_factory=ScrapingAntConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    cleanup: CleanupConfig = field(default_factory=CleanupConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        config = cls()
        
        # ScrapingAnt
        if os.getenv("SCRAPINGANT_ENABLED"):
            config.scrapingant.enabled = os.getenv("SCRAPINGANT_ENABLED").lower() == "true"
        
        # Cache
        if os.getenv("CACHE_ENABLED"):
            config.cache.enabled = os.getenv("CACHE_ENABLED").lower() == "true"
        if os.getenv("CACHE_DIR"):
            config.cache.file_cache_dir = os.getenv("CACHE_DIR")
        
        # Logging
        if os.getenv("LOG_LEVEL"):
            config.logging.console_level = os.getenv("LOG_LEVEL")
        if os.getenv("LOG_DIR"):
            config.logging.log_dir = os.getenv("LOG_DIR")
        
        # Scraper
        if os.getenv("NETWORK_NODES"):
            config.scraper.network_nodes = os.getenv("NETWORK_NODES").split(",")
        if os.getenv("NODE_PROXY_URL"):
            config.scraper.node_proxy_url = os.getenv("NODE_PROXY_URL")
        if os.getenv("MAX_CONCURRENT_REQUESTS"):
            config.scraper.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS"))
        
        return config


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config):
    """Set global configuration instance"""
    global _config
    _config = config
