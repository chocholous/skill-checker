# apify-mcpc plugin

Claude Code plugin for finding, evaluating, and running [Apify Actors](https://apify.com/store) using the [mcpc CLI](https://www.npmjs.com/package/@apify/mcpc).

## What it does

- Searches Apify Store for the right Actor for any scraping/automation task
- Compares Actors by stats, ratings, and maintenance status
- Reads input schemas to build correct Actor inputs
- Runs Actors and retrieves structured results
- Covers 9 marketing intelligence use cases with domain-specific guidance

## Prerequisites

- [mcpc CLI](https://www.npmjs.com/package/@apify/mcpc): `npm install -g @apify/mcpc`
- Apify account with OAuth: `mcpc mcp.apify.com login`

## Installation

### From skill-checker marketplace

```bash
claude marketplace add chocholous/skill-checker
claude plugin install apify-mcpc@skill-checker
```

### Local development

```bash
claude --plugin-dir ./plugins/apify-mcpc
```

## Use cases

The plugin includes 9 use-case files with suggested Actors, search keywords, and gotchas:

| Use Case | Description |
|---|---|
| Audience Analysis | Demographics, follower behavior, engagement quality |
| Brand Monitoring | Reviews, ratings, sentiment, brand mentions |
| Competitor Intelligence | Competitor strategies, ads, pricing, positioning |
| Content Analytics | Engagement metrics, campaign ROI, content performance |
| Influencer Discovery | Find influencers, verify authenticity, partnerships |
| Lead Generation | B2B/B2C leads, contact enrichment, prospecting |
| Market Research | Market conditions, pricing, geographic opportunities |
| Trend Analysis | Emerging trends, viral content, content strategy |
| Universal Scraping | General-purpose scraping for any platform |

Actor tables in use-case files are **suggestions, not closed lists**. The agent always searches Apify Store for the latest options.

## Plugin structure

```
plugins/apify-mcpc/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── skills/
│   └── apify-mcpc/
│       ├── SKILL.md             # Main skill (workflow, mcpc reference)
│       ├── scripts/
│       │   └── check_apify.sh   # Prerequisite check
│       └── references/
│           ├── issue-reporting.md   # Issue reporting template
│           └── use-cases/
│               ├── audience-analysis.md
│               ├── brand-monitoring.md
│               ├── competitor-intelligence.md
│               ├── content-analytics.md
│               ├── influencer-discovery.md
│               ├── lead-generation.md
│               ├── market-research.md
│               ├── trend-analysis.md
│               └── universal-scraping.md
├── LICENSE                      # Apache 2.0
└── README.md
```

## Features

- **Dynamic context**: `!command` injection prefetches mcpc version, active sessions, and CLI help at skill load time
- **Allowed tools**: Pre-approved `Bash(mcpc *)`, `Bash(jq *)`, `Read`, `Grep`, `Glob` for frictionless workflow
- **Progressive disclosure**: SKILL.md stays under 500 lines; use-case details load on demand
- **Workflow checklist**: 7-step Find → Understand → Validate → Run → Verify process

## License

[Apache 2.0](LICENSE) — same as [Crawlee](https://github.com/apify/crawlee).
