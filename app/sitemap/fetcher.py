"""Sitemap fetching functionality."""
from typing import Optional

import aiohttp
from app.utils.logger import get_logger
from app.utils.aio import fetch_url

logger = get_logger(__name__)


async def fetch_sitemap(
    url: str,
    timeout: int = 30,
    retry_attempts: int = 3,
    user_agent: str = "SEO-Gap-Analysis-Agent/1.0"
) -> Optional[str]:
    """
    Fetch sitemap XML content.
    
    Args:
        url: Sitemap URL
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        user_agent: User agent string
        
    Returns:
        Sitemap XML content or None if failed
    """
    headers = {"User-Agent": user_agent}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        content = await fetch_url(session, url, timeout, retry_attempts)
        
        if content:
            logger.info(f"Successfully fetched sitemap: {url}")
        else:
            logger.error(f"Failed to fetch sitemap: {url}")
        
        return content


async def fetch_sitemaps(
    urls: list[str],
    timeout: int = 30,
    retry_attempts: int = 3,
    user_agent: str = "SEO-Gap-Analysis-Agent/1.0"
) -> dict[str, Optional[str]]:
    """
    Fetch multiple sitemaps.
    
    Args:
        urls: List of sitemap URLs
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        user_agent: User agent string
        
    Returns:
        Dictionary mapping URLs to their XML content
    """
    results = {}
    headers = {"User-Agent": user_agent}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for url in urls:
            content = await fetch_url(session, url, timeout, retry_attempts)
            results[url] = content
            
            if content:
                logger.info(f"Successfully fetched sitemap: {url}")
            else:
                logger.error(f"Failed to fetch sitemap: {url}")
    
    return results
