"""Generate embeddings for content chunks."""
import asyncio
import numpy as np
from typing import List, Optional
from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Constants
EPSILON = 1e-10  # Small value to prevent division by zero in normalization
MAX_RETRY_WAIT = 60  # Maximum wait time between retries (seconds)
API_ERROR_WAIT = 30  # Wait time for API errors (seconds)


async def generate_embedding(
    text: str,
    api_key: str,
    model: str = "text-embedding-3-large",
    timeout: int = 30,
    max_retries: int = 3
) -> Optional[np.ndarray]:
    """
    Generate embedding for text with retry logic.
    
    Args:
        text: Input text
        api_key: OpenAI API key
        model: Embedding model name
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        Embedding vector as numpy array or None if failed
    """
    if not text or not text.strip():
        return None
    
    client = AsyncOpenAI(api_key=api_key, timeout=timeout)
    
    for attempt in range(max_retries):
        try:
            response = await client.embeddings.create(
                model=model,
                input=text
            )
            
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            
            # Normalize embedding
            embedding = embedding / (np.linalg.norm(embedding) + EPSILON)
            
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except RateLimitError as e:
            wait_time = min(2 ** attempt, MAX_RETRY_WAIT)  # Exponential backoff, capped
            logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to generate embedding after {max_retries} attempts: {e}")
                return None
                
        except (APIError, APIConnectionError) as e:
            wait_time = min(2 ** attempt, API_ERROR_WAIT)
            logger.warning(f"API error: {e}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to generate embedding after {max_retries} attempts: {e}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout generating embedding (attempt {attempt + 1}/{max_retries})")
            if attempt >= max_retries - 1:
                logger.error(f"Failed to generate embedding after {max_retries} timeout attempts")
                return None
                
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            return None
    
    return None


async def generate_embeddings_batch(
    texts: List[str],
    api_key: str,
    model: str = "text-embedding-3-large",
    batch_size: int = 100,
    timeout: int = 60,
    max_retries: int = 3,
    max_concurrent: int = 5
) -> List[Optional[np.ndarray]]:
    """
    Generate embeddings for multiple texts in batches with bounded parallelism.
    
    Args:
        texts: List of texts
        api_key: OpenAI API key
        model: Embedding model name
        batch_size: Number of texts per batch
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        max_concurrent: Maximum concurrent batch requests
        
    Returns:
        List of embedding vectors
    """
    embeddings = []
    client = AsyncOpenAI(api_key=api_key, timeout=timeout)
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(batch_start: int, batch_texts: List[str]) -> List[Optional[np.ndarray]]:
        """Process a single batch with semaphore control."""
        async with semaphore:
            # Filter out empty texts
            valid_batch = [(idx, text) for idx, text in enumerate(batch_texts) if text and text.strip()]
            
            if not valid_batch:
                return [None] * len(batch_texts)
            
            for attempt in range(max_retries):
                try:
                    indices, valid_texts = zip(*valid_batch)
                    
                    response = await client.embeddings.create(
                        model=model,
                        input=list(valid_texts)
                    )
                    
                    batch_embeddings = [None] * len(batch_texts)
                    for idx, embedding_data in zip(indices, response.data):
                        embedding = np.array(embedding_data.embedding, dtype=np.float32)
                        # Normalize embedding
                        embedding = embedding / (np.linalg.norm(embedding) + EPSILON)
                        batch_embeddings[idx] = embedding
                    
                    logger.info(f"Generated {len(valid_texts)} embeddings (batch starting at {batch_start})")
                    return batch_embeddings
                    
                except RateLimitError as e:
                    wait_time = min(2 ** attempt, MAX_RETRY_WAIT)
                    logger.warning(f"Rate limit hit for batch {batch_start}, waiting {wait_time}s")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Failed batch {batch_start} after {max_retries} attempts: {e}")
                        return [None] * len(batch_texts)
                        
                except (APIError, APIConnectionError) as e:
                    wait_time = min(2 ** attempt, API_ERROR_WAIT)
                    logger.warning(f"API error for batch {batch_start}: {e}, retrying in {wait_time}s")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Failed batch {batch_start} after {max_retries} attempts: {e}")
                        return [None] * len(batch_texts)
                        
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for batch {batch_start} (attempt {attempt + 1}/{max_retries})")
                    if attempt >= max_retries - 1:
                        logger.error(f"Failed batch {batch_start} after {max_retries} timeout attempts")
                        return [None] * len(batch_texts)
                        
                except Exception as e:
                    logger.error(f"Unexpected error for batch {batch_start}: {e}")
                    return [None] * len(batch_texts)
            
            return [None] * len(batch_texts)
    
    # Create tasks for all batches
    tasks = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        tasks.append(process_batch(i, batch))
    
    # Process batches with bounded parallelism
    batch_results = await asyncio.gather(*tasks)
    
    # Flatten results
    for batch_result in batch_results:
        embeddings.extend(batch_result)
    
    return embeddings
