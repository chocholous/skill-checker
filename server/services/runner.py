"""
RunManager — manages async scenario execution with SSE progress events.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from sim_core import (
    DEFAULT_CONCURRENCY,
    RunResult,
    Scenario,
    load_manifest,
    run_scenario,
    save_reports,
)


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RunState:
    run_id: str
    status: RunStatus
    models: list[str]
    scenario_ids: list[str]
    concurrency: int
    progress: dict[str, dict[str, str]] = field(default_factory=dict)  # {scenario_id: {model: status}}
    results: list[RunResult] = field(default_factory=list)
    error: str | None = None
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    started_at: str = ""
    completed_at: str = ""


class RunManager:
    def __init__(self):
        self._runs: dict[str, RunState] = {}

    def get_run(self, run_id: str) -> RunState | None:
        return self._runs.get(run_id)

    def start_run(
        self,
        scenarios: list[Scenario],
        models: list[str],
        concurrency: int = DEFAULT_CONCURRENCY,
    ) -> str:
        run_id = uuid.uuid4().hex[:12]
        state = RunState(
            run_id=run_id,
            status=RunStatus.PENDING,
            models=models,
            scenario_ids=[s.id for s in scenarios],
            concurrency=concurrency,
            started_at=datetime.now().isoformat(),
        )

        # Init progress grid
        for s in scenarios:
            state.progress[s.id] = {m: "pending" for m in models}

        self._runs[run_id] = state

        asyncio.create_task(self._execute(state, scenarios, models, concurrency))
        return run_id

    async def _execute(
        self,
        state: RunState,
        scenarios: list[Scenario],
        models: list[str],
        concurrency: int,
    ):
        state.status = RunStatus.RUNNING
        await state.queue.put({"event": "started", "data": {
            "run_id": state.run_id,
            "total": len(scenarios) * len(models),
        }})

        try:
            manifest = load_manifest()
            semaphore = asyncio.Semaphore(concurrency)

            async def run_one(scenario: Scenario, model: str):
                state.progress[scenario.id][model] = "running"
                await state.queue.put({"event": "progress", "data": {
                    "scenario_id": scenario.id,
                    "model": model,
                    "status": "running",
                }})

                result = await run_scenario(scenario, model, manifest, semaphore)
                state.results.append(result)

                cell_status = "error" if result.error else "ok"
                state.progress[scenario.id][model] = cell_status
                await state.queue.put({"event": "progress", "data": {
                    "scenario_id": scenario.id,
                    "model": model,
                    "status": cell_status,
                    "duration_s": result.duration_s,
                    "error": result.error,
                }})

            tasks = [
                run_one(s, m)
                for s in scenarios
                for m in models
            ]
            await asyncio.gather(*tasks)

            # Save reports
            md_path, json_path = save_reports(scenarios, state.results, models)

            state.status = RunStatus.COMPLETED
            state.completed_at = datetime.now().isoformat()
            await state.queue.put({"event": "completed", "data": {
                "run_id": state.run_id,
                "report_md": md_path.name,
                "report_json": json_path.name,
            }})

        except Exception as e:
            state.status = RunStatus.FAILED
            state.error = str(e)
            state.completed_at = datetime.now().isoformat()
            await state.queue.put({"event": "error", "data": {
                "run_id": state.run_id,
                "error": str(e),
            }})

        # Signal end of stream
        await state.queue.put(None)


# Singleton
run_manager = RunManager()
