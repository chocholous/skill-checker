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
    save_scored_report,
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
    model: str
    domains: list[str] | None
    concurrency: int
    # {scenario_id: {skill_name: status}}
    progress: dict[str, dict[str, str]] = field(default_factory=dict)
    results: list[ScoredRun] = field(default_factory=list)
    error: str | None = None
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    started_at: str = ""
    completed_at: str = ""


class RunManager:
    def __init__(self):
        self._scored_runs: dict[str, ScoredRunState] = {}

    def get_scored_run(self, run_id: str) -> ScoredRunState | None:
        return self._scored_runs.get(run_id)

    def start_scored_run(
        self,
        domains: list[str] | None,
        model: str,
        concurrency: int = DEFAULT_CONCURRENCY,
    ) -> str:
        """Start a scored run. Returns run_id."""
        run_id = uuid.uuid4().hex[:12]

        state = ScoredRunState(
            run_id=run_id,
            status=ScoredRunStatus.PENDING,
            model=model,
            domains=domains,
            concurrency=concurrency,
            started_at=datetime.now().isoformat(),
        )

        self._scored_runs[run_id] = state

        asyncio.create_task(self._execute_scored(state))
        return run_id

    async def _execute_scored(self, state: ScoredRunState):
        """Execute a scored run: for each (scenario, skill) combination, run scored evaluation."""
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

            # Build task list: (scenario, skill_name)
            tasks_list: list[tuple[Scenario, str]] = []
            for domain_id, scenarios in filtered.items():
                for scenario in scenarios:
                    skills = get_target_skills(scenario, manifest)
                    for skill_name in skills:
                        tasks_list.append((scenario, skill_name))
                        # Init progress grid
                        if scenario.id not in state.progress:
                            state.progress[scenario.id] = {}
                        state.progress[scenario.id][skill_name] = "pending"

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

            async def run_one_scored(scenario: Scenario, skill_name: str):
                state.progress[scenario.id][skill_name] = "running"
                await state.queue.put(
                    {
                        "event": "progress",
                        "data": {
                            "scenario_id": scenario.id,
                            "skill": skill_name,
                            "status": "running",
                        },
                    }
                )

                scored = await run_scored_scenario(
                    scenario, skill_name, state.model, manifest, semaphore
                )
                state.results.append(scored)

                cell_status = "error" if scored.error else "ok"
                state.progress[scenario.id][skill_name] = cell_status
                await state.queue.put(
                    {
                        "event": "progress",
                        "data": {
                            "scenario_id": scenario.id,
                            "skill": skill_name,
                            "status": cell_status,
                            "duration_s": scored.duration_s,
                            "error": scored.error,
                        },
                    }
                )

            coros = [run_one_scored(s, sk) for s, sk in tasks_list]
            await asyncio.gather(*coros)

            # Save scored report
            metadata = {
                "model": state.model,
                "domains": state.domains,
                "concurrency": state.concurrency,
            }
            report_path = save_scored_report(state.results, metadata)

            state.status = ScoredRunStatus.COMPLETED
            state.completed_at = datetime.now().isoformat()
            await state.queue.put(
                {
                    "event": "completed",
                    "data": {
                        "run_id": state.run_id,
                        "report_json": report_path.name,
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
