"""Text processing utilities."""
import re
from typing import Optional


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def clean_html_remnants(text: str) -> str:
    """
    Remove HTML remnants from text.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    # Remove HTML entities
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    
    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    return text


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain name
    """
    match = re.search(r'https?://([^/]+)', url)
    if match:
        return match.group(1)
    return url


def normalize_url(url: str) -> str:
    """
    Normalize URL by removing fragments and trailing slashes.
    
    Args:
        url: Input URL
        
    Returns:
        Normalized URL
    """
    # Remove fragment
    url = url.split('#')[0]
    
    # Remove trailing slash
    if url.endswith('/') and url.count('/') > 3:
        url = url[:-1]
    
    return url


def count_tokens(text: str) -> int:
    """
    Approximate token count for text.
    
    Args:
        text: Input text
        
    Returns:
        Approximate token count
    """
    # Simple approximation: ~4 characters per token
    return len(text) // 4


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+\s+', text)
    return [s.strip() for s in sentences if s.strip()]
