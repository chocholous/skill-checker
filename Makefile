.PHONY: setup test build dev-backend dev-frontend lint

# Default target — setup everything
setup:
	python3.13 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	cd web && npm install

# Run sim.py dry-run + lint as a smoke test
test:
	.venv/bin/python sim.py --dry-run
	cd web && npm run lint

# Build frontend for production
build:
	cd web && npm run build

dev-backend:
	.venv/bin/uvicorn server.main:app --reload --host 127.0.0.1 --port 8420

dev-frontend:
	cd web && npm run dev

lint:
	cd web && npm run lint
