"""Reports router — historical report browsing."""

import json

from fastapi import APIRouter, HTTPException

from sim_core import REPORTS_DIR

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def list_reports():
    """List all report files, newest first."""
    REPORTS_DIR.mkdir(exist_ok=True)
    reports = []

    for md_file in sorted(REPORTS_DIR.glob("report_*.md"), reverse=True):
        json_file = md_file.with_suffix(".json")
        meta = {}
        if json_file.exists():
            try:
                data = json.loads(json_file.read_text())
                meta = {
                    "generated": data.get("generated"),
                    "models": data.get("models"),
                    "scenario_count": data.get("scenario_count"),
                }
            except (json.JSONDecodeError, KeyError):
                pass

        reports.append({
            "filename": md_file.name,
            "json_filename": json_file.name if json_file.exists() else None,
            **meta,
        })

    return reports


@router.get("/{filename}")
def get_report(filename: str):
    """Return report content (markdown or JSON based on extension)."""
    path = REPORTS_DIR / filename
    if not path.exists():
        raise HTTPException(404, f"Report '{filename}' not found")

    if filename.endswith(".json"):
        return json.loads(path.read_text())

    return {"filename": filename, "content": path.read_text()}


@router.delete("/{filename}")
def delete_report(filename: str):
    """Delete a report (both .md and .json)."""
    md_path = REPORTS_DIR / filename
    if not md_path.exists():
        raise HTTPException(404, f"Report '{filename}' not found")

    md_path.unlink()
    json_path = md_path.with_suffix(".json")
    if json_path.exists():
        json_path.unlink()

    return {"status": "deleted", "filename": filename}
