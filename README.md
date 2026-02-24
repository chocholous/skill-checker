# Skill Checker

Test how well your SKILL.md holds up against real user prompts — before users find the gaps for you.

Sends skills + simulated scenarios to Claude via `claude -p`, identifies **complexities** (gaps, ambiguities, failures) scored by severity across 5 categories, and produces Markdown + JSON reports.

## How it works

```
SKILL.md  +  scenario (YAML)
               │
               ▼
         claude -p  (skill + prompt → model)
               │
               ▼
       Report: scored complexities
       (Markdown + JSON)
```

| Category | Checks | Method |
|---|---|---|
| **WF** — Workflow | Completeness, feedback loops, scope detection | Claude audit |
| **DK** — Domain Knowledge | Actor selection, edge cases, expectations | Claude audit |
| **BP** — Best Practices | Token budget, naming, progressive disclosure | Static linter |
| **APF** — Apify Platform | Schema drift, tool availability, input gotchas | Claude audit |
| **SEC** — Security | Auth patterns, credential exposure | Claude audit |

## Quick start

```bash
git clone <repo-url> && cd skill-checker/main
make setup                          # venv + pip + npm + clone skills
make test                           # pytest + dry-run + lint
python3 sim.py -s dc-1 -m haiku    # run one scenario (cheapest)
```

> Run `sim.py` from a regular terminal, **not** from a Claude Code session (`claude -p` nesting doesn't work).

**Prerequisites:** Python 3.13+, Node.js 20+, [Claude CLI](https://claude.ai/claude-code) (`claude -p`).

## CLI usage

```bash
python3 sim.py [OPTIONS]
```

| Flag | Short | Description |
|---|---|---|
| `--list` | | List all scenarios |
| `--dry-run` | | Preview runs + cost estimate |
| `--scenario ID` | `-s` | Run specific scenario |
| `--model NAME` | `-m` | Model override (repeatable) |
| `--skill NAME` | | Filter by target skill |
| `--concurrency N` | `-c` | Max parallel calls (default: 3) |
| `--scored` | | Domain-based heatmap mode |
| `--domain NAME` | `-d` | Filter scored mode by domain |
| `--output PATH` | `-o` | Custom output path |

```bash
# Explore
python3 sim.py --list
python3 sim.py --dry-run

# Single scenario
python3 sim.py -s dc-1 -m haiku

# Multi-model full run
python3 sim.py -m sonnet -m opus

# Scored heatmap: each domain × 3 skills
python3 sim.py --scored
python3 sim.py --scored -d brand-monitoring
```

### Scored mode

Each domain scenario runs against 3 skills: **specialist + apify-mcpc + ultimate-scraper**. Produces a heatmap comparing how different skills handle the same tasks. Dev domains run only against their specialist.

### Model strategy

Without `--model`, each category uses its default models. With `--model`, it overrides all categories. BP linter always runs statically (no API calls).

| Scenarios | Total |
|---|---|
| 23 category scenarios (4 YAML files) + 7 BP linter checks per skill | **52 checks** (~$2-7 full run) |

## Web UI

```bash
make dev    # backend :8420 + frontend :5173
```

- **Dashboard** — skills, scenarios, recent runs overview
- **Scenarios** — browse/edit YAML with CodeMirror
- **Reports** — Markdown/JSON with category filtering
- **Heatmap** — scored grid (domain × skill), multi-model comparison

Production: `make build` → `web/dist/` served by FastAPI.

## Tested skills (13)

| Category | Count | Skills |
|---|---|---|
| Dispatcher | 9 | audience-analysis, brand-monitoring, competitor-intelligence, content-analytics, influencer-discovery, lead-generation, market-research, trend-analysis, ultimate-scraper |
| Dispatcher outlier | 1 | ecommerce (inline schema, no mcpc) |
| Dev | 2 | actor-development, actorization |
| MCPC plugin | 1 | [apify-mcpc](plugins/apify-mcpc/README.md) |

Skills registered in `skills_manifest.yaml`. Dispatcher skills cloned from [apify/agent-skills](https://github.com/apify/agent-skills) via `make setup`.

## apify-mcpc plugin

Claude Code plugin that gives Claude access to Apify Store — search, evaluate, and run Actors through [mcpc CLI](https://www.npmjs.com/package/@apify/mcpc). Includes a 7-step skill workflow with mandatory user confirmation gates and 9 domain-specific use-case guides.

See **[plugins/apify-mcpc/README.md](plugins/apify-mcpc/README.md)** for full details (tools, connection modes, installation).

<details>
<summary><strong>5-category taxonomy (37 checks)</strong></summary>

### WF — Workflow Quality (6)

| ID | Severity | Check |
|---|---|---|
| WF-1 | HIGH | Missing workflow |
| WF-2 | MED | No feedback loop |
| WF-3 | HIGH | Wrong degrees of freedom |
| WF-4 | MED | Missing examples |
| WF-5 | MED | No scope detection |
| WF-6 | MED | Linear-only workflow |

### DK — Domain Knowledge (8)

| ID | Severity | Check |
|---|---|---|
| DK-1 | HIGH | Actor selection ambiguity |
| DK-2 | MED | Output variability |
| DK-3 | MED | Unrealistic expectations |
| DK-4 | MED | Time-sensitive content |
| DK-5 | MED | No scheduling pattern |
| DK-6 | HIGH | Missing domain caveats |
| DK-7 | HIGH | Input correctness validation |
| DK-8 | MED | Data completeness awareness |

### BP — Best Practices (8) — static linter

| ID | Severity | Check |
|---|---|---|
| BP-1 | HIGH | Token budget exceeded (>500 lines) |
| BP-2 | MED | Poor description |
| BP-3 | LOW | Deep reference nesting |
| BP-4 | LOW | Inconsistent terminology |
| BP-5 | MED | No progressive disclosure |
| BP-6 | LOW | Magic constants |
| BP-7 | MED | Duplication between SKILL.md and references |
| BP-8 | MED | Missing "when to read" guidance |

### APF — Apify Platform Awareness (13)

| ID | Severity | Check |
|---|---|---|
| APF-1 | CRIT | Path resolution |
| APF-2 | HIGH | Schema drift |
| APF-3 | HIGH | Expected tool not available |
| APF-4 | HIGH | Input schema gotchas |
| APF-5 | MED | No resource budgeting |
| APF-6 | MED | Run observability |
| APF-7 | MED | Output storage confusion |
| APF-8 | MED | Store search mismatch |
| APF-9 | LOW | Actor metadata ignorance |
| APF-10 | MED | Proxy unawareness |
| APF-11 | MED | Multi-actor orchestration gap |
| APF-12 | MED | Memory and scaling limits |
| APF-13 | LOW | Parallelization patterns |

### SEC — Security (2)

| ID | Severity | Check |
|---|---|---|
| SEC-1 | HIGH | Auth anti-patterns |
| SEC-4 | MED | Credential exposure |

</details>

## Project structure

```
sim.py                    # CLI entry point (async orchestrator)
sim_core.py               # Core: taxonomy, loaders, execution, reporting
bp_linter.py              # Static best-practices linter (no API)
skills_manifest.yaml      # Skill registry (name → path + category)
Makefile                  # Setup, dev, test, build targets

scenarios/                # Test scenarios (YAML)
  wf_scenarios.yaml       #   Workflow (5)
  dk_scenarios.yaml       #   Domain knowledge (6)
  apf_scenarios.yaml      #   Apify platform (10)
  sec_scenarios.yaml      #   Security (2)
  *.yaml                  #   + domain scenarios (scored mode)

server/                   # FastAPI backend
  main.py                 #   App, CORS, SPA fallback
  routers/                #   API endpoints
  services/               #   Business logic

web/                      # React 19 + Vite + TypeScript
  src/pages/              #   Dashboard, Scenarios, Reports, Heatmap
  src/components/         #   HeatmapTable, YamlEditor, MarkdownViewer
  src/api/                #   Typed API client

plugins/apify-mcpc/       # Claude Code plugin
  skills/apify-mcpc/      #   SKILL.md + 9 use-case guides

skills/                   # Cloned apify/agent-skills (gitignored)
reports/                  # Generated output (gitignored)
```

## Configuration

Copy `.env.example` → `.env`:

```ini
BACKEND_PORT=8420
FRONTEND_PORT=5173
```

Makefile, Vite config, and FastAPI all read from `.env`. CORS auto-configured for the frontend port.

### Adding a new skill

1. Add to `skills_manifest.yaml`:
   ```yaml
   my-skill:
     path: path/to/SKILL.md
     category: dispatcher
   ```
2. Create scenario(s) in `scenarios/` with `target_skill: my-skill`
3. Verify: `python3 sim.py --list`

### Updating upstream skills

```bash
make update-skills    # git pull in skills/
```

## Makefile targets

| Target | Description |
|---|---|
| `make setup` | Create venv, install Python + Node deps, clone skills |
| `make test` | pytest + dry-run + ESLint |
| `make dev` | Start backend + frontend dev servers |
| `make build` | Build frontend for production |
| `make lint` | Run ESLint |
| `make run ARGS="..."` | Run sim.py with args |
| `make update-skills` | Pull latest agent-skills |
| `make worktree BRANCH=x` | Create git worktree |

## Tech stack

**Backend:** Python 3.13, FastAPI, Uvicorn | **Frontend:** React 19, TypeScript 5.9, Vite 7, styled-components, [@apify/ui-library](https://www.npmjs.com/package/@apify/ui-library) | **Testing:** pytest, ESLint | **AI:** Claude CLI (`claude -p`)

## Troubleshooting

**`claude: command not found`** — Install [Claude Code](https://claude.ai/claude-code), verify with `which claude`.

**Path errors in skills_manifest.yaml** — All paths must resolve. Run `make setup` if `skills/` is missing. Check with `python3 sim.py --dry-run`.

**venv issues** — Makefile uses `.venv/bin/python` directly. For manual: `source .venv/bin/activate`.

**Port conflicts** — Change in `.env`, or run manually: `uvicorn server.main:app --port 9000`.

## Related docs

- [plugins/apify-mcpc/README.md](plugins/apify-mcpc/README.md) — mcpc plugin details
- [web/README.md](web/README.md) — frontend setup
- [skills/README.md](skills/README.md) — upstream Apify agent skills

## License

The apify-mcpc plugin is licensed under [Apache 2.0](plugins/apify-mcpc/LICENSE).
