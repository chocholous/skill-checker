"""Unit tests for server/services/runner.py — multi-model + incremental save."""

import asyncio
import inspect
from pathlib import Path
from unittest.mock import patch

import pytest

from server.services.runner import RunManager, ScoredRunState, ScoredRunStatus
from sim_core import CheckResult, Scenario, ScoredRun


def _make_scored_run(
    scenario_id: str = "ci-1",
    skill: str = "apify-competitor-intelligence",
    model: str = "sonnet",
) -> ScoredRun:
    return ScoredRun(
        scenario_id=scenario_id,
        skill=skill,
        model=model,
        checks=[
            CheckResult(
                check_id="WF-1",
                result="pass",
                evidence="Has workflow steps",
                summary="Workflow present",
            ),
        ],
        risk_level="LOW",
        markdown_response="## Analysis",
        duration_s=1.2,
        cost_info="input=100, output=200",
        error=None,
    )


def _make_scenario(
    scenario_id: str = "ci-1",
    domain: str = "competitive-intelligence",
    skill: str = "apify-competitor-intelligence",
) -> Scenario:
    return Scenario(
        id=scenario_id,
        name="Test scenario",
        prompt="Test prompt",
        target_skill=skill,
        source_file="test.yaml",
        domain=domain,
    )


# ---------------------------------------------------------------------------
# ScoredRunState — models field is list[str]
# ---------------------------------------------------------------------------


def test_scored_run_state_has_models_list():
    """ScoredRunState.models is a list[str], not a single str."""
    state = ScoredRunState(
        run_id="test123",
        status=ScoredRunStatus.PENDING,
        models=["sonnet", "haiku"],
        domains=None,
        concurrency=3,
        started_at="",
    )
    assert state.models == ["sonnet", "haiku"]
    assert isinstance(state.models, list)
    # Ensure no 'model' attribute exists (old interface removed)
    assert not hasattr(state, "model")


def test_scored_run_state_has_save_lock():
    """ScoredRunState has an asyncio.Lock for save protection."""
    state = ScoredRunState(
        run_id="lock_test",
        status=ScoredRunStatus.PENDING,
        models=["sonnet"],
        domains=None,
        concurrency=3,
        started_at="",
    )
    assert isinstance(state._save_lock, asyncio.Lock)


def test_scored_run_state_default_progress_and_results():
    """progress and results start empty."""
    state = ScoredRunState(
        run_id="prog_test",
        status=ScoredRunStatus.PENDING,
        models=["sonnet"],
        domains=None,
        concurrency=3,
        started_at="",
    )
    assert state.progress == {}
    assert state.results == []


# ---------------------------------------------------------------------------
# RunManager.start_scored_run — accepts models list
# ---------------------------------------------------------------------------


def test_run_manager_start_scored_run_signature_uses_models():
    """start_scored_run() parameter is 'models' (list), not 'model' (str)."""
    manager = RunManager()
    sig = inspect.signature(manager.start_scored_run)
    params = sig.parameters

    assert "models" in params, "start_scored_run must have 'models' parameter"
    assert "model" not in params, "start_scored_run must not have old 'model' parameter"


def test_run_manager_stores_state_with_models_list():
    """start_scored_run() stores state with correct models list."""
    manager = RunManager()

    with patch("server.services.runner.asyncio.create_task"):
        run_id = manager.start_scored_run(
            domains=["competitive-intelligence"],
            models=["sonnet", "opus"],
            concurrency=2,
        )

    state = manager.get_scored_run(run_id)
    assert state is not None
    assert state.models == ["sonnet", "opus"]
    assert state.domains == ["competitive-intelligence"]
    assert state.concurrency == 2
    assert state.run_id == run_id


# ---------------------------------------------------------------------------
# _execute_scored — async tests using asyncio.run() directly
# ---------------------------------------------------------------------------


def _run_execute_scored_with_mocks(
    state: ScoredRunState,
    manager: RunManager,
    mock_manifest: dict,
    domain_scenarios: dict,
    target_skills: list[str],
    side_effect_run=None,
    side_effect_save=None,
) -> None:
    """Helper to run _execute_scored with common mocks synchronously."""

    async def _inner():
        with (
            patch("server.services.runner.load_manifest", return_value=mock_manifest),
            patch(
                "server.services.runner.load_domain_scenarios",
                return_value=domain_scenarios,
            ),
            patch(
                "server.services.runner.get_target_skills",
                return_value=target_skills,
            ),
            patch(
                "server.services.runner.run_scored_scenario",
                side_effect=side_effect_run,
            ),
            patch(
                "server.services.runner.save_scored_report_incremental",
                side_effect=side_effect_save,
            ),
        ):
            await manager._execute_scored(state)

    asyncio.run(_inner())


def test_execute_scored_task_list_cross_product():
    """Task list iterates over (scenario × skill × model) cross-product."""
    manager = RunManager()
    scenario = _make_scenario()

    state = ScoredRunState(
        run_id="xproduct_test",
        status=ScoredRunStatus.PENDING,
        models=["sonnet", "haiku"],
        domains=["competitive-intelligence"],
        concurrency=2,
        started_at="",
    )
    manager._scored_runs["xproduct_test"] = state

    mock_manifest = {
        "apify-competitor-intelligence": {
            "path": "/fake/path",
            "category": "dispatcher",
        },
        "apify-mcpc": {"path": "/fake/mcpc", "category": "dispatcher"},
    }

    calls_made: list[tuple[str, str, str]] = []

    async def fake_run(s, skill, model, manifest, semaphore):
        calls_made.append((s.id, skill, model))
        return _make_scored_run(scenario_id=s.id, skill=skill, model=model)

    _run_execute_scored_with_mocks(
        state=state,
        manager=manager,
        mock_manifest=mock_manifest,
        domain_scenarios={"competitive-intelligence": [scenario]},
        target_skills=["apify-competitor-intelligence", "apify-mcpc"],
        side_effect_run=fake_run,
        side_effect_save=lambda *a: None,
    )

    # 1 scenario × 2 skills × 2 models = 4 tasks
    assert len(calls_made) == 4
    models_seen = {m for _, _, m in calls_made}
    assert "sonnet" in models_seen
    assert "haiku" in models_seen
    skills_seen = {sk for _, sk, _ in calls_made}
    assert "apify-competitor-intelligence" in skills_seen
    assert "apify-mcpc" in skills_seen


def test_execute_scored_incremental_save_called_per_task():
    """save_scored_report_incremental is called once per completed task."""
    manager = RunManager()
    scenario = _make_scenario()

    state = ScoredRunState(
        run_id="inc_save_test",
        status=ScoredRunStatus.PENDING,
        models=["sonnet"],
        domains=["competitive-intelligence"],
        concurrency=1,
        started_at="",
    )
    manager._scored_runs["inc_save_test"] = state

    mock_manifest = {
        "apify-competitor-intelligence": {
            "path": "/fake/path",
            "category": "dispatcher",
        },
    }
    save_call_count: list[int] = []

    def fake_save(run_id, results, metadata):
        save_call_count.append(len(results))

    async def fake_run(s, skill, model, manifest, semaphore):
        return _make_scored_run(scenario_id=s.id, skill=skill, model=model)

    _run_execute_scored_with_mocks(
        state=state,
        manager=manager,
        mock_manifest=mock_manifest,
        domain_scenarios={"competitive-intelligence": [scenario]},
        target_skills=["apify-competitor-intelligence"],
        side_effect_run=fake_run,
        side_effect_save=fake_save,
    )

    # 1 task → 1 incremental save call
    assert len(save_call_count) == 1
    assert save_call_count[0] == 1


def test_execute_scored_metadata_uses_models_list():
    """Metadata passed to save uses 'models' key (list), not 'model' (str)."""
    manager = RunManager()
    scenario = _make_scenario()

    state = ScoredRunState(
        run_id="meta_test",
        status=ScoredRunStatus.PENDING,
        models=["sonnet", "opus"],
        domains=["competitive-intelligence"],
        concurrency=1,
        started_at="",
    )
    manager._scored_runs["meta_test"] = state

    mock_manifest = {
        "apify-competitor-intelligence": {
            "path": "/fake/path",
            "category": "dispatcher",
        },
    }
    captured_metadata: list[dict] = []

    def fake_save(run_id, results, metadata):
        captured_metadata.append(dict(metadata))

    async def fake_run(s, skill, model, manifest, semaphore):
        return _make_scored_run(scenario_id=s.id, skill=skill, model=model)

    _run_execute_scored_with_mocks(
        state=state,
        manager=manager,
        mock_manifest=mock_manifest,
        domain_scenarios={"competitive-intelligence": [scenario]},
        target_skills=["apify-competitor-intelligence"],
        side_effect_run=fake_run,
        side_effect_save=fake_save,
    )

    assert len(captured_metadata) >= 1
    for meta in captured_metadata:
        assert "models" in meta, f"'models' key missing from metadata: {meta}"
        assert isinstance(meta["models"], list)
        assert "sonnet" in meta["models"]
        assert "opus" in meta["models"]
        assert "model" not in meta, f"Old 'model' key found in metadata: {meta}"


def test_execute_scored_sse_progress_includes_model():
    """SSE progress events include 'model' field."""
    manager = RunManager()
    scenario = _make_scenario()

    state = ScoredRunState(
        run_id="sse_model_test",
        status=ScoredRunStatus.PENDING,
        models=["sonnet"],
        domains=["competitive-intelligence"],
        concurrency=1,
        started_at="",
    )
    manager._scored_runs["sse_model_test"] = state

    mock_manifest = {
        "apify-competitor-intelligence": {
            "path": "/fake/path",
            "category": "dispatcher",
        },
    }

    async def fake_run(s, skill, model, manifest, semaphore):
        return _make_scored_run(scenario_id=s.id, skill=skill, model=model)

    _run_execute_scored_with_mocks(
        state=state,
        manager=manager,
        mock_manifest=mock_manifest,
        domain_scenarios={"competitive-intelligence": [scenario]},
        target_skills=["apify-competitor-intelligence"],
        side_effect_run=fake_run,
        side_effect_save=lambda *a: None,
    )

    # Drain the queue
    events = []
    while not state.queue.empty():
        msg = state.queue.get_nowait()
        if msg is not None:
            events.append(msg)

    progress_events = [e for e in events if e["event"] == "progress"]
    assert len(progress_events) >= 1, "Expected at least one progress event"

    for event in progress_events:
        assert "model" in event["data"], (
            f"Progress event missing 'model' field: {event['data']}"
        )


def test_execute_scored_no_final_save_scored_report():
    """The old non-incremental save_scored_report is NOT imported or called."""
    import server.services.runner as runner_module

    # Verify save_scored_report is not imported in runner module
    assert not hasattr(runner_module, "save_scored_report"), (
        "save_scored_report (non-incremental) should not be imported in runner"
    )


def test_execute_scored_partial_save_on_crash():
    """On asyncio.gather exception, partial results trigger an emergency save."""
    manager = RunManager()
    scenario = _make_scenario()

    state = ScoredRunState(
        run_id="crash_test",
        status=ScoredRunStatus.PENDING,
        models=["sonnet"],
        domains=["competitive-intelligence"],
        concurrency=1,
        started_at="",
    )
    manager._scored_runs["crash_test"] = state

    # Pre-populate some results so the crash path has data to save
    state.results.append(_make_scored_run())

    mock_manifest = {
        "apify-competitor-intelligence": {
            "path": "/fake/path",
            "category": "dispatcher",
        },
    }

    emergency_saves: list[int] = []

    def fake_save(run_id, results, metadata):
        emergency_saves.append(len(results))

    async def crashing_run(*args, **kwargs):
        raise RuntimeError("Simulated crash")

    _run_execute_scored_with_mocks(
        state=state,
        manager=manager,
        mock_manifest=mock_manifest,
        domain_scenarios={"competitive-intelligence": [scenario]},
        target_skills=["apify-competitor-intelligence"],
        side_effect_run=crashing_run,
        side_effect_save=fake_save,
    )

    # State must be FAILED after crash
    assert state.status == ScoredRunStatus.FAILED
    # Emergency save should have been triggered since we had 1 pre-existing result
    assert len(emergency_saves) >= 1, (
        "Expected emergency save to be called when gather crashes with partial results"
    )


# ---------------------------------------------------------------------------
# ScoredRunStatus enum
# ---------------------------------------------------------------------------


def test_scored_run_status_enum():
    assert ScoredRunStatus.PENDING == "pending"
    assert ScoredRunStatus.RUNNING == "running"
    assert ScoredRunStatus.COMPLETED == "completed"
    assert ScoredRunStatus.FAILED == "failed"
