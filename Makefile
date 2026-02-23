.DEFAULT_GOAL := help
.PHONY: help setup test build dev dev-backend dev-frontend lint run update-skills worktree worktree-remove sync-workspace

# Load port config from .env (with defaults)
-include .env
export
BACKEND_PORT ?= 8420
FRONTEND_PORT ?= 5173

help: ## Show available targets
	@printf "\n  Skill Checker — available targets:\n\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@printf "\n"

setup: ## Create venv, install deps, clone skills
	python3.13 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	cd web && npm install
	@if [ ! -d skills/.git ]; then \
		printf "Cloning apify/agent-skills into skills/...\n"; \
		git clone https://github.com/apify/agent-skills.git skills; \
	else \
		printf "skills/ already exists, skipping clone.\n"; \
	fi

update-skills: ## Pull latest agent-skills into skills/
	@if [ -d skills/.git ]; then \
		cd skills && git pull; \
	else \
		printf "skills/ not found — run 'make setup' first.\n"; exit 1; \
	fi

test: ## Run pytest + sim.py dry-run + frontend lint
	.venv/bin/python -m pytest tests/ -v
	.venv/bin/python sim.py --dry-run
	cd web && npm run lint

build: ## Build frontend for production
	cd web && npm run build

_check-venv:
	@.venv/bin/python -c "import fastapi" 2>/dev/null || \
		(printf "\033[31mError: venv is missing or broken. Run 'make setup' first.\033[0m\n" && exit 1)

_check-node:
	@test -d web/node_modules || \
		(printf "\033[31mError: node_modules missing. Run 'make setup' first.\033[0m\n" && exit 1)

dev: _check-venv _check-node ## Start backend + frontend dev servers
	@printf "Starting backend (:$(BACKEND_PORT)) and frontend (:$(FRONTEND_PORT))...\n"
	.venv/bin/uvicorn server.main:app --reload --host 127.0.0.1 --port $(BACKEND_PORT) & \
	cd web && npx vite --port $(FRONTEND_PORT) & \
	wait

dev-backend: _check-venv ## Start backend only
	.venv/bin/uvicorn server.main:app --reload --host 127.0.0.1 --port $(BACKEND_PORT)

dev-frontend: _check-node ## Start frontend only
	cd web && npx vite --port $(FRONTEND_PORT)

lint: ## Run frontend linter
	cd web && npm run lint

run: ## Run sim.py (e.g. make run ARGS="-s dc-1 -m haiku")
	.venv/bin/python sim.py $(ARGS)

sync-workspace: ## Sync VS Code multi-root workspace file
	@python3 -c "\
	import json, os, sys; \
	root = os.path.abspath('..'); \
	ws_name = os.path.basename(root) + '.code-workspace'; \
	ws_path = os.path.join(root, ws_name); \
	folders = [{'path': 'main', 'name': 'main'}]; \
	wt_dir = os.path.join(root, 'worktrees'); \
	[folders.append({'path': f'worktrees/{d}', 'name': d}) for d in sorted(os.listdir(wt_dir)) if os.path.isfile(os.path.join(wt_dir, d, '.git'))] if os.path.isdir(wt_dir) else None; \
	data = {}; \
	exec('try:\n with open(ws_path) as f: data=json.load(f)\nexcept FileNotFoundError: pass\nexcept json.JSONDecodeError as e: sys.exit(f\"Invalid JSON in {ws_path}: {e}\")'); \
	data['folders'] = folders; \
	data.setdefault('settings', {'search.exclude': {'**/.git': True, '**/.venv': True, '**/node_modules': True, '**/__pycache__': True}}); \
	open(ws_path, 'w').write(json.dumps(data, indent=2) + '\n'); \
	print(f'Synced {ws_name}: {len(folders)} folders')"

worktree: ## Create git worktree (make worktree BRANCH=<name>)
	@test -n "$(BRANCH)" || (echo "Usage: make worktree BRANCH=<name>" && exit 1)
	git worktree add ../worktrees/$(BRANCH) -b $(BRANCH)
	cd ../worktrees/$(BRANCH) && bash .worktree-setup.sh
	@$(MAKE) sync-workspace

worktree-remove: ## Remove git worktree (make worktree-remove BRANCH=<name>)
	@test -n "$(BRANCH)" || (echo "Usage: make worktree-remove BRANCH=<name>" && exit 1)
	git worktree remove ../worktrees/$(BRANCH)
	git branch -D $(BRANCH)
	@$(MAKE) sync-workspace
