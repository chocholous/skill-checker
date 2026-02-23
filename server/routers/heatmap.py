"""
Heatmap router — domain/skill health overview + scored run management.
"""

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from bp_linter import run_bp_checks
from sim_core import (
    ALL_CATEGORIES,
    BP_CATEGORIES,
    CATEGORY_GROUPS,
    DEFAULT_CONCURRENCY,
    DEV_DOMAINS,
    DOMAIN_SKILL_MAP,
    LLM_CHECK_IDS,
    load_domain_scenarios,
    load_latest_scored_report,
    load_manifest,
    read_skill,
)
from server.services.runner import run_manager, ScoredRunStatus

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])


# ---------------------------------------------------------------------------
# GET /api/heatmap/domains
# ---------------------------------------------------------------------------


@router.get("/domains")
def get_domains():
    """Return list of domain info."""
    domain_scenarios = load_domain_scenarios()
    result = []
    for domain_id, scenarios in sorted(domain_scenarios.items()):
        result.append(
            {
                "id": domain_id,
                "specialist": DOMAIN_SKILL_MAP.get(domain_id, ""),
                "scenario_count": len(scenarios),
                "is_dev": domain_id in DEV_DOMAINS,
            }
        )
    return result


# ---------------------------------------------------------------------------
# GET /api/heatmap/skills
# ---------------------------------------------------------------------------


@router.get("/skills")
def get_skills_health():
    """Return skill health overview from latest scored report."""
    latest = load_latest_scored_report()
    if latest is None:
        return []

    _metadata, runs = latest

    # Reverse map: skill_name → domain
    skill_to_domain: dict[str, str] = {}
    for domain_id, skill_name in DOMAIN_SKILL_MAP.items():
        skill_to_domain[skill_name] = domain_id

    # Aggregate stats per skill
    skill_stats: dict[str, dict] = {}
    # Track per-check failures for top_gaps
    skill_check_fails: dict[str, dict[str, int]] = {}
    for run in runs:
        skill = run.skill
        if skill not in skill_stats:
            skill_stats[skill] = {
                "pass_count": 0,
                "fail_count": 0,
                "unclear_count": 0,
                "na_count": 0,
            }
            skill_check_fails[skill] = {}
        for check in run.checks:
            if check.result == "pass":
                skill_stats[skill]["pass_count"] += 1
            elif check.result == "fail":
                skill_stats[skill]["fail_count"] += 1
                skill_check_fails[skill][check.check_id] = (
                    skill_check_fails[skill].get(check.check_id, 0) + 1
                )
            elif check.result == "unclear":
                skill_stats[skill]["unclear_count"] += 1
            else:
                skill_stats[skill]["na_count"] += 1

    result = []
    for skill, stats in sorted(skill_stats.items()):
        total = stats["pass_count"] + stats["fail_count"] + stats["unclear_count"]
        pass_pct = round(100 * stats["pass_count"] / total, 1) if total > 0 else 0.0
        domain = skill_to_domain.get(skill, "")

        # Top gaps: check IDs with most failures
        top_gaps = []
        if skill in skill_check_fails:
            sorted_fails = sorted(
                skill_check_fails[skill].items(), key=lambda x: x[1], reverse=True
            )
            for check_id, _count in sorted_fails[:5]:
                check_info = ALL_CATEGORIES.get(check_id, {})
                top_gaps.append(
                    {
                        "check_id": check_id,
                        "name": check_info.get("name", check_id),
                        "severity": check_info.get("severity", ""),
                    }
                )

        result.append(
            {
                "skill": skill,
                "domain": domain,
                "is_dev": domain in DEV_DOMAINS,
                "pass_pct": pass_pct,
                "pass_count": stats["pass_count"],
                "fail_count": stats["fail_count"],
                "unclear_count": stats["unclear_count"],
                "na_count": stats["na_count"],
                "top_gaps": top_gaps,
            }
        )
    return result


# ---------------------------------------------------------------------------
# GET /api/heatmap/domain/{domain_id}
# ---------------------------------------------------------------------------


@router.get("/domain/{domain_id}")
def get_domain_heatmap(domain_id: str):
    """Return domain heatmap matrix (Level 2 data)."""
    domain_scenarios = load_domain_scenarios()
    if domain_id not in domain_scenarios:
        raise HTTPException(404, f"Domain '{domain_id}' not found")

    scenarios = domain_scenarios[domain_id]
    specialist = DOMAIN_SKILL_MAP.get(domain_id, "")
    is_dev = domain_id in DEV_DOMAINS

    # Build check list: LLM checks only (no BP), sorted by group order
    group_order = ("WF", "DK", "APF", "SEC")
    checks = []
    for group_key in group_order:
        group = CATEGORY_GROUPS[group_key]
        for cat_id, cat in group["categories"].items():
            checks.append(
                {
                    "id": cat_id,
                    "name": cat["name"],
                    "severity": cat["severity"],
                    "group": group_key,
                }
            )

    # Load latest scored report
    latest = load_latest_scored_report()
    matrix: dict[str, dict[str, dict]] = {}

    if latest is not None:
        _metadata, runs = latest
        # Index: (scenario_id, skill) -> ScoredRun
        run_index: dict[tuple[str, str], object] = {}
        for run in runs:
            run_index[(run.scenario_id, run.skill)] = run

        for scenario in scenarios:
            scenario_matrix: dict[str, dict] = {}
            for check_info in checks:
                check_id = check_info["id"]
                cell: dict[str, dict | None] = {}

                # Specialist result
                specialist_run = run_index.get((scenario.id, specialist))
                if specialist_run is not None:
                    specialist_check = next(
                        (c for c in specialist_run.checks if c.check_id == check_id),
                        None,
                    )
                    if specialist_check:
                        cell["specialist"] = {
                            "result": specialist_check.result,
                            "evidence": specialist_check.evidence,
                            "summary": specialist_check.summary,
                        }
                    else:
                        cell["specialist"] = None
                else:
                    cell["specialist"] = None

                # MCPC result (only for non-dev domains)
                if not is_dev:
                    mcpc_run = run_index.get((scenario.id, "apify-mcpc"))
                    if mcpc_run is not None:
                        mcpc_check = next(
                            (c for c in mcpc_run.checks if c.check_id == check_id),
                            None,
                        )
                        if mcpc_check:
                            cell["mcpc"] = {
                                "result": mcpc_check.result,
                                "evidence": mcpc_check.evidence,
                                "summary": mcpc_check.summary,
                            }
                        else:
                            cell["mcpc"] = None
                    else:
                        cell["mcpc"] = None
                else:
                    cell["mcpc"] = None

                scenario_matrix[check_id] = cell
            matrix[scenario.id] = scenario_matrix

    return {
        "domain": domain_id,
        "specialist": specialist,
        "is_dev": is_dev,
        "scenarios": [{"id": s.id, "name": s.name} for s in scenarios],
        "checks": checks,
        "matrix": matrix,
    }


# ---------------------------------------------------------------------------
# GET /api/heatmap/bp
# ---------------------------------------------------------------------------


@router.get("/bp")
def get_bp_matrix():
    """Return BP static linter matrix for all skills from manifest."""
    manifest = load_manifest()
    skill_names = sorted(manifest.keys())

    # Build check metadata list
    checks = [
        {
            "id": check_id,
            "name": info["name"],
            "severity": info["severity"],
        }
        for check_id, info in BP_CATEGORIES.items()
    ]

    # Build matrix: {check_id: {skill_name: {result, detail}}}
    matrix: dict[str, dict[str, dict]] = {c["id"]: {} for c in checks}

    for skill_name in skill_names:
        try:
            skill_content = read_skill(manifest, skill_name)
            bp_results = run_bp_checks(skill_content, skill_name)
            for bp_result in bp_results:
                result_str = "fail" if bp_result.triggered else "pass"
                matrix[bp_result.check_id][skill_name] = {
                    "result": result_str,
                    "detail": bp_result.detail,
                }
        except (ValueError, FileNotFoundError) as e:
            # Skill path not accessible — mark all checks as error
            for check in checks:
                matrix[check["id"]][skill_name] = {
                    "result": "error",
                    "detail": str(e),
                }

    return {
        "skills": skill_names,
        "checks": checks,
        "matrix": matrix,
    }


# ---------------------------------------------------------------------------
# GET /api/heatmap/detail/{scenario_id}/{check_id}
# ---------------------------------------------------------------------------


@router.get("/detail/{scenario_id}/{check_id}")
def get_cell_detail(scenario_id: str, check_id: str):
    """Return detailed comparison for a specific scenario/check cell."""
    # Validate check_id exists
    if check_id not in ALL_CATEGORIES and check_id not in BP_CATEGORIES:
        raise HTTPException(404, f"Check '{check_id}' not found")

    # Find the domain for this scenario
    domain_scenarios = load_domain_scenarios()
    found_domain: str | None = None
    found_scenario = None
    for domain_id, scenarios in domain_scenarios.items():
        for s in scenarios:
            if s.id == scenario_id:
                found_domain = domain_id
                found_scenario = s
                break
        if found_domain:
            break

    if found_domain is None or found_scenario is None:
        raise HTTPException(404, f"Scenario '{scenario_id}' not found")

    is_dev = found_domain in DEV_DOMAINS
    specialist = DOMAIN_SKILL_MAP.get(found_domain, found_scenario.target_skill)

    latest = load_latest_scored_report()
    specialist_detail: dict | None = None
    mcpc_detail: dict | None = None

    if latest is not None:
        _metadata, runs = latest
        run_index: dict[tuple[str, str], object] = {}
        for run in runs:
            run_index[(run.scenario_id, run.skill)] = run

        specialist_run = run_index.get((scenario_id, specialist))
        if specialist_run is not None:
            specialist_check = next(
                (c for c in specialist_run.checks if c.check_id == check_id),
                None,
            )
            specialist_detail = {
                "skill": specialist_run.skill,
                "result": specialist_check.result if specialist_check else "unclear",
                "evidence": specialist_check.evidence if specialist_check else "",
                "summary": specialist_check.summary if specialist_check else "",
                "model": specialist_run.model,
                "markdown_response": specialist_run.markdown_response,
            }

        if not is_dev:
            mcpc_run = run_index.get((scenario_id, "apify-mcpc"))
            if mcpc_run is not None:
                mcpc_check = next(
                    (c for c in mcpc_run.checks if c.check_id == check_id),
                    None,
                )
                mcpc_detail = {
                    "skill": mcpc_run.skill,
                    "result": mcpc_check.result if mcpc_check else "unclear",
                    "evidence": mcpc_check.evidence if mcpc_check else "",
                    "summary": mcpc_check.summary if mcpc_check else "",
                    "model": mcpc_run.model,
                    "markdown_response": mcpc_run.markdown_response,
                }

    return {
        "scenario_id": scenario_id,
        "check_id": check_id,
        "specialist": specialist_detail,
        "mcpc": mcpc_detail,
    }


# ---------------------------------------------------------------------------
# POST /api/heatmap/run
# ---------------------------------------------------------------------------


class ScoredRunRequest(BaseModel):
    domains: list[str] | None = None  # None = all domains
    model: str = "sonnet"
    concurrency: int = DEFAULT_CONCURRENCY


@router.post("/run")
async def start_scored_run(body: ScoredRunRequest):
    """Start a scored run. Returns run_id and total task count."""
    domain_scenarios = load_domain_scenarios()

    # Filter domains if requested
    if body.domains is not None:
        unknown = set(body.domains) - set(domain_scenarios.keys())
        if unknown:
            raise HTTPException(400, f"Unknown domains: {', '.join(sorted(unknown))}")
        filtered = {d: domain_scenarios[d] for d in body.domains}
    else:
        filtered = domain_scenarios

    if not filtered:
        raise HTTPException(400, "No domain scenarios found")

    manifest = load_manifest()

    # Count total tasks
    total = 0
    for domain_id, scenarios in filtered.items():
        is_dev = domain_id in DEV_DOMAINS
        for scenario in scenarios:
            total += 1  # specialist
            if not is_dev and "apify-mcpc" in manifest:
                total += 1  # mcpc

    run_id = run_manager.start_scored_run(
        domains=body.domains,
        model=body.model,
        concurrency=body.concurrency,
    )

    return {"run_id": run_id, "total": total}


# ---------------------------------------------------------------------------
# GET /api/heatmap/run/{run_id}/stream
# ---------------------------------------------------------------------------


@router.get("/run/{run_id}/stream")
async def stream_scored_run(run_id: str):
    """SSE stream for scored run progress."""
    state = run_manager.get_scored_run(run_id)
    if not state:
        raise HTTPException(404, f"Scored run '{run_id}' not found")

    async def event_generator():
        while True:
            msg = await state.queue.get()
            if msg is None:
                break
            event = msg["event"]
            data = json.dumps(msg["data"])
            yield f"event: {event}\ndata: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
