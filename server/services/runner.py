"""
RunManager — manages async scenario execution with SSE progress events.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from sim_core import (
    DEFAULT_CONCURRENCY,
    Scenario,
    ScoredRun,
    get_target_skills,
    load_domain_scenarios,
    load_manifest,
    run_scored_scenario,
    save_scored_report_incremental,
)


class ScoredRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScoredRunState:
    run_id: str
    status: ScoredRunStatus
    models: list[str]
    domains: list[str] | None
    concurrency: int
    # {scenario_id: {skill_name: {model: status}}}
    progress: dict[str, dict[str, dict[str, str]]] = field(default_factory=dict)
    results: list[ScoredRun] = field(default_factory=list)
    error: str | None = None
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    started_at: str = ""
    completed_at: str = ""
    _save_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RunManager:
    def __init__(self):
        self._scored_runs: dict[str, ScoredRunState] = {}

    def get_scored_run(self, run_id: str) -> ScoredRunState | None:
        return self._scored_runs.get(run_id)

    def start_scored_run(
        self,
        domains: list[str] | None,
        models: list[str],
        concurrency: int = DEFAULT_CONCURRENCY,
    ) -> str:
        """Start a scored run. Returns run_id."""
        run_id = uuid.uuid4().hex[:12]

        state = ScoredRunState(
            run_id=run_id,
            status=ScoredRunStatus.PENDING,
            models=models,
            domains=domains,
            concurrency=concurrency,
            started_at=datetime.now().isoformat(),
        )

        self._scored_runs[run_id] = state

        asyncio.create_task(self._execute_scored(state))
        return run_id

    async def _execute_scored(self, state: ScoredRunState):
        """Execute a scored run: for each (scenario, skill, model) combination, run scored evaluation."""
        state.status = ScoredRunStatus.RUNNING

        try:
            manifest = load_manifest()
            domain_scenarios = load_domain_scenarios()

            # Filter domains if specified
            if state.domains is not None:
                filtered = {
                    d: domain_scenarios[d]
                    for d in state.domains
                    if d in domain_scenarios
                }
            else:
                filtered = domain_scenarios

            # Build task list: (scenario, skill_name, model) cross-product
            tasks_list: list[tuple[Scenario, str, str]] = []
            for domain_id, scenarios in filtered.items():
                for scenario in scenarios:
                    skills = get_target_skills(scenario, manifest)
                    for skill_name in skills:
                        for model in state.models:
                            tasks_list.append((scenario, skill_name, model))
                            # Init progress grid
                            if scenario.id not in state.progress:
                                state.progress[scenario.id] = {}
                            if skill_name not in state.progress[scenario.id]:
                                state.progress[scenario.id][skill_name] = {}
                            state.progress[scenario.id][skill_name][model] = "pending"

            total = len(tasks_list)
            await state.queue.put(
                {
                    "event": "started",
                    "data": {
                        "run_id": state.run_id,
                        "total": total,
                    },
                }
            )

            semaphore = asyncio.Semaphore(state.concurrency)

            async def run_one_scored(scenario: Scenario, skill_name: str, model: str):
                state.progress[scenario.id][skill_name][model] = "running"
                await state.queue.put(
                    {
                        "event": "progress",
                        "data": {
                            "scenario_id": scenario.id,
                            "skill": skill_name,
                            "model": model,
                            "status": "running",
                        },
                    }
                )

                scored = await run_scored_scenario(
                    scenario, skill_name, model, manifest, semaphore
                )
                state.results.append(scored)

                # Incremental save after each completed task
                metadata = {
                    "models": state.models,
                    "domains": state.domains,
                    "concurrency": state.concurrency,
                }
                async with state._save_lock:
                    save_scored_report_incremental(
                        state.run_id, state.results, metadata
                    )

                cell_status = "error" if scored.error else "ok"
                state.progress[scenario.id][skill_name][model] = cell_status
                await state.queue.put(
                    {
                        "event": "progress",
                        "data": {
                            "scenario_id": scenario.id,
                            "skill": skill_name,
                            "model": model,
                            "status": cell_status,
                            "duration_s": scored.duration_s,
                            "error": scored.error,
                        },
                    }
                )

            coros = [run_one_scored(s, sk, m) for s, sk, m in tasks_list]
            try:
                await asyncio.gather(*coros)
            except Exception as gather_exc:
                # On partial failure: save whatever results we have so far
                if state.results:
                    metadata = {
                        "models": state.models,
                        "domains": state.domains,
                        "concurrency": state.concurrency,
                    }
                    async with state._save_lock:
                        save_scored_report_incremental(
                            state.run_id, state.results, metadata
                        )
                raise gather_exc

            state.status = ScoredRunStatus.COMPLETED
            state.completed_at = datetime.now().isoformat()

            # Determine the final report filename (already saved incrementally)
            report_name = f"scored_run_{state.run_id}.json"

            await state.queue.put(
                {
                    "event": "completed",
                    "data": {
                        "run_id": state.run_id,
                        "report_json": report_name,
                        "total_results": len(state.results),
                    },
                }
            )

        except Exception as e:
            state.status = ScoredRunStatus.FAILED
            state.error = str(e)
            state.completed_at = datetime.now().isoformat()
            await state.queue.put(
                {
                    "event": "error",
                    "data": {
                        "run_id": state.run_id,
                        "error": str(e),
                    },
                }
            )

        # Signal end of stream
        await state.queue.put(None)


# Singleton
run_manager = RunManager()
