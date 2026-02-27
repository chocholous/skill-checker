"""
Unit tests for the PostToolUse cost-tracking hook (scripts/track-cost.sh).

These tests run the shell script directly with mock hook payloads — no Claude
or plugin installation needed. They run in milliseconds.
"""

import json
import os
import subprocess
from pathlib import Path

from conftest import HOOK_SCRIPT


def _payload(command: str, stdout: str = "", exit_code: int = 0) -> str:
    """Build a minimal PostToolUse hook JSON payload."""
    return json.dumps(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "tool_response": {"stdout": stdout, "stderr": "", "exitCode": exit_code},
        }
    )


def _run(payload: str, log_file: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(HOOK_SCRIPT)],
        input=payload,
        capture_output=True,
        text=True,
        env={**os.environ, "APIFY_COST_LOG": str(log_file)},
        timeout=10,
    )


def test_logs_cost_when_call_actor_returns_meta(tmp_path):
    """Writes a cost entry when call-actor --json response includes _meta."""
    log = tmp_path / "costs.log"
    stdout_json = json.dumps(
        {
            "_meta": {"usageTotalUsd": 0.0042},
            "structuredContent": {"runId": "abc123"},
        }
    )
    payload = _payload(
        command="mcpc @apify tools-call call-actor actor:=\"apify/google-search-scraper\" input:='{}' --json",
        stdout=stdout_json,
    )

    result = _run(payload, log)

    assert result.returncode == 0, f"Hook script failed:\nstderr: {result.stderr}"
    assert log.exists(), "Log file was not created"
    content = log.read_text()
    assert "actor=apify/google-search-scraper" in content, content
    assert "usd=0.0042" in content, content


def test_skips_non_call_actor_commands(tmp_path):
    """Does not write log for commands that are not call-actor."""
    log = tmp_path / "costs.log"
    payload = _payload(
        command='mcpc @apify tools-call search-actors keywords:="instagram"',
    )

    result = _run(payload, log)

    assert result.returncode == 0
    assert not log.exists(), "Log must not be created for non-call-actor command"


def test_skips_when_no_json_flag(tmp_path):
    """Does not write log when call-actor is used without --json (no _meta available)."""
    log = tmp_path / "costs.log"
    payload = _payload(
        command="mcpc @apify tools-call call-actor actor:=\"apify/google-search-scraper\" input:='{}'",
    )

    result = _run(payload, log)

    assert result.returncode == 0
    assert not log.exists(), "Log must not be created without --json"


def test_skips_when_response_has_no_meta(tmp_path):
    """Does not write log when stdout was piped through jq and _meta was stripped."""
    log = tmp_path / "costs.log"
    stdout_json = json.dumps({"structuredContent": {"runId": "abc123", "itemCount": 5}})
    payload = _payload(
        command="mcpc @apify tools-call call-actor actor:=\"apify/x\" input:='{}' --json",
        stdout=stdout_json,
    )

    result = _run(payload, log)

    assert result.returncode == 0
    assert not log.exists(), "Log must not be created when no cost data in response"


def test_handles_invalid_json_gracefully(tmp_path):
    """Does not crash and does not write log when stdout is not valid JSON."""
    log = tmp_path / "costs.log"
    payload = _payload(
        command="mcpc @apify tools-call call-actor actor:=\"apify/x\" input:='{}' --json",
        stdout="this is not json",
    )

    result = _run(payload, log)

    assert result.returncode == 0
    assert not log.exists(), "Log must not be created on JSON parse error"
