"""Database utilities and schema management."""
import aiosqlite
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from pydantic import ValidationError
from enum import IntEnum

from app.utils.logger import get_logger
from app.utils.models import PageModel, GapModel

logger = get_logger(__name__)


class Priority(IntEnum):
    """Priority levels for gaps."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class DatabasePool:
    """Simple connection pool for aiosqlite."""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        """
        Initialize database pool.
        
        Args:
            db_path: Path to database
            max_connections: Maximum number of connections
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections: List[aiosqlite.Connection] = []
        self._available: List[aiosqlite.Connection] = []
        
    async def get_connection(self) -> aiosqlite.Connection:
        """Get a connection from the pool."""
        if self._available:
            return self._available.pop()
        
        if len(self._connections) < self.max_connections:
            conn = await aiosqlite.connect(self.db_path)
            self._connections.append(conn)
            return conn
        
        # Wait for an available connection
        import asyncio
        while not self._available:
            await asyncio.sleep(0.01)
        return self._available.pop()
    
    def release_connection(self, conn: aiosqlite.Connection):
        """Release a connection back to the pool."""
        if conn in self._connections:
            self._available.append(conn)
    
    async def close_all(self):
        """Close all connections."""
        for conn in self._connections:
            await conn.close()
        self._connections.clear()
        self._available.clear()


@asynccontextmanager
async def get_db_connection(db_path: str):
    """
    Context manager for database connections.
    
    Args:
        db_path: Path to database
        
    Yields:
        Database connection
    """
    conn = await aiosqlite.connect(db_path)
    try:
        yield conn
    finally:
        await conn.close()


async def init_database(db_path: str) -> None:
    """
    Initialize database schema.
    
    Args:
        db_path: Path to database file
    """
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(db_path) as db:
        # Pages table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                domain TEXT NOT NULL,
                is_primary BOOLEAN NOT NULL DEFAULT 0,
                title TEXT,
                description TEXT,
                h1 TEXT,
                content_text TEXT,
                word_count INTEGER,
                schema_data TEXT,
                last_crawled TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Content chunks table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER,
                FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
                UNIQUE(page_id, chunk_index)
            )
        """)
        
        # Embeddings table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                model TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
                UNIQUE(chunk_id)
            )
        """)
        
        # Gaps table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_url TEXT NOT NULL,
                gap_type TEXT NOT NULL,
                similarity_score REAL,
                closest_match_url TEXT,
                analysis TEXT,
                priority INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_pages_domain ON pages(domain)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_pages_is_primary ON pages(is_primary)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_page_id ON chunks(page_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_gaps_type ON gaps(gap_type)")
        
        await db.commit()
        logger.info(f"Database initialized at {db_path}")


async def store_page(
    db_path: str,
    url: str,
    domain: str,
    is_primary: bool,
    title: Optional[str] = None,
    description: Optional[str] = None,
    h1: Optional[str] = None,
    content_text: Optional[str] = None,
    word_count: Optional[int] = None,
    schema_data: Optional[str] = None
) -> int:
    """
    Store page data in database.
    
    Args:
        db_path: Path to database
        url: Page URL
        domain: Domain name
        is_primary: Whether this is primary site
        title: Page title
        description: Meta description
        h1: H1 heading
        content_text: Page content
        word_count: Word count
        schema_data: Schema JSON data
        
    Returns:
        Page ID
        
    Raises:
        ValidationError: If page data is invalid
    """
    # Validate page data before storing
    try:
        page_model = PageModel(
            url=url,
            domain=domain,
            is_primary=is_primary,
            title=title,
            description=description,
            h1=h1,
            content_text=content_text,
            word_count=word_count,
            schema_data=schema_data
        )
    except ValidationError as e:
        logger.error(f"Page validation failed for {url}: {e}")
        raise
    
    async with aiosqlite.connect(db_path) as db:
        # First, try to get existing page ID
        cursor = await db.execute("SELECT id FROM pages WHERE url = ?", (url,))
        row = await cursor.fetchone()
        
        if row:
            # Update existing page
            page_id = row[0]
            await db.execute("""
                UPDATE pages SET
                    title=?, description=?, h1=?, content_text=?,
                    word_count=?, schema_data=?, last_crawled=CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title, description, h1, content_text, word_count, schema_data, page_id))
        else:
            # Insert new page
            cursor = await db.execute("""
                INSERT INTO pages (url, domain, is_primary, title, description, h1, content_text, word_count, schema_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (url, domain, is_primary, title, description, h1, content_text, word_count, schema_data))
            page_id = cursor.lastrowid
        
        await db.commit()
        return page_id


async def get_page_id(db_path: str, url: str) -> Optional[int]:
    """
    Get page ID by URL.
    
    Args:
        db_path: Path to database
        url: Page URL
        
    Returns:
        Page ID or None
    """
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT id FROM pages WHERE url = ?", (url,))
        row = await cursor.fetchone()
        return row[0] if row else None


async def store_pages_batch(
    db_path: str,
    pages: List[Dict[str, Any]]
) -> List[int]:
    """
    Store multiple pages in a single transaction.
    
    Args:
        db_path: Path to database
        pages: List of page data dictionaries
        
    Returns:
        List of page IDs
        
    Raises:
        ValidationError: If any page data is invalid
    """
    # Validate all pages first
    validated_pages = []
    for page in pages:
        try:
            page_model = PageModel(**page)
            validated_pages.append(page)
        except ValidationError as e:
            logger.error(f"Page validation failed for {page.get('url')}: {e}")
            raise
    
    page_ids = []
    async with aiosqlite.connect(db_path) as db:
        for page in validated_pages:
            # Check if page exists
            cursor = await db.execute("SELECT id FROM pages WHERE url = ?", (page['url'],))
            row = await cursor.fetchone()
            
            if row:
                # Update existing page
                page_id = row[0]
                await db.execute("""
                    UPDATE pages SET
                        title=?, description=?, h1=?, content_text=?,
                        word_count=?, schema_data=?, last_crawled=CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    page.get('title'),
                    page.get('description'),
                    page.get('h1'),
                    page.get('content_text'),
                    page.get('word_count'),
                    page.get('schema_data'),
                    page_id
                ))
            else:
                # Insert new page
                cursor = await db.execute("""
                    INSERT INTO pages (url, domain, is_primary, title, description, h1, content_text, word_count, schema_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    page['url'],
                    page['domain'],
                    page['is_primary'],
                    page.get('title'),
                    page.get('description'),
                    page.get('h1'),
                    page.get('content_text'),
                    page.get('word_count'),
                    page.get('schema_data')
                ))
                page_id = cursor.lastrowid
            
            page_ids.append(page_id)
        
        await db.commit()
        logger.info(f"Stored {len(page_ids)} pages in batch")
    
    return page_ids


async def store_gaps_batch(
    db_path: str,
    gaps: List[Dict[str, Any]]
) -> None:
    """
    Store multiple gaps in a single transaction.
    
    Args:
        db_path: Path to database
        gaps: List of gap data dictionaries
        
    Raises:
        ValidationError: If any gap data is invalid
    """
    # Validate all gaps first
    for gap in gaps:
        try:
            GapModel(**gap)
        except ValidationError as e:
            logger.error(f"Gap validation failed: {e}")
            raise
    
    # Convert priority string to enum value
    def get_priority_value(priority_str: Optional[str]) -> int:
        """Convert priority string to database integer value."""
        priority_map = {
            'high': Priority.HIGH,
            'medium': Priority.MEDIUM,
            'low': Priority.LOW
        }
        return priority_map.get(priority_str, Priority.LOW)
    
    async with aiosqlite.connect(db_path) as db:
        await db.executemany("""
            INSERT INTO gaps (competitor_url, gap_type, similarity_score, closest_match_url, analysis, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (
                gap['competitor_url'],
                gap['gap_type'],
                gap.get('similarity_score'),
                gap.get('closest_match_url'),
                gap.get('analysis'),
                get_priority_value(gap.get('priority'))
            )
            for gap in gaps
        ])
        await db.commit()
        logger.info(f"Stored {len(gaps)} gaps in batch")
