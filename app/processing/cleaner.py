"""Text cleaning and normalization."""
import re
from typing import Optional
from app.utils.text import normalize_whitespace, clean_html_remnants
from app.utils.logger import get_logger

logger = get_logger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    # Remove HTML remnants
    text = clean_html_remnants(text)
    
    # Normalize whitespace
    text = normalize_whitespace(text)
    
    # Remove excessive punctuation
    text = re.sub(r'([!?.]){2,}', r'\1', text)
    
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove extra spaces around punctuation
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    
    # Normalize whitespace again after all replacements
    text = normalize_whitespace(text)
    
    return text


def remove_boilerplate(text: str, common_phrases: Optional[list[str]] = None) -> str:
    """
    Remove common boilerplate text.
    
    Args:
        text: Input text
        common_phrases: List of common phrases to remove
        
    Returns:
        Text with boilerplate removed
    """
    if not common_phrases:
        common_phrases = [
            'cookie policy',
            'privacy policy',
            'terms of service',
            'all rights reserved',
            'copyright',
            'skip to content',
            'back to top'
        ]
    
    text_lower = text.lower()
    
    for phrase in common_phrases:
        # Remove phrase and surrounding context
        pattern = re.compile(r'.{0,50}' + re.escape(phrase) + r'.{0,50}', re.IGNORECASE)
        text = pattern.sub('', text)
    
    return normalize_whitespace(text)


def validate_content(text: str, min_length: int = 100) -> bool:
    """
    Validate if content is substantial enough.
    
    Args:
        text: Text to validate
        min_length: Minimum character length
        
    Returns:
        True if content is valid
    """
    if not text or len(text) < min_length:
        return False
    
    # Check if it's mostly meaningful text (not just numbers/symbols)
    words = text.split()
    if len(words) < 20:
        return False
    
    return True
