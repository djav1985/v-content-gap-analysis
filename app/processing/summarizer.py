"""Content summarization using LLM."""
import asyncio
from typing import List, Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
import tiktoken

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Constants
CHARS_PER_TOKEN_APPROX = 4  # Approximate character to token ratio for fallback


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Count tokens in text using tiktoken.
    
    Args:
        text: Input text
        model: Model name for tokenization
        
    Returns:
        Token count
    """
    try:
        # Use cl100k_base encoding for GPT-4 models
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback to simple approximation
        return len(text) // CHARS_PER_TOKEN_APPROX


async def summarize_content(
    text: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 500,
    timeout: int = 30,
    max_retries: int = 3
) -> Optional[str]:
    """
    Generate summary of content using LLM with retry logic.
    
    Args:
        text: Content to summarize
        api_key: OpenAI API key
        model: Model to use
        max_tokens: Maximum tokens in summary
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        Summary text or None if failed
    """
    if not text or len(text) < 100:
        return None
    
    # Limit input text based on token count
    text_tokens = count_tokens(text, model)
    if text_tokens > 3000:
        # Truncate to approximately 3000 tokens
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)[:3000]
        text = encoding.decode(tokens)
    
    client = AsyncOpenAI(api_key=api_key, timeout=timeout)
    
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates concise summaries of web page content. Focus on the main topics and key points."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize the following content in 2-3 sentences:\n\n{text}"
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            logger.debug(f"Generated summary: {summary[:100]}...")
            return summary
            
        except RateLimitError as e:
            wait_time = min(2 ** attempt, 60)
            logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to generate summary after {max_retries} attempts: {e}")
                return None
                
        except (APIError, APIConnectionError) as e:
            wait_time = min(2 ** attempt, 30)
            logger.warning(f"API error: {e}, retrying in {wait_time}s")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to generate summary after {max_retries} attempts: {e}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout generating summary (attempt {attempt + 1}/{max_retries})")
            if attempt >= max_retries - 1:
                logger.error(f"Failed to generate summary after {max_retries} timeout attempts")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None
    
    return None


async def extract_topics(
    text: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    max_topics: int = 5,
    timeout: int = 30,
    max_retries: int = 3
) -> Optional[List[str]]:
    """
    Extract main topics from content using LLM with retry logic.
    
    Args:
        text: Content to analyze
        api_key: OpenAI API key
        model: Model to use
        max_topics: Maximum number of topics
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        List of topics or None if failed
    """
    if not text or len(text) < 100:
        return None
    
    # Limit input text based on token count
    text_tokens = count_tokens(text, model)
    if text_tokens > 3000:
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)[:3000]
        text = encoding.decode(tokens)
    
    client = AsyncOpenAI(api_key=api_key, timeout=timeout)
    
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful assistant that identifies main topics in web content. Return a comma-separated list of {max_topics} main topics."
                    },
                    {
                        "role": "user",
                        "content": f"What are the main topics in this content?\n\n{text}"
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            topics_text = response.choices[0].message.content.strip()
            topics = [t.strip() for t in topics_text.split(',')]
            topics = topics[:max_topics]
            
            logger.debug(f"Extracted topics: {topics}")
            return topics
            
        except RateLimitError as e:
            wait_time = min(2 ** attempt, 60)
            logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to extract topics after {max_retries} attempts: {e}")
                return None
                
        except (APIError, APIConnectionError) as e:
            wait_time = min(2 ** attempt, 30)
            logger.warning(f"API error: {e}, retrying in {wait_time}s")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to extract topics after {max_retries} attempts: {e}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout extracting topics (attempt {attempt + 1}/{max_retries})")
            if attempt >= max_retries - 1:
                logger.error(f"Failed to extract topics after {max_retries} timeout attempts")
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract topics: {e}")
            return None
    
    return None
