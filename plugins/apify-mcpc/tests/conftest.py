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
from dataclasses import dataclass
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

# ---------------------------------------------------------------------------
# Spy mcpc
# ---------------------------------------------------------------------------

# Shell script content for spy mcpc.
# - Records every call to $MCPC_CALL_LOG (one line per invocation)
# - Returns canned JSON responses matching real mcpc output shape
# - Returns _meta.usageTotalUsd in call-actor --json responses (for hook tests)
_SPY_MCPC_SCRIPT = """\
#!/usr/bin/env bash
printf '%s\\n' "$*" >> "${MCPC_CALL_LOG:-/dev/null}"
CMD="$*"

if [[ -z "$CMD" ]]; then
    printf '@apify -> mcp.apify.com (running)\\n'
    printf '@apify-docs -> mcp.apify.com?tools=docs (running)\\n'
elif [[ "$CMD" == *"--version"* ]]; then
    echo "1.0.0-spy"
elif [[ "$CMD" == *"--help"* ]]; then
    printf 'Usage: mcpc [options] <server> <command>\\n'
elif [[ "$CMD" == *"call-actor"* && "$CMD" == *"--json"* ]]; then
    printf '{"_meta":{"usageTotalUsd":0.0042},"content":[{"type":"text","text":"Run completed. 1 item."}],"structuredContent":{"runId":"spy-run-abc","datasetId":"spy-ds-def","itemCount":1,"items":[{"url":"https://example.com","title":"Test Page"}]}}\\n'
elif [[ "$CMD" == *"call-actor"* ]]; then
    printf '{"content":[{"type":"text","text":"Run completed."}],"structuredContent":{"runId":"spy-run-abc","datasetId":"spy-ds-def","itemCount":1,"items":[{"url":"https://example.com","title":"Test Page"}]}}\\n'
elif [[ "$CMD" == *"search-actors"* ]]; then
    printf '{"content":[{"type":"text","text":"Found 2 actors."}],"structuredContent":{"actors":[{"fullName":"apify/instagram-post-scraper","title":"Instagram Post Scraper","stats":{"totalUsers":70000,"successRate":99.8},"pricing":{"model":"PAY_PER_EVENT","isFree":false},"rating":{"average":4.8,"count":150},"isDeprecated":false,"developer":{"username":"apify"}},{"fullName":"clockworks/tiktok-scraper","title":"TikTok Scraper","stats":{"totalUsers":50000,"successRate":98.5},"pricing":{"model":"PAY_PER_EVENT","isFree":false},"rating":{"average":4.7,"count":120},"isDeprecated":false,"developer":{"username":"clockworks"}}]}}\\n'
elif [[ "$CMD" == *"fetch-actor-details"* ]]; then
    printf '{"content":[{"type":"text","text":"Actor details."}],"structuredContent":{"actorInfo":{"title":"Instagram Post Scraper","fullName":"apify/instagram-post-scraper","stats":{"totalUsers":70000,"successRate":99.8},"pricing":{"model":"PAY_PER_EVENT","isFree":false},"rating":{"average":4.8},"isDeprecated":false},"readme":"Scrapes Instagram posts. Input: username (list, no @). Example: {\\"username\\":[\\"nasa\\"],\\"resultsLimit\\":10}","inputSchema":{"type":"object","properties":{"username":{"type":"array","items":{"type":"string"},"title":"Usernames"},"resultsLimit":{"type":"integer","default":50}},"required":["username"]}}}\\n'
elif [[ "$CMD" == *"get-actor-output"* ]]; then
    printf '{"content":[{"type":"text","text":"1 item."}],"structuredContent":{"datasetId":"spy-ds-def","items":[{"url":"https://example.com","title":"Test Page"}],"itemCount":1,"totalItemCount":1,"offset":0,"limit":100}}\\n'
elif [[ "$CMD" == *"get-actor-run"* ]]; then
    printf '{"content":[{"type":"text","text":"Run SUCCEEDED."}],"structuredContent":{"runId":"spy-run-abc","actorName":"apify/instagram-post-scraper","status":"SUCCEEDED","dataset":{"datasetId":"spy-ds-def","itemCount":1}}}\\n'
elif [[ "$CMD" == *"search-apify-docs"* || "$CMD" == *"fetch-apify-docs"* ]]; then
    printf '{"content":[{"type":"text","text":"Docs found."}],"structuredContent":{"results":[{"title":"Getting Started","url":"https://docs.apify.com/platform/actors"}]}}\\n'
else
    printf '{}'
fi
exit 0
"""


@dataclass
class SpyMcpc:
    """Spy mcpc binary with associated log paths and convenience methods."""

    path_override: str  # prepend to PATH so Claude uses spy instead of real mcpc
    call_log: Path  # every mcpc invocation is logged here (one line per call)
    cost_log: Path  # PostToolUse hook writes cost entries here

    @property
    def env(self) -> dict[str, str]:
        """Extra env vars to pass to run_claude so spy and hook use test paths."""
        return {
            "MCPC_CALL_LOG": str(self.call_log),
            "APIFY_COST_LOG": str(self.cost_log),
        }

    def calls(self) -> list[str]:
        """Return list of recorded mcpc invocation argument strings."""
        if not self.call_log.exists():
            return []
        return self.call_log.read_text().strip().splitlines()


def make_spy_mcpc(tmp_path: Path) -> SpyMcpc:
    """Write spy mcpc binary to tmp_path and return a SpyMcpc descriptor."""
    mcpc_bin = tmp_path / "mcpc"
    mcpc_bin.write_text(_SPY_MCPC_SCRIPT)
    mcpc_bin.chmod(0o755)
    return SpyMcpc(
        path_override=f"{tmp_path}:{os.environ.get('PATH', '')}",
        call_log=tmp_path / "mcpc-calls.log",
        cost_log=tmp_path / "apify-costs.log",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_plugin(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_CLAUDE_BIN, "plugin", *args],
        capture_output=True,
        text=True,
        env=_ENV,
        timeout=60,
    )


def run_claude(
    prompt: str,
    *,
    skip_permissions: bool = True,
    path_override: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    cmd = [_CLAUDE_BIN, "-p", "--output-format", "json", "--no-session-persistence"]
    if skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    env = _ENV.copy()
    if path_override is not None:
        env["PATH"] = path_override
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
