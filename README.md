# SEO Content Gap Analysis Agent

An advanced AI-powered system that analyzes your website against competitors to identify content gaps, SEO opportunities, and strategic improvements.

## Overview

This Python-based SEO Gap Analysis Agent automates competitive content analysis using:
- **Web Crawling**: Asynchronous sitemap processing and page fetching
- **AI Analysis**: OpenAI embeddings and LLM-powered content comparison
- **Semantic Clustering**: Identify topic gaps and content opportunities
- **Automated Reporting**: Comprehensive JSON and Markdown reports

## Features

### Core Capabilities

- ✅ **Sitemap Processing**: Fetch and parse XML sitemaps from your site and competitors
- ✅ **Content Extraction**: Extract clean text, metadata, and schema from HTML pages
- ✅ **Semantic Analysis**: Generate embeddings for content similarity comparison
- ✅ **Gap Detection**: Identify missing pages, thin content, and metadata issues
- ✅ **LLM Insights**: Deep content comparison using GPT-4
- ✅ **Actionable Reports**: Prioritized recommendations with quick wins

### Analysis Types

1. **Missing Content**: Competitor pages with no similar content on your site
2. **Thin Content**: Your pages significantly shorter than competitor equivalents
3. **Metadata Gaps**: Missing or incomplete title tags, descriptions, H1s
4. **Schema Gaps**: Pages lacking structured data markup
5. **Topic Clustering**: Semantic grouping to find content themes

## Installation

### Prerequisites

- Python 3.11 or higher
- OpenAI API key

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/djav1985/v-content-gap-analysis.git
cd v-content-gap-analysis
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

4. **Configure settings**:
Edit `config/settings.yaml`:
```yaml
site: "https://your-site.com/sitemap.xml"
chunk_size: 1500
similarity_threshold: 0.45
```

5. **Add competitors**:
Edit `config/competitors.yaml`:
```yaml
competitors:
  - https://competitor1.com/sitemap.xml
  - https://competitor2.com/sitemap.xml
```

## Usage

### Basic Usage

Run the analysis:
```bash
python main.py
```

The agent will:
1. Fetch and parse all sitemaps
2. Crawl pages from your site and competitors
3. Extract and clean content
4. Generate semantic embeddings
5. Perform gap analysis
6. Generate comprehensive reports

### Output

Reports are saved to the `reports/` directory:

- **`gap_report.json`**: Machine-readable analysis with all data
- **`gap_report.md`**: Human-readable report with recommendations

### Example Report Sections

The Markdown report includes:
- **Executive Summary**: Overview of total gaps and priorities
- **Quick Wins**: High-impact, low-effort improvements
- **Prioritized Action Plan**: Complete roadmap
- **Detailed Gap Analysis**: In-depth breakdown by category

## Project Structure

```
v-content-gap-analysis/
├── app/
│   ├── sitemap/          # Sitemap fetching and parsing
│   ├── crawler/          # HTML fetching and extraction
│   ├── processing/       # Text cleaning, chunking, summarization
│   ├── embeddings/       # Vector generation and comparison
│   ├── analysis/         # Gap detection and recommendations
│   ├── reporting/        # Report generation
│   └── utils/            # Configuration, logging, utilities
├── config/
│   ├── settings.yaml     # Main configuration
│   └── competitors.yaml  # Competitor sitemaps
├── data/
│   ├── raw_html/         # Cached HTML
│   ├── cleaned_text/     # Processed content
│   ├── embeddings/       # Vector data
│   ├── pages.db          # SQLite database
│   └── logs/             # Application logs
├── reports/              # Generated reports
├── main.py               # Main orchestrator
└── requirements.txt      # Python dependencies
```

## Configuration

### Settings (`config/settings.yaml`)

Key configuration options:

```yaml
# Primary site to analyze
site: "https://your-site.com/sitemap.xml"

# Chunk size for embeddings (tokens)
chunk_size: 1500

# Similarity threshold (0-1, lower = stricter)
similarity_threshold: 0.45

# Concurrent request limit
max_concurrent_requests: 10

# Models
models:
  embeddings: "text-embedding-3-large"
  llm: "gpt-4o-mini"

# Analysis thresholds
thresholds:
  thin_content_ratio: 3.0  # Competitor/your word count
  min_similarity: 0.45
  cluster_min_samples: 2
```

## Architecture

### Workflow

```
1. Input → Load config & competitor list
2. Sitemap → Fetch & parse all sitemaps
3. Crawler → Async HTML fetching & extraction
4. Processing → Clean, chunk, extract metadata
5. Embeddings → Generate semantic vectors
6. Analysis → Compare, cluster, detect gaps
7. LLM → Deep content comparison
8. Reports → Generate JSON & Markdown output
```

### Agent System

The application uses a modular agent architecture:

- **Overseer Agent** (`main.py`): Orchestrates end-to-end workflow
- **Sitemap Agent**: Fetches and parses sitemaps
- **Crawler Agent**: Fetches HTML and extracts content
- **Processing Agent**: Cleans and chunks content
- **Embedding Agent**: Generates semantic vectors
- **Comparison Agent**: Finds similarities and gaps
- **Analysis Agent**: LLM-based deep analysis
- **Reporting Agent**: Generates structured reports

## Database Schema

SQLite database (`data/pages.db`) structure:

- **pages**: URL, domain, metadata, content, word count
- **chunks**: Content chunks with token counts
- **embeddings**: Vector embeddings (BLOB storage)
- **gaps**: Detected gaps with analysis

## Technologies

- **Python 3.11+**: Core language with modern async/await patterns
- **aiohttp**: Async HTTP requests with connection pooling and retry logic
- **BeautifulSoup4/Selectolax**: HTML parsing and content extraction
- **OpenAI API**: Embeddings (text-embedding-3-large) and LLM analysis (gpt-4o-mini)
- **scikit-learn**: Clustering and similarity computation with DBSCAN
- **SQLite**: Data persistence with optimized upsert operations
- **tiktoken**: Accurate token counting for chunking and cost estimation
- **Pydantic**: Runtime data validation and settings management
- **PyYAML**: Configuration file parsing with validation

## Development

### Code Quality

All code follows:
- **PEP8 style guidelines**: Consistent formatting and naming conventions
- **Type hints for all functions**: Complete type annotations using `typing` module
- **Comprehensive docstrings**: Detailed documentation for all public functions and classes
- **Error handling with structured logging**: Context-aware logging with error classification
- **Resilient retry logic**: Exponential backoff for API calls and network requests
- **Database transaction safety**: Proper upsert handling with correct ID returns
- **Input validation**: Pydantic models for data validation before database operations

### Quality Assurance Features

- **Structured Logging**: All logs include contextual information (URLs, counts, error types)
- **Error Propagation**: Exceptions are properly wrapped and classified for debugging
- **Retry Mechanisms**: Configurable retry logic with exponential backoff for:
  - HTTP requests (rate limiting aware)
  - OpenAI API calls (embedding and LLM)
  - Database operations (transaction safety)
- **Deduplication**: Gap detection includes URL-based deduplication to avoid redundant reports
- **Percentage Metrics**: All comparisons include human-readable percentage differences
- **Concurrency Controls**: Semaphore-based batching prevents resource exhaustion

### Adding New Features

1. Create module in appropriate `app/` subdirectory
2. Follow existing patterns for async operations
3. Add structured logging with context for observability
4. Implement retry logic for external calls
5. Validate inputs using Pydantic models
6. Add proper type hints and docstrings
7. Update configuration if needed
8. Update this README and CHANGELOG

## Troubleshooting

### Common Issues

**"OPENAI_API_KEY not set"**
- Create `.env` file with your API key
- Or export as environment variable

**"No URLs found in sitemap"**
- Verify sitemap URL is accessible
- Check sitemap XML format
- Review logs in `data/logs/`

**"Failed to fetch pages"**
- Check internet connectivity
- Verify user agent isn't blocked
- Reduce `max_concurrent_requests`

**High API costs**
- Reduce number of pages analyzed
- Use smaller embedding model
- Adjust `chunk_size` to reduce chunks

## Limitations

- Requires OpenAI API access (paid)
- Processing time scales with page count
- Rate limits apply to API calls
- Embedding storage can be large

## Future Enhancements

- [ ] Multi-language support
- [ ] Image analysis
- [ ] Backlink gap analysis
- [ ] Keyword clustering
- [ ] Historical trend tracking
- [ ] Web UI dashboard

## License

See LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- Check existing issues on GitHub
- Review logs in `data/logs/`
- Consult OpenAI API documentation

## Acknowledgments

Built with modern Python async patterns and OpenAI's powerful embedding and language models.

---

**Version**: 1.1.0  
**Author**: SEO Gap Analysis Team  
**Last Updated**: 2024-12-05

## Recent Improvements (v1.1.0)

- **Enhanced Type Safety**: Complete type hints across all modules using proper `typing` imports
- **Improved Error Handling**: Structured logging with contextual information and error classification
- **Better Retry Logic**: Exponential backoff with configurable limits for all external calls
- **Database Reliability**: Fixed upsert ID handling to return correct IDs after conflict resolution
- **Deduplication**: Gap detection now deduplicates by URL to prevent redundant recommendations
- **Metrics Enhancement**: Added percentage calculations and human-readable comparisons
- **Concurrency Controls**: Improved semaphore-based batching for API calls
- **Validation Strengthening**: Pydantic validation before all database writes
