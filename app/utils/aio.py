"""Async utilities for HTTP requests."""
import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

import aiohttp
from app.utils.logger import get_logger, log_with_context

logger = get_logger(__name__)

# Constants
DEFAULT_PER_HOST_LIMIT = 5  # Default maximum concurrent connections per host
DEFAULT_RETRY_BACKOFF_BASE = 2  # Base for exponential backoff
MAX_RETRY_WAIT = 60  # Maximum wait time between retries (seconds)


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
    retry_attempts: int = 3,
    headers: Optional[Dict[str, str]] = None,
    backoff_base: float = DEFAULT_RETRY_BACKOFF_BASE
) -> Optional[str]:
    """
    Fetch URL content with retry logic and exponential backoff.
    
    Args:
        session: Aiohttp client session
        url: URL to fetch
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        headers: Optional HTTP headers for this request
        backoff_base: Base for exponential backoff calculation
        
    Returns:
        Response text or None if failed
    """
    last_error = None
    
    for attempt in range(retry_attempts):
        try:
            async with session.get(
                url, 
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:
                    # Rate limited - use longer backoff
                    wait_time = min(backoff_base ** (attempt + 2), MAX_RETRY_WAIT)
                    log_with_context(
                        logger, logging.WARNING,
                        f"Rate limited fetching {url}, waiting {wait_time}s",
                        context={'url': url, 'attempt': attempt + 1, 'status': 429}
                    )
                    await asyncio.sleep(wait_time)
                    continue
                elif response.status >= 500:
                    # Server error - retry with backoff
                    log_with_context(
                        logger, logging.WARNING,
                        f"Server error fetching {url}: HTTP {response.status}",
                        context={'url': url, 'attempt': attempt + 1, 'status': response.status}
                    )
                else:
                    # Client error - don't retry
                    log_with_context(
                        logger, logging.WARNING,
                        f"Failed to fetch {url}: HTTP {response.status}",
                        context={'url': url, 'status': response.status},
                        error_type='client_error'
                    )
                    return None
                    
        except asyncio.TimeoutError as e:
            last_error = e
            log_with_context(
                logger, logging.WARNING,
                f"Timeout fetching {url}",
                context={'url': url, 'attempt': attempt + 1, 'max_attempts': retry_attempts},
                error_type='timeout'
            )
        except aiohttp.ClientError as e:
            last_error = e
            log_with_context(
                logger, logging.WARNING,
                f"Client error fetching {url}: {e}",
                context={'url': url, 'attempt': attempt + 1},
                error_type='client_error'
            )
        except Exception as e:
            last_error = e
            log_with_context(
                logger, logging.ERROR,
                f"Unexpected error fetching {url}: {e}",
                context={'url': url},
                error_type='unexpected',
                exc_info=True
            )
            return None
        
        # Exponential backoff for retries
        if attempt < retry_attempts - 1:
            wait_time = min(backoff_base ** attempt, MAX_RETRY_WAIT)
            await asyncio.sleep(wait_time)
    
    # All retries failed
    if last_error:
        log_with_context(
            logger, logging.ERROR,
            f"Failed to fetch {url} after {retry_attempts} attempts",
            context={'url': url, 'last_error': str(last_error)},
            error_type='max_retries_exceeded'
        )
    
    return None


async def fetch_urls_batch(
    urls: List[str],
    max_concurrent: int = 10,
    timeout: int = 30,
    retry_attempts: int = 3,
    headers: Optional[Dict[str, str]] = None,
    session: Optional[aiohttp.ClientSession] = None
) -> Dict[str, Optional[str]]:
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
            content = await fetch_url(sess, url, timeout, retry_attempts, headers)
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
            per_host_limit=min(max_concurrent, DEFAULT_PER_HOST_LIMIT),
            timeout=timeout
        )
    
    session = await session_manager.get_session()
    
    try:
        # Pass headers to fetch_urls_batch which will use them per request
        results = await fetch_urls_batch(
            urls,
            max_concurrent,
            timeout,
            retry_attempts,
            headers=headers,
            session=session
        )
        return results
    finally:
        if should_close:
            await session_manager.close()
