.DEFAULT_GOAL := help
.PHONY: help setup test build dev dev-backend dev-frontend lint run update-skills

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

test: ## Run sim.py dry-run + frontend lint
	.venv/bin/python sim.py --dry-run
	cd web && npm run lint

build: ## Build frontend for production
	cd web && npm run build

dev: ## Start backend + frontend dev servers
	@printf "Starting backend (:8420) and frontend (:5173)...\n"
	.venv/bin/uvicorn server.main:app --reload --host 127.0.0.1 --port 8420 & \
	cd web && npm run dev & \
	wait

dev-backend: ## Start backend only
	.venv/bin/uvicorn server.main:app --reload --host 127.0.0.1 --port 8420

dev-frontend: ## Start frontend only
	cd web && npm run dev

lint: ## Run frontend linter
	cd web && npm run lint

run: ## Run sim.py (e.g. make run ARGS="-s dc-1 -m haiku")
	.venv/bin/python sim.py $(ARGS)
