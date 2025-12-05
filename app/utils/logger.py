"""Logging configuration for the SEO Gap Analysis Agent."""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter that adds structured context to log messages."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with structured context.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log message
        """
        # Add custom fields if present
        extras = []
        if hasattr(record, 'context'):
            context = record.context
            if isinstance(context, dict):
                for key, value in context.items():
                    extras.append(f"{key}={value}")
        
        # Add exception context if present
        if hasattr(record, 'error_type'):
            extras.append(f"error_type={record.error_type}")
        
        # Build the message
        base_msg = super().format(record)
        if extras:
            return f"{base_msg} [{', '.join(extras)}]"
        return base_msg


def setup_logger(
    name: str = "seo_gap_agent",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    use_structured: bool = True
) -> logging.Logger:
    """
    Set up and configure logger.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        use_structured: Whether to use structured formatter
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    if use_structured:
        formatter = StructuredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to create file handler for {log_file}: {e}")
    
    return logger


def get_logger(name: str = "seo_gap_agent") -> logging.Logger:
    """
    Get existing logger or create a new one.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    error_type: Optional[str] = None,
    exc_info: bool = False
) -> None:
    """
    Log message with structured context.
    
    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        context: Optional context dictionary
        error_type: Optional error type classification
        exc_info: Whether to include exception info
    """
    extra = {}
    if context:
        extra['context'] = context
    if error_type:
        extra['error_type'] = error_type
    
    logger.log(level, message, extra=extra, exc_info=exc_info)
