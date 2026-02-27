# apify-mcpc plugin

Claude Code plugin for finding, evaluating, and running [Apify Actors](https://apify.com/store) using the [mcpc CLI](https://www.npmjs.com/package/@apify/mcpc).

## Table of contents

- [What it does](#what-it-does)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Skills](#skills)
- [Use cases](#use-cases)
- [Skill workflow](#skill-workflow)
- [Available mcpc tools](#available-mcpc-tools)
- [Connection modes](#connection-modes)
- [Cost tracking](#cost-tracking)
- [User-Agent tracking](#user-agent-tracking)
- [Plugin structure](#plugin-structure)
- [Features](#features)
- [Testing](#testing)
- [Related](#related)
- [License](#license)

## What it does

- Searches Apify Store for the right Actor for any scraping/automation task
- Compares Actors by stats, ratings, and maintenance status
- Reads input schemas to build correct Actor inputs
- Runs Actors and retrieves structured results (sync or async with resume)
- Tracks run costs automatically via PostToolUse hook → `~/.apify-costs.log`
- Covers 8 marketing intelligence use cases with domain-specific guidance, plus multi-actor workflow patterns

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

## Skills

This plugin provides two slash commands:

| Command | Description |
|---|---|
| `/apify-mcpc` | Main skill — find, evaluate, and run Apify Actors (full 7-step workflow) |
| `/apify-status` | Show active mcpc sessions and run cost history from `~/.apify-costs.log` |

## Use cases

The plugin includes 8 use-case files with suggested Actors, search keywords, and gotchas, plus a multi-actor workflow patterns reference:

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
| Multi-Actor Workflows | Chaining Actors, handle discovery via SERP, enrichment |

Actor tables in use-case files are **suggestions, not closed lists**. The agent always searches Apify Store for the latest options.

## Skill workflow

The skill enforces a 7-step workflow with mandatory gates to prevent wasted money on incorrect Actor runs:

1. **Search** — Find candidate Actors (always at least 2 searches: broad then narrow)
2. **Fetch details** — Read README, input schema, stats, ratings
3. **Build input** — Cross-reference schema with README for correct values
4. **Validate** — Challenge assumptions about identifiers, verify against target service
5. **Run** — Execute the Actor (test run with limit=1 first when uncertain)
6. **Verify** — Sanity-check results before presenting (zero results = wrong input, not "no data")
7. **Get results** — Fetch full dataset with field selection and pagination

Two mandatory gates stop the agent before running:
- **After Step 2**: Show user the Actor choice + planned input, wait for confirmation
- **After Step 4**: If any input value is guessed, tell user before running

The agent determines scope first — **docs-only** (Crawlee/platform questions), **find-only** (Actor comparison without running), or **full pipeline** (data extraction) — to avoid unnecessary Actor searches or runs.

## Available mcpc tools

| Session | Tool | Purpose |
|---|---|---|
| `@apify` | `search-actors` | Search Apify Store by keywords |
| `@apify` | `fetch-actor-details` | Get README, input schema, stats, pricing |
| `@apify` | `call-actor` | Run an Actor (sync or async) |
| `@apify` | `get-actor-output` | Fetch dataset results with field selection |
| `@apify` | `get-actor-run` | Check run status and stats |
| `@apify` | `apify-slash-rag-web-browser` | Quick web search / URL fetch without Actor workflow |
| `@apify-docs` | `search-apify-docs` | Search Apify/Crawlee documentation |
| `@apify-docs` | `fetch-apify-docs` | Fetch a specific documentation page |

## Connection modes

- **Full mode** (`@apify`) — requires OAuth (`mcpc mcp.apify.com login`), provides all tools including Actor execution
- **Docs-only mode** (`@apify-docs`) — no authentication needed, only documentation search and fetch

The prerequisite check script (`check_apify.sh`) verifies both sessions are active before the skill starts.

## Cost tracking

A PostToolUse hook fires after every `call-actor --json` run and appends to `~/.apify-costs.log`:

```
2026-02-27T21:00:00Z    actor=apify/instagram-post-scraper    usd=0.0042
```

Override the log path with `APIFY_COST_LOG=/path/to/file`. View the log and session totals with `/apify-status`.

## User-Agent tracking

All mcpc calls include a `-H "User-Agent: apify-agent-skills/apify-mcpc-<version>/<action>"` header for Apify usage analytics, mirroring the `User-Agent` pattern used by other Apify agent skills in their `run_actor.js` scripts. The version is read from `plugin.json` at runtime.

## Plugin structure

```
plugins/apify-mcpc/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (hooks, version, allowed-tools)
├── scripts/
│   └── track-cost.sh            # PostToolUse hook — logs call-actor costs
├── skills/
│   ├── apify-mcpc/
│   │   ├── SKILL.md             # Main skill (7-step workflow, mcpc reference)
│   │   ├── scripts/
│   │   │   └── check_apify.sh   # Prerequisite check (mcpc version + sessions)
│   │   └── references/
│   │       ├── issue-reporting.md
│   │       └── use-cases/
│   │           ├── audience-analysis.md
│   │           ├── brand-monitoring.md
│   │           ├── competitor-intelligence.md
│   │           ├── content-analytics.md
│   │           ├── influencer-discovery.md
│   │           ├── lead-generation.md
│   │           ├── market-research.md
│   │           ├── trend-analysis.md
│   │           └── multi-actor-workflows.md
│   └── apify-status/
│       └── SKILL.md             # /apify-status command (sessions + cost log)
├── tests/
│   ├── conftest.py              # Shared fixtures, spy mcpc, run_claude helper
│   ├── test_hook.py             # Unit tests for track-cost.sh (5)
│   ├── test_install.py          # Install/uninstall tests (2)
│   ├── test_integration.py      # Spy mcpc integration tests (11)
│   └── test_skills.py           # E2E skill tests via claude -p (5)
├── LICENSE                      # Apache 2.0
└── README.md
```

## Features

- **Dynamic context**: `!command` injection prefetches mcpc version, active sessions, and CLI help at skill load time
- **Allowed tools**: Pre-approved `Bash(mcpc *)`, `Bash(jq *)`, `Read`, `Grep`, `Glob` for frictionless workflow
- **Progressive disclosure**: SKILL.md stays under 500 lines; use-case details load on demand
- **Workflow checklist**: 7-step Find → Understand → Validate → Run → Verify process
- **Cost tracking**: PostToolUse hook logs every `call-actor --json` cost to `~/.apify-costs.log`
- **Async resume**: Saves `runId` immediately for long-running actors; resumes with `get-actor-run` after session reset
- **Session overview**: `/apify-status` command shows active mcpc sessions and cost totals

## Testing

```bash
# Run all 23 tests (requires plugin installed from marketplace)
CLAUDECODE= pytest plugins/apify-mcpc/tests/ -v
```

| File | Tests | What |
|---|---|---|
| `test_hook.py` | 5 | Unit tests for `track-cost.sh` (no Claude) |
| `test_install.py` | 2 | Install/uninstall from marketplace |
| `test_integration.py` | 11 | Spy mcpc — hook wiring, workflow order, async resume, reference files, data handling |
| `test_skills.py` | 5 | E2E skill tests via `claude -p` (missing mcpc, use cases, permissions, apify-status) |

Tests use a spy mcpc binary that records all calls to a log file and returns canned JSON responses — no real Apify account needed.

## Related

- [Root README](../../README.md) — Skill Checker project overview, CLI usage, Web UI, full project structure
- [Upstream skills](../../skills/README.md) — Apify agent skills tested alongside this plugin

## License

[Apache 2.0](LICENSE) — same as [Crawlee](https://github.com/apify/crawlee).
