"""Content extraction from HTML pages."""
import json
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from app.utils.logger import get_logger
from app.utils.text import normalize_whitespace, clean_html_remnants

logger = get_logger(__name__)


def extract_metadata(html: str) -> Dict[str, Optional[str]]:
    """
    Extract metadata from HTML.
    
    Args:
        html: HTML content
        
    Returns:
        Dictionary with metadata
    """
    soup = BeautifulSoup(html, 'lxml')
    
    metadata = {
        'title': None,
        'description': None,
        'h1': None,
        'canonical': None,
        'og_title': None,
        'og_description': None,
        'og_type': None
    }
    
    # Title
    title_tag = soup.find('title')
    if title_tag:
        metadata['title'] = normalize_whitespace(title_tag.get_text())
    
    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        metadata['description'] = normalize_whitespace(meta_desc['content'])
    
    # H1
    h1_tag = soup.find('h1')
    if h1_tag:
        metadata['h1'] = normalize_whitespace(h1_tag.get_text())
    
    # Canonical
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if canonical and canonical.get('href'):
        metadata['canonical'] = canonical['href']
    
    # Open Graph
    og_title = soup.find('meta', attrs={'property': 'og:title'})
    if og_title and og_title.get('content'):
        metadata['og_title'] = normalize_whitespace(og_title['content'])
    
    og_desc = soup.find('meta', attrs={'property': 'og:description'})
    if og_desc and og_desc.get('content'):
        metadata['og_description'] = normalize_whitespace(og_desc['content'])
    
    og_type = soup.find('meta', attrs={'property': 'og:type'})
    if og_type and og_type.get('content'):
        metadata['og_type'] = og_type['content']
    
    return metadata


def extract_schema(html: str) -> Optional[str]:
    """
    Extract schema.org JSON-LD data.
    
    Args:
        html: HTML content
        
    Returns:
        Schema JSON as string or None
    """
    soup = BeautifulSoup(html, 'lxml')
    
    schema_scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})
    
    if not schema_scripts:
        return None
    
    schemas = []
    for script in schema_scripts:
        try:
            # Guard against None or whitespace-only content
            if script.string and script.string.strip():
                schema_data = json.loads(script.string)
                schemas.append(schema_data)
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue
    
    if schemas:
        return json.dumps(schemas, ensure_ascii=False)
    
    return None


def extract_content(html: str) -> str:
    """
    Extract main content text from HTML.
    
    Args:
        html: HTML content
        
    Returns:
        Extracted content text
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
        element.decompose()
    
    # Try to find main content area
    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
    
    if main_content:
        text = main_content.get_text(separator=' ', strip=True)
    else:
        text = soup.get_text(separator=' ', strip=True)
    
    # Clean the text
    text = clean_html_remnants(text)
    text = normalize_whitespace(text)
    
    return text


def extract_headings(html: str) -> Dict[str, List[str]]:
    """
    Extract all headings from HTML.
    
    Args:
        html: HTML content
        
    Returns:
        Dictionary with heading levels and their texts
    """
    soup = BeautifulSoup(html, 'lxml')
    
    headings = {
        'h1': [],
        'h2': [],
        'h3': [],
        'h4': [],
        'h5': [],
        'h6': []
    }
    
    for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        tags = soup.find_all(level)
        headings[level] = [normalize_whitespace(tag.get_text()) for tag in tags]
    
    return headings


def extract_page_data(html: str) -> Dict[str, Any]:
    """
    Extract all relevant data from HTML page.
    
    Args:
        html: HTML content
        
    Returns:
        Dictionary with all extracted data
    """
    metadata = extract_metadata(html)
    content = extract_content(html)
    headings = extract_headings(html)
    schema = extract_schema(html)
    
    word_count = len(content.split())
    
    return {
        'metadata': metadata,
        'content': content,
        'headings': headings,
        'schema': schema,
        'word_count': word_count
    }
