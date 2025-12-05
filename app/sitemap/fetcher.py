"""Sitemap fetching functionality."""
import asyncio
from typing import Optional

import aiohttp
from app.utils.logger import get_logger
from app.utils.aio import fetch_url, SessionManager

logger = get_logger(__name__)


async def fetch_sitemap(
    url: str,
    timeout: int = 30,
    retry_attempts: int = 3,
    user_agent: str = "SEO-Gap-Analysis-Agent/1.0",
    session: Optional[aiohttp.ClientSession] = None
) -> Optional[str]:
    """
    Fetch sitemap XML content.
    
    Args:
        url: Sitemap URL
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        user_agent: User agent string
        session: Optional existing session to reuse
        
    Returns:
        Sitemap XML content or None if failed
    """
    headers = {"User-Agent": user_agent}
    
    should_close = session is None
    if session is None:
        session = aiohttp.ClientSession(headers=headers)
    
    try:
        content = await fetch_url(session, url, timeout, retry_attempts)
        
        if content:
            logger.info(f"Successfully fetched sitemap: {url}")
        else:
            logger.error(f"Failed to fetch sitemap: {url}")
        
        return content
    finally:
        if should_close:
            await session.close()


async def fetch_sitemaps(
    urls: list[str],
    timeout: int = 30,
    retry_attempts: int = 3,
    user_agent: str = "SEO-Gap-Analysis-Agent/1.0",
    max_concurrent: int = 5,
    session_manager: Optional[SessionManager] = None
) -> dict[str, Optional[str]]:
    """
    Fetch multiple sitemaps concurrently with shared session.
    
    Args:
        urls: List of sitemap URLs
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        user_agent: User agent string
        max_concurrent: Maximum concurrent requests
        session_manager: Optional session manager to reuse
        
    Returns:
        Dictionary mapping URLs to their XML content
    """
    results = {}
    headers = {"User-Agent": user_agent}
    
    should_close = session_manager is None
    if session_manager is None:
        session_manager = SessionManager(
            max_connections=max_concurrent * 2,
            per_host_limit=max_concurrent,
            timeout=timeout
        )
    
    session = await session_manager.get_session()
    
    try:
        # Fetch sitemaps concurrently with semaphore
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url: str):
            async with semaphore:
                content = await fetch_url(session, url, timeout, retry_attempts, headers)
                if content:
                    logger.info(f"Successfully fetched sitemap: {url}")
                else:
                    logger.error(f"Failed to fetch sitemap: {url}")
                return url, content
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        
        for url, content in responses:
            results[url] = content
            
        logger.info(f"Fetched {len([c for c in results.values() if c])}/{len(urls)} sitemaps successfully")
        
    finally:
        if should_close:
            await session_manager.close()
    
    return results
