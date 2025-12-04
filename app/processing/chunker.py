"""Content chunking functionality."""
from typing import List
import tiktoken
from app.utils.logger import get_logger

logger = get_logger(__name__)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text.
    
    Args:
        text: Input text
        model: Model name for tokenization
        
    Returns:
        Token count
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to simple approximation
        return len(text) // 4


def chunk_text(
    text: str,
    chunk_size: int = 1500,
    overlap: int = 200,
    model: str = "gpt-4"
) -> List[str]:
    """
    Split text into chunks based on token count.
    
    Args:
        text: Input text
        chunk_size: Target chunk size in tokens
        overlap: Overlap between chunks in tokens
        model: Model name for tokenization
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
    except Exception:
        # Fallback: split by characters
        words = text.split()
        chunk_word_size = chunk_size // 4
        overlap_word_size = overlap // 4
        
        chunks = []
        for i in range(0, len(words), chunk_word_size - overlap_word_size):
            chunk_words = words[i:i + chunk_word_size]
            chunks.append(' '.join(chunk_words))
        
        return chunks
    
    # Split tokens into chunks
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        
        try:
            chunk_text = encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
        except Exception as e:
            logger.warning(f"Failed to decode chunk: {e}")
        
        # Move start position with overlap
        start = end - overlap if end < len(tokens) else end
        
        if start >= len(tokens):
            break
    
    logger.debug(f"Created {len(chunks)} chunks from text of {len(tokens)} tokens")
    return chunks


def chunk_by_paragraphs(
    text: str,
    target_chunk_size: int = 1500,
    model: str = "gpt-4"
) -> List[str]:
    """
    Split text into chunks by paragraphs, respecting target size.
    
    Args:
        text: Input text
        target_chunk_size: Target chunk size in tokens
        model: Model name for tokenization
        
    Returns:
        List of text chunks
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_tokens = count_tokens(para, model)
        
        if current_size + para_tokens > target_chunk_size and current_chunk:
            # Save current chunk and start new one
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_tokens
        else:
            current_chunk.append(para)
            current_size += para_tokens
    
    # Add remaining chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    logger.debug(f"Created {len(chunks)} paragraph-based chunks")
    return chunks
