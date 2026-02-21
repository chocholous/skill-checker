"""Runs router — start runs + SSE stream progress."""

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from sim_core import DEFAULT_CONCURRENCY, DEFAULT_MODELS, load_scenarios
from server.services.runner import run_manager, RunStatus

router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunRequest(BaseModel):
    scenario_ids: list[str] | None = None  # None = all
    models: list[str] = DEFAULT_MODELS
    concurrency: int = DEFAULT_CONCURRENCY


@router.post("")
async def start_run(body: RunRequest):
    """Start a new run. Returns run_id."""
    all_scenarios = load_scenarios()

    if body.scenario_ids:
        scenarios = [s for s in all_scenarios if s.id in body.scenario_ids]
        missing = set(body.scenario_ids) - {s.id for s in scenarios}
        if missing:
            raise HTTPException(404, f"Unknown scenarios: {', '.join(missing)}")
    else:
        scenarios = all_scenarios

    if not scenarios:
        raise HTTPException(400, "No scenarios to run")

    run_id = run_manager.start_run(scenarios, body.models, body.concurrency)
    return {
        "run_id": run_id,
        "total": len(scenarios) * len(body.models),
        "scenarios": len(scenarios),
        "models": body.models,
    }


@router.get("/{run_id}/stream")
async def stream_run(run_id: str):
    """SSE stream for run progress."""
    state = run_manager.get_run(run_id)
    if not state:
        raise HTTPException(404, f"Run '{run_id}' not found")

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


@router.get("/{run_id}/result")
def get_run_result(run_id: str):
    """Get completed run result."""
    state = run_manager.get_run(run_id)
    if not state:
        raise HTTPException(404, f"Run '{run_id}' not found")

    return {
        "run_id": state.run_id,
        "status": state.status.value,
        "models": state.models,
        "scenario_ids": state.scenario_ids,
        "progress": state.progress,
        "started_at": state.started_at,
        "completed_at": state.completed_at,
        "error": state.error,
        "result_count": len(state.results),
        "results": [
            {
                "scenario_id": r.scenario_id,
                "model": r.model,
                "response": r.response,
                "duration_s": r.duration_s,
                "cost_info": r.cost_info,
                "error": r.error,
            }
            for r in state.results
        ],
    }
