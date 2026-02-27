# Multi-Actor Workflows

## When to use
A single Actor can't complete the task — chain results from one Actor as input to another. Also use when you know a person/brand but not their exact social handle on a target platform.

## Pattern 1: Handle Discovery (SERP → Platform Scraper)

**When**: You have a name or brand but need the exact social handle before scraping.

**Chain**: `apify/google-search-scraper` → platform-specific scraper

```
Search: "John Smith CEO Acme Corp Instagram"
         ↓ extract handle from SERP snippet
         → apify/instagram-profile-scraper handle:="johnsmith_acme"
```

**Fits**: Audience Analysis, Influencer Discovery, Content Analytics

**Gotcha**: Verify the handle in the SERP result actually matches the right person — common names return false positives. Run a 1-result test scrape first (Step 6 in main workflow).

## Pattern 2: Web Research (SERP → Content)

**When**: Find web pages about a topic, then scrape their content.

**Chain**: `apify/google-search-scraper` → `apify/website-content-crawler` or `apify-slash-rag-web-browser`

```
Search: "Acme Corp pricing 2024"
         ↓ extract URLs from SERP
         → website-content-crawler startUrls:=[extracted URLs]
```

Use `rag-web-browser` for quick single-page fetches; `website-content-crawler` for multi-page or AI-ready extraction.

**Fits**: Competitor Intelligence, Brand Monitoring, Market Research

## Pattern 3: Lead Discovery (SERP → Contact Enrichment)

**When**: Find business websites by search, then extract contact info.

**Chain**: `apify/google-search-scraper` → `vdrmota/contact-info-scraper`

```
Search: "yoga studios Prague"
         ↓ extract website URLs from SERP
         → contact-info-scraper startUrls:=[extracted URLs]
```

**Fits**: Lead Generation

**Gotcha**: SERP returns ~10 results per page — use `resultsPerPage:=10` and multiple pages if you need volume.

## Pattern 4: Trend Validation (Trends → SERP)

**When**: Confirm a trend with real search data, then find what's being written about it.

**Chain**: `apify/google-trends-scraper` → `apify/google-search-scraper`

```
Trends: rising keyword "oat milk latte"
         ↓ use as search query
         → google-search-scraper query:="oat milk latte recipe"
```

**Fits**: Trend Analysis, Market Research

## Quick lookup: rag-web-browser (no chain needed)

For one-off URL fetches or web searches — call directly, no Actor pipeline:

```bash
mcpc @apify tools-call apify-slash-rag-web-browser query:="san francisco coffee shops"
mcpc @apify tools-call apify-slash-rag-web-browser query:="https://example.com/pricing"
```

Parameters: `query` (required), `maxResults` (default 3), `outputFormats` (`"markdown"` default, `"text"` saves tokens).

## Chaining in practice

Output from step 1 is never directly usable as input to step 2 — always extract the relevant field first, and save to file:

```bash
# Step 1: SERP → save URLs to file
mcpc @apify tools-call call-actor actor:="apify/google-search-scraper" \
  input:='{"queries": "yoga studios Prague", "resultsPerPage": 10}' \
  previewOutput:=false --json \
  | jq -r '.structuredContent.items[].url' > urls.txt

# Step 2: feed URLs into next Actor
mcpc @apify tools-call call-actor actor:="vdrmota/contact-info-scraper" \
  input:="$(jq -Rn '[inputs | select(. != "")] | map({url: .})' urls.txt | jq -n --argjson urls "$(cat /dev/stdin)" '{startUrls: $urls}')"
```

Save intermediate outputs to files — never pipe large datasets through the context.
