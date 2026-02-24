# Skill Checker

**Test how well your SKILL.md holds up against real user prompts — before users find the gaps for you.**

Skill Checker is a CLI + Web tool that sends [Claude Code](https://claude.ai/claude-code) skills (SKILL.md files) through simulated user scenarios and produces detailed quality reports. It catches missing guidance, edge cases, and platform-specific pitfalls across 37 checks in 5 categories.

Built primarily to test [Apify](https://apify.com) agent skills — including the **apify-mcpc** plugin — but the framework works for any SKILL.md that follows the Claude Code skill format.

## Table of contents

- [How it works](#how-it-works)
- [The apify-mcpc plugin](#the-apify-mcpc-plugin)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [CLI usage](#cli-usage)
- [Web UI](#web-ui)
- [What gets tested (13 skills)](#what-gets-tested-13-skills)
- [Project structure](#project-structure)
- [Configuration](#configuration)
- [Makefile targets](#makefile-targets)
- [Tech stack](#tech-stack)
- [Troubleshooting](#troubleshooting)
- [Related documentation](#related-documentation)
- [License](#license)

## How it works

```
SKILL.md  +  test scenario (YAML)
               |
               v
         claude -p  (sends skill + prompt to Claude)
               |
               v
       Markdown + JSON report
       with scored complexities
```

Each scenario pairs a SKILL.md file with a prompt that simulates a real user request. The tool sends both to Claude via `claude -p`, then the model identifies **complexities** — gaps, ambiguities, and potential failures — scored by severity (LOW → CRITICAL) across 5 categories:

| Category | What it checks | Method |
|---|---|---|
| **WF** — Workflow | Completeness, feedback loops, scope detection | Claude audit |
| **DK** — Domain Knowledge | Actor selection, edge cases, realistic expectations | Claude audit |
| **BP** — Best Practices | Token budget, naming, progressive disclosure | Static linter (free) |
| **APF** — Apify Platform | Schema drift, tool availability, input gotchas | Claude audit |
| **SEC** — Security | Auth patterns, credential exposure | Claude audit |

## The apify-mcpc plugin

The repo includes a **Claude Code plugin** ([`plugins/apify-mcpc/`](plugins/apify-mcpc/README.md)) that gives Claude the ability to find, evaluate, and run [Apify Actors](https://apify.com/store) through the [mcpc CLI](https://www.npmjs.com/package/@apify/mcpc).

**What it does:**

- Searches Apify Store for the right Actor for any scraping/automation task
- Compares Actors by stats, ratings, maintenance status, and pricing
- Reads input schemas to build correct Actor inputs
- Runs Actors with mandatory user confirmation gates (no surprise executions)
- Includes 9 domain-specific use-case guides (audience analysis, lead generation, brand monitoring, ...)

**The 7-step skill workflow:**

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

**Available mcpc tools:**

| Session | Tool | Purpose |
|---|---|---|
| `@apify` | `search-actors` | Search Apify Store by keywords |
| `@apify` | `fetch-actor-details` | Get README, input schema, stats, pricing |
| `@apify` | `call-actor` | Run an Actor (sync or async) |
| `@apify` | `get-actor-output` | Fetch dataset results with field selection |
| `@apify` | `get-actor-run` | Check run status and stats |
| `@apify` | `apify-slash-rag-web-browser` | Quick web search / URL fetch |
| `@apify-docs` | `search-apify-docs` | Search Apify/Crawlee documentation |
| `@apify-docs` | `fetch-apify-docs` | Fetch a specific documentation page |

**Connection modes:**
- **Full mode** (`@apify`) — requires OAuth (`mcpc mcp.apify.com login`), provides all tools including Actor execution
- **Docs-only mode** (`@apify-docs`) — no authentication needed, only documentation search and fetch

**User-Agent tracking:** All mcpc calls include a custom `User-Agent` header (`apify-agent-skills/apify-mcpc-<version>/<action>`) for Apify usage analytics, mirroring the pattern used by other Apify agent skills.

See the [plugin README](plugins/apify-mcpc/README.md) for installation, full structure, and more details.

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.13+ | `python3.13 --version` |
| Node.js | 20+ | `node --version` |
| Claude CLI | latest | `claude --version` |

Claude CLI is part of [Claude Code](https://claude.ai/claude-code). The tool uses `claude -p` (pipe mode) to send prompts to models.

## Quick start

```bash
git clone <repo-url> && cd skill-checker/main
make setup                          # venv + pip + npm + clone skills
make test                           # pytest + dry-run + lint smoke test
python3 sim.py -s dc-1 -m haiku    # run one scenario (cheapest model)
```

> **Note:** Run `sim.py` from a regular terminal, **not** from within a Claude Code session — `claude -p` nesting doesn't work.

## CLI usage

```bash
python3 sim.py [OPTIONS]
```

| Flag | Short | What it does |
|---|---|---|
| `--list` | | List all available scenarios |
| `--dry-run` | | Preview what would run + cost estimate |
| `--scenario ID` | `-s` | Run a specific scenario by ID |
| `--model NAME` | `-m` | Model to use (repeatable for multiple) |
| `--skill NAME` | | Filter scenarios by target skill |
| `--concurrency N` | `-c` | Max parallel calls (default: 3) |
| `--scored` | | Domain-based heatmap mode |
| `--domain NAME` | `-d` | Filter scored mode by domain |
| `--output PATH` | `-o` | Custom output path |

**Common workflows:**

```bash
# Explore what's available
python3 sim.py --list
python3 sim.py --dry-run

# Run a single scenario quickly
python3 sim.py -s dc-1 -m haiku

# Run all scenarios across two models
python3 sim.py -m sonnet -m opus

# Full run with higher concurrency
python3 sim.py -c 5

# Scored heatmap: each domain × 3 skills
python3 sim.py --scored

# Scored heatmap for one domain only
python3 sim.py --scored -d brand-monitoring
```

### Scored mode

In scored mode (`--scored`), each domain scenario automatically runs against 3 skills: the domain specialist + `apify-mcpc` + `apify-ultimate-scraper`. This produces a heatmap showing how different skills handle the same real-world tasks.

## Web UI

A React dashboard for browsing scenarios, viewing reports, and exploring heatmap results.

```bash
make dev    # backend on :8420 + frontend on :5173
```

**Pages:**

- **Dashboard** — overview of skills, scenarios, and recent runs
- **Scenarios** — browse and edit scenario YAML files with CodeMirror
- **Reports** — view Markdown/JSON reports with category filtering
- **Heatmap** — scored analysis grid (domain x skill), multi-model comparison

For production: `make build` compiles the frontend into `web/dist/`, served by the FastAPI backend.

## What gets tested (13 skills)

| Category | Skills | Source |
|---|---|---|
| Dispatcher (9) | audience-analysis, brand-monitoring, competitor-intelligence, content-analytics, influencer-discovery, lead-generation, market-research, trend-analysis, ultimate-scraper | [apify/agent-skills](https://github.com/apify/agent-skills) |
| Dispatcher outlier (1) | ecommerce | [apify/agent-skills](https://github.com/apify/agent-skills) |
| Dev (2) | actor-development, actorization | [apify/agent-skills](https://github.com/apify/agent-skills) |
| MCPC plugin (1) | **apify-mcpc** | `plugins/apify-mcpc/` (this repo) |

All skills are registered in `skills_manifest.yaml`. Dispatcher skills are cloned from GitHub by `make setup`; the mcpc plugin lives locally.

## Project structure

```
skill-checker/main/
  sim.py                    # CLI entry point (async orchestrator)
  sim_core.py               # Core logic: taxonomy, loaders, execution, reporting
  bp_linter.py              # Static best-practices linter (no API calls)
  skills_manifest.yaml      # Skill registry (name → path + category)
  requirements.txt          # Python deps (FastAPI, PyYAML, uvicorn, ...)
  Makefile                  # Setup, dev, test, build, run targets

  scenarios/                # Test scenarios (YAML)
    wf_scenarios.yaml       #   Workflow quality (5 scenarios)
    dk_scenarios.yaml       #   Domain knowledge (6 scenarios)
    apf_scenarios.yaml      #   Apify platform (10 scenarios)
    sec_scenarios.yaml      #   Security (2 scenarios)
    brand-reputation-monitoring.yaml  # Domain-based (scored mode)
    ...                     #   + 12 more domain files

  server/                   # FastAPI backend
    main.py                 #   App setup, CORS, SPA fallback
    routers/                #   API endpoints (scenarios, reports, heatmap, ...)
    services/               #   Business logic (runner, yaml editor)

  web/                      # React 19 + Vite + TypeScript frontend
    src/pages/              #   Dashboard, Scenarios, Reports, Heatmap
    src/components/         #   HeatmapTable, YamlEditor, MarkdownViewer, ...
    src/api/                #   Typed API client
    src/hooks/              #   React hooks

  plugins/
    apify-mcpc/             # Claude Code plugin (skill + use-case guides)
      .claude-plugin/       #   plugin.json manifest
      skills/apify-mcpc/    #   SKILL.md + 9 use-case .md files + scripts

  skills/                   # Cloned from apify/agent-skills (gitignored)
  reports/                  # Generated reports (gitignored)
```

## Configuration

### Ports

Copy `.env.example` to `.env` and adjust if needed:

```ini
BACKEND_PORT=8420
FRONTEND_PORT=5173
```

Both Makefile, Vite config, and FastAPI read from `.env`. CORS is auto-configured for the frontend port.

### Adding a new skill

1. Add the SKILL.md path to `skills_manifest.yaml`:
   ```yaml
   my-new-skill:
     path: path/to/SKILL.md
     category: dispatcher   # or: dev, mcpc-plugin, dispatcher-outlier
   ```
2. Create scenario(s) in `scenarios/` referencing `target_skill: my-new-skill`
3. Verify: `python3 sim.py --list`

### Updating upstream skills

```bash
make update-skills    # git pull in skills/
```

## Makefile targets

| Target | What it does |
|---|---|
| `make help` | Show all targets |
| `make setup` | Create venv, install Python + Node deps, clone skills |
| `make test` | pytest + dry-run + ESLint |
| `make dev` | Start backend + frontend dev servers |
| `make build` | Build frontend for production |
| `make lint` | Run ESLint |
| `make run ARGS="..."` | Run sim.py with args (e.g. `make run ARGS="-s dc-1"`) |
| `make update-skills` | Pull latest from apify/agent-skills |
| `make worktree BRANCH=x` | Create a git worktree for parallel work |

## Tech stack

- **Backend:** Python 3.13, FastAPI, Uvicorn
- **Frontend:** React 19, TypeScript 5.9, Vite 7, styled-components, [@apify/ui-library](https://www.npmjs.com/package/@apify/ui-library)
- **Testing:** pytest (Python), ESLint (TypeScript)
- **AI:** Claude CLI (`claude -p` pipe mode) — not the API directly

## Troubleshooting

### `claude: command not found`

Install [Claude Code](https://claude.ai/claude-code), then verify:

```bash
which claude && claude --version
```

### Path errors in skills_manifest.yaml

All paths must resolve to existing files. If `skills/` is missing, run `make setup`. Quick check:

```bash
python3 sim.py --dry-run
```

### venv issues

The Makefile calls `.venv/bin/python` directly — no manual activation needed. For manual commands:

```bash
source .venv/bin/activate
python sim.py --list
```

### Port conflicts

Backend defaults to **8420**, frontend to **5173**. Change in `.env` or:

```bash
# Backend
uvicorn server.main:app --port 9000

# Frontend (Vite auto-increments if port is busy)
cd web && npx vite --port 3000
```

## Related documentation

| Document | Description |
|---|---|
| [plugins/apify-mcpc/README.md](plugins/apify-mcpc/README.md) | apify-mcpc plugin — installation, workflow, mcpc tools, connection modes |
| [web/README.md](web/README.md) | React frontend — Vite setup, ESLint configuration |
| [skills/README.md](skills/README.md) | Upstream Apify agent skills (cloned by `make setup`) — skill list, installation for other AI tools |

## License

The apify-mcpc plugin is licensed under [Apache 2.0](plugins/apify-mcpc/LICENSE).
