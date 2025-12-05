"""Database utilities and schema management."""
import aiosqlite
from pathlib import Path
from typing import Optional
from pydantic import ValidationError

from app.utils.logger import get_logger
from app.utils.models import PageModel, GapModel

logger = get_logger(__name__)


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
        cursor = await db.execute("""
            INSERT INTO pages (url, domain, is_primary, title, description, h1, content_text, word_count, schema_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                h1=excluded.h1,
                content_text=excluded.content_text,
                word_count=excluded.word_count,
                schema_data=excluded.schema_data,
                last_crawled=CURRENT_TIMESTAMP
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
