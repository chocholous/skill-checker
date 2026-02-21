---
name: apify-mcpc
description: "Finds, evaluates, and runs Apify Actors using the mcpc CLI. Searches Apify Store, compares Actors by stats and ratings, reads input schemas to build correct inputs, runs Actors via call-actor, and retrieves results. Covers 9 marketing intelligence use cases (audience analysis, brand monitoring, competitor intelligence, content analytics, influencer discovery, lead generation, market research, trend analysis, universal scraping) with domain-specific Actor suggestions and gotchas. Use when user wants to scrape data, extract information from websites, run automation, find tools on Apify platform, or search Apify/Crawlee documentation. Do NOT use for developing new Actors (use apify-actor-development skill instead)."
allowed-tools: Bash(mcpc *), Bash(jq *), Read, Grep, Glob
argument-hint: "[use-case or search query]"
---

# mcpc-apify

## Prerequisites

Run before first use in a session:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/apify-mcpc/scripts/check_apify.sh
```

The script checks: mcpc CLI installed, OAuth profile for mcp.apify.com, active @apify and @apify-docs sessions.
If it fails:
- mcpc missing → `npm i -g @anthropic-ai/mcpc`
- OAuth missing → `mcpc mcp.apify.com login`
- Sessions missing → `mcpc mcp.apify.com connect @apify` and/or `mcpc 'mcp.apify.com?tools=docs' connect @apify-docs`

## Environment

mcpc version: !`mcpc --version 2>/dev/null || echo "NOT INSTALLED"`

Active sessions:
!`mcpc 2>&1 | grep -E '(@apify|@apify-docs|mcp.apify.com)' || echo "No active sessions"`

## mcpc CLI Reference

Available tools and arguments (for building correct mcpc calls):
!`mcpc --help 2>/dev/null | head -30 || echo "mcpc not available — install with: npm install -g @apify/mcpc"`

## Use Cases

Match the user's intent to a use case. Each file has suggested Actors, search keywords, and domain-specific gotchas.

| Use Case | File | When |
|---|---|---|
| Audience Analysis | [audience-analysis.md](use-cases/audience-analysis.md) | Demographics, follower behavior, engagement quality |
| Brand Monitoring | [brand-monitoring.md](use-cases/brand-monitoring.md) | Reviews, ratings, sentiment, brand mentions |
| Competitor Intelligence | [competitor-intelligence.md](use-cases/competitor-intelligence.md) | Competitor strategies, ads, pricing, positioning |
| Content Analytics | [content-analytics.md](use-cases/content-analytics.md) | Engagement metrics, campaign ROI, content performance |
| Influencer Discovery | [influencer-discovery.md](use-cases/influencer-discovery.md) | Find influencers, verify authenticity, partnerships |
| Lead Generation | [lead-generation.md](use-cases/lead-generation.md) | B2B/B2C leads, contact enrichment, prospecting |
| Market Research | [market-research.md](use-cases/market-research.md) | Market conditions, pricing, geographic opportunities |
| Trend Analysis | [trend-analysis.md](use-cases/trend-analysis.md) | Emerging trends, viral content, content strategy |
| Universal Scraping | [universal-scraping.md](use-cases/universal-scraping.md) | General-purpose scraping, no specific use case |

**Important**: Actor tables in use-case files are **suggestions, not closed lists**. Always verify via `search-actors` for the latest options.

## mcpc Argument Syntax

All tool arguments use `:=` (no spaces around it). Values are auto-parsed: valid JSON becomes that type, otherwise treated as string.

```bash
keywords:="web scraper"          # string
limit:=5                         # number (valid JSON)
enabled:=true                    # boolean (valid JSON)
input:='{"startUrls":[...]}'     # object — entire JSON as single-quoted string
```

If the first argument starts with `{` or `[`, the whole input is parsed as one JSON structure (not key-value pairs). Pipe JSON via stdin as alternative.

## Connection Modes

### Docs-only mode (no token needed)

```bash
mcpc 'mcp.apify.com?tools=docs' connect @apify-docs
```

Tools: `search-apify-docs`, `fetch-apify-docs` — for searching Apify/Crawlee documentation.

### Full mode (requires authentication)

Authenticate via OAuth (opens browser):

```bash
mcpc mcp.apify.com login
```

Then create a persistent session:

```bash
mcpc mcp.apify.com connect @apify
```

Tools: `search-actors`, `fetch-actor-details`, `call-actor`, `get-actor-output`, `get-actor-run`, `apify-slash-rag-web-browser` + docs tools.

### Missing auth handling

If the task requires Actors and user is not authenticated:

1. Tell the user — they need to run `mcpc mcp.apify.com login` (opens browser for OAuth)
2. Do NOT fall back to docs-only mode silently — the user expects Actor results
3. If auth unavailable, explain what's possible without it (docs only) and ask how to proceed

## Quick Data Retrieval: rag-web-browser

For one-off web searches or URL fetching, use the dedicated tool directly — no need for the full search → call workflow:

```bash
mcpc @apify tools-call apify-slash-rag-web-browser query:="san francisco weather" maxResults:=3
mcpc @apify tools-call apify-slash-rag-web-browser query:="https://www.example.com"
```

Use when: user wants immediate data ("get me info about X", "fetch this URL"), not a specialized scraper.

## Workflow: Find → Understand → Validate → Run → Verify

### Determine workflow scope

Before starting the 7-step workflow, identify what the user actually needs:

- **Docs-only** (user asks about Crawlee, Apify platform, configuration) → skip to [Docs-only Workflow](#docs-only-workflow) section
- **Find-only** (user wants actor recommendation, comparison, schema inspection) → do Steps 1-2, present comparison, STOP. Only continue to Steps 3-7 if user says "run it"
- **Full pipeline** (user wants data extracted/scraped) → follow all 7 steps

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Match use case and search for Actors
- [ ] Step 2: Fetch Actor details and input schema
- [ ] Step 3: Build input and confirm with user
- [ ] Step 4: Validate inputs against the target service
- [ ] Step 5: Run the Actor
- [ ] Step 6: Verify results make sense
- [ ] Step 7: Get results and present to user
```

### Step 1: Match use case and search for Actors

1. Check the [Use Cases](#use-cases) table — read the matching file for suggested Actors and search keywords
2. Search Apify Store for latest options:

```bash
mcpc @apify tools-call search-actors keywords:="instagram profile"
```

- Use 1-3 specific keywords — platform name + data type (e.g., "instagram posts", "amazon products")
- Use keywords from the use-case file when available
- Avoid generic terms like "crawler", "data extraction"
- Pick all valid candidates for comparison
- Actor identifier in results is `fullName` field (e.g., `apify/website-content-crawler`)

### Step 2: Fetch Actor details and input schema

`fetch-actor-details` returns description, README, stats, AND the full input schema in one call. Parameter is `actor` (not actorId):

```bash
mcpc @apify tools-call fetch-actor-details actor:="apify/website-content-crawler"
```

Use `output` parameter to select specific sections and save tokens:

```bash
mcpc @apify tools-call fetch-actor-details actor:="apify/website-content-crawler" output:='{"inputSchema": true}'
mcpc @apify tools-call fetch-actor-details actor:="apify/website-content-crawler" output:='{"readme": true}'
```

Valid `output` fields: `inputSchema`, `readme`, `outputSchema`, `mcpTools` (for MCP server Actors).

- Verify the Actor does what's needed (description, README)
- Check `isDeprecated` — never use deprecated Actors
- Read the input schema — it contains `properties`, `required`, `prefill` for each field
- Compare candidates — see "How to Compare Actors" below
- Interpret schema fields — see "How to Read Input Schema" below
- **Read the README thoroughly** — not just for technical parameters, but for **methodology advice**: how to find correct input values, what formats the target service uses, edge cases, limitations, and tips the author provides. The README often explains how the service being scraped works and what values actually make sense.

### Step 3: Build input and confirm with user

The schema alone is not enough — cross-reference with the README to understand what values the Actor actually expects:

1. **Identify required fields** from the schema's `required` array
2. **Read each field's `description`** — it often specifies exact formats, allowed values, or constraints not captured by `type` alone (e.g., "URL must include protocol", "comma-separated list", "ISO country code")
3. **Check `prefill` values** — use as starting point, adapt to user's actual needs
4. **When the schema description is unclear**, fetch the README (`output:='{"readme": true}'`) — it typically has usage examples with realistic inputs
5. **Show the user** the planned input JSON with explanations. Wait for confirmation before running.

### Step 4: Validate inputs against the target service

Before running the Actor, critically evaluate whether your input values make sense **in the context of how the target service actually works**:

1. **Think about what the service expects** — Does the service use usernames, display names, or IDs? Are the identifiers case-sensitive? Does the service have a specific URL format? Would the service even have the data you're looking for?
2. **Challenge your assumptions** — If you're using identifiers (usernames, URLs, search terms) that you constructed yourself rather than obtained from a reliable source, ask: how confident am I that these are correct? A person named "John Smith" might use "jsmith", "johnsmith123", or "totally_unrelated_handle" on any given platform.
3. **Verify identifiers when uncertain** — If input values are based on guesswork (e.g., assuming a social media username from a person's real name), verify them before running a paid scrape. Options: search the web, check the person's known profiles for cross-links, or run a minimal test (1 result) to confirm the identifier resolves to the expected entity.
4. **Consider the service's data model** — Does the service distinguish between profiles, pages, and groups? Between posts, stories, and reels? Make sure you're targeting the right entity type.

If you cannot confidently verify an input value, tell the user what you're uncertain about and suggest how to resolve it before spending money on a scrape.

### Step 5: Run the Actor

```bash
mcpc @apify tools-call call-actor actor:="apify/website-content-crawler" input:='{"startUrls":[{"url":"https://example.com"}],"proxyConfiguration":{"useApifyProxy":true}}'
```

The response contains `datasetId` and a preview of output items. Note the `datasetId` for Step 6. On input validation error, go back to Step 3.

By default, `call-actor` runs synchronously (waits for completion). For long-running Actors, use `async:=true` — the response will contain `runId` instead; poll status with `get-actor-run`.

### Step 6: Verify results make sense

Before presenting results to the user or fetching the full dataset, do a sanity check on the initial output:

1. **Check result count** — Does the number of results match expectations? Zero results likely means wrong input values, not "no data exists". A suspiciously low or high count warrants investigation.
2. **Spot-check content** — Look at a few result items. Do they correspond to what was requested? If you scraped a person's profile, does the bio/description match who they actually are? If you scraped a business, is it in the right location/industry?
3. **Cross-reference with general knowledge** — You know things about the world. If a famous athlete's profile shows 50 followers, that's almost certainly the wrong account. If a major company's page has no posts, something is off. Use common sense.
4. **Flag anomalies to the user** — If anything looks wrong, say so before proceeding. It's cheaper to re-run with corrected inputs than to deliver bad data.

### Step 7: Get results

Use `datasetId` from Step 5 (not actor name):

```bash
mcpc @apify tools-call get-actor-output datasetId:="<datasetId-from-step-5>"
```

With field selection and pagination:

```bash
mcpc @apify tools-call get-actor-output datasetId:="abc123" fields:="title,url,price" limit:=50
```

If the run was async or is still in progress, check status with `get-actor-run runId:="<runId>"` first.

Check the use-case file for suggested follow-up workflows after presenting results.

### Error handling — Feedback Loop

1. Read the error message
2. Non-obvious fixes:
   - "must have required property 'actor'" → parameter is `actor`, not `actorId`
   - "Authentication required" / 401 → OAuth expired, re-run `mcpc mcp.apify.com login` then `mcpc mcp.apify.com connect @apify`
   - "usage hard limit exceeded" → user's Apify plan limit, inform the user
3. Retry from the appropriate step
4. After 2 failed retries, tell the user what's happening and ask for guidance

## How to Read Input Schema

The input schema from `fetch-actor-details` is standard JSON Schema, but with Apify-specific conventions:

- **`prefill`** — example values provided by the Actor author. Use as starting point for building input.
- **`sectionCaption` / `sectionDescription`** — group related fields; read these to understand field purpose in context.
- **`editor`** — hints at expected format (e.g., `"requestListSources"` means the field expects `[{"url": "..."}]` objects, not plain strings).

### Apify input gotchas

**startUrls pattern** — most scrapers use `startUrls`, which is NOT an array of strings. It's an array of request objects:
```json
// Correct
{"startUrls": [{"url": "https://example.com"}, {"url": "https://example.com/page2"}]}

// Wrong — plain strings don't work
{"startUrls": ["https://example.com"]}
```

**Field naming** — Actors don't follow a single convention. Common variants:
- Max results: `maxItems`, `maxResults`, `maxCrawlPages`, `resultsLimit` — always check the schema
- Search input: `searchTerms`, `queries`, `keywords`, `search` — varies per Actor

**Social handles** — typically without `@`: `"apify"` not `"@apify"`

**Proxy** — when needed: `"proxyConfiguration": {"useApifyProxy": true}`

## How to Compare Actors

| Metric | Prefer |
|--------|--------|
| `isDeprecated` | Always `false` — eliminate first |
| `pricingModel` / cost per run | **Cheapest that works** — prefer lower cost for the use case |
| Author `apify/` | Official, often more reliable |
| `successRate` | Higher (>90% is good, <80% is a red flag) |
| `totalUsers` | Higher = battle-tested (>100 users = safe bet) |
| `lastRunAt` / `modifiedAt` | More recent = maintained |

**Selection rule**: Pick the cheapest Actor that meets functional requirements. Only choose a more expensive Actor if the cheaper one fails, lacks required features, or has poor success rate.

**Fallback chain**: If the chosen Actor fails (error, bad data, deprecated), try the next candidate from the comparison. Don't ask the user before trying an alternative — just report what happened and what you're trying instead. Only stop and ask if all candidates fail.

When in doubt, present top 2-3 to the user with stats.

## Docs-only Workflow

For Apify/Crawlee documentation questions without needing Actors:

```bash
mcpc @apify-docs tools-call search-apify-docs docSource:="apify" query:="proxy configuration" limit:=5
mcpc @apify-docs tools-call fetch-apify-docs url:="https://docs.apify.com/platform/proxy"
```

- `docSource`: `"apify"`, `"crawlee-js"`, or `"crawlee-py"`
- `query`: keywords only, not sentences

## Filtering mcpc Output

mcpc responses can be large. Use these techniques to get only what you need:

### Server-side filtering (preferred — saves tokens)

| Situation | Technique |
|-----------|-----------|
| Need only input schema, not README/stats | `fetch-actor-details ... output:='{"inputSchema": true}'` |
| Need only README | `fetch-actor-details ... output:='{"readme": true}'` |
| Dataset has many fields, need only some | `get-actor-output ... fields:="title,url,price"` |
| Large dataset, need a sample | `get-actor-output ... limit:=10` |
| Paginate through results | `get-actor-output ... offset:=10 limit:=10` |

### Client-side filtering (`--json` + `jq`)

Use when server-side filtering isn't enough or for scripting:

```bash
# Extract actor names from search
mcpc @apify --json tools-call search-actors keywords:="instagram scraper" | \
  jq -r '.structuredContent.actors[].fullName'

# Compare actors by stats
mcpc @apify --json tools-call search-actors keywords:="instagram scraper" | \
  jq -r '.structuredContent.actors[].fullName' | while read -r name; do
    mcpc @apify --json tools-call fetch-actor-details actor:="$name" output:='{"inputSchema": false}' | \
      jq '.structuredContent'
  done
```

JSON responses wrap tool output in `{content, structuredContent}` — always access data via `.structuredContent`.

### When to filter

- **Step 2 (fetch details)**: First call without `output` to get overview. Follow-up calls with `output:='{"inputSchema": true}'` or `output:='{"readme": true}'` to dig deeper without re-fetching everything.
- **Step 7 (get results)**: Always use `fields` if you know which columns matter. Use `limit` for first peek, then fetch more if needed.
- **Comparing actors**: Use `--json` + `jq` to extract stats programmatically when comparing 3+ candidates.

## Recurring runs and scheduling

This skill handles one-shot runs. For recurring/scheduled scraping:

1. **Apify Schedules**: Guide user to set up schedules in Apify Console (UI) — Actors can be scheduled with cron syntax
2. **Webhook integration**: Actors support webhooks on completion — useful for pipelines
3. **Delta detection**: For "only new data" use cases, the agent must implement diffing — Apify doesn't track deltas automatically. Recommend: store previous run's dataset ID, compare on next run.

This skill does NOT create schedules programmatically — that requires Apify API, not mcpc.
