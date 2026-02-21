# Skill Checker

CLI + Web tool for testing SKILL.md quality with Claude models.

## How It Works

```
SKILL.md + test prompt
        |
        v
  claude -p audit
        |
        v
  Markdown + JSON report
  (GEN/APF complexities)
```

Each scenario pairs a **SKILL.md** file with a **test prompt** simulating a real user request. The tool sends both to Claude models via `claude -p`, then analyzes the response for **complexities** — gaps, missing guidance, and potential failures — classified into GEN (general skill quality) and APF (Apify platform pitfalls) categories.

## Quick Start

```bash
git clone <repo-url> && cd skill-checker
make setup                          # venv + pip + npm + clone skills
make test                           # dry-run + lint smoke test
python3 sim.py -s dc-1 -m haiku    # run one scenario
```

## CLI Usage

```
python3 sim.py [OPTIONS]
```

| Flag | Short | Description |
|---|---|---|
| `--list` | | List all scenarios |
| `--dry-run` | | Show what would run + cost estimate |
| `--scenario ID` | `-s` | Run specific scenario by ID |
| `--model NAME` | `-m` | Model to use (repeat for multiple) |
| `--skill NAME` | | Filter scenarios by target skill |
| `--concurrency N` | `-c` | Max parallel calls (default: 3) |
| `--output PATH` | `-o` | Custom output file path |

**Examples:**

```bash
python3 sim.py --list                # List all scenarios
python3 sim.py --dry-run             # Preview + cost estimate
python3 sim.py -s dc-1 -m haiku     # Single scenario, single model
python3 sim.py -m sonnet -m opus     # Two models, all scenarios
python3 sim.py -c 5                  # Full run, concurrency 5
```

Default models: `sonnet`, `opus`, `haiku`.

## Web UI

The web interface provides:

- **Dashboard** — overview of skills, scenarios, and recent runs
- **Run Builder** — select scenarios/models and launch runs
- **Scenario Editor** — browse and edit scenario YAML files
- **Report Viewer** — view Markdown/JSON reports with filtering

```bash
make dev    # backend :8420 + frontend :5173
```

## Project Structure

```
skill-checker/
  sim.py                  # CLI entry point
  sim_core.py             # Shared logic (loading, execution, reporting)
  skills_manifest.yaml    # Paths to SKILL.md files
  requirements.txt        # Python dependencies
  Makefile                # Setup, dev, test, build targets
  scenarios/
    dispatcher_common.yaml
    dispatcher_specific.yaml
    dev_skills.yaml
    mcpc_plugin.yaml
  skills/                 # Cloned from apify/agent-skills (gitignored)
  server/
    main.py               # FastAPI backend
    routers/              # API route handlers
    services/             # Business logic
  web/
    src/
      pages/              # React pages (dashboard, run builder, ...)
      components/         # Shared UI components
      api/                # API client
      hooks/              # React hooks
  apify-mcpc-plugin/      # Centralized mcpc workflow + skill
  reports/                # Generated reports (gitignored)
```

## Makefile Targets

| Target | Description |
|---|---|
| `make help` | Show available targets (default) |
| `make setup` | Create venv, install deps, clone skills |
| `make test` | Run dry-run + frontend lint |
| `make dev` | Start backend + frontend dev servers |
| `make build` | Build frontend for production |
| `make lint` | Run frontend linter |
| `make run` | Run sim.py (pass-through, e.g. `make run ARGS="-s dc-1"`) |
| `make update-skills` | Pull latest skills from upstream |

## Taxonomy

Scenarios test for **24 complexity categories** across two layers:

**GEN — General skill quality** (13 categories, LOW to HIGH severity)
Token budget, workflow completeness, feedback loops, degrees of freedom, dependencies, examples, error handling, and more.

**APF — Apify platform pitfalls** (11 categories, LOW to CRITICAL severity)
Path resolution, schema drift, tool availability, input validation, actor selection, resource budgeting, auth patterns, and more.

See [CLAUDE.md](CLAUDE.md) for the full taxonomy tables.

## Links

- [SETUP.md](SETUP.md) — detailed installation and configuration guide
- [CLAUDE.md](CLAUDE.md) — project architecture, taxonomy, and contributor instructions
- [apify/agent-skills](https://github.com/apify/agent-skills) — upstream SKILL.md repository
