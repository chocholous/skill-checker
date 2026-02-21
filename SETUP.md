# Setup Guide

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.13+ | `python3.13 --version` |
| Node.js | 20+ | `node --version` |
| Claude CLI | latest | `claude --version` |

Claude CLI is part of [Claude Code](https://claude.ai/claude-code). The tool uses `claude -p` to send prompts to models.

## Install

```bash
make setup
```

This runs:
1. `python3.13 -m venv .venv` — creates a Python virtual environment
2. `.venv/bin/pip install -r requirements.txt` — installs Python deps (FastAPI, PyYAML, uvicorn, ...)
3. `cd web && npm install` — installs frontend deps (React, Vite, ...)
4. `git clone apify/agent-skills skills/` — clones SKILL.md files from [upstream](https://github.com/apify/agent-skills)

To update skills to latest version:

```bash
make update-skills
```

## Configure skills_manifest.yaml

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

## Verify

```bash
make test
```

This runs:
- `sim.py --dry-run` — validates scenarios load and skills resolve
- `npm run lint` — checks frontend code quality

## Run CLI

Run from terminal, **not** from within a Claude Code session (`claude -p` nesting doesn't work).

```bash
python3 sim.py --list              # List all scenarios
python3 sim.py --dry-run           # Preview what would run + cost estimate
python3 sim.py -s dc-1 -m haiku   # Single scenario, single model
python3 sim.py -m sonnet -m opus   # Two models, all scenarios
python3 sim.py                     # Full run (54 calls, ~$3-8)
python3 sim.py -c 5                # Increase concurrency (default 3)
```

Reports are saved to `reports/` as Markdown + JSON.

## Run Web UI

### Development

```bash
make dev
```

Starts both servers in parallel:
- **Backend**: FastAPI on `http://127.0.0.1:8420` (auto-reload)
- **Frontend**: Vite on `http://localhost:5173` (HMR)

### Production build

```bash
make build
```

Builds the frontend into `web/dist/`. Serve with any static file server or configure the FastAPI backend to serve it.

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

If a skill path is invalid, the dry-run will report the error.

### venv activation issues

The Makefile uses `.venv/bin/python` directly, so manual activation is not required. If you want to run commands manually:

```bash
source .venv/bin/activate
python sim.py --list
```

### Port conflicts

- Backend default: **8420**. Change via: `uvicorn server.main:app --port <PORT>`
- Frontend default: **5173**. Vite auto-increments if the port is busy.

If port 8420 is already in use:

```bash
lsof -i :8420    # find the process
kill <PID>        # free the port
```
