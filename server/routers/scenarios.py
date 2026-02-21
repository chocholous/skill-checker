"""Scenarios router — CRUD + raw YAML edit."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sim_core import load_scenarios, ALL_CATEGORIES, SCENARIOS_DIR
from server.services.yaml_editor import save_scenario_yaml, YamlValidationError

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


class YamlUpdateRequest(BaseModel):
    content: str


@router.get("")
def list_scenarios():
    """Return all scenarios grouped by source file."""
    scenarios = load_scenarios()
    return [
        {
            "id": s.id,
            "name": s.name,
            "prompt": s.prompt,
            "target_skill": s.target_skill,
            "source_file": s.source_file,
            "expected_complexities": [
                {
                    "id": c,
                    "type": "GEN" if c.startswith("GEN-") else "APF",
                    "severity": ALL_CATEGORIES[c]["severity"] if c in ALL_CATEGORIES else None,
                    "name": ALL_CATEGORIES[c]["name"] if c in ALL_CATEGORIES else None,
                    "description": ALL_CATEGORIES[c]["description"] if c in ALL_CATEGORIES else None,
                }
                for c in s.expected_complexities
            ],
        }
        for s in scenarios
    ]


@router.get("/file/{source_file}/raw")
def get_raw_yaml(source_file: str):
    """Return raw YAML content for editing."""
    path = SCENARIOS_DIR / source_file
    if not path.exists():
        raise HTTPException(404, f"File '{source_file}' not found")
    return {"source_file": source_file, "content": path.read_text()}


@router.put("/file/{source_file}")
def update_yaml(source_file: str, body: YamlUpdateRequest):
    """Validate and save edited YAML."""
    try:
        save_scenario_yaml(source_file, body.content)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except YamlValidationError as e:
        raise HTTPException(422, detail={"errors": e.errors})
    return {"status": "ok", "source_file": source_file}


@router.get("/{scenario_id}")
def get_scenario(scenario_id: str):
    """Return single scenario detail."""
    scenarios = load_scenarios()
    for s in scenarios:
        if s.id == scenario_id:
            return {
                "id": s.id,
                "name": s.name,
                "prompt": s.prompt,
                "target_skill": s.target_skill,
                "source_file": s.source_file,
                "expected_complexities": [
                    {
                        "id": c,
                        "type": "GEN" if c.startswith("GEN-") else "APF",
                        "severity": ALL_CATEGORIES[c]["severity"] if c in ALL_CATEGORIES else None,
                        "name": ALL_CATEGORIES[c]["name"] if c in ALL_CATEGORIES else None,
                        "description": ALL_CATEGORIES[c]["description"] if c in ALL_CATEGORIES else None,
                    }
                    for c in s.expected_complexities
                ],
            }
    raise HTTPException(404, f"Scenario '{scenario_id}' not found")
