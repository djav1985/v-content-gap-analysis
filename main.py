"""Main orchestrator for SEO Gap Analysis Agent."""
import asyncio
import sys
from pathlib import Path
from typing import Optional

from app.utils.config import load_config, load_competitors
from app.utils.logger import setup_logger
from app.utils.database import init_database, store_page, get_page_id, store_gaps_batch
from app.utils.text import extract_domain, count_tokens

from app.sitemap.fetcher import fetch_sitemaps
from app.sitemap.parser import parse_sitemap

from app.crawler.fetcher import fetch_pages
from app.crawler.extractor import extract_page_data

from app.processing.cleaner import clean_text, validate_content
from app.processing.chunker import chunk_text
from app.processing.metadata import extract_metadata_signals

from app.embeddings.generator import generate_embeddings_batch
from app.embeddings.vectorstore import store_embeddings_batch, get_all_embeddings, store_chunk
from app.embeddings.comparer import find_content_gaps

from app.analysis.gap_detector import get_all_gaps
from app.analysis.llm_compare import compare_pages
from app.analysis.recommender import (
    prioritize_gaps,
    generate_action_plan,
    generate_summary,
    generate_quick_wins
)

from app.reporting.json_report import generate_json_report
from app.reporting.markdown_report import generate_markdown_report


logger = None


async def process_sitemap(sitemap_url: str, user_agent: str) -> list[str]:
    """Fetch and parse a sitemap."""
    logger.info(f"Processing sitemap: {sitemap_url}")
    
    sitemaps = await fetch_sitemaps([sitemap_url], user_agent=user_agent)
    xml_content = sitemaps.get(sitemap_url)
    
    if not xml_content:
        logger.error(f"Failed to fetch sitemap: {sitemap_url}")
        return []
    
    urls = parse_sitemap(xml_content, sitemap_url)
    logger.info(f"Found {len(urls)} URLs in sitemap")
    
    return urls


async def crawl_and_extract(
    urls: list[str],
    is_primary: bool,
    db_path: str,
    config: dict
) -> list[int]:
    """Crawl pages and extract content."""
    logger.info(f"Crawling {len(urls)} pages...")
    
    # Fetch HTML
    pages_html = await fetch_pages(
        urls,
        max_concurrent=config.max_concurrent_requests,
        timeout=config.request_timeout,
        retry_attempts=config.retry_attempts,
        user_agent=config.user_agent
    )
    
    page_ids = []
    
    for url, html in pages_html.items():
        if not html:
            continue
        
        try:
            # Extract content
            page_data = extract_page_data(html)
            metadata = page_data['metadata']
            content = page_data['content']
            
            # Clean content
            cleaned_content = clean_text(content)
            
            # Validate
            if not validate_content(cleaned_content):
                logger.warning(f"Skipping {url}: content too short")
                continue
            
            # Store page
            domain = extract_domain(url)
            page_id = await store_page(
                db_path,
                url=url,
                domain=domain,
                is_primary=is_primary,
                title=metadata.get('title'),
                description=metadata.get('description'),
                h1=metadata.get('h1'),
                content_text=cleaned_content,
                word_count=page_data['word_count'],
                schema_data=page_data.get('schema')
            )
            
            page_ids.append(page_id)
            logger.info(f"Stored page: {url}")
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            continue
    
    logger.info(f"Successfully crawled and stored {len(page_ids)} pages")
    return page_ids


async def process_and_embed(
    page_ids: list[int],
    db_path: str,
    config: dict
) -> None:
    """Process content into chunks and generate embeddings."""
    logger.info(f"Processing {len(page_ids)} pages into chunks...")
    
    import aiosqlite
    
    all_chunk_ids = []
    all_chunks_text = []
    
    async with aiosqlite.connect(db_path) as db:
        for page_id in page_ids:
            # Get page content
            cursor = await db.execute(
                "SELECT content_text FROM pages WHERE id = ?",
                (page_id,)
            )
            row = await cursor.fetchone()
            
            if not row or not row[0]:
                continue
            
            content = row[0]
            
            # Create chunks
            chunks = chunk_text(
                content,
                chunk_size=config.chunk_size,
                overlap=200
            )
            
            # Store chunks
            for i, chunk in enumerate(chunks[:config.max_chunks_per_page]):
                token_count = count_tokens(chunk)
                chunk_id = await store_chunk(
                    db_path,
                    page_id=page_id,
                    chunk_index=i,
                    content=chunk,
                    token_count=token_count
                )
                all_chunk_ids.append(chunk_id)
                all_chunks_text.append(chunk)
    
    logger.info(f"Created {len(all_chunk_ids)} chunks")
    
    if not all_chunks_text:
        logger.warning("No chunks to embed")
        return
    
    # Generate embeddings
    logger.info("Generating embeddings...")
    embeddings = await generate_embeddings_batch(
        all_chunks_text,
        api_key=config.openai_api_key,
        model=config.models.embeddings,
        batch_size=100
    )
    
    # Store embeddings
    valid_embeddings = [
        (chunk_id, emb)
        for chunk_id, emb in zip(all_chunk_ids, embeddings)
        if emb is not None
    ]
    
    if valid_embeddings:
        chunk_ids, emb_arrays = zip(*valid_embeddings)
        await store_embeddings_batch(
            db_path,
            list(chunk_ids),
            list(emb_arrays),
            config.models.embeddings
        )
        logger.info(f"Stored {len(valid_embeddings)} embeddings")


async def analyze_gaps(db_path: str, config: dict) -> dict:
    """Perform gap analysis."""
    logger.info("Analyzing content gaps...")
    
    # Get all embeddings
    primary_embeddings = await get_all_embeddings(db_path, is_primary=True)
    competitor_embeddings = await get_all_embeddings(db_path, is_primary=False)
    
    logger.info(f"Primary embeddings: {len(primary_embeddings)}")
    logger.info(f"Competitor embeddings: {len(competitor_embeddings)}")
    
    # Find content gaps using embeddings
    primary_data = [(cid, emb, url) for cid, pid, emb, url in primary_embeddings]
    competitor_data = [(cid, emb, url) for cid, pid, emb, url in competitor_embeddings]
    
    content_gaps = find_content_gaps(
        primary_data,
        competitor_data,
        threshold=config.similarity_threshold
    )
    
    # Store gaps in database using batch operation
    if content_gaps:
        await store_gaps_batch(db_path, content_gaps)
    
    # Get all gaps
    gaps = await get_all_gaps(
        db_path,
        {
            'similarity_threshold': config.similarity_threshold,
            'thin_content_ratio': config.thresholds.thin_content_ratio
        }
    )
    
    return gaps


async def generate_reports(gaps: dict, config: dict) -> None:
    """Generate analysis reports."""
    logger.info("Generating reports...")
    
    # Prioritize and create recommendations
    prioritized = prioritize_gaps(gaps)
    action_plan = generate_action_plan(prioritized)
    quick_wins = generate_quick_wins(prioritized)
    summary = generate_summary(gaps)
    
    # Generate JSON report
    generate_json_report(
        gaps=gaps,
        summary=summary,
        action_plan=action_plan,
        quick_wins=quick_wins,
        config={
            'site': config.site,
            'competitors': getattr(config, 'competitors', []),
            'similarity_threshold': config.similarity_threshold,
            'chunk_size': config.chunk_size,
            'thin_content_ratio': config.thresholds.thin_content_ratio
        },
        output_path=config.output.json_report
    )
    
    # Generate Markdown report
    generate_markdown_report(
        gaps=gaps,
        summary=summary,
        action_plan=action_plan,
        quick_wins=quick_wins,
        config={
            'site': config.site,
            'competitors': getattr(config, 'competitors', []),
            'similarity_threshold': config.similarity_threshold,
            'chunk_size': config.chunk_size,
            'thin_content_ratio': config.thresholds.thin_content_ratio
        },
        output_path=config.output.markdown_report
    )
    
    logger.info("Reports generated successfully")


async def main():
    """Main execution flow."""
    global logger
    
    # Setup logging
    logger = setup_logger(
        name="seo_gap_agent",
        log_file="data/logs/seo_gap_agent.log"
    )
    
    logger.info("=" * 60)
    logger.info("SEO Gap Analysis Agent Started")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        competitors = load_competitors()
        
        # Add competitors to config for reporting
        config.competitors = competitors
        
        # Validate OpenAI API key
        if not config.openai_api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            logger.error("Please set it in .env file or environment")
            return
        
        # Initialize database
        logger.info("Initializing database...")
        await init_database(config.database.path)
        
        # Process primary sitemap
        logger.info("Processing primary sitemap...")
        primary_urls = await process_sitemap(config.site, config.user_agent)
        
        if not primary_urls:
            logger.error("No URLs found in primary sitemap")
            return
        
        # Crawl primary site
        logger.info("Crawling primary site...")
        primary_page_ids = await crawl_and_extract(
            primary_urls[:config.max_pages_per_site],
            is_primary=True,
            db_path=config.database.path,
            config=config
        )
        
        # Process primary content
        if primary_page_ids:
            await process_and_embed(primary_page_ids, config.database.path, config)
        
        # Process competitor sitemaps
        for competitor_url in competitors:
            logger.info(f"Processing competitor: {competitor_url}")
            competitor_urls = await process_sitemap(competitor_url, config.user_agent)
            
            if not competitor_urls:
                continue
            
            # Crawl competitor
            competitor_page_ids = await crawl_and_extract(
                competitor_urls[:config.max_pages_per_site],
                is_primary=False,
                db_path=config.database.path,
                config=config
            )
            
            # Process competitor content
            if competitor_page_ids:
                await process_and_embed(competitor_page_ids, config.database.path, config)
        
        # Analyze gaps
        gaps = await analyze_gaps(config.database.path, config)
        
        # Generate reports
        await generate_reports(gaps, config)
        
        logger.info("=" * 60)
        logger.info("SEO Gap Analysis Complete!")
        logger.info(f"Reports saved to: {config.output.json_report} and {config.output.markdown_report}")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
