"""Scenarios router — CRUD + raw YAML edit."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sim_core import (
    load_scenarios,
    SCENARIOS_DIR,
    DOMAIN_SKILL_MAP,
    CATEGORY_GROUPS,
)
from server.services.yaml_editor import (
    save_scenario_yaml,
    create_scenario_yaml,
    delete_scenario_yaml,
    YamlValidationError,
)

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


class YamlUpdateRequest(BaseModel):
    content: str


class YamlCreateRequest(BaseModel):
    filename: str
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
            "category": s.category,
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


@router.post("/file")
def create_file(body: YamlCreateRequest):
    """Create a new scenario YAML file."""
    try:
        create_scenario_yaml(body.filename, body.content)
    except FileExistsError:
        raise HTTPException(409, f"File '{body.filename}' already exists")
    except YamlValidationError as e:
        raise HTTPException(422, detail={"errors": e.errors})
    return {"status": "ok", "source_file": body.filename}


@router.delete("/file/{source_file}")
def delete_file(source_file: str):
    """Delete a scenario YAML file (creates .bak backup first)."""
    try:
        delete_scenario_yaml(source_file)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    return {"status": "ok"}


@router.get("/templates")
def get_templates():
    """Return YAML templates for both scenario formats."""
    domain_template = (
        "domain: my-domain\n"
        "target_skill: apify-my-skill\n"
        "\n"
        "scenarios:\n"
        "  - id: new-1\n"
        '    name: "New scenario"\n'
        '    prompt: "Describe the task here"\n'
    )
    category_template = (
        "category: WF\n"
        "default_models: [sonnet]\n"
        "\n"
        "scenarios:\n"
        "  - id: new-1\n"
        '    name: "New scenario"\n'
        '    target_skill: ""\n'
        '    prompt: "Describe the task here"\n'
    )
    return {
        "domain": domain_template,
        "category": category_template,
        "domains": sorted(DOMAIN_SKILL_MAP.keys()),
        "categories": sorted(CATEGORY_GROUPS.keys()),
    }


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
                "category": s.category,
            }
    raise HTTPException(404, f"Scenario '{scenario_id}' not found")
