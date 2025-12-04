"""Generate embeddings for content chunks."""
import numpy as np
from typing import List, Optional
from openai import AsyncOpenAI
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_embedding(
    text: str,
    api_key: str,
    model: str = "text-embedding-3-large"
) -> Optional[np.ndarray]:
    """
    Generate embedding for text.
    
    Args:
        text: Input text
        api_key: OpenAI API key
        model: Embedding model name
        
    Returns:
        Embedding vector as numpy array or None if failed
    """
    if not text or not text.strip():
        return None
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.embeddings.create(
            model=model,
            input=text
        )
        
        embedding = np.array(response.data[0].embedding, dtype=np.float32)
        logger.debug(f"Generated embedding of dimension {len(embedding)}")
        return embedding
        
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


async def generate_embeddings_batch(
    texts: List[str],
    api_key: str,
    model: str = "text-embedding-3-large",
    batch_size: int = 100
) -> List[Optional[np.ndarray]]:
    """
    Generate embeddings for multiple texts in batches.
    
    Args:
        texts: List of texts
        api_key: OpenAI API key
        model: Embedding model name
        batch_size: Number of texts per batch
        
    Returns:
        List of embedding vectors
    """
    embeddings = []
    client = AsyncOpenAI(api_key=api_key)
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Filter out empty texts
        valid_batch = [(idx, text) for idx, text in enumerate(batch) if text and text.strip()]
        
        if not valid_batch:
            embeddings.extend([None] * len(batch))
            continue
        
        try:
            indices, valid_texts = zip(*valid_batch)
            
            response = await client.embeddings.create(
                model=model,
                input=list(valid_texts)
            )
            
            batch_embeddings = [None] * len(batch)
            for idx, embedding_data in zip(indices, response.data):
                embedding = np.array(embedding_data.embedding, dtype=np.float32)
                batch_embeddings[idx] = embedding
            
            embeddings.extend(batch_embeddings)
            logger.info(f"Generated {len(valid_texts)} embeddings (batch {i//batch_size + 1})")
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for batch: {e}")
            embeddings.extend([None] * len(batch))
    
    return embeddings
