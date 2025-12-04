"""Content summarization using LLM."""
from typing import Optional
from openai import AsyncOpenAI
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def summarize_content(
    text: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 500
) -> Optional[str]:
    """
    Generate summary of content using LLM.
    
    Args:
        text: Content to summarize
        api_key: OpenAI API key
        model: Model to use
        max_tokens: Maximum tokens in summary
        
    Returns:
        Summary text or None if failed
    """
    if not text or len(text) < 100:
        return None
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise summaries of web page content. Focus on the main topics and key points."
                },
                {
                    "role": "user",
                    "content": f"Summarize the following content in 2-3 sentences:\n\n{text[:4000]}"
                }
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        logger.debug(f"Generated summary: {summary[:100]}...")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        return None


async def extract_topics(
    text: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    max_topics: int = 5
) -> Optional[list[str]]:
    """
    Extract main topics from content using LLM.
    
    Args:
        text: Content to analyze
        api_key: OpenAI API key
        model: Model to use
        max_topics: Maximum number of topics
        
    Returns:
        List of topics or None if failed
    """
    if not text or len(text) < 100:
        return None
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful assistant that identifies main topics in web content. Return a comma-separated list of {max_topics} main topics."
                },
                {
                    "role": "user",
                    "content": f"What are the main topics in this content?\n\n{text[:4000]}"
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
        
    except Exception as e:
        logger.error(f"Failed to extract topics: {e}")
        return None
