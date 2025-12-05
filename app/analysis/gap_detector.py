"""Gap detection and analysis."""
import aiosqlite
from typing import Any, Dict, List, Set

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
        List of missing page gaps (deduplicated)
    """
    gaps = []
    processed_urls: Set[str] = set()  # Track URLs to avoid duplicates
    
    async with aiosqlite.connect(db_path) as db:
        # Get all gaps below threshold
        cursor = await db.execute("""
            SELECT DISTINCT competitor_url, closest_match_url, similarity_score
            FROM gaps
            WHERE gap_type = 'missing_content'
            AND similarity_score < ?
            ORDER BY similarity_score ASC
        """, (similarity_threshold,))
        
        rows = await cursor.fetchall()
        
        for row in rows:
            competitor_url = row[0]
            
            # Skip if we've already processed this URL
            if competitor_url in processed_urls:
                continue
            
            processed_urls.add(competitor_url)
            
            # Calculate priority based on similarity score
            similarity_score = row[2]
            if similarity_score < 0.2:
                priority = 'high'
            elif similarity_score < 0.35:
                priority = 'medium'
            else:
                priority = 'low'
            
            gaps.append({
                'type': 'missing_page',
                'competitor_url': competitor_url,
                'closest_match_url': row[1],
                'similarity_score': similarity_score,
                'similarity_percentage': f"{similarity_score * 100:.1f}%",
                'priority': priority
            })
    
    logger.info(f"Detected {len(gaps)} unique missing pages (deduplicated from {len(rows)} raw gaps)")
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
        List of thin content gaps (deduplicated by primary URL)
    """
    gaps = []
    processed_urls: Set[str] = set()
    
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
            ORDER BY ratio DESC
        """, (ratio_threshold,))
        
        rows = await cursor.fetchall()
        
        for row in rows:
            primary_url = row[0]
            
            # Only keep the worst case for each primary URL
            if primary_url in processed_urls:
                continue
            
            processed_urls.add(primary_url)
            
            ratio = row[4]
            
            # Calculate priority based on ratio
            if ratio > 5.0:
                priority = 'high'
            elif ratio > 4.0:
                priority = 'medium'
            else:
                priority = 'low'
            
            # Calculate percentage difference
            word_diff_percentage = ((row[3] - row[1]) / row[1]) * 100
            
            gaps.append({
                'type': 'thin_content',
                'primary_url': primary_url,
                'primary_word_count': row[1],
                'competitor_url': row[2],
                'competitor_word_count': row[3],
                'ratio': ratio,
                'word_difference': row[3] - row[1],
                'word_diff_percentage': f"{word_diff_percentage:.1f}%",
                'priority': priority
            })
    
    logger.info(f"Detected {len(gaps)} unique thin content pages (deduplicated from {len(rows)} comparisons)")
    return gaps


async def detect_metadata_gaps(db_path: str) -> List[Dict[str, Any]]:
    """
    Detect pages with missing or poor metadata.
    
    Args:
        db_path: Path to database
        
    Returns:
        List of metadata gaps (deduplicated by URL)
    """
    gaps = []
    processed_urls: Set[str] = set()
    
    async with aiosqlite.connect(db_path) as db:
        # Find pages with missing metadata
        cursor = await db.execute("""
            SELECT DISTINCT url, title, description, h1
            FROM pages
            WHERE is_primary = 1
            AND (title IS NULL OR description IS NULL OR h1 IS NULL)
            ORDER BY url
        """)
        
        rows = await cursor.fetchall()
        
        for row in rows:
            url = row[0]
            
            if url in seen_urls:
                continue
            
            seen_urls.add(url)
            
            missing = []
            if not row[1]:
                missing.append('title')
            if not row[2]:
                missing.append('description')
            if not row[3]:
                missing.append('h1')
            
            # Calculate severity
            missing_count = len(missing)
            if 'title' in missing or missing_count >= 2:
                priority = 'high'
            elif missing_count >= 1:
                priority = 'medium'
            else:
                priority = 'low'
            
            gaps.append({
                'type': 'metadata_gap',
                'url': url,
                'missing_elements': missing,
                'missing_count': missing_count,
                'priority': priority
            })
    
    logger.info(f"Detected {len(gaps)} unique metadata gaps")
    return gaps


async def detect_schema_gaps(db_path: str) -> List[Dict[str, Any]]:
    """
    Detect pages missing schema markup.
    
    Args:
        db_path: Path to database
        
    Returns:
        List of schema gaps (deduplicated by URL)
    """
    gaps = []
    processed_urls: Set[str] = set()
    
    async with aiosqlite.connect(db_path) as db:
        # Find primary pages without schema
        cursor = await db.execute("""
            SELECT DISTINCT p1.url
            FROM pages p1
            WHERE p1.is_primary = 1
            AND (p1.schema_data IS NULL OR p1.schema_data = '')
            AND EXISTS (
                SELECT 1 FROM pages p2
                WHERE p2.is_primary = 0
                AND p2.schema_data IS NOT NULL
                AND p2.schema_data != ''
            )
            ORDER BY p1.url
        """)
        
        rows = await cursor.fetchall()
        
        for row in rows:
            url = row[0]
            
            if url in processed_urls:
                continue
            
            processed_urls.add(url)
            
            gaps.append({
                'type': 'schema_gap',
                'url': url,
                'priority': 'medium'
            })
    
    logger.info(f"Detected {len(gaps)} unique schema gaps")
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
