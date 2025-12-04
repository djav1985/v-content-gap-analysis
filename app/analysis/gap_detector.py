"""Gap detection and analysis."""
import aiosqlite
from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def detect_missing_pages(
    db_path: str,
    similarity_threshold: float = 0.45
) -> List[Dict[str, Any]]:
    """
    Detect competitor pages with no similar primary page.
    
    Args:
        db_path: Path to database
        similarity_threshold: Threshold for considering pages similar
        
    Returns:
        List of missing page gaps
    """
    gaps = []
    
    async with aiosqlite.connect(db_path) as db:
        # Get all gaps below threshold
        cursor = await db.execute("""
            SELECT competitor_url, closest_match_url, similarity_score
            FROM gaps
            WHERE gap_type = 'missing_content'
            AND similarity_score < ?
            ORDER BY similarity_score ASC
        """, (similarity_threshold,))
        
        rows = await cursor.fetchall()
        
        for row in rows:
            gaps.append({
                'type': 'missing_page',
                'competitor_url': row[0],
                'closest_match_url': row[1],
                'similarity_score': row[2],
                'priority': 'high' if row[2] < 0.3 else 'medium'
            })
    
    logger.info(f"Detected {len(gaps)} missing pages")
    return gaps


async def detect_thin_content(
    db_path: str,
    ratio_threshold: float = 3.0
) -> List[Dict[str, Any]]:
    """
    Detect primary pages with thin content compared to competitors.
    
    Args:
        db_path: Path to database
        ratio_threshold: Word count ratio threshold
        
    Returns:
        List of thin content gaps
    """
    gaps = []
    
    async with aiosqlite.connect(db_path) as db:
        # Compare word counts
        cursor = await db.execute("""
            SELECT 
                p1.url as primary_url,
                p1.word_count as primary_words,
                p2.url as competitor_url,
                p2.word_count as competitor_words,
                CAST(p2.word_count AS FLOAT) / CAST(p1.word_count AS FLOAT) as ratio
            FROM pages p1
            JOIN pages p2 ON p1.title = p2.title OR p1.h1 = p2.h1
            WHERE p1.is_primary = 1
            AND p2.is_primary = 0
            AND p1.word_count > 0
            AND CAST(p2.word_count AS FLOAT) / CAST(p1.word_count AS FLOAT) > ?
        """, (ratio_threshold,))
        
        rows = await cursor.fetchall()
        
        for row in rows:
            gaps.append({
                'type': 'thin_content',
                'primary_url': row[0],
                'primary_word_count': row[1],
                'competitor_url': row[2],
                'competitor_word_count': row[3],
                'ratio': row[4],
                'priority': 'high' if row[4] > 5.0 else 'medium'
            })
    
    logger.info(f"Detected {len(gaps)} thin content pages")
    return gaps


async def detect_metadata_gaps(db_path: str) -> List[Dict[str, Any]]:
    """
    Detect pages with missing or poor metadata.
    
    Args:
        db_path: Path to database
        
    Returns:
        List of metadata gaps
    """
    gaps = []
    
    async with aiosqlite.connect(db_path) as db:
        # Find pages with missing metadata
        cursor = await db.execute("""
            SELECT url, title, description, h1
            FROM pages
            WHERE is_primary = 1
            AND (title IS NULL OR description IS NULL OR h1 IS NULL)
        """)
        
        rows = await cursor.fetchall()
        
        for row in rows:
            missing = []
            if not row[1]:
                missing.append('title')
            if not row[2]:
                missing.append('description')
            if not row[3]:
                missing.append('h1')
            
            gaps.append({
                'type': 'metadata_gap',
                'url': row[0],
                'missing_elements': missing,
                'priority': 'high' if 'title' in missing else 'medium'
            })
    
    logger.info(f"Detected {len(gaps)} metadata gaps")
    return gaps


async def detect_schema_gaps(db_path: str) -> List[Dict[str, Any]]:
    """
    Detect pages missing schema markup.
    
    Args:
        db_path: Path to database
        
    Returns:
        List of schema gaps
    """
    gaps = []
    
    async with aiosqlite.connect(db_path) as db:
        # Find primary pages without schema
        cursor = await db.execute("""
            SELECT p1.url
            FROM pages p1
            WHERE p1.is_primary = 1
            AND (p1.schema_data IS NULL OR p1.schema_data = '')
            AND EXISTS (
                SELECT 1 FROM pages p2
                WHERE p2.is_primary = 0
                AND p2.schema_data IS NOT NULL
                AND p2.schema_data != ''
            )
        """)
        
        rows = await cursor.fetchall()
        
        for row in rows:
            gaps.append({
                'type': 'schema_gap',
                'url': row[0],
                'priority': 'medium'
            })
    
    logger.info(f"Detected {len(gaps)} schema gaps")
    return gaps


async def get_all_gaps(db_path: str, config: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all types of gaps.
    
    Args:
        db_path: Path to database
        config: Configuration dictionary
        
    Returns:
        Dictionary with all gap types
    """
    missing_pages = await detect_missing_pages(
        db_path,
        config.get('similarity_threshold', 0.45)
    )
    
    thin_content = await detect_thin_content(
        db_path,
        config.get('thin_content_ratio', 3.0)
    )
    
    metadata_gaps = await detect_metadata_gaps(db_path)
    schema_gaps = await detect_schema_gaps(db_path)
    
    return {
        'missing_pages': missing_pages,
        'thin_content': thin_content,
        'metadata_gaps': metadata_gaps,
        'schema_gaps': schema_gaps
    }
