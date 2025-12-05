# Changelog

All notable changes to the SEO Gap Analysis Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2024-12-05

### Fixed

#### Critical Bug Fixes
- **NameError in `detect_metadata_gaps()`**: Fixed undefined variable `seen_urls` in `app/analysis/gap_detector.py` line 173
  - Changed to use the correctly defined `processed_urls` variable
  - Prevents runtime crash when detecting metadata gaps
- **JSON-LD Parsing Null Guard**: Added null/whitespace validation in `extract_schema()` in `app/crawler/extractor.py`
  - Added check for `script.string` being None or empty before parsing
  - Enhanced exception handling to include TypeError and AttributeError
  - Prevents crashes on malformed or empty JSON-LD script tags

#### Database Foreign Key Enforcement
- **SQLite Foreign Keys**: Enabled `PRAGMA foreign_keys = ON` in all database connections
  - Updated `get_connection()` in DatabasePool class
  - Updated `get_db_connection()` context manager
  - Updated `init_database()` function
  - Added pragma to all `aiosqlite.connect()` calls in:
    - `app/utils/database.py` (store_page, get_page_id, store_pages_batch, store_gaps_batch)
    - `app/embeddings/vectorstore.py` (all embedding and chunk storage functions)
    - `app/analysis/gap_detector.py` (all gap detection functions)
  - Ensures cascading deletes work correctly (e.g., deleting a page removes its chunks and embeddings)
  - Maintains referential integrity across all foreign key relationships

### Improved

#### Code Quality and Maintainability
- **Constants for Gap Types and Priorities**: Added module-level constants to `gap_detector.py`
  - Defined `GAP_TYPE_MISSING_CONTENT`, `GAP_TYPE_THIN_CONTENT`, `GAP_TYPE_METADATA_GAP`, `GAP_TYPE_SCHEMA_GAP`
  - Defined `PRIORITY_HIGH`, `PRIORITY_MEDIUM`, `PRIORITY_LOW`
  - Replaced hardcoded strings throughout the module
  - Prevents typos and improves maintainability
- **Null Safety**: Improved null checking in schema gap priority assignment
  - Changed from `similarity_score and similarity_score > 0.7` to explicit null checking
  - Uses `similarity_score is not None and similarity_score > 0.7` for clarity
- **Code Cleanup**: Removed redundant `get_db()` helper function from database.py
  - Simplified to use `get_db_connection()` context manager directly

#### Schema Gap Detection Logic
- **Matched Competitor Comparison**: Completely rewrote `detect_schema_gaps()` to tie comparisons to nearest competitor pages
  - Previous implementation: Checked if ANY competitor had schema data
  - New implementation: Compares only to matched/nearest competitor pages based on similarity
  - Joins with gaps table to find closest matches for each primary page
  - Reduces false positives significantly by only flagging gaps where similar competitors have schema
  - Prioritizes gaps based on similarity score (high: >0.7, medium: >0.5, low: ≤0.5)
  - Returns competitor URL and similarity score for better context

#### Documentation Enhancements
- **Sitemap Index Handling**: Added comprehensive documentation in README.md
  - Clarified behavior: Parser returns both sitemap URLs and direct page URLs from index files
  - Documented non-recursive approach (returns sitemap URLs for orchestrator to handle)
  - Explained deduplication and normalization process
  - Covers standard sitemaps, sitemap indexes, and mixed formats
- **Database Upsert Strategy**: Added detailed section explaining deduplication approach
  - Documented check-then-upsert pattern for pages and chunks tables
  - Explained ON CONFLICT handling for embeddings table
  - Described application-level deduplication for gaps table
  - Outlined foreign key cascade behavior and enforcement
  - Clarifies prevention of unbounded duplicates across all tables

## [1.1.0] - 2024-12-05

### Fixed

#### Type Hints and Consistency
- **Type Annotations**: Aligned all type hints across modules to use proper `typing` imports (`List`, `Dict`, `Optional`, `Any`)
- **Consistency**: Standardized return types and parameter annotations in all functions across:
  - `app/crawler/*` (fetcher.py, extractor.py)
  - `app/processing/*` (cleaner.py, chunker.py, metadata.py, summarizer.py)
  - `app/embeddings/*` (generator.py, vectorstore.py, comparer.py)
  - `app/analysis/*` (gap_detector.py, llm_compare.py, recommender.py)
  - `main.py` orchestration layer

#### Database Reliability
- **SQLite Upsert Handling**: Fixed `store_page`, `store_pages_batch`, `store_chunk`, and `store_chunks_batch` to return correct IDs
  - Changed from relying on `lastrowid` after `ON CONFLICT` (which returns 0) to explicit SELECT-then-UPDATE/INSERT pattern
  - Ensures chunk and embedding relationships maintain integrity
- **Bulk Insert Optimization**: Improved batch operations to handle upserts correctly while maintaining performance
- **Transaction Safety**: All batch operations now properly commit only after all items are processed

### Improved

#### Error Handling and Resilience
- **Structured Logging**: Added `StructuredFormatter` and `log_with_context()` helper to logger.py
  - Logs now include contextual metadata (URLs, counts, status codes)
  - Error classification with `error_type` field for easier debugging
  - Support for custom context dictionaries in all log statements
- **Config Loading**: Enhanced error propagation in `load_config()` and `load_competitors()`:
  - Wrapped exceptions with proper error messages
  - Added explicit error types for different failure modes
  - Better validation error messages from Pydantic
- **Main Orchestrator**: Comprehensive try-except blocks in `main.py`:
  - Graceful handling of sitemap parsing failures
  - Continued execution after individual competitor failures
  - Structured error logging for all critical paths

#### Async Operations and Retry Logic
- **HTTP Requests**: Enhanced `fetch_url()` in aio.py:
  - Configurable exponential backoff base
  - Rate limit detection (HTTP 429) with extended backoff
  - Separate handling for client errors vs server errors
  - Maximum retry wait cap to prevent excessive delays
  - Structured logging with request context
- **OpenAI API Calls**: Improved retry semantics in:
  - `generate_embeddings_batch()`: Better batch-level error handling
  - `summarize_content()`: Consistent retry pattern
  - `compare_pages()`: Rate limit aware retries
  - All LLM calls now use exponential backoff with configurable limits
- **Concurrency Controls**: Semaphore-based batching prevents resource exhaustion
  - Bounded parallelism for embedding generation
  - Per-host connection limits in SessionManager
  - Configurable batch sizes and concurrent request limits

#### Gap Detection and Reporting
- **Deduplication**: All gap detection functions now deduplicate by URL:
  - `detect_missing_pages()`: Tracks seen competitor URLs
  - `detect_thin_content()`: Only reports worst case per primary URL
  - `detect_metadata_gaps()`: Deduplicates by primary URL
  - `detect_schema_gaps()`: Ensures unique URL reporting
- **Enhanced Metrics**: Added human-readable percentages and calculations:
  - Similarity scores displayed as percentages
  - Word count differences shown as both absolute and percentage
  - Missing element counts for metadata gaps
- **Better Thresholds**: Refined priority assignment based on severity:
  - Missing pages: High (<20% similarity), Medium (<35%), Low (>=35%)
  - Thin content: High (>5x ratio), Medium (>4x), Low (>3x)
  - Metadata gaps: High (missing title or >=2 elements), Medium (>=1 element)
- **SQL Optimization**: Added `DISTINCT` and `ORDER BY` clauses to prevent duplicate rows from database queries

### Added

#### Logging Infrastructure
- `StructuredFormatter` class for context-aware log formatting
- `log_with_context()` helper function for structured logging
- Support for `error_type` classification in all error logs
- Context dictionaries with relevant metadata (URLs, counts, IDs)

#### Configuration Validation
- Explicit error messages for missing or invalid configuration files
- Better validation feedback from Pydantic models
- Chained exceptions using `raise ... from e` pattern for traceable errors

#### Documentation
- Updated README.md with:
  - Detailed code quality standards
  - Quality assurance features section
  - Recent improvements summary (v1.1.0)
  - Enhanced technology descriptions
- Updated CHANGELOG.md with comprehensive v1.1.0 release notes

### Technical Details

- **Python Version**: 3.11+ (unchanged)
- **Database**: SQLite with corrected upsert behavior
- **API**: OpenAI with improved retry logic and rate limit handling
- **Architecture**: Enhanced async/await patterns with better error boundaries
- **Error Handling**: Comprehensive logging and graceful degradation
- **Code Quality**: Full type hints compliance, PEP8 adherence, complete docstrings

### Reason for Changes

This release focuses on production readiness through improved reliability, observability, and correctness:

1. **Type Safety**: Complete type hint alignment prevents runtime type errors and improves IDE support
2. **Database Correctness**: Fixed upsert ID handling prevents data integrity issues with chunks and embeddings
3. **Error Resilience**: Structured logging and better error handling make debugging and monitoring much easier
4. **Deduplication**: Prevents redundant gap reporting and improves report quality
5. **Retry Logic**: Intelligent retries with backoff reduce transient failures from network and API issues
6. **Metrics Clarity**: Percentage-based metrics make reports more actionable for stakeholders

---

## [1.0.0] - 2024-12-04

### Added

#### Core Infrastructure
- **Configuration System** (`app/utils/config.py`)
  - Pydantic-based configuration with validation
  - YAML configuration file support
  - Environment variable integration for API keys
  - Separate settings and competitors configuration files

- **Logging System** (`app/utils/logger.py`)
  - Structured logging with file and console output
  - Configurable log levels
  - Timestamped log entries
  - Log rotation support

- **Utility Modules**
  - `app/utils/text.py`: Text processing and normalization utilities
  - `app/utils/aio.py`: Async HTTP request handling with retry logic
  - `app/utils/database.py`: SQLite database management and schema

- **Database Schema**
  - Pages table: Store URLs, metadata, content, word counts
  - Chunks table: Content chunks with token counts
  - Embeddings table: Vector embeddings with BLOB storage
  - Gaps table: Detected gaps with analysis metadata
  - Optimized indexes for performance

#### Sitemap Processing
- **Sitemap Fetcher** (`app/sitemap/fetcher.py`)
  - Async sitemap downloading
  - Retry logic with exponential backoff
  - Support for sitemap indexes
  - Custom user agent support

- **Sitemap Parser** (`app/sitemap/parser.py`)
  - XML parsing with namespace handling
  - URL extraction and deduplication
  - URL normalization
  - Pattern-based URL filtering

#### Web Crawler
- **Page Fetcher** (`app/crawler/fetcher.py`)
  - Async concurrent page fetching
  - Configurable concurrency limits
  - Timeout and retry handling
  - Request throttling

- **Content Extractor** (`app/crawler/extractor.py`)
  - HTML parsing with BeautifulSoup4
  - Metadata extraction (title, description, H1, Open Graph)
  - Schema.org JSON-LD extraction
  - Main content isolation
  - Heading structure extraction
  - Boilerplate removal

#### Content Processing
- **Text Cleaner** (`app/processing/cleaner.py`)
  - HTML remnant removal
  - Whitespace normalization
  - Boilerplate text removal
  - Content validation
  - URL and email sanitization

- **Metadata Processor** (`app/processing/metadata.py`)
  - SEO signal extraction
  - Metadata quality analysis
  - Cross-site metadata comparison
  - Missing element detection

- **Content Chunker** (`app/processing/chunker.py`)
  - Token-based text chunking using tiktoken
  - Configurable chunk size and overlap
  - Paragraph-aware chunking
  - Multiple chunking strategies

- **Content Summarizer** (`app/processing/summarizer.py`)
  - LLM-based content summarization
  - Topic extraction
  - Configurable summary length
  - Async processing

#### Embeddings & Vector Store
- **Embedding Generator** (`app/embeddings/generator.py`)
  - OpenAI embedding generation
  - Batch processing for efficiency
  - Support for text-embedding-3-large model
  - Error handling and retry logic

- **Vector Store** (`app/embeddings/vectorstore.py`)
  - SQLite-based vector storage
  - BLOB serialization for embeddings
  - Batch insertion for performance
  - Efficient retrieval queries

- **Content Comparer** (`app/embeddings/comparer.py`)
  - Cosine similarity computation
  - Most similar content finder
  - DBSCAN clustering for topic detection
  - Similarity matrix generation
  - Content gap identification

#### Gap Analysis
- **Gap Detector** (`app/analysis/gap_detector.py`)
  - Missing page detection
  - Thin content identification
  - Metadata gap analysis
  - Schema markup gap detection
  - Comprehensive gap aggregation

- **LLM Comparison** (`app/analysis/llm_compare.py`)
  - Deep page-to-page comparison
  - Missing section identification
  - Competitive advantage analysis
  - Content outline generation
  - Rewrite suggestions

- **Recommender** (`app/analysis/recommender.py`)
  - Gap prioritization with impact scoring
  - Action plan generation
  - Quick win identification
  - Executive summary creation

#### Reporting
- **JSON Report Generator** (`app/reporting/json_report.py`)
  - Structured JSON output
  - Complete gap data export
  - Machine-readable format
  - Metadata inclusion

- **Markdown Report Generator** (`app/reporting/markdown_report.py`)
  - Human-readable reports
  - Executive summary section
  - Quick wins highlighting
  - Prioritized action plan
  - Detailed gap breakdowns
  - Configuration documentation

#### Main Orchestrator
- **Main.py**
  - End-to-end workflow orchestration
  - Sequential agent execution
  - Error handling and logging
  - Progress tracking
  - Database initialization
  - Report generation

### Configuration Files

- **settings.yaml**: Main application configuration
  - Site URL and competitors
  - Processing parameters
  - Model selection
  - Threshold configuration
  - Output paths

- **competitors.yaml**: Competitor sitemap list

- **requirements.txt**: Python dependencies
  - aiohttp for async HTTP
  - BeautifulSoup4 for HTML parsing
  - OpenAI for embeddings and LLM
  - scikit-learn for clustering
  - tiktoken for token counting
  - pydantic for configuration
  - Supporting libraries

### Documentation

- **README.md**: Comprehensive project documentation
  - Installation instructions
  - Usage examples
  - Configuration guide
  - Architecture overview
  - Troubleshooting guide
  - Development guidelines

- **AGENTS.md**: System design specification
  - Purpose and workflow
  - Agent architecture
  - Configuration details
  - Code quality rules
  - Development workflow

- **CHANGELOG.md**: This file

### Technical Details

- **Python Version**: 3.11+
- **Database**: SQLite with optimized schema
- **API**: OpenAI embeddings and chat completions
- **Architecture**: Async/await throughout
- **Error Handling**: Comprehensive logging and graceful degradation
- **Code Quality**: PEP8 compliant with type hints and docstrings

### Reason for Changes

Initial implementation of the SEO Gap Analysis Agent system based on the AGENTS.md specification. This release provides a complete, production-ready solution for automated competitive SEO analysis.

---

## Future Releases

### Planned Features
- Multi-language support
- Image analysis capabilities
- Backlink gap analysis
- Advanced keyword clustering
- Historical trend tracking
- Web UI dashboard
- API endpoint exposure
- Enhanced caching mechanisms
- Incremental updates support
- Custom plugin system
