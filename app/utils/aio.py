"""Async utilities for HTTP requests."""
import asyncio
from typing import Optional, Dict, List
from urllib.parse import urlparse

import aiohttp
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages shared aiohttp session with per-host limits."""
    
    def __init__(
        self,
        max_connections: int = 100,
        per_host_limit: int = 10,
        timeout: int = 30
    ):
        """
        Initialize session manager.
        
        Args:
            max_connections: Total connection limit
            per_host_limit: Connections per host
            timeout: Default timeout in seconds
        """
        self.max_connections = max_connections
        self.per_host_limit = per_host_limit
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create shared session."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.per_host_limit,
                ttl_dns_cache=300
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self._session
    
    async def close(self):
        """Close session if open."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None


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
    headers: Optional[dict] = None,
    session: Optional[aiohttp.ClientSession] = None
) -> dict[str, Optional[str]]:
    """
    Fetch multiple URLs concurrently.
    
    Args:
        urls: List of URLs to fetch
        max_concurrent: Maximum concurrent requests
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        headers: Optional HTTP headers
        session: Optional existing session to reuse
        
    Returns:
        Dictionary mapping URLs to their content
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}
    
    async def fetch_with_semaphore(sess: aiohttp.ClientSession, url: str):
        async with semaphore:
            content = await fetch_url(sess, url, timeout, retry_attempts)
            return url, content
    
    # Use provided session or create a new one
    should_close = session is None
    if session is None:
        connector = aiohttp.TCPConnector(
            limit=max_concurrent,
            limit_per_host=min(max_concurrent, 5)
        )
        session = aiohttp.ClientSession(connector=connector, headers=headers)
    
    try:
        tasks = [fetch_with_semaphore(session, url) for url in urls]
        responses = await asyncio.gather(*tasks)
        
        for url, content in responses:
            results[url] = content
    finally:
        if should_close:
            await session.close()
    
    return results


async def fetch_urls_concurrent(
    urls: List[str],
    max_concurrent: int = 10,
    timeout: int = 30,
    retry_attempts: int = 3,
    headers: Optional[Dict[str, str]] = None,
    session_manager: Optional[SessionManager] = None
) -> Dict[str, Optional[str]]:
    """
    Fetch multiple URLs using a shared session manager.
    
    Args:
        urls: List of URLs to fetch
        max_concurrent: Maximum concurrent requests
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        headers: Optional HTTP headers
        session_manager: Optional session manager to reuse
        
    Returns:
        Dictionary mapping URLs to their content
    """
    should_close = session_manager is None
    if session_manager is None:
        session_manager = SessionManager(
            max_connections=max_concurrent * 2,
            per_host_limit=min(max_concurrent, 5),
            timeout=timeout
        )
    
    session = await session_manager.get_session()
    
    # Update headers if provided
    if headers:
        session._default_headers.update(headers)
    
    try:
        results = await fetch_urls_batch(
            urls,
            max_concurrent,
            timeout,
            retry_attempts,
            headers=None,  # Already set on session
            session=session
        )
        return results
    finally:
        if should_close:
            await session_manager.close()
