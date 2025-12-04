"""Async utilities for HTTP requests."""
import asyncio
from typing import Optional

import aiohttp
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def fetch_url(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 30,
    retry_attempts: int = 3
) -> Optional[str]:
    """
    Fetch URL content with retry logic.
    
    Args:
        session: Aiohttp client session
        url: URL to fetch
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        
    Returns:
        Response text or None if failed
    """
    for attempt in range(retry_attempts):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{retry_attempts})")
        except aiohttp.ClientError as e:
            logger.warning(f"Client error fetching {url}: {e} (attempt {attempt + 1}/{retry_attempts})")
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            break
        
        if attempt < retry_attempts - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return None


async def fetch_urls_batch(
    urls: list[str],
    max_concurrent: int = 10,
    timeout: int = 30,
    retry_attempts: int = 3,
    headers: Optional[dict] = None
) -> dict[str, Optional[str]]:
    """
    Fetch multiple URLs concurrently.
    
    Args:
        urls: List of URLs to fetch
        max_concurrent: Maximum concurrent requests
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        headers: Optional HTTP headers
        
    Returns:
        Dictionary mapping URLs to their content
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}
    
    async def fetch_with_semaphore(session: aiohttp.ClientSession, url: str):
        async with semaphore:
            content = await fetch_url(session, url, timeout, retry_attempts)
            return url, content
    
    connector = aiohttp.TCPConnector(limit=max_concurrent)
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [fetch_with_semaphore(session, url) for url in urls]
        responses = await asyncio.gather(*tasks)
        
        for url, content in responses:
            results[url] = content
    
    return results
