# Quick Start Guide

Get up and running with the SEO Gap Analysis Agent in 5 minutes.

## Step 1: Install Dependencies

```bash
# Clone the repository (if not already done)
git clone https://github.com/djav1985/v-content-gap-analysis.git
cd v-content-gap-analysis

# Install Python dependencies
pip install -r requirements.txt
```

## Step 2: Configure API Key

Create a `.env` file in the project root:

```bash
echo "OPENAI_API_KEY=sk-your-actual-api-key-here" > .env
```

Or copy the example:

```bash
cp .env.example .env
# Then edit .env and add your API key
```

## Step 3: Configure Your Site

Edit `config/settings.yaml`:

```yaml
site: "https://your-website.com/sitemap.xml"
```

## Step 4: Add Competitors

Edit `config/competitors.yaml`:

```yaml
competitors:
  - https://competitor1.com/sitemap.xml
  - https://competitor2.com/sitemap.xml
  - https://competitor3.com/sitemap.xml
```

## Step 5: Run the Analysis

```bash
python main.py
```

The agent will:
1. ✅ Fetch your sitemap and competitor sitemaps
2. ✅ Crawl pages (limited to 50 per site for initial run)
3. ✅ Extract and analyze content
4. ✅ Generate semantic embeddings
5. ✅ Detect content gaps
6. ✅ Create comprehensive reports

## Step 6: Review Reports

Check the generated reports in the `reports/` directory:

```bash
# View the markdown report
cat reports/gap_report.md

# Or view JSON for programmatic access
cat reports/gap_report.json
```

## What You'll Get

### Quick Wins
Immediate improvements you can make:
- Missing metadata (titles, descriptions)
- Missing schema markup
- Easy content additions

### Prioritized Action Plan
Complete roadmap with:
- Missing content pages
- Thin content to expand
- SEO gaps to address

### Detailed Analysis
- Similarity scores
- Word count comparisons
- Competitive insights

## Configuration Tips

### Adjust Analysis Depth

In `config/settings.yaml`:

```yaml
# More strict similarity (fewer gaps found)
similarity_threshold: 0.60

# Less strict (more gaps found)
similarity_threshold: 0.30

# Larger chunks = fewer API calls
chunk_size: 2000

# More concurrent requests = faster (but higher load)
max_concurrent_requests: 20
```

### Limit Pages Analyzed

Edit `main.py` to change page limits:

```python
# Line ~XXX - adjust these numbers
primary_urls[:50]  # Change 50 to desired number
competitor_urls[:50]  # Change 50 to desired number
```

## Troubleshooting

### "OPENAI_API_KEY not set"
- Make sure `.env` file exists
- Check that API key is valid
- Try: `export OPENAI_API_KEY=sk-your-key`

### "No URLs found in sitemap"
- Verify sitemap URL is correct
- Check sitemap is publicly accessible
- Try accessing sitemap in browser first

### Process is slow
- Reduce number of pages
- Increase `max_concurrent_requests`
- Use smaller `chunk_size`

### High API costs
- Reduce pages analyzed
- Use `text-embedding-3-small` instead of large
- Increase `chunk_size` to create fewer chunks

## Next Steps

1. **Validate Quick Wins** - Start with the easiest improvements
2. **Prioritize Missing Content** - Create briefs for high-impact pages
3. **Schedule Updates** - Plan metadata and schema additions
4. **Monitor Progress** - Re-run analysis monthly

## Advanced Usage

### Custom Filtering

Add URL filtering in sitemap parser:

```python
filtered_urls = filter_urls(
    urls,
    include_patterns=[r'/blog/', r'/products/'],
    exclude_patterns=[r'/tag/', r'/author/']
)
```

### LLM Comparison

For deeper analysis on specific gaps, the system automatically uses GPT-4 mini for comparisons.

### Database Queries

Access the SQLite database directly:

```bash
sqlite3 data/pages.db
```

```sql
-- View all pages
SELECT url, word_count, is_primary FROM pages;

-- View gaps
SELECT * FROM gaps ORDER BY similarity_score;
```

## Support

- Check logs: `tail -f data/logs/seo_gap_agent.log`
- Review documentation: `README.md`
- See architecture: `AGENTS.md`

Happy analyzing! 🚀
