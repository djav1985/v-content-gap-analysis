"""Vector storage and retrieval using SQLite."""
import numpy as np
import aiosqlite
from typing import List, Optional, Tuple, Dict, Any
from pydantic import ValidationError

from app.utils.logger import get_logger
from app.utils.models import ChunkModel, EmbeddingModel

logger = get_logger(__name__)


async def store_embedding(
    db_path: str,
    chunk_id: int,
    embedding: np.ndarray,
    model: str
) -> None:
    """
    Store embedding in database.
    
    Args:
        db_path: Path to database
        chunk_id: Chunk ID
        embedding: Embedding vector
        model: Model name
    """
    async with aiosqlite.connect(db_path) as db:
        embedding_blob = embedding.tobytes()
        
        await db.execute("""
            INSERT INTO embeddings (chunk_id, embedding, model)
            VALUES (?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                embedding=excluded.embedding,
                model=excluded.model,
                created_at=CURRENT_TIMESTAMP
        """, (chunk_id, embedding_blob, model))
        
        await db.commit()


async def store_embeddings_batch(
    db_path: str,
    chunk_ids: List[int],
    embeddings: List[np.ndarray],
    model: str
) -> None:
    """
    Store multiple embeddings in database with optimized batch insert.
    
    Args:
        db_path: Path to database
        chunk_ids: List of chunk IDs
        embeddings: List of embedding vectors
        model: Model name
    """
    # Validate embeddings
    for chunk_id, embedding in zip(chunk_ids, embeddings):
        if embedding is not None:
            try:
                EmbeddingModel(
                    chunk_id=chunk_id,
                    embedding=embedding.tolist(),
                    model=model
                )
            except ValidationError as e:
                logger.error(f"Embedding validation failed for chunk {chunk_id}: {e}")
                raise
    
    async with aiosqlite.connect(db_path) as db:
        # Prepare batch data
        data = [
            (chunk_id, embedding.tobytes(), model)
            for chunk_id, embedding in zip(chunk_ids, embeddings)
            if embedding is not None
        ]
        
        if not data:
            logger.warning("No valid embeddings to store")
            return
        
        # Use executemany for batch insert
        await db.executemany("""
            INSERT INTO embeddings (chunk_id, embedding, model)
            VALUES (?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                embedding=excluded.embedding,
                model=excluded.model,
                created_at=CURRENT_TIMESTAMP
        """, data)
        
        await db.commit()
        logger.info(f"Stored {len(data)} embeddings in batch")


async def get_embedding(db_path: str, chunk_id: int) -> Optional[np.ndarray]:
    """
    Retrieve embedding from database.
    
    Args:
        db_path: Path to database
        chunk_id: Chunk ID
        
    Returns:
        Embedding vector or None
    """
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT embedding FROM embeddings WHERE chunk_id = ?",
            (chunk_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return np.frombuffer(row[0], dtype=np.float32)
        return None


async def get_all_embeddings(
    db_path: str,
    is_primary: Optional[bool] = None
) -> List[Tuple[int, int, np.ndarray, str]]:
    """
    Retrieve all embeddings with metadata.
    
    Args:
        db_path: Path to database
        is_primary: Filter by primary site if specified
        
    Returns:
        List of tuples: (chunk_id, page_id, embedding, url)
    """
    async with aiosqlite.connect(db_path) as db:
        if is_primary is not None:
            query = """
                SELECT e.chunk_id, c.page_id, e.embedding, p.url
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.id
                JOIN pages p ON c.page_id = p.id
                WHERE p.is_primary = ?
            """
            cursor = await db.execute(query, (is_primary,))
        else:
            query = """
                SELECT e.chunk_id, c.page_id, e.embedding, p.url
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.id
                JOIN pages p ON c.page_id = p.id
            """
            cursor = await db.execute(query)
        
        rows = await cursor.fetchall()
        
        results = [
            (row[0], row[1], np.frombuffer(row[2], dtype=np.float32), row[3])
            for row in rows
        ]
        
        logger.info(f"Retrieved {len(results)} embeddings")
        return results


async def store_chunks_batch(
    db_path: str,
    chunks_data: List[Dict[str, Any]]
) -> List[int]:
    """
    Store multiple chunks in a single transaction.
    
    Args:
        db_path: Path to database
        chunks_data: List of chunk data dictionaries with keys:
                    page_id, chunk_index, content, token_count
        
    Returns:
        List of chunk IDs
        
    Raises:
        ValidationError: If any chunk data is invalid
    """
    # Validate all chunks first
    for chunk in chunks_data:
        try:
            ChunkModel(**chunk)
        except ValidationError as e:
            logger.error(f"Chunk validation failed: {e}")
            raise
    
    chunk_ids = []
    async with aiosqlite.connect(db_path) as db:
        for chunk in chunks_data:
            cursor = await db.execute("""
                INSERT INTO chunks (page_id, chunk_index, content, token_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(page_id, chunk_index) DO UPDATE SET
                    content=excluded.content,
                    token_count=excluded.token_count
            """, (
                chunk['page_id'],
                chunk['chunk_index'],
                chunk['content'],
                chunk['token_count']
            ))
            chunk_ids.append(cursor.lastrowid)
        
        await db.commit()
        logger.info(f"Stored {len(chunk_ids)} chunks in batch")
    
    return chunk_ids


async def store_chunk(
    db_path: str,
    page_id: int,
    chunk_index: int,
    content: str,
    token_count: int
) -> int:
    """
    Store content chunk in database.
    
    Args:
        db_path: Path to database
        page_id: Page ID
        chunk_index: Chunk index
        content: Chunk content
        token_count: Token count
        
    Returns:
        Chunk ID
        
    Raises:
        ValidationError: If chunk data is invalid
    """
    # Validate chunk data before storing
    try:
        chunk_model = ChunkModel(
            page_id=page_id,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count
        )
    except ValidationError as e:
        logger.error(f"Chunk validation failed: {e}")
        raise
    
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("""
            INSERT INTO chunks (page_id, chunk_index, content, token_count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(page_id, chunk_index) DO UPDATE SET
                content=excluded.content,
                token_count=excluded.token_count
        """, (page_id, chunk_index, content, token_count))
        
        chunk_id = cursor.lastrowid
        await db.commit()
        
        return chunk_id
