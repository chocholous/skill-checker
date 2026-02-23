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

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.13+ | `python3.13 --version` |
| Node.js | 20+ | `node --version` |
| Claude CLI | latest | `claude --version` |

Claude CLI is part of [Claude Code](https://claude.ai/claude-code). The tool uses `claude -p` to send prompts to models.

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

Run from terminal, **not** from within a Claude Code session (`claude -p` nesting doesn't work).

## Web UI

The web interface provides:

- **Dashboard** — overview of skills, scenarios, and recent runs
- **Run Builder** — select scenarios/models and launch runs
- **Scenario Editor** — browse and edit scenario YAML files
- **Report Viewer** — view Markdown/JSON reports with filtering

### Development

```bash
make dev    # backend :8420 + frontend :5173
```

### Production build

```bash
make build
```

Builds the frontend into `web/dist/`.

## Configuration

### skills_manifest.yaml

The manifest maps skill names to paths of SKILL.md files. Skills from `apify/agent-skills` are cloned into `skills/` by `make setup` and use relative paths. Local skills (e.g. `apify-mcpc`) use paths within the project.

```yaml
skills:
  # From cloned agent-skills repo
  apify-audience-analysis:
    path: skills/skills/apify-audience-analysis/SKILL.md
    category: dispatcher

  # Local skill
  apify-mcpc:
    path: apify-mcpc-plugin/skills/apify-mcpc/SKILL.md
    category: mcpc-plugin
```

### Adding a new skill

1. If the skill is in `apify/agent-skills` — run `make update-skills`, then add an entry with the relative path
2. If the skill is local — add an entry pointing to its path within this repo
3. Create scenario(s) in `scenarios/` that reference the skill by name (`target_skill: my-skill`)
4. Verify with `python3 sim.py --list`

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

## Troubleshooting

### `claude: command not found`

Claude CLI must be installed and on your PATH. Install via [Claude Code](https://claude.ai/claude-code), then verify:

```bash
which claude
claude --version
```

### Path errors in skills_manifest.yaml

All paths must point to existing files. If `skills/` is missing, run `make setup`. Verify:

```bash
python3 sim.py --dry-run
```

### venv activation issues

The Makefile uses `.venv/bin/python` directly, so manual activation is not required. If you want to run commands manually:

```bash
source .venv/bin/activate
python sim.py --list
```

### Port conflicts

- Backend default: **8420**. Change via: `uvicorn server.main:app --port <PORT>`
- Frontend default: **5173**. Vite auto-increments if the port is busy.
