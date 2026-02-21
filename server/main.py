"""
Skill Checker Web — FastAPI application.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.routers import scenarios, runs, reports, categories, skills

app = FastAPI(title="Skill Checker", version="1.0.0")

# CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Routers
app.include_router(scenarios.router)
app.include_router(runs.router)
app.include_router(reports.router)
app.include_router(categories.router)
app.include_router(skills.router)


# Serve built frontend (production) — must be LAST (catch-all)
DIST_DIR = Path(__file__).parent.parent / "web" / "dist"
if DIST_DIR.exists():
    # Static assets (JS, CSS, etc.)
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="static-assets")

    # SPA fallback: any non-API route → index.html
    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str):
        # Serve actual files if they exist in dist
        file_path = DIST_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for SPA routing
        return FileResponse(DIST_DIR / "index.html")
