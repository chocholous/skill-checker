"""Skills router — manifest + SKILL.md content."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from sim_core import load_manifest

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("")
def get_skills():
    """Return manifest with exists check for each skill path."""
    manifest = load_manifest()
    return {
        name: {
            **info,
            "name": name,
            "exists": Path(info["path"]).exists(),
        }
        for name, info in manifest.items()
    }


@router.get("/{name}/content")
def get_skill_content(name: str):
    """Return SKILL.md content for a skill."""
    manifest = load_manifest()
    skill_info = manifest.get(name)
    if not skill_info:
        raise HTTPException(404, f"Skill '{name}' not found in manifest")

    path = Path(skill_info["path"])
    if not path.exists():
        raise HTTPException(404, f"SKILL.md not found at {path}")

    return {
        "name": name,
        "path": str(path),
        "content": path.read_text(),
        "lines": len(path.read_text().splitlines()),
    }
