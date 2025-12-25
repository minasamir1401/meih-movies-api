"""
Centralized Logging System
===========================
Provides structured logging with multiple handlers and formatters.
"""

import logging
import sys
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing and analysis"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console output for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        return super().format(record)


class LoggingManager:
    """
    Centralized logging manager for the entire application.
    
    Features:
    - Multiple log levels and handlers
    - File rotation
    - JSON and colored console output
    - Performance tracking
    - Error aggregation
    """
    
    def __init__(
        self,
        app_name: str = "scraper",
        log_dir: str = "logs",
        console_level: str = "INFO",
        file_level: str = "DEBUG",
        json_logs: bool = True,
        max_file_size_mb: int = 10,
        backup_count: int = 5
    ):
        """
        Initialize logging manager
        
        Args:
            app_name: Application name for log files
            log_dir: Directory for log files
            console_level: Logging level for console output
            file_level: Logging level for file output
            json_logs: Whether to create JSON log files
            max_file_size_mb: Maximum size of each log file (MB)
            backup_count: Number of backup files to keep
        """
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.console_level = getattr(logging, console_level.upper())
        self.file_level = getattr(logging, file_level.upper())
        self.json_logs = json_logs
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.backup_count = backup_count
        
        # Statistics
        self.stats = {
            'debug': 0,
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0
        }
        
        # Setup root logger
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Configure the root logger with handlers"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture everything
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (rotating)
        file_handler = RotatingFileHandler(
            self.log_dir / f"{self.app_name}.log",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.file_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # JSON handler (if enabled)
        if self.json_logs:
            json_handler = RotatingFileHandler(
                self.log_dir / f"{self.app_name}.json",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            json_handler.setLevel(self.file_level)
            json_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(json_handler)
        
        # Error-only handler
        error_handler = RotatingFileHandler(
            self.log_dir / f"{self.app_name}_errors.log",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance
        
        Args:
            name: Logger name (usually __name__)
        
        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)
    
    def log_with_context(
        self,
        logger: logging.Logger,
        level: str,
        message: str,
        **context
    ):
        """
        Log a message with additional context
        
        Args:
            logger: Logger instance
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **context: Additional context data
        """
        log_func = getattr(logger, level.lower())
        
        # Create a log record with extra data
        extra = {'extra_data': context}
        log_func(message, extra=extra)
        
        # Update stats
        level_lower = level.lower()
        if level_lower in self.stats:
            self.stats[level_lower] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        total = sum(self.stats.values())
        return {
            **self.stats,
            'total': total,
            'error_rate': (self.stats['error'] + self.stats['critical']) / max(total, 1) * 100
        }
    
    def reset_stats(self):
        """Reset logging statistics"""
        for key in self.stats:
            self.stats[key] = 0


class PerformanceLogger:
    """Context manager for logging performance metrics"""
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        """
        Initialize performance logger
        
        Args:
            logger: Logger instance
            operation: Name of the operation being timed
            **context: Additional context
        """
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting: {self.operation}", extra={'extra_data': self.context})
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f"Completed: {self.operation} ({duration:.2f}s)",
                extra={'extra_data': {**self.context, 'duration': duration}}
            )
        else:
            self.logger.error(
                f"Failed: {self.operation} ({duration:.2f}s) - {exc_val}",
                extra={'extra_data': {**self.context, 'duration': duration, 'error': str(exc_val)}}
            )


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def setup_logging(
    app_name: str = "scraper",
    log_dir: str = "logs",
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    json_logs: bool = True
) -> LoggingManager:
    """
    Setup global logging configuration
    
    Args:
        app_name: Application name
        log_dir: Directory for log files
        console_level: Console logging level
        file_level: File logging level
        json_logs: Enable JSON logs
    
    Returns:
        LoggingManager instance
    """
    global _logging_manager
    _logging_manager = LoggingManager(
        app_name=app_name,
        log_dir=log_dir,
        console_level=console_level,
        file_level=file_level,
        json_logs=json_logs
    )
    return _logging_manager


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance (convenience function)
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    if _logging_manager is None:
        setup_logging()
    return _logging_manager.get_logger(name)
