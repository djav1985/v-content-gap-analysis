"""HTML page fetching functionality."""
from typing import Optional

from app.utils.aio import fetch_urls_batch
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def fetch_pages(
    urls: list[str],
    max_concurrent: int = 10,
    timeout: int = 30,
    retry_attempts: int = 3,
    user_agent: str = "SEO-Gap-Analysis-Agent/1.0"
) -> dict[str, Optional[str]]:
    """
    Fetch HTML content for multiple pages.
    
    Args:
        urls: List of page URLs
        max_concurrent: Maximum concurrent requests
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        user_agent: User agent string
        
    Returns:
        Dictionary mapping URLs to their HTML content
    """
    headers = {"User-Agent": user_agent}
    
    logger.info(f"Fetching {len(urls)} pages with {max_concurrent} concurrent requests")
    
    results = await fetch_urls_batch(
        urls=urls,
        max_concurrent=max_concurrent,
        timeout=timeout,
        retry_attempts=retry_attempts,
        headers=headers
    )
    
    successful = sum(1 for content in results.values() if content is not None)
    logger.info(f"Successfully fetched {successful}/{len(urls)} pages")
    
    return results
