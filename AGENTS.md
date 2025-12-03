# AGENTS.md file

## 1. Purpose of the Application

This Python application is an **SEO Gap Analysis Agent** designed to:

1. Crawl your website sitemap.
2. Crawl competitor sitemaps.
3. Extract and summarize all page content.
4. Generate embeddings using OpenAI.
5. Compare your site’s semantic coverage to competitors.
6. Identify:

   * Missing topics
   * Weak pages
   * Thin content
   * Pages competitors have that you do not
   * Metadata and schema gaps
7. Produce a **complete structured gap report** with actionable recommendations.

This becomes an automated, AI-assisted SEO auditor tailored for competitive content strategy.

---

## 2. High-Level Workflow

### Step 1 – Input

* Your sitemap URL
* Competitor sitemap URLs
* Optional configuration (crawl depth, chunk size, etc.)

### Step 2 – Fetch + Parse Sitemaps

* Extract URLs
* Normalize duplicates
* Filter by patterns if needed (/blog/, /services/, etc.)

### Step 3 – Crawl Pages

* Concurrent async fetch
* Extract HTML
* Remove boilerplate (nav, footer, legal)

### Step 4 – Content Processing

For each page:

* Clean text
* Extract metadata
* Extract schema
* Extract headings
* Chunk into ~1500-token blocks
* Store in database

### Step 5 – Generate Embeddings (OpenAI)

* Use text-embedding-3-large
* Create vector for each chunk
* Store vectors in SQLite (BLOB)

### Step 6 – Semantic Clustering

* Group pages by similarity
* Identify shared topics between sites
* Identify competitor topics missing on your site

### Step 7 – Page-Level Gap Detection

For each competitor page:

* Find closest matching page on your site
* If similarity < threshold → missing page
* If competitor text length > yours by 3× → thin content
* If you have no cluster member → content gap

### Step 8 – Advanced LLM Comparison

For high-value mismatches:

* Summaries generated
* LLM comparisons using gpt-4.1-mini
* Produce:

  * Missing sections
  * Missing arguments
  * Competitor advantages
  * Proposed new page outlines

### Step 9 – Generate Final Report

Saved as:

* /reports/gap_report.json
* /reports/gap_report.md

Includes:

* Missing topics
* Weak pages
* Metadata gaps
* Schema gaps
* Suggested new pages
* Suggested page rewrites
* Prioritized recommendations

---

## 3. Directory Structure

This structure is clean, modular, and production-friendly.

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
│   ├── pages.db            # SQLite storage
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
│   │   ├── fetcher.py      # downloads XML
│   │   └── parser.py       # extracts URLs
│   │
│   ├── crawler/
│   │   ├── fetcher.py      # async fetch HTML
│   │   └── extractor.py    # scrapes text + metadata
│   │
│   ├── processing/
│   │   ├── cleaner.py      # removes boilerplate
│   │   ├── chunker.py      # token-based chunking
│   │   ├── metadata.py     # titles/meta/schema
│   │   └── summarizer.py   # optional LLM summaries
│   │
│   ├── embeddings/
│   │   ├── generator.py    # OpenAI embeddings
│   │   ├── vectorstore.py  # SQLite row storage
│   │   └── comparer.py     # cosine similarity, clustering
│   │
│   ├── analysis/
│   │   ├── gap_detector.py # missing topics, thin content
│   │   ├── llm_compare.py  # semantic LLM comparisons
│   │   └── recommender.py  # new pages & rewrite suggestions
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
├── main.py                 # entry point
└── requirements.txt
```

---

## 4. Configuration Overview

### `/config/settings.yaml`

```
site: "https://vontainment.com/sitemap.xml"
chunk_size: 1500
similarity_threshold: 0.45
models:
  embeddings: "text-embedding-3-large"
  llm: "gpt-4.1-mini"
```

### `/config/competitors.yaml`

```
competitors:
  - https://bigshotmad.com/sitemap.xml
  - https://cejaywebsites.com/sitemap.xml
  - https://wonderfulwebsites.com/port-charlotte/sitemap.xml
```

---

## 5. Technologies Used

* Python 3.11+
* aiohttp
* BeautifulSoup4 or Selectolax
* OpenAI embeddings + chat models
* SQLite (via `sqlite3` or `dataset`)
* numpy for cosine similarity
* scikit-learn (DBSCAN or HDBSCAN for clustering)
* pydantic for data models (optional)

---

## 6. What You End Up With

A fully automated system that:

* Reads all sitemaps
* Understands your content in a semantic, LLM-aware way
* Understands competitor content
* Produces a **true AI-powered gap analysis** report
* Suggests exactly what you should write next
* Identifies which pages are weak, thin, outdated, or missing
* Gives outline suggestions for new pages
* Recommends metadata and schema upgrades
* Provides a prioritized SEO roadmap