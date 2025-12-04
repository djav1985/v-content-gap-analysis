"""Metadata extraction and processing."""
from typing import Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_metadata_signals(metadata: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """
    Extract SEO signals from metadata.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        Dictionary with SEO signals
    """
    signals = {
        'has_title': bool(metadata.get('title')),
        'has_description': bool(metadata.get('description')),
        'has_h1': bool(metadata.get('h1')),
        'has_canonical': bool(metadata.get('canonical')),
        'has_og_tags': bool(metadata.get('og_title') or metadata.get('og_description')),
        'title_length': len(metadata.get('title', '')) if metadata.get('title') else 0,
        'description_length': len(metadata.get('description', '')) if metadata.get('description') else 0
    }
    
    # Check for issues
    signals['title_too_short'] = signals['title_length'] < 30
    signals['title_too_long'] = signals['title_length'] > 60
    signals['description_too_short'] = signals['description_length'] < 120
    signals['description_too_long'] = signals['description_length'] > 160
    
    return signals


def compare_metadata(primary_meta: Dict[str, Any], competitor_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare metadata between primary and competitor pages.
    
    Args:
        primary_meta: Primary page metadata signals
        competitor_meta: Competitor page metadata signals
        
    Returns:
        Comparison results
    """
    comparison = {
        'missing_elements': [],
        'quality_gaps': []
    }
    
    # Check for missing elements
    if competitor_meta.get('has_title') and not primary_meta.get('has_title'):
        comparison['missing_elements'].append('title')
    
    if competitor_meta.get('has_description') and not primary_meta.get('has_description'):
        comparison['missing_elements'].append('description')
    
    if competitor_meta.get('has_h1') and not primary_meta.get('has_h1'):
        comparison['missing_elements'].append('h1')
    
    if competitor_meta.get('has_og_tags') and not primary_meta.get('has_og_tags'):
        comparison['missing_elements'].append('og_tags')
    
    # Check quality gaps
    if competitor_meta.get('title_length', 0) > primary_meta.get('title_length', 0) * 1.5:
        comparison['quality_gaps'].append('title_shorter')
    
    if competitor_meta.get('description_length', 0) > primary_meta.get('description_length', 0) * 1.5:
        comparison['quality_gaps'].append('description_shorter')
    
    return comparison
