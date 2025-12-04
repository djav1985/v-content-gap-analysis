# AGENTS.md

## 1. Purpose of the Application

This project is a Python-based **SEO Gap AnalysisAgent System**. Its purpose is to:

1. Crawl and parse your website sitemap.
2. Crawl competitor sitemaps.
3. Extract and summarize all relevant page content.
4. Clean, normalize, and chunk page content.
5. Generate embeddings using OpenAI models.
6. Perform semantic clustering and similarity analysis.
7. Detect content gaps, missing topics, weak pages, and structural SEO issues.
8. Run targeted LLM comparisons on important mismatches.
9. Produce a complete structured gap report in both JSON and Markdown formats.

This system functions as an automated, AI‑assisted SEO auditor that delivers actionable content strategy insights.

## 2. Base Directory Structure

```
seo-gap-agent/
│
├── config/
│   ├── settings.yaml
│   └── competitors.yaml
│
├── data/
│   ├── raw_html/
│   ├── cleaned_text/
│   ├── embeddings/
│   ├── pages.db
│   └── logs/
│
├── reports/
│   ├── gap_report.json
│   └── gap_report.md
│
├── app/
│   ├── __init__.py
│   │
│   ├── sitemap/
│   │   ├── fetcher.py
│   │   └── parser.py
│   │
│   ├── crawler/
│   │   ├── fetcher.py
│   │   └── extractor.py
│   │
│   ├── processing/
│   │   ├── cleaner.py
│   │   ├── chunker.py
│   │   ├── metadata.py
│   │   └── summarizer.py
│   │
│   ├── embeddings/
│   │   ├── generator.py
│   │   ├── vectorstore.py
│   │   └── comparer.py
│   │
│   ├── analysis/
│   │   ├── gap_detector.py
│   │   ├── llm_compare.py
│   │   └── recommender.py
│   │
│   ├── reporting/
│   │   ├── json_report.py
│   │   └── markdown_report.py
│   │
│   └── utils/
│       ├── aio.py
│       ├── logger.py
│       ├── config.py
│       └── text.py
│
├── main.py
└── requirements.txt
```

## 3. High‑Level Workflow

### Step 1 – Input

* Primary sitemap URL
* Competitor sitemap URLs
* Optional config (crawl depth, chunk size, thresholds)

### Step 2 – Fetch + Parse Sitemaps

* Download XML
* Extract URLs
* Deduplicate and normalize
* Apply optional URL filtering rules

### Step 3 – Crawl Pages

* Asynchronous HTML fetching
* Extract text, metadata, schema
* Strip boilerplate elements

### Step 4 – Content Processing

* Clean and normalize text
* Extract metadata and structured schema
* Token‑based chunking into ~1500‑token segments
* Store all processed content in SQLite

### Step 5 – Generate Embeddings

* Use OpenAI `text-embedding-3-large`
* Generate vector for each chunk
* Store embeddings in SQLite as BLOBs

### Step 6 – Semantic Clustering

* Cluster semantically similar pages
* Detect shared topics across sites
* Identify competitor topics missing on your site

### Step 7 – Page‑Level Gap Detection

* For each competitor page:

  * Identify your closest matching page
  * If similarity < threshold → missing page
  * If competitor content is 3× longer → thin content
  * If no cluster neighbor exists → content gap

### Step 8 – LLM‑Based Comparison

* Use `gpt-4.1-mini` for deeper page contrast
* Generate:

  * Missing sections
  * Missing arguments
  * Competitive advantages
  * Proposed outlines for new pages

### Step 9 – Final Report Generation

* Output saved to `/reports/gap_report.json` and `/reports/gap_report.md`
* Includes:

  * Missing topics
  * Weak/thin pages
  * Metadata gaps
  * Schema issues
  * Recommended new pages
  * Rewrite suggestions
  * Prioritized roadmap

## 4. Agent Rules & Behavior

### Overseer Agent

* Controls workflow end‑to‑end.
* Validates configuration and input.
* Executes agents in sequence: sitemap → crawl → process → embed → compare → report.
* Handles orchestration and merging of all results.
* Writes authoritative analysis outputs into `/reports/`.

### Sitemap Agent

* Fetches and parses all sitemaps.
* Filters invalid or duplicate URLs.
* Normalizes URL structure.
* Saves raw and processed sitemap files.

### Crawler Agent

* Fetches HTML concurrently.
* Extracts readable text, headings, metadata, and schema.
* Removes boilerplate elements.
* Writes raw and cleaned output to `/data/`.

### Processing Agent

* Normalizes whitespace, strips junk, and cleans HTML remnants.
* Extracts metadata and schema signals.
* Generates content chunks.
* Optional LLM summarization.

### Embedding Agent

* Creates semantic vectors for all content chunks.
* Uses OpenAI embedding models.
* Stores vectors in SQLite.
* Ensures deterministic caching.

### Comparison Agent

* Performs cosine similarity and clustering.
* Identifies content gaps.
* Detects thin, weak, or missing pages.
* Flags outlier content clusters.

### Analysis Agent

* Runs LLM comparisons on important page gaps.
* Generates rewrite suggestions and new page outlines.
* Produces prioritized recommendations.

### Reporting Agent

* Builds JSON and Markdown reports.
* Ensures clear structured output.

## 5. Configuration Overview

### 5.1 `settings.yaml`

```
site: "https://vontainment.com/sitemap.xml"
chunk_size: 1500
similarity_threshold: 0.45
models:
  embeddings: "text-embedding-3-large"
  llm: "gpt-4.1-mini"
```

### 5.2 `competitors.yaml`

```
competitors:
  - https://bigshotmad.com/sitemap.xml
  - https://cejaywebsites.com/sitemap.xml
  - https://wonderfulwebsites.com/port-charlotte/sitemap.xml
```

## 6. Technologies Used

* Python 3.11+
* aiohttp
* Selectolax or BeautifulSoup4
* OpenAI embeddings and LLM API
* SQLite for persistent storage
* numpy for similarity calculations
* scikit‑learn for clustering
* pydantic for structured models (optional)

## 7. Final Output

The system produces a polished, AI‑generated competitive SEO gap analysis, including:

* Missing topics and pages
* Thin or weak content
* Metadata and schema deficiencies
* Suggested new content and page outlines
* Rewrite recommendations for existing pages
* A complete, prioritized SEO roadmap

## 8. Project Work Rules (Critical)

### 8.1 Documentation Enforcement

Before committing or applying any code changes, the system must:

1. Review the current `README.md`.
2. Update it so it accurately reflects the current codebase.
3. Expand it if new workflows or modules were added.
4. Remove outdated explanations.
5. Ensure installation steps and usage examples remain correct.

### 8.2 Automatic CHANGELOG Management

The system must:

1. Create a `CHANGELOG.md` if missing.
2. Append a new entry for every change.
3. Include:

   * Date
   * Files modified
   * Summary of updates
   * Reason for the change

### 8.3 Code Edit / Commit Flow

All code updates must follow this order:

1. Identify the modules affected.
2. Update `README.md` first.
3. Update or create `CHANGELOG.md`.
4. Apply code changes.
5. Re-review `README.md` to confirm accuracy.

No change is complete unless both README and CHANGELOG reflect it.

## 9. Code Quality & Style Rules

### 9.1 General Code Quality Requirements

All code written for this project must be:

* Fully functional and production‑ready.
* Secure by default, following modern security best practices.
* Efficient, predictable, and maintainable.
* Structured to avoid unnecessary complexity or duplication.
* Written to fail safely, with clear error handling paths.

### 9.2 Style & Structure Standards

Code must:

* Follow PEP8 style guidelines.
* Use clear, descriptive variable and function names.
* Organize logic into small, testable functions.
* Avoid large monolithic blocks of logic.
* Ensure consistent indentation and spacing.
* Include type hints for all functions and parameters.
* Include docstrings for all public functions and classes.
* Contain only intentional comments—no clutter or noise.
