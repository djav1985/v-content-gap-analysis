"""HTML page fetching functionality."""
from typing import Optional

from app.utils.aio import fetch_urls_batch, SessionManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def fetch_pages(
    urls: list[str],
    max_concurrent: int = 10,
    timeout: int = 30,
    retry_attempts: int = 3,
    user_agent: str = "SEO-Gap-Analysis-Agent/1.0",
    session_manager: Optional[SessionManager] = None
) -> dict[str, Optional[str]]:
    """
    Fetch HTML content for multiple pages using shared session.
    
    Args:
        urls: List of page URLs
        max_concurrent: Maximum concurrent requests
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        user_agent: User agent string
        session_manager: Optional session manager to reuse
        
    Returns:
        Dictionary mapping URLs to their HTML content
    """
    headers = {"User-Agent": user_agent}
    
    logger.info(f"Fetching {len(urls)} pages with {max_concurrent} concurrent requests")
    
    should_close = session_manager is None
    if session_manager is None:
        session_manager = SessionManager(
            max_connections=max_concurrent * 2,
            per_host_limit=min(max_concurrent, 5),
            timeout=timeout
        )
    
    session = await session_manager.get_session()
    
    # Update session headers
    session._default_headers.update(headers)
    
    try:
        results = await fetch_urls_batch(
            urls=urls,
            max_concurrent=max_concurrent,
            timeout=timeout,
            retry_attempts=retry_attempts,
            headers=None,  # Already set on session
            session=session
        )
        
        successful = sum(1 for content in results.values() if content is not None)
        logger.info(f"Successfully fetched {successful}/{len(urls)} pages")
        
        return results
    finally:
        if should_close:
            await session_manager.close()
