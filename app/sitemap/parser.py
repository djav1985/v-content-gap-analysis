"""Sitemap parsing functionality."""
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import urljoin

from app.utils.logger import get_logger
from app.utils.text import normalize_url

logger = get_logger(__name__)


def parse_sitemap(xml_content: str, base_url: Optional[str] = None) -> list[str]:
    """
    Parse sitemap XML and extract URLs.
    
    Args:
        xml_content: Sitemap XML content
        base_url: Base URL for resolving relative URLs
        
    Returns:
        List of URLs found in sitemap
    """
    urls = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # Handle different sitemap formats
        namespaces = {
            'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'xhtml': 'http://www.w3.org/1999/xhtml'
        }
        
        # Check if it's a sitemap index
        sitemap_elements = root.findall('.//sm:sitemap/sm:loc', namespaces)
        if sitemap_elements:
            logger.info("Found sitemap index with nested sitemaps")
            for elem in sitemap_elements:
                if elem.text:
                    url = elem.text.strip()
                    if base_url:
                        url = urljoin(base_url, url)
                    urls.append(normalize_url(url))
        
        # Extract regular URLs
        url_elements = root.findall('.//sm:url/sm:loc', namespaces)
        for elem in url_elements:
            if elem.text:
                url = elem.text.strip()
                if base_url:
                    url = urljoin(base_url, url)
                urls.append(normalize_url(url))
        
        # Fallback: try without namespace
        if not urls:
            for elem in root.iter('loc'):
                if elem.text:
                    url = elem.text.strip()
                    if base_url:
                        url = urljoin(base_url, url)
                    urls.append(normalize_url(url))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        logger.info(f"Parsed {len(unique_urls)} unique URLs from sitemap")
        return unique_urls
        
    except ET.ParseError as e:
        logger.error(f"Failed to parse sitemap XML: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing sitemap: {e}")
        return []


def filter_urls(
    urls: list[str],
    include_patterns: Optional[list[str]] = None,
    exclude_patterns: Optional[list[str]] = None
) -> list[str]:
    """
    Filter URLs based on patterns.
    
    Args:
        urls: List of URLs to filter
        include_patterns: List of patterns to include (regex)
        exclude_patterns: List of patterns to exclude (regex)
        
    Returns:
        Filtered list of URLs
    """
    import re
    
    filtered = urls
    
    if include_patterns:
        filtered = [
            url for url in filtered
            if any(re.search(pattern, url) for pattern in include_patterns)
        ]
    
    if exclude_patterns:
        filtered = [
            url for url in filtered
            if not any(re.search(pattern, url) for pattern in exclude_patterns)
        ]
    
    logger.info(f"Filtered {len(urls)} URLs to {len(filtered)} URLs")
    return filtered
