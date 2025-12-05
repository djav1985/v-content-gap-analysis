"""LLM-based content comparison."""
import asyncio
from typing import Dict, Any, Optional
from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def compare_pages(
    primary_content: str,
    competitor_content: str,
    primary_url: str,
    competitor_url: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    timeout: int = 60,
    max_retries: int = 3
) -> Optional[Dict[str, Any]]:
    """
    Compare two pages using LLM with retry logic.
    
    Args:
        primary_content: Primary page content
        competitor_content: Competitor page content
        primary_url: Primary page URL
        competitor_url: Competitor page URL
        api_key: OpenAI API key
        model: Model to use
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        Comparison results dictionary
    """
    client = AsyncOpenAI(api_key=api_key, timeout=timeout)
    
    prompt = f"""Compare these two web pages and identify:

1. Missing sections in the primary page
2. Missing key arguments or points
3. Competitive advantages in the competitor's content
4. Recommended improvements

Primary Page ({primary_url}):
{primary_content[:3000]}

Competitor Page ({competitor_url}):
{competitor_content[:3000]}

Provide a structured analysis in JSON format with keys:
- missing_sections: list of section topics missing
- missing_arguments: list of key points not covered
- competitive_advantages: what makes competitor content stronger
- recommendations: specific improvements to make
"""
    
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an SEO content analyst. Provide detailed, actionable insights in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            
            logger.info(f"Completed LLM comparison for {primary_url} vs {competitor_url}")
            return analysis
            
        except RateLimitError as e:
            wait_time = min(2 ** attempt, 60)
            logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to compare pages after {max_retries} attempts: {e}")
                return None
                
        except (APIError, APIConnectionError) as e:
            wait_time = min(2 ** attempt, 30)
            logger.warning(f"API error: {e}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to compare pages after {max_retries} attempts: {e}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout comparing pages (attempt {attempt + 1}/{max_retries})")
            if attempt >= max_retries - 1:
                logger.error(f"Failed to compare pages after {max_retries} timeout attempts")
                return None
                
        except Exception as e:
            logger.error(f"Failed to compare pages with LLM: {e}")
            return None
    
    return None


async def generate_page_outline(
    competitor_content: str,
    competitor_url: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    timeout: int = 60,
    max_retries: int = 3
) -> Optional[str]:
    """
    Generate outline for a new page based on competitor content with retry logic.
    
    Args:
        competitor_content: Competitor page content
        competitor_url: Competitor page URL
        api_key: OpenAI API key
        model: Model to use
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        Page outline as string
    """
    client = AsyncOpenAI(api_key=api_key, timeout=timeout)
    
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content strategist. Create detailed page outlines for SEO content."
                    },
                    {
                        "role": "user",
                        "content": f"""Based on this competitor page, create a comprehensive outline for a new page that would compete effectively:

Competitor Content ({competitor_url}):
{competitor_content[:3000]}

Include:
1. Suggested title and meta description
2. H1 and main H2 sections
3. Key topics to cover
4. Content angles to emphasize
5. Recommended word count range
"""
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            outline = response.choices[0].message.content.strip()
            logger.info(f"Generated outline based on {competitor_url}")
            return outline
            
        except RateLimitError as e:
            wait_time = min(2 ** attempt, 60)
            logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to generate outline after {max_retries} attempts: {e}")
                return None
                
        except (APIError, APIConnectionError) as e:
            wait_time = min(2 ** attempt, 30)
            logger.warning(f"API error: {e}, retrying in {wait_time}s")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to generate outline after {max_retries} attempts: {e}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout generating outline (attempt {attempt + 1}/{max_retries})")
            if attempt >= max_retries - 1:
                logger.error(f"Failed to generate outline after {max_retries} timeout attempts")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate outline: {e}")
            return None
    
    return None


async def suggest_rewrites(
    content: str,
    url: str,
    issues: list[str],
    api_key: str,
    model: str = "gpt-4o-mini",
    timeout: int = 60,
    max_retries: int = 3
) -> Optional[str]:
    """
    Suggest content improvements and rewrites with retry logic.
    
    Args:
        content: Page content
        url: Page URL
        issues: List of identified issues
        api_key: OpenAI API key
        model: Model to use
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        Rewrite suggestions
    """
    client = AsyncOpenAI(api_key=api_key, timeout=timeout)
    
    issues_text = "\n".join(f"- {issue}" for issue in issues)
    
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content improvement specialist. Provide specific, actionable rewrite suggestions."
                    },
                    {
                        "role": "user",
                        "content": f"""For this page with the following issues:

{issues_text}

Current Content ({url}):
{content[:2000]}

Provide specific suggestions to:
1. Improve thin content
2. Add missing sections
3. Strengthen arguments
4. Enhance SEO value
"""
                    }
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            suggestions = response.choices[0].message.content.strip()
            logger.info(f"Generated rewrite suggestions for {url}")
            return suggestions
            
        except RateLimitError as e:
            wait_time = min(2 ** attempt, 60)
            logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to generate suggestions after {max_retries} attempts: {e}")
                return None
                
        except (APIError, APIConnectionError) as e:
            wait_time = min(2 ** attempt, 30)
            logger.warning(f"API error: {e}, retrying in {wait_time}s")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to generate suggestions after {max_retries} attempts: {e}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout generating suggestions (attempt {attempt + 1}/{max_retries})")
            if attempt >= max_retries - 1:
                logger.error(f"Failed to generate suggestions after {max_retries} timeout attempts")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate rewrite suggestions: {e}")
            return None
    
    return None
