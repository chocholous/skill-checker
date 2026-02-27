"""
Shared fixtures and helpers for apify-mcpc plugin tests.

IMPORTANT: Run outside an active Claude Code session:
    CLAUDECODE= pytest plugins/apify-mcpc/tests/ -v

These tests modify your user-scope plugin installation. They clean up after
themselves, but if interrupted mid-run, manually uninstall with:
    claude plugin uninstall apify-mcpc
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).parent.parent
HOOK_SCRIPT = PLUGIN_DIR / "scripts" / "track-cost.sh"
MARKETPLACE = "skill-checker"
PLUGIN_NAME = "apify-mcpc"

# Unset CLAUDECODE so claude -p can be called from within a Claude Code session
_ENV = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

# Resolve claude binary once at import time — used as explicit executable so
# PATH overrides in individual tests don't accidentally hide it
_CLAUDE_BIN = shutil.which("claude") or "claude"


def run_plugin(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_CLAUDE_BIN, "plugin", *args],
        capture_output=True,
        text=True,
        env=_ENV,
        timeout=60,
    )


def run_claude(
    prompt: str, *, skip_permissions: bool = True, path_override: str | None = None
) -> subprocess.CompletedProcess:
    cmd = [_CLAUDE_BIN, "-p", "--output-format", "json", "--no-session-persistence"]
    if skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    env = _ENV.copy()
    if path_override is not None:
        env["PATH"] = path_override
    return subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


@pytest.fixture(scope="module")
def installed_plugin():
    """Install apify-mcpc from marketplace, yield, then uninstall."""
    run_plugin("uninstall", PLUGIN_NAME)  # clean slate

    result = run_plugin("install", f"{PLUGIN_NAME}@{MARKETPLACE}")
    assert result.returncode == 0, (
        f"Plugin install failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    yield
    run_plugin("uninstall", PLUGIN_NAME)
